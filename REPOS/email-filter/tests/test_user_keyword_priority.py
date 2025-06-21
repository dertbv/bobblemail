#!/usr/bin/env python3
"""
Test User Keyword Priority

This script tests whether user keywords in my_keywords.txt properly override 
system classifications, especially for investment-related terms like trump, elon, tesla.
"""

import sys
sys.path.append('.')

from utils import load_simple_filters
from spam_classifier import check_message_optimized, compile_patterns_optimized

def test_user_keyword_priority():
    """Test that user keywords take priority over system classifications"""
    
    print("🧪 Testing User Keyword Priority...")
    
    # Load user keywords from my_keywords.txt
    simple_filters = load_simple_filters()
    print(f"📋 Loaded {len(simple_filters)} user keywords from my_keywords.txt")
    
    # Check specific user keywords
    user_keywords = ['trump', 'elon', 'tesla', 'vance']
    print(f"\n🔍 Checking user-specified keywords: {user_keywords}")
    
    for keyword in user_keywords:
        if keyword in simple_filters:
            print(f"  ✅ '{keyword}' found in user keywords")
        else:
            print(f"  ❌ '{keyword}' NOT found in user keywords")
    
    # Compile patterns for testing
    compiled_patterns = compile_patterns_optimized(simple_filters)
    
    # Test emails with user keywords
    test_emails = [
        {
            'subject': 'Trump announces new economic policy',
            'headers': 'From: news@example.com\nSubject: Trump announces new economic policy',
            'expected': 'Should be flagged by user keyword "trump"'
        },
        {
            'subject': 'Elon Musk Tesla announcement',
            'headers': 'From: investor@example.com\nSubject: Elon Musk Tesla announcement', 
            'expected': 'Should be flagged by user keywords "elon" and "tesla"'
        },
        {
            'subject': 'Tesla stock price analysis',
            'headers': 'From: finance@example.com\nSubject: Tesla stock price analysis',
            'expected': 'Should be flagged by user keyword "tesla"'
        }
    ]
    
    print(f"\n🧪 Testing email content against user keywords...")
    
    for i, test_email in enumerate(test_emails, 1):
        print(f"\n--- Test {i} ---")
        print(f"Subject: {test_email['subject']}")
        print(f"Expected: {test_email['expected']}")
        
        # Test keyword matching
        keyword_match, keyword_reason = check_message_optimized(
            test_email['headers'], 
            simple_filters, 
            compiled_patterns
        )
        
        if keyword_match:
            print(f"  ✅ FLAGGED: {keyword_reason}")
        else:
            print(f"  ❌ NOT FLAGGED: No user keyword match found")
    
    print(f"\n📊 Summary:")
    print(f"  • User keywords loaded: {len(simple_filters)}")
    print(f"  • Key user terms: {[k for k in user_keywords if k in simple_filters]}")
    print(f"  • Missing user terms: {[k for k in user_keywords if k not in simple_filters]}")

def check_keyword_integration_logic():
    """Check how user keywords integrate with spam classifier"""
    
    print(f"\n🔧 Checking keyword integration logic...")
    
    # Test the classification priority
    from spam_classifier import classify_spam_type
    from keyword_processor import keyword_processor
    
    # Test trump content (should be flagged by user keyword, not Investment Spam)
    test_subject = "Trump's latest investment announcement"
    test_headers = f"Subject: {test_subject}\nFrom: news@example.com"
    
    print(f"\nTesting: '{test_subject}'")
    
    # Check spam classifier result
    spam_result = keyword_processor.process_keywords(test_headers, "news@example.com", test_subject)
    print(f"  Spam Classifier: {spam_result}")
    
    # Check user keyword result
    simple_filters = load_simple_filters()
    compiled_patterns = compile_patterns_optimized(simple_filters)
    keyword_match, keyword_reason = check_message_optimized(test_headers, simple_filters, compiled_patterns)
    
    print(f"  User Keywords: {'FLAGGED' if keyword_match else 'NOT FLAGGED'} - {keyword_reason}")
    
    # User keywords should take precedence!
    if keyword_match:
        print(f"  ✅ USER KEYWORD SHOULD OVERRIDE: {keyword_reason}")
    else:
        print(f"  ❌ PROBLEM: User keyword not detecting content with 'trump'")

if __name__ == "__main__":
    test_user_keyword_priority()
    check_keyword_integration_logic()