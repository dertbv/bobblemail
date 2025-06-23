#!/usr/bin/env python3
"""
Live 20%+ Growth Stock Research System
Real-time stock screening for high-potential opportunities

This module implements live research capabilities to identify stocks
with 20%+ growth potential in the next 30 days using multiple data sources.
"""

import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from functools import wraps
import time
import json
from threading import Lock


def ttl_cache(seconds=900, maxsize=100):
    """
    Time-based LRU cache decorator with TTL (time-to-live)
    
    Args:
        seconds: Cache TTL in seconds (default 15 minutes)
        maxsize: Maximum number of cached items
    
    Returns:
        Decorator function that adds TTL caching to the wrapped function
    """
    def decorator(func):
        cache = {}
        cache_lock = Lock()
        cache_order = []  # Track insertion order for LRU
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function arguments
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            with cache_lock:
                # Check if key exists and is not expired
                if key in cache:
                    value, timestamp = cache[key]
                    if current_time - timestamp < seconds:
                        # Move to end (most recently used)
                        cache_order.remove(key)
                        cache_order.append(key)
                        # Log cache hit
                        if hasattr(func, '__self__') and hasattr(func.__self__, 'logger'):
                            func.__self__.logger.debug(f"Cache hit for {func.__name__} with key: {key[:50]}...")
                        return value
                    else:
                        # Expired - remove from cache
                        del cache[key]
                        cache_order.remove(key)
                        if hasattr(func, '__self__') and hasattr(func.__self__, 'logger'):
                            func.__self__.logger.debug(f"Cache expired for {func.__name__} with key: {key[:50]}...")
                
                # Clean up expired entries
                expired_keys = []
                for k in list(cache.keys()):
                    _, timestamp = cache[k]
                    if current_time - timestamp >= seconds:
                        expired_keys.append(k)
                
                for k in expired_keys:
                    del cache[k]
                    if k in cache_order:
                        cache_order.remove(k)
            
            # Call the actual function
            result = func(*args, **kwargs)
            
            with cache_lock:
                # Add to cache
                cache[key] = (result, current_time)
                cache_order.append(key)
                
                # Enforce maxsize limit (LRU eviction)
                while len(cache) > maxsize:
                    oldest_key = cache_order.pop(0)
                    del cache[oldest_key]
            
            return result
        
        # Add method to clear cache manually
        def clear_cache():
            with cache_lock:
                cache.clear()
                cache_order.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


class LiveStockResearcher:
    """
    Live stock research system for identifying 20%+ growth opportunities
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.setup_logging()
        
        # API configuration
        self.alpha_vantage_key = self.config.get('alpha_vantage_key', 'demo')
        self.fmp_key = self.config.get('fmp_key', 'demo')
        
        # Screening criteria for 20%+ growth potential
        self.growth_criteria = {
            'min_growth_potential': 20.0,  # Minimum 20% upside
            'max_price': 50.0,  # Focus on accessible stocks
            'min_volume': 100000,  # Minimum daily volume
            'min_market_cap': 10000000,  # $10M minimum market cap
            'max_volatility': 0.8,  # Maximum daily volatility threshold
        }
        
        # Technical indicators thresholds
        self.technical_thresholds = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'momentum_threshold': 0.05,  # 5% positive momentum
            'volume_spike_threshold': 1.5,  # 1.5x average volume
        }

    def setup_logging(self):
        """Configure logging for research activities"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('live_research.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    @ttl_cache(seconds=900, maxsize=100)  # 15-minute cache
    def get_stock_data(self, ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get cached stock data using Yahoo Finance
        
        Args:
            ticker: Stock ticker symbol
            period: Data period (1mo, 3mo, 6mo, 1y)
            
        Returns:
            DataFrame with stock data or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval="1d")
            
            if data.empty:
                self.logger.warning(f"No data found for {ticker}")
                return None
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Calculate technical indicators for growth potential assessment
        
        Args:
            data: Stock price DataFrame
            
        Returns:
            Dictionary of technical indicators
        """
        if data.empty or len(data) < 14:
            return {}
            
        try:
            current_price = data['Close'].iloc[-1]
            
            # RSI calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # Moving averages
            sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(window=min(50, len(data))).mean().iloc[-1]
            
            # Volume analysis
            avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price momentum (30-day)
            if len(data) >= 30:
                price_30_days_ago = data['Close'].iloc[-30]
                momentum = (current_price - price_30_days_ago) / price_30_days_ago
            else:
                momentum = (current_price - data['Close'].iloc[0]) / data['Close'].iloc[0]
            
            # Volatility (standard deviation of returns)
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            return {
                'current_price': float(current_price),
                'rsi': float(current_rsi),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'volume_ratio': float(volume_ratio),
                'momentum_30d': float(momentum),
                'volatility': float(volatility),
                'price_vs_sma20': float((current_price - sma_20) / sma_20),
                'price_vs_sma50': float((current_price - sma_50) / sma_50)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {}

    def get_fundamental_data(self, ticker: str) -> Dict:
        """
        Get fundamental data for growth assessment
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary of fundamental metrics
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract key fundamental metrics
            fundamentals = {
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', None),
                'forward_pe': info.get('forwardPE', None),
                'peg_ratio': info.get('pegRatio', None),
                'revenue_growth': info.get('revenueGrowth', None),
                'earnings_growth': info.get('earningsGrowth', None),
                'profit_margins': info.get('profitMargins', None),
                'beta': info.get('beta', None),
                'analyst_target': info.get('targetMeanPrice', None),
                'recommendation': info.get('recommendationMean', None),
                '52_week_high': info.get('fiftyTwoWeekHigh', None),
                '52_week_low': info.get('fiftyTwoWeekLow', None),
            }
            
            return fundamentals
            
        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            return {}

    def calculate_growth_potential(self, ticker: str, technical_data: Dict, fundamental_data: Dict) -> Dict:
        """
        Calculate growth potential score and target price
        
        Args:
            ticker: Stock ticker symbol
            technical_data: Technical indicators
            fundamental_data: Fundamental metrics
            
        Returns:
            Growth potential analysis
        """
        current_price = technical_data.get('current_price', 0)
        if current_price == 0:
            return {'growth_potential': 0, 'confidence': 0, 'reasons': ['No price data']}
        
        growth_score = 0
        confidence_score = 0
        reasons = []
        
        # Technical factors (40% weight)
        
        # RSI oversold condition (good entry point)
        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            growth_score += 15
            reasons.append(f"Oversold RSI ({rsi:.1f}) - potential bounce")
        elif rsi < 40:
            growth_score += 8
            reasons.append(f"Low RSI ({rsi:.1f}) - near oversold")
        
        # Momentum analysis
        momentum = technical_data.get('momentum_30d', 0)
        if momentum > 0.1:  # 10%+ momentum
            growth_score += 10
            reasons.append(f"Strong momentum ({momentum*100:.1f}%)")
        elif momentum > 0.05:  # 5%+ momentum
            growth_score += 5
            reasons.append(f"Positive momentum ({momentum*100:.1f}%)")
        
        # Volume spike
        volume_ratio = technical_data.get('volume_ratio', 1)
        if volume_ratio > 2:
            growth_score += 10
            reasons.append(f"High volume activity ({volume_ratio:.1f}x avg)")
        elif volume_ratio > 1.5:
            growth_score += 5
            reasons.append(f"Increased volume ({volume_ratio:.1f}x avg)")
        
        # Moving average position
        price_vs_sma20 = technical_data.get('price_vs_sma20', 0)
        if price_vs_sma20 > 0.02:  # 2% above SMA20
            growth_score += 5
            reasons.append("Above 20-day moving average")
        
        # Fundamental factors (40% weight)
        
        # Analyst target price
        analyst_target = fundamental_data.get('analyst_target')
        if analyst_target and current_price:
            target_upside = (analyst_target - current_price) / current_price
            if target_upside > 0.3:  # 30%+ upside
                growth_score += 20
                reasons.append(f"High analyst target upside ({target_upside*100:.1f}%)")
            elif target_upside > 0.2:  # 20%+ upside
                growth_score += 15
                reasons.append(f"Good analyst target upside ({target_upside*100:.1f}%)")
            elif target_upside > 0.1:  # 10%+ upside
                growth_score += 8
                reasons.append(f"Moderate analyst upside ({target_upside*100:.1f}%)")
        
        # Growth metrics
        earnings_growth = fundamental_data.get('earnings_growth')
        if earnings_growth and earnings_growth > 0.15:  # 15%+ earnings growth
            growth_score += 10
            reasons.append(f"Strong earnings growth ({earnings_growth*100:.1f}%)")
        elif earnings_growth and earnings_growth > 0.05:  # 5%+ earnings growth
            growth_score += 5
            reasons.append(f"Positive earnings growth ({earnings_growth*100:.1f}%)")
        
        # Valuation metrics
        pe_ratio = fundamental_data.get('pe_ratio')
        if pe_ratio and 5 < pe_ratio < 15:  # Reasonable valuation
            growth_score += 5
            reasons.append(f"Reasonable P/E ratio ({pe_ratio:.1f})")
        
        # Market position factors (20% weight)
        
        # 52-week position
        week_52_high = fundamental_data.get('52_week_high')
        week_52_low = fundamental_data.get('52_week_low')
        if week_52_high and week_52_low and current_price:
            position_in_range = (current_price - week_52_low) / (week_52_high - week_52_low)
            if position_in_range < 0.3:  # Near 52-week low
                growth_score += 10
                reasons.append("Near 52-week low - potential recovery")
            elif position_in_range < 0.5:  # Lower half of range
                growth_score += 5
                reasons.append("In lower half of 52-week range")
        
        # Calculate confidence based on data availability
        available_metrics = sum([
            1 if technical_data.get('rsi') else 0,
            1 if technical_data.get('momentum_30d') is not None else 0,
            1 if fundamental_data.get('analyst_target') else 0,
            1 if fundamental_data.get('earnings_growth') else 0,
            1 if fundamental_data.get('pe_ratio') else 0
        ])
        confidence_score = min(100, (available_metrics / 5) * 100)
        
        # Calculate target price estimate
        target_price = current_price
        if analyst_target:
            target_price = max(target_price, analyst_target)
        
        # Technical target based on momentum and support/resistance
        if momentum > 0.05:
            technical_target = current_price * (1 + momentum + 0.1)  # Add 10% buffer
            target_price = max(target_price, technical_target)
        
        growth_potential = (target_price - current_price) / current_price * 100
        
        return {
            'growth_potential': max(0, growth_potential),
            'growth_score': growth_score,
            'confidence': confidence_score,
            'target_price': target_price,
            'reasons': reasons[:5],  # Top 5 reasons
            'technical_score': min(100, growth_score * 1.2)  # Scale for display
        }

    def screen_for_growth_stocks(self, ticker_list: List[str]) -> List[Dict]:
        """
        Screen a list of tickers for 20%+ growth potential
        
        Args:
            ticker_list: List of stock tickers to screen
            
        Returns:
            List of qualified stocks with growth analysis
        """
        qualified_stocks = []
        
        for ticker in ticker_list:
            try:
                self.logger.info(f"Screening {ticker} for growth potential")
                
                # Get stock data
                data = self.get_stock_data(ticker)
                if data is None or data.empty:
                    continue
                
                # Calculate technical indicators
                technical_data = self.calculate_technical_indicators(data)
                if not technical_data:
                    continue
                
                # Get fundamental data
                fundamental_data = self.get_fundamental_data(ticker)
                
                # Apply basic filters
                current_price = technical_data.get('current_price', 0)
                market_cap = fundamental_data.get('market_cap', 0)
                
                if current_price > self.growth_criteria['max_price']:
                    continue
                if market_cap < self.growth_criteria['min_market_cap']:
                    continue
                
                # Calculate growth potential
                growth_analysis = self.calculate_growth_potential(ticker, technical_data, fundamental_data)
                
                # Filter for 20%+ growth potential
                if growth_analysis['growth_potential'] >= self.growth_criteria['min_growth_potential']:
                    
                    stock_analysis = {
                        'ticker': ticker,
                        'current_price': current_price,
                        'target_price': growth_analysis['target_price'],
                        'upside_potential': growth_analysis['growth_potential'],
                        'growth_score': growth_analysis['growth_score'],
                        'technical_score': growth_analysis['technical_score'],
                        'confidence': growth_analysis['confidence'],
                        'reasons': growth_analysis['reasons'],
                        'market_cap': market_cap,
                        'volume_ratio': technical_data.get('volume_ratio', 1),
                        'momentum_30d': technical_data.get('momentum_30d', 0),
                        'rsi': technical_data.get('rsi', 50),
                        'days_to_hold': min(30, max(7, 30 - int(growth_analysis['growth_score'] / 10))),
                        'risk_level': min(5, max(1, int(technical_data.get('volatility', 0.3) * 10))),
                        'category_name': self._categorize_stock(growth_analysis['growth_potential'], growth_analysis['confidence']),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    qualified_stocks.append(stock_analysis)
                    self.logger.info(f"✅ {ticker}: {growth_analysis['growth_potential']:.1f}% upside potential")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error screening {ticker}: {e}")
                continue
        
        # Sort by growth potential
        qualified_stocks.sort(key=lambda x: x['upside_potential'], reverse=True)
        
        return qualified_stocks

    def _categorize_stock(self, growth_potential: float, confidence: float) -> str:
        """Categorize stock based on growth potential and confidence"""
        if growth_potential >= 40 and confidence >= 70:
            return "High Potential"
        elif growth_potential >= 30 and confidence >= 60:
            return "Strong Growth"
        elif growth_potential >= 20 and confidence >= 50:
            return "Moderate Growth"
        else:
            return "Speculative"

    def get_watchlist_tickers(self) -> List[str]:
        """
        Get a comprehensive list of tickers to screen for growth opportunities
        
        Returns:
            List of ticker symbols to analyze
        """
        # Base watchlist of penny stocks and growth candidates
        base_tickers = [
            # Penny stocks with potential
            'SNDL', 'TLRY', 'ACB', 'HEXO', 'OGI', 'CRON', 'CGC',
            'NIO', 'XPEV', 'LI', 'NKLA', 'RIDE', 'FSR', 'LCID',
            'AMC', 'GME', 'BB', 'NOK', 'CLOV', 'WISH', 'SOFI',
            'PLTR', 'SPCE', 'BNGO', 'OCGN', 'SENS', 'ATOS', 'CTXR',
            'WKHS', 'HYLN', 'SOLO', 'AYRO', 'BLNK', 'CHPT', 'PLUG',
            'FCEL', 'BLDP', 'CLNE', 'GEVO', 'KOSS', 'EXPR', 'NAKD',
            
            # High growth potential stocks under $50
            'AMD', 'NVDA', 'TSLA', 'ROKU', 'SQ', 'PYPL', 'ZM', 'DOCU',
            'CRWD', 'OKTA', 'TWLO', 'SHOP', 'SNAP', 'PINS', 'UBER',
            'LYFT', 'SPOT', 'NET', 'DDOG', 'SNOW', 'PLTR', 'RBLX',
            
            # Biotech and pharma with catalysts
            'MRNA', 'BNTX', 'NVAX', 'INO', 'VXRT', 'IBIO', 'CODX',
            'DVAX', 'ADMA', 'SESN', 'TRIL', 'DARE', 'OBSV', 'JAGX'
        ]
        
        return base_tickers

    def live_research_scan(self) -> Dict:
        """
        Perform live research scan for 20%+ growth opportunities
        
        Returns:
            Dictionary with scan results and metadata
        """
        start_time = time.time()
        self.logger.info("🔍 Starting live research scan for 20%+ growth opportunities")
        
        # Get ticker list
        ticker_list = self.get_watchlist_tickers()
        self.logger.info(f"Screening {len(ticker_list)} tickers")
        
        # Screen for growth stocks
        qualified_stocks = self.screen_for_growth_stocks(ticker_list)
        
        scan_duration = time.time() - start_time
        
        # Prepare results
        results = {
            'scan_timestamp': datetime.now().isoformat(),
            'scan_duration_seconds': round(scan_duration, 2),
            'total_screened': len(ticker_list),
            'qualified_count': len(qualified_stocks),
            'picks': qualified_stocks[:20],  # Top 20 picks
            'criteria': {
                'min_growth_potential': self.growth_criteria['min_growth_potential'],
                'max_price': self.growth_criteria['max_price'],
                'min_confidence': 50
            },
            'data_sources': ['Yahoo Finance', 'Technical Analysis', 'Fundamental Analysis'],
            'next_scan_recommended': (datetime.now() + timedelta(hours=4)).isoformat()
        }
        
        self.logger.info(f"✅ Scan complete: {len(qualified_stocks)} stocks with 20%+ potential found in {scan_duration:.1f}s")
        
        return results
    
    def clear_cache(self):
        """
        Clear all cached stock data
        
        This is useful when you want to force fresh data retrieval,
        such as during market hours or after significant time has passed.
        """
        if hasattr(self.get_stock_data, 'clear_cache'):
            self.get_stock_data.clear_cache()
            self.logger.info("Stock data cache cleared")
    
    def get_cache_info(self) -> Dict[str, any]:
        """
        Get information about the current cache state
        
        Returns:
            Dictionary with cache statistics
        """
        # Since we're using a custom cache, we can't easily get stats
        # But we can at least indicate the cache settings
        return {
            'cache_ttl_seconds': 900,  # 15 minutes
            'max_cache_size': 100,
            'cache_type': 'TTL-based LRU cache'
        }

# Example usage and testing
if __name__ == "__main__":
    researcher = LiveStockResearcher()
    results = researcher.live_research_scan()
    
    print(f"\n🎯 LIVE RESEARCH RESULTS")
    print(f"Found {results['qualified_count']} stocks with 20%+ growth potential")
    print(f"Scan completed in {results['scan_duration_seconds']} seconds")
    
    print(f"\n📈 TOP GROWTH OPPORTUNITIES:")
    for i, stock in enumerate(results['picks'][:10], 1):
        print(f"{i:2}. {stock['ticker']:6} ${stock['current_price']:6.2f} → ${stock['target_price']:6.2f} ({stock['upside_potential']:+5.1f}%)")