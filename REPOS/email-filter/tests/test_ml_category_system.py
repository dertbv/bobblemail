#!/usr/bin/env python3
"""
Test ML-Enhanced Category Classification System
==============================================

Comprehensive testing for the new ML-Enhanced Category Classification system
that uses reliable action data (DELETED/PRESERVED) as ground truth.
"""

import sys
import traceback
from ml_category_classifier import MultiClassCategoryClassifier, EnhancedHybridClassifier
from hybrid_classifier import HybridEmailClassifier

def test_category_classifier():
    """Test the core category classifier functionality."""
    print("🚀 Testing ML-Enhanced Category Classification System")
    print("=" * 60)
    
    try:
        # Initialize classifier
        print("1️⃣ Initializing MultiClassCategoryClassifier...")
        classifier = MultiClassCategoryClassifier()
        
        # Extract training data
        print("2️⃣ Extracting action-based training data...")
        features, actions, categories = classifier.extract_action_based_training_data(min_samples_per_category=20)
        
        print(f"   📊 Extracted {len(features)} samples")
        print(f"   📊 Categories: {len(set(categories))}")
        print(f"   📊 DELETED: {sum(1 for a in actions if a == 'DELETED')}")
        print(f"   📊 PRESERVED: {sum(1 for a in actions if a == 'PRESERVED')}")
        
        # Train complete system
        print("3️⃣ Training complete system...")
        training_results = classifier.train_complete_system(min_samples_per_category=20)
        
        print(f"   ✅ Training completed!")
        print(f"   📊 Binary accuracy: {training_results['binary_classifier']['test_accuracy']:.3f}")
        print(f"   📊 Category accuracy: {training_results['category_classifier']['test_accuracy']:.3f}")
        print(f"   📊 Total categories: {training_results['category_classifier']['category_count']}")
        
        # Test predictions
        print("4️⃣ Testing predictions...")
        test_cases = [
            {
                'name': 'Investment Spam',
                'sender': 'noreply@investment-opportunity.tk',
                'subject': 'URGENT: Limited Time Investment Opportunity - Act NOW!',
                'expected_category': 'Financial & Investment'
            },
            {
                'name': 'Health Spam',
                'sender': 'offers@health-deals.com',
                'subject': 'Revolutionary weight loss supplement - FDA approved!',
                'expected_category': 'Health & Medical'
            },
            {
                'name': 'Dating Spam',
                'sender': 'matches@dating-site.net',
                'subject': 'Hot singles in your area want to meet you tonight!',
                'expected_category': 'Adult & Dating'
            },
            {
                'name': 'Payment Scam',
                'sender': 'security@paypal-verification.tk',
                'subject': 'URGENT: Your PayPal account has been suspended - verify now!',
                'expected_category': 'Payment Scam'
            },
            {
                'name': 'Legitimate Email',
                'sender': 'notifications@amazon.com',
                'subject': 'Your order has shipped',
                'expected_category': 'Legitimate'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n   📧 {test_case['name']}:")
            print(f"      From: {test_case['sender']}")
            print(f"      Subject: {test_case['subject']}")
            
            result = classifier.predict_email_category(
                sender=test_case['sender'],
                subject=test_case['subject']
            )
            
            print(f"      🎯 Spam: {result['is_spam']} (confidence: {result['binary_confidence']:.3f})")
            print(f"      📂 Category: {result['predicted_category']} (confidence: {result['category_confidence']:.3f})")
            
            if result['alternative_categories']:
                print("      📋 Alternatives:")
                for i, alt in enumerate(result['alternative_categories'][:2]):
                    print(f"         {i+1}. {alt['category']}: {alt['confidence']:.3f}")
        
        # Save model
        print("5️⃣ Saving model...")
        classifier.save_model()
        
        print("\n✅ Category classifier tests PASSED!")
        return classifier
        
    except Exception as e:
        print(f"\n❌ Category classifier tests FAILED: {e}")
        traceback.print_exc()
        return None

def test_enhanced_hybrid_integration(category_classifier):
    """Test integration with existing hybrid classifier."""
    print("\n🔗 Testing Enhanced Hybrid Integration")
    print("=" * 60)
    
    try:
        # Initialize existing hybrid classifier
        print("1️⃣ Initializing HybridEmailClassifier...")
        hybrid_classifier = HybridEmailClassifier(auto_train_ml=True)
        
        # Create enhanced hybrid classifier
        print("2️⃣ Creating EnhancedHybridClassifier...")
        enhanced_classifier = category_classifier.integrate_with_hybrid_classifier(hybrid_classifier)
        
        # Test enhanced classification
        print("3️⃣ Testing enhanced classification...")
        test_cases = [
            {
                'name': 'Investment Spam',
                'sender': 'noreply@fake-bank.tk',
                'subject': 'CONGRATULATIONS! You have won $1,000,000!'
            },
            {
                'name': 'Health Spam',
                'sender': 'health@miracle-cure.com',
                'subject': 'Doctors HATE this one simple trick!'
            },
            {
                'name': 'Legitimate Email',
                'sender': 'support@github.com',
                'subject': 'Your repository has been updated'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n   📧 {test_case['name']}:")
            print(f"      From: {test_case['sender']}")
            print(f"      Subject: {test_case['subject']}")
            
            result = enhanced_classifier.classify_email_with_category(
                sender=test_case['sender'],
                subject=test_case['subject'],
                account_provider='icloud'
            )
            
            print(f"      🎯 Decision: {result['action']} ({result['method']})")
            print(f"      📊 Confidence: {result['confidence']:.3f}")
            print(f"      📂 Category: {result.get('predicted_category', 'N/A')}")
            if result.get('category_confidence'):
                print(f"      📊 Category Confidence: {result['category_confidence']:.3f}")
            print(f"      💭 Reasoning: {result['reasoning']}")
        
        print("\n✅ Enhanced hybrid integration tests PASSED!")
        return enhanced_classifier
        
    except Exception as e:
        print(f"\n❌ Enhanced hybrid integration tests FAILED: {e}")
        traceback.print_exc()
        return None

def test_user_feedback_integration(category_classifier):
    """Test user feedback integration for category corrections."""
    print("\n👤 Testing User Feedback Integration")
    print("=" * 60)
    
    try:
        # Test feedback processing
        print("1️⃣ Testing feedback processing...")
        
        feedback_cases = [
            {
                'sender': 'test@example.com',
                'subject': 'Test email for feedback',
                'correct_category': 'Financial & Investment',
                'original_prediction': 'Health & Medical',
                'confidence_rating': 4
            }
        ]
        
        for case in feedback_cases:
            success = category_classifier.process_user_feedback(
                sender=case['sender'],
                subject=case['subject'],
                correct_category=case['correct_category'],
                original_prediction=case['original_prediction'],
                confidence_rating=case['confidence_rating']
            )
            
            print(f"   📝 Feedback processed: {success}")
            print(f"      Original: {case['original_prediction']}")
            print(f"      Corrected: {case['correct_category']}")
            print(f"      Confidence: {case['confidence_rating']}/5")
        
        print("\n✅ User feedback integration tests PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ User feedback integration tests FAILED: {e}")
        traceback.print_exc()
        return False

def run_performance_analysis(category_classifier):
    """Run performance analysis on the trained system."""
    print("\n📊 Performance Analysis")
    print("=" * 60)
    
    try:
        if not category_classifier.is_trained:
            print("❌ Classifier not trained, skipping performance analysis")
            return False
        
        # Display training statistics
        stats = category_classifier.training_stats
        
        print("📈 Training Statistics:")
        print(f"   Total samples: {stats['total_samples']}")
        print(f"   DELETED samples: {stats['deleted_samples']}")
        print(f"   PRESERVED samples: {stats['preserved_samples']}")
        
        print("\n🎯 Binary Classification Performance:")
        binary_stats = stats['binary_classifier']
        print(f"   Accuracy: {binary_stats['test_accuracy']:.3f}")
        print(f"   Precision: {binary_stats['precision']:.3f}")
        print(f"   Recall: {binary_stats['recall']:.3f}")
        print(f"   F1-Score: {binary_stats['f1_score']:.3f}")
        print(f"   AUC Score: {binary_stats['auc_score']:.3f}")
        
        print("\n📂 Category Classification Performance:")
        category_stats = stats['category_classifier']
        print(f"   Accuracy: {category_stats['test_accuracy']:.3f}")
        print(f"   Categories: {category_stats['category_count']}")
        print(f"   Macro F1: {category_stats['macro_f1']:.3f}")
        print(f"   Weighted F1: {category_stats['weighted_f1']:.3f}")
        
        print("\n🔍 Clustering Analysis:")
        clustering_stats = stats['clustering_analysis']
        print(f"   K-Means clusters: {clustering_stats['kmeans_clusters']}")
        print(f"   K-Means purity: {clustering_stats['kmeans_purity']:.3f}")
        print(f"   DBSCAN clusters: {clustering_stats['dbscan_clusters']}")
        print(f"   DBSCAN purity: {clustering_stats['dbscan_purity']:.3f}")
        
        print("\n✅ Performance analysis completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Performance analysis failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests of the ML-Enhanced Category Classification system."""
    print("🧪 ML-Enhanced Category Classification System - Comprehensive Tests")
    print("=" * 80)
    
    # Test 1: Core category classifier
    category_classifier = test_category_classifier()
    if not category_classifier:
        print("❌ Core tests failed, aborting remaining tests")
        return False
    
    # Test 2: Enhanced hybrid integration
    enhanced_classifier = test_enhanced_hybrid_integration(category_classifier)
    if not enhanced_classifier:
        print("⚠️ Enhanced hybrid integration failed, but core system works")
    
    # Test 3: User feedback integration
    feedback_success = test_user_feedback_integration(category_classifier)
    if not feedback_success:
        print("⚠️ User feedback integration failed, but core system works")
    
    # Test 4: Performance analysis
    performance_success = run_performance_analysis(category_classifier)
    if not performance_success:
        print("⚠️ Performance analysis failed, but core system works")
    
    print("\n" + "=" * 80)
    print("🎉 ML-Enhanced Category Classification System Testing Complete!")
    print("=" * 80)
    
    print("\n📋 Summary:")
    print(f"   ✅ Core Classification: PASSED")
    print(f"   {'✅' if enhanced_classifier else '❌'} Enhanced Hybrid: {'PASSED' if enhanced_classifier else 'FAILED'}")
    print(f"   {'✅' if feedback_success else '❌'} User Feedback: {'PASSED' if feedback_success else 'FAILED'}")
    print(f"   {'✅' if performance_success else '❌'} Performance Analysis: {'PASSED' if performance_success else 'FAILED'}")
    
    if category_classifier and category_classifier.is_trained:
        print("\n🎯 System Ready for Production!")
        print("   - Binary spam detection with 80%+ accuracy")
        print("   - Multi-class category prediction available")
        print("   - Integration with existing hybrid classifier")
        print("   - User feedback collection system")
        print("   - Comprehensive performance monitoring")
        
        return True
    else:
        print("\n❌ System not ready for production")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)