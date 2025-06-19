#!/usr/bin/env python3
"""
Test Email Authentication System
===============================

Tests the new SPF/DKIM validation system with the spoofed Robinhood email case.
Validates that spoofed emails are now properly detected.
"""

import email
from email_authentication import EmailAuthenticator, authenticate_email_headers

def test_spoofed_robinhood_email():
    """Test spoofed Robinhood email detection"""
    print("🧪 Testing Spoofed Robinhood Email Detection")
    print("=" * 50)
    
    # Simulate spoofed email headers (no proper authentication)
    spoofed_headers = """From: Robinhood Support <support@robinhood.com>
To: user@example.com
Subject: Important: Verify Your Withdrawal Request
Date: Thu, 19 Jun 2025 17:00:00 -0400
Message-ID: <fake123@attacker.com>
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

"""
    
    # Test authentication
    auth_result = authenticate_email_headers(spoofed_headers)
    
    print("Authentication Results:")
    print(f"  SPF Result: {auth_result['spf_result']}")
    print(f"  DKIM Result: {auth_result['dkim_result']}")
    print(f"  Is Authentic: {auth_result['is_authentic']}")
    print(f"  Confidence Modifier: {auth_result['confidence_modifier']:+.1f}")
    print(f"  Summary: {auth_result['auth_summary']}")
    
    # Test the impact on classification confidence
    original_confidence = 85.0  # Phishing confidence from content
    adjusted_confidence = original_confidence + auth_result['confidence_modifier']
    adjusted_confidence = max(0.0, min(100.0, adjusted_confidence))
    
    print(f"\nClassification Impact:")
    print(f"  Original Confidence: {original_confidence:.1f}%")
    print(f"  Authentication Adjustment: {auth_result['confidence_modifier']:+.1f}")
    print(f"  Final Confidence: {adjusted_confidence:.1f}%")
    
    # Check if this would catch the spoofed email
    if not auth_result['is_authentic'] and abs(auth_result['confidence_modifier']) > 5.0:
        print(f"✅ SUCCESS: Authentication system would help detect this spoofed email!")
    else:
        print(f"⚠️ WARNING: Authentication system may not catch this spoofing attempt")
    
    return auth_result

def test_legitimate_robinhood_email():
    """Test legitimate Robinhood email with proper authentication"""
    print("\n🧪 Testing Legitimate Robinhood Email")
    print("=" * 50)
    
    # Simulate legitimate email with proper authentication headers
    legitimate_headers = """From: Robinhood Support <support@robinhood.com>
To: user@example.com
Subject: Important: Verify Your Withdrawal Request
Date: Thu, 19 Jun 2025 17:00:00 -0400
Message-ID: <real123@robinhood.com>
Authentication-Results: gmail.com;
    dkim=pass header.i=@robinhood.com header.s=selector1;
    spf=pass (google.com: domain of support@robinhood.com designates 152.70.150.118 as permitted sender) smtp.mailfrom=support@robinhood.com;
    dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=robinhood.com
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=robinhood.com; s=selector1;
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

"""
    
    # Test authentication
    auth_result = authenticate_email_headers(legitimate_headers)
    
    print("Authentication Results:")
    print(f"  SPF Result: {auth_result['spf_result']}")
    print(f"  DKIM Result: {auth_result['dkim_result']}")
    print(f"  Is Authentic: {auth_result['is_authentic']}")
    print(f"  Confidence Modifier: {auth_result['confidence_modifier']:+.1f}")
    print(f"  Summary: {auth_result['auth_summary']}")
    
    # Test the impact on classification confidence
    original_confidence = 85.0  # Phishing confidence from content
    adjusted_confidence = original_confidence + auth_result['confidence_modifier']
    adjusted_confidence = max(0.0, min(100.0, adjusted_confidence))
    
    print(f"\nClassification Impact:")
    print(f"  Original Confidence: {original_confidence:.1f}%")
    print(f"  Authentication Adjustment: {auth_result['confidence_modifier']:+.1f}")
    print(f"  Final Confidence: {adjusted_confidence:.1f}%")
    
    # Check if authentication would help legitimate emails
    if auth_result['is_authentic'] and auth_result['confidence_modifier'] > 0:
        print(f"✅ SUCCESS: Authentication system would help protect legitimate emails!")
    elif auth_result['is_authentic']:
        print(f"ℹ️ NEUTRAL: Authentication passes but no confidence boost")
    else:
        print(f"❌ PROBLEM: Legitimate email fails authentication!")
    
    return auth_result

def test_domain_extraction():
    """Test domain extraction from various From header formats"""
    print("\n🧪 Testing Domain Extraction")
    print("=" * 50)
    
    authenticator = EmailAuthenticator()
    
    test_cases = [
        "Robinhood Support <support@robinhood.com>",
        "support@robinhood.com",
        "\"User Name\" <user@example.com>",
        "noreply@bank.com",
        "Customer Service <cs@company.co.uk>"
    ]
    
    for from_header in test_cases:
        domain = authenticator._extract_domain_from_header(from_header)
        print(f"  '{from_header}' → '{domain}'")
    
    print("✅ Domain extraction test completed")

if __name__ == "__main__":
    print("🔐 Email Authentication System Test Suite")
    print("Testing SPF/DKIM validation for spoofing detection\n")
    
    # Test spoofed email (should be flagged)
    spoofed_result = test_spoofed_robinhood_email()
    
    # Test legitimate email (should pass)
    legitimate_result = test_legitimate_robinhood_email()
    
    # Test domain extraction
    test_domain_extraction()
    
    print(f"\n🎯 Test Summary:")
    print(f"  Spoofed email authentic: {spoofed_result['is_authentic']}")
    print(f"  Legitimate email authentic: {legitimate_result['is_authentic']}")
    print(f"  System can distinguish between spoofed/legitimate: {spoofed_result['is_authentic'] != legitimate_result['is_authentic']}")
    
    if not spoofed_result['is_authentic'] and legitimate_result['is_authentic']:
        print("✅ SUCCESS: Authentication system working correctly!")
    else:
        print("⚠️ NEEDS TUNING: Authentication system needs adjustment")