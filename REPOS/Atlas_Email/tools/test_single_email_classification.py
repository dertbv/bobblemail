#!/usr/bin/env python3
"""Test classification of a single email to debug whitelist issue"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
from src.atlas_email.ml.category_classifier import CategoryClassifier
from src.atlas_email.utils.domain_validator import DomainValidator
from src.atlas_email.ml.settings import MLSettings

# Test with one of the emails that was marked as Whitelisted Protected
test_email = {
    "sender": "support@e.usa.experian.com",
    "subject": "Good news, Robert, your FICO® Score could help you score auto insurance savings",
    "domain": "e.usa.experian.com"
}

print(f"\n{'='*80}")
print(f"TESTING EMAIL CLASSIFICATION PIPELINE")
print(f"{'='*80}")
print(f"Sender: {test_email['sender']}")
print(f"Subject: {test_email['subject']}")
print(f"Domain: {test_email['domain']}")
print(f"{'='*80}\n")

# Initialize classifiers
ml_settings = MLSettings()
ensemble_classifier = EnsembleHybridClassifier(ml_settings)
category_classifier = CategoryClassifier()
domain_validator = DomainValidator()

# Step 1: Domain Validation
print("STEP 1: Domain Validation")
print("-" * 40)
domain_check = domain_validator.validate_domain(test_email['domain'])
print(f"Domain Valid: {domain_check['is_valid']}")
print(f"Risk Score: {domain_check.get('risk_score', 'N/A')}")
print(f"Reason: {domain_check.get('reason', 'N/A')}")

# Step 2: Spam Detection
print("\n\nSTEP 2: Spam Detection (Ensemble Classifier)")
print("-" * 40)
is_spam, confidence, reason = ensemble_classifier.is_spam(
    test_email['sender'], 
    test_email['subject']
)
print(f"Is Spam: {is_spam}")
print(f"Confidence: {confidence}")
print(f"Reason: {reason}")

# Step 3: Category Classification
print("\n\nSTEP 3: Category Classification")
print("-" * 40)
if is_spam:
    category = category_classifier.classify(test_email['sender'], test_email['subject'])
    print(f"Spam Category: {category}")
else:
    print("Not classified as spam, so no category assigned")

# Step 4: Check whitelist settings
print("\n\nSTEP 4: Whitelist Settings Check")
print("-" * 40)
print(f"Whitelist Enabled: {ml_settings.WHITELIST_ENABLED}")
print(f"Whitelist Domains: {ml_settings.WHITELIST_DOMAINS}")
print(f"Whitelist Addresses: {ml_settings.WHITELIST_ADDRESSES}")

# Step 5: Check if domain is in whitelist
print("\n\nSTEP 5: Domain Whitelist Check")
print("-" * 40)
is_whitelisted = False
if ml_settings.WHITELIST_ENABLED:
    # Check domain whitelist
    for domain in ml_settings.WHITELIST_DOMAINS:
        if test_email['domain'].endswith(domain):
            is_whitelisted = True
            print(f"Domain {test_email['domain']} matches whitelist domain {domain}")
            break
    
    # Check address whitelist
    if test_email['sender'].lower() in [addr.lower() for addr in ml_settings.WHITELIST_ADDRESSES]:
        is_whitelisted = True
        print(f"Sender {test_email['sender']} is in whitelist addresses")

print(f"Is Whitelisted: {is_whitelisted}")

print("\n\nFINAL VERDICT:")
print("-" * 40)
if is_whitelisted:
    print("❌ EMAIL WOULD BE WHITELISTED (Protected from deletion)")
elif is_spam:
    print(f"✅ EMAIL WOULD BE DELETED as {category}")
else:
    print("✅ EMAIL WOULD BE PRESERVED as legitimate")

print(f"\n{'='*80}\n")