#!/usr/bin/env python3
"""
Multi-Price Range Stock Analysis Web Application - Real Data Version
Flask web app that provides comprehensive stock analysis across different price ranges
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import threading
import time
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

# Global variables to store analysis results
current_analysis = None
analysis_in_progress = False
analysis_thread = None

class MultiPriceStockAnalyzer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"outputs/stock_analysis_{self.timestamp}"
        self.phase_dirs = [f"{self.output_dir}/phase{i}" for i in range(1, 6)]
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        for phase_dir in self.phase_dirs:
            os.makedirs(phase_dir, exist_ok=True)
    
    def get_stock_universe(self):
        """Phase 1: Collect multi-price range stock universe"""
        print("Phase 1: Collecting multi-price range stock universe...")
        
        # Expanded list of potential stocks across all price ranges
        candidate_tickers = [
            # Under $5 stocks
            'SNDL', 'NOK', 'F', 'BBD', 'TLRY', 'NIO', 'RIDE', 'WKHS', 'WISH', 'CLOV', 
            'AMC', 'GME', 'BB', 'NAKD', 'ATOS', 'CTXR', 'OBSV', 'GNUS', 'ZSAN', 'IDEX', 
            'XELA', 'SENS', 'SAVA', 'CLVS', 'ADTX', 'BNGO', 'OCGN', 'PROG', 'HYMC', 'MULN',
            'CEI', 'MMTLP', 'BBIG', 'SPRT', 'VINC', 'EEGI', 'TSNP', 'OZSC', 'SNPW', 'OPTI',
            'UAPC', 'TXHD', 'IFAN', 'CRYBF', 'MINE', 'WDLF', 'SIRC', 'HMBL', 'RGBP', 'INND',
            'DPLS', 'AITX', 'IBIO', 'JAGX', 'VISL', 'XSPA', 'EXPR', 'SKLZ', 'MRIN', 'RELI',
            
            # $5-$10 stocks  
            'SOFI', 'PLTR', 'HOOD', 'WISH', 'ROOT', 'CLOV', 'SKLZ', 'OPEN', 'DKNG', 'SPCE',
            'LCID', 'RIVN', 'ABNB', 'COIN', 'RBLX', 'PATH', 'UPST', 'AFRM', 'SQ', 'PYPL',
            'ROKU', 'SNAP', 'TWTR', 'UBER', 'LYFT', 'PINS', 'ZM', 'DOCU', 'CRWD', 'OKTA',
            'SNOW', 'NET', 'DDOG', 'MDB', 'ZS', 'TEAM', 'WDAY', 'NOW', 'CRM', 'ADBE',
            
            # $10-$20 stocks
            'AMD', 'INTC', 'NVDA', 'TSM', 'QCOM', 'AVGO', 'TXN', 'ADI', 'MRVL', 'XLNX',
            'MU', 'WDC', 'STX', 'NXPI', 'MCHP', 'KLAC', 'LRCX', 'AMAT', 'ASML', 'TSM',
            'BABA', 'JD', 'PDD', 'BIDU', 'NTES', 'TME', 'BILI', 'IQ', 'VIPS', 'WB',
            'SE', 'GRAB', 'DIDI', 'BEKE', 'EDU', 'TAL', 'YMM', 'DOYU', 'HUYA', 'MOMO'
        ]
        
        all_stocks = []
        print(f"Analyzing {len(candidate_tickers)} candidate stocks across all price ranges...")
        
        for ticker in candidate_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                market_cap = info.get('marketCap', 0)
                
                # Multi-price range classification
                if current_price and current_price < 20.0 and market_cap > 1000000:
                    category = self.classify_stock_category(current_price, market_cap)
                    all_stocks.append({
                        'ticker': ticker,
                        'price': current_price,
                        'market_cap': market_cap,
                        'sector': info.get('sector', 'Unknown'),
                        'industry': info.get('industry', 'Unknown'),
                        'category': category['category'],
                        'category_name': category['name'],
                        'risk_level': category['risk_level']
                    })
                    print(f"  ✓ {ticker}: ${current_price:.2f} (Market Cap: ${market_cap:,}) - {category['name']}")
                
            except Exception as e:
                print(f"  ✗ Error processing {ticker}: {e}")
                continue
        
        # Save to phase1 directory
        with open(f"{self.phase_dirs[0]}/stock_universe.json", 'w') as f:
            json.dump(all_stocks, f, indent=2)
        
        print(f"Found {len(all_stocks)} qualifying stocks across all price ranges")
        return all_stocks
    
    def classify_stock_category(self, price, market_cap):
        """Classify stocks into price-based categories"""
        if price < 5.0:
            return {
                'category': 'under-5',
                'name': 'Ultra-Small Cap Stock',
                'risk_level': 5,
                'description': 'Highest risk, highest potential reward',
                'typical_hold': '15-60 days',
                'strategy': 'High-Risk Growth'
            }
        elif price < 10.0:
            return {
                'category': '5-to-10',
                'name': 'Small Cap Stock',
                'risk_level': 3,
                'description': 'Moderate risk, good reward potential',
                'typical_hold': '30-120 days',
                'strategy': 'Growth & Momentum'
            }
        else:  # price < 20.0
            return {
                'category': '10-to-20',
                'name': 'Mid-Small Cap Stock',
                'risk_level': 2,
                'description': 'Lower risk, steady growth potential',
                'typical_hold': '60-180 days',
                'strategy': 'Value & Quality Growth'
            }
    
    def perform_technical_analysis(self, stock_data):
        """Phase 2: Real technical analysis"""
        print("Phase 2: Performing technical analysis...")
        
        technical_scores = {}
        
        for stock in stock_data:
            ticker = stock['ticker']
            try:
                print(f"  Analyzing {ticker}...")
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                
                if len(hist) < 50:
                    print(f"    ✗ Insufficient data for {ticker}")
                    continue
                
                # Calculate technical indicators
                hist['SMA_10'] = hist['Close'].rolling(window=10).mean()
                hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                
                # RSI calculation
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
                
                # Volume analysis
                avg_volume = hist['Volume'].rolling(window=20).mean()
                recent_volume = hist['Volume'].tail(5).mean()
                volume_ratio = recent_volume / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 0
                
                # Price momentum
                price_momentum = hist['Close'].pct_change().tail(10).mean()
                
                # Technical scoring
                current_price = hist['Close'].iloc[-1]
                sma_20 = hist['SMA_20'].iloc[-1]
                rsi = hist['RSI'].iloc[-1]
                
                score = 0
                if not pd.isna(sma_20) and current_price > sma_20:
                    score += 25
                if not pd.isna(rsi) and 30 < rsi < 70:
                    score += 25
                if volume_ratio > 1.1:
                    score += 25
                if price_momentum > 0:
                    score += 25
                
                technical_scores[ticker] = {
                    'score': min(score, 100),
                    'rsi': float(rsi) if not pd.isna(rsi) else None,
                    'volume_ratio': float(volume_ratio),
                    'price_momentum': float(price_momentum),
                    'current_price': float(current_price),
                    'sma_20': float(sma_20) if not pd.isna(sma_20) else None
                }
                
                print(f"    ✓ {ticker} technical score: {score}")
                
            except Exception as e:
                print(f"    ✗ Error analyzing {ticker}: {e}")
                continue
        
        # Save results
        with open(f"{self.phase_dirs[1]}/technical_analysis.json", 'w') as f:
            json.dump(technical_scores, f, indent=2)
        
        return technical_scores
    
    def perform_fundamental_analysis(self, stock_data):
        """Phase 3: Real fundamental analysis"""
        print("Phase 3: Performing fundamental analysis...")
        
        fundamental_scores = {}
        
        for stock in stock_data:
            ticker = stock['ticker']
            try:
                print(f"  Analyzing {ticker} fundamentals...")
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Extract key metrics
                revenue_growth = info.get('revenueGrowth', 0) or 0
                profit_margins = info.get('profitMargins', 0) or 0
                debt_to_equity = info.get('debtToEquity', 0) or 0
                current_ratio = info.get('currentRatio', 0) or 0
                operating_margins = info.get('operatingMargins', 0) or 0
                
                # Fundamental scoring
                score = 0
                if revenue_growth > 0.1:  # 10% revenue growth
                    score += 20
                if profit_margins > 0:
                    score += 20
                if debt_to_equity < 0.5 or debt_to_equity == 0:  # Low debt
                    score += 20
                if current_ratio > 1.5:  # Good liquidity
                    score += 20
                if operating_margins > 0:
                    score += 20
                
                fundamental_scores[ticker] = {
                    'score': min(score, 100),
                    'revenue_growth': float(revenue_growth),
                    'profit_margins': float(profit_margins),
                    'debt_to_equity': float(debt_to_equity),
                    'current_ratio': float(current_ratio),
                    'operating_margins': float(operating_margins)
                }
                
                print(f"    ✓ {ticker} fundamental score: {score}")
                
            except Exception as e:
                print(f"    ✗ Error analyzing {ticker}: {e}")
                continue
        
        # Save results
        with open(f"{self.phase_dirs[2]}/fundamental_analysis.json", 'w') as f:
            json.dump(fundamental_scores, f, indent=2)
        
        return fundamental_scores
    
    def analyze_sentiment(self, stock_data):
        """Phase 4: Basic sentiment analysis"""
        print("Phase 4: Analyzing sentiment...")
        
        sentiment_scores = {}
        
        for stock in stock_data:
            ticker = stock['ticker']
            try:
                # Basic sentiment analysis (can be enhanced with news APIs)
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Use analyst recommendations as sentiment proxy
                recommendation = info.get('recommendationKey', 'hold')
                
                score = 50  # Neutral baseline
                if recommendation in ['strongBuy', 'buy']:
                    score = 80
                elif recommendation in ['strongSell', 'sell']:
                    score = 20
                
                sentiment_scores[ticker] = {
                    'score': score,
                    'recommendation': recommendation,
                    'analyst_rating': recommendation
                }
                
                print(f"    ✓ {ticker} sentiment score: {score}")
                
            except Exception as e:
                print(f"    ✗ Error analyzing {ticker}: {e}")
                sentiment_scores[ticker] = {
                    'score': 50,
                    'recommendation': 'hold',
                    'analyst_rating': 'hold'
                }
        
        # Save results
        with open(f"{self.phase_dirs[3]}/sentiment_analysis.json", 'w') as f:
            json.dump(sentiment_scores, f, indent=2)
        
        return sentiment_scores
    
    def generate_final_rankings(self, stock_data, technical_scores, fundamental_scores, sentiment_scores):
        """Phase 5: Generate final rankings with category-specific scoring and holding periods"""
        print("Phase 5: Generating final rankings with category-specific scoring...")
        
        final_scores = []
        
        for stock in stock_data:
            ticker = stock['ticker']
            category = stock['category']
            category_name = stock['category_name']
            risk_level = stock['risk_level']
            
            tech_score = technical_scores.get(ticker, {}).get('score', 0)
            fund_score = fundamental_scores.get(ticker, {}).get('score', 0)
            sent_score = sentiment_scores.get(ticker, {}).get('score', 0)
            
            # Category-specific weighted composite score
            if category == 'under-5':  # Under $5 - favor technical (high risk)
                composite_score = (tech_score * 0.6 + fund_score * 0.25 + sent_score * 0.15)
            elif category == '5-to-10':  # $5-$10 - balanced approach
                composite_score = (tech_score * 0.45 + fund_score * 0.4 + sent_score * 0.15)
            else:  # $10-$20 - favor fundamentals (lower risk)
                composite_score = (tech_score * 0.3 + fund_score * 0.55 + sent_score * 0.15)
            
            # Get current price and calculate target
            try:
                yf_stock = yf.Ticker(ticker)
                info = yf_stock.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                
                # Category-adjusted target calculation
                base_multiplier = {'under-5': 500, '5-to-10': 400, '10-to-20': 350}[category]
                target_multiplier = 1 + (composite_score / base_multiplier)
                target_price = current_price * target_multiplier
                upside_potential = (target_price - current_price) / current_price * 100
                
                # Calculate optimal holding period
                category_info = self.classify_stock_category(current_price, stock.get('market_cap', 0))
                technical_data = technical_scores.get(ticker, {})
                holding_period = self.calculate_optimal_holding_period(
                    ticker, tech_score, fund_score, category_info, technical_data
                )
                
                # Generate investment rationale
                rationale = self.generate_investment_rationale(
                    ticker, tech_score, fund_score, sent_score, composite_score, upside_potential
                )
                
                # Position sizing recommendation
                position_size = {'under-5': "1-3%", '5-to-10': "3-6%", '10-to-20': "5-10%"}[category]
                
                final_scores.append({
                    'ticker': ticker,
                    'composite_score': round(composite_score, 1),
                    'current_price': round(current_price, 2),
                    'target_price': round(target_price, 2),
                    'upside_potential': round(upside_potential, 1),
                    'technical_score': round(tech_score, 1),
                    'fundamental_score': round(fund_score, 1),
                    'sentiment_score': round(sent_score, 1),
                    'category': category,
                    'category_name': category_name,
                    'risk_level': risk_level,
                    'strategy': category_info['strategy'],
                    'optimal_hold': holding_period['period_text'],
                    'exit_window': holding_period['exit_window'],
                    'hold_confidence': holding_period['confidence'],
                    'position_size': position_size,
                    'rationale': rationale,
                    'exchange': self.get_stock_exchange(ticker)
                })
                
                print(f"    ✓ {ticker}: Score {composite_score:.1f}, Target ${target_price:.2f}")
                
            except Exception as e:
                print(f"    ✗ Error calculating final score for {ticker}: {e}")
                continue
        
        # Generate category-specific rankings
        category_rankings = self.generate_category_rankings(final_scores)
        
        # Save results
        with open(f"{self.phase_dirs[4]}/final_rankings.json", 'w') as f:
            json.dump(category_rankings, f, indent=2)
        
        print(f"Category rankings generated successfully!")
        return category_rankings
    
    def generate_category_rankings(self, all_stocks):
        """Generate top 10 rankings for each price category"""
        print("Generating top 10 rankings for each price category...")
        
        # Separate stocks by category
        under_5_stocks = [stock for stock in all_stocks if stock['category'] == 'under-5']
        five_to_10_stocks = [stock for stock in all_stocks if stock['category'] == '5-to-10']
        ten_to_20_stocks = [stock for stock in all_stocks if stock['category'] == '10-to-20']
        
        # Sort each category by upside_potential (highest return first)
        under_5_stocks.sort(key=lambda x: x['upside_potential'], reverse=True)
        five_to_10_stocks.sort(key=lambda x: x['upside_potential'], reverse=True)
        ten_to_20_stocks.sort(key=lambda x: x['upside_potential'], reverse=True)
        
        # Get top 10 for each category
        under_5_top_10 = under_5_stocks[:min(10, len(under_5_stocks))]
        five_to_10_top_10 = five_to_10_stocks[:min(10, len(five_to_10_stocks))]
        ten_to_20_top_10 = ten_to_20_stocks[:min(10, len(ten_to_20_stocks))]
        
        print(f"  Under $5: {len(under_5_top_10)} stocks")
        print(f"  $5-$10: {len(five_to_10_top_10)} stocks")
        print(f"  $10-$20: {len(ten_to_20_top_10)} stocks")
        
        return {
            'under_5_picks': under_5_top_10,
            '5_to_10_picks': five_to_10_top_10,
            '10_to_20_picks': ten_to_20_top_10,
            'category_breakdown': self.calculate_category_breakdown(all_stocks),
            'total_analyzed': len(all_stocks)
        }
    
    def generate_investment_rationale(self, ticker, tech_score, fund_score, sent_score, composite_score, upside_potential):
        """Generate detailed investment rationale for a stock"""
        rationale = f"{ticker} is recommended based on our comprehensive analysis:\n\n"
        
        # Technical analysis rationale
        if tech_score >= 75:
            rationale += "🔹 STRONG TECHNICAL SIGNALS: Excellent technical setup with positive momentum, favorable volume patterns, and strong price trends above moving averages.\n\n"
        elif tech_score >= 50:
            rationale += "🔹 POSITIVE TECHNICAL OUTLOOK: Good technical indicators suggest potential for upward price movement with some favorable signals.\n\n"
        else:
            rationale += "🔹 MIXED TECHNICAL SIGNALS: Technical indicators show neutral conditions, suggesting price action may depend on other factors.\n\n"
        
        # Fundamental analysis rationale
        if fund_score >= 60:
            rationale += "💰 SOLID FUNDAMENTALS: Strong financial position with good revenue growth, healthy profit margins, manageable debt levels, and adequate liquidity.\n\n"
        elif fund_score >= 40:
            rationale += "💼 ADEQUATE FUNDAMENTALS: Reasonable financial metrics with some positive factors supporting the investment thesis.\n\n"
        else:
            rationale += "⚠️ SPECULATIVE PLAY: Lower fundamental score indicates higher risk, but potential for significant upside if company executes on growth plans.\n\n"
        
        # Sentiment rationale
        if sent_score >= 70:
            rationale += "📈 POSITIVE SENTIMENT: Analysts and market participants have a favorable view with buy recommendations supporting the bullish case.\n\n"
        else:
            rationale += "📊 NEUTRAL SENTIMENT: Market sentiment is balanced, providing opportunity for positive surprise from good news or execution.\n\n"
        
        # Overall investment thesis
        if composite_score >= 60:
            rationale += f"🎯 INVESTMENT THESIS: With a composite score of {composite_score:.1f}/100, this stock represents a compelling opportunity with {upside_potential:.1f}% projected upside. The combination of technical momentum and fundamental strength creates an attractive risk-reward profile for penny stock investors."
        else:
            rationale += f"💡 SPECULATIVE OPPORTUNITY: Composite score of {composite_score:.1f}/100 indicates moderate potential with {upside_potential:.1f}% upside. This represents a higher-risk play that could benefit significantly from positive catalysts or improved execution."
        
        return rationale
    
    def get_stock_exchange(self, ticker):
        """Determine the most likely exchange for a ticker"""
        # Common NASDAQ tickers
        nasdaq_tickers = {
            'SNDL', 'TLRY', 'NIO', 'WKHS', 'CLOV', 'AMC', 'ATOS', 'CTXR', 
            'SENS', 'SAVA', 'BNGO', 'OCGN', 'MULN', 'EXPR', 'SKLZ'
        }
        
        # Common NYSE tickers
        nyse_tickers = {
            'NOK', 'BBD', 'F', 'BB'
        }
        
        if ticker in nasdaq_tickers:
            return 'NASDAQ'
        elif ticker in nyse_tickers:
            return 'NYSE'
        else:
            # Default assumption for penny stocks
            return 'NASDAQ'
    
    def calculate_optimal_holding_period(self, ticker, tech_score, fund_score, category_info, technical_data):
        """Calculate optimal holding period based on momentum sustainability and catalysts"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            
            if len(hist) < 60:
                return {
                    'period_text': category_info['typical_hold'],
                    'exit_window': 'N/A',
                    'reason': 'Insufficient data',
                    'confidence': 30
                }
            
            # Analyze momentum sustainability
            rsi = technical_data.get('rsi', 50)
            volume_ratio = technical_data.get('volume_ratio', 1.0)
            price_momentum = technical_data.get('price_momentum', 0)
            
            # Base holding period on category
            base_days = {'under-5': 30, '5-to-10': 60, '10-to-20': 120}[category_info['category']]
            
            # Adjust based on technical momentum strength
            momentum_score = (tech_score + fund_score) / 2
            
            if momentum_score >= 80:  # Strong momentum
                multiplier = 1.5
                reason = "Strong momentum indicators suggest extended uptrend"
            elif momentum_score >= 60:  # Good momentum
                multiplier = 1.2
                reason = "Good momentum with sustainable technical setup"
            elif momentum_score >= 40:  # Moderate momentum
                multiplier = 1.0
                reason = "Moderate momentum requires standard holding period"
            else:  # Weak momentum
                multiplier = 0.7
                reason = "Weak momentum suggests shorter holding period"
            
            # RSI adjustments
            if rsi > 70:  # Overbought
                multiplier *= 0.8
                reason += "; overbought conditions may limit upside"
            elif rsi < 30:  # Oversold
                multiplier *= 1.3
                reason += "; oversold conditions suggest strong bounce potential"
            
            # Volume adjustments
            if volume_ratio > 2.0:  # High volume
                multiplier *= 1.1
                reason += "; high volume supports momentum"
            elif volume_ratio < 0.8:  # Low volume
                multiplier *= 0.9
                reason += "; low volume may indicate weaker momentum"
            
            # Calculate final holding period
            optimal_days = int(base_days * multiplier)
            optimal_days = max(15, min(optimal_days, 180))  # Clamp between 15-180 days
            
            # Format output
            if optimal_days < 30:
                period_text = f"{optimal_days} days"
                window_text = f"Day {max(1, optimal_days-7)}-{optimal_days+7}"
            elif optimal_days < 60:
                period_text = f"{optimal_days} days"
                window_text = f"Day {optimal_days-10}-{optimal_days+10}"
            else:
                period_text = f"{optimal_days} days"
                window_text = f"Day {optimal_days-15}-{optimal_days+15}"
            
            return {
                'optimal_days': optimal_days,
                'period_text': period_text,
                'exit_window': window_text,
                'reason': reason,
                'confidence': min(100, momentum_score + 10)
            }
            
        except Exception as e:
            print(f"Error calculating holding period for {ticker}: {e}")
            return {
                'optimal_days': base_days,
                'period_text': category_info['typical_hold'],
                'exit_window': f"Day {base_days-10}-{base_days+10}",
                'reason': "Standard category-based holding period",
                'confidence': 50
            }
    
    def calculate_category_breakdown(self, stock_data):
        """Calculate distribution of stocks across price categories"""
        breakdown = {'under-5': 0, '5-to-10': 0, '10-to-20': 0}
        for stock in stock_data:
            breakdown[stock['category']] += 1
        
        return {
            'under_5': {'count': breakdown['under-5'], 'name': 'Under $5 Stocks'},
            '5_to_10': {'count': breakdown['5-to-10'], 'name': '$5-$10 Stocks'},
            '10_to_20': {'count': breakdown['10-to-20'], 'name': '$10-$20 Stocks'},
            'total': len(stock_data)
        }
    
    def run_analysis(self):
        """Main analysis method with real data"""
        print("Starting Multi-Price Range Stock Analysis...")
        
        try:
            # Phase 1: Get stock universe with category classification
            stock_data = self.get_stock_universe()
            if not stock_data:
                raise Exception("No qualifying stocks found")
            
            # Phase 2: Technical analysis
            technical_scores = self.perform_technical_analysis(stock_data)
            
            # Phase 3: Fundamental analysis
            fundamental_scores = self.perform_fundamental_analysis(stock_data)
            
            # Phase 4: Sentiment analysis
            sentiment_scores = self.analyze_sentiment(stock_data)
            
            # Phase 5: Final rankings with category-specific scoring
            category_rankings = self.generate_final_rankings(
                stock_data, technical_scores, fundamental_scores, sentiment_scores
            )
            
            # Add additional data for backward compatibility and APIs
            result = category_rankings.copy()
            result.update({
                'technical_data': technical_scores,
                'fundamental_data': fundamental_scores,
                'sentiment_data': sentiment_scores,
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            raise e

@app.route('/')
def index():
    """Main page with analysis dashboard"""
    return render_template('index.html')

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    """Start a new penny stock analysis with real data"""
    global analysis_in_progress, analysis_thread
    
    try:
        if analysis_in_progress:
            return jsonify({
                'status': 'error',
                'message': 'Analysis already in progress'
            }), 400
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(target=run_background_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Real data analysis started',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error starting analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to start analysis: {str(e)}'
        }), 500

@app.route('/api/analysis-status')
def analysis_status():
    """Get current analysis status"""
    global analysis_in_progress, current_analysis
    
    return jsonify({
        'in_progress': analysis_in_progress,
        'has_results': current_analysis is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/results')
def get_results():
    """Get analysis results"""
    global current_analysis
    
    if current_analysis is None:
        return jsonify({
            'status': 'error',
            'message': 'No analysis results available'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': current_analysis,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stock/<ticker>')
def get_stock_details(ticker):
    """Get detailed information for a specific stock"""
    global current_analysis
    
    if current_analysis is None:
        return jsonify({
            'status': 'error',
            'message': 'No analysis data available'
        }), 404
    
    # Find stock in results
    stock_data = None
    for stock in current_analysis.get('top_10_picks', []):
        if stock['ticker'].upper() == ticker.upper():
            stock_data = stock
            break
    
    if stock_data is None:
        return jsonify({
            'status': 'error',
            'message': f'Stock {ticker} not found in analysis'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': stock_data
    })

@app.route('/dashboard')
def dashboard():
    """Analysis dashboard page"""
    return render_template('dashboard.html')

@app.route('/stock/<ticker>')
def stock_detail(ticker):
    """Individual stock detail page"""
    return render_template('stock_detail.html', ticker=ticker.upper())

@app.route('/category/<category>')
def category_page(category):
    """Price category page"""
    valid_categories = ['under-5', '5-to-10', '10-to-20']
    if category not in valid_categories:
        return "Category not found", 404
    return render_template('category.html', category=category)

@app.route('/api/category/<category>')
def get_category_data(category):
    """Get stocks for a specific price category"""
    global current_analysis
    
    if current_analysis is None:
        return jsonify({
            'status': 'error',
            'message': 'No analysis data available'
        }), 404
    
    valid_categories = ['under-5', '5-to-10', '10-to-20']
    if category not in valid_categories:
        return jsonify({
            'status': 'error',
            'message': 'Invalid category'
        }), 400
    
    # Get category-specific data
    category_key = f"{category.replace('-', '_')}_picks"
    category_data = current_analysis.get(category_key, [])
    
    return jsonify({
        'status': 'success',
        'data': {
            'category': category,
            'stocks': category_data,
            'count': len(category_data)
        }
    })

@app.route('/30-day-picks')
def thirty_day_picks():
    """30-day trading opportunity page"""
    return render_template('30_day_picks.html')

@app.route('/api/30-day-picks')
def get_thirty_day_picks():
    """Get top stocks under $10 for 30-day trading strategy"""
    global current_analysis
    
    if current_analysis is None:
        return jsonify({
            'status': 'error',
            'message': 'No analysis data available'
        }), 404
    
    # Combine under $5 and $5-$10 stocks (both under $10)
    under_5_stocks = current_analysis.get('under_5_picks', [])
    five_to_10_stocks = current_analysis.get('5_to_10_picks', [])
    
    # Filter for stocks with price < $10 and optimal holding period <= 30 days
    all_under_10 = under_5_stocks + five_to_10_stocks
    
    # Filter for 30-day opportunities
    thirty_day_candidates = []
    for stock in all_under_10:
        if stock['current_price'] < 10.0:
            # Check if optimal holding period is 30 days or less
            optimal_days = stock.get('optimal_days', 30)
            if 'days' in stock.get('optimal_hold', ''):
                try:
                    days_text = stock['optimal_hold'].split()[0]
                    optimal_days = int(days_text)
                except:
                    optimal_days = 30
            
            if optimal_days <= 45:  # Include stocks with up to 45-day holds for 30-day strategy
                # Add 30-day specific metrics
                stock_copy = stock.copy()
                stock_copy['days_to_hold'] = min(optimal_days, 30)
                stock_copy['trading_strategy'] = 'Short-Term Momentum'
                stock_copy['risk_warning'] = 'High volatility - suitable for day/swing trading'
                thirty_day_candidates.append(stock_copy)
    
    # Sort by upside potential (highest first) and take top 15
    thirty_day_candidates.sort(key=lambda x: x['upside_potential'], reverse=True)
    top_picks = thirty_day_candidates[:15]
    
    return jsonify({
        'status': 'success',
        'data': {
            'picks': top_picks,
            'count': len(top_picks),
            'strategy': '30-day momentum trading',
            'description': 'Stocks under $10 with highest short-term return potential'
        }
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Multi-Price Range Stock Analysis API'
    })

def run_background_analysis():
    """Run real analysis in background thread"""
    global analysis_in_progress, current_analysis
    
    try:
        analysis_in_progress = True
        print("Starting real background analysis...")
        
        # Create analyzer and run analysis
        analyzer = MultiPriceStockAnalyzer()
        result = analyzer.run_analysis()
        
        current_analysis = result
        print("Real background analysis completed successfully")
        
    except Exception as e:
        print(f"Error in real background analysis: {e}")
        current_analysis = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    
    finally:
        analysis_in_progress = False

if __name__ == '__main__':
    print("Starting Multi-Price Range Stock Analysis Web Application...")
    print("Access the application at: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)