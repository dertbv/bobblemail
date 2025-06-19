#!/usr/bin/env python3
"""
Test the integrated logical classifier system
"""

import sys
sys.path.append('.')

from keyword_processor import keyword_processor

def test_integrated_classification():
    """Test the integrated logical classifier in the keyword processor"""
    
    print("🧪 Testing Integrated Logical Classification System")
    print("=" * 60)
    
    # Test cases from the problematic emails
    test_emails = [
        # Adult content
        ("FUCK👅ME..    <f3qkt4dxpvr@yun>", "Adult explicit subject"),
        
        # Brand impersonation
        ("Walmart🛒 <dcev2ty2xi@RcwMvw2k>", "You have won an 𝐢𝐏𝐚𝐝 𝐏𝐫𝐨🎁"),
        ("Temu® <gf6wiz1opl@orvr.ua8w8q>", "✅ 🎉Congrats!! dertbv: You're the winner"),
        
        # Financial spam
        ("Elon's AI Revolution || DI<em>", "Post-2025: Musk's Vision for AI Dominance"),
        ("Trump Musk Showdown | UFG <ne>", "The Feud Between Trump and Musk Is Just"),
        
        # Legitimate promotional
        ("SKECHERS <no-reply@emails.skechers.com>", "Father's Day Deals End Tonight"),
        ("Wrangler <wrangler@e.wrangler.com>", "30% off sitewide ends tomorrow"),
        
        # DOGE stimulus (should be Financial & Investment Spam)
        ("DOGE Checks Dropped, Jacob Davis | FIU <expert@research.firstinvestmentupdates.com>", "Did You Just Get a $5,000 DOGE Stimulus Check?")
    ]
    
    for sender, subject in test_emails:
        # Test the integrated classification
        result = keyword_processor.process_keywords("", sender, subject, "")
        confidence = getattr(keyword_processor, 'last_classification_confidence', 0.0)
        
        print(f"📧 {sender}")
        print(f"   Subject: {subject}")
        print(f"   Classification: {result}")
        print(f"   Confidence: {confidence:.2f}")
        print()
    
    print("✅ Integration test complete!")


if __name__ == "__main__":
    test_integrated_classification()