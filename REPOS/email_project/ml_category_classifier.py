"""
Multi-Class Category Classifier for Email Spam Detection
=======================================================

ML-Enhanced Classification system for category determination using reliable action data
(DELETED/PRESERVED) as ground truth instead of potentially flawed category labels.

Implementation approach:
- Phase 1: Binary classification using DELETED/PRESERVED actions (implemented)
- Phase 2: Category clustering of high-confidence spam emails
- Phase 3: Multi-class category prediction model
- Phase 4: Integration with hybrid classifier
"""

import sqlite3
import json
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict, Counter
from sklearn.cluster import KMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

from ml_feature_extractor import MLFeatureExtractor
from hybrid_classifier import HybridEmailClassifier

class MultiClassCategoryClassifier:
    """
    Advanced ML-Enhanced Category Classifier that combines:
    1. Action-based binary classification (DELETED/PRESERVED as ground truth)
    2. Content clustering for category discovery 
    3. Multi-class category prediction using 73-feature pipeline
    4. Integration with existing hybrid classification system
    5. User feedback integration for category corrections
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from database import DB_FILE
            db_path = DB_FILE
        """Initialize the multi-class category classifier."""
        self.db_path = db_path
        self.feature_extractor = MLFeatureExtractor(db_path)
        
        # Category mappings - consolidated categories for better classification
        self.consolidated_categories = {
            'Financial & Investment': ['Financial & Investment Spam', 'Encoded Financial & Investment Spam', 'Business Opportunity Spam'],
            'Health & Medical': ['Health & Medical Spam', 'Encoded Pharmaceutical Spam'],
            'Adult & Dating': ['Adult & Dating Spam', 'Encoded Adult Content Spam', 'Encoded Social/Dating Spam'],
            'Legal & Compensation': ['Legal & Compensation Scams'],
            'Payment Scam': ['Payment Scam', 'Encoded Payment Scam'],
            'Phishing': ['Phishing', 'Encoded Phishing'],
            'Gambling': ['Gambling Spam', 'Encoded Gambling Spam'],
            'Brand Impersonation': ['Brand Impersonation', 'Encoded Brand Impersonation'],
            'Marketing & Promotional': ['Promotional Email', 'Encoded Marketing Spam'],
            'Real Estate': ['Real Estate Spam'],
            'Generic Spam': ['Encoded Spam', 'User Keyword'],
            'Unknown': []  # Fallback for unclassified
        }
        
        # Reverse mapping for quick lookup
        self.category_to_consolidated = {}
        for consolidated, original_list in self.consolidated_categories.items():
            for original in original_list:
                self.category_to_consolidated[original] = consolidated
        
        # Model components
        self.binary_classifier = None  # For DELETED/PRESERVED classification
        self.category_classifier = None  # For multi-class category prediction
        self.tfidf_vectorizer = None  # For text feature extraction
        self.label_encoder = None  # For category encoding
        self.feature_scaler = None  # For feature scaling
        
        # Model metadata
        self.is_trained = False
        self.training_stats = {}
        self.feature_names = []
        
        # Clustering for category discovery
        self.category_clusters = {}
        self.cluster_centers = {}
        
        # Try to load existing model state
        self._load_model_if_exists()
        
    def extract_action_based_training_data(self, min_samples_per_category: int = 10) -> Tuple[List[Dict], List[str], List[str]]:
        """
        Extract training data using ACTION field as reliable ground truth.
        
        Args:
            min_samples_per_category: Minimum samples required per category
            
        Returns:
            Tuple of (feature_dicts, actions, categories)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Query all emails with reliable action labels
        query = """
            SELECT 
                sender_email, sender_domain, subject, category, action,
                confidence_score, ml_validation_method, reason, raw_data
            FROM processed_emails_bulletproof 
            WHERE action IN ('DELETED', 'PRESERVED') 
                AND category IS NOT NULL 
                AND category != ''
            ORDER BY timestamp DESC
        """
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        print(f"📊 Found {len(rows)} emails with action labels")
        
        # Extract features and labels
        features = []
        actions = []
        categories = []
        
        # Track category distribution
        category_counts = Counter()
        
        for row in rows:
            # Extract comprehensive features
            feature_dict = self.feature_extractor.extract_features_from_email(
                sender=row['sender_email'],
                subject=row['subject'], 
                domain=row['sender_domain'],
                headers=row['raw_data'] or ""  # Use raw_data as headers fallback
            )
            
            # Add metadata features
            feature_dict['confidence_score'] = row['confidence_score'] or 0.0
            feature_dict['has_confidence'] = 1 if row['confidence_score'] else 0
            
            # Consolidate category
            original_category = row['category']
            consolidated_category = self.category_to_consolidated.get(original_category, 'Unknown')
            
            # Only include if we have enough samples for this category
            category_counts[consolidated_category] += 1
            
            features.append(feature_dict)
            actions.append(row['action'])
            categories.append(consolidated_category)
        
        # Filter out categories with too few samples
        filtered_features = []
        filtered_actions = []
        filtered_categories = []
        
        valid_categories = {cat for cat, count in category_counts.items() if count >= min_samples_per_category}
        print(f"📊 Valid categories (>={min_samples_per_category} samples): {len(valid_categories)}")
        
        for feature_dict, action, category in zip(features, actions, categories):
            if category in valid_categories:
                filtered_features.append(feature_dict)
                filtered_actions.append(action)
                filtered_categories.append(category)
        
        conn.close()
        
        # Print category distribution
        final_category_counts = Counter(filtered_categories)
        print("📊 Final category distribution:")
        for category, count in final_category_counts.most_common():
            print(f"   {category}: {count}")
        
        return filtered_features, filtered_actions, filtered_categories
    
    def perform_category_clustering(self, features: List[Dict], categories: List[str], 
                                  actions: List[str]) -> Dict[str, Any]:
        """
        Perform clustering analysis to discover category boundaries in DELETED emails.
        
        Args:
            features: Feature dictionaries
            categories: Category labels
            actions: Action labels (DELETED/PRESERVED)
            
        Returns:
            Clustering analysis results
        """
        print("🔍 Performing category clustering analysis...")
        
        # Filter to only DELETED emails (reliable spam labels)
        deleted_indices = [i for i, action in enumerate(actions) if action == 'DELETED']
        deleted_features = [features[i] for i in deleted_indices]
        deleted_categories = [categories[i] for i in deleted_indices]
        
        if len(deleted_features) < 50:
            print("⚠️  Insufficient DELETED emails for clustering analysis")
            return {}
        
        # Convert features to matrix
        feature_matrix = self.feature_extractor.prepare_training_matrix(deleted_features)
        feature_matrix = np.array(feature_matrix)
        
        # Standardize features for clustering
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_matrix)
        
        # Perform clustering with different algorithms
        clustering_results = {}
        
        # K-Means clustering (assuming we know approximate number of categories)
        n_categories = len(set(deleted_categories))
        kmeans = KMeans(n_clusters=n_categories, random_state=42, n_init=10)
        kmeans_labels = kmeans.fit_predict(scaled_features)
        
        # DBSCAN for density-based clustering
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        dbscan_labels = dbscan.fit_predict(scaled_features)
        
        # Analyze cluster-category alignment
        kmeans_purity = self._calculate_cluster_purity(kmeans_labels, deleted_categories)
        dbscan_purity = self._calculate_cluster_purity(dbscan_labels, deleted_categories)
        
        clustering_results = {
            'kmeans_clusters': len(set(kmeans_labels)),
            'kmeans_purity': kmeans_purity,
            'dbscan_clusters': len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0),
            'dbscan_noise_points': list(dbscan_labels).count(-1),
            'dbscan_purity': dbscan_purity,
            'ground_truth_categories': n_categories,
            'deleted_sample_count': len(deleted_features)
        }
        
        # Store cluster centers for later use
        self.cluster_centers = {
            'kmeans': kmeans.cluster_centers_,
            'scaler': scaler
        }
        
        print(f"✅ Clustering analysis completed:")
        print(f"   K-Means: {clustering_results['kmeans_clusters']} clusters, purity: {kmeans_purity:.3f}")
        print(f"   DBSCAN: {clustering_results['dbscan_clusters']} clusters, purity: {dbscan_purity:.3f}")
        
        return clustering_results
    
    def _calculate_cluster_purity(self, cluster_labels: List[int], true_categories: List[str]) -> float:
        """Calculate purity score for clustering results."""
        if len(cluster_labels) != len(true_categories):
            return 0.0
        
        cluster_category_map = defaultdict(lambda: defaultdict(int))
        
        # Map clusters to categories
        for cluster_id, category in zip(cluster_labels, true_categories):
            if cluster_id != -1:  # Ignore noise points in DBSCAN
                cluster_category_map[cluster_id][category] += 1
        
        # Calculate purity
        total_correct = 0
        total_points = sum(1 for label in cluster_labels if label != -1)
        
        for cluster_id, category_counts in cluster_category_map.items():
            # Most common category in this cluster
            most_common_count = max(category_counts.values()) if category_counts else 0
            total_correct += most_common_count
        
        return total_correct / total_points if total_points > 0 else 0.0
    
    def train_binary_classifier(self, features: List[Dict], actions: List[str]) -> Dict[str, Any]:
        """
        Train binary classifier for DELETED/PRESERVED prediction.
        
        Args:
            features: Feature dictionaries
            actions: Action labels
            
        Returns:
            Training results
        """
        print("🧠 Training binary classifier (DELETED/PRESERVED)...")
        
        # Store consistent feature names from training data
        self.feature_names = sorted(list(features[0].keys())) if features else []
        
        # Convert features to matrix using consistent feature names
        feature_matrix = self.feature_extractor.prepare_training_matrix(features, self.feature_names)
        
        # Convert to numpy arrays
        X = np.array(feature_matrix)
        y = np.array([1 if action == 'DELETED' else 0 for action in actions])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scale features
        self.feature_scaler = StandardScaler()
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)
        
        # Train Gaussian Naive Bayes for continuous features
        self.binary_classifier = GaussianNB()
        self.binary_classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_accuracy = self.binary_classifier.score(X_train_scaled, y_train)
        test_accuracy = self.binary_classifier.score(X_test_scaled, y_test)
        
        # Predictions for detailed metrics
        y_pred = self.binary_classifier.predict(X_test_scaled)
        
        # Calculate detailed metrics
        from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
        auc_score = roc_auc_score(y_test, self.binary_classifier.predict_proba(X_test_scaled)[:, 1])
        
        binary_results = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc_score': auc_score,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': len(self.feature_names)
        }
        
        print(f"✅ Binary classifier trained:")
        print(f"   Accuracy: {test_accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall: {recall:.3f}")
        print(f"   F1-Score: {f1:.3f}")
        
        return binary_results
    
    def train_category_classifier(self, features: List[Dict], categories: List[str], 
                                actions: List[str]) -> Dict[str, Any]:
        """
        Train multi-class category classifier on DELETED emails only.
        
        Args:
            features: Feature dictionaries
            categories: Category labels
            actions: Action labels
            
        Returns:
            Training results
        """
        print("🧠 Training multi-class category classifier...")
        
        # Filter to only DELETED emails (reliable spam labels)
        deleted_indices = [i for i, action in enumerate(actions) if action == 'DELETED']
        deleted_features = [features[i] for i in deleted_indices]
        deleted_categories = [categories[i] for i in deleted_indices]
        
        if len(deleted_features) < 50:
            raise ValueError("Insufficient DELETED emails for category classification")
        
        # Convert features to matrix using consistent feature names
        feature_matrix = self.feature_extractor.prepare_training_matrix(deleted_features, self.feature_names)
        
        # Encode categories
        self.label_encoder = LabelEncoder()
        encoded_categories = self.label_encoder.fit_transform(deleted_categories)
        
        # Convert to numpy arrays
        X = np.array(feature_matrix)
        y = encoded_categories
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Use the same scaler as binary classifier
        X_train_scaled = self.feature_scaler.transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)
        
        # Train Gaussian Naive Bayes for multi-class
        self.category_classifier = GaussianNB()
        self.category_classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_accuracy = self.category_classifier.score(X_train_scaled, y_train)
        test_accuracy = self.category_classifier.score(X_test_scaled, y_test)
        
        # Predictions for detailed analysis
        y_pred = self.category_classifier.predict(X_test_scaled)
        
        # Generate classification report
        category_names = self.label_encoder.classes_
        classification_rep = classification_report(y_test, y_pred, target_names=category_names, output_dict=True)
        
        category_results = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'category_count': len(category_names),
            'categories': list(category_names),
            'macro_precision': classification_rep['macro avg']['precision'],
            'macro_recall': classification_rep['macro avg']['recall'],
            'macro_f1': classification_rep['macro avg']['f1-score'],
            'weighted_f1': classification_rep['weighted avg']['f1-score']
        }
        
        print(f"✅ Category classifier trained:")
        print(f"   Accuracy: {test_accuracy:.3f}")
        print(f"   Categories: {len(category_names)}")
        print(f"   Macro F1: {classification_rep['macro avg']['f1-score']:.3f}")
        
        return category_results
    
    def train_complete_system(self, min_samples_per_category: int = 10) -> Dict[str, Any]:
        """
        Train the complete multi-class category classification system.
        
        Args:
            min_samples_per_category: Minimum samples required per category
            
        Returns:
            Complete training results
        """
        print("🚀 Training complete ML-Enhanced Category Classification system...")
        
        # Phase 1: Extract action-based training data
        features, actions, categories = self.extract_action_based_training_data(min_samples_per_category)
        
        if len(features) < 100:
            raise ValueError("Insufficient training data for multi-class classification")
        
        # Phase 2: Perform category clustering analysis
        clustering_results = self.perform_category_clustering(features, categories, actions)
        
        # Phase 3: Train binary classifier (DELETED/PRESERVED)
        binary_results = self.train_binary_classifier(features, actions)
        
        # Phase 4: Train category classifier (multi-class on DELETED emails)
        category_results = self.train_category_classifier(features, categories, actions)
        
        # Combine all results
        self.training_stats = {
            'total_samples': len(features),
            'deleted_samples': sum(1 for action in actions if action == 'DELETED'),
            'preserved_samples': sum(1 for action in actions if action == 'PRESERVED'),
            'binary_classifier': binary_results,
            'category_classifier': category_results,
            'clustering_analysis': clustering_results,
            'feature_count': len(self.feature_names),
            'consolidated_categories': list(self.consolidated_categories.keys())
        }
        
        self.is_trained = True
        
        print("✅ Complete system training finished:")
        print(f"   Total samples: {len(features)}")
        print(f"   Binary accuracy: {binary_results['test_accuracy']:.3f}")
        print(f"   Category accuracy: {category_results['test_accuracy']:.3f}")
        print(f"   Categories: {category_results['category_count']}")
        
        return self.training_stats
    
    def predict_email_category(self, sender: str, subject: str, domain: str = None, 
                             headers: str = "") -> Dict[str, Any]:
        """
        Predict category for a single email with confidence scores and alternatives.
        
        Args:
            sender: Email sender
            subject: Email subject
            domain: Sender domain (optional)
            headers: Email headers (optional)
            
        Returns:
            Prediction results with confidence scores and alternatives
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Check if actual models are loaded (not just metadata)
        if (self.binary_classifier is None or self.feature_scaler is None or 
            self.category_classifier is None):
            raise ValueError("Model components not loaded - metadata only. Retraining required.")
        
        # Extract features
        features = self.feature_extractor.extract_features_from_email(sender, subject, domain, headers)
        
        # Convert to matrix using consistent feature names
        feature_matrix = self.feature_extractor.prepare_training_matrix([features], self.feature_names)
        X = np.array(feature_matrix)
        
        # Ensure consistent feature count
        if X.shape[1] != len(self.feature_names):
            print(f"⚠️  Feature count mismatch: got {X.shape[1]}, expected {len(self.feature_names)}")
            # Pad or truncate to match training feature count
            if X.shape[1] < len(self.feature_names):
                # Pad with zeros
                padding = np.zeros((X.shape[0], len(self.feature_names) - X.shape[1]))
                X = np.hstack([X, padding])
            else:
                # Truncate to match training features
                X = X[:, :len(self.feature_names)]
        
        X_scaled = self.feature_scaler.transform(X)
        
        # Phase 1: Binary prediction (DELETED/PRESERVED)
        spam_probability = self.binary_classifier.predict_proba(X_scaled)[0, 1]
        is_spam = spam_probability > 0.5
        binary_confidence = max(spam_probability, 1 - spam_probability)
        
        # Phase 2: Category prediction (only if predicted as spam)
        category_prediction = None
        category_confidence = 0.0
        alternative_categories = []
        
        if is_spam and spam_probability > 0.6:  # Only predict category for confident spam predictions
            # Get category probabilities
            category_probs = self.category_classifier.predict_proba(X_scaled)[0]
            category_indices = np.argsort(category_probs)[::-1]  # Sort descending
            
            # Get top prediction
            top_category_idx = category_indices[0]
            category_prediction = self.label_encoder.classes_[top_category_idx]
            category_confidence = category_probs[top_category_idx]
            
            # Get top 3 alternatives
            for i in range(min(3, len(category_indices))):
                idx = category_indices[i]
                category_name = self.label_encoder.classes_[idx]
                confidence = category_probs[idx]
                alternative_categories.append({
                    'category': category_name,
                    'confidence': confidence
                })
        
        return {
            'is_spam': is_spam,
            'spam_probability': spam_probability,
            'binary_confidence': binary_confidence,
            'predicted_category': category_prediction or 'Unknown',
            'category_confidence': category_confidence,
            'alternative_categories': alternative_categories,
            'method': 'ml_category_enhanced',
            'requires_high_confidence': spam_probability < 0.6,
            'features_used': len([f for f in features.values() if f != 0])
        }
    
    def integrate_with_hybrid_classifier(self, hybrid_classifier: HybridEmailClassifier) -> 'EnhancedHybridClassifier':
        """
        Create enhanced hybrid classifier that includes category prediction.
        
        Args:
            hybrid_classifier: Existing hybrid classifier
            
        Returns:
            Enhanced hybrid classifier with category capabilities
        """
        if not self.is_trained:
            raise ValueError("Category classifier must be trained before integration")
        
        return EnhancedHybridClassifier(hybrid_classifier, self)
    
    def process_user_feedback(self, sender: str, subject: str, correct_category: str, 
                            original_prediction: str, confidence_rating: int) -> bool:
        """
        Process user feedback for category corrections.
        
        Args:
            sender: Email sender
            subject: Email subject
            correct_category: User-provided correct category
            original_prediction: Original predicted category
            confidence_rating: User confidence in correction (1-5)
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Insert feedback into database
            query = """
                INSERT INTO user_feedback 
                (sender, subject, original_classification, feedback_type, 
                 confidence_rating, user_classification, processed, timestamp)
                VALUES (?, ?, ?, 'category_correction', ?, ?, FALSE, datetime('now'))
            """
            
            conn.execute(query, (sender, subject, original_prediction, confidence_rating, correct_category))
            conn.commit()
            conn.close()
            
            print(f"✅ User feedback recorded: {original_prediction} -> {correct_category}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to record user feedback: {e}")
            return False
    
    def save_model(self, filepath: str = "ml_category_classifier.json"):
        """Save trained model components with actual sklearn models."""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        import pickle
        import os
        
        # Save sklearn models with pickle
        model_files = {}
        
        if self.binary_classifier:
            binary_path = filepath.replace('.json', '_binary.pkl')
            with open(binary_path, 'wb') as f:
                pickle.dump(self.binary_classifier, f)
            model_files['binary_classifier'] = binary_path
            
        if self.feature_scaler:
            scaler_path = filepath.replace('.json', '_scaler.pkl')
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            model_files['feature_scaler'] = scaler_path
            
        if self.category_classifier:
            category_path = filepath.replace('.json', '_category.pkl')
            with open(category_path, 'wb') as f:
                pickle.dump(self.category_classifier, f)
            model_files['category_classifier'] = category_path
            
        if self.label_encoder:
            encoder_path = filepath.replace('.json', '_encoder.pkl')
            with open(encoder_path, 'wb') as f:
                pickle.dump(self.label_encoder, f)
            model_files['label_encoder'] = encoder_path
        
        # Save metadata and model file references
        model_data = {
            'is_trained': self.is_trained,
            'training_stats': self.training_stats,
            'feature_names': self.feature_names,
            'consolidated_categories': self.consolidated_categories,
            'category_to_consolidated': self.category_to_consolidated,
            'label_classes': list(self.label_encoder.classes_) if self.label_encoder else [],
            'model_type': 'GaussianNB',
            'feature_count': len(self.feature_names),
            'model_files': model_files  # References to actual model files
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        print(f"✅ Category classifier models saved: metadata + {len(model_files)} model files")
    
    def _load_model_if_exists(self, filepath: str = "ml_category_classifier.json"):
        """Load model state from saved file if it exists."""
        try:
            import os
            import pickle
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    model_data = json.load(f)
                
                # Load basic state
                self.is_trained = model_data.get('is_trained', False)
                self.training_stats = model_data.get('training_stats', {})
                self.feature_names = model_data.get('feature_names', [])
                
                # Load actual sklearn models if available
                model_files = model_data.get('model_files', {})
                models_loaded = 0
                
                if 'binary_classifier' in model_files and os.path.exists(model_files['binary_classifier']):
                    with open(model_files['binary_classifier'], 'rb') as f:
                        self.binary_classifier = pickle.load(f)
                    models_loaded += 1
                
                if 'feature_scaler' in model_files and os.path.exists(model_files['feature_scaler']):
                    with open(model_files['feature_scaler'], 'rb') as f:
                        self.feature_scaler = pickle.load(f)
                    models_loaded += 1
                
                if 'category_classifier' in model_files and os.path.exists(model_files['category_classifier']):
                    with open(model_files['category_classifier'], 'rb') as f:
                        self.category_classifier = pickle.load(f)
                    models_loaded += 1
                
                if 'label_encoder' in model_files and os.path.exists(model_files['label_encoder']):
                    with open(model_files['label_encoder'], 'rb') as f:
                        self.label_encoder = pickle.load(f)
                    models_loaded += 1
                
                if self.is_trained:
                    if models_loaded > 0:
                        print(f"✅ ML Category Classifier: Loaded {models_loaded} trained models from disk")
                        print(f"   Training samples: {self.training_stats.get('total_samples', 'unknown')}")
                        print(f"   Binary accuracy: {self.training_stats.get('binary_classifier', {}).get('test_accuracy', 0):.3f}")
                    else:
                        print(f"⚠️  ML Category Classifier: Metadata loaded but models missing - retraining needed")
                        self.is_trained = False  # Force retrain if models missing
                else:
                    print(f"⚠️  ML Category Classifier: Model file exists but not marked as trained")
            else:
                print(f"ℹ️  ML Category Classifier: No existing model file found at {filepath}")
                
        except Exception as e:
            print(f"⚠️  Failed to load existing model: {e}")
            self.is_trained = False


class EnhancedHybridClassifier:
    """
    Enhanced Hybrid Classifier that combines the original hybrid classifier
    with multi-class category prediction capabilities.
    """
    
    def __init__(self, hybrid_classifier: HybridEmailClassifier, category_classifier: MultiClassCategoryClassifier):
        """Initialize enhanced hybrid classifier."""
        self.hybrid_classifier = hybrid_classifier
        self.category_classifier = category_classifier
        
    def classify_email_with_category(self, sender: str, subject: str, headers: str = "", 
                                   account_provider: str = "unknown") -> Dict[str, Any]:
        """
        Classify email with both spam detection and category prediction.
        
        Args:
            sender: Email sender
            subject: Email subject
            headers: Email headers
            account_provider: Account provider
            
        Returns:
            Enhanced classification result with category prediction
        """
        # Get original hybrid classification
        hybrid_result = self.hybrid_classifier.classify_email(sender, subject, headers, account_provider)
        
        # Add category prediction if email is classified as spam
        if hybrid_result.get('is_spam', False):
            try:
                category_result = self.category_classifier.predict_email_category(sender, subject, headers=headers)
                
                # Enhance hybrid result with category information
                hybrid_result.update({
                    'predicted_category': category_result['predicted_category'],
                    'category_confidence': category_result['category_confidence'],
                    'alternative_categories': category_result['alternative_categories'],
                    'category_method': 'ml_enhanced',
                    'category_available': True
                })
                
            except Exception as e:
                print(f"⚠️  Category prediction failed: {e}")
                hybrid_result.update({
                    'predicted_category': 'Unknown',
                    'category_confidence': 0.0,
                    'alternative_categories': [],
                    'category_method': 'fallback',
                    'category_available': False
                })
        else:
            # Not spam, no category needed
            hybrid_result.update({
                'predicted_category': 'Legitimate',
                'category_confidence': 1.0,
                'alternative_categories': [],
                'category_method': 'not_spam',
                'category_available': True
            })
        
        return hybrid_result


# Example usage and testing
if __name__ == "__main__":
    # Initialize and train the complete system
    print("🚀 Initializing ML-Enhanced Category Classification System...")
    
    try:
        classifier = MultiClassCategoryClassifier()
        
        # Train the complete system
        print("\n🧠 Training complete system...")
        training_results = classifier.train_complete_system(min_samples_per_category=15)
        
        print("\n📊 Training Results Summary:")
        print(f"   Total samples: {training_results['total_samples']}")
        print(f"   Binary accuracy: {training_results['binary_classifier']['test_accuracy']:.3f}")
        print(f"   Category accuracy: {training_results['category_classifier']['test_accuracy']:.3f}")
        print(f"   Categories available: {training_results['category_classifier']['category_count']}")
        
        # Test predictions
        test_cases = [
            {
                'name': 'Investment Spam',
                'sender': 'noreply@investment-opportunity.tk',
                'subject': '🤑💰 URGENT: Limited Time Investment Opportunity - Act NOW!'
            },
            {
                'name': 'Health Spam', 
                'sender': 'offers@health-deals.com',
                'subject': 'Revolutionary weight loss supplement - FDA approved!'
            },
            {
                'name': 'Dating Spam',
                'sender': 'matches@dating-site.net',
                'subject': 'Hot singles in your area want to meet you tonight!'
            }
        ]
        
        print("\n🔍 Testing Category Predictions:")
        print("=" * 60)
        
        for test_case in test_cases:
            print(f"\n📧 {test_case['name']}:")
            print(f"   From: {test_case['sender']}")
            print(f"   Subject: {test_case['subject']}")
            
            result = classifier.predict_email_category(
                sender=test_case['sender'],
                subject=test_case['subject']
            )
            
            print(f"   🎯 Spam: {result['is_spam']} (confidence: {result['binary_confidence']:.3f})")
            print(f"   📂 Category: {result['predicted_category']} (confidence: {result['category_confidence']:.3f})")
            
            if result['alternative_categories']:
                print("   📋 Alternatives:")
                for alt in result['alternative_categories'][:2]:
                    print(f"      - {alt['category']}: {alt['confidence']:.3f}")
        
        # Save model
        classifier.save_model()
        
        print("\n✅ ML-Enhanced Category Classification system completed successfully!")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()