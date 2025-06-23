#!/usr/bin/env python3
"""
Production-Ready Stock Analysis Web Application
Consolidated, async-enhanced Flask app with proper architecture

This replaces the original app.py with:
- No duplicate code (consolidated from 3 apps)
- Proper state management (no global variables) 
- Non-blocking async operations
- Security improvements (debug=False, localhost-only)
- Better error handling and data integrity
"""

import os
import json
import time
import math
import concurrent.futures
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from flask import Flask, render_template, jsonify, request, redirect
from queue import Queue, Empty
import threading

# Import analysis engines
try:
    from run_penny_stock_analysis import PennyStockAnalyzer
    PENNY_ANALYZER_AVAILABLE = True
except ImportError:
    PENNY_ANALYZER_AVAILABLE = False
    print("Warning: PennyStockAnalyzer not available")

# Import live research system
try:
    from live_research_system import LiveStockResearcher
    LIVE_RESEARCH_AVAILABLE = True
except ImportError:
    LIVE_RESEARCH_AVAILABLE = False
    print("Warning: LiveStockResearcher not available")


@dataclass
class AnalysisState:
    """Application state management - no more global variables"""
    current_analysis: Optional[Dict[str, Any]] = None
    analysis_in_progress: bool = False
    current_phase: int = 0
    analysis_start_time: Optional[float] = None
    phase_times: List[float] = field(default_factory=list)
    executor: concurrent.futures.ThreadPoolExecutor = field(
        default_factory=lambda: concurrent.futures.ThreadPoolExecutor(max_workers=4)
    )
    analysis_task: Optional[concurrent.futures.Future] = None


class StockAnalysisApp:
    """Production-ready Stock Analysis Application"""
    
    def __init__(self):
        self.state = AnalysisState()
        self.app = Flask(__name__)
        self.phase_names = [
            "Discovering stocks...",
            "Analyzing technical indicators...", 
            "Evaluating financials...",
            "Processing market sentiment...",
            "Generating recommendations..."
        ]
        self._setup_data_directories()
        self._setup_routes()
        
    def _setup_data_directories(self):
        """Setup data directories for bundled app"""
        import sys
        from pathlib import Path
        
        # Determine data directory based on execution context
        if getattr(sys, 'frozen', False):
            # Running as bundled app - use user Documents folder
            self.data_dir = Path.home() / 'Documents' / 'StocksAnalyzer'
            self.outputs_dir = self.data_dir / 'outputs'
        else:
            # Running from source - use current directory
            self.data_dir = Path.cwd()
            self.outputs_dir = self.data_dir / 'outputs'
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment variables for analysis engines
        os.environ['STOCKS_DATA_DIR'] = str(self.data_dir)
        os.environ['STOCKS_OUTPUTS_DIR'] = str(self.outputs_dir)
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html')
            
        @self.app.route('/api/start-analysis', methods=['POST'])
        def start_analysis():
            """Start a new stock analysis (non-blocking)"""
            if self.state.analysis_in_progress:
                return jsonify({
                    'status': 'error',
                    'message': 'Analysis already in progress'
                }), 400
            
            # Reset state for new analysis
            self.state.analysis_in_progress = True
            self.state.analysis_start_time = time.time()
            self.state.phase_times = [self.state.analysis_start_time]
            self.state.current_phase = 0
            
            # Submit analysis task to executor (non-blocking)
            self.state.analysis_task = self.state.executor.submit(self._run_background_analysis)
            
            return jsonify({
                'status': 'success',
                'message': 'Analysis started',
                'timestamp': datetime.now().isoformat()
            })
            
        @self.app.route('/api/analysis-status')
        def analysis_status():
            """Get current analysis status"""
            progress_percentage = 0
            
            if self.state.analysis_start_time and self.state.analysis_in_progress:
                elapsed_time = time.time() - self.state.analysis_start_time
                # Simple progress calculation
                progress_percentage = min((elapsed_time / 3.5) * 10, 100)
                    
            elif self.state.current_analysis is not None and not self.state.analysis_in_progress:
                progress_percentage = 100
            
            return jsonify({
                'in_progress': self.state.analysis_in_progress,
                'has_results': self.state.current_analysis is not None,
                'current_phase': self.state.current_phase,
                'phase_name': self.phase_names[self.state.current_phase] if self.state.current_phase < len(self.phase_names) else "Completing...",
                'progress_percentage': round(progress_percentage),
                'timestamp': datetime.now().isoformat()
            })
            
        @self.app.route('/api/results')
        def get_results():
            """Get analysis results"""
            if self.state.current_analysis is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis results available'
                }), 404
            
            # Clean NaN values before returning
            cleaned_data = self._clean_nan_values(self.state.current_analysis)
            
            return jsonify({
                'status': 'success',
                'data': cleaned_data,
                'timestamp': datetime.now().isoformat()
            })
            
        @self.app.route('/api/stock/<ticker>')
        def get_stock_details(ticker):
            """Get detailed information for a specific stock"""
            if self.state.current_analysis is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available'
                }), 404
            
            # Find stock in results
            stock_data = None
            ticker_upper = ticker.upper()
            for stock in self.state.current_analysis.get('top_10_picks', []):
                if stock['ticker'].upper() == ticker_upper:
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
            
        @self.app.route('/stock/<ticker>')
        def stock_analysis(ticker):
            """Individual stock detail page"""
            return render_template('stock_detail.html', ticker=ticker.upper())
            
        @self.app.route('/category/<category>')
        def category_view(category):
            """Category-specific stock listing page"""
            category_names = {
                'under-5': 'Under $5 Stocks',
                '5-to-10': '$5 - $10 Stocks', 
                '10-to-20': '$10 - $20 Stocks'
            }
            category_name = category_names.get(category, 'Stock Category')
            return render_template('category.html', category=category, category_name=category_name)
            
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'Penny Stock Analysis API',
                'version': '2.0',  # New consolidated version
                'features': {
                    'async_enabled': True,
                    'state_management': 'dataclass',
                    'executor_threads': 4
                }
            })
            
        @self.app.route('/30-day-picks')
        def thirty_day_picks():
            """30-day picks page"""
            return render_template('30_day_picks.html')
            
        @self.app.route('/api/30-day-picks')
        def get_thirty_day_picks():
            """Get 30-day optimized picks with live 20%+ growth research"""
            use_live_research = request.args.get('live', 'true').lower() == 'true'
            
            # Try live research first if available and requested
            if use_live_research and LIVE_RESEARCH_AVAILABLE:
                try:
                    researcher = LiveStockResearcher()
                    live_results = researcher.live_research_scan()
                    
                    # Format for consistent API response
                    formatted_picks = []
                    for pick in live_results.get('picks', []):
                        formatted_pick = {
                            'ticker': pick['ticker'],
                            'current_price': pick['current_price'],
                            'target_price': pick['target_price'],
                            'upside_potential': pick['upside_potential'],
                            'days_to_hold': pick.get('days_to_hold', 20),
                            'technical_score': pick.get('technical_score', 75),
                            'risk_level': pick.get('risk_level', 3),
                            'category_name': pick.get('category_name', 'Growth Opportunity'),
                            'reasons': pick.get('reasons', []),
                            'confidence': pick.get('confidence', 70),
                            'volume_ratio': pick.get('volume_ratio', 1.0),
                            'momentum_30d': pick.get('momentum_30d', 0.0),
                            'rsi': pick.get('rsi', 50),
                            'last_updated': pick.get('last_updated'),
                            'data_source': 'Live Research'
                        }
                        formatted_picks.append(formatted_pick)
                    
                    return jsonify({
                        'status': 'success',
                        'data': {
                            'picks': formatted_picks,
                            'metadata': {
                                'total_screened': live_results.get('total_screened', 0),
                                'qualified_count': live_results.get('qualified_count', 0),
                                'scan_duration': live_results.get('scan_duration_seconds', 0),
                                'scan_timestamp': live_results.get('scan_timestamp'),
                                'criteria': live_results.get('criteria', {}),
                                'data_sources': live_results.get('data_sources', []),
                                'source_type': 'live_research'
                            }
                        }
                    })
                    
                except Exception as e:
                    # Log error and fall back to static analysis
                    print(f"Live research failed: {e}")
                    # Continue to fallback logic below
            
            # Fallback to existing static analysis
            if self.state.current_analysis is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No analysis data available. Try running an analysis first.',
                    'suggestion': 'Use the dashboard to start a new analysis or enable live research.'
                }), 404
                
            # Filter existing analysis for 30-day optimized picks
            thirty_day_picks = []
            for stock in self.state.current_analysis.get('top_10_picks', []):
                if stock.get('optimal_holding_days', 30) <= 30:
                    # Ensure consistent data structure
                    formatted_stock = {
                        'ticker': stock.get('ticker', ''),
                        'current_price': stock.get('current_price', 0),
                        'target_price': stock.get('target_price', stock.get('current_price', 0)),
                        'upside_potential': stock.get('upside_potential', 0),
                        'days_to_hold': stock.get('optimal_holding_days', 20),
                        'technical_score': stock.get('technical_score', 70),
                        'risk_level': stock.get('risk_level', 3),
                        'category_name': stock.get('category_name', 'Analysis Pick'),
                        'data_source': 'Static Analysis'
                    }
                    thirty_day_picks.append(formatted_stock)
                    
            return jsonify({
                'status': 'success',
                'data': {
                    'picks': thirty_day_picks,
                    'metadata': {
                        'source_type': 'static_analysis',
                        'analysis_timestamp': self.state.current_analysis.get('timestamp'),
                        'total_picks': len(thirty_day_picks)
                    }
                }
            })
            
        @self.app.route('/api/live-research', methods=['POST'])
        def trigger_live_research():
            """Trigger on-demand live research for 20%+ growth stocks"""
            if not LIVE_RESEARCH_AVAILABLE:
                return jsonify({
                    'status': 'error',
                    'message': 'Live research system not available'
                }), 503
            
            try:
                # Get parameters from request
                data = request.get_json() or {}
                min_growth = data.get('min_growth_potential', 20.0)
                max_price = data.get('max_price', 50.0)
                max_results = data.get('max_results', 20)
                
                # Initialize researcher with custom criteria
                config = {
                    'min_growth_potential': min_growth,
                    'max_price': max_price
                }
                researcher = LiveStockResearcher(config)
                
                # Perform live research scan
                results = researcher.live_research_scan()
                
                # Limit results if requested
                if max_results:
                    results['picks'] = results['picks'][:max_results]
                
                return jsonify({
                    'status': 'success',
                    'message': f'Found {len(results["picks"])} stocks with {min_growth}%+ growth potential',
                    'data': results
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Live research failed: {str(e)}'
                }), 500
        
        @self.app.route('/api/clear-cache', methods=['POST'])
        def clear_cache():
            """Clear the live research cache (admin use)"""
            try:
                if LIVE_RESEARCH_AVAILABLE:
                    researcher = LiveStockResearcher()
                    researcher.clear_cache()
                    return jsonify({
                        'status': 'success',
                        'message': 'Live research cache cleared successfully'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Live research system not available'
                    }), 503
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to clear cache: {str(e)}'
                }), 500
            
        @self.app.route('/debug')
        def debug():
            """Debug page (only available in debug mode)"""
            if not self.app.debug:
                return jsonify({'error': 'Debug mode is disabled'}), 403
                
            with open('debug_dashboard.html', 'r') as f:
                return f.read()
                
        @self.app.route('/test')
        def test():
            """Test display page"""
            with open('test_display.html', 'r') as f:
                return f.read()
    
    def _clean_nan_values(self, obj):
        """Recursively clean NaN values from nested dictionaries/lists"""
        if isinstance(obj, dict):
            return {k: self._clean_nan_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and math.isnan(obj):
            return None  # Use None instead of 0 to preserve data integrity
        return obj
    
    def _update_phase_callback(self, phase: int):
        """Update current phase for progress tracking"""
        current_time = time.time()
        if len(self.state.phase_times) <= phase:
            self.state.phase_times.append(current_time)
        else:
            self.state.phase_times[phase] = current_time
        
        self.state.current_phase = phase
        print(f"Phase {phase + 1}/5: {self.phase_names[phase]} (at {current_time:.2f}s)")
    
    def _run_background_analysis(self):
        """Run analysis in background thread (non-blocking)"""
        try:
            print(f"Starting background analysis at {self.state.analysis_start_time:.2f}s...")
            
            if not PENNY_ANALYZER_AVAILABLE:
                raise Exception("Penny stock analyzer not available")
                
            # Create analyzer instance
            analyzer = PennyStockAnalyzer()
            
            # Run analysis with phase tracking
            self._update_phase_callback(0)  # Phase 1: Stock discovery
            tickers = analyzer.get_penny_stock_universe()
            
            self._update_phase_callback(1)  # Phase 2: Technical analysis
            technical_scores = analyzer.perform_technical_analysis(tickers)
            
            self._update_phase_callback(2)  # Phase 3: Fundamental analysis  
            fundamental_scores = analyzer.perform_fundamental_analysis(tickers)
            
            self._update_phase_callback(3)  # Phase 4: Sentiment analysis
            sentiment_scores = analyzer.analyze_sentiment(tickers)
            
            self._update_phase_callback(4)  # Phase 5: Final rankings
            top_10_picks = analyzer.generate_final_rankings(
                tickers, technical_scores, fundamental_scores, sentiment_scores
            )
            
            # Load additional data from phase files
            self.state.current_analysis = self._load_analysis_data(analyzer.output_dir, top_10_picks)
            
            # Calculate completion time
            completion_time = time.time()
            self.state.phase_times.append(completion_time)
            total_duration = completion_time - self.state.analysis_start_time
            print(f"Background analysis completed successfully in {total_duration:.2f}s")
            
        except Exception as e:
            print(f"Error in background analysis: {e}")
            self.state.current_analysis = {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self.state.analysis_in_progress = False
            self.state.current_phase = 0
            self.state.analysis_start_time = None
    
    def _load_analysis_data(self, output_dir: str, top_10_picks: List[Dict]) -> Dict:
        """Load additional analysis data from phase files"""
        technical_data = {}
        fundamental_data = {}
        sentiment_data = {}
        
        # Load data files if they exist
        try:
            with open(f"{output_dir}/phase2/technical_analysis.json", 'r') as f:
                technical_data = json.load(f)
        except FileNotFoundError:
            pass
        
        try:
            with open(f"{output_dir}/phase3/fundamental_analysis.json", 'r') as f:
                fundamental_data = json.load(f)
        except FileNotFoundError:
            pass
        
        try:
            with open(f"{output_dir}/phase4/sentiment_analysis.json", 'r') as f:
                sentiment_data = json.load(f)
        except FileNotFoundError:
            pass
        
        return {
            'timestamp': datetime.now().isoformat(),
            'top_10_picks': top_10_picks,
            'technical_data': technical_data,
            'fundamental_data': fundamental_data,
            'sentiment_data': sentiment_data,
            'output_directory': output_dir
        }
    
    def load_previous_analysis(self):
        """Load the most recent analysis from disk"""
        try:
            import glob
            output_dirs = sorted(glob.glob("outputs/penny_stocks_*"))
            if output_dirs:
                latest_dir = output_dirs[-1]
                print(f"Loading previous analysis from: {latest_dir}")
                
                # Try to load rankings
                try:
                    with open(f"{latest_dir}/phase5/final_rankings_with_holding.json", 'r') as f:
                        top_picks = json.load(f)
                        print("Loaded rankings with holding period data")
                except FileNotFoundError:
                    with open(f"{latest_dir}/phase5/final_rankings.json", 'r') as f:
                        top_picks = json.load(f)
                        print("Loaded rankings without holding period data")
                
                self.state.current_analysis = self._load_analysis_data(latest_dir, top_picks)
                print(f"Loaded {len(top_picks)} picks from previous analysis")
                return True
        except Exception as e:
            print(f"Error loading previous analysis: {e}")
        return False
    
    def cleanup(self):
        """Cleanup resources on shutdown"""
        if self.state.executor:
            self.state.executor.shutdown(wait=True)
            print("Executor shutdown complete")
    
    def run(self, debug=False, host='127.0.0.1', port=8080):
        """Run the Flask application"""
        print("Starting Penny Stock Analysis Web Application...")
        print(f"Access the application at: http://{host}:{port}")
        
        # Try to load previous analysis on startup
        if self.load_previous_analysis():
            print("Previous analysis loaded successfully")
        else:
            print("No previous analysis found")
        
        try:
            self.app.run(
                debug=debug,
                host=host,
                port=port,
                threaded=True  # Enable threading for better performance
            )
        finally:
            self.cleanup()


# Create global app instance (for compatibility with existing code)
app = StockAnalysisApp()

if __name__ == '__main__':
    # Production configuration (secure defaults)
    DEBUG = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    HOST = os.getenv('APP_HOST', '127.0.0.1')  # Localhost only by default
    PORT = int(os.getenv('APP_PORT', '8080'))
    
    app.run(debug=DEBUG, host=HOST, port=PORT)