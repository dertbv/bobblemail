#!/usr/bin/env python3
"""
Test Random Forest Integration with Hybrid Classifier
Validates that Random Forest is properly integrated and working
"""

from hybrid_classifier import HybridEmailClassifier
import time

def test_random_forest_integration():
    """Test Random Forest integration with hybrid classifier"""
    print("🧪 TESTING RANDOM FOREST INTEGRATION")
    print("=" * 50)
    
    # Initialize hybrid classifier with Random Forest
    print("1. Initializing Hybrid Classifier with Random Forest...")
    try:
        classifier = HybridEmailClassifier(use_random_forest=True)
        print(f"✅ Hybrid classifier initialized")
        print(f"   🌲 Random Forest enabled: {classifier.use_random_forest}")
        print(f"   🧠 Naive Bayes trained: {classifier.is_ml_trained}")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test cases covering different spam types
    test_cases = [
        # Financial spam
        ("crypto-investment@suspicious.tk", "🚀 URGENT: 1000% Bitcoin Returns Guaranteed!", True),
        # Health spam  
        ("health-miracle@spam.com", "Blood sugar breakthrough - diabetes cure discovered", True),
        # Gambling spam
        ("casino-bonus@gambling.tk", "🎰 $500 FREE casino bonus - claim your winnings now!", True),
        # Legitimate emails
        ("support@amazon.com", "Your order #123456 has been shipped", False),
        ("noreply@chase.com", "Your monthly statement is ready", False),
        ("alerts@apple.com", "Sign-in detected from new device", False),
    ]
    
    print(f"\n2. Testing {len(test_cases)} email classifications:")
    print(f"{'Subject':<45} {'Prediction':<12} {'Method':<15} {'Confidence':<12} {'Time':<8}")
    print("-" * 100)
    
    total_time = 0
    correct_predictions = 0
    random_forest_used = 0
    
    for sender, subject, expected_spam in test_cases:
        try:
            start_time = time.time()
            result = classifier.classify_email(sender, subject)
            prediction_time = time.time() - start_time
            total_time += prediction_time
            
            predicted_spam = result.get('is_spam', False)
            method = result.get('method', 'unknown')
            confidence = result.get('confidence', 0)
            
            # Track accuracy
            if predicted_spam == expected_spam:
                correct_predictions += 1
            
            # Track Random Forest usage
            if 'random_forest' in method or result.get('ml_method') == 'random_forest':
                random_forest_used += 1
            
            prediction_str = "SPAM" if predicted_spam else "LEGIT"
            expected_str = "✅" if predicted_spam == expected_spam else "❌"
            
            print(f"{subject[:45]:<45} {prediction_str:<12} {method:<15} {confidence:.3f}       {prediction_time*1000:.1f}ms {expected_str}")
            
        except Exception as e:
            print(f"{subject[:45]:<45} ERROR: {e}")
    
    # Performance summary
    avg_time = total_time / len(test_cases)
    accuracy = correct_predictions / len(test_cases)
    rf_usage = random_forest_used / len(test_cases)
    
    print("-" * 100)
    print(f"\n📊 PERFORMANCE SUMMARY:")
    print(f"   🎯 Accuracy: {accuracy:.1%} ({correct_predictions}/{len(test_cases)})")
    print(f"   🌲 Random Forest Usage: {rf_usage:.1%} ({random_forest_used}/{len(test_cases)})")
    print(f"   ⚡ Average Prediction Time: {avg_time*1000:.1f}ms")
    
    # Get prediction stats
    stats = classifier.get_prediction_stats()
    print(f"\n📈 PREDICTION STATISTICS:")
    print(f"   Total Predictions: {stats['total_predictions']}")
    print(f"   ML Decisions: {stats['ml_decisions']}")
    print(f"   Rule-based Decisions: {stats['rule_based_decisions']}")
    print(f"   Hybrid Decisions: {stats['hybrid_decisions']}")
    
    # Validate Random Forest is working
    print(f"\n🔍 RANDOM FOREST VALIDATION:")
    if classifier.use_random_forest and classifier.rf_classifier:
        if classifier.rf_classifier.is_trained:
            rf_metrics = classifier.rf_classifier.get_performance_metrics()
            print(f"   ✅ Random Forest Model Loaded")
            print(f"   📊 Training Accuracy: {rf_metrics.get('accuracy', 0):.3f}")
            print(f"   📊 Training Precision: {rf_metrics.get('precision', 0):.3f}")
            print(f"   📊 Training F1 Score: {rf_metrics.get('f1_score', 0):.3f}")
        else:
            print(f"   ❌ Random Forest Model Not Trained")
    else:
        print(f"   ❌ Random Forest Not Available")
    
    # Test individual Random Forest prediction
    print(f"\n🧪 DIRECT RANDOM FOREST TEST:")
    if classifier.rf_classifier and classifier.rf_classifier.is_trained:
        try:
            rf_result = classifier.rf_classifier.predict(
                "crypto-scam@suspicious.tk", 
                "URGENT: Bitcoin investment opportunity - 500% returns!"
            )
            print(f"   📧 Test Email: Bitcoin investment scam")
            print(f"   🎯 Prediction: {'SPAM' if rf_result['is_spam'] else 'LEGIT'}")
            print(f"   📊 Confidence: {rf_result['confidence']:.3f}")
            print(f"   ⚡ Prediction Time: {rf_result['prediction_time']*1000:.1f}ms")
            print(f"   🔧 Features Used: {rf_result['features_used']}")
        except Exception as e:
            print(f"   ❌ Direct RF test failed: {e}")
    
    print(f"\n{'✅ RANDOM FOREST INTEGRATION SUCCESSFUL!' if accuracy > 0.7 and random_forest_used > 0 else '❌ INTEGRATION ISSUES DETECTED'}")
    
    return accuracy > 0.7 and random_forest_used > 0


if __name__ == "__main__":
    success = test_random_forest_integration()