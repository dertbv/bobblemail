#!/usr/bin/env python3
"""
ML Model Ensemble Classifier
============================

Combines multiple ML models and keyword matching for superior spam detection:
1. Random Forest Classifier (tree-based ML)
2. Naive Bayes Classifier (probabilistic ML) 
3. Keyword Matching (rule-based patterns)

Uses weighted voting and consensus algorithms to achieve higher accuracy
than any individual model.
"""

import json
import pickle
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Import existing models and components
from ml_feature_extractor import MLFeatureExtractor
from ml_classifier import NaiveBayesClassifier
from spam_classifier import classify_encoded_spam_content, check_all_keywords
from keyword_processor import KeywordProcessor

# Try to import Random Forest
try:
    from random_forest_classifier import ProductionRandomForestClassifier
    RANDOM_FOREST_AVAILABLE = True
except ImportError:
    RANDOM_FOREST_AVAILABLE = False

# Check for sklearn
try:
    from sklearn.ensemble import RandomForestClassifier
    import sklearn
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class MLEnsembleClassifier:
    """
    Advanced ensemble classifier combining multiple spam detection approaches
    """
    
    def __init__(self, config_path="ml_ensemble_config.json"):
        self.config_path = config_path
        self.models = {}
        self.weights = {}
        self.feature_extractor = None
        self.keyword_processor = None
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components
        self.initialize_models()
        
        print("🤖 ML Ensemble Classifier initialized")
        self.print_model_status()
    
    def load_config(self):
        """Load ensemble configuration with defaults"""
        default_config = {
            "model_weights": {
                "random_forest": 0.4,
                "naive_bayes": 0.3,
                "keyword_matching": 0.3
            },
            "confidence_thresholds": {
                "high_confidence": 0.85,
                "medium_confidence": 0.65,
                "low_confidence": 0.45
            },
            "consensus_settings": {
                "require_majority": True,
                "category_agreement_threshold": 0.6,
                "enable_confidence_boost": True
            },
            "model_paths": {
                "random_forest": "random_forest_model.pkl",
                "naive_bayes": "naive_bayes_model.json"
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            print(f"📋 Creating default ensemble config: {self.config_path}")
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def initialize_models(self):
        """Initialize all available models"""
        # 1. Initialize Random Forest
        if SKLEARN_AVAILABLE and RANDOM_FOREST_AVAILABLE:
            try:
                # Use the ProductionRandomForestClassifier wrapper
                self.models["random_forest"] = ProductionRandomForestClassifier()
                # Load the saved model
                self.models["random_forest"].load_model(self.config["model_paths"]["random_forest"])
                self.weights["random_forest"] = self.config["model_weights"]["random_forest"]
                print("✅ Random Forest model loaded")
            except Exception as e:
                print(f"❌ Failed to load Random Forest: {e}")
                self.weights["random_forest"] = 0
        else:
            print("❌ Random Forest unavailable (missing sklearn/model)")
            self.weights["random_forest"] = 0
        
        # 2. Initialize Naive Bayes
        try:
            self.models["naive_bayes"] = NaiveBayesClassifier()
            if hasattr(self.models["naive_bayes"], 'load_model'):
                self.models["naive_bayes"].load_model(self.config["model_paths"]["naive_bayes"])
            self.weights["naive_bayes"] = self.config["model_weights"]["naive_bayes"]
            print("✅ Naive Bayes model loaded")
        except Exception as e:
            print(f"❌ Failed to load Naive Bayes: {e}")
            self.weights["naive_bayes"] = 0
        
        # 3. Initialize Keyword Processor
        try:
            self.keyword_processor = KeywordProcessor()
            self.weights["keyword_matching"] = self.config["model_weights"]["keyword_matching"]
            print("✅ Keyword matching initialized")
        except Exception as e:
            print(f"❌ Failed to initialize keyword matching: {e}")
            self.weights["keyword_matching"] = 0
        
        # 4. Initialize Feature Extractor
        try:
            self.feature_extractor = MLFeatureExtractor()
            print("✅ Feature extractor initialized")
        except Exception as e:
            print(f"❌ Failed to initialize feature extractor: {e}")
        
        # Normalize weights to sum to 1.0
        self.normalize_weights()
    
    def normalize_weights(self):
        """Normalize weights so they sum to 1.0"""
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for model in self.weights:
                self.weights[model] = self.weights[model] / total_weight
        print(f"🔧 Normalized model weights: {self.weights}")
    
    def print_model_status(self):
        """Print status of all models"""
        print("\n📊 Ensemble Model Status:")
        for model_name, weight in self.weights.items():
            status = "✅ Active" if weight > 0 else "❌ Inactive"
            print(f"  {model_name}: {status} (weight: {weight:.2f})")
        print()
    
    def predict_random_forest(self, email_data):
        """Get Random Forest prediction"""
        if "random_forest" not in self.models or not self.feature_extractor:
            return None
        
        try:
            # Use the Random Forest wrapper's predict method
            result = self.models["random_forest"].predict(
                sender=email_data.get("sender", ""),
                subject=email_data.get("subject", ""),
                headers=email_data.get("body", "")
            )
            
            return {
                "confidence": result.get("spam_probability", 0.5),
                "category": "SPAM" if result.get("is_spam", False) else "HAM",
                "raw_result": result
            }
        except Exception as e:
            print(f"❌ Random Forest prediction failed: {e}")
            return None
    
    def predict_naive_bayes(self, email_data):
        """Get Naive Bayes prediction"""
        if "naive_bayes" not in self.models:
            return None
        
        try:
            # Use Naive Bayes classifier
            result = self.models["naive_bayes"].predict_single(
                sender=email_data.get("sender", ""),
                subject=email_data.get("subject", ""),
                headers=email_data.get("body", "")
            )
            
            return {
                "confidence": result.get("confidence", 0.5),
                "category": result.get("classification", "UNKNOWN"),
                "reasoning": result.get("reasoning", [])
            }
        except Exception as e:
            print(f"❌ Naive Bayes prediction failed: {e}")
            return None
    
    def predict_keyword_matching(self, email_data):
        """Get keyword matching prediction"""
        if not self.keyword_processor:
            return None
        
        try:
            subject = email_data.get("subject", "")
            sender = email_data.get("sender", "")
            body = email_data.get("body", "")
            
            # Try encoded spam classification first
            encoded_result = classify_encoded_spam_content(
                headers="", 
                sender=sender, 
                subject=subject
            )
            
            if encoded_result:
                # Categories are now clean from the source function
                return {
                    "confidence": 0.9,  # High confidence for keyword matches
                    "category": encoded_result,
                    "method": "encoded_classification"
                }
            
            # Fallback to keyword processor with protection patterns
            try:
                from keyword_processor import keyword_processor
                # Use full keyword processor which includes protection patterns
                classification_result = keyword_processor.process_keywords(
                    headers or "", sender or "", subject or ""
                )
                
                # Convert result to expected format
                if classification_result == "Not Spam":
                    return {
                        'category': 'Not Spam',
                        'confidence': 0.95,
                        'model_scores': {'ensemble': 0.05},
                        'metadata': {'method': 'keyword_processor_protected'}
                    }
                elif classification_result and classification_result != "Marketing Spam":
                    return {
                        'category': classification_result,
                        'confidence': 0.8,
                        'model_scores': {'ensemble': 0.8},
                        'metadata': {'method': 'keyword_processor'}
                    }
            except Exception as e:
                print(f"Warning: Keyword processor fallback failed: {e}")
            
            # Final fallback to direct keyword checking
            combined_text = f"{subject} {body}".lower()
            
            # Check each category for matches
            spam_categories = [
                'Phishing', 'Brand Impersonation', 'Adult Content Spam',
                'Financial & Investment Spam', 'Gambling Spam', 'Health & Medical Spam',
                'Marketing Spam', 'Payment Scam'
            ]
            
            best_category = None
            best_confidence = 0
            
            for category in spam_categories:
                found_keyword, confidence = check_all_keywords(combined_text, category)
                if found_keyword and confidence > best_confidence:
                    best_category = category
                    best_confidence = confidence
            
            if best_category:
                return {
                    "confidence": best_confidence,
                    "category": best_category,
                    "method": "keyword_matching"
                }
            else:
                return {
                    "confidence": 0.1,  # Low confidence for no matches
                    "category": "HAM",
                    "method": "keyword_matching"
                }
                
        except Exception as e:
            print(f"❌ Keyword matching failed: {e}")
            return None
    
    def ensemble_classify(self, email_data):
        """
        Main ensemble classification method
        Combines all model predictions using weighted voting
        """
        start_time = time.time()
        
        # Get predictions from all models
        predictions = {
            "random_forest": self.predict_random_forest(email_data),
            "naive_bayes": self.predict_naive_bayes(email_data),
            "keyword_matching": self.predict_keyword_matching(email_data)
        }
        
        # Calculate weighted ensemble score
        ensemble_score = 0
        category_votes = {}
        active_models = 0
        
        for model_name, prediction in predictions.items():
            if prediction and self.weights[model_name] > 0:
                active_models += 1
                model_weight = self.weights[model_name]
                
                # Add to ensemble score (convert to binary spam/ham)
                if model_name == "keyword_matching":
                    # Keyword matching returns category names
                    spam_confidence = prediction["confidence"] if prediction["category"] != "HAM" else (1 - prediction["confidence"])
                else:
                    # ML models return direct spam confidence
                    spam_confidence = prediction["confidence"]
                
                ensemble_score += model_weight * spam_confidence
                
                # Collect category votes
                category = prediction["category"]
                if category not in category_votes:
                    category_votes[category] = 0
                category_votes[category] += model_weight
        
        # Determine final classification
        is_spam = ensemble_score > 0.5
        
        # Get consensus category with preference for specific categories
        if category_votes:
            # Prioritize specific spam categories over generic "SPAM"/"HAM"
            specific_categories = {k: v for k, v in category_votes.items() 
                                 if k not in ["SPAM", "HAM", "UNKNOWN"]}
            
            if specific_categories and is_spam:
                # If we have specific categories and this is spam, use the highest-weighted specific category
                final_category = max(specific_categories.items(), key=lambda x: x[1])[0]
            else:
                # Otherwise use the highest-weighted category overall
                final_category = max(category_votes.items(), key=lambda x: x[1])[0]
        else:
            final_category = "SPAM" if is_spam else "HAM"
        
        # Calculate confidence level
        confidence_level = self.get_confidence_level(ensemble_score)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        result = {
            "final_classification": final_category,
            "spam_probability": ensemble_score,
            "confidence_level": confidence_level,
            "is_spam": is_spam,
            "model_predictions": predictions,
            "category_votes": category_votes,
            "active_models": active_models,
            "processing_time_ms": round(processing_time, 2),
            "ensemble_weights": self.weights.copy()
        }
        
        return result
    
    def get_confidence_level(self, score):
        """Convert numeric score to confidence level"""
        thresholds = self.config["confidence_thresholds"]
        
        if score >= thresholds["high_confidence"] or score <= (1 - thresholds["high_confidence"]):
            return "HIGH"
        elif score >= thresholds["medium_confidence"] or score <= (1 - thresholds["medium_confidence"]):
            return "MEDIUM"
        else:
            return "LOW"
    
    def classify_email(self, subject="", sender="", body="", headers=""):
        """
        Convenient interface for email classification
        """
        email_data = {
            "subject": subject,
            "sender": sender,
            "body": body,
            "headers": headers
        }
        
        return self.ensemble_classify(email_data)
    
    def _convert_features_to_array(self, feature_dict):
        """Convert feature dictionary to array format for Random Forest"""
        if not hasattr(self.models["random_forest"], 'feature_names'):
            # If no feature names stored, try to get them from the model
            if hasattr(self.models["random_forest"], 'feature_names_'):
                feature_names = self.models["random_forest"].feature_names_
            else:
                # Fallback: use sorted feature dict keys
                feature_names = sorted(feature_dict.keys())
        else:
            feature_names = self.models["random_forest"].feature_names
        
        # Convert to array in the same order as training
        features_array = []
        for feature_name in feature_names:
            value = feature_dict.get(feature_name, 0)
            # Convert to numeric
            if isinstance(value, bool):
                features_array.append(1 if value else 0)
            elif isinstance(value, (int, float)):
                features_array.append(float(value))
            else:
                features_array.append(0)  # Default for non-numeric
        
        return np.array(features_array)
    
    def get_model_performance_stats(self):
        """Get performance statistics for the ensemble"""
        stats = {
            "active_models": sum(1 for w in self.weights.values() if w > 0),
            "total_models": len(self.weights),
            "model_weights": self.weights.copy(),
            "sklearn_available": SKLEARN_AVAILABLE,
            "random_forest_available": RANDOM_FOREST_AVAILABLE
        }
        return stats


if __name__ == "__main__":
    # Test the ensemble classifier
    print("🧪 Testing ML Ensemble Classifier")
    
    ensemble = MLEnsembleClassifier()
    
    # Test with a known spam email
    test_email = {
        "subject": "URGENT: Claim your $500 Walmart gift card now!",
        "sender": "winner@fake-walmart.tk",
        "body": "Congratulations! You've won a $500 Walmart gift card. Click here to claim immediately!"
    }
    
    result = ensemble.classify_email(**test_email)
    
    print("\n📧 Test Email Classification:")
    print(f"Subject: {test_email['subject']}")
    print(f"Sender: {test_email['sender']}")
    print(f"\n🎯 Ensemble Result:")
    print(f"Classification: {result['final_classification']}")
    print(f"Spam Probability: {result['spam_probability']:.3f}")
    print(f"Confidence Level: {result['confidence_level']}")
    print(f"Processing Time: {result['processing_time_ms']}ms")
    print(f"Active Models: {result['active_models']}")
    
    print("\n📊 Model Performance Stats:")
    stats = ensemble.get_model_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")