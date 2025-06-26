"""
Binary Feedback Learning System - Phase 1
=========================================
Processes user feedback to improve ML model accuracy through supervised learning.

This system converts thumbs up/down feedback from the validation interface into
ML training data and retrains models for continuous improvement.
"""

import sqlite3
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import json

from atlas_email.models.database import DatabaseManager
from atlas_email.ml.feature_extractor import MLFeatureExtractor
from atlas_email.ml.naive_bayes import NaiveBayesClassifier
from atlas_email.ml.random_forest import RandomForestClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinaryFeedbackProcessor:
    """
    Processes user validation feedback to improve ML model accuracy.
    
    Converts thumbs up/down feedback into training data and retrains
    ML models for continuous learning and improvement.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from atlas_email.models.database import DB_FILE
            db_path = DB_FILE
        """Initialize the binary feedback processor."""
        self.db_path = db_path
        self.db = DatabaseManager(db_path)
        self.feature_extractor = MLFeatureExtractor(db_path)
        
        # Spam category definitions for label conversion
        self.spam_categories = {
            'Marketing Spam', 'Payment Scam', 'Phishing', 'Financial & Investment Spam',
            'Adult & Dating Spam', 'Health & Medical Spam', 'Gambling Spam', 'Tech Support Scam',
            'Brand Impersonation', 'Cryptocurrency Scam', 'Romance Scam', 'Prize Scam',
            'Fake Newsletter', 'Survey Scam', 'Job Scam', 'Software & App Spam',
            'Investment Scam', 'Pharmaceutical Spam', 'Travel Spam'
        }
        
        logger.info("🤖 Binary Feedback Processor initialized")
    
    def get_unprocessed_feedback(self) -> List[Dict[str, Any]]:
        """
        Retrieve all unprocessed feedback records with email context.
        
        Returns:
            List of feedback records with email data for feature extraction
        """
        try:
            query = """
            SELECT 
                uf.id,
                uf.sender,
                uf.subject,
                uf.original_classification,
                uf.feedback_type,
                uf.confidence_rating,
                uf.timestamp,
                peb.raw_data,
                peb.action,
                peb.confidence_score
            FROM user_feedback uf
            LEFT JOIN processed_emails_bulletproof peb 
                ON uf.sender = peb.sender_email 
                AND uf.subject = peb.subject
            WHERE uf.processed = FALSE
            ORDER BY uf.timestamp DESC
            """
            
            results = self.db.execute_query(query)
            
            feedback_records = []
            for row in results:
                feedback_records.append({
                    'id': row[0],
                    'sender': row[1],
                    'subject': row[2],
                    'original_classification': row[3],
                    'feedback_type': row[4],
                    'confidence_rating': row[5],
                    'timestamp': row[6],
                    'content': row[7] if row[7] else '',
                    'action': row[8] if row[8] else 'UNKNOWN',
                    'original_confidence': row[9] if row[9] else 0.5
                })
            
            logger.info(f"📊 Retrieved {len(feedback_records)} unprocessed feedback records")
            return feedback_records
            
        except Exception as e:
            logger.error(f"❌ Error retrieving unprocessed feedback: {e}")
            return []
    
    def convert_feedback_to_binary_labels(self, feedback_records: List[Dict]) -> List[Tuple[Dict, int]]:
        """
        Convert user feedback to binary training labels.
        
        Feedback Types:
        - 'false_positive': User says it's legitimate (label = 0)
        - 'correct': User confirms original classification (keep original)
        - 'incorrect': User disagrees with classification (flip original)
        
        Args:
            feedback_records: List of feedback records
            
        Returns:
            List of (record, binary_label) tuples
        """
        labeled_data = []
        
        for record in feedback_records:
            feedback_type = record['feedback_type']
            original_classification = record['original_classification']
            
            # Convert feedback to binary label
            if feedback_type == 'false_positive':
                # User confirmed it's legitimate
                binary_label = 0
                reason = "User confirmed legitimate"
                
            elif feedback_type == 'correct':
                # User confirmed original classification was correct
                if original_classification in self.spam_categories:
                    binary_label = 1  # Confirmed spam
                    reason = f"User confirmed spam: {original_classification}"
                else:
                    binary_label = 0  # Confirmed legitimate
                    reason = f"User confirmed legitimate: {original_classification}"
                    
            elif feedback_type == 'incorrect':
                # User disagreed with original classification
                if original_classification in self.spam_categories:
                    binary_label = 0  # Originally spam, user says legitimate
                    reason = f"User corrected spam to legitimate: {original_classification}"
                else:
                    binary_label = 1  # Originally legitimate, user says spam
                    reason = f"User corrected legitimate to spam: {original_classification}"
                    
            else:
                # Unknown feedback type, default to legitimate
                binary_label = 0
                reason = f"Unknown feedback type: {feedback_type}"
            
            # Add reasoning to record for tracking
            record['conversion_reason'] = reason
            labeled_data.append((record, binary_label))
            
        logger.info(f"🏷️ Converted {len(labeled_data)} feedback records to binary labels")
        return labeled_data
    
    def extract_features_from_feedback(self, labeled_data: List[Tuple[Dict, int]]) -> Tuple[List[List], List[int]]:
        """
        Extract ML features from feedback records.
        
        Args:
            labeled_data: List of (record, binary_label) tuples
            
        Returns:
            Tuple of (features_list, labels_list)
        """
        features_list = []
        labels_list = []
        
        for record, binary_label in labeled_data:
            try:
                # Extract features using existing feature extraction pipeline
                features = self.feature_extractor.extract_features_from_email(
                    sender=record['sender'],
                    subject=record['subject'],
                    headers=record['content']  # Use content as headers since it contains raw email data
                )
                
                if features and len(features) > 0:
                    features_list.append(features)
                    labels_list.append(binary_label)
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not extract features for record {record['id']}: {e}")
                continue
        
        logger.info(f"🧠 Extracted features for {len(features_list)} feedback records")
        return features_list, labels_list
    
    def retrain_models_with_feedback(self, features: List[List], labels: List[int]) -> Dict[str, Any]:
        """
        Retrain ML models with new feedback data.
        
        Args:
            features: List of feature vectors
            labels: List of binary labels
            
        Returns:
            Dictionary with retraining results and accuracy metrics
        """
        if len(features) == 0:
            logger.warning("⚠️ No features provided for retraining")
            return {'success': False, 'reason': 'No training data'}
        
        results = {
            'success': False,
            'models_retrained': [],
            'accuracy_improvements': {},
            'training_samples': len(features),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Retrain Naive Bayes classifier
            logger.info("🔄 Retraining Naive Bayes classifier with feedback data...")
            nb_classifier = NaiveBayesClassifier(self.db_path)
            
            # Load existing model for baseline evaluation
            if nb_classifier.load_model():
                # Get baseline accuracy before retraining
                baseline_accuracy = nb_classifier.evaluate_on_test_data().get('accuracy', 0.0)
            else:
                # Train from scratch if no model exists
                nb_classifier.train()
                baseline_accuracy = nb_classifier.evaluate_on_test_data().get('accuracy', 0.0)
            
            # Retrain with feedback data (feedback is automatically included)
            nb_success = nb_classifier.train(use_user_feedback=True)
            
            if nb_success:
                # Measure accuracy after retraining
                new_accuracy = nb_classifier.evaluate_on_test_data().get('accuracy', 0.0)
                accuracy_improvement = new_accuracy - baseline_accuracy
                
                results['models_retrained'].append('naive_bayes')
                results['accuracy_improvements']['naive_bayes'] = {
                    'baseline': baseline_accuracy,
                    'new_accuracy': new_accuracy,
                    'improvement': accuracy_improvement
                }
                logger.info(f"✅ Naive Bayes retrained: {accuracy_improvement:+.3f} accuracy change")
            
            # Retrain Random Forest classifier
            logger.info("🔄 Retraining Random Forest classifier with feedback data...")
            rf_classifier = RandomForestClassifier(self.db_path)
            
            # Get baseline accuracy before retraining
            baseline_accuracy = rf_classifier.evaluate_on_test_data() if hasattr(rf_classifier, 'evaluate_on_test_data') else 0.0
            
            # Retrain with feedback data
            rf_success = rf_classifier.train(additional_training_data=(features, labels))
            
            if rf_success:
                # Measure accuracy after retraining (if evaluation method exists)
                new_accuracy = rf_classifier.evaluate_on_test_data() if hasattr(rf_classifier, 'evaluate_on_test_data') else baseline_accuracy
                accuracy_improvement = new_accuracy - baseline_accuracy
                
                results['models_retrained'].append('random_forest')
                results['accuracy_improvements']['random_forest'] = {
                    'baseline': baseline_accuracy,
                    'new_accuracy': new_accuracy,
                    'improvement': accuracy_improvement
                }
                logger.info(f"✅ Random Forest retrained: {accuracy_improvement:+.3f} accuracy change")
            
            results['success'] = len(results['models_retrained']) > 0
            
        except Exception as e:
            logger.error(f"❌ Error during model retraining: {e}")
            results['error'] = str(e)
        
        return results
    
    def mark_feedback_processed(self, feedback_ids: List[int], retraining_results: Dict[str, Any]):
        """
        Mark feedback records as processed and track their contributions.
        
        Args:
            feedback_ids: List of feedback record IDs
            retraining_results: Results from model retraining
        """
        try:
            # Calculate overall accuracy improvement
            total_improvement = 0.0
            model_count = 0
            
            for model, metrics in retraining_results.get('accuracy_improvements', {}).items():
                total_improvement += metrics.get('improvement', 0.0)
                model_count += 1
            
            avg_improvement = total_improvement / model_count if model_count > 0 else 0.0
            contributed_to_accuracy = avg_improvement > 0.001  # Threshold for meaningful improvement
            
            # Update feedback records
            for feedback_id in feedback_ids:
                update_query = """
                UPDATE user_feedback 
                SET processed = TRUE,
                    contributed_to_accuracy = ?
                WHERE id = ?
                """
                
                self.db.execute_update(update_query, (
                    contributed_to_accuracy,
                    feedback_id
                ))
            
            logger.info(f"✅ Marked {len(feedback_ids)} feedback records as processed")
            logger.info(f"📈 Average accuracy improvement: {avg_improvement:+.3f}")
            
        except Exception as e:
            logger.error(f"❌ Error marking feedback as processed: {e}")
    
    def process_all_unprocessed_feedback(self) -> Dict[str, Any]:
        """
        Main method to process all unprocessed feedback and retrain models.
        
        Returns:
            Dictionary with processing results and metrics
        """
        logger.info("🚀 Starting binary feedback learning pipeline...")
        
        # Step 1: Get unprocessed feedback
        feedback_records = self.get_unprocessed_feedback()
        
        if not feedback_records:
            logger.info("ℹ️ No unprocessed feedback found")
            return {'success': True, 'feedback_count': 0, 'message': 'No feedback to process'}
        
        # Step 2: Convert feedback to binary labels
        labeled_data = self.convert_feedback_to_binary_labels(feedback_records)
        
        # Step 3: Extract features
        features, labels = self.extract_features_from_feedback(labeled_data)
        
        if not features:
            logger.warning("⚠️ No features could be extracted from feedback")
            return {'success': False, 'reason': 'Feature extraction failed'}
        
        # Step 4: Retrain models
        retraining_results = self.retrain_models_with_feedback(features, labels)
        
        # Step 5: Mark feedback as processed
        feedback_ids = [record['id'] for record, _ in labeled_data]
        self.mark_feedback_processed(feedback_ids, retraining_results)
        
        # Compile final results
        final_results = {
            'success': retraining_results.get('success', False),
            'feedback_processed': len(feedback_records),
            'features_extracted': len(features),
            'models_retrained': retraining_results.get('models_retrained', []),
            'accuracy_improvements': retraining_results.get('accuracy_improvements', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("🎯 Binary feedback learning pipeline completed")
        logger.info(f"📊 Final results: {json.dumps(final_results, indent=2)}")
        
        return final_results

def main():
    """Command-line interface for binary feedback processing."""
    print("🤖 Binary Feedback Learning System - Phase 1")
    print("=" * 50)
    
    processor = BinaryFeedbackProcessor()
    results = processor.process_all_unprocessed_feedback()
    
    print("\n📈 Processing Results:")
    print(f"  Feedback Records Processed: {results.get('feedback_processed', 0)}")
    print(f"  Features Extracted: {results.get('features_extracted', 0)}")
    print(f"  Models Retrained: {', '.join(results.get('models_retrained', []))}")
    
    accuracy_improvements = results.get('accuracy_improvements', {})
    if accuracy_improvements:
        print("\n🎯 Accuracy Improvements:")
        for model, metrics in accuracy_improvements.items():
            improvement = metrics.get('improvement', 0.0)
            print(f"  {model}: {improvement:+.3f} ({improvement*100:+.1f}%)")
    
    print(f"\n✅ Success: {results.get('success', False)}")

if __name__ == "__main__":
    main()