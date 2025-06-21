#!/usr/bin/env python3
"""
Penny Stock Analysis Web Application
Flask web app that provides penny stock analysis through a web interface
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import threading
import time
from run_penny_stock_analysis import PennyStockAnalyzer

app = Flask(__name__)

# Global variables to store analysis results
current_analysis = None
analysis_in_progress = False
analysis_thread = None

@app.route('/')
def index():
    """Main page with analysis dashboard"""
    return render_template('index.html')

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    """Start a new penny stock analysis"""
    global analysis_in_progress, analysis_thread
    
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
    """Run analysis in background thread"""
    global analysis_in_progress, current_analysis
    
    try:
        analysis_in_progress = True
        print("Starting background analysis...")
        
        # Create analyzer instance
        analyzer = PennyStockAnalyzer()
        
        # Run analysis
        top_10_picks = analyzer.run_analysis()
        
        # Load additional data from phase files
        output_dir = analyzer.output_dir
        
        # Load technical analysis data
        technical_data = {}
        try:
            with open(f"{output_dir}/phase2/technical_analysis.json", 'r') as f:
                technical_data = json.load(f)
        except FileNotFoundError:
            pass
        
        # Load fundamental analysis data
        fundamental_data = {}
        try:
            with open(f"{output_dir}/phase3/fundamental_analysis.json", 'r') as f:
                fundamental_data = json.load(f)
        except FileNotFoundError:
            pass
        
        # Load sentiment analysis data
        sentiment_data = {}
        try:
            with open(f"{output_dir}/phase4/sentiment_analysis.json", 'r') as f:
                sentiment_data = json.load(f)
        except FileNotFoundError:
            pass
        
        # Combine all data
        current_analysis = {
            'timestamp': datetime.now().isoformat(),
            'top_10_picks': top_10_picks,
            'technical_data': technical_data,
            'fundamental_data': fundamental_data,
            'sentiment_data': sentiment_data,
            'output_directory': output_dir
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
    print("Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)