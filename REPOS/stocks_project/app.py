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
import math
from run_penny_stock_analysis import PennyStockAnalyzer

app = Flask(__name__)

# Global variables to store analysis results
current_analysis = None
analysis_in_progress = False
analysis_thread = None
current_phase = 0
analysis_start_time = None
phase_times = []  # Track actual phase durations
phase_names = [
    "Discovering stocks...",
    "Analyzing technical indicators...", 
    "Evaluating financials...",
    "Processing market sentiment...",
    "Generating recommendations..."
]

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

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
    global analysis_in_progress, current_analysis, current_phase, phase_names, analysis_start_time
    
    # KISS: 35 second analysis divided by 10 = 3.5 second intervals
    if analysis_start_time and analysis_in_progress:
        elapsed_time = time.time() - analysis_start_time
        # Update progress every 3.5 seconds by 10%
        progress_percentage = min((elapsed_time / 3.5) * 10, 100)
    else:
        progress_percentage = 0
    
    return jsonify({
        'in_progress': analysis_in_progress,
        'has_results': current_analysis is not None,
        'current_phase': current_phase,
        'phase_name': phase_names[current_phase] if current_phase < len(phase_names) else "Completing...",
        'progress_percentage': round(progress_percentage),
        'timestamp': datetime.now().isoformat()
    })

def clean_nan_values(obj):
    """Recursively clean NaN values from nested dictionaries/lists"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return 0  # Replace NaN with 0
    return obj

@app.route('/api/results')
def get_results():
    """Get analysis results"""
    global current_analysis
    
    if current_analysis is None:
        return jsonify({
            'status': 'error',
            'message': 'No analysis results available'
        }), 404
    
    # Clean NaN values before returning
    cleaned_data = clean_nan_values(current_analysis)
    
    return jsonify({
        'status': 'success',
        'data': cleaned_data,
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


@app.route('/stock/<ticker>')
def stock_detail(ticker):
    """Individual stock detail page"""
    return render_template('stock_detail.html', ticker=ticker.upper())

@app.route('/category/<category>')
def category_view(category):
    """Category-specific stock listing page"""
    category_names = {
        'under-5': 'Under $5 Stocks',
        '5-to-10': '$5 - $10 Stocks', 
        '10-to-20': '$10 - $20 Stocks'
    }
    category_name = category_names.get(category, 'Stock Category')
    return render_template('category.html', category=category, category_name=category_name)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Penny Stock Analysis API'
    })

@app.route('/debug')
def debug():
    """Debug page"""
    with open('debug_dashboard.html', 'r') as f:
        return f.read()

@app.route('/test')
def test():
    """Test display page"""
    with open('test_display.html', 'r') as f:
        return f.read()

def update_phase_callback(phase):
    """Update current phase for progress tracking"""
    global current_phase, phase_times
    
    # Record time when phase changes
    current_time = time.time()
    if len(phase_times) <= phase:
        phase_times.append(current_time)
    else:
        phase_times[phase] = current_time
    
    current_phase = phase
    print(f"Phase {phase + 1}/5: {phase_names[phase]} (at {current_time:.2f}s)")

def run_background_analysis():
    """Run analysis in background thread"""
    global analysis_in_progress, current_analysis, current_phase, analysis_start_time, phase_times
    
    try:
        analysis_in_progress = True
        current_phase = 0
        analysis_start_time = time.time()
        phase_times = [analysis_start_time]  # Initialize with start time
        print(f"Starting background analysis at {analysis_start_time:.2f}s...")
        
        # Create analyzer instance
        analyzer = PennyStockAnalyzer()
        
        # Run analysis with manual phase tracking
        update_phase_callback(0)  # Phase 1: Stock discovery
        tickers = analyzer.get_penny_stock_universe()
        
        update_phase_callback(1)  # Phase 2: Technical analysis
        technical_scores = analyzer.perform_technical_analysis(tickers)
        
        update_phase_callback(2)  # Phase 3: Fundamental analysis  
        fundamental_scores = analyzer.perform_fundamental_analysis(tickers)
        
        update_phase_callback(3)  # Phase 4: Sentiment analysis
        sentiment_scores = analyzer.analyze_sentiment(tickers)
        
        update_phase_callback(4)  # Phase 5: Final rankings
        top_10_picks = analyzer.generate_final_rankings(tickers, technical_scores, 
                                                       fundamental_scores, sentiment_scores)
        
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
        
        # Record completion time and calculate phase durations
        completion_time = time.time()
        phase_times.append(completion_time)
        
        # Calculate and log phase durations
        total_duration = completion_time - analysis_start_time
        print(f"Background analysis completed successfully in {total_duration:.2f}s")
        print("Phase durations:")
        
        phase_durations = []
        for i in range(len(phase_times) - 1):
            duration = phase_times[i + 1] - phase_times[i]
            percentage = (duration / total_duration) * 100
            phase_durations.append(duration)
            print(f"  Phase {i + 1}: {duration:.2f}s ({percentage:.1f}%)")
        
        # Calculate cumulative percentages for progress ranges
        cumulative_percentages = [0]
        for duration in phase_durations:
            next_percentage = cumulative_percentages[-1] + (duration / total_duration) * 100
            cumulative_percentages.append(round(next_percentage))
        
        print(f"Suggested progress ranges: {list(zip(cumulative_percentages[:-1], cumulative_percentages[1:]))}")
        
        print("Background analysis completed successfully")
        
    except Exception as e:
        print(f"Error in background analysis: {e}")
        current_analysis = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    
    finally:
        analysis_in_progress = False
        current_phase = 0  # Reset phase when done
        analysis_start_time = None  # Reset start time
        # Keep phase_times for reference until next analysis

def load_previous_analysis():
    """Load the most recent analysis from disk"""
    global current_analysis
    try:
        # Find the most recent output directory
        import glob
        output_dirs = sorted(glob.glob("outputs/penny_stocks_*"))
        if output_dirs:
            latest_dir = output_dirs[-1]
            print(f"Loading previous analysis from: {latest_dir}")
            
            # Try to load rankings with holding data first
            try:
                with open(f"{latest_dir}/phase5/final_rankings_with_holding.json", 'r') as f:
                    top_picks = json.load(f)
                    print("Loaded rankings with holding period data")
            except FileNotFoundError:
                # Fall back to regular rankings
                with open(f"{latest_dir}/phase5/final_rankings.json", 'r') as f:
                    top_picks = json.load(f)
                    print("Loaded rankings without holding period data")
            
            # Load other phase data
            with open(f"{latest_dir}/phase2/technical_analysis.json", 'r') as f:
                technical_data = json.load(f)
            with open(f"{latest_dir}/phase3/fundamental_analysis.json", 'r') as f:
                fundamental_data = json.load(f)
            with open(f"{latest_dir}/phase4/sentiment_analysis.json", 'r') as f:
                sentiment_data = json.load(f)
            
            current_analysis = {
                'timestamp': datetime.now().isoformat(),
                'top_10_picks': top_picks,
                'technical_data': technical_data,
                'fundamental_data': fundamental_data,
                'sentiment_data': sentiment_data,
                'output_directory': latest_dir
            }
            print(f"Loaded {len(top_picks)} picks from previous analysis")
            return True
    except Exception as e:
        print(f"Error loading previous analysis: {e}")
    return False

if __name__ == '__main__':
    print("Starting Penny Stock Analysis Web Application...")
    print("Access the application at: http://localhost:8080")
    
    # Try to load previous analysis on startup
    if load_previous_analysis():
        print("Previous analysis loaded successfully")
    else:
        print("No previous analysis found")
    
    app.run(debug=True, host='0.0.0.0', port=8080)