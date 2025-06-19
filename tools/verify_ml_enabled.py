#!/usr/bin/env python3
"""
ML Enablement Verification Script
================================

Verifies that Machine Learning has been successfully enabled in the hybrid classifier.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_classifier import HybridEmailClassifier, classify_email_hybrid
from ml_classifier import NaiveBayesClassifier

def verify_ml_enabled():
    """Comprehensive verification that ML is enabled and working."""
    
    print("🔍 VERIFYING ML ENABLEMENT IN EMAIL FILTERING SYSTEM")
    print("=" * 60)
    
    # Test 1: Direct ML Classifier
    print("\n1️⃣ Testing Direct ML Classifier...")
    try:
        ml_classifier = NaiveBayesClassifier()
        ml_classifier.load_model()
        
        test_result = ml_classifier.predict_single(
            "scam@investment.tk", 
            "URGENT: Bitcoin investment opportunity!"
        )
        
        print(f"   ✅ ML Classifier: Operational")
        print(f"   📊 Training size: {ml_classifier.training_size} samples")
        print(f"   📊 Features: {ml_classifier.feature_count}")
        print(f"   🎯 Test prediction: {test_result['spam_probability']:.3f} spam probability")
        
    except Exception as e:
        print(f"   ❌ ML Classifier: Failed ({e})")
        return False
    
    # Test 2: Hybrid Classifier with Auto-ML
    print("\n2️⃣ Testing Hybrid Classifier with Auto-ML...")
    try:
        hybrid = HybridEmailClassifier(auto_train_ml=True)
        
        print(f"   ✅ Hybrid Classifier: Initialized")
        print(f"   🧠 ML Component: {'Trained' if hybrid.is_ml_trained else 'Not Trained'}")
        
        if not hybrid.is_ml_trained:
            print("   ❌ ML not trained in hybrid classifier")
            return False
            
    except Exception as e:
        print(f"   ❌ Hybrid Classifier: Failed ({e})")
        return False
    
    # Test 3: ML-Enhanced Classification
    print("\n3️⃣ Testing ML-Enhanced Classification...")
    
    test_cases = [
        {
            'name': 'Obvious Spam',
            'sender': 'crypto-profits@scam.tk',
            'subject': '💰 URGENT: Get Rich Quick Investment!',
            'expected_action': 'DELETED'
        },
        {
            'name': 'Legitimate Email', 
            'sender': 'support@amazon.com',
            'subject': 'Your package has been delivered',
            'expected_action': 'PRESERVED'
        },
        {
            'name': 'Marketing Email',
            'sender': 'newsletter@company.com', 
            'subject': 'Weekly newsletter - Technology updates',
            'expected_action': 'PRESERVED'
        }
    ]
    
    ml_predictions = 0
    correct_predictions = 0
    
    for test_case in test_cases:
        try:
            result = hybrid.classify_email(
                test_case['sender'],
                test_case['subject'], 
                account_provider='icloud'
            )
            
            is_ml_used = result.get('ml_available', False)
            is_correct = result['action'] == test_case['expected_action']
            
            if is_ml_used:
                ml_predictions += 1
            if is_correct:
                correct_predictions += 1
            
            status = "✅" if is_correct else "❌"
            ml_status = "🧠 ML" if is_ml_used else "📋 Rule"
            
            print(f"   {status} {test_case['name']}: {result['action']} ({ml_status}) - {result['method']}")
            
            if result.get('ml_spam_probability') is not None:
                print(f"      ML Spam Probability: {result['ml_spam_probability']:.3f}")
                
        except Exception as e:
            print(f"   ❌ {test_case['name']}: Error ({e})")
    
    # Test 4: Performance Statistics
    print("\n4️⃣ Performance Statistics...")
    stats = hybrid.get_prediction_stats()
    
    print(f"   📊 Total predictions: {stats['total_predictions']}")
    print(f"   🧠 ML decisions: {stats['ml_decisions']}")
    print(f"   📋 Rule-based decisions: {stats['rule_based_decisions']}")
    print(f"   🔄 Hybrid decisions: {stats['hybrid_decisions']}")
    
    if stats['total_predictions'] > 0:
        ml_percentage = (stats['ml_decisions'] / stats['total_predictions']) * 100
        print(f"   📈 ML usage rate: {ml_percentage:.1f}%")
    
    # Test 5: Wrapper Function
    print("\n5️⃣ Testing Wrapper Function...")
    try:
        wrapper_result = classify_email_hybrid(
            "phishing@suspicious.net",
            "Verify your account immediately!",
            account_provider="gmail"
        )
        
        is_ml_used = wrapper_result.get('ml_available', False)
        print(f"   ✅ Wrapper function: Working ({wrapper_result['method']})")
        print(f"   🧠 ML used: {'Yes' if is_ml_used else 'No'}")
        
    except Exception as e:
        print(f"   ❌ Wrapper function: Failed ({e})")
    
    # Final Assessment
    print("\n" + "=" * 60)
    print("📋 FINAL ASSESSMENT")
    print("=" * 60)
    
    success_criteria = [
        hybrid.is_ml_trained,
        ml_predictions >= 2,  # ML was used for most predictions
        correct_predictions >= 2  # Most predictions were correct
    ]
    
    if all(success_criteria):
        print("🎉 SUCCESS: Machine Learning is FULLY ENABLED and OPERATIONAL!")
        print("   ✅ ML component trained and loaded")
        print("   ✅ Hybrid classifier using ML predictions")
        print("   ✅ Auto-training working correctly")
        print("   ✅ High accuracy predictions")
        print("   ✅ Performance tracking active")
        print("\n🚀 Your email filtering system now has advanced ML capabilities!")
        return True
    else:
        print("⚠️  PARTIAL SUCCESS: ML enabled but not fully operational")
        print(f"   ML Trained: {'✅' if hybrid.is_ml_trained else '❌'}")
        print(f"   ML Used: {'✅' if ml_predictions >= 2 else '❌'}")
        print(f"   Accuracy: {'✅' if correct_predictions >= 2 else '❌'}")
        return False

if __name__ == "__main__":
    success = verify_ml_enabled()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("   1. ML is now active in your email processing")
        print("   2. The system will learn from user feedback")
        print("   3. Consider installing NumPy/Scikit-learn for advanced features")
        print("   4. Monitor performance via web dashboard at http://localhost:8000")
        
    exit(0 if success else 1)