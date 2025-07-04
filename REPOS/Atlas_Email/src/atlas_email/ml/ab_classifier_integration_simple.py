"""
A/B Testing Integration for Simple 4-Category Classification System
================================================================

This module enables parallel operation of the old and new classification systems
for A/B testing and gradual rollout. Uses the simple classifier without numpy/sklearn.
"""

import sqlite3
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import random

from atlas_email.ml.category_classifier import MultiClassCategoryClassifier
from atlas_email.ml.simple_four_category_classifier import SimpleFourCategoryClassifier
from atlas_email.models.database import DB_FILE


class ABClassifierIntegrationSimple:
    """
    Manages A/B testing between old and new classification systems.
    Uses the simple rule-based classifier that doesn't require numpy.
    """
    
    def __init__(self, db_path: str = None, rollout_percentage: float = 10.0):
        """
        Initialize A/B testing integration.
        
        Args:
            db_path: Database path
            rollout_percentage: Percentage of traffic to route to new classifier (0-100)
        """
        self.db_path = db_path or DB_FILE
        self.rollout_percentage = rollout_percentage
        
        # Initialize both classifiers
        try:
            self.old_classifier = MultiClassCategoryClassifier(db_path)
            self.old_available = True
        except Exception as e:
            print(f"⚠️ Old classifier unavailable: {e}")
            self.old_available = False
            
        self.new_classifier = SimpleFourCategoryClassifier()
        
        # Tracking
        self.comparison_results = []
        self._ensure_tracking_table()
        
    def _ensure_tracking_table(self):
        """Create A/B testing tracking table if not exists."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_testing_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                email_uid TEXT,
                sender TEXT,
                subject TEXT,
                old_category TEXT,
                old_confidence REAL,
                new_category TEXT,
                new_subcategory TEXT,
                new_confidence REAL,
                categories_match BOOLEAN,
                processing_time_old REAL,
                processing_time_new REAL,
                selected_classifier TEXT,
                user_feedback TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ab_test_id 
            ON ab_testing_results(test_id)
        """)
        
        conn.commit()
        conn.close()
    
    def classify_with_ab_testing(self, sender: str, subject: str, 
                                body: str = "", headers: str = "",
                                force_classifier: str = None) -> Dict[str, Any]:
        """
        Classify email using A/B testing between old and new classifiers.
        
        Args:
            sender: Email sender
            subject: Email subject
            body: Email body content
            headers: Email headers
            force_classifier: Force use of 'old' or 'new' classifier
            
        Returns:
            Classification result from selected classifier with A/B metadata
        """
        test_id = datetime.now().strftime('%Y%m%d')
        
        # Determine which classifier to use
        if force_classifier:
            use_new = force_classifier == 'new'
        else:
            use_new = random.random() * 100 < self.rollout_percentage
        
        # Always run both classifiers for comparison (if old is available)
        comparison_data = self._run_comparison(sender, subject, body, headers)
        
        # Select result based on A/B test
        if use_new:
            primary_result = comparison_data['new_result'].copy()
            primary_result['classifier_used'] = 'new'
            primary_result['ab_test_id'] = test_id
            primary_result['classification_version'] = 2
        else:
            primary_result = comparison_data['old_result'].copy()
            primary_result['classifier_used'] = 'old'
            primary_result['ab_test_id'] = test_id
            primary_result['classification_version'] = 1
        
        # Add comparison metadata
        primary_result['ab_testing'] = {
            'enabled': True,
            'rollout_percentage': self.rollout_percentage,
            'categories_match': comparison_data['categories_match'],
            'old_category': comparison_data['old_result'].get('predicted_category', 'N/A'),
            'new_category': comparison_data['new_result'].get('category'),
            'new_subcategory': comparison_data['new_result'].get('subcategory'),
            'confidence_delta': abs(
                comparison_data['old_result'].get('category_confidence', 0) - 
                comparison_data['new_result'].get('confidence', 0)
            )
        }
        
        # Track the comparison
        self._track_comparison(test_id, sender, subject, comparison_data, use_new)
        
        return primary_result
    
    def _run_comparison(self, sender: str, subject: str, 
                       body: str = "", headers: str = "") -> Dict[str, Any]:
        """Run both classifiers and compare results."""
        # Time old classifier
        if self.old_available:
            start_old = time.time()
            try:
                # Extract domain from sender
                domain = sender.split('@')[1] if '@' in sender else None
                old_result = self.old_classifier.predict_email_category(
                    sender, subject, domain, headers
                )
            except Exception as e:
                old_result = {
                    'predicted_category': 'Error',
                    'category_confidence': 0.0,
                    'error': str(e)
                }
            old_time = (time.time() - start_old) * 1000
        else:
            old_result = {
                'predicted_category': 'N/A',
                'category_confidence': 0.0
            }
            old_time = 0
        
        # Time new classifier
        start_new = time.time()
        new_result = self.new_classifier.classify(sender, subject, body)
        new_time = (time.time() - start_new) * 1000
        
        # Map old categories to new for comparison
        category_mapping = {
            'Phishing': 'Dangerous',
            'Payment Scam': 'Scams',
            'Financial & Investment Spam': 'Commercial Spam',
            'Health & Medical Spam': 'Commercial Spam',
            'Adult & Dating Spam': 'Commercial Spam',
            'Business Opportunity Spam': 'Commercial Spam',
            'Promotional Email': 'Legitimate Marketing'
        }
        
        old_mapped = category_mapping.get(
            old_result.get('predicted_category', ''), 
            old_result.get('predicted_category', '')
        )
        
        categories_match = old_mapped == new_result['category']
        
        return {
            'old_result': old_result,
            'new_result': new_result,
            'old_time': old_time,
            'new_time': new_time,
            'categories_match': categories_match
        }
    
    def _track_comparison(self, test_id: str, sender: str, subject: str,
                         comparison_data: Dict[str, Any], used_new: bool):
        """Track comparison results in database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            INSERT INTO ab_testing_results 
            (test_id, sender, subject, old_category, old_confidence,
             new_category, new_subcategory, new_confidence, categories_match,
             processing_time_old, processing_time_new, selected_classifier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            sender,
            subject,
            comparison_data['old_result'].get('predicted_category'),
            comparison_data['old_result'].get('category_confidence', 0),
            comparison_data['new_result']['category'],
            comparison_data['new_result']['subcategory'],
            comparison_data['new_result']['confidence'],
            comparison_data['categories_match'],
            comparison_data['old_time'],
            comparison_data['new_time'],
            'new' if used_new else 'old'
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get A/B testing performance metrics."""
        conn = sqlite3.connect(self.db_path)
        
        # Get recent results
        since_date = (datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_classifications,
                SUM(CASE WHEN selected_classifier = 'new' THEN 1 ELSE 0 END) as new_classifier_uses,
                AVG(processing_time_old) as avg_old_time,
                AVG(processing_time_new) as avg_new_time,
                AVG(CASE WHEN categories_match THEN 1.0 ELSE 0.0 END) as match_rate,
                COUNT(DISTINCT CASE WHEN new_category = 'Commercial Spam' 
                                   AND new_subcategory = 'Auto warranty & insurance' 
                                   THEN sender || subject END) as auto_warranty_fixes
            FROM ab_testing_results
            WHERE timestamp >= ?
        """, (since_date,))
        
        metrics = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_classifications': metrics[0] or 0,
            'new_classifier_uses': metrics[1] or 0,
            'avg_processing_time_old_ms': metrics[2] or 0,
            'avg_processing_time_new_ms': metrics[3] or 0,
            'category_match_rate': metrics[4] or 0,
            'auto_warranty_fixes': metrics[5] or 0,
            'rollout_percentage': self.rollout_percentage
        }
    
    def set_rollout_percentage(self, percentage: float):
        """Update the rollout percentage for new classifier."""
        self.rollout_percentage = max(0, min(100, percentage))
        print(f"✅ Rollout percentage set to {self.rollout_percentage}%")
        
        
def test_ab_integration():
    """Test the A/B integration with sample emails."""
    ab_classifier = ABClassifierIntegrationSimple(rollout_percentage=50)
    
    test_emails = [
        {
            'sender': 'warranty@autoprotect.com',
            'subject': 'Your auto warranty is about to expire',
            'body': 'Final notice about your vehicle warranty.'
        },
        {
            'sender': 'support@paypal.com',
            'subject': 'Verify your account',
            'body': 'Please verify your PayPal account.'
        }
    ]
    
    print("🧪 Testing A/B Classification Integration")
    print("=" * 60)
    
    for email in test_emails:
        result = ab_classifier.classify_with_ab_testing(
            email['sender'],
            email['subject'],
            email['body']
        )
        
        print(f"\nSubject: {email['subject']}")
        print(f"Classifier Used: {result['classifier_used']}")
        if result['classifier_used'] == 'new':
            print(f"Category: {result['category']}")
            print(f"Subcategory: {result['subcategory']}")
        else:
            print(f"Category: {result.get('predicted_category', 'Unknown')}")
        print(f"A/B Match: {result['ab_testing']['categories_match']}")
        

if __name__ == "__main__":
    test_ab_integration()