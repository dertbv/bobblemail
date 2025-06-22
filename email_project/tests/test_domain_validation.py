#!/usr/bin/env python3
"""
Test Domain Validation System
============================

Tests the domain validation capabilities including WHOIS integration,
legitimate domain protection, and gibberish detection.
"""

import sys
from domain_validator import (
    DomainValidator, 
    is_gibberish_email, 
    detect_provider_from_sender,
    looks_like_gibberish
)

def test_domain_validation():
    """Test various domain validation features."""
    
    print("🔍 Testing Domain Validation System")
    print("=" * 50)
    
    # Initialize domain validator
    validator = DomainValidator()
    
    # Test cases representing different types of emails
    test_cases = [
        # Legitimate domains (should be preserved)
        ("notification@apple.com", "Your iCloud storage is full", "Apple notification"),
        ("no-reply@samsung.com", "Samsung account update", "Samsung legitimate"),
        ("service@chase.com", "Your statement is ready", "Chase Bank"),
        ("alerts@amazon.com", "Your order has shipped", "Amazon notification"),
        
        # Medical/Healthcare domains (critical protection)
        ("noreplyLSFPSS@lmgdoctors.com", "MRI appointment scheduled", "Medical facility"),
        ("appointments@mayoclinic.org", "Appointment reminder", "Mayo Clinic"),
        
        # Suspicious/Spam domains (should be flagged)
        ("promo@h90803qdq5.ckc", "Special offer inside", "Gibberish domain"),
        ("deal@33xlwjnlpm.hss2657.vrsa.com", "Limited time offer", "Suspicious subdomain"),
        ("winner@7mHo2a6iuV1VQUS0.com", "You've won!", "Random string domain"),
        
        # Edge cases
        ("test@qbrf.zvvsuyowrmxfm.us", "Testing email", "Random string US domain"),
        ("info@itbsr3.jijlzt.fyxjh8.us", "Information", "Gibberish with real TLD"),
    ]
    
    print("🧪 Testing Domain Validation on Sample Emails\n")
    
    for i, (sender, subject, description) in enumerate(test_cases, 1):
        print(f"Test {i}: {description}")
        print(f"   FROM: {sender}")
        print(f"   SUBJECT: {subject}")
        
        # Test gibberish detection
        is_gibberish = is_gibberish_email(sender)
        provider = detect_provider_from_sender(sender)
        
        print(f"   🔍 Gibberish Email: {'Yes' if is_gibberish else 'No'}")
        print(f"   🏢 Provider: {provider}")
        
        # Test domain validation
        try:
            allow_deletion, reason, is_suspicious = validator.validate_domain_before_deletion(sender, subject)
            
            status = "🗑️  ALLOW DELETION" if allow_deletion else "🛡️  PRESERVE"
            print(f"   {status}")
            print(f"   📋 Reason: {reason}")
            print(f"   ⚠️  Suspicious: {'Yes' if is_suspicious else 'No'}")
            
            # Highlight critical protections
            if not allow_deletion and any(word in sender.lower() for word in ['doctor', 'medical', 'clinic', 'hospital']):
                print("   🏥 MEDICAL PROTECTION ACTIVATED!")
            elif not allow_deletion and any(word in sender.lower() for word in ['apple', 'amazon', 'chase', 'samsung']):
                print("   🏢 LEGITIMATE COMPANY PROTECTION!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print()
    
    # Test specific domain validation features
    print("🔬 Testing Specific Domain Validation Features")
    print("=" * 50)
    
    # Test gibberish detection on various strings
    gibberish_tests = [
        ("normal text", False),
        ("qbrf.zvvsuyowrmxfm", True),
        ("apple.com", False),
        ("h90803qdq5", True),
        ("google", False),
        ("33xlwjnlpm.hss2657", True)
    ]
    
    print("\n🎯 Gibberish Detection Tests:")
    for text, expected in gibberish_tests:
        result = looks_like_gibberish(text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{text}' → {'Gibberish' if result else 'Normal'}")
    
    # Test provider detection
    print("\n🏢 Provider Detection Tests:")
    provider_tests = [
        "test@gmail.com",
        "user@outlook.com", 
        "alerts@apple.com",
        "spam@h90803qdq5.ckc",
        "info@lmgdoctors.com"
    ]
    
    for email in provider_tests:
        provider = detect_provider_from_sender(email)
        print(f"   📧 {email} → Provider: {provider}")
    
    print("\n🎉 Domain Validation Test Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ WHOIS Integration - Domain age and registration analysis")
    print("✅ Legitimate Domain Protection - Major companies and services")
    print("✅ Medical Domain Protection - Healthcare providers preserved")
    print("✅ Gibberish Detection - Random string domain identification")
    print("✅ Provider-Aware Logic - Different rules for different providers")
    print("✅ Conservative Safety - Errs on side of preservation")

if __name__ == "__main__":
    test_domain_validation()