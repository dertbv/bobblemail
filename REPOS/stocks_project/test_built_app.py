#!/usr/bin/env python3
"""
Test Suite for Built Stocks Analyzer Application
Validates the standalone macOS app bundle functionality
"""

import os
import sys
import subprocess
import time
import requests
import json
import signal
from pathlib import Path
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AppTester:
    """Test suite for the built Stocks Analyzer application"""
    
    def __init__(self, app_path=None):
        self.script_dir = Path(__file__).parent
        self.app_path = Path(app_path) if app_path else self.script_dir / 'dist' / 'StocksAnalyzer.app'
        self.app_process = None
        self.test_results = []
        
    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if message:
            logger.info(f"   {message}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_app_bundle_structure(self):
        """Test 1: Verify app bundle structure"""
        logger.info("Testing app bundle structure...")
        
        if not self.app_path.exists():
            self.log_test("App Bundle Exists", False, f"App not found at {self.app_path}")
            return False
        
        self.log_test("App Bundle Exists", True)
        
        # Check required paths
        required_paths = [
            self.app_path / 'Contents',
            self.app_path / 'Contents' / 'Info.plist',
            self.app_path / 'Contents' / 'MacOS',
            self.app_path / 'Contents' / 'Resources',
            self.app_path / 'Contents' / 'MacOS' / 'stocks_launcher'
        ]
        
        all_paths_exist = True
        for path in required_paths:
            exists = path.exists()
            if not exists:
                all_paths_exist = False
                logger.error(f"Missing: {path}")
        
        self.log_test("App Bundle Structure", all_paths_exist)
        return all_paths_exist
    
    def test_executable_permissions(self):
        """Test 2: Verify executable has proper permissions"""
        logger.info("Testing executable permissions...")
        
        exe_path = self.app_path / 'Contents' / 'MacOS' / 'stocks_launcher'
        
        if not exe_path.exists():
            self.log_test("Executable Exists", False, "Main executable not found")
            return False
        
        self.log_test("Executable Exists", True)
        
        # Check if executable
        is_executable = os.access(exe_path, os.X_OK)
        self.log_test("Executable Permissions", is_executable)
        
        return is_executable
    
    def test_info_plist(self):
        """Test 3: Verify Info.plist contents"""
        logger.info("Testing Info.plist...")
        
        plist_path = self.app_path / 'Contents' / 'Info.plist'
        
        if not plist_path.exists():
            self.log_test("Info.plist Exists", False)
            return False
        
        self.log_test("Info.plist Exists", True)
        
        try:
            # Read plist
            result = subprocess.run([
                'plutil', '-convert', 'json', '-o', '-', str(plist_path)
            ], capture_output=True, text=True, check=True)
            
            plist_data = json.loads(result.stdout)
            
            # Check required keys
            required_keys = [
                'CFBundleName',
                'CFBundleExecutable',
                'CFBundleIdentifier',
                'CFBundleVersion'
            ]
            
            all_keys_present = True
            for key in required_keys:
                if key not in plist_data:
                    all_keys_present = False
                    logger.error(f"Missing plist key: {key}")
            
            self.log_test("Info.plist Valid", all_keys_present)
            
            # Log some key values
            if all_keys_present:
                logger.info(f"   Bundle Name: {plist_data.get('CFBundleName')}")
                logger.info(f"   Bundle ID: {plist_data.get('CFBundleIdentifier')}")
                logger.info(f"   Version: {plist_data.get('CFBundleVersion')}")
            
            return all_keys_present
            
        except Exception as e:
            self.log_test("Info.plist Valid", False, str(e))
            return False
    
    def test_resources(self):
        """Test 4: Verify required resources are included"""
        logger.info("Testing included resources...")
        
        resources_path = self.app_path / 'Contents' / 'Resources'
        
        # Check for templates
        templates_exist = (resources_path / 'templates').exists()
        self.log_test("Templates Included", templates_exist)
        
        # Check for static files
        static_exist = (resources_path / 'static').exists()
        self.log_test("Static Files Included", static_exist)
        
        return templates_exist and static_exist
    
    @contextmanager
    def launch_app(self, timeout=30):
        """Context manager to launch and cleanup the app"""
        logger.info("Launching application...")
        
        try:
            # Launch the app
            self.app_process = subprocess.Popen([
                'open', '-W', str(self.app_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to start
            time.sleep(5)
            
            yield self.app_process
            
        finally:
            # Cleanup
            if self.app_process:
                try:
                    # Try graceful shutdown first
                    self.app_process.terminate()
                    self.app_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.app_process.kill()
                    self.app_process.wait()
                
                logger.info("Application stopped")
    
    def find_app_port(self):
        """Find which port the app is running on"""
        # Common ports the app might use
        test_ports = [5000, 5001, 5002, 5003, 5004, 5005]
        
        for port in test_ports:
            try:
                response = requests.get(f'http://127.0.0.1:{port}', timeout=2)
                if response.status_code == 200:
                    return port
            except:
                continue
        
        return None
    
    def test_web_interface(self):
        """Test 5: Verify web interface functionality"""
        logger.info("Testing web interface...")
        
        try:
            with self.launch_app():
                # Wait for app to fully start
                time.sleep(10)
                
                # Find the port
                port = self.find_app_port()
                
                if not port:
                    self.log_test("Web Server Running", False, "Could not connect to web server")
                    return False
                
                self.log_test("Web Server Running", True, f"Running on port {port}")
                
                base_url = f'http://127.0.0.1:{port}'
                
                # Test main page
                try:
                    response = requests.get(base_url, timeout=10)
                    main_page_ok = response.status_code == 200
                    self.log_test("Main Page Loads", main_page_ok)
                except Exception as e:
                    self.log_test("Main Page Loads", False, str(e))
                    return False
                
                # Test API endpoint
                try:
                    response = requests.get(f'{base_url}/api/status', timeout=10)
                    api_ok = response.status_code in [200, 404]  # 404 is OK if endpoint doesn't exist
                    self.log_test("API Accessible", api_ok)
                except Exception as e:
                    self.log_test("API Accessible", False, str(e))
                
                return main_page_ok
                
        except Exception as e:
            self.log_test("Web Interface Test", False, f"Launch failed: {e}")
            return False
    
    def test_data_directory(self):
        """Test 6: Verify data directory creation"""
        logger.info("Testing data directory creation...")
        
        # Expected data directory
        expected_data_dir = Path.home() / 'Documents' / 'StocksAnalyzer'
        
        # Clean up if exists from previous tests
        if expected_data_dir.exists():
            import shutil
            shutil.rmtree(expected_data_dir)
        
        try:
            with self.launch_app():
                time.sleep(5)  # Give app time to create directories
                
                data_dir_created = expected_data_dir.exists()
                self.log_test("Data Directory Created", data_dir_created, 
                            str(expected_data_dir) if data_dir_created else "")
                
                if data_dir_created:
                    outputs_dir = expected_data_dir / 'outputs'
                    outputs_created = outputs_dir.exists()
                    self.log_test("Outputs Directory Created", outputs_created)
                    
                    return data_dir_created and outputs_created
                
                return data_dir_created
                
        except Exception as e:
            self.log_test("Data Directory Test", False, str(e))
            return False
    
    def test_dmg_installer(self):
        """Test 7: Verify DMG installer if it exists"""
        logger.info("Testing DMG installer...")
        
        dmg_path = self.script_dir / 'dist' / 'StocksAnalyzer-1.0.0.dmg'
        
        if not dmg_path.exists():
            self.log_test("DMG Installer", False, "DMG file not found")
            return False
        
        self.log_test("DMG File Exists", True)
        
        # Test DMG can be mounted
        try:
            result = subprocess.run([
                'hdiutil', 'attach', '-readonly', '-mountpoint', '/tmp/stocks_test_mount', 
                str(dmg_path)
            ], capture_output=True, check=True)
            
            # Check if app exists in mounted DMG
            mounted_app = Path('/tmp/stocks_test_mount') / 'StocksAnalyzer.app'
            app_in_dmg = mounted_app.exists()
            
            # Unmount
            subprocess.run(['hdiutil', 'detach', '/tmp/stocks_test_mount'], 
                         capture_output=True, check=True)
            
            self.log_test("DMG Mounts Successfully", True)
            self.log_test("App Included in DMG", app_in_dmg)
            
            return app_in_dmg
            
        except subprocess.SubprocessError as e:
            self.log_test("DMG Mounts Successfully", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🧪 Starting Stocks Analyzer App Test Suite")
        logger.info("=" * 50)
        
        tests = [
            self.test_app_bundle_structure,
            self.test_executable_permissions,
            self.test_info_plist,
            self.test_resources,
            self.test_web_interface,
            self.test_data_directory,
            self.test_dmg_installer
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
                self.log_test(test.__name__, False, f"Exception: {e}")
        
        # Summary
        logger.info("")
        logger.info("🏁 Test Results Summary")
        logger.info("=" * 30)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            logger.info(f"{status} {result['test']}")
            if result['message']:
                logger.info(f"   {result['message']}")
        
        logger.info("")
        logger.info(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! App is ready for distribution.")
            return True
        else:
            logger.error(f"❌ {total - passed} tests failed. Please review and fix issues.")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test built Stocks Analyzer application')
    parser.add_argument('--app-path', type=str, 
                       help='Path to StocksAnalyzer.app (default: dist/StocksAnalyzer.app)')
    
    args = parser.parse_args()
    
    tester = AppTester(args.app_path)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()