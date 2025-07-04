"""
Four-Category Email Classification System
=========================================

A streamlined classification system that categorizes emails into 4 main categories:
1. Dangerous - Immediate security/financial risks
2. Commercial Spam - Unsolicited bulk commercial emails  
3. Scams - Deceptive emails seeking money/information
4. Legitimate Marketing - Marketing from legitimate businesses

This classifier addresses the misclassification issue where auto warranty emails
were incorrectly categorized as Adult spam.
"""

import sqlite3
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib

from atlas_email.ml.feature_extractor import MLFeatureExtractor
from atlas_email.models.database import DB_FILE


class FourCategoryClassifier:
    """
    Simplified 4-category email classifier with subcategory tracking.
    """
    
    # Main categories
    DANGEROUS = "Dangerous"
    COMMERCIAL_SPAM = "Commercial Spam"
    SCAMS = "Scams"
    LEGITIMATE_MARKETING = "Legitimate Marketing"
    
    # Subcategory mappings
    SUBCATEGORIES = {
        DANGEROUS: [
            "Phishing attempts",
            "Malware/virus distribution",
            "Account compromise attempts",
            "Fake security alerts",
            "Cryptocurrency scams"
        ],
        COMMERCIAL_SPAM: [
            "Auto warranty & insurance",
            "Health & medical products",
            "Adult & dating services",
            "Gambling promotions",
            "General product marketing"
        ],
        SCAMS: [
            "Advance fee fraud",
            "Lottery & prize scams",
            "Work-from-home schemes",
            "Investment fraud",
            "Romance scams"
        ],
        LEGITIMATE_MARKETING: [
            "Newsletter subscriptions",
            "Promotional emails",
            "Event invitations",
            "Product updates",
            "Sales notifications"
        ]
    }
    
    # Category mapping from old system
    CATEGORY_MAPPING = {
        # Dangerous mappings
        'Phishing': (DANGEROUS, 'Phishing attempts'),
        'Encoded Phishing': (DANGEROUS, 'Phishing attempts'),
        'Brand Impersonation': (DANGEROUS, 'Account compromise attempts'),
        'Encoded Brand Impersonation': (DANGEROUS, 'Account compromise attempts'),
        
        # Commercial Spam mappings
        'Financial & Investment Spam': (COMMERCIAL_SPAM, 'General product marketing'),
        'Health & Medical Spam': (COMMERCIAL_SPAM, 'Health & medical products'),
        'Adult & Dating Spam': (COMMERCIAL_SPAM, 'Adult & dating services'),
        'Gambling Spam': (COMMERCIAL_SPAM, 'Gambling promotions'),
        'Real Estate Spam': (COMMERCIAL_SPAM, 'General product marketing'),
        'Business Opportunity Spam': (COMMERCIAL_SPAM, 'General product marketing'),
        
        # Scams mappings
        'Payment Scam': (SCAMS, 'Advance fee fraud'),
        'Legal & Compensation Scams': (SCAMS, 'Advance fee fraud'),
        'Encoded Payment Scam': (SCAMS, 'Advance fee fraud'),
        
        # Legitimate Marketing mappings
        'Promotional Email': (LEGITIMATE_MARKETING, 'Promotional emails'),
        'Encoded Marketing Spam': (LEGITIMATE_MARKETING, 'Promotional emails'),
    }
    
    def __init__(self, db_path: str = None):
        """Initialize the 4-category classifier."""
        self.db_path = db_path or DB_FILE
        self.feature_extractor = MLFeatureExtractor(self.db_path)
        
        # Models
        self.text_classifier = None
        self.tfidf_vectorizer = None
        self.label_encoder = None
        
        # Training state
        self.is_trained = False
        self.training_stats = {}
        
        # Subcategory patterns
        self.subcategory_patterns = self._load_subcategory_patterns()
        
    def _load_subcategory_patterns(self) -> Dict[str, List[Dict]]:
        """Load subcategory detection patterns."""
        patterns = {
            # Auto warranty patterns (fixing the main issue)
            'Auto warranty & insurance': [
                {'type': 'keyword', 'pattern': r'\b(auto|car|vehicle)\s*(warranty|protection|insurance)\b', 'weight': 0.9},
                {'type': 'keyword', 'pattern': r'\bendurance\s*auto\b', 'weight': 0.95},
                {'type': 'keyword', 'pattern': r'\bwarranty\s*(expir|eligib|discount|save)\b', 'weight': 0.85},
                {'type': 'domain', 'pattern': r'warranty|auto|vehicle|insurance', 'weight': 0.7},
            ],
            
            # Phishing patterns
            'Phishing attempts': [
                {'type': 'keyword', 'pattern': r'\b(verify|confirm|update)\s*(your)?\s*(account|password|identity)\b', 'weight': 0.9},
                {'type': 'keyword', 'pattern': r'\bsuspicious\s*activity\b', 'weight': 0.85},
                {'type': 'keyword', 'pattern': r'\b(click|act)\s*(here|now|immediately)\b', 'weight': 0.7},
                {'type': 'url', 'pattern': r'bit\.ly|tinyurl|short\.link', 'weight': 0.8},
            ],
            
            # Adult & dating patterns
            'Adult & dating services': [
                {'type': 'keyword', 'pattern': r'\b(hot|sexy|singles?|dating|meet)\b', 'weight': 0.8},
                {'type': 'keyword', 'pattern': r'\b(adult|xxx|porn)\b', 'weight': 0.95},
                {'type': 'keyword', 'pattern': r'\bin\s*your\s*area\b', 'weight': 0.7},
            ],
            
            # Health & medical patterns
            'Health & medical products': [
                {'type': 'keyword', 'pattern': r'\b(weight\s*loss|diet|pills?|supplement)\b', 'weight': 0.8},
                {'type': 'keyword', 'pattern': r'\b(viagra|cialis|pharmacy)\b', 'weight': 0.9},
                {'type': 'keyword', 'pattern': r'\bFDA\s*approved\b', 'weight': 0.7},
            ],
        }
        
        return patterns
    
    def detect_subcategory(self, text: str, domain: str = "") -> Tuple[str, float]:
        """
        Detect the most likely subcategory for an email.
        
        Returns:
            Tuple of (subcategory, confidence)
        """
        text_lower = text.lower()
        domain_lower = domain.lower() if domain else ""
        
        subcategory_scores = defaultdict(float)
        
        for subcategory, patterns in self.subcategory_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                weight = pattern_info['weight']
                pattern_type = pattern_info['type']
                
                if pattern_type == 'keyword':
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        subcategory_scores[subcategory] += weight
                elif pattern_type == 'domain' and domain_lower:
                    if re.search(pattern, domain_lower, re.IGNORECASE):
                        subcategory_scores[subcategory] += weight
                elif pattern_type == 'url':
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        subcategory_scores[subcategory] += weight
        
        if not subcategory_scores:
            return "Unknown", 0.0
            
        # Get the highest scoring subcategory
        best_subcategory = max(subcategory_scores.items(), key=lambda x: x[1])
        
        # Normalize confidence to 0-1 range
        confidence = min(best_subcategory[1] / 3.0, 1.0)
        
        return best_subcategory[0], confidence
    
    def map_old_category(self, old_category: str) -> Tuple[str, str]:
        """
        Map old category to new 4-category system.
        
        Returns:
            Tuple of (new_category, subcategory)
        """
        if old_category in self.CATEGORY_MAPPING:
            return self.CATEGORY_MAPPING[old_category]
        
        # Default mapping based on keywords
        old_cat_lower = old_category.lower()
        
        if 'phish' in old_cat_lower or 'security' in old_cat_lower:
            return self.DANGEROUS, 'Phishing attempts'
        elif 'spam' in old_cat_lower or 'commercial' in old_cat_lower:
            return self.COMMERCIAL_SPAM, 'General product marketing'
        elif 'scam' in old_cat_lower or 'fraud' in old_cat_lower:
            return self.SCAMS, 'Advance fee fraud'
        else:
            return self.COMMERCIAL_SPAM, 'General product marketing'
    
    def prepare_training_data(self) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Prepare training data from existing classifications.
        
        Returns:
            Tuple of (texts, categories, subcategories, actions)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT sender_email, sender_domain, subject, category, action
            FROM processed_emails_bulletproof
            WHERE action IN ('DELETED', 'PRESERVED')
            AND category IS NOT NULL
            AND subject IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 10000
        """
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        texts = []
        categories = []
        subcategories = []
        actions = []
        
        # Statistics
        category_counts = Counter()
        
        for row in rows:
            # Combine sender and subject for text classification
            text = f"{row['sender_email']} {row['subject']}"
            
            # Map old category to new system
            new_category, subcategory = self.map_old_category(row['category'])
            
            # For auto warranty misclassifications
            if 'Adult' in row['category'] and row['subject']:
                detected_subcat, confidence = self.detect_subcategory(
                    row['subject'], 
                    row['sender_domain']
                )
                if detected_subcat == 'Auto warranty & insurance' and confidence > 0.7:
                    new_category = self.COMMERCIAL_SPAM
                    subcategory = detected_subcat
            
            texts.append(text)
            categories.append(new_category)
            subcategories.append(subcategory)
            actions.append(row['action'])
            
            category_counts[new_category] += 1
        
        conn.close()
        
        print(f"📊 Prepared {len(texts)} training samples")
        print("Category distribution:")
        for cat, count in category_counts.most_common():
            print(f"  {cat}: {count} ({count/len(texts)*100:.1f}%)")
        
        return texts, categories, subcategories, actions
    
    def train(self) -> Dict[str, Any]:
        """
        Train the 4-category classifier.
        
        Returns:
            Training statistics and metrics
        """
        print("🚀 Training 4-Category Classification System...")
        
        # Prepare training data
        texts, categories, subcategories, actions = self.prepare_training_data()
        
        if len(texts) < 100:
            raise ValueError("Insufficient training data")
        
        # Initialize models
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=2
        )
        
        self.label_encoder = LabelEncoder()
        
        # Transform data
        X = self.tfidf_vectorizer.fit_transform(texts)
        y = self.label_encoder.fit_transform(categories)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train classifier
        self.text_classifier = MultinomialNB(alpha=0.1)
        self.text_classifier.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.text_classifier.score(X_train, y_train)
        test_score = self.text_classifier.score(X_test, y_test)
        
        # Cross-validation
        cv_scores = cross_val_score(self.text_classifier, X, y, cv=5)
        
        # Detailed evaluation
        y_pred = self.text_classifier.predict(X_test)
        class_report = classification_report(
            y_test, y_pred, 
            target_names=self.label_encoder.classes_,
            output_dict=True
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        self.is_trained = True
        self.training_stats = {
            'train_score': train_score,
            'test_score': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'total_samples': len(texts),
            'train_samples': len(X_train.toarray()),
            'test_samples': len(X_test.toarray()),
            'categories': list(self.label_encoder.classes_),
            'classification_report': class_report,
            'confusion_matrix': cm.tolist()
        }
        
        print(f"✅ Training completed!")
        print(f"   Test accuracy: {test_score:.3f}")
        print(f"   Cross-validation: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        
        return self.training_stats
    
    def classify(self, sender: str, subject: str, domain: str = None) -> Dict[str, Any]:
        """
        Classify an email into one of the 4 categories.
        
        Returns:
            Classification result with category, subcategory, and confidence
        """
        if not self.is_trained:
            raise ValueError("Classifier must be trained before use")
        
        # Prepare text
        text = f"{sender} {subject}"
        
        # Transform text
        X = self.tfidf_vectorizer.transform([text])
        
        # Get prediction probabilities
        proba = self.text_classifier.predict_proba(X)[0]
        
        # Get top prediction
        predicted_idx = np.argmax(proba)
        predicted_category = self.label_encoder.inverse_transform([predicted_idx])[0]
        confidence = proba[predicted_idx]
        
        # Detect subcategory
        subcategory, subcat_confidence = self.detect_subcategory(subject, domain or sender.split('@')[-1])
        
        # Get alternative predictions
        sorted_indices = np.argsort(proba)[::-1]
        alternatives = []
        for idx in sorted_indices[:3]:
            cat = self.label_encoder.inverse_transform([idx])[0]
            alternatives.append({
                'category': cat,
                'confidence': proba[idx]
            })
        
        return {
            'category': predicted_category,
            'subcategory': subcategory,
            'confidence': float(confidence),
            'subcategory_confidence': float(subcat_confidence),
            'alternatives': alternatives,
            'is_spam': predicted_category != self.LEGITIMATE_MARKETING,
            'priority': self._get_priority(predicted_category),
            'method': '4-category-v2'
        }
    
    def _get_priority(self, category: str) -> str:
        """Get priority level for a category."""
        priority_map = {
            self.DANGEROUS: 'CRITICAL',
            self.SCAMS: 'HIGH', 
            self.COMMERCIAL_SPAM: 'HIGH',
            self.LEGITIMATE_MARKETING: 'MEDIUM'
        }
        return priority_map.get(category, 'MEDIUM')
    
    def save_model(self, path_prefix: str = None):
        """Save the trained model."""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        if path_prefix is None:
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            path_prefix = project_root / "data" / "models" / "four_category_classifier"
        
        # Save models
        joblib.dump(self.text_classifier, f"{path_prefix}_classifier.pkl")
        joblib.dump(self.tfidf_vectorizer, f"{path_prefix}_vectorizer.pkl")
        joblib.dump(self.label_encoder, f"{path_prefix}_encoder.pkl")
        
        # Save metadata
        metadata = {
            'is_trained': self.is_trained,
            'training_stats': self.training_stats,
            'categories': list(self.label_encoder.classes_) if self.label_encoder else [],
            'subcategory_patterns': list(self.subcategory_patterns.keys()),
            'version': '2.0'
        }
        
        with open(f"{path_prefix}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Model saved to {path_prefix}_*")
    
    def load_model(self, path_prefix: str = None):
        """Load a saved model."""
        if path_prefix is None:
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            path_prefix = project_root / "data" / "models" / "four_category_classifier"
        
        try:
            # Load models
            self.text_classifier = joblib.load(f"{path_prefix}_classifier.pkl")
            self.tfidf_vectorizer = joblib.load(f"{path_prefix}_vectorizer.pkl")
            self.label_encoder = joblib.load(f"{path_prefix}_encoder.pkl")
            
            # Load metadata
            with open(f"{path_prefix}_metadata.json", 'r') as f:
                metadata = json.load(f)
            
            self.is_trained = metadata['is_trained']
            self.training_stats = metadata['training_stats']
            
            print(f"✅ Model loaded from {path_prefix}_*")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise


# Testing and validation
if __name__ == "__main__":
    classifier = FourCategoryClassifier()
    
    # Train the classifier
    stats = classifier.train()
    
    # Test cases focusing on auto warranty issue
    test_cases = [
        {
            'name': 'Auto Warranty (Previously Misclassified)',
            'sender': 'noreply@dertbv.com',
            'subject': "dertbv you're eligible for discounted pricing you could save thousands on auto repair🔔"
        },
        {
            'name': 'Endurance Auto Warranty',
            'sender': 'info@endurance-warranty.net',
            'subject': '🔒 Endurance Auto Warranty: Trusted Protection for Your Vehicle'
        },
        {
            'name': 'Actual Adult Spam',
            'sender': 'hotsingles@dating.com',
            'subject': 'Hot singles in your area want to meet you tonight!'
        },
        {
            'name': 'Phishing Attempt',
            'sender': 'security@amaz0n-verify.com',
            'subject': 'Urgent: Verify your account or it will be suspended'
        },
        {
            'name': 'Legitimate Marketing',
            'sender': 'newsletter@company.com',
            'subject': 'Your monthly product updates and special offers'
        }
    ]
    
    print("\n🔍 Testing Classifications:")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\n📧 {test['name']}:")
        print(f"   From: {test['sender']}")
        print(f"   Subject: {test['subject']}")
        
        result = classifier.classify(test['sender'], test['subject'])
        
        print(f"   📂 Category: {result['category']} (confidence: {result['confidence']:.3f})")
        print(f"   📌 Subcategory: {result['subcategory']} (confidence: {result['subcategory_confidence']:.3f})")
        print(f"   🚨 Priority: {result['priority']}")
        print(f"   🎯 Is Spam: {result['is_spam']}")
    
    # Save the model
    classifier.save_model()
    
    print("\n✅ 4-Category Classifier ready for deployment!")