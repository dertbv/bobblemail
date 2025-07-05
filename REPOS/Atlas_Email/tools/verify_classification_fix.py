#!/usr/bin/env python3
"""Verify that spam emails are now properly classified"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("🧪 Testing classification fix for spam emails...\n")

# Test with keyword processor directly (what will be used with AB testing disabled)
from atlas_email.filters.keyword_processor import KeywordProcessor
kp = KeywordProcessor()

test_cases = [
    ("Trump Infrastructure <noreply@trumpboom.com>", "Trump's infrastructure boom - Trump just greenlit America's infrastructure"),
    ("Laser News <alerts@laserstrike.net>", "[Horrifying Laser Strike] • R [Jul 4, 2025] | Forget the hype. This A"),
    ("peacock® <ohyzvtkdwpc@xgsrksd>", "dertbv: 🛑 Payment-Declined-Order#0074-7")
]

spam_categories = [
    'Financial & Investment Spam', 'Gambling Spam', 'Health & Medical Spam',
    'Adult & Dating Spam', 'Business Opportunity Spam', 'Brand Impersonation',
    'Payment Scam', 'Phishing', 'Education/Training Spam', 'Real Estate Spam',
    'Legal & Compensation Scams', 'Marketing Spam', 'Promotional Email'
]

print("Results with AB Testing DISABLED (using keyword processor):\n")

all_correct = True
for sender, subject in test_cases:
    category = kp.process_keywords("", sender, subject)
    is_spam = category in spam_categories
    
    print(f"📧 {subject[:50]}...")
    print(f"   Sender: {sender}")
    print(f"   Category: {category}")
    print(f"   Is Spam: {is_spam}")
    print(f"   Action: {'🗑️ DELETE' if is_spam else '❌ PRESERVE'}")
    
    if not is_spam or category == "Error":
        all_correct = False
        print(f"   ⚠️ PROBLEM: Should be classified as spam!")
    else:
        print(f"   ✅ CORRECT: Properly classified as spam")
    print()

if all_correct:
    print("✅ SUCCESS: All test emails are now properly classified as spam!")
    print("   They will be DELETED instead of preserved.")
else:
    print("❌ FAILED: Some emails are still not being classified correctly.")
    print("   AB testing is disabled, so the issue must be in keyword_processor.")