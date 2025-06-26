#!/usr/bin/env python3
"""
Random Forest Classifier - Production Integration
Integrates the high-performing Random Forest model into the main email processing pipeline
"""

import sys
import pickle
import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Check for sklearn
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from atlas_email.ml.feature_extractor import MLFeatureExtractor
from atlas_email.ml.naive_bayes import NaiveBayesClassifier


class ProductionRandomForestClassifier:
    """
    Production-ready Random Forest classifier for email spam detection
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from atlas_email.models.database import DB_FILE
            db_path = DB_FILE
        self.db_path = db_path
        self.feature_extractor = MLFeatureExtractor(db_path)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_trained = False
        self.training_metadata = {}
        
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for Random Forest classifier")
        
        print("🌲 Random Forest Classifier initialized")
    
    def train(self, retrain: bool = False) -> Dict[str, Any]:
        """Train the Random Forest model"""
        
        if self.is_trained and not retrain:
            print("✅ Model already trained. Use retrain=True to force retraining.")
            return self.training_metadata
        
        print("🌲 Training Random Forest Classifier...")
        start_time = time.time()
        
        # Extract training data
        print("📊 Extracting training data...")
        try:
            feature_dicts, labels = self.feature_extractor.extract_training_data(limit=1000)
            feedback_features, feedback_labels = self.feature_extractor.extract_user_feedback_data()
            
            if feedback_features:
                feature_dicts.extend(feedback_features)
                labels.extend(feedback_labels)
            
            print(f"✅ Extracted {len(feature_dicts)} training samples")
            
            if len(feature_dicts) < 50:
                raise ValueError("Insufficient training data (need at least 50 samples)")
                
        except Exception as e:
            print(f"❌ Error extracting training data: {e}")
            return {"status": "failed", "error": str(e)}
        
        # Convert to numeric format
        print("🔄 Converting features to numeric format...")
        try:
            X, y, feature_names = self._convert_features_to_matrix(feature_dicts, labels)
            self.feature_names = feature_names
            
            print(f"✅ Feature matrix: {X.shape}")
            print(f"✅ Class distribution: {sum(y)} spam, {len(y)-sum(y)} legitimate")
            
        except Exception as e:
            print(f"❌ Error converting features: {e}")
            return {"status": "failed", "error": str(e)}
        
        # Split data for validation
        if len(X) < 20:
            print("❌ Too few samples for train/test split")
            return {"status": "failed", "error": "Insufficient data for validation"}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        print("📏 Scaling features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        print("🌲 Training Random Forest model...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1  # Use all available cores
        )
        
        try:
            self.model.fit(X_train_scaled, y_train)
            training_time = time.time() - start_time
            
            # Validate model
            y_pred = self.model.predict(X_test_scaled)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            # Store training metadata
            self.training_metadata = {
                "status": "success",
                "training_time": training_time,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "feature_count": len(self.feature_names),
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "timestamp": datetime.now().isoformat()
            }
            
            self.is_trained = True
            
            print(f"✅ Random Forest training completed in {training_time:.2f}s")
            print(f"📊 Performance: Accuracy={accuracy:.3f}, Precision={precision:.3f}, F1={f1:.3f}")
            
            return self.training_metadata
            
        except Exception as e:
            print(f"❌ Random Forest training failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _convert_features_to_matrix(self, feature_dicts: List[Dict], labels: List[str]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Convert feature dictionaries to numeric matrix"""
        
        # Get all feature names
        all_features = set()
        for feature_dict in feature_dicts:
            all_features.update(feature_dict.keys())
        
        feature_names = sorted(list(all_features))
        
        # Convert to matrix
        X = []
        for feature_dict in feature_dicts:
            row = []
            for feature_name in feature_names:
                value = feature_dict.get(feature_name, 0)
                # Convert to numeric
                if isinstance(value, bool):
                    row.append(1 if value else 0)
                elif isinstance(value, (int, float)):
                    row.append(float(value))
                else:
                    row.append(0)  # Default for non-numeric
            X.append(row)
        
        # Convert labels to numeric (spam=1, legitimate=0)
        y = []
        for label in labels:
            if isinstance(label, str):
                y.append(1 if label.lower() in ['spam', 'deleted'] else 0)
            else:
                y.append(int(label))  # Assume already numeric
        
        return np.array(X), np.array(y), feature_names
    
    def predict(self, sender: str, subject: str, headers: str = "", domain: str = None) -> Dict[str, Any]:
        """Make spam prediction using Random Forest"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        start_time = time.time()
        
        try:
            # Extract features for this email
            features = self.feature_extractor.extract_features_from_email(
                sender, subject, domain, headers
            )
            
            # Convert to matrix format
            feature_vector = []
            for feature_name in self.feature_names:
                value = features.get(feature_name, 0)
                if isinstance(value, bool):
                    feature_vector.append(1 if value else 0)
                elif isinstance(value, (int, float)):
                    feature_vector.append(float(value))
                else:
                    feature_vector.append(0)
            
            # Scale features
            X = np.array(feature_vector).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Get feature importance for this prediction
            feature_importance = self._get_top_features(feature_vector)
            
            prediction_time = time.time() - start_time
            
            return {
                "is_spam": bool(prediction),
                "predicted_class": int(prediction),
                "spam_probability": float(probabilities[1]) if len(probabilities) > 1 else 0.5,
                "legitimate_probability": float(probabilities[0]) if len(probabilities) > 0 else 0.5,
                "confidence": float(max(probabilities)),
                "prediction_time": prediction_time,
                "features_used": len([f for f in feature_vector if f != 0]),
                "top_features": feature_importance,
                "model": "RandomForest"
            }
            
        except Exception as e:
            return {
                "error": f"Prediction failed: {e}",
                "is_spam": False,
                "confidence": 0.0,
                "model": "RandomForest"
            }
    
    def _get_top_features(self, feature_vector: List[float], top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top contributing features for this prediction"""
        try:
            if not self.model or not self.feature_names:
                return []
            
            # Get feature importances from the trained model
            importances = self.model.feature_importances_
            
            # Combine with actual feature values
            feature_contributions = []
            for i, (importance, value) in enumerate(zip(importances, feature_vector)):
                if value != 0 and importance > 0.001:  # Only non-zero features with some importance
                    feature_contributions.append((self.feature_names[i], importance * abs(value)))
            
            # Sort by contribution and return top N
            feature_contributions.sort(key=lambda x: x[1], reverse=True)
            return feature_contributions[:top_n]
            
        except Exception:
            return []
    
    def save_model(self, filepath: str = "random_forest_model.pkl"):
        """Save the trained model to disk"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'training_metadata': self.training_metadata
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"✅ Random Forest model saved to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str = "random_forest_model.pkl") -> bool:
        """Load a trained model from disk"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.training_metadata = model_data.get('training_metadata', {})
            self.is_trained = True
            
            print(f"✅ Random Forest model loaded from {filepath}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Model file {filepath} not found")
            return False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current model performance metrics"""
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        return self.training_metadata.copy()


# Integration function for hybrid classifier
def integrate_random_forest_with_hybrid():
    """Integration function to test Random Forest with existing hybrid system"""
    print("🔗 INTEGRATING RANDOM FOREST WITH HYBRID SYSTEM")
    print("=" * 55)
    
    # Initialize classifiers
    rf_classifier = ProductionRandomForestClassifier()
    
    # Train Random Forest
    print("1. Training Random Forest...")
    training_result = rf_classifier.train()
    
    if training_result.get("status") != "success":
        print("❌ Random Forest training failed")
        return False
    
    # Save the model
    print("2. Saving Random Forest model...")
    rf_classifier.save_model()
    
    # Test predictions
    print("3. Testing Random Forest predictions...")
    test_cases = [
        ("crypto-investment@suspicious.tk", "🚀 URGENT: 1000% Bitcoin Returns!"),
        ("support@amazon.com", "Your order #123456 has shipped"),
        ("noreply@bank.com", "Monthly statement available"),
        ("winner@lottery-scam.tk", "Congratulations! You won $1M!"),
        ("health-offer@spam.com", "Blood sugar miracle cure - FREE trial"),
        ("casino-bonus@gambling.tk", "🎰 $500 casino bonus - claim now!")
    ]
    
    print(f"\n📧 Testing {len(test_cases)} sample emails:")
    print(f"{'Subject':<40} {'RF Prediction':<15} {'Confidence':<12} {'Time':<8}")
    print("-" * 80)
    
    total_time = 0
    correct_predictions = 0
    
    for sender, subject in test_cases:
        try:
            result = rf_classifier.predict(sender, subject)
            
            prediction = "SPAM" if result['is_spam'] else "LEGIT"
            confidence = result['confidence']
            pred_time = result['prediction_time']
            total_time += pred_time
            
            # Simple validation (assuming obvious cases)
            expected_spam = any(word in subject.lower() for word in ['bitcoin', 'returns', 'won', 'casino', 'bonus', 'miracle', 'free trial'])
            actual_spam = result['is_spam']
            if expected_spam == actual_spam:
                correct_predictions += 1
            
            print(f"{subject[:40]:<40} {prediction:<15} {confidence:.3f}       {pred_time*1000:.1f}ms")
            
        except Exception as e:
            print(f"{subject[:40]:<40} ERROR: {e}")
    
    avg_time = total_time / len(test_cases)
    accuracy = correct_predictions / len(test_cases)
    
    print("-" * 80)
    print(f"📊 Average prediction time: {avg_time*1000:.1f}ms")
    print(f"📊 Simple validation accuracy: {accuracy:.1%}")
    
    print("\n4. Performance Summary:")
    metrics = rf_classifier.get_performance_metrics()
    if "error" not in metrics:
        print(f"   🎯 Training Accuracy: {metrics.get('accuracy', 0):.3f}")
        print(f"   🎯 Precision: {metrics.get('precision', 0):.3f}")
        print(f"   🎯 F1 Score: {metrics.get('f1_score', 0):.3f}")
        print(f"   ⚡ Training Time: {metrics.get('training_time', 0):.2f}s")
        print(f"   📊 Training Samples: {metrics.get('training_samples', 0)}")
    
    print("\n✅ Random Forest integration completed successfully!")
    return True


if __name__ == "__main__":
    success = integrate_random_forest_with_hybrid()