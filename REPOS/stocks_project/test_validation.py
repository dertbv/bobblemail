#!/usr/bin/env python3
"""
Test script for API input validation
"""

import requests
import json
import sys

# Test configuration
BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api'

def test_ticker_validation():
    """Test ticker validation"""
    print("Testing ticker validation...")
    
    test_cases = [
        # Valid cases
        ('AAPL', True, 'Valid 4-letter ticker'),
        ('MSFT', True, 'Valid 4-letter ticker'),
        ('F', True, 'Valid 1-letter ticker'),
        ('GOOGL', True, 'Valid 5-letter ticker'),
        
        # Invalid cases
        ('', False, 'Empty ticker'),
        ('GOOGL123', False, 'Ticker with numbers'),
        ('goog', False, 'Lowercase ticker'),
        ('GOOGLE', False, 'Ticker too long'),
        ('A@PL', False, 'Ticker with special characters'),
        ('123', False, 'Numbers only'),
    ]
    
    for ticker, should_pass, description in test_cases:
        url = f'{API_BASE}/stock/{ticker}'
        try:
            response = requests.get(url, timeout=5)
            passed = response.status_code != 400
            
            if passed == should_pass:
                print(f"   ✅ {description}: {ticker} - {'PASSED' if should_pass else 'REJECTED'}")
            else:
                print(f"   ❌ {description}: {ticker} - Expected {'PASS' if should_pass else 'REJECT'}, got {'PASS' if passed else 'REJECT'}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  {description}: {ticker} - Request failed: {e}")

def test_category_validation():
    """Test category validation"""
    print("\nTesting category validation...")
    
    test_cases = [
        # Valid cases
        ('under-5', True, 'Valid under-5 category'),
        ('5-to-10', True, 'Valid 5-to-10 category'),
        ('10-to-20', True, 'Valid 10-to-20 category'),
        
        # Invalid cases
        ('under5', False, 'Invalid format'),
        ('over-20', False, 'Non-existent category'),
        ('', False, 'Empty category'),
        ('UNDER-5', False, 'Uppercase category'),
        ('under-5-extended', False, 'Extended invalid category'),
        ('5to10', False, 'Missing dashes'),
    ]
    
    for category, should_pass, description in test_cases:
        url = f'{API_BASE}/category/{category}'
        try:
            response = requests.get(url, timeout=5)
            passed = response.status_code != 400
            
            if passed == should_pass:
                print(f"   ✅ {description}: {category} - {'PASSED' if should_pass else 'REJECTED'}")
            else:
                print(f"   ❌ {description}: {category} - Expected {'PASS' if should_pass else 'REJECT'}, got {'PASS' if passed else 'REJECT'}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  {description}: {category} - Request failed: {e}")

def test_analysis_request_validation():
    """Test analysis request validation"""
    print("\nTesting analysis request validation...")
    
    test_cases = [
        # Valid cases
        ({}, True, 'Empty JSON object'),
        ({'force_restart': True}, True, 'Valid force_restart field'),
        ({'analysis_type': 'standard'}, True, 'Valid analysis_type field'),
        
        # Invalid cases
        ('not_json', False, 'Non-JSON data'),
        ({'invalid_field': True}, False, 'Invalid field'),
        ({'force_restart': True, 'extra_field': 'value'}, False, 'Extra unexpected field'),
    ]
    
    url = f'{API_BASE}/start-analysis'
    
    for data, should_pass, description in test_cases:
        try:
            if isinstance(data, dict):
                response = requests.post(url, json=data, timeout=5)
            else:
                # Send non-JSON data
                response = requests.post(url, data=data, headers={'Content-Type': 'application/json'}, timeout=5)
            
            passed = response.status_code not in [400, 415]  # 400 = validation error, 415 = unsupported media type
            
            if passed == should_pass:
                print(f"   ✅ {description} - {'PASSED' if should_pass else 'REJECTED'}")
            else:
                print(f"   ❌ {description} - Expected {'PASS' if should_pass else 'REJECT'}, got {'PASS' if passed else 'REJECT'}")
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        print(f"      Error: {error_data.get('message', 'Unknown error')}")
                    except:
                        print(f"      HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  {description} - Request failed: {e}")

def test_error_responses():
    """Test error response formats"""
    print("\nTesting error response formats...")
    
    # Test invalid ticker
    response = requests.get(f'{API_BASE}/stock/INVALID123', timeout=5)
    if response.status_code == 400:
        try:
            data = response.json()
            if 'status' in data and 'message' in data:
                print("   ✅ Error response format is consistent")
            else:
                print("   ❌ Error response missing required fields")
        except:
            print("   ❌ Error response is not valid JSON")
    else:
        print(f"   ⚠️  Expected 400 status code, got {response.status_code}")

if __name__ == "__main__":
    print("🧪 API Validation Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f'{API_BASE}/health', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running\n")
        else:
            print(f"❌ Server returned status {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the Flask app first.")
        print("   Run: source venv/bin/activate && python app.py")
        sys.exit(1)
    
    # Run validation tests
    test_ticker_validation()
    test_category_validation()
    test_analysis_request_validation()
    test_error_responses()
    
    print("\n" + "=" * 50)
    print("🏁 Validation tests completed!")