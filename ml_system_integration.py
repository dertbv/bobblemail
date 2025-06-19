"""
ML System Integration - Advanced Email Spam Detection Suite
==========================================================

Integrates all advanced ML components into a unified, production-ready system:
- Advanced ML classifiers with multiple algorithms
- Adaptive pattern detection for evolving threats
- Continuous learning pipeline
- Comprehensive evaluation framework
- Seamless integration with existing email processing system
"""

import json
import sqlite3
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import threading
import time
from dataclasses import dataclass

# Import all our advanced ML components
from advanced_ml_classifier import AdvancedMLClassifier
from adaptive_pattern_detector import AdaptivePatternDetector
from continuous_learning_system import ContinuousLearningSystem
from advanced_evaluation_framework import AdvancedEvaluationFramework, EvaluationMetrics
from ml_classifier import NaiveBayesClassifier

@dataclass
class UnifiedPrediction:
    """Unified prediction result combining all ML approaches."""
    final_prediction: int  # 0 = legitimate, 1 = spam
    confidence: float
    spam_probability: float
    reasoning: List[str]
    
    # Component predictions
    ml_prediction: Optional[Dict[str, Any]] = None
    pattern_prediction: Optional[Dict[str, Any]] = None
    baseline_prediction: Optional[Dict[str, Any]] = None
    
    # Metadata
    processing_time_ms: float = 0.0
    model_versions: Dict[str, int] = None
    features_used: int = 0

class AdvancedMLSystem:
    """
    Unified advanced ML system for email spam detection.
    
    Integrates multiple ML approaches with continuous learning and evaluation.
    """
    
    def __init__(self, db_path: str = "mail_filter.db", auto_train: bool = True):
        self.db_path = db_path
        self.auto_train = auto_train
        
        # Initialize all components
        print("🚀 Initializing Advanced ML System...")
        self.advanced_classifier = AdvancedMLClassifier(db_path)
        self.pattern_detector = AdaptivePatternDetector(db_path)
        self.continuous_learning = ContinuousLearningSystem(db_path)
        self.evaluation_framework = AdvancedEvaluationFramework(db_path)
        self.baseline_classifier = NaiveBayesClassifier(db_path)
        
        # System state
        self.is_trained = False
        self.system_version = "2.0.0"
        self.initialization_time = datetime.now()
        
        # Performance tracking
        self.prediction_count = 0
        self.total_processing_time = 0.0
        self.performance_stats = {
            'predictions_made': 0,
            'average_processing_time': 0.0,
            'accuracy_estimates': [],
            'user_feedback_count': 0
        }
        
        # Configuration
        self.config = {
            'use_advanced_ml': True,
            'use_pattern_detection': True,
            'use_ensemble_voting': True,
            'confidence_threshold': 0.7,
            'fallback_to_baseline': True,
            'continuous_learning_enabled': True,
            'auto_retrain_threshold': 100
        }
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the complete ML system."""
        try:
            # Train baseline classifier first
            print("📊 Training baseline Naive Bayes classifier...")
            baseline_summary = self.baseline_classifier.train(use_user_feedback=True)
            print("✅ Baseline classifier trained")
            
            # Train advanced classifiers if enabled
            if self.config['use_advanced_ml'] and self.auto_train:
                print("🧠 Training advanced ML classifiers...")
                try:
                    performance = self.advanced_classifier.train_all_models(
                        use_user_feedback=True, max_samples=1000
                    )
                    print("✅ Advanced classifiers trained")
                except Exception as e:
                    print(f"⚠️  Advanced classifier training failed: {e}")
                    print("   Falling back to baseline classifier only")
                    self.config['use_advanced_ml'] = False
            
            # Start continuous learning if enabled
            if self.config['continuous_learning_enabled']:
                self.continuous_learning.start_continuous_learning()
                print("✅ Continuous learning system started")
            
            self.is_trained = True
            print("🎉 Advanced ML System initialization completed successfully!")
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            print("   System running in limited mode")
            self.is_trained = False
    
    def predict_spam(self, sender: str, subject: str, domain: str = None, 
                    headers: str = "") -> UnifiedPrediction:
        """
        Make a unified spam prediction using all available ML approaches.
        
        Args:
            sender: Email sender
            subject: Email subject
            domain: Sender domain (optional)
            headers: Email headers (optional)
            
        Returns:
            Unified prediction with confidence and reasoning
        """
        start_time = time.time()
        
        if not self.is_trained:
            # Fallback prediction
            return self._fallback_prediction(sender, subject)
        
        reasoning = []
        predictions = {}
        
        # 1. Baseline Naive Bayes prediction (always available)
        try:
            baseline_pred = self.baseline_classifier.predict_single(
                sender, subject, domain, headers
            )
            predictions['baseline'] = baseline_pred
            reasoning.append(f"Baseline classifier: {baseline_pred['spam_probability']:.2f} spam probability")
            
        except Exception as e:
            print(f"⚠️  Baseline prediction failed: {e}")
            baseline_pred = {'spam_probability': 0.5, 'predicted_class': 0}
            predictions['baseline'] = baseline_pred
        
        # 2. Advanced ML prediction (if available)
        ml_pred = None
        if self.config['use_advanced_ml']:
            try:
                ml_pred = self.advanced_classifier.predict_advanced(
                    sender, subject, domain, headers
                )
                predictions['advanced_ml'] = ml_pred
                reasoning.append(f"Advanced ML: {ml_pred['spam_probability']:.2f} spam probability")
                reasoning.append(f"ML consensus: {ml_pred['consensus_strength']:.2f}")
                
            except Exception as e:
                print(f"⚠️  Advanced ML prediction failed: {e}")
                reasoning.append("Advanced ML unavailable")
        
        # 3. Pattern-based prediction (if enabled)
        pattern_pred = None
        if self.config['use_pattern_detection']:
            try:
                pattern_pred = self.pattern_detector.predict_using_patterns(sender, subject)
                predictions['patterns'] = pattern_pred
                reasoning.append(f"Pattern analysis: {pattern_pred['confidence']:.2f} confidence")
                
                if pattern_pred['matched_patterns']:
                    reasoning.append(f"Matched {len(pattern_pred['matched_patterns'])} known patterns")
                
                if pattern_pred['campaign_matches']:
                    reasoning.append(f"Matched {len(pattern_pred['campaign_matches'])} spam campaigns")
                    
            except Exception as e:
                print(f"⚠️  Pattern prediction failed: {e}")
                reasoning.append("Pattern analysis unavailable")
        
        # 4. Combine predictions using ensemble voting
        final_prediction = self._combine_predictions(predictions)
        
        # 5. Apply confidence threshold
        if final_prediction['confidence'] < self.config['confidence_threshold']:
            reasoning.append(f"Low confidence ({final_prediction['confidence']:.2f}), conservative classification")
            # Be more conservative - lean towards not spam if unsure
            if final_prediction['spam_probability'] < 0.7:
                final_prediction['final_prediction'] = 0
                final_prediction['spam_probability'] = min(final_prediction['spam_probability'], 0.4)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Update performance tracking
        self._update_performance_stats(processing_time)
        
        # Record prediction for continuous learning
        if self.config['continuous_learning_enabled']:
            self.continuous_learning.record_prediction(
                sender, subject, final_prediction['final_prediction'], 
                final_prediction['confidence']
            )
        
        # Create unified prediction result
        unified_prediction = UnifiedPrediction(
            final_prediction=final_prediction['final_prediction'],
            confidence=final_prediction['confidence'],
            spam_probability=final_prediction['spam_probability'],
            reasoning=reasoning,
            ml_prediction=ml_pred,
            pattern_prediction=pattern_pred,
            baseline_prediction=baseline_pred,
            processing_time_ms=processing_time,
            model_versions={
                'system': self.system_version,
                'baseline': getattr(self.baseline_classifier, 'model_version', 1),
                'advanced_ml': getattr(self.advanced_classifier, 'model_version', 1)
            },
            features_used=ml_pred.get('features_used', 0) if ml_pred else 0
        )
        
        return unified_prediction
    
    def _combine_predictions(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Combine multiple predictions using ensemble voting."""
        if not predictions:
            return {'final_prediction': 0, 'spam_probability': 0.5, 'confidence': 0.1}
        
        # Weight the predictions based on their reliability
        weights = {
            'baseline': 0.3,       # Reliable but basic
            'advanced_ml': 0.5,    # Most sophisticated
            'patterns': 0.2        # Good for known threats
        }
        
        spam_probs = []
        confidences = []
        votes = []
        
        # Collect weighted predictions
        for pred_type, pred_data in predictions.items():
            weight = weights.get(pred_type, 0.1)
            
            if pred_type == 'baseline':
                spam_prob = pred_data.get('spam_probability', 0.5)
                confidence = pred_data.get('confidence', 0.5)
                vote = pred_data.get('predicted_class', 0)
                
            elif pred_type == 'advanced_ml':
                spam_prob = pred_data.get('spam_probability', 0.5)
                confidence = pred_data.get('confidence', 0.5)
                vote = pred_data.get('final_prediction', 0)
                
            elif pred_type == 'patterns':
                spam_prob = 0.8 if pred_data.get('is_spam_by_patterns', False) else 0.2
                confidence = pred_data.get('confidence', 0.5)
                vote = 1 if pred_data.get('is_spam_by_patterns', False) else 0
                
            else:
                continue
            
            # Add weighted contributions
            spam_probs.append(spam_prob * weight)
            confidences.append(confidence * weight)
            votes.append(vote * weight)
        
        # Calculate final values
        final_spam_prob = sum(spam_probs) / sum(weights.values()) if spam_probs else 0.5
        final_confidence = sum(confidences) / sum(weights.values()) if confidences else 0.5
        final_vote = sum(votes) / sum(weights.values()) if votes else 0
        
        # Determine final classification
        final_prediction = 1 if final_spam_prob > 0.5 else 0
        
        # Boost confidence if all methods agree
        if len(set(pred.get('predicted_class', pred.get('final_prediction', 0)) 
                  for pred in predictions.values())) == 1:
            final_confidence = min(final_confidence * 1.2, 1.0)
        
        return {
            'final_prediction': final_prediction,
            'spam_probability': final_spam_prob,
            'confidence': final_confidence
        }
    
    def _fallback_prediction(self, sender: str, subject: str) -> UnifiedPrediction:
        """Fallback prediction when system is not trained."""
        # Simple heuristic-based prediction
        spam_indicators = 0
        
        if subject:
            spam_words = ['urgent', 'free', 'win', 'money', '$$$', '💰', '🚀']
            spam_indicators += sum(1 for word in spam_words if word in subject.lower())
        
        if sender:
            if any(suspicious in sender.lower() for suspicious in ['noreply', 'no-reply']):
                spam_indicators += 1
        
        spam_probability = min(spam_indicators * 0.2, 0.9)
        final_prediction = 1 if spam_probability > 0.5 else 0
        
        return UnifiedPrediction(
            final_prediction=final_prediction,
            confidence=0.3,  # Low confidence for fallback
            spam_probability=spam_probability,
            reasoning=["System not trained - using fallback heuristics"],
            processing_time_ms=1.0
        )
    
    def record_user_feedback(self, sender: str, subject: str, 
                           predicted_spam: bool, actual_spam: bool,
                           user_comment: str = "") -> bool:
        """
        Record user feedback for continuous learning.
        
        Args:
            sender: Email sender
            subject: Email subject  
            predicted_spam: What the system predicted
            actual_spam: What it actually was
            user_comment: Optional user comment
            
        Returns:
            Success status
        """
        try:
            # Convert to labels
            predicted_label = 1 if predicted_spam else 0
            true_label = 1 if actual_spam else 0
            
            # Determine correction type
            if predicted_label == true_label:
                correction_type = 'correct'
            elif predicted_label == 1 and true_label == 0:
                correction_type = 'false_positive'
            else:
                correction_type = 'false_negative'
            
            # Record in continuous learning system
            if self.config['continuous_learning_enabled']:
                self.continuous_learning.record_learning_event(
                    sender, subject, true_label, predicted_label,
                    0.9,  # High confidence for user feedback
                    'user_feedback', correction_type
                )
            
            # Update pattern detector
            if self.config['use_pattern_detection']:
                action = 'DELETED' if actual_spam else 'PRESERVED'
                self.pattern_detector.analyze_email_for_patterns(
                    sender, subject, action
                )
            
            # Update performance stats
            self.performance_stats['user_feedback_count'] += 1
            
            print(f"📝 User feedback recorded: {correction_type} for '{subject[:40]}...'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to record user feedback: {e}")
            return False
    
    def evaluate_system_performance(self, test_size: int = 200) -> Dict[str, Any]:
        """
        Evaluate current system performance.
        
        Args:
            test_size: Number of test samples to use
            
        Returns:
            Comprehensive evaluation results
        """
        print(f"📊 Evaluating system performance with {test_size} samples...")
        
        try:
            # Get test data from recent emails
            test_data = self._get_recent_test_data(test_size)
            
            if not test_data or len(test_data[0]) < 10:
                return {'error': 'Insufficient test data'}
            
            X_test, y_true = test_data
            
            # Make predictions on test data
            predictions = []
            processing_times = []
            
            for test_email in X_test:
                start_time = time.time()
                
                unified_pred = self.predict_spam(
                    test_email.get('sender', ''),
                    test_email.get('subject', '')
                )
                
                predictions.append(unified_pred.final_prediction)
                processing_times.append(time.time() - start_time)
            
            # Create evaluation metrics
            metrics = self.evaluation_framework._calculate_comprehensive_metrics(
                y_true, predictions, "UnifiedMLSystem", len(X_test)
            )
            
            # Add system-specific metrics
            system_metrics = {
                'evaluation_metrics': metrics,
                'average_processing_time_ms': statistics.mean(processing_times) * 1000,
                'total_predictions_made': self.performance_stats['predictions_made'],
                'system_uptime_hours': (datetime.now() - self.initialization_time).total_seconds() / 3600,
                'continuous_learning_active': self.continuous_learning.learning_active,
                'user_feedback_count': self.performance_stats['user_feedback_count'],
                'system_version': self.system_version,
                'components_active': {
                    'baseline_classifier': True,
                    'advanced_ml': self.config['use_advanced_ml'] and self.advanced_classifier.is_trained,
                    'pattern_detection': self.config['use_pattern_detection'],
                    'continuous_learning': self.config['continuous_learning_enabled']
                }
            }
            
            print("✅ System evaluation completed")
            return system_metrics
            
        except Exception as e:
            print(f"❌ System evaluation failed: {e}")
            return {'error': str(e)}
    
    def _get_recent_test_data(self, limit: int) -> Optional[Tuple[List, List]]:
        """Get recent email data for testing."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT sender_email, subject, action 
                FROM processed_emails_bulletproof 
                WHERE subject IS NOT NULL AND subject != ''
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            emails = cursor.fetchall()
            conn.close()
            
            if not emails:
                return None
            
            X_test = [{'sender': email[0], 'subject': email[1]} for email in emails]
            y_test = [1 if email[2] == 'DELETED' else 0 for email in emails]
            
            return X_test, y_test
            
        except Exception as e:
            print(f"❌ Error getting test data: {e}")
            return None
    
    def _update_performance_stats(self, processing_time_ms: float):
        """Update performance statistics."""
        self.prediction_count += 1
        self.total_processing_time += processing_time_ms
        
        self.performance_stats['predictions_made'] = self.prediction_count
        self.performance_stats['average_processing_time'] = (
            self.total_processing_time / self.prediction_count
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'system_version': self.system_version,
            'is_trained': self.is_trained,
            'initialization_time': self.initialization_time.isoformat(),
            'uptime_hours': (datetime.now() - self.initialization_time).total_seconds() / 3600,
            'configuration': self.config,
            'performance_stats': self.performance_stats,
            'components_status': {
                'baseline_classifier': {
                    'trained': getattr(self.baseline_classifier, 'is_trained', False),
                    'training_size': getattr(self.baseline_classifier, 'training_size', 0)
                },
                'advanced_classifier': {
                    'trained': getattr(self.advanced_classifier, 'is_trained', False)
                },
                'pattern_detector': {
                    'patterns_learned': len(getattr(self.pattern_detector, 'patterns', {})),
                    'campaigns_detected': len(getattr(self.pattern_detector, 'campaigns', {}))
                },
                'continuous_learning': {
                    'active': getattr(self.continuous_learning, 'learning_active', False),
                    'events_in_queue': len(getattr(self.continuous_learning, 'learning_queue', []))
                }
            }
        }
    
    def shutdown(self):
        """Gracefully shutdown the ML system."""
        print("⏹️  Shutting down Advanced ML System...")
        
        # Stop continuous learning
        if self.config['continuous_learning_enabled']:
            self.continuous_learning.stop_continuous_learning()
        
        # Save models
        try:
            if self.is_trained:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_prefix = f"ml_system_shutdown_{timestamp}"
                
                if self.config['use_advanced_ml']:
                    self.advanced_classifier.save_models(f"{backup_prefix}_advanced")
                
                self.baseline_classifier.save_model(f"{backup_prefix}_baseline.json")
                
                print("✅ Models saved before shutdown")
        
        except Exception as e:
            print(f"⚠️  Error saving models: {e}")
        
        print("✅ Advanced ML System shutdown completed")


# Example usage and integration testing
if __name__ == "__main__":
    print("🚀 Testing Advanced ML System Integration...")
    
    # Initialize the unified system
    ml_system = AdvancedMLSystem(auto_train=True)
    
    try:
        # Test predictions
        test_emails = [
            ("support@amazon.com", "Your package has been delivered"),
            ("crypto-profits@scam.tk", "🚀💰 URGENT: 1000% Bitcoin Returns!"),
            ("newsletter@bank.com", "Monthly account statement is ready"),
            ("winner@lottery.fake", "🎉 Congratulations! You've won $1,000,000!"),
            ("noreply@legitimate-service.com", "Password reset confirmation")
        ]
        
        print("\n📧 Testing email predictions...")
        for sender, subject in test_emails:
            prediction = ml_system.predict_spam(sender, subject)
            
            spam_status = "SPAM" if prediction.final_prediction == 1 else "LEGITIMATE"
            print(f"   📨 '{subject[:40]}...' → {spam_status}")
            print(f"      Confidence: {prediction.confidence:.2f}")
            print(f"      Processing time: {prediction.processing_time_ms:.1f}ms")
            print(f"      Reasoning: {'; '.join(prediction.reasoning[:2])}")
            print()
        
        # Test user feedback
        print("📝 Testing user feedback system...")
        ml_system.record_user_feedback(
            "crypto-profits@scam.tk",
            "Bitcoin Returns!",
            predicted_spam=True,
            actual_spam=True,
            user_comment="Correctly identified crypto scam"
        )
        
        # Get system status
        print("📊 System Status:")
        status = ml_system.get_system_status()
        print(f"   Version: {status['system_version']}")
        print(f"   Uptime: {status['uptime_hours']:.1f} hours")
        print(f"   Predictions made: {status['performance_stats']['predictions_made']}")
        print(f"   Components active: {sum(status['components_status'][comp].get('trained', status['components_status'][comp].get('active', False)) for comp in status['components_status'])}/4")
        
        # Evaluate system performance
        print("\n📊 Evaluating system performance...")
        evaluation = ml_system.evaluate_system_performance(test_size=50)
        
        if 'evaluation_metrics' in evaluation:
            metrics = evaluation['evaluation_metrics']
            print(f"   Accuracy: {metrics.accuracy:.3f}")
            print(f"   F1 Score: {metrics.f1_score:.3f}")
            print(f"   False Positive Rate: {metrics.false_positive_rate:.3f}")
            print(f"   User Satisfaction: {metrics.user_satisfaction_score:.3f}")
        
        print("\n✅ Advanced ML System integration test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    finally:
        # Cleanup
        ml_system.shutdown()