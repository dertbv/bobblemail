#!/usr/bin/env python3
"""
Penny Stock Analysis Web Application
Flask web app that provides penny stock analysis through a web interface
"""

from flask import Flask, render_template, jsonify, request, g
import json
import os
from datetime import datetime
import threading
import time
from functools import lru_cache
from run_penny_stock_analysis import PennyStockAnalyzer
from validation import APIValidator, ValidationError, handle_validation_error
from file_locking import safe_read_json, safe_write_json, load_analysis_phase_safe, FileLockError
from logging_config import main_logger, log_api_call, log_analysis_phase, log_file_operation

app = Flask(__name__)

# Setup Flask logging
app.logger.handlers = main_logger.handlers
app.logger.setLevel(main_logger.level)

# Global variables to store analysis results
current_analysis = None
analysis_in_progress = False
analysis_thread = None

# Cache for analysis metadata to avoid repeated file system scans
_analysis_cache = {
    'last_check': None,
    'latest_dir': None,
    'cache_duration': 60  # Cache for 60 seconds
}

def get_latest_analysis_dir():
    """Get the latest analysis directory - NO CACHING"""
    output_dir = 'outputs'
    if not os.path.exists(output_dir):
        return None
    
    # Find the most recent analysis directory
    output_dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    if not output_dirs:
        return None
        
    # Sort by directory name (which includes timestamp) - most recent first
    output_dirs.sort(key=lambda x: x.split('_')[-1] if '_' in x else x, reverse=True)
    return output_dirs[0]

@log_file_operation(main_logger, 'load_analysis')
def load_most_recent_analysis():
    """Load the most recent analysis results from disk with memory optimization and file locking"""
    try:
        latest_dir = get_latest_analysis_dir()
        if not latest_dir:
            return None
            
        main_logger.info(f"Loading analysis from: {latest_dir}")
        
        # Try to load final rankings with safe file operations
        rankings_file = os.path.join('outputs', latest_dir, 'phase5', 'final_rankings.json')
        rankings = safe_read_json(rankings_file)
        
        if rankings is not None:
            
            # Handle different data formats
            if isinstance(rankings, list):
                # Simple list format (like penny_stocks_20250621_222219) - legacy format
                # Need to enrich with missing fields
                top_picks = []
                for i, pick in enumerate(rankings[:10]):
                    enriched_pick = dict(pick)  # Copy the original
                    
                    # Add missing fields that the frontend expects
                    enriched_pick['category'] = 'under-5' if pick['current_price'] < 5 else ('5-to-10' if pick['current_price'] < 10 else '10-to-20')
                    enriched_pick['category_name'] = 'Ultra-Small Cap Stock' if pick['current_price'] < 5 else ('Small Cap Stock' if pick['current_price'] < 10 else 'Mid-Small Cap Stock')
                    enriched_pick['risk_level'] = 5 if pick['current_price'] < 1 else (4 if pick['current_price'] < 5 else 3)
                    enriched_pick['strategy'] = 'High-Risk Growth' if pick['current_price'] < 5 else 'Growth Play'
                    enriched_pick['optimal_hold'] = '30-60 days'
                    enriched_pick['exit_window'] = 'Day 30-60'
                    enriched_pick['hold_confidence'] = 75.0
                    enriched_pick['position_size'] = '1-3%' if pick['current_price'] < 5 else '3-5%'
                    enriched_pick['exchange'] = 'NASDAQ'  # Default
                    
                    # Generate basic rationale
                    enriched_pick['rationale'] = f"{pick['ticker']} shows potential with {pick['composite_score']:.1f}/100 composite score and {pick['upside_potential']:.1f}% upside potential."
                    
                    top_picks.append(enriched_pick)
                    
            elif isinstance(rankings, dict):
                # New categorized format - return ALL picks from ALL categories (up to 30 total)
                top_picks = []
                for category_key in ['under_5_picks', '5_to_10_picks', '10_to_20_picks']:
                    if category_key in rankings:
                        category_picks = rankings[category_key]
                        # Enrich each pick with category information
                        for pick in category_picks:
                            enriched_pick = dict(pick)  # Copy the original
                            
                            # Add missing fields that the frontend expects
                            enriched_pick['category'] = category_key.replace('_picks', '').replace('_', '-')
                            enriched_pick['category_name'] = 'Ultra-Small Cap Stock' if pick['current_price'] < 5 else ('Small Cap Stock' if pick['current_price'] < 10 else 'Mid-Small Cap Stock')
                            enriched_pick['risk_level'] = 5 if pick['current_price'] < 1 else (4 if pick['current_price'] < 5 else 3)
                            enriched_pick['strategy'] = 'High-Risk Growth' if pick['current_price'] < 5 else 'Growth Play'
                            enriched_pick['optimal_hold'] = '30-60 days'
                            enriched_pick['exit_window'] = 'Day 30-60'
                            enriched_pick['hold_confidence'] = 75.0
                            enriched_pick['position_size'] = '1-3%' if pick['current_price'] < 5 else '3-5%'
                            enriched_pick['exchange'] = 'NASDAQ'  # Default
                            
                            # Generate basic rationale
                            enriched_pick['rationale'] = f"{pick['ticker']} shows potential with {pick['composite_score']:.1f}/100 composite score and {pick['upside_potential']:.1f}% upside potential."
                            
                            top_picks.append(enriched_pick)
                
                # Sort by composite score for overall display
                top_picks.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
            else:
                top_picks = []
            
            # Return data in the format the web app expects with proper timestamp
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            
            return {
                'status': 'complete',
                'top_10_picks': top_picks,
                'analysis_complete': True,
                'timestamp': timestamp,  # Use proper ISO timestamp instead of directory name
                'total_stocks_analyzed': len(top_picks)
            }
    except (FileLockError, IOError) as e:
        main_logger.error(f"File access error loading recent analysis: {e}", exc_info=True)
        return None
    except Exception as e:
        main_logger.error(f"Error loading recent analysis: {e}", exc_info=True)
        return None
    
    return None

@app.route('/')
@log_api_call(main_logger)
def index():
    """Main page with analysis dashboard"""
    return render_template('index.html')

@app.route('/api/start-analysis', methods=['POST'])
@log_api_call(main_logger)
def start_analysis():
    """Start a new penny stock analysis with validation"""
    try:
        # Validate request
        request_data = APIValidator.validate_analysis_request(request)
        
        global analysis_in_progress, analysis_thread
        
        if analysis_in_progress:
            return jsonify({
                'status': 'error',
                'message': 'Analysis already in progress'
            }), 409  # Conflict status code
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(target=run_background_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Analysis started',
            'timestamp': datetime.now().isoformat()
        })
        
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        main_logger.error(f"Unexpected error in start_analysis: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@app.route('/api/analysis-status')
@log_api_call(main_logger)
def analysis_status():
    """Get current analysis status"""
    global analysis_in_progress, current_analysis
    
    # Check if we have existing results even if no current analysis
    if current_analysis is None and not analysis_in_progress:
        recent_analysis = load_most_recent_analysis()
        has_results = recent_analysis is not None
    else:
        has_results = current_analysis is not None
    
    return jsonify({
        'in_progress': analysis_in_progress,
        'has_results': has_results,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/results')
@log_api_call(main_logger)
def get_results():
    """Get analysis results"""
    global current_analysis
    
    # If no current analysis, try to load the most recent one
    if current_analysis is None:
        current_analysis = load_most_recent_analysis()
    
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

def get_stock_from_analysis(ticker):
    """Efficiently get single stock data without loading full analysis with safe file operations"""
    latest_dir = get_latest_analysis_dir()
    if not latest_dir:
        return None
        
    try:
        rankings_file = os.path.join('outputs', latest_dir, 'phase5', 'final_rankings.json')
        rankings = safe_read_json(rankings_file)
        
        if rankings is not None:
            
            # Search for specific ticker without loading full dataset
            if isinstance(rankings, list):
                for stock in rankings[:10]:  # Only check top 10
                    if stock.get('ticker', '').upper() == ticker.upper():
                        return stock
            elif isinstance(rankings, dict):
                # Check all categories efficiently
                for category_key in ['under_5_picks', '5_to_10_picks', '10_to_20_picks']:
                    if category_key in rankings:
                        for stock in rankings[category_key]:
                            if stock.get('ticker', '').upper() == ticker.upper():
                                return stock
    except (FileLockError, IOError) as e:
        main_logger.error(f"File access error loading stock {ticker}: {e}", exc_info=True)
    except Exception as e:
        main_logger.error(f"Error loading stock {ticker}: {e}", exc_info=True)
    
    return None

@app.route('/api/stock/<ticker>')
@log_api_call(main_logger)
def get_stock_details(ticker):
    """Get detailed information for a specific stock with validation and memory optimization"""
    try:
        # Validate ticker format
        validated_ticker = APIValidator.validate_ticker(ticker)
        
        # Try to get from current analysis first
        global current_analysis
        
        if current_analysis is not None:
            for stock in current_analysis.get('top_10_picks', []):
                if stock['ticker'].upper() == validated_ticker:
                    return jsonify({
                        'status': 'success',
                        'data': stock
                    })
        
        # Fall back to direct file access for memory efficiency
        stock_data = get_stock_from_analysis(validated_ticker)
        if stock_data is None:
            return jsonify({
                'status': 'error',
                'message': f'Stock {validated_ticker} not found in analysis'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': stock_data
        })
        
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        print(f"Unexpected error in get_stock_details: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@app.route('/dashboard')
def dashboard():
    """Analysis dashboard page"""
    return render_template('dashboard.html')

@app.route('/stock/<ticker>')
def stock_detail(ticker):
    """Individual stock detail page with validation"""
    try:
        # Validate ticker
        validated_ticker = APIValidator.validate_ticker(ticker)
        return render_template('stock_detail.html', ticker=validated_ticker)
        
    except ValidationError:
        # For page routes, redirect to 404 instead of JSON error
        return render_template('404.html'), 404
    except Exception as e:
        print(f"Unexpected error in stock_detail: {e}")
        return render_template('500.html'), 500

@app.route('/category/<category_name>')
def category_page(category_name):
    """Category page for price ranges with validation"""
    try:
        # Validate category
        validated_category = APIValidator.validate_category(category_name)
        
        # Map category names to display titles
        category_map = {
            'under-5': {'title': 'Under $5 Stocks', 'description': 'Ultra-Small Cap stocks with highest risk/reward potential', 'min_price': 0, 'max_price': 5},
            '5-to-10': {'title': '$5 - $10 Stocks', 'description': 'Small Cap stocks with balanced risk/reward profile', 'min_price': 5, 'max_price': 10},
            '10-to-20': {'title': '$10 - $20 Stocks', 'description': 'Mid-Small Cap stocks with lower risk, steady growth', 'min_price': 10, 'max_price': 20}
        }
        
        category_info = category_map[validated_category]
        return render_template('category.html', 
                             category=validated_category,
                             title=category_info['title'],
                             description=category_info['description'],
                             min_price=category_info['min_price'],
                             max_price=category_info['max_price'])
        
    except ValidationError:
        # For page routes, redirect to 404 instead of JSON error
        return render_template('404.html'), 404
    except Exception as e:
        print(f"Unexpected error in category_page: {e}")
        return render_template('500.html'), 500

@app.route('/30-day-picks')
def thirty_day_picks():
    """30-day picks page"""
    return render_template('30_day_picks.html')

def get_category_data_optimized(category_name):
    """Get category data with memory optimization and safe file operations"""
    latest_dir = get_latest_analysis_dir()
    if not latest_dir:
        return None
        
    try:
        rankings_file = os.path.join('outputs', latest_dir, 'phase5', 'final_rankings.json')
        rankings = safe_read_json(rankings_file)
        
        if rankings is not None:
            
            # Define price filters for categories
            price_filters = {
                'under-5': lambda price: price < 5,
                '5-to-10': lambda price: 5 <= price < 10,
                '10-to-20': lambda price: 10 <= price <= 20
            }
            
            if category_name not in price_filters:
                return None
                
            filtered_picks = []
            
            if isinstance(rankings, list):
                # Filter list format efficiently
                for stock in rankings[:10]:
                    if price_filters[category_name](stock.get('current_price', 0)):
                        filtered_picks.append(stock)
            elif isinstance(rankings, dict):
                # Use pre-categorized data if available
                category_mappings = {
                    'under-5': 'under_5_picks',
                    '5-to-10': '5_to_10_picks', 
                    '10-to-20': '10_to_20_picks'
                }
                
                if category_mappings[category_name] in rankings:
                    filtered_picks = rankings[category_mappings[category_name]]
                else:
                    # Fall back to filtering all picks
                    all_picks = []
                    for key in ['under_5_picks', '5_to_10_picks', '10_to_20_picks']:
                        if key in rankings:
                            all_picks.extend(rankings[key])
                    
                    for stock in all_picks:
                        if price_filters[category_name](stock.get('current_price', 0)):
                            filtered_picks.append(stock)
            
            return {
                'picks': filtered_picks,
                'count': len(filtered_picks),
                'timestamp': datetime.now().isoformat()
            }
            
    except (FileLockError, IOError) as e:
        print(f"File access error loading category {category_name}: {e}")
    except Exception as e:
        print(f"Error loading category {category_name}: {e}")
    
    return None

@app.route('/api/category/<category_name>')
def get_category_data(category_name):
    """Get filtered stock data for a specific category with validation and memory optimization"""
    try:
        # Validate category
        validated_category = APIValidator.validate_category(category_name)
        
        # Try current analysis first
        global current_analysis
        if current_analysis is not None:
            price_filters = {
                'under-5': lambda price: price < 5,
                '5-to-10': lambda price: 5 <= price < 10,
                '10-to-20': lambda price: 10 <= price <= 20
            }
            
            all_picks = current_analysis.get('top_10_picks', [])
            filtered_picks = [pick for pick in all_picks if price_filters[validated_category](pick['current_price'])]
            
            return jsonify({
                'status': 'success',
                'category': validated_category,
                'data': {
                    'picks': filtered_picks,
                    'count': len(filtered_picks),
                    'timestamp': current_analysis.get('timestamp', datetime.now().isoformat())
                }
            })
        
        # Fall back to optimized file access
        category_data = get_category_data_optimized(validated_category)
        if category_data is None:
            return jsonify({
                'status': 'error',
                'message': 'No analysis results available'
            }), 404
        
        return jsonify({
            'status': 'success',
            'category': validated_category,
            'data': category_data
        })
        
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        print(f"Unexpected error in get_category_data: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@app.route('/api/health')
@log_api_call(main_logger)
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Penny Stock Analysis API'
    })

@log_analysis_phase(main_logger, 'background_analysis')
def run_background_analysis():
    """Run analysis in background thread"""
    global analysis_in_progress, current_analysis
    
    try:
        analysis_in_progress = True
        main_logger.info("Starting background analysis...")
        
        # No cache to clear - always gets latest directory
        
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
        
        # Enrich top_10_picks with missing fields that the frontend expects
        enriched_picks = []
        for i, pick in enumerate(top_10_picks[:10]):
            enriched_pick = dict(pick)  # Copy the original
            
            # Add missing fields that the frontend expects
            enriched_pick['category'] = 'under-5' if pick['current_price'] < 5 else ('5-to-10' if pick['current_price'] < 10 else '10-to-20')
            enriched_pick['category_name'] = 'Ultra-Small Cap Stock' if pick['current_price'] < 5 else ('Small Cap Stock' if pick['current_price'] < 10 else 'Mid-Small Cap Stock')
            enriched_pick['risk_level'] = 5 if pick['current_price'] < 1 else (4 if pick['current_price'] < 5 else 3)
            enriched_pick['strategy'] = 'High-Risk Growth' if pick['current_price'] < 5 else 'Growth Play'
            enriched_pick['optimal_hold'] = '30-60 days'
            enriched_pick['exit_window'] = 'Day 30-60'
            enriched_pick['hold_confidence'] = 75.0
            enriched_pick['position_size'] = '1-3%' if pick['current_price'] < 5 else '3-5%'
            enriched_pick['exchange'] = 'NASDAQ'  # Default
            
            # Generate basic rationale
            enriched_pick['rationale'] = f"{pick['ticker']} shows potential with {pick['composite_score']:.1f}/100 composite score and {pick['upside_potential']:.1f}% upside potential."
            
            enriched_picks.append(enriched_pick)

        # Combine all data
        current_analysis = {
            'timestamp': datetime.now().isoformat(),
            'top_10_picks': enriched_picks,
            'technical_data': technical_data,
            'fundamental_data': fundamental_data,
            'sentiment_data': sentiment_data,
            'output_directory': output_dir
        }
        
        main_logger.info("Background analysis completed successfully")
        
    except Exception as e:
        main_logger.error(f"Error in background analysis: {e}", exc_info=True)
        current_analysis = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    
    finally:
        analysis_in_progress = False

def clear_all_caches():
    """Clear all memory caches"""
    global current_analysis
    current_analysis = None
    main_logger.info("All caches cleared - no function caches to clear")

# Global error handlers
@app.errorhandler(ValidationError)
def handle_validation_error_global(error):
    """Global handler for validation errors"""
    return handle_validation_error(error)

@app.errorhandler(400)
def handle_bad_request(error):
    """Handle bad request errors"""
    main_logger.warning(f"Bad request: {request.path} - {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Bad request',
        'error_type': 'bad_request'
    }), 400

@app.errorhandler(403)
def handle_forbidden(error):
    """Handle forbidden access errors"""
    main_logger.warning(f"Forbidden access attempt: {request.path} from {request.remote_addr}")
    # Check if it's an API request
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Access forbidden',
            'error_type': 'forbidden'
        }), 403
    else:
        # For page requests, render 403 template
        return render_template('403.html'), 403

@app.errorhandler(404)
def handle_not_found(error):
    """Handle not found errors"""
    # Check if it's an API request
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found',
            'error_type': 'not_found'
        }), 404
    else:
        # For page requests, render 404 template
        return render_template('404_simple.html'), 404

@app.errorhandler(413)
def handle_request_too_large(error):
    """Handle request entity too large"""
    return jsonify({
        'status': 'error',
        'message': 'Request body too large',
        'error_type': 'request_too_large'
    }), 413

@app.errorhandler(415)
def handle_unsupported_media_type(error):
    """Handle unsupported media type"""
    return jsonify({
        'status': 'error',
        'message': 'Unsupported media type. Expected application/json',
        'error_type': 'unsupported_media_type'
    }), 415

@app.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors"""
    main_logger.error(f"Internal server error: {request.path} - {str(error)}", exc_info=True)
    
    # Check if it's an API request
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500
    else:
        # For page requests, render 500 template
        return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting Penny Stock Analysis Web Application...")
    print("Access the application at: http://localhost:5006")
    print("Memory optimization enabled with LRU caching")
    app.run(debug=True, host='0.0.0.0', port=5006)