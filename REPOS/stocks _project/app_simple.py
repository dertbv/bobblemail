#!/usr/bin/env python3
"""
Penny Stock Analysis Web Application (Simplified)
Flask web app that provides penny stock analysis through a web interface
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Global variables to store analysis results
current_analysis = None
analysis_in_progress = False
analysis_thread = None

# Sample data for demonstration
SAMPLE_STOCKS = [
    {
        'ticker': 'SNDL',
        'current_price': 2.45,
        'target_price': 3.20,
        'upside_potential': 30.6,
        'composite_score': 85.2,
        'technical_score': 88.0,
        'fundamental_score': 82.5,
        'sentiment_score': 85.0
    },
    {
        'ticker': 'NOK',
        'current_price': 4.12,
        'target_price': 5.50,
        'upside_potential': 33.5,
        'composite_score': 82.1,
        'technical_score': 85.0,
        'fundamental_score': 78.5,
        'sentiment_score': 82.8
    },
    {
        'ticker': 'PLTR',
        'current_price': 3.85,
        'target_price': 4.90,
        'upside_potential': 27.3,
        'composite_score': 79.8,
        'technical_score': 82.0,
        'fundamental_score': 76.5,
        'sentiment_score': 81.0
    }
]

@app.route('/')
def index():
    """Main page with analysis dashboard"""
    return render_template('index.html')

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    """Start a new penny stock analysis"""
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
            'message': 'Analysis started',
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

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Penny Stock Analysis API'
    })

def run_background_analysis():
    """Run analysis in background thread (simulated)"""
    global analysis_in_progress, current_analysis
    
    try:
        analysis_in_progress = True
        print("Starting background analysis (simulated)...")
        
        # Simulate analysis phases
        phases = [
            "Collecting penny stock universe...",
            "Performing technical analysis...", 
            "Analyzing fundamentals...",
            "Processing sentiment data...",
            "Generating final rankings..."
        ]
        
        for i, phase in enumerate(phases):
            print(f"Phase {i+1}: {phase}")
            time.sleep(2)  # Simulate work
        
        # Create sample analysis results
        current_analysis = {
            'timestamp': datetime.now().isoformat(),
            'top_10_picks': SAMPLE_STOCKS,
            'technical_data': {
                stock['ticker']: {
                    'rsi': 65.5,
                    'volume_ratio': 1.25,
                    'price_momentum': 0.05
                } for stock in SAMPLE_STOCKS
            },
            'fundamental_data': {
                stock['ticker']: {
                    'revenue_growth': 0.15,
                    'profit_margins': 0.08,
                    'debt_to_equity': 0.35,
                    'current_ratio': 1.8
                } for stock in SAMPLE_STOCKS
            },
            'sentiment_data': {
                stock['ticker']: {
                    'news_sentiment': 'positive',
                    'social_sentiment': 'neutral',
                    'analyst_rating': 'buy'
                } for stock in SAMPLE_STOCKS
            }
        }
        
        print("Background analysis completed successfully")
        
    except Exception as e:
        print(f"Error in background analysis: {e}")
        current_analysis = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    
    finally:
        analysis_in_progress = False

if __name__ == '__main__':
    print("Starting Penny Stock Analysis Web Application...")
    print("Access the application at: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)