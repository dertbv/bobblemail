"""
A/B Testing Integration for 4-Category Classification System
===========================================================

This module enables parallel operation of the old and new classification systems
for A/B testing and gradual rollout.
"""

import sqlite3
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import random

from atlas_email.ml.category_classifier import MultiClassCategoryClassifier
from atlas_email.ml.four_category_classifier import FourCategoryClassifier
from atlas_email.ml.subcategory_tagger import SubcategoryTagger
from atlas_email.models.database import DB_FILE


class ABClassifierIntegration:
    """
    Manages A/B testing between old and new classification systems.
    """
    
    def __init__(self, db_path: str = None, rollout_percentage: float = 0.0):
        """
        Initialize A/B testing integration.
        
        Args:
            db_path: Database path
            rollout_percentage: Percentage of traffic to route to new classifier (0-100)
        """
        self.db_path = db_path or DB_FILE
        self.rollout_percentage = rollout_percentage
        
        # Initialize both classifiers
        self.old_classifier = MultiClassCategoryClassifier(db_path)
        self.new_classifier = FourCategoryClassifier(db_path)
        self.subcategory_tagger = SubcategoryTagger(db_path)
        
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
                                domain: str = None, headers: str = "",
                                force_classifier: str = None) -> Dict[str, Any]:
        """
        Classify email using A/B testing between old and new classifiers.
        
        Args:
            sender: Email sender
            subject: Email subject
            domain: Sender domain
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
        
        # Always run both classifiers for comparison
        comparison_data = self._run_comparison(sender, subject, domain, headers)
        
        # Select result based on A/B test
        if use_new:
            primary_result = comparison_data['new_result'].copy()
            primary_result['classifier_used'] = 'new'
            primary_result['ab_test_id'] = test_id
        else:
            primary_result = comparison_data['old_result'].copy()
            primary_result['classifier_used'] = 'old'
            primary_result['ab_test_id'] = test_id
        
        # Add comparison metadata
        primary_result['ab_testing'] = {
            'enabled': True,
            'rollout_percentage': self.rollout_percentage,
            'categories_match': comparison_data['categories_match'],
            'old_category': comparison_data['old_result'].get('predicted_category'),
            'new_category': comparison_data['new_result'].get('category'),
            'confidence_delta': abs(
                comparison_data['old_result'].get('category_confidence', 0) - 
                comparison_data['new_result'].get('confidence', 0)
            )
        }
        
        # Track the comparison
        self._track_comparison(test_id, sender, subject, comparison_data, use_new)
        
        return primary_result
    
    def _run_comparison(self, sender: str, subject: str, 
                       domain: str = None, headers: str = "") -> Dict[str, Any]:
        """Run both classifiers and compare results."""
        # Time old classifier
        start_old = time.time()
        try:
            old_result = self.old_classifier.predict_email_category(
                sender, subject, domain, headers
            )
        except Exception as e:
            old_result = {
                'predicted_category': 'Error',
                'category_confidence': 0.0,
                'error': str(e)
            }
        time_old = time.time() - start_old
        
        # Time new classifier
        start_new = time.time()
        try:
            new_result = self.new_classifier.classify(sender, subject, domain)
        except Exception as e:
            new_result = {
                'category': 'Error',
                'subcategory': 'Error',
                'confidence': 0.0,
                'error': str(e)
            }
        time_new = time.time() - start_new
        
        # Map old category to new system for comparison
        old_category_mapped = self._map_old_to_new_category(
            old_result.get('predicted_category', 'Unknown')
        )
        
        categories_match = old_category_mapped == new_result.get('category')
        
        return {
            'old_result': old_result,
            'new_result': new_result,
            'processing_time_old': time_old,
            'processing_time_new': time_new,
            'categories_match': categories_match,
            'old_category_mapped': old_category_mapped
        }
    
    def _map_old_to_new_category(self, old_category: str) -> str:
        """Map old category to new 4-category system."""
        # Use the mapping from FourCategoryClassifier
        mapping = FourCategoryClassifier.CATEGORY_MAPPING.get(old_category)
        if mapping:
            return mapping[0]  # Return new category
        
        # Default mapping logic
        if 'phish' in old_category.lower():
            return 'Dangerous'
        elif 'scam' in old_category.lower():
            return 'Scams'
        elif 'legitimate' in old_category.lower() or 'promotional' in old_category.lower():
            return 'Legitimate Marketing'
        else:
            return 'Commercial Spam'
    
    def _track_comparison(self, test_id: str, sender: str, subject: str,
                         comparison_data: Dict, used_new: bool):
        """Track A/B testing comparison results."""
        conn = sqlite3.connect(self.db_path)
        
        old_result = comparison_data['old_result']
        new_result = comparison_data['new_result']
        
        conn.execute("""
            INSERT INTO ab_testing_results 
            (test_id, sender, subject, old_category, old_confidence,
             new_category, new_subcategory, new_confidence, categories_match,
             processing_time_old, processing_time_new, selected_classifier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id, sender, subject,
            old_result.get('predicted_category'),
            old_result.get('category_confidence', 0.0),
            new_result.get('category'),
            new_result.get('subcategory'),
            new_result.get('confidence', 0.0),
            comparison_data['categories_match'],
            comparison_data['processing_time_old'],
            comparison_data['processing_time_new'],
            'new' if used_new else 'old'
        ))
        
        conn.commit()
        conn.close()
    
    def get_ab_testing_metrics(self, test_id: str = None, 
                              days: int = 7) -> Dict[str, Any]:
        """Get A/B testing metrics and comparison results."""
        conn = sqlite3.connect(self.db_path)
        
        # Base query
        if test_id:
            query = """
                SELECT * FROM ab_testing_results 
                WHERE test_id = ?
            """
            params = (test_id,)
        else:
            query = """
                SELECT * FROM ab_testing_results 
                WHERE timestamp > datetime('now', '-' || ? || ' days')
            """
            params = (days,)
        
        cursor = conn.execute(query, params)
        results = cursor.fetchall()
        
        # Calculate metrics
        metrics = {
            'total_comparisons': len(results),
            'agreement_rate': 0.0,
            'old_classifier_selections': 0,
            'new_classifier_selections': 0,
            'avg_time_old': 0.0,
            'avg_time_new': 0.0,
            'category_distribution_old': defaultdict(int),
            'category_distribution_new': defaultdict(int),
            'mismatches': []
        }
        
        if results:
            agreements = sum(1 for r in results if r[9])  # categories_match column
            metrics['agreement_rate'] = agreements / len(results) * 100
            
            metrics['old_classifier_selections'] = sum(1 for r in results if r[12] == 'old')
            metrics['new_classifier_selections'] = sum(1 for r in results if r[12] == 'new')
            
            total_time_old = sum(r[10] for r in results if r[10])
            total_time_new = sum(r[11] for r in results if r[11])
            
            metrics['avg_time_old'] = total_time_old / len(results) if results else 0
            metrics['avg_time_new'] = total_time_new / len(results) if results else 0
            
            # Category distributions
            for r in results:
                if r[4]:  # old_category
                    metrics['category_distribution_old'][r[4]] += 1
                if r[6]:  # new_category
                    metrics['category_distribution_new'][r[6]] += 1
                
                # Track mismatches
                if not r[9] and len(metrics['mismatches']) < 10:
                    metrics['mismatches'].append({
                        'sender': r[2],
                        'subject': r[3],
                        'old_category': r[4],
                        'new_category': r[6],
                        'new_subcategory': r[7]
                    })
        
        conn.close()
        return metrics
    
    def update_rollout_percentage(self, new_percentage: float):
        """Update the rollout percentage for new classifier."""
        if 0 <= new_percentage <= 100:
            self.rollout_percentage = new_percentage
            print(f"✅ Rollout percentage updated to {new_percentage}%")
        else:
            raise ValueError("Rollout percentage must be between 0 and 100")
    
    def get_recommendation(self) -> Dict[str, Any]:
        """Get recommendation on whether to increase rollout based on metrics."""
        metrics = self.get_ab_testing_metrics(days=7)
        
        recommendation = {
            'current_rollout': self.rollout_percentage,
            'recommended_action': 'maintain',
            'recommended_rollout': self.rollout_percentage,
            'confidence': 0.0,
            'reasons': []
        }
        
        if metrics['total_comparisons'] < 100:
            recommendation['recommended_action'] = 'wait'
            recommendation['reasons'].append("Insufficient data (need 100+ comparisons)")
            return recommendation
        
        # Check agreement rate
        if metrics['agreement_rate'] >= 90:
            recommendation['confidence'] += 0.3
            recommendation['reasons'].append(f"High agreement rate: {metrics['agreement_rate']:.1f}%")
        elif metrics['agreement_rate'] < 70:
            recommendation['confidence'] -= 0.3
            recommendation['reasons'].append(f"Low agreement rate: {metrics['agreement_rate']:.1f}%")
        
        # Check performance
        if metrics['avg_time_new'] <= metrics['avg_time_old'] * 1.5:
            recommendation['confidence'] += 0.2
            recommendation['reasons'].append("New classifier performance acceptable")
        else:
            recommendation['confidence'] -= 0.2
            recommendation['reasons'].append("New classifier slower than acceptable")
        
        # Check for auto warranty fix effectiveness
        auto_warranty_fixes = self._check_auto_warranty_fixes()
        if auto_warranty_fixes['improvement_rate'] > 80:
            recommendation['confidence'] += 0.3
            recommendation['reasons'].append(
                f"Auto warranty classification improved by {auto_warranty_fixes['improvement_rate']:.1f}%"
            )
        
        # Make recommendation
        if recommendation['confidence'] >= 0.5:
            if self.rollout_percentage < 100:
                recommendation['recommended_action'] = 'increase'
                recommendation['recommended_rollout'] = min(
                    self.rollout_percentage + 20, 100
                )
        elif recommendation['confidence'] <= -0.3:
            if self.rollout_percentage > 0:
                recommendation['recommended_action'] = 'decrease'
                recommendation['recommended_rollout'] = max(
                    self.rollout_percentage - 20, 0
                )
        
        return recommendation
    
    def _check_auto_warranty_fixes(self) -> Dict[str, Any]:
        """Check effectiveness of auto warranty classification fixes."""
        conn = sqlite3.connect(self.db_path)
        
        # Check recent auto warranty classifications
        cursor = conn.execute("""
            SELECT 
                COUNT(CASE WHEN old_category = 'Adult & Dating Spam' 
                      AND subject LIKE '%warranty%' THEN 1 END) as old_misclassified,
                COUNT(CASE WHEN new_category = 'Commercial Spam' 
                      AND new_subcategory = 'Auto warranty & insurance' THEN 1 END) as new_correct,
                COUNT(CASE WHEN subject LIKE '%warranty%' THEN 1 END) as total_warranty
            FROM ab_testing_results
            WHERE timestamp > datetime('now', '-7 days')
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        old_misclassified = result[0] or 0
        new_correct = result[1] or 0
        total_warranty = result[2] or 1  # Avoid division by zero
        
        improvement_rate = (new_correct / total_warranty * 100) if total_warranty > 0 else 0
        
        return {
            'old_misclassified': old_misclassified,
            'new_correct': new_correct,
            'total_warranty': total_warranty,
            'improvement_rate': improvement_rate
        }
    
    def generate_ab_report(self, output_file: str = None) -> str:
        """Generate comprehensive A/B testing report."""
        metrics = self.get_ab_testing_metrics(days=7)
        recommendation = self.get_recommendation()
        auto_warranty = self._check_auto_warranty_fixes()
        
        report = {
            'report_date': datetime.now().isoformat(),
            'rollout_status': {
                'current_percentage': self.rollout_percentage,
                'total_comparisons': metrics['total_comparisons'],
                'period_days': 7
            },
            'performance_metrics': {
                'agreement_rate': metrics['agreement_rate'],
                'avg_processing_time_old': metrics['avg_time_old'],
                'avg_processing_time_new': metrics['avg_time_new'],
                'speed_ratio': metrics['avg_time_new'] / metrics['avg_time_old'] if metrics['avg_time_old'] > 0 else 0
            },
            'classification_metrics': {
                'category_distribution_old': dict(metrics['category_distribution_old']),
                'category_distribution_new': dict(metrics['category_distribution_new']),
                'top_mismatches': metrics['mismatches'][:5]
            },
            'auto_warranty_fix': {
                'total_warranty_emails': auto_warranty['total_warranty'],
                'old_misclassified': auto_warranty['old_misclassified'],
                'new_correct': auto_warranty['new_correct'],
                'improvement_rate': auto_warranty['improvement_rate']
            },
            'recommendation': recommendation
        }
        
        if output_file is None:
            output_file = f"ab_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ A/B testing report saved to: {output_file}")
        return output_file


# Testing and monitoring
if __name__ == "__main__":
    # Initialize with 20% rollout
    ab_integration = ABClassifierIntegration(rollout_percentage=20.0)
    
    # Test cases
    test_emails = [
        {
            'sender': 'warranty@auto-protect.com',
            'subject': 'Final Notice: Your auto warranty is about to expire!'
        },
        {
            'sender': 'security@amaz0n-verify.com',
            'subject': 'Urgent: Verify your account or it will be suspended'
        },
        {
            'sender': 'deals@legitimate-store.com',
            'subject': 'Weekend Sale: 30% off all items'
        }
    ]
    
    print("🧪 A/B Testing Classification System")
    print("=" * 80)
    print(f"Current rollout: {ab_integration.rollout_percentage}%")
    print()
    
    for email in test_emails:
        print(f"📧 Testing: {email['subject'][:50]}...")
        result = ab_integration.classify_with_ab_testing(
            email['sender'], 
            email['subject']
        )
        
        print(f"   Classifier used: {result['classifier_used']}")
        print(f"   Category: {result.get('category') or result.get('predicted_category')}")
        print(f"   Confidence: {result.get('confidence') or result.get('category_confidence'):.3f}")
        print(f"   Categories match: {result['ab_testing']['categories_match']}")
        print()
    
    # Get metrics
    print("\n📊 A/B Testing Metrics (Last 7 days):")
    metrics = ab_integration.get_ab_testing_metrics()
    print(f"   Total comparisons: {metrics['total_comparisons']}")
    print(f"   Agreement rate: {metrics['agreement_rate']:.1f}%")
    print(f"   Avg time old: {metrics['avg_time_old']:.3f}s")
    print(f"   Avg time new: {metrics['avg_time_new']:.3f}s")
    
    # Get recommendation
    print("\n🎯 Rollout Recommendation:")
    rec = ab_integration.get_recommendation()
    print(f"   Action: {rec['recommended_action']}")
    print(f"   Recommended rollout: {rec['recommended_rollout']}%")
    print(f"   Confidence: {rec['confidence']:.2f}")
    print("   Reasons:")
    for reason in rec['reasons']:
        print(f"      - {reason}")
    
    # Generate report
    report_file = ab_integration.generate_ab_report()
    print(f"\n📄 Full report saved to: {report_file}")