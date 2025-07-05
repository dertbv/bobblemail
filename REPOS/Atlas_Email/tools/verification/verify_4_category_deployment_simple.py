#!/usr/bin/env python3
"""
Verify 4-Category Deployment with Simple Classifier
==================================================

Tests the deployment without numpy/sklearn dependencies.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.atlas_email.ml.simple_four_category_classifier import SimpleFourCategoryClassifier
from src.atlas_email.ml.ab_classifier_integration_simple import ABClassifierIntegrationSimple

def verify_deployment():
    """Verify the 4-category system is working correctly."""
    print("🔍 Verifying 4-Category Deployment")
    print("=" * 60)
    
    # Test 1: Simple Classifier
    print("\n1️⃣ Testing Simple Classifier:")
    classifier = SimpleFourCategoryClassifier()
    
    test_cases = [
        {
            'subject': 'Your auto warranty is about to expire!',
            'sender': 'noreply@autoprotect.com',
            'expected': 'Commercial Spam'
        },
        {
            'subject': 'Final notice about your vehicle warranty',
            'sender': 'warranty@carprotection.net',
            'expected': 'Commercial Spam'
        },
        {
            'subject': 'Car warranty expiration notice',
            'sender': 'service@vehiclewarranty.com',
            'expected': 'Commercial Spam'
        }
    ]
    
    all_passed = True
    for test in test_cases:
        result = classifier.classify(test['subject'], test['sender'])
        passed = result['category'] == test['expected']
        if passed and result['category'] == 'Commercial Spam':
            passed = 'auto' in result['subcategory'].lower() or 'warranty' in result['subcategory'].lower()
        
        status = "✅" if passed else "❌"
        all_passed &= passed
        
        print(f"{status} Subject: {test['subject'][:40]}...")
        print(f"   Category: {result['category']}")
        print(f"   Subcategory: {result['subcategory']}")
        print(f"   Confidence: {result['confidence']:.2f}")
    
    # Test 2: A/B Testing Integration
    print("\n2️⃣ Testing A/B Integration:")
    try:
        ab_classifier = ABClassifierIntegrationSimple(rollout_percentage=100)  # Force new classifier
        
        result = ab_classifier.classify_with_ab_testing(
            sender='warranty@autoprotect.com',
            subject='Your auto warranty is about to expire',
            body='Act now to extend your vehicle warranty coverage',
            force_classifier='new'
        )
        
        if result['classifier_used'] == 'new':
            print("✅ A/B testing integration working")
            print(f"   Category: {result['category']}")
            print(f"   Subcategory: {result['subcategory']}")
            print(f"   Confidence: {result['confidence']:.2f}")
        else:
            print("❌ A/B testing not using new classifier")
            all_passed = False
            
    except Exception as e:
        print(f"❌ A/B testing failed: {e}")
        all_passed = False
    
    # Test 3: Database Tables
    print("\n3️⃣ Checking Database Tables:")
    try:
        from src.atlas_email.models.database import DB_FILE
        conn = sqlite3.connect(DB_FILE)
        
        # Check for new columns
        cursor = conn.execute("PRAGMA table_info(processed_emails_bulletproof)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['category_v2', 'subcategory', 'category_confidence_v2', 'classification_version']
        missing = [col for col in required_columns if col not in columns]
        
        if not missing:
            print("✅ All required columns present")
        else:
            print(f"❌ Missing columns: {missing}")
            all_passed = False
            
        # Check for A/B testing table
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ab_testing_results'")
        if cursor.fetchone():
            print("✅ A/B testing table exists")
        else:
            print("❌ A/B testing table missing")
            all_passed = False
            
        conn.close()
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ DEPLOYMENT VERIFIED SUCCESSFULLY!")
        print("   - Auto warranty emails classified as Commercial Spam ✓")
        print("   - A/B testing framework operational ✓")
        print("   - Database migration complete ✓")
        
        # Update status file
        import json
        status = {
            "deployment_date": datetime.now().isoformat(),
            "database_migrated": True,
            "classifier_trained": True,
            "ab_testing_enabled": True,
            "rollout_percentage": 10,
            "simple_classifier_deployed": True,
            "notes": "Simple rule-based classifier deployed successfully. Auto warranty emails now correctly classified."
        }
        
        with open("4_category_deployment_status.json", "w") as f:
            json.dump(status, f, indent=2)
            
        print("\n📊 Next Steps:")
        print("   1. Monitor A/B testing results")
        print("   2. Gradually increase rollout percentage")
        print("   3. Collect user feedback on classifications")
    else:
        print("❌ DEPLOYMENT VERIFICATION FAILED")
        print("   Please check the errors above and fix them.")
        

if __name__ == "__main__":
    verify_deployment()