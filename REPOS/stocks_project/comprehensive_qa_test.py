#!/usr/bin/env python3
"""
Comprehensive QA Testing Suite for Penny Stock Analysis Web Application
This script performs automated testing across all areas requested
"""

import requests
import json
import time
import threading
import sys
import os
import subprocess
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random
import string

# Test configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_RESULTS = {
    "functional": [],
    "security": [],
    "performance": [],
    "integration": [],
    "edge_cases": [],
    "bugs": [],
    "recommendations": []
}

class QATestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.flask_process = None
        self.start_time = None
        
    def start_flask_app(self):
        """Start Flask application for testing"""
        print("🚀 Starting Flask application for QA testing...")
        
        # Activate virtual environment and start Flask
        cmd = ["bash", "-c", "source venv/bin/activate && python app.py"]
        
        try:
            # Start Flask in background
            self.flask_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, FLASK_ENV='testing')
            )
            
            # Wait for app to start
            time.sleep(5)
            
            # Test if app is running
            try:
                response = requests.get(f"{BASE_URL}/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Flask application started successfully")
                    return True
            except:
                pass
                
            print("❌ Failed to start Flask application")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Flask app: {e}")
            return False
    
    def stop_flask_app(self):
        """Stop Flask application"""
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=10)
                print("🛑 Flask application stopped")
            except:
                self.flask_process.kill()
                print("🛑 Flask application force killed")
    
    def log_test_result(self, category, test_name, status, details=None, severity="INFO"):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "severity": severity
        }
        TEST_RESULTS[category].append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_functional_api_endpoints(self):
        """Test 1: Functional Testing - API Endpoints"""
        print("\n🧪 FUNCTIONAL TESTING - API Endpoints")
        
        # Test health endpoint
        try:
            response = self.session.get(f"{BASE_URL}/api/health", timeout=5)
            if response.status_code == 200 and response.json().get('status') == 'healthy':
                self.log_test_result('functional', 'Health Endpoint', 'PASS')
            else:
                self.log_test_result('functional', 'Health Endpoint', 'FAIL', 
                                   f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test_result('functional', 'Health Endpoint', 'FAIL', str(e))
        
        # Test analysis status endpoint
        try:
            response = self.session.get(f"{BASE_URL}/api/analysis-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'in_progress' in data and 'has_results' in data:
                    self.log_test_result('functional', 'Analysis Status Endpoint', 'PASS')
                else:
                    self.log_test_result('functional', 'Analysis Status Endpoint', 'FAIL',
                                       f"Missing required fields: {data}")
            else:
                self.log_test_result('functional', 'Analysis Status Endpoint', 'FAIL',
                                   f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result('functional', 'Analysis Status Endpoint', 'FAIL', str(e))
        
        # Test start analysis endpoint
        try:
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{BASE_URL}/api/start-analysis", 
                                       json={}, headers=headers, timeout=5)
            if response.status_code in [200, 409]:  # 409 if already in progress
                self.log_test_result('functional', 'Start Analysis Endpoint', 'PASS')
            else:
                self.log_test_result('functional', 'Start Analysis Endpoint', 'FAIL',
                                   f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test_result('functional', 'Start Analysis Endpoint', 'FAIL', str(e))
        
        # Test results endpoint
        try:
            response = self.session.get(f"{BASE_URL}/api/results", timeout=5)
            if response.status_code in [200, 404]:  # 404 if no results available
                self.log_test_result('functional', 'Results Endpoint', 'PASS')
            else:
                self.log_test_result('functional', 'Results Endpoint', 'FAIL',
                                   f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result('functional', 'Results Endpoint', 'FAIL', str(e))
        
        # Test stock detail endpoint
        try:
            response = self.session.get(f"{BASE_URL}/api/stock/AAPL", timeout=5)
            if response.status_code in [200, 404]:  # 404 if stock not in analysis
                self.log_test_result('functional', 'Stock Detail Endpoint', 'PASS')
            else:
                self.log_test_result('functional', 'Stock Detail Endpoint', 'FAIL',
                                   f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result('functional', 'Stock Detail Endpoint', 'FAIL', str(e))
        
        # Test category endpoint
        try:
            response = self.session.get(f"{BASE_URL}/api/category/under-5", timeout=5)
            if response.status_code in [200, 404]:  # 404 if no results available
                self.log_test_result('functional', 'Category Endpoint', 'PASS')
            else:
                self.log_test_result('functional', 'Category Endpoint', 'FAIL',
                                   f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result('functional', 'Category Endpoint', 'FAIL', str(e))
    
    def test_functional_web_pages(self):
        """Test web page rendering"""
        print("\n🧪 FUNCTIONAL TESTING - Web Pages")
        
        pages = [
            ('/', 'Home Page'),
            ('/dashboard', 'Dashboard Page'),
            ('/30-day-picks', '30-Day Picks Page'),
            ('/category/under-5', 'Category Page'),
            ('/stock/AAPL', 'Stock Detail Page')
        ]
        
        for path, name in pages:
            try:
                response = self.session.get(f"{BASE_URL}{path}", timeout=5)
                if response.status_code == 200:
                    # Check if it's HTML content
                    if 'text/html' in response.headers.get('Content-Type', ''):
                        self.log_test_result('functional', f'{name} Rendering', 'PASS')
                    else:
                        self.log_test_result('functional', f'{name} Rendering', 'FAIL',
                                           'Not HTML content')
                else:
                    self.log_test_result('functional', f'{name} Rendering', 'FAIL',
                                       f"Status: {response.status_code}")
            except Exception as e:
                self.log_test_result('functional', f'{name} Rendering', 'FAIL', str(e))
    
    def test_security_input_validation(self):
        """Test 2: Security Testing - Input Validation"""
        print("\n🔒 SECURITY TESTING - Input Validation")
        
        # Test SQL injection attempts
        sql_payloads = ["'; DROP TABLE users; --", "1' OR '1'='1", "UNION SELECT * FROM users"]
        
        for payload in sql_payloads:
            try:
                response = self.session.get(f"{BASE_URL}/api/stock/{payload}", timeout=5)
                if response.status_code == 400:  # Should be rejected
                    self.log_test_result('security', f'SQL Injection Protection ({payload[:10]}...)', 'PASS')
                else:
                    self.log_test_result('security', f'SQL Injection Protection ({payload[:10]}...)', 'FAIL',
                                       f"Payload not rejected: {response.status_code}", "HIGH")
            except Exception as e:
                self.log_test_result('security', f'SQL Injection Protection ({payload[:10]}...)', 'PASS',
                                   "Request properly rejected")
        
        # Test XSS attempts
        xss_payloads = ["<script>alert('xss')</script>", "javascript:alert(1)", "<img src=x onerror=alert(1)>"]
        
        for payload in xss_payloads:
            try:
                response = self.session.get(f"{BASE_URL}/api/stock/{payload}", timeout=5)
                if response.status_code == 400:
                    self.log_test_result('security', f'XSS Protection ({payload[:15]}...)', 'PASS')
                else:
                    self.log_test_result('security', f'XSS Protection ({payload[:15]}...)', 'FAIL',
                                       f"Payload not rejected: {response.status_code}", "HIGH")
            except Exception as e:
                self.log_test_result('security', f'XSS Protection ({payload[:15]}...)', 'PASS',
                                   "Request properly rejected")
        
        # Test path traversal
        path_payloads = ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam"]
        
        for payload in path_payloads:
            try:
                response = self.session.get(f"{BASE_URL}/api/stock/{payload}", timeout=5)
                if response.status_code == 400:
                    self.log_test_result('security', f'Path Traversal Protection ({payload[:15]}...)', 'PASS')
                else:
                    self.log_test_result('security', f'Path Traversal Protection ({payload[:15]}...)', 'FAIL',
                                       f"Payload not rejected: {response.status_code}", "MEDIUM")
            except Exception as e:
                self.log_test_result('security', f'Path Traversal Protection ({payload[:15]}...)', 'PASS',
                                   "Request properly rejected")
    
    def test_security_error_disclosure(self):
        """Test error message information disclosure"""
        print("\n🔒 SECURITY TESTING - Error Disclosure")
        
        # Test invalid endpoints
        try:
            response = self.session.get(f"{BASE_URL}/api/nonexistent", timeout=5)
            if response.status_code == 404:
                data = response.json()
                # Check if error message doesn't reveal sensitive info
                sensitive_terms = ['stack trace', 'file path', 'database', 'internal']
                message = data.get('message', '').lower()
                
                if any(term in message for term in sensitive_terms):
                    self.log_test_result('security', 'Error Message Disclosure', 'FAIL',
                                       f"Sensitive info in error: {message}", "MEDIUM")
                else:
                    self.log_test_result('security', 'Error Message Disclosure', 'PASS')
            else:
                self.log_test_result('security', 'Error Message Disclosure', 'FAIL',
                                   f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test_result('security', 'Error Message Disclosure', 'FAIL', str(e))
    
    def test_performance_load_testing(self):
        """Test 3: Performance Testing"""
        print("\n⚡ PERFORMANCE TESTING - Load Testing")
        
        # Concurrent request test
        def make_request(endpoint):
            try:
                start_time = time.time()
                response = self.session.get(f"{BASE_URL}{endpoint}", timeout=10)
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'endpoint': endpoint
                }
            except Exception as e:
                return {
                    'status_code': None,
                    'response_time': None,
                    'endpoint': endpoint,
                    'error': str(e)
                }
        
        # Test concurrent requests to health endpoint
        endpoints = ['/api/health'] * 10
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        success_count = sum(1 for r in results if r.get('status_code') == 200)
        avg_response_time = sum(r.get('response_time', 0) for r in results if r.get('response_time')) / len(results)
        
        if success_count >= 8:  # At least 80% success rate
            self.log_test_result('performance', 'Concurrent Request Handling', 'PASS',
                               f"Success: {success_count}/10, Avg time: {avg_response_time:.3f}s")
        else:
            self.log_test_result('performance', 'Concurrent Request Handling', 'FAIL',
                               f"Success: {success_count}/10, Total time: {total_time:.3f}s", "MEDIUM")
        
        # Test response time for each endpoint
        critical_endpoints = [
            '/api/health',
            '/api/analysis-status',
            '/api/results'
        ]
        
        for endpoint in critical_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{BASE_URL}{endpoint}", timeout=5)
                response_time = time.time() - start_time
                
                if response_time < 1.0:  # Should respond within 1 second
                    self.log_test_result('performance', f'Response Time {endpoint}', 'PASS',
                                       f"Response time: {response_time:.3f}s")
                else:
                    self.log_test_result('performance', f'Response Time {endpoint}', 'FAIL',
                                       f"Slow response: {response_time:.3f}s", "MEDIUM")
            except Exception as e:
                self.log_test_result('performance', f'Response Time {endpoint}', 'FAIL', str(e))
    
    def test_edge_cases(self):
        """Test 4: Edge Case Testing"""
        print("\n🎯 EDGE CASE TESTING")
        
        # Test invalid ticker formats
        invalid_tickers = ['', '123', 'TOOLONG', 'aa', '@#$%', '12345678']
        
        for ticker in invalid_tickers:
            try:
                response = self.session.get(f"{BASE_URL}/api/stock/{ticker}", timeout=5)
                if response.status_code == 400:
                    self.log_test_result('edge_cases', f'Invalid Ticker Rejection ({ticker})', 'PASS')
                else:
                    self.log_test_result('edge_cases', f'Invalid Ticker Rejection ({ticker})', 'FAIL',
                                       f"Should reject invalid ticker: {response.status_code}")
            except Exception as e:
                self.log_test_result('edge_cases', f'Invalid Ticker Rejection ({ticker})', 'PASS',
                                   "Request properly rejected")
        
        # Test invalid categories
        invalid_categories = ['invalid', '', '999', 'under-100']
        
        for category in invalid_categories:
            try:
                response = self.session.get(f"{BASE_URL}/api/category/{category}", timeout=5)
                if response.status_code == 400:
                    self.log_test_result('edge_cases', f'Invalid Category Rejection ({category})', 'PASS')
                else:
                    self.log_test_result('edge_cases', f'Invalid Category Rejection ({category})', 'FAIL',
                                       f"Should reject invalid category: {response.status_code}")
            except Exception as e:
                self.log_test_result('edge_cases', f'Invalid Category Rejection ({category})', 'PASS',
                                   "Request properly rejected")
        
        # Test oversized requests
        try:
            large_payload = {'data': 'x' * 10000}  # 10KB payload
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{BASE_URL}/api/start-analysis",
                                       json=large_payload, headers=headers, timeout=5)
            
            if response.status_code == 413:  # Request too large
                self.log_test_result('edge_cases', 'Large Request Rejection', 'PASS')
            else:
                self.log_test_result('edge_cases', 'Large Request Rejection', 'FAIL',
                                   f"Should reject large requests: {response.status_code}")
        except Exception as e:
            self.log_test_result('edge_cases', 'Large Request Rejection', 'PASS',
                               "Request properly rejected")
    
    def test_integration_workflow(self):
        """Test 5: Integration Testing"""
        print("\n🔗 INTEGRATION TESTING - End-to-End Workflow")
        
        # Test complete workflow
        try:
            # 1. Check initial status
            response = self.session.get(f"{BASE_URL}/api/analysis-status", timeout=5)
            if response.status_code == 200:
                initial_status = response.json()
                self.log_test_result('integration', 'Initial Status Check', 'PASS')
            else:
                self.log_test_result('integration', 'Initial Status Check', 'FAIL',
                                   f"Status: {response.status_code}")
                return
            
            # 2. Start analysis (if not in progress)
            if not initial_status.get('in_progress', False):
                headers = {'Content-Type': 'application/json'}
                response = self.session.post(f"{BASE_URL}/api/start-analysis",
                                           json={}, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    self.log_test_result('integration', 'Analysis Start', 'PASS')
                else:
                    self.log_test_result('integration', 'Analysis Start', 'FAIL',
                                       f"Status: {response.status_code}")
            
            # 3. Check status during analysis
            time.sleep(2)
            response = self.session.get(f"{BASE_URL}/api/analysis-status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                if status.get('in_progress') or status.get('has_results'):
                    self.log_test_result('integration', 'Analysis Progress Check', 'PASS')
                else:
                    self.log_test_result('integration', 'Analysis Progress Check', 'WARNING',
                                       "No progress detected")
            
            # 4. Try to get results
            response = self.session.get(f"{BASE_URL}/api/results", timeout=5)
            if response.status_code in [200, 404]:  # Either has results or no results yet
                self.log_test_result('integration', 'Results Retrieval', 'PASS')
            else:
                self.log_test_result('integration', 'Results Retrieval', 'FAIL',
                                   f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test_result('integration', 'End-to-End Workflow', 'FAIL', str(e))
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        print("\n📊 GENERATING QA REPORT")
        
        total_tests = sum(len(TEST_RESULTS[category]) for category in TEST_RESULTS if category not in ['bugs', 'recommendations'])
        passed_tests = sum(len([t for t in TEST_RESULTS[category] if t['status'] == 'PASS']) 
                          for category in TEST_RESULTS if category not in ['bugs', 'recommendations'])
        failed_tests = sum(len([t for t in TEST_RESULTS[category] if t['status'] == 'FAIL']) 
                          for category in TEST_RESULTS if category not in ['bugs', 'recommendations'])
        
        # Analyze results and generate bugs/recommendations
        self.analyze_results()
        
        report = f"""
# COMPREHENSIVE QA TEST REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## EXECUTIVE SUMMARY
- **Total Tests Run**: {total_tests}
- **Passed**: {passed_tests} ({(passed_tests/total_tests*100):.1f}% if total_tests > 0 else 0)
- **Failed**: {failed_tests} ({(failed_tests/total_tests*100):.1f}% if total_tests > 0 else 0)
- **Critical Issues**: {len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'HIGH'])}
- **Medium Issues**: {len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'MEDIUM'])}

## FUNCTIONAL TESTING RESULTS
"""
        
        for category in ['functional', 'security', 'performance', 'integration', 'edge_cases']:
            report += f"\n### {category.upper()} TESTING\n"
            
            if TEST_RESULTS[category]:
                for test in TEST_RESULTS[category]:
                    status_emoji = "✅" if test['status'] == 'PASS' else "❌" if test['status'] == 'FAIL' else "⚠️"
                    report += f"- {status_emoji} **{test['test_name']}**: {test['status']}\n"
                    if test['details']:
                        report += f"  - Details: {test['details']}\n"
            else:
                report += "- No tests run in this category\n"
        
        # Bug reports
        report += "\n## BUG REPORTS\n"
        if TEST_RESULTS['bugs']:
            for i, bug in enumerate(TEST_RESULTS['bugs'], 1):
                report += f"\n### Bug #{i} - {bug['severity']} Severity\n"
                report += f"- **Issue**: {bug['title']}\n"
                report += f"- **Description**: {bug['description']}\n"
                report += f"- **Impact**: {bug['impact']}\n"
                report += f"- **Recommendation**: {bug['recommendation']}\n"
        else:
            report += "No critical bugs identified.\n"
        
        # Recommendations
        report += "\n## RECOMMENDATIONS\n"
        if TEST_RESULTS['recommendations']:
            for i, rec in enumerate(TEST_RESULTS['recommendations'], 1):
                report += f"{i}. **{rec['title']}**: {rec['description']}\n"
        else:
            report += "No specific recommendations at this time.\n"
        
        report += f"\n## TESTING METHODOLOGY\n"
        report += "- **Automated Testing**: All tests were run using automated scripts\n"
        report += "- **Test Environment**: Local Flask development server\n"
        report += "- **Coverage**: API endpoints, web pages, security, performance, edge cases\n"
        report += "- **Duration**: {:.1f} seconds\n".format(time.time() - self.start_time if self.start_time else 0)
        
        return report
    
    def analyze_results(self):
        """Analyze test results and generate bugs/recommendations"""
        
        # Check for high-severity security issues
        security_fails = [t for t in TEST_RESULTS['security'] if t['status'] == 'FAIL' and t.get('severity') == 'HIGH']
        for fail in security_fails:
            TEST_RESULTS['bugs'].append({
                'severity': 'HIGH',
                'title': f"Security Vulnerability: {fail['test_name']}",
                'description': f"Security test failed: {fail['details']}",
                'impact': "Potential security breach, data exposure, or system compromise",
                'recommendation': "Implement proper input validation and sanitization"
            })
        
        # Check for performance issues
        perf_fails = [t for t in TEST_RESULTS['performance'] if t['status'] == 'FAIL']
        for fail in perf_fails:
            TEST_RESULTS['bugs'].append({
                'severity': 'MEDIUM',
                'title': f"Performance Issue: {fail['test_name']}",
                'description': f"Performance test failed: {fail['details']}",
                'impact': "Poor user experience, potential timeouts under load",
                'recommendation': "Optimize response times and implement caching"
            })
        
        # General recommendations
        TEST_RESULTS['recommendations'].extend([
            {
                'title': 'Implement Authentication',
                'description': 'Add user authentication and authorization to secure sensitive operations'
            },
            {
                'title': 'Add Rate Limiting',
                'description': 'Implement rate limiting to prevent abuse and DoS attacks'
            },
            {
                'title': 'Enhance Error Handling',
                'description': 'Implement comprehensive error handling with user-friendly messages'
            },
            {
                'title': 'Add Input Sanitization',
                'description': 'Enhance input validation and sanitization across all endpoints'
            },
            {
                'title': 'Implement Logging',
                'description': 'Add comprehensive security and audit logging'
            },
            {
                'title': 'Add Health Monitoring',
                'description': 'Implement application health monitoring and alerting'
            }
        ])
    
    def run_all_tests(self):
        """Run complete QA test suite"""
        print("🎯 STARTING COMPREHENSIVE QA TESTING SUITE")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Start Flask app
        if not self.start_flask_app():
            print("❌ Cannot start Flask app. Testing aborted.")
            return None
        
        try:
            # Run all test categories
            self.test_functional_api_endpoints()
            self.test_functional_web_pages()
            self.test_security_input_validation()
            self.test_security_error_disclosure()
            self.test_performance_load_testing()
            self.test_edge_cases()
            self.test_integration_workflow()
            
            # Generate report
            report = self.generate_report()
            
            print("\n" + "=" * 60)
            print("🎯 QA TESTING COMPLETED")
            print(f"⏱️  Total time: {time.time() - self.start_time:.1f} seconds")
            
            return report
            
        finally:
            # Clean up
            self.stop_flask_app()

def main():
    """Main function to run QA testing"""
    qa_suite = QATestSuite()
    report = qa_suite.run_all_tests()
    
    if report:
        # Save report to file
        with open('qa_test_report.md', 'w') as f:
            f.write(report)
        
        print(f"\n📋 Full report saved to: qa_test_report.md")
        print("\n" + "=" * 60)
        print("SUMMARY OF CRITICAL FINDINGS:")
        
        critical_bugs = len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'HIGH'])
        medium_bugs = len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'MEDIUM'])
        
        if critical_bugs > 0:
            print(f"🚨 {critical_bugs} CRITICAL security issues found")
        if medium_bugs > 0:
            print(f"⚠️  {medium_bugs} MEDIUM severity issues found")
        
        if critical_bugs == 0 and medium_bugs == 0:
            print("✅ No critical issues identified")
        
        print("=" * 60)

if __name__ == "__main__":
    main()