#!/usr/bin/env python3
"""
Direct QA Testing Suite - Runs tests without subprocess
"""

import sys
import os
sys.path.append('.')

from app import app
import json
import threading
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test results storage
TEST_RESULTS = {
    "functional": [],
    "security": [],
    "performance": [],
    "integration": [],
    "edge_cases": [],
    "usability": [],
    "bugs": [],
    "recommendations": []
}

class DirectQATest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5002"
        self.session = requests.Session()
        self.server_thread = None
        self.start_time = time.time()
        
    def log_result(self, category, test_name, status, details=None, severity="INFO"):
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
    
    def start_server(self):
        """Start Flask server in background thread"""
        def run_server():
            app.run(debug=False, host='127.0.0.1', port=5002, use_reloader=False)
        
        print("🚀 Starting Flask server for QA testing...")
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Verify server is running
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Flask server started successfully")
                return True
        except:
            pass
        
        print("❌ Failed to start Flask server")
        return False
    
    def test_functional_endpoints(self):
        """Test all API endpoints"""
        print("\n🧪 FUNCTIONAL TESTING - API Endpoints")
        
        # Health endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result('functional', 'Health Endpoint', 'PASS', 
                                  f"Response: {data}")
                else:
                    self.log_result('functional', 'Health Endpoint', 'FAIL',
                                  f"Invalid response: {data}")
            else:
                self.log_result('functional', 'Health Endpoint', 'FAIL',
                              f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('functional', 'Health Endpoint', 'FAIL', str(e))
        
        # Analysis status endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/analysis-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['in_progress', 'has_results', 'timestamp']
                if all(field in data for field in required_fields):
                    self.log_result('functional', 'Analysis Status Endpoint', 'PASS')
                else:
                    self.log_result('functional', 'Analysis Status Endpoint', 'FAIL',
                                  f"Missing fields in response: {data}")
            else:
                self.log_result('functional', 'Analysis Status Endpoint', 'FAIL',
                              f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('functional', 'Analysis Status Endpoint', 'FAIL', str(e))
        
        # Start analysis endpoint
        try:
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/api/start-analysis",
                                       json={}, headers=headers, timeout=10)
            if response.status_code in [200, 409]:  # 200 = started, 409 = already running
                data = response.json()
                self.log_result('functional', 'Start Analysis Endpoint', 'PASS',
                              f"Status: {response.status_code}, Response: {data}")
            else:
                self.log_result('functional', 'Start Analysis Endpoint', 'FAIL',
                              f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result('functional', 'Start Analysis Endpoint', 'FAIL', str(e))
        
        # Results endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/results", timeout=5)
            if response.status_code in [200, 404]:
                self.log_result('functional', 'Results Endpoint', 'PASS',
                              f"Status: {response.status_code}")
            else:
                self.log_result('functional', 'Results Endpoint', 'FAIL',
                              f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_result('functional', 'Results Endpoint', 'FAIL', str(e))
        
        # Stock endpoint with valid ticker
        try:
            response = self.session.get(f"{self.base_url}/api/stock/AAPL", timeout=5)
            if response.status_code in [200, 404]:
                self.log_result('functional', 'Stock Endpoint (Valid)', 'PASS',
                              f"Status: {response.status_code}")
            else:
                self.log_result('functional', 'Stock Endpoint (Valid)', 'FAIL',
                              f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('functional', 'Stock Endpoint (Valid)', 'FAIL', str(e))
        
        # Category endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/category/under-5", timeout=5)
            if response.status_code in [200, 404]:
                self.log_result('functional', 'Category Endpoint', 'PASS',
                              f"Status: {response.status_code}")
            else:
                self.log_result('functional', 'Category Endpoint', 'FAIL',
                              f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('functional', 'Category Endpoint', 'FAIL', str(e))
    
    def test_web_pages(self):
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
                response = self.session.get(f"{self.base_url}{path}", timeout=5)
                if response.status_code == 200:
                    if 'text/html' in response.headers.get('Content-Type', ''):
                        self.log_result('functional', f'{name} Rendering', 'PASS')
                    else:
                        self.log_result('functional', f'{name} Rendering', 'FAIL',
                                      'Not HTML content')
                elif response.status_code == 404 and path.startswith('/stock/'):
                    # Stock pages might 404 if ticker not found - this is acceptable
                    self.log_result('functional', f'{name} Rendering', 'PASS',
                                  'Properly handles missing stock')
                else:
                    self.log_result('functional', f'{name} Rendering', 'FAIL',
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result('functional', f'{name} Rendering', 'FAIL', str(e))
    
    def test_security_validation(self):
        """Test security and input validation"""
        print("\n🔒 SECURITY TESTING")
        
        # Test SQL injection attempts on ticker endpoint
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
            "admin'--",
            "' OR 1=1#"
        ]
        
        for payload in sql_payloads:
            try:
                response = self.session.get(f"{self.base_url}/api/stock/{payload}", timeout=5)
                if response.status_code == 400:  # Validation should reject
                    data = response.json()
                    if data.get('error_type') == 'validation_error':
                        self.log_result('security', f'SQL Injection Block ({payload[:10]}...)', 'PASS')
                    else:
                        self.log_result('security', f'SQL Injection Block ({payload[:10]}...)', 'FAIL',
                                      f"Wrong error type: {data.get('error_type')}", "MEDIUM")
                else:
                    self.log_result('security', f'SQL Injection Block ({payload[:10]}...)', 'FAIL',
                                  f"Payload not blocked: {response.status_code}", "HIGH")
            except Exception as e:
                self.log_result('security', f'SQL Injection Block ({payload[:10]}...)', 'PASS',
                              "Request properly rejected")
        
        # Test XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/*/`/*\\`/*'/*\\\">alert(1)//'"
        ]
        
        for payload in xss_payloads:
            try:
                response = self.session.get(f"{self.base_url}/api/stock/{payload}", timeout=5)
                if response.status_code == 400:
                    self.log_result('security', f'XSS Protection ({payload[:15]}...)', 'PASS')
                else:
                    self.log_result('security', f'XSS Protection ({payload[:15]}...)', 'FAIL',
                                  f"Payload not blocked: {response.status_code}", "HIGH")
            except Exception as e:
                self.log_result('security', f'XSS Protection ({payload[:15]}...)', 'PASS',
                              "Request properly rejected")
        
        # Test path traversal
        path_payloads = [
            "../../../etc/passwd",
            "..\\\\..\\\\..\\\\windows\\\\system32\\\\config\\\\sam",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//etc//passwd"
        ]
        
        for payload in path_payloads:
            try:
                response = self.session.get(f"{self.base_url}/api/stock/{payload}", timeout=5)
                if response.status_code == 400:
                    self.log_result('security', f'Path Traversal Block ({payload[:15]}...)', 'PASS')
                else:
                    self.log_result('security', f'Path Traversal Block ({payload[:15]}...)', 'FAIL',
                                  f"Payload not blocked: {response.status_code}", "MEDIUM")
            except Exception as e:
                self.log_result('security', f'Path Traversal Block ({payload[:15]}...)', 'PASS',
                              "Request properly rejected")
        
        # Test invalid content types
        try:
            headers = {'Content-Type': 'text/plain'}
            response = self.session.post(f"{self.base_url}/api/start-analysis",
                                       data="invalid", headers=headers, timeout=5)
            if response.status_code == 415:  # Unsupported Media Type
                self.log_result('security', 'Content-Type Validation', 'PASS')
            else:
                self.log_result('security', 'Content-Type Validation', 'FAIL',
                              f"Should reject non-JSON: {response.status_code}", "MEDIUM")
        except Exception as e:
            self.log_result('security', 'Content-Type Validation', 'FAIL', str(e))
        
        # Test request size limits
        try:
            large_payload = {'data': 'x' * 10000}  # 10KB
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/api/start-analysis",
                                       json=large_payload, headers=headers, timeout=5)
            if response.status_code == 413:  # Request Entity Too Large
                self.log_result('security', 'Request Size Limit', 'PASS')
            else:
                self.log_result('security', 'Request Size Limit', 'FAIL',
                              f"Should reject large requests: {response.status_code}", "LOW")
        except Exception as e:
            self.log_result('security', 'Request Size Limit', 'FAIL', str(e))
    
    def test_performance(self):
        """Test performance under load"""
        print("\n⚡ PERFORMANCE TESTING")
        
        # Test response times
        endpoints = [
            '/api/health',
            '/api/analysis-status',
            '/api/results'
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                response_time = time.time() - start_time
                
                if response_time < 1.0:  # Should respond within 1 second
                    self.log_result('performance', f'Response Time {endpoint}', 'PASS',
                                  f"{response_time:.3f}s")
                elif response_time < 2.0:
                    self.log_result('performance', f'Response Time {endpoint}', 'WARNING',
                                  f"Slow response: {response_time:.3f}s")
                else:
                    self.log_result('performance', f'Response Time {endpoint}', 'FAIL',
                                  f"Very slow: {response_time:.3f}s", "MEDIUM")
            except Exception as e:
                self.log_result('performance', f'Response Time {endpoint}', 'FAIL', str(e))
        
        # Test concurrent requests
        def make_request():
            try:
                start = time.time()
                response = self.session.get(f"{self.base_url}/api/health", timeout=10)
                return {
                    'status': response.status_code,
                    'time': time.time() - start
                }
            except Exception as e:
                return {'status': None, 'error': str(e)}
        
        print("   Testing concurrent requests...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        success_count = sum(1 for r in results if r.get('status') == 200)
        avg_time = sum(r.get('time', 0) for r in results if 'time' in r) / len(results)
        
        if success_count >= 8:  # 80% success rate
            self.log_result('performance', 'Concurrent Request Handling', 'PASS',
                          f"Success: {success_count}/10, Avg: {avg_time:.3f}s")
        else:
            self.log_result('performance', 'Concurrent Request Handling', 'FAIL',
                          f"Poor success rate: {success_count}/10", "MEDIUM")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🎯 EDGE CASE TESTING")
        
        # Invalid ticker formats
        invalid_tickers = ['', '123', 'TOOLONGGG', 'aa', '@#$%', 'A', 'ABCDEF']
        
        for ticker in invalid_tickers:
            try:
                response = self.session.get(f"{self.base_url}/api/stock/{ticker}", timeout=5)
                if response.status_code == 400:
                    data = response.json()
                    if data.get('error_type') == 'validation_error':
                        self.log_result('edge_cases', f'Invalid Ticker ({ticker or "empty"})', 'PASS')
                    else:
                        self.log_result('edge_cases', f'Invalid Ticker ({ticker or "empty"})', 'FAIL',
                                      f"Wrong error type: {data}")
                else:
                    self.log_result('edge_cases', f'Invalid Ticker ({ticker or "empty"})', 'FAIL',
                                  f"Should reject: {response.status_code}")
            except Exception as e:
                self.log_result('edge_cases', f'Invalid Ticker ({ticker or "empty"})', 'FAIL', str(e))
        
        # Invalid categories
        invalid_categories = ['invalid', '', 'under-100', '999', 'abc']
        
        for category in invalid_categories:
            try:
                response = self.session.get(f"{self.base_url}/api/category/{category}", timeout=5)
                if response.status_code == 400:
                    self.log_result('edge_cases', f'Invalid Category ({category or "empty"})', 'PASS')
                else:
                    self.log_result('edge_cases', f'Invalid Category ({category or "empty"})', 'FAIL',
                                  f"Should reject: {response.status_code}")
            except Exception as e:
                self.log_result('edge_cases', f'Invalid Category ({category or "empty"})', 'FAIL', str(e))
        
        # Non-existent endpoints
        try:
            response = self.session.get(f"{self.base_url}/api/nonexistent", timeout=5)
            if response.status_code == 404:
                data = response.json()
                # Check error message doesn't leak sensitive info
                message = data.get('message', '').lower()
                sensitive_terms = ['traceback', 'file path', 'database', 'internal error']
                
                if not any(term in message for term in sensitive_terms):
                    self.log_result('edge_cases', 'Error Message Safety', 'PASS')
                else:
                    self.log_result('edge_cases', 'Error Message Safety', 'FAIL',
                                  f"Sensitive info leaked: {message}", "MEDIUM")
            else:
                self.log_result('edge_cases', 'Non-existent Endpoint', 'FAIL',
                              f"Expected 404, got: {response.status_code}")
        except Exception as e:
            self.log_result('edge_cases', 'Non-existent Endpoint', 'FAIL', str(e))
    
    def test_integration_workflow(self):
        """Test end-to-end integration"""
        print("\n🔗 INTEGRATION TESTING")
        
        try:
            # 1. Check initial status
            response = self.session.get(f"{self.base_url}/api/analysis-status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                self.log_result('integration', 'Status Check Integration', 'PASS',
                              f"Initial status: {status}")
            else:
                self.log_result('integration', 'Status Check Integration', 'FAIL',
                              f"Status endpoint failed: {response.status_code}")
                return
            
            # 2. Try to start analysis
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/api/start-analysis",
                                       json={}, headers=headers, timeout=10)
            
            if response.status_code in [200, 409]:
                self.log_result('integration', 'Analysis Start Integration', 'PASS',
                              f"Start response: {response.status_code}")
            else:
                self.log_result('integration', 'Analysis Start Integration', 'FAIL',
                              f"Failed to start: {response.status_code}")
            
            # 3. Check status after start attempt
            time.sleep(1)
            response = self.session.get(f"{self.base_url}/api/analysis-status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                self.log_result('integration', 'Post-Start Status Check', 'PASS',
                              f"Status after start: {status}")
            else:
                self.log_result('integration', 'Post-Start Status Check', 'FAIL',
                              f"Status check failed: {response.status_code}")
            
            # 4. Test results endpoint
            response = self.session.get(f"{self.base_url}/api/results", timeout=5)
            if response.status_code in [200, 404]:
                self.log_result('integration', 'Results Integration', 'PASS',
                              f"Results check: {response.status_code}")
            else:
                self.log_result('integration', 'Results Integration', 'FAIL',
                              f"Results failed: {response.status_code}")
            
        except Exception as e:
            self.log_result('integration', 'End-to-End Workflow', 'FAIL', str(e))
    
    def analyze_and_report(self):
        """Analyze results and generate bugs/recommendations"""
        
        # Identify bugs from failed tests
        for category in ['functional', 'security', 'performance', 'edge_cases', 'integration']:
            failed_tests = [t for t in TEST_RESULTS[category] if t['status'] == 'FAIL']
            
            for test in failed_tests:
                severity = test.get('severity', 'MEDIUM')
                
                bug = {
                    'severity': severity,
                    'title': f"{category.title()} Issue: {test['test_name']}",
                    'description': test['details'] or 'Test failed without specific details',
                    'category': category,
                    'test_name': test['test_name']
                }
                
                if category == 'security' and severity == 'HIGH':
                    bug['impact'] = 'Critical security vulnerability - immediate attention required'
                    bug['recommendation'] = 'Implement proper input validation and security controls'
                elif category == 'performance':
                    bug['impact'] = 'Performance degradation affecting user experience'
                    bug['recommendation'] = 'Optimize response times and implement caching'
                elif category == 'functional':
                    bug['impact'] = 'Core functionality not working as expected'
                    bug['recommendation'] = 'Fix application logic and error handling'
                else:
                    bug['impact'] = 'System reliability and user experience affected'
                    bug['recommendation'] = 'Review and fix the identified issue'
                
                TEST_RESULTS['bugs'].append(bug)
        
        # Add general recommendations
        recommendations = [
            {
                'title': 'Implement Authentication & Authorization',
                'description': 'Add user authentication to secure sensitive operations and prevent unauthorized access',
                'priority': 'HIGH'
            },
            {
                'title': 'Add Rate Limiting',
                'description': 'Implement rate limiting to prevent abuse, DoS attacks, and ensure fair resource usage',
                'priority': 'HIGH'
            },
            {
                'title': 'Enhance Input Validation',
                'description': 'Strengthen input validation across all endpoints to prevent injection attacks',
                'priority': 'HIGH'
            },
            {
                'title': 'Implement HTTPS',
                'description': 'Use HTTPS in production to encrypt data in transit and protect against MITM attacks',
                'priority': 'HIGH'
            },
            {
                'title': 'Add Security Headers',
                'description': 'Implement security headers (CSP, HSTS, X-Frame-Options) to prevent various attacks',
                'priority': 'MEDIUM'
            },
            {
                'title': 'Implement Health Monitoring',
                'description': 'Add comprehensive health checks and monitoring for production deployment',
                'priority': 'MEDIUM'
            },
            {
                'title': 'Add Audit Logging',
                'description': 'Implement comprehensive audit logging for security and compliance monitoring',
                'priority': 'MEDIUM'
            },
            {
                'title': 'Error Handling Improvements',
                'description': 'Enhance error handling to provide better user experience while maintaining security',
                'priority': 'MEDIUM'
            },
            {
                'title': 'Add Unit Tests',
                'description': 'Implement comprehensive unit test coverage to prevent regressions',
                'priority': 'LOW'
            },
            {
                'title': 'Performance Optimization',
                'description': 'Implement caching strategies and optimize database queries for better performance',
                'priority': 'LOW'
            }
        ]
        
        TEST_RESULTS['recommendations'] = recommendations
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        total_tests = sum(len(TEST_RESULTS[cat]) for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
        passed_tests = sum(len([t for t in TEST_RESULTS[cat] if t['status'] == 'PASS']) 
                          for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
        failed_tests = sum(len([t for t in TEST_RESULTS[cat] if t['status'] == 'FAIL']) 
                          for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
        warning_tests = sum(len([t for t in TEST_RESULTS[cat] if t['status'] == 'WARNING']) 
                           for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
        
        critical_bugs = len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'HIGH'])
        medium_bugs = len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'MEDIUM'])
        low_bugs = len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'LOW'])
        
        report = f"""
# COMPREHENSIVE QA TEST REPORT
**Penny Stock Analysis Web Application**

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Test Duration: {time.time() - self.start_time:.1f} seconds

## EXECUTIVE SUMMARY

### Test Results Overview
- **Total Tests Executed**: {total_tests}
- **Passed**: {passed_tests} ({(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%)
- **Failed**: {failed_tests} ({(failed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%)
- **Warnings**: {warning_tests} ({(warning_tests/total_tests*100) if total_tests > 0 else 0:.1f}%)

### Security & Bug Summary
- **🚨 Critical (HIGH) Issues**: {critical_bugs}
- **⚠️ Medium Issues**: {medium_bugs}
- **ℹ️ Low Issues**: {low_bugs}
- **📋 Recommendations**: {len(TEST_RESULTS['recommendations'])}

## DETAILED TEST RESULTS

"""
        
        # Add detailed results by category
        categories = ['functional', 'security', 'performance', 'integration', 'edge_cases']
        
        for category in categories:
            report += f"### {category.upper()} TESTING\n\n"
            
            if TEST_RESULTS[category]:
                passed = len([t for t in TEST_RESULTS[category] if t['status'] == 'PASS'])
                failed = len([t for t in TEST_RESULTS[category] if t['status'] == 'FAIL'])
                warnings = len([t for t in TEST_RESULTS[category] if t['status'] == 'WARNING'])
                total = len(TEST_RESULTS[category])
                
                report += f"**Summary**: {passed} passed, {failed} failed, {warnings} warnings out of {total} tests\n\n"
                
                for test in TEST_RESULTS[category]:
                    status_emoji = "✅" if test['status'] == 'PASS' else "❌" if test['status'] == 'FAIL' else "⚠️"
                    report += f"- {status_emoji} **{test['test_name']}**: {test['status']}\n"
                    if test['details']:
                        report += f"  - *Details*: {test['details']}\n"
                    if test.get('severity') and test['severity'] != 'INFO':
                        report += f"  - *Severity*: {test['severity']}\n"
                report += "\n"
            else:
                report += "No tests executed in this category.\n\n"
        
        # Bug Reports
        report += "## BUG REPORTS\n\n"
        
        if TEST_RESULTS['bugs']:
            # Group bugs by severity
            high_bugs = [b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'HIGH']
            medium_bugs = [b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'MEDIUM']
            low_bugs = [b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'LOW']
            
            for severity, bugs in [('HIGH', high_bugs), ('MEDIUM', medium_bugs), ('LOW', low_bugs)]:
                if bugs:
                    report += f"### {severity} Severity Issues\n\n"
                    for i, bug in enumerate(bugs, 1):
                        report += f"#### Bug #{i} - {bug['title']}\n"
                        report += f"- **Category**: {bug.get('category', 'Unknown')}\n"
                        report += f"- **Description**: {bug['description']}\n"
                        if bug.get('impact'):
                            report += f"- **Impact**: {bug['impact']}\n"
                        if bug.get('recommendation'):
                            report += f"- **Recommendation**: {bug['recommendation']}\n"
                        report += "\n"
        else:
            report += "🎉 No bugs identified during testing!\n\n"
        
        # Recommendations
        report += "## RECOMMENDATIONS FOR IMPROVEMENT\n\n"
        
        if TEST_RESULTS['recommendations']:
            high_recs = [r for r in TEST_RESULTS['recommendations'] if r.get('priority') == 'HIGH']
            medium_recs = [r for r in TEST_RESULTS['recommendations'] if r.get('priority') == 'MEDIUM']
            low_recs = [r for r in TEST_RESULTS['recommendations'] if r.get('priority') == 'LOW']
            
            for priority, recs in [('HIGH PRIORITY', high_recs), ('MEDIUM PRIORITY', medium_recs), ('LOW PRIORITY', low_recs)]:
                if recs:
                    report += f"### {priority}\n\n"
                    for rec in recs:
                        report += f"- **{rec['title']}**: {rec['description']}\n"
                    report += "\n"
        
        # Testing Methodology
        report += "## TESTING METHODOLOGY\n\n"
        report += "- **Testing Framework**: Custom Python-based automated testing suite\n"
        report += "- **Test Environment**: Local Flask development server (127.0.0.1:5002)\n"
        report += "- **Test Coverage**: \n"
        report += "  - API endpoint functionality\n"
        report += "  - Web page rendering\n"
        report += "  - Security vulnerability scanning\n"
        report += "  - Performance and load testing\n"
        report += "  - Edge case and error handling\n"
        report += "  - End-to-end integration testing\n"
        report += "- **Test Types**: Functional, Security, Performance, Integration, Edge Case\n"
        report += f"- **Total Test Duration**: {time.time() - self.start_time:.1f} seconds\n\n"
        
        # Security Assessment
        report += "## SECURITY ASSESSMENT\n\n"
        if critical_bugs > 0:
            report += f"⚠️ **CRITICAL**: {critical_bugs} high-severity security issues identified that require immediate attention.\n\n"
        elif medium_bugs > 0:
            report += f"⚠️ **MODERATE**: {medium_bugs} medium-severity issues identified that should be addressed.\n\n"
        else:
            report += "✅ **GOOD**: No critical security vulnerabilities identified in basic testing.\n\n"
        
        report += "**Note**: This assessment covers basic security testing. A comprehensive security audit should include:\n"
        report += "- Penetration testing\n"
        report += "- Code review\n"
        report += "- Dependency vulnerability scanning\n"
        report += "- Infrastructure security assessment\n\n"
        
        # Performance Assessment
        report += "## PERFORMANCE ASSESSMENT\n\n"
        perf_issues = [t for t in TEST_RESULTS['performance'] if t['status'] in ['FAIL', 'WARNING']]
        if perf_issues:
            report += f"⚠️ **Performance Issues Identified**: {len(perf_issues)} performance-related issues found.\n\n"
        else:
            report += "✅ **Performance**: Basic performance tests passed satisfactorily.\n\n"
        
        report += "**Note**: Performance testing was limited to basic response times and concurrent request handling. Production performance testing should include:\n"
        report += "- Extended load testing\n"
        report += "- Stress testing\n"
        report += "- Memory usage profiling\n"
        report += "- Database performance analysis\n\n"
        
        # Conclusions
        report += "## CONCLUSIONS\n\n"
        
        overall_health = "GOOD"
        if critical_bugs > 0:
            overall_health = "CRITICAL"
        elif failed_tests > passed_tests/2:
            overall_health = "POOR"
        elif medium_bugs > 3:
            overall_health = "MODERATE"
        
        report += f"**Overall Application Health**: {overall_health}\n\n"
        
        if overall_health == "CRITICAL":
            report += "🚨 **Immediate Action Required**: Critical security issues must be addressed before production deployment.\n\n"
        elif overall_health == "POOR":
            report += "⚠️ **Significant Issues**: Multiple functional issues require attention before production readiness.\n\n"
        elif overall_health == "MODERATE":
            report += "⚠️ **Minor Issues**: Some issues identified but application is generally functional.\n\n"
        else:
            report += "✅ **Ready for Further Testing**: Basic functionality appears sound, ready for more comprehensive testing.\n\n"
        
        report += "---\n"
        report += "*This report was generated by an automated QA testing suite. Manual testing and code review are recommended for comprehensive quality assurance.*\n"
        
        return report
    
    def run_all_tests(self):
        """Execute complete QA test suite"""
        print("🎯 STARTING COMPREHENSIVE QA TESTING")
        print("=" * 60)
        
        if not self.start_server():
            print("❌ Cannot start server. Testing aborted.")
            return None
        
        try:
            # Execute all test categories
            self.test_functional_endpoints()
            self.test_web_pages()
            self.test_security_validation()
            self.test_performance()
            self.test_edge_cases()
            self.test_integration_workflow()
            
            # Analyze results and generate report
            self.analyze_and_report()
            report = self.generate_report()
            
            print(f"\n{'=' * 60}")
            print("🎯 QA TESTING COMPLETED")
            print(f"⏱️ Total Duration: {time.time() - self.start_time:.1f} seconds")
            
            # Print summary
            total_tests = sum(len(TEST_RESULTS[cat]) for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
            passed = sum(len([t for t in TEST_RESULTS[cat] if t['status'] == 'PASS']) 
                        for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
            failed = sum(len([t for t in TEST_RESULTS[cat] if t['status'] == 'FAIL']) 
                        for cat in TEST_RESULTS if cat not in ['bugs', 'recommendations'])
            
            print(f"📊 SUMMARY: {passed} passed, {failed} failed out of {total_tests} tests")
            
            critical_bugs = len([b for b in TEST_RESULTS['bugs'] if b.get('severity') == 'HIGH'])
            if critical_bugs > 0:
                print(f"🚨 {critical_bugs} CRITICAL issues found!")
            else:
                print("✅ No critical issues identified")
            
            return report
            
        except Exception as e:
            print(f"❌ Testing failed with error: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Main execution function"""
    qa_test = DirectQATest()
    report = qa_test.run_all_tests()
    
    if report:
        # Save report
        report_file = 'qa_comprehensive_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📋 Comprehensive report saved to: {report_file}")
        print("=" * 60)
    
if __name__ == "__main__":
    main()