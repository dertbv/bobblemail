"""
Test Suite for 4-Category Classification System
==============================================

Comprehensive tests to validate the accuracy improvements,
especially for auto warranty email classification.
"""

import unittest
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.atlas_email.ml.four_category_classifier import FourCategoryClassifier
from src.atlas_email.ml.subcategory_tagger import SubcategoryTagger
from src.atlas_email.ml.ab_classifier_integration import ABClassifierIntegration


class TestFourCategoryClassifier(unittest.TestCase):
    """Test the 4-category classifier implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test classifier."""
        cls.classifier = FourCategoryClassifier()
        # Train if not already trained
        if not cls.classifier.is_trained:
            try:
                cls.classifier.train()
            except Exception as e:
                print(f"Warning: Could not train classifier: {e}")
    
    def test_auto_warranty_classification(self):
        """Test that auto warranty emails are correctly classified."""
        test_cases = [
            {
                'sender': 'noreply@dertbv.com',
                'subject': "dertbv you're eligible for discounted pricing you could save thousands on auto repair🔔",
                'expected_category': 'Commercial Spam',
                'expected_subcategory': 'Auto warranty & insurance'
            },
            {
                'sender': 'warranty@endurance-auto.net',
                'subject': '🔒 Endurance Auto Warranty: Trusted Protection for Your Vehicle',
                'expected_category': 'Commercial Spam',
                'expected_subcategory': 'Auto warranty & insurance'
            },
            {
                'sender': 'finalnotice@carprotection.com',
                'subject': 'FINAL NOTICE: Your vehicle warranty is about to expire',
                'expected_category': 'Commercial Spam',
                'expected_subcategory': 'Auto warranty & insurance'
            }
        ]
        
        if not self.classifier.is_trained:
            self.skipTest("Classifier not trained")
        
        for test in test_cases:
            with self.subTest(subject=test['subject']):
                result = self.classifier.classify(
                    test['sender'], 
                    test['subject']
                )
                
                self.assertEqual(result['category'], test['expected_category'],
                    f"Expected {test['expected_category']} but got {result['category']}")
                
                self.assertEqual(result['subcategory'], test['expected_subcategory'],
                    f"Expected subcategory {test['expected_subcategory']} but got {result['subcategory']}")
                
                self.assertGreater(result['confidence'], 0.5,
                    f"Confidence too low: {result['confidence']}")
    
    def test_adult_spam_classification(self):
        """Test that actual adult spam is still correctly classified."""
        test_cases = [
            {
                'sender': 'hotsingles@dating-site.net',
                'subject': 'Hot singles in your area want to meet you tonight!',
                'expected_category': 'Commercial Spam',
                'expected_subcategory': 'Adult & dating services'
            },
            {
                'sender': 'noreply@xxxsite.com',
                'subject': 'XXX content - Adults only special offer',
                'expected_category': 'Commercial Spam',
                'expected_subcategory': 'Adult & dating services'
            }
        ]
        
        if not self.classifier.is_trained:
            self.skipTest("Classifier not trained")
        
        for test in test_cases:
            with self.subTest(subject=test['subject']):
                result = self.classifier.classify(
                    test['sender'], 
                    test['subject']
                )
                
                self.assertEqual(result['category'], test['expected_category'])
                self.assertEqual(result['subcategory'], test['expected_subcategory'])
    
    def test_dangerous_email_classification(self):
        """Test dangerous email classification."""
        test_cases = [
            {
                'sender': 'security@amaz0n-verify.com',
                'subject': 'Urgent: Verify your account or it will be suspended',
                'expected_category': 'Dangerous',
                'expected_subcategory': 'Phishing attempts'
            },
            {
                'sender': 'support@micr0soft-security.net',
                'subject': 'Security Alert: Suspicious activity detected on your account',
                'expected_category': 'Dangerous',
                'expected_subcategory': 'Phishing attempts'
            }
        ]
        
        if not self.classifier.is_trained:
            self.skipTest("Classifier not trained")
        
        for test in test_cases:
            with self.subTest(subject=test['subject']):
                result = self.classifier.classify(
                    test['sender'], 
                    test['subject']
                )
                
                self.assertEqual(result['category'], test['expected_category'])
                self.assertIn('Phishing', result['subcategory'])
                self.assertEqual(result['priority'], 'CRITICAL')
    
    def test_category_distribution(self):
        """Test that all 4 categories are properly represented."""
        if not self.classifier.is_trained:
            self.skipTest("Classifier not trained")
        
        # Check that classifier knows all 4 categories
        expected_categories = {
            'Dangerous', 
            'Commercial Spam', 
            'Scams', 
            'Legitimate Marketing'
        }
        
        if hasattr(self.classifier, 'label_encoder') and self.classifier.label_encoder:
            actual_categories = set(self.classifier.label_encoder.classes_)
            
            for cat in expected_categories:
                self.assertIn(cat, actual_categories,
                    f"Category '{cat}' not found in trained classifier")


class TestSubcategoryTagger(unittest.TestCase):
    """Test the subcategory tagging functionality."""
    
    def setUp(self):
        """Set up test tagger."""
        self.tagger = SubcategoryTagger()
    
    def test_auto_warranty_tagging(self):
        """Test auto warranty subcategory detection."""
        test_cases = [
            {
                'category': 'Commercial Spam',
                'subject': 'Your auto warranty is about to expire - Act now!',
                'expected_subcategory': 'Auto warranty & insurance',
                'min_confidence': 0.7
            },
            {
                'category': 'Commercial Spam',
                'subject': 'Endurance Auto Protection - Save thousands on repairs',
                'expected_subcategory': 'Auto warranty & insurance',
                'min_confidence': 0.8
            },
            {
                'category': 'Commercial Spam',
                'subject': 'Vehicle warranty final notice #45829',
                'expected_subcategory': 'Auto warranty & insurance',
                'min_confidence': 0.7
            }
        ]
        
        for test in test_cases:
            with self.subTest(subject=test['subject']):
                result = self.tagger.tag_email(
                    category=test['category'],
                    subject=test['subject'],
                    sender='test@example.com'
                )
                
                self.assertEqual(result['subcategory'], test['expected_subcategory'],
                    f"Expected {test['expected_subcategory']} but got {result['subcategory']}")
                
                self.assertGreaterEqual(result['confidence'], test['min_confidence'],
                    f"Confidence {result['confidence']} below minimum {test['min_confidence']}")
    
    def test_pattern_matching(self):
        """Test pattern matching for various subcategories."""
        test_cases = [
            # Phishing
            {
                'category': 'Dangerous',
                'subject': 'Verify your PayPal account immediately',
                'expected_patterns': ['verify', 'account']
            },
            # Health spam
            {
                'category': 'Commercial Spam',
                'subject': 'Lose 30 pounds in 30 days - FDA approved',
                'expected_patterns': ['lose', 'pounds', 'FDA approved']
            },
            # Lottery scam
            {
                'category': 'Scams',
                'subject': 'Congratulations! You won the Google lottery - $1,000,000',
                'expected_patterns': ['congratulations', 'won', 'lottery']
            }
        ]
        
        for test in test_cases:
            with self.subTest(subject=test['subject']):
                result = self.tagger.tag_email(
                    category=test['category'],
                    subject=test['subject']
                )
                
                self.assertGreater(len(result['matched_patterns']), 0,
                    "No patterns matched")
                
                # Check that at least one expected pattern matched
                matched_pattern_values = [p['pattern'] for p in result['matched_patterns']]
                pattern_found = False
                for expected in test['expected_patterns']:
                    for pattern in matched_pattern_values:
                        if expected.lower() in pattern.lower():
                            pattern_found = True
                            break
                
                self.assertTrue(pattern_found,
                    f"None of expected patterns {test['expected_patterns']} found in {matched_pattern_values}")


class TestABIntegration(unittest.TestCase):
    """Test A/B testing integration."""
    
    def setUp(self):
        """Set up A/B testing with 50% rollout."""
        self.ab_integration = ABClassifierIntegration(rollout_percentage=50.0)
    
    def test_ab_classification(self):
        """Test that A/B testing runs both classifiers."""
        test_email = {
            'sender': 'warranty@auto-protect.com',
            'subject': 'Your vehicle warranty expires soon - Save now!'
        }
        
        result = self.ab_integration.classify_with_ab_testing(
            test_email['sender'],
            test_email['subject']
        )
        
        # Check that A/B testing metadata is present
        self.assertIn('ab_testing', result)
        self.assertIn('classifier_used', result)
        self.assertIn('categories_match', result['ab_testing'])
        
        # Check that both classifiers were compared
        self.assertIn('old_category', result['ab_testing'])
        self.assertIn('new_category', result['ab_testing'])
    
    def test_force_classifier(self):
        """Test forcing specific classifier in A/B testing."""
        test_email = {
            'sender': 'test@example.com',
            'subject': 'Test email for classifier selection'
        }
        
        # Force old classifier
        result_old = self.ab_integration.classify_with_ab_testing(
            test_email['sender'],
            test_email['subject'],
            force_classifier='old'
        )
        self.assertEqual(result_old['classifier_used'], 'old')
        
        # Force new classifier
        result_new = self.ab_integration.classify_with_ab_testing(
            test_email['sender'],
            test_email['subject'],
            force_classifier='new'
        )
        self.assertEqual(result_new['classifier_used'], 'new')
    
    def test_metrics_tracking(self):
        """Test that A/B testing metrics are tracked."""
        # Run a few classifications
        test_emails = [
            ('warranty@test.com', 'Auto warranty expiring'),
            ('phishing@test.com', 'Verify your account'),
            ('deals@test.com', 'Weekend sale 50% off')
        ]
        
        for sender, subject in test_emails:
            self.ab_integration.classify_with_ab_testing(sender, subject)
        
        # Get metrics
        metrics = self.ab_integration.get_ab_testing_metrics(days=1)
        
        self.assertGreater(metrics['total_comparisons'], 0)
        self.assertIn('agreement_rate', metrics)
        self.assertIn('avg_time_old', metrics)
        self.assertIn('avg_time_new', metrics)


class TestMigration(unittest.TestCase):
    """Test database migration functionality."""
    
    def test_category_mapping(self):
        """Test that category mappings are correct."""
        from src.atlas_email.ml.migrate_to_four_categories import FourCategoryMigration
        
        migration = FourCategoryMigration()
        
        # Test specific mappings
        mappings_to_test = [
            ('Adult & Dating Spam', 'Commercial Spam', 'Adult & dating services'),
            ('Phishing', 'Dangerous', 'Phishing attempts'),
            ('Payment Scam', 'Scams', 'Advance fee fraud'),
            ('Promotional Email', 'Legitimate Marketing', 'Promotional emails')
        ]
        
        for old_cat, expected_new, expected_sub in mappings_to_test:
            new_cat, subcat = migration.CATEGORY_MAPPING[old_cat]
            self.assertEqual(new_cat, expected_new,
                f"Wrong mapping for {old_cat}: expected {expected_new}, got {new_cat}")
            self.assertEqual(subcat, expected_sub,
                f"Wrong subcategory for {old_cat}: expected {expected_sub}, got {subcat}")


def run_accuracy_report():
    """Generate a comprehensive accuracy report."""
    print("\n" + "="*80)
    print("4-CATEGORY CLASSIFICATION ACCURACY REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize classifier
    classifier = FourCategoryClassifier()
    if not classifier.is_trained:
        print("Training classifier...")
        classifier.train()
    
    # Test auto warranty fixes
    print("AUTO WARRANTY CLASSIFICATION TEST")
    print("-" * 40)
    
    auto_warranty_tests = [
        ('noreply@dertbv.com', "you're eligible for auto warranty savings"),
        ('endurance@protection.net', 'Endurance Auto Warranty - Final Notice'),
        ('warranty@carshield.info', 'Your vehicle warranty expires in 30 days'),
        ('autoprotect@coverage.com', 'Save $3000 on auto repairs - warranty coverage'),
    ]
    
    correct = 0
    for sender, subject in auto_warranty_tests:
        result = classifier.classify(sender, subject)
        is_correct = (result['category'] == 'Commercial Spam' and 
                     result['subcategory'] == 'Auto warranty & insurance')
        correct += is_correct
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {subject[:50]}")
        print(f"   Category: {result['category']} (conf: {result['confidence']:.2f})")
        print(f"   Subcategory: {result['subcategory']}")
    
    accuracy = correct / len(auto_warranty_tests) * 100
    print(f"\nAuto Warranty Accuracy: {accuracy:.1f}% ({correct}/{len(auto_warranty_tests)})")
    
    # Test other categories
    print("\n\nOTHER CATEGORY TESTS")
    print("-" * 40)
    
    other_tests = [
        ('security@amaz0n.fake', 'Verify your account', 'Dangerous', 'Phishing'),
        ('lottery@winner.com', 'You won $1,000,000', 'Scams', 'Lottery'),
        ('newsletter@company.com', 'Monthly product updates', 'Legitimate Marketing', 'Newsletter'),
        ('singles@dating.net', 'Hot singles nearby', 'Commercial Spam', 'Adult'),
    ]
    
    for sender, subject, expected_cat, expected_sub_keyword in other_tests:
        result = classifier.classify(sender, subject)
        cat_correct = result['category'] == expected_cat
        sub_correct = expected_sub_keyword.lower() in result['subcategory'].lower()
        
        status = "✅" if cat_correct else "❌"
        print(f"{status} {subject} -> {result['category']}")
    
    # A/B Testing Summary
    print("\n\nA/B TESTING SUMMARY")
    print("-" * 40)
    
    ab = ABClassifierIntegration(rollout_percentage=20)
    recommendation = ab.get_recommendation()
    
    print(f"Current Rollout: {ab.rollout_percentage}%")
    print(f"Recommendation: {recommendation['recommended_action']}")
    print(f"Recommended Rollout: {recommendation['recommended_rollout']}%")
    print("Reasons:")
    for reason in recommendation['reasons']:
        print(f"  - {reason}")
    
    print("\n" + "="*80)
    print("REPORT COMPLETE")
    print("="*80)


if __name__ == '__main__':
    # Run tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Generate accuracy report
    run_accuracy_report()