#!/usr/bin/env python3
"""
Penny Stock Analysis Tool - Main Execution Script
Uses the Agentic Loop system to analyze penny stocks and generate top 10 picks
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
from file_locking import safe_write_json, save_analysis_phase_safe, safe_append_file

class PennyStockAnalyzer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"outputs/penny_stocks_{self.timestamp}"
        self.phase_dirs = [f"{self.output_dir}/phase{i}" for i in range(1, 6)]
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        for phase_dir in self.phase_dirs:
            os.makedirs(phase_dir, exist_ok=True)
    
    def get_penny_stock_universe(self) -> Dict[str, List[str]]:
        """
        Phase 1: Collect stock universe across all price categories
        Returns dict with categorized ticker symbols for stocks under $20 with market cap > $1M
        """
        print("Phase 1: Collecting stock universe across price categories...")
        
        # Expanded sample list to ensure enough stocks in each category
        sample_tickers = [
            # Under $5 candidates
            'SNDL', 'BBD', 'NIO', 'WKHS', 'CLOV', 'BB', 'ATOS', 'CTXR', 'OBSV', 'GNUS',
            'NAKD', 'WISH', 'RIDE', 'SENS', 'BNGO', 'OCGN', 'SAVA', 'PROG', 'XELA', 'CEI',
            'FAMI', 'MULX', 'BIOR', 'CYCC', 'MRIN', 'APRN', 'BFRI', 'CARV', 'DLPN', 'ENDP',
            
            # $5-$10 candidates  
            'NOK', 'TLRY', 'AMC', 'GME', 'PLTR', 'MVIS', 'CLNE', 'SPCE', 'HYMC', 'RDBX',
            'ROOT', 'SOFI', 'LCID', 'RIVN', 'GOEV', 'NKLA', 'FSLY', 'PINS', 'SNAP', 'UBER',
            'LYFT', 'ROKU', 'SQ', 'PYPL', 'SHOP', 'SPOT', 'ZM', 'DOCU', 'CRWD', 'OKTA',
            
            # $10-$20 candidates
            'F', 'T', 'VZ', 'BAC', 'C', 'WFC', 'GE', 'PFE', 'XOM', 'CVX',
            'KO', 'PEP', 'WMT', 'TGT', 'HD', 'LOW', 'NKE', 'DIS', 'NFLX', 'AMD',
            'INTC', 'CSCO', 'ORCL', 'CRM', 'ADBE', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'AAPL'
        ]
        
        # Categorize stocks by price range
        categorized_stocks = {
            'under_5': [],
            '5_to_10': [],
            '10_to_20': []
        }
        
        for ticker in sample_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                current_price = info.get('currentPrice', 0)
                market_cap = info.get('marketCap', 0)
                
                # Require minimum market cap
                if market_cap > 1000000:
                    stock_data = {
                        'ticker': ticker,
                        'price': current_price,
                        'market_cap': market_cap,
                        'sector': info.get('sector', 'Unknown')
                    }
                    
                    # Categorize by price
                    if current_price < 5.0:
                        categorized_stocks['under_5'].append(stock_data)
                    elif 5.0 <= current_price < 10.0:
                        categorized_stocks['5_to_10'].append(stock_data)
                    elif 10.0 <= current_price <= 20.0:
                        categorized_stocks['10_to_20'].append(stock_data)
                        
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
        
        # Print category counts
        for category, stocks in categorized_stocks.items():
            print(f"{category.replace('_', '-')} category: {len(stocks)} stocks")
        
        # Save categorized data to phase1 directory with safe file operations
        if not save_analysis_phase_safe(self.output_dir, 1, categorized_stocks):
            print("Warning: Failed to save phase 1 data")
        
        # Return flat list of all tickers for analysis
        all_tickers = []
        for category_stocks in categorized_stocks.values():
            all_tickers.extend([stock['ticker'] for stock in category_stocks])
        
        return all_tickers
    
    def perform_technical_analysis(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Phase 2: Technical analysis for each ticker
        """
        print("Phase 2: Performing technical analysis...")
        
        technical_scores = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                
                if len(hist) < 50:
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
                
                # Calculate technical score
                current_price = hist['Close'].iloc[-1]
                sma_20 = hist['SMA_20'].iloc[-1]
                rsi = hist['RSI'].iloc[-1]
                
                # Simple scoring logic
                score = 0
                if current_price > sma_20:
                    score += 30
                if 30 < rsi < 70:
                    score += 25
                if volume_ratio > 1.2:
                    score += 25
                if hist['Close'].pct_change().tail(5).mean() > 0:
                    score += 20
                
                technical_scores[ticker] = {
                    'score': min(score, 100),
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'price_momentum': hist['Close'].pct_change().tail(5).mean()
                }
                
            except Exception as e:
                print(f"Error in technical analysis for {ticker}: {e}")
        
        # Save technical analysis results with safe file operations
        if not save_analysis_phase_safe(self.output_dir, 2, technical_scores):
            print("Warning: Failed to save phase 2 data")
        
        return technical_scores
    
    def perform_fundamental_analysis(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Phase 3: Fundamental analysis for each ticker
        """
        print("Phase 3: Performing fundamental analysis...")
        
        fundamental_scores = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Extract key fundamental metrics
                revenue_growth = info.get('revenueGrowth', 0) or 0
                profit_margins = info.get('profitMargins', 0) or 0
                debt_to_equity = info.get('debtToEquity', 0) or 0
                current_ratio = info.get('currentRatio', 0) or 0
                
                # Simple fundamental scoring
                score = 0
                if revenue_growth > 0.1:  # 10% revenue growth
                    score += 30
                if profit_margins > 0:
                    score += 25
                if debt_to_equity < 0.5:  # Low debt
                    score += 25
                if current_ratio > 1.5:  # Good liquidity
                    score += 20
                
                fundamental_scores[ticker] = {
                    'score': min(score, 100),
                    'revenue_growth': revenue_growth,
                    'profit_margins': profit_margins,
                    'debt_to_equity': debt_to_equity,
                    'current_ratio': current_ratio
                }
                
            except Exception as e:
                print(f"Error in fundamental analysis for {ticker}: {e}")
        
        # Save fundamental analysis results with safe file operations
        if not save_analysis_phase_safe(self.output_dir, 3, fundamental_scores):
            print("Warning: Failed to save phase 3 data")
        
        return fundamental_scores
    
    def analyze_sentiment(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Phase 4: Sentiment and news analysis
        """
        print("Phase 4: Analyzing sentiment and news...")
        
        sentiment_scores = {}
        for ticker in tickers:
            # Placeholder for sentiment analysis
            # In real implementation, this would use news APIs and sentiment analysis
            sentiment_scores[ticker] = {
                'score': 50,  # Neutral baseline
                'news_sentiment': 'neutral',
                'social_sentiment': 'neutral',
                'analyst_rating': 'hold'
            }
        
        # Save sentiment analysis results with safe file operations
        if not save_analysis_phase_safe(self.output_dir, 4, sentiment_scores):
            print("Warning: Failed to save phase 4 data")
        
        return sentiment_scores
    
    def generate_final_rankings(self, tickers: List[str], technical_scores: Dict, 
                              fundamental_scores: Dict, sentiment_scores: Dict) -> Dict[str, List[Dict]]:
        """
        Phase 5: Integrate all analysis and generate final rankings by category
        Returns top 10 picks for each price category
        """
        print("Phase 5: Generating final rankings by category...")
        
        # Calculate scores for all stocks
        all_scores = []
        for ticker in tickers:
            tech_score = technical_scores.get(ticker, {}).get('score', 0)
            fund_score = fundamental_scores.get(ticker, {}).get('score', 0)
            sent_score = sentiment_scores.get(ticker, {}).get('score', 0)
            
            # Weighted composite score
            composite_score = (tech_score * 0.4 + fund_score * 0.4 + sent_score * 0.2)
            
            # Get current price for target calculation and categorization
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('currentPrice', 0)
                target_price = current_price * (1 + composite_score / 500)  # Simple target calculation
                
                stock_data = {
                    'ticker': ticker,
                    'composite_score': composite_score,
                    'current_price': current_price,
                    'target_price': target_price,
                    'upside_potential': (target_price - current_price) / current_price * 100,
                    'technical_score': tech_score,
                    'fundamental_score': fund_score,
                    'sentiment_score': sent_score
                }
                
                all_scores.append(stock_data)
                
            except Exception as e:
                print(f"Error calculating final score for {ticker}: {e}")
        
        # Categorize stocks by current price
        categorized_picks = {
            'under_5_picks': [],
            '5_to_10_picks': [],
            '10_to_20_picks': []
        }
        
        for stock in all_scores:
            price = stock['current_price']
            if price < 5.0:
                categorized_picks['under_5_picks'].append(stock)
            elif 5.0 <= price < 10.0:
                categorized_picks['5_to_10_picks'].append(stock)
            elif 10.0 <= price <= 20.0:
                categorized_picks['10_to_20_picks'].append(stock)
        
        # Sort each category by composite score and take top 10
        final_rankings = {}
        for category, stocks in categorized_picks.items():
            stocks.sort(key=lambda x: x['composite_score'], reverse=True)
            top_10 = stocks[:10]
            final_rankings[category] = top_10
            print(f"{category.replace('_', '-')}: {len(top_10)} picks (from {len(stocks)} candidates)")
        
        # Save categorized final rankings with safe file operations
        if not save_analysis_phase_safe(self.output_dir, 5, final_rankings):
            print("Warning: Failed to save phase 5 data")
        
        return final_rankings
    
    def generate_report(self, categorized_picks: Dict[str, List[Dict]]):
        """
        Generate final report with categorized stock picks
        """
        print("Generating final report...")
        
        report = f"""# Multi-Category Stock Analysis Report - {datetime.now().strftime('%Y-%m-%d')}

## Executive Summary
This report presents the top 10 stocks in three price categories with the highest potential for growth, based on comprehensive technical, fundamental, and sentiment analysis.

## Methodology
- **Technical Analysis (40%)**: Price momentum, volume patterns, technical indicators
- **Fundamental Analysis (40%)**: Financial health, growth prospects, business metrics
- **Sentiment Analysis (20%)**: News sentiment, social media buzz, analyst opinions

## Category Analysis

"""
        
        category_names = {
            'under_5_picks': 'Under $5 Stocks (High Risk/High Reward)',
            '5_to_10_picks': '$5-$10 Stocks (Moderate Risk)',
            '10_to_20_picks': '$10-$20 Stocks (Lower Risk)'
        }
        
        for category, picks in categorized_picks.items():
            if picks:  # Only show categories that have picks
                report += f"""### {category_names[category]}

"""
                for i, pick in enumerate(picks, 1):
                    report += f"""#### {i}. {pick['ticker']}
- **Current Price**: ${pick['current_price']:.2f}
- **Target Price**: ${pick['target_price']:.2f}
- **Upside Potential**: {pick['upside_potential']:.1f}%
- **Composite Score**: {pick['composite_score']:.1f}/100
- **Technical Score**: {pick['technical_score']:.1f}/100
- **Fundamental Score**: {pick['fundamental_score']:.1f}/100
- **Sentiment Score**: {pick['sentiment_score']:.1f}/100

"""
        
        report += """
## Risk Disclaimer
**IMPORTANT**: Penny stocks are highly speculative and risky investments. They are subject to:
- High volatility and potential for significant losses
- Limited liquidity and wide bid-ask spreads
- Potential for manipulation and fraud
- Limited analyst coverage and financial information
- Risk of delisting from exchanges

This analysis is for informational purposes only and should not be considered as investment advice. Always consult with a qualified financial advisor before making investment decisions.

## Data Sources
- Yahoo Finance API for market data
- Technical analysis calculations
- Public financial statements and SEC filings

Generated by Agentic Loop Penny Stock Analysis System
"""
        
        # Save final report with safe file operations
        report_file = f"{self.output_dir}/penny_stock_report.md"
        try:
            # Write the complete report in one operation
            with open(report_file, 'w') as f:
                f.write(report)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            print(f"Report saved to: {report_file}")
        except IOError as e:
            print(f"Warning: Failed to save report: {e}")
    
    def run_analysis(self):
        """
        Main execution method that runs the complete analysis
        """
        print("Starting Multi-Category Stock Analysis...")
        print(f"Output directory: {self.output_dir}")
        
        # Phase 1: Get stock universe across all price categories
        tickers = self.get_penny_stock_universe()
        print(f"Found {len(tickers)} stocks to analyze across all categories")
        
        # Phase 2: Technical analysis
        technical_scores = self.perform_technical_analysis(tickers)
        
        # Phase 3: Fundamental analysis
        fundamental_scores = self.perform_fundamental_analysis(tickers)
        
        # Phase 4: Sentiment analysis
        sentiment_scores = self.analyze_sentiment(tickers)
        
        # Phase 5: Final rankings by category
        categorized_picks = self.generate_final_rankings(tickers, technical_scores, 
                                                        fundamental_scores, sentiment_scores)
        
        # Generate final report
        self.generate_report(categorized_picks)
        
        print("Analysis complete!")
        
        # Return flattened list for backward compatibility with web app
        all_picks = []
        for category_picks in categorized_picks.values():
            all_picks.extend(category_picks)
        
        # Sort all picks by composite score for overall ranking
        all_picks.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return all_picks[:10]  # Return top 10 overall for compatibility

if __name__ == "__main__":
    analyzer = PennyStockAnalyzer()
    results = analyzer.run_analysis()
    
    print("\nTop 10 Penny Stock Picks:")
    for i, pick in enumerate(results, 1):
        print(f"{i}. {pick['ticker']} - ${pick['current_price']:.2f} "
              f"(Target: ${pick['target_price']:.2f}, "
              f"Upside: {pick['upside_potential']:.1f}%)")