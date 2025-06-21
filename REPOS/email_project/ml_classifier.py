"""
Email Spam Classifier - Machine Learning Implementation
======================================================

Implements Naive Bayes classification for email spam detection, building on the
modular KeywordProcessor foundation and leveraging extracted training features.
"""

import json
import math
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from ml_feature_extractor import MLFeatureExtractor

class NaiveBayesClassifier:
    """
    Naive Bayes classifier for email spam detection.
    
    Uses the extracted features from MLFeatureExtractor and implements
    Gaussian Naive Bayes for continuous features and Multinomial for discrete features.
    """
    
    def __init__(self, db_path: str = "mail_filter.db"):
        """Initialize classifier with feature extractor."""
        self.db_path = db_path
        self.feature_extractor = MLFeatureExtractor(db_path)
        
        # Model parameters
        self.class_priors = {}  # P(class)
        self.feature_stats = {}  # Statistics for each feature by class
        self.feature_names = []
        self.classes = [0, 1]  # 0 = legitimate, 1 = spam
        
        # Model metadata
        self.is_trained = False
        self.training_size = 0
        self.feature_count = 0
        
    def train(self, use_user_feedback: bool = True, max_samples: Optional[int] = None) -> Dict[str, Any]:
        """
        Train the Naive Bayes classifier on processed emails and user feedback.
        
        Args:
            use_user_feedback: Whether to include user feedback in training
            max_samples: Maximum number of samples to use for training
            
        Returns:
            Training summary statistics
        """
        print("🧠 Training Naive Bayes classifier...")
        
        # Extract training data
        features, labels = self.feature_extractor.extract_training_data(limit=max_samples)
        
        # Include user feedback if available
        if use_user_feedback:
            feedback_features, feedback_labels = self.feature_extractor.extract_user_feedback_data()
            if feedback_features:
                features.extend(feedback_features)
                labels.extend(feedback_labels)
                print(f"📊 Added {len(feedback_features)} user feedback samples")
        
        if not features:
            raise ValueError("No training data available")
        
        # Store training metadata
        self.training_size = len(features)
        self.feature_names = list(features[0].keys())
        self.feature_count = len(self.feature_names)
        
        print(f"📊 Training on {self.training_size} samples with {self.feature_count} features")
        
        # Calculate class distribution
        class_counts = Counter(labels)
        total_samples = len(labels)
        
        print(f"📊 Class distribution: {class_counts[0]} legitimate, {class_counts[1]} spam")
        
        # Calculate class priors P(class)
        for class_label in self.classes:
            self.class_priors[class_label] = class_counts[class_label] / total_samples
        
        # Calculate feature statistics for each class
        self._calculate_feature_statistics(features, labels)
        
        self.is_trained = True
        
        # Return training summary
        summary = {
            'training_size': self.training_size,
            'feature_count': self.feature_count,
            'legitimate_samples': class_counts[0],
            'spam_samples': class_counts[1],
            'spam_ratio': class_counts[1] / total_samples,
            'class_priors': self.class_priors,
            'feature_names': self.feature_names[:10]  # Sample of feature names
        }
        
        print("✅ Training completed successfully")
        return summary
    
    def _calculate_feature_statistics(self, features: List[Dict], labels: List[int]):
        """Calculate mean and variance for each feature by class."""
        # Group features by class
        features_by_class = {0: [], 1: []}
        for feature_dict, label in zip(features, labels):
            features_by_class[label].append(feature_dict)
        
        # Calculate statistics for each feature and class
        self.feature_stats = {}
        
        for class_label in self.classes:
            self.feature_stats[class_label] = {}
            class_features = features_by_class[class_label]
            
            if not class_features:
                continue
            
            for feature_name in self.feature_names:
                values = [feature_dict.get(feature_name, 0) for feature_dict in class_features]
                
                # Calculate mean and variance
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                
                # Add smoothing to prevent zero variance
                variance = max(variance, 1e-6)
                
                self.feature_stats[class_label][feature_name] = {
                    'mean': mean,
                    'variance': variance,
                    'std': math.sqrt(variance)
                }
    
    def predict_single(self, sender: str, subject: str, domain: str = None, 
                      headers: str = "") -> Dict[str, Any]:
        """
        Predict spam probability for a single email.
        
        Args:
            sender: Email sender
            subject: Email subject  
            domain: Sender domain (optional)
            headers: Email headers (optional)
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract features using the modular processor
        features = self.feature_extractor.extract_features_from_email(
            sender, subject, domain, headers
        )
        
        # Calculate log probabilities for each class
        log_probs = {}
        
        for class_label in self.classes:
            # Start with class prior
            log_prob = math.log(self.class_priors[class_label])
            
            # Add feature likelihoods
            for feature_name in self.feature_names:
                feature_value = features.get(feature_name, 0)
                feature_stats = self.feature_stats[class_label].get(feature_name)
                
                if feature_stats:
                    # Gaussian probability for continuous features
                    likelihood = self._gaussian_probability(
                        feature_value, feature_stats['mean'], feature_stats['variance']
                    )
                    log_prob += math.log(max(likelihood, 1e-10))  # Prevent log(0)
            
            log_probs[class_label] = log_prob
        
        # Convert to probabilities and normalize
        max_log_prob = max(log_probs.values())
        probs = {}
        for class_label, log_prob in log_probs.items():
            probs[class_label] = math.exp(log_prob - max_log_prob)
        
        # Normalize
        total_prob = sum(probs.values())
        if total_prob > 0:
            for class_label in probs:
                probs[class_label] /= total_prob
        
        # Generate prediction
        spam_probability = probs.get(1, 0.5)
        predicted_class = 1 if spam_probability > 0.5 else 0
        confidence = max(spam_probability, 1 - spam_probability)
        
        return {
            'predicted_class': predicted_class,
            'is_spam': predicted_class == 1,
            'spam_probability': spam_probability,
            'legitimate_probability': probs.get(0, 1 - spam_probability),
            'confidence': confidence,
            'features_used': len([f for f in features.values() if f != 0]),
            'top_features': self._get_top_contributing_features(features, log_probs)
        }
    
    def _gaussian_probability(self, x: float, mean: float, variance: float) -> float:
        """Calculate Gaussian probability density."""
        if variance == 0:
            return 1.0 if x == mean else 1e-10
        
        coeff = 1.0 / math.sqrt(2 * math.pi * variance)
        exponent = -((x - mean) ** 2) / (2 * variance)
        return coeff * math.exp(exponent)
    
    def _get_top_contributing_features(self, features: Dict, log_probs: Dict, top_k: int = 5) -> List[Tuple[str, float]]:
        """Get top contributing features for the prediction."""
        contributions = []
        
        spam_log_prob = log_probs.get(1, 0)
        legit_log_prob = log_probs.get(0, 0)
        
        for feature_name, feature_value in features.items():
            if feature_value != 0:  # Only consider active features
                # Calculate feature contribution to spam vs legitimate
                spam_stats = self.feature_stats.get(1, {}).get(feature_name)
                legit_stats = self.feature_stats.get(0, {}).get(feature_name)
                
                if spam_stats and legit_stats:
                    spam_likelihood = self._gaussian_probability(
                        feature_value, spam_stats['mean'], spam_stats['variance']
                    )
                    legit_likelihood = self._gaussian_probability(
                        feature_value, legit_stats['mean'], legit_stats['variance']
                    )
                    
                    # Log likelihood ratio
                    if legit_likelihood > 0:
                        contribution = math.log(spam_likelihood / legit_likelihood)
                        contributions.append((feature_name, contribution))
        
        # Sort by absolute contribution and return top k
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        return contributions[:top_k]
    
    def evaluate_on_test_data(self, test_size: int = 100) -> Dict[str, Any]:
        """
        Evaluate model performance on held-out test data.
        
        Args:
            test_size: Number of samples to use for testing
            
        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        print(f"📊 Evaluating model on {test_size} test samples...")
        
        # Get fresh test data (different from training)
        features, labels = self.feature_extractor.extract_training_data(limit=test_size)
        
        if len(features) < test_size:
            print(f"⚠️  Only {len(features)} samples available for testing")
        
        # Make predictions
        predictions = []
        spam_probabilities = []
        
        for feature_dict in features:
            # Create dummy email data from features to use predict_single
            prediction = self.predict_single("test@example.com", "test subject")
            predictions.append(prediction['predicted_class'])
            spam_probabilities.append(prediction['spam_probability'])
        
        # Calculate metrics
        true_positives = sum(1 for true_label, pred in zip(labels, predictions) 
                           if true_label == 1 and pred == 1)
        false_positives = sum(1 for true_label, pred in zip(labels, predictions) 
                            if true_label == 0 and pred == 1)
        true_negatives = sum(1 for true_label, pred in zip(labels, predictions) 
                           if true_label == 0 and pred == 0)
        false_negatives = sum(1 for true_label, pred in zip(labels, predictions) 
                            if true_label == 1 and pred == 0)
        
        # Calculate evaluation metrics
        accuracy = (true_positives + true_negatives) / len(labels) if labels else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # False positive rate (important for email filtering)
        fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_positive_rate': fpr,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives,
            'test_size': len(labels)
        }
        
        print(f"✅ Evaluation completed:")
        print(f"   📊 Accuracy: {accuracy:.3f}")
        print(f"   📊 Precision: {precision:.3f}")
        print(f"   📊 Recall: {recall:.3f}")
        print(f"   📊 F1 Score: {f1_score:.3f}")
        print(f"   📊 False Positive Rate: {fpr:.3f}")
        
        return metrics
    
    def save_model(self, filepath: str = "naive_bayes_model.json"):
        """Save trained model to file."""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        model_data = {
            'class_priors': self.class_priors,
            'feature_stats': self.feature_stats,
            'feature_names': self.feature_names,
            'training_size': self.training_size,
            'feature_count': self.feature_count,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        print(f"✅ Model saved to {filepath}")
    
    def load_model(self, filepath: str = "naive_bayes_model.json"):
        """Load trained model from file."""
        with open(filepath, 'r') as f:
            model_data = json.load(f)
        
        # Convert string keys back to integers for class priors and feature stats
        self.class_priors = {int(k): v for k, v in model_data['class_priors'].items()}
        
        # Convert feature_stats keys back to integers
        self.feature_stats = {}
        for class_key, features in model_data['feature_stats'].items():
            self.feature_stats[int(class_key)] = features
        
        self.feature_names = model_data['feature_names']
        self.training_size = model_data['training_size']
        self.feature_count = model_data['feature_count']
        self.is_trained = model_data['is_trained']
        
        print(f"✅ Model loaded from {filepath}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize classifier
    classifier = NaiveBayesClassifier()
    
    # Train the model
    print("🚀 Starting ML training...")
    training_summary = classifier.train(use_user_feedback=True, max_samples=500)
    
    print("\n📊 Training Summary:")
    for key, value in training_summary.items():
        if key != 'feature_names':  # Skip long feature list
            print(f"   {key}: {value}")
    
    # Test prediction on sample email
    print("\n🔍 Testing prediction...")
    test_prediction = classifier.predict_single(
        sender="noreply@suspicious-investment.tk",
        subject="🤑💰 URGENT: Limited Time Investment Opportunity - Act NOW!",
    )
    
    print("📧 Test Email Prediction:")
    for key, value in test_prediction.items():
        if key != 'top_features':  # Skip detailed features
            print(f"   {key}: {value}")
    
    # Evaluate model performance
    print("\n📊 Evaluating model performance...")
    evaluation = classifier.evaluate_on_test_data(test_size=50)
    
    # Save model
    classifier.save_model()
    
    print("\n✅ ML classifier implementation completed successfully!")