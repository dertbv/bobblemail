#!/usr/bin/env python3
"""
Stocks Analyzer - Standalone Application Launcher
Handles server startup, port management, and browser launch for macOS app bundle
"""

import os
import sys
import socket
import webbrowser
import threading
import time
import signal
import subprocess
from pathlib import Path
import logging
from contextlib import closing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StocksLauncher:
    """Main launcher for the Stocks Analyzer application"""
    
    def __init__(self):
        self.port = 5000
        self.host = '127.0.0.1'
        self.server_process = None
        self.shutdown_event = threading.Event()
        
        # Determine if running as bundled app
        if getattr(sys, 'frozen', False):
            # Running as bundled executable
            self.bundle_dir = Path(sys._MEIPASS)
            self.app_dir = Path(sys.executable).parent.parent
            self.resources_dir = self.app_dir / 'Resources'
            self.data_dir = Path.home() / 'Documents' / 'StocksAnalyzer'
        else:
            # Running from source
            self.bundle_dir = Path(__file__).parent
            self.app_dir = self.bundle_dir
            self.resources_dir = self.bundle_dir
            self.data_dir = self.bundle_dir
        
        # Ensure data directory exists
        self.outputs_dir = self.data_dir / 'outputs'
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Bundle directory: {self.bundle_dir}")
        logger.info(f"Resources directory: {self.resources_dir}")
        logger.info(f"Data directory: {self.data_dir}")
    
    def find_free_port(self, start_port=5000, max_port=5100):
        """Find an available port in the given range"""
        for port in range(start_port, max_port):
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                if sock.connect_ex((self.host, port)) != 0:
                    return port
        raise RuntimeError(f"No free ports available between {start_port} and {max_port}")
    
    def wait_for_server(self, timeout=30):
        """Wait for the Flask server to start"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                    if sock.connect_ex((self.host, self.port)) == 0:
                        return True
            except:
                pass
            time.sleep(0.5)
        return False
    
    def launch_browser(self):
        """Open the default browser to the application"""
        url = f"http://{self.host}:{self.port}"
        logger.info(f"Opening browser at {url}")
        
        # Wait a bit for server to fully initialize
        time.sleep(2)
        
        # Open browser
        webbrowser.open(url)
    
    def start_server(self):
        """Start the Flask server"""
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'production'
        env['STOCKS_DATA_DIR'] = str(self.data_dir)
        env['STOCKS_OUTPUTS_DIR'] = str(self.outputs_dir)
        
        # Change to app directory
        os.chdir(str(self.bundle_dir))
        
        # Import and run the Flask app directly
        sys.path.insert(0, str(self.bundle_dir))
        
        try:
            # Import the app module
            import app
            
            # Get the Flask app instance
            if hasattr(app, 'StockAnalysisApp'):
                # Using the class-based app
                stock_app = app.StockAnalysisApp()
                flask_app = stock_app.app
            else:
                # Direct Flask app
                flask_app = app.app
            
            # Update paths for bundled resources
            if getattr(sys, 'frozen', False):
                flask_app.template_folder = str(self.resources_dir / 'templates')
                flask_app.static_folder = str(self.resources_dir / 'static')
            
            # Run the Flask app
            logger.info(f"Starting Flask server on {self.host}:{self.port}")
            flask_app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received")
        self.shutdown_event.set()
        
        if self.server_process and self.server_process.is_alive():
            logger.info("Stopping server...")
            # The Flask server should stop when the main thread exits
            sys.exit(0)
    
    def show_error_dialog(self, message):
        """Show error dialog using macOS native dialog"""
        try:
            subprocess.run([
                'osascript', '-e',
                f'display dialog "{message}" with title "Stocks Analyzer Error" buttons {{"OK"}} default button "OK"'
            ])
        except:
            print(f"Error: {message}")
    
    def run(self):
        """Main entry point"""
        try:
            # Find available port
            self.port = self.find_free_port()
            logger.info(f"Using port {self.port}")
            
            # Set up signal handlers
            signal.signal(signal.SIGINT, self.handle_shutdown)
            signal.signal(signal.SIGTERM, self.handle_shutdown)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()
            
            # Wait for server to start
            if self.wait_for_server():
                logger.info("Server started successfully")
                
                # Launch browser
                self.launch_browser()
                
                # Show dock notification
                if sys.platform == 'darwin':
                    try:
                        subprocess.run([
                            'osascript', '-e',
                            'display notification "Stocks Analyzer is running" with title "Stocks Analyzer"'
                        ])
                    except:
                        pass
                
                # Keep the main thread alive
                try:
                    while not self.shutdown_event.is_set():
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
            else:
                raise RuntimeError("Server failed to start within timeout period")
                
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.show_error_dialog(f"Failed to start Stocks Analyzer: {str(e)}")
            sys.exit(1)
        finally:
            logger.info("Application shutting down")


def main():
    """Main entry point for the application"""
    launcher = StocksLauncher()
    launcher.run()


if __name__ == '__main__':
    main()