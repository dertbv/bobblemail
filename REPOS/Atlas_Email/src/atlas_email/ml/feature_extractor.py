"""
ML Feature Extraction Pipeline
==============================

Leverages the existing modular KeywordProcessor to extract features for machine learning
from email data, building on the stable foundation while preparing for ML integration.
"""

import re
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from atlas_email.filters.keyword_processor import KeywordProcessor
from atlas_email.core.spam_classifier import (
    check_all_keywords, is_legitimate_company_domain, detect_provider_from_sender
)
try:
    import tldextract
except ImportError:
    tldextract = None

class MLFeatureExtractor:
    """
    Extracts machine learning features from email data using the modular KeywordProcessor
    as the foundation, combining rule-based analysis with ML-ready feature engineering.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from atlas_email.models.database import DB_FILE
            db_path = DB_FILE
        """Initialize with database connection and keyword processor."""
        self.db_path = db_path
        self.keyword_processor = KeywordProcessor()
        
        # Feature categories for organized extraction
        self.feature_categories = [
            'domain_features', 'content_features', 'spam_indicators', 
            'structural_features', 'provider_features', 'emoji_features'
        ]
    
    def extract_training_data(self, limit: Optional[int] = None) -> Tuple[List[Dict], List[str]]:
        """
        Extract training data from processed emails and user feedback.
        
        Args:
            limit: Optional limit on number of records to extract
            
        Returns:
            Tuple of (feature_dicts, labels)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Query processed emails with labels
        query = """
            SELECT 
                sender_email, sender_domain, subject, category, action,
                confidence_score, ml_validation_method, reason
            FROM processed_emails_bulletproof 
            WHERE category IS NOT NULL AND action IS NOT NULL
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        # Extract features and labels
        features = []
        labels = []
        
        for row in rows:
            # Extract features using modular processor
            feature_dict = self.extract_features_from_email(
                sender=row['sender_email'],
                subject=row['subject'], 
                domain=row['sender_domain']
            )
            
            # Add metadata features
            feature_dict['confidence_score'] = row['confidence_score'] or 0.0
            feature_dict['has_confidence'] = 1 if row['confidence_score'] else 0
            
            features.append(feature_dict)
            
            # Create binary labels: DELETED = 1 (spam), PRESERVED = 0 (not spam)
            labels.append(1 if row['action'] == 'DELETED' else 0)
        
        conn.close()
        return features, labels
    
    def extract_user_feedback_data(self) -> Tuple[List[Dict], List[str]]:
        """
        Extract training data from user feedback for supervised learning.
        
        Returns:
            Tuple of (feature_dicts, corrected_labels)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT 
                sender, subject, original_classification, 
                feedback_type, confidence_rating, user_classification
            FROM user_feedback 
            WHERE processed = FALSE
        """
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        features = []
        labels = []
        
        for row in rows:
            # Extract features
            feature_dict = self.extract_features_from_email(
                sender=row['sender'],
                subject=row['subject']
            )
            
            # Add feedback-specific features
            feature_dict['original_confidence'] = row['confidence_rating'] or 0
            feature_dict['feedback_type'] = self._encode_feedback_type(row['feedback_type'])
            
            features.append(feature_dict)
            
            # Create labels based on user feedback
            # 'correct' = keep original classification
            # 'incorrect' = reverse classification  
            # 'false_positive' = definitely not spam (0)
            if row['feedback_type'] == 'false_positive':
                labels.append(0)  # Not spam
            elif row['feedback_type'] == 'correct':
                # Keep original action (spam detection was correct)
                labels.append(1)  # Assume original was spam if user said correct
            else:  # 'incorrect'
                # Reverse the original classification
                labels.append(0)  # User said it was wrong, so probably not spam
        
        conn.close()
        return features, labels
    
    def extract_features_from_email(self, sender: str, subject: str, 
                                   domain: str = None, headers: str = "") -> Dict[str, Any]:
        """
        Extract comprehensive ML features from a single email using modular processor.
        
        Args:
            sender: Email sender
            subject: Email subject
            domain: Sender domain (optional, will extract if not provided)
            headers: Email headers (optional)
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Basic text preparation
        subject_str = str(subject) if subject else ""
        sender_str = str(sender) if sender else ""
        headers_str = str(headers) if headers else ""
        all_text = f"{subject_str} {headers_str}".lower()
        
        # 1. DOMAIN FEATURES (using modular processor)
        if not domain:
            domain, sender_provider = self.keyword_processor.extract_domain_info(sender_str)
        else:
            sender_provider = detect_provider_from_sender(sender_str)
            
        features.update(self._extract_domain_features(domain, sender_provider, sender_str))
        
        # 2. CONTENT FEATURES (using modular processor)
        features.update(self._extract_content_features(subject_str, all_text))
        
        # 3. SPAM INDICATORS (using modular processor)
        features.update(self._extract_spam_indicators(all_text, domain, sender_provider))
        
        # 4. STRUCTURAL FEATURES
        features.update(self._extract_structural_features(subject_str, sender_str))
        
        # 5. PROVIDER FEATURES
        features.update(self._extract_provider_features(sender_provider))
        
        # 6. EMOJI FEATURES (using modular processor)
        features.update(self._extract_emoji_features(subject_str, all_text))
        
        return features
    
    def _extract_domain_features(self, domain: str, sender_provider: str, sender: str) -> Dict[str, Any]:
        """Extract domain-related features using modular processor methods."""
        features = {}
        
        # Use modular processor for domain analysis
        features['suspicious_domain'] = int(self.keyword_processor.is_suspicious_domain(domain, sender_provider))
        features['legitimate_domain'] = int(is_legitimate_company_domain(domain))
        
        # Domain structure features
        if domain:
            domain_parts = domain.split('.')
            features['domain_length'] = len(domain)
            features['domain_parts_count'] = len(domain_parts)
            features['domain_has_numbers'] = int(any(char.isdigit() for char in domain))
            features['domain_main_length'] = len(domain_parts[0]) if domain_parts else 0
            
            # TLD analysis
            if tldextract:
                extracted = tldextract.extract(domain)
                features['tld_length'] = len(extracted.suffix) if extracted.suffix else 0
                features['has_subdomain'] = int(bool(extracted.subdomain))
            else:
                # Fallback TLD analysis
                features['tld_length'] = len(domain.split('.')[-1]) if '.' in domain else 0
                features['has_subdomain'] = int(domain.count('.') > 1)
            
            # Suspicious TLD check
            features['suspicious_tld'] = int(domain.endswith(tuple(self.keyword_processor.SUSPICIOUS_TLDS)))
        else:
            # Default values for missing domain
            for key in ['domain_length', 'domain_parts_count', 'domain_has_numbers', 
                       'domain_main_length', 'tld_length', 'has_subdomain', 'suspicious_tld']:
                features[key] = 0
        
        # Provider reputation score
        provider_scores = {
            'gmail': 0.95, 'icloud': 0.95, 'outlook': 0.90, 
            'yahoo': 0.75, 'aol': 0.70, 'unknown': 0.20
        }
        features['provider_reputation'] = provider_scores.get(sender_provider, 0.20)
        
        return features
    
    def _extract_content_features(self, subject: str, all_text: str) -> Dict[str, Any]:
        """Extract content-related features using modular processor methods."""
        features = {}
        
        # Text length features
        features['subject_length'] = len(subject)
        features['text_length'] = len(all_text)
        features['text_word_count'] = len(all_text.split())
        
        # Character analysis
        features['subject_has_numbers'] = int(any(char.isdigit() for char in subject))
        features['subject_uppercase_ratio'] = sum(1 for c in subject if c.isupper()) / len(subject) if subject else 0
        features['subject_special_chars'] = sum(1 for c in subject if not c.isalnum() and not c.isspace())
        
        # Spam indicators from text
        features['has_money_symbols'] = int(any(symbol in all_text for symbol in ['$', '€', '£', '¥', '₿']))
        features['has_urgency_words'] = int(any(word in all_text for word in ['urgent', 'immediate', 'now', 'limited time']))
        features['has_promotional_words'] = int(any(word in all_text for word in ['free', 'bonus', 'offer', 'deal', 'sale']))
        
        # Use modular processor for encoded spam detection
        features['encoded_spam'] = int(self.keyword_processor.check_encoded_spam(subject, ""))
        
        return features
    
    def _extract_spam_indicators(self, all_text: str, domain: str, sender_provider: str) -> Dict[str, Any]:
        """Extract spam indicators using modular processor category matching."""
        features = {}
        
        # Use modular processor for category detection
        for category in self.keyword_processor.SPAM_CATEGORIES:
            # Get confidence score for each category
            found_keyword, confidence = check_all_keywords(all_text, category)
            features[f'category_{category.lower().replace(" ", "_")}_confidence'] = confidence
            features[f'category_{category.lower().replace(" ", "_")}_match'] = int(found_keyword is not None)
        
        # Use modular processor for domain pattern detection
        domain_pattern_result = self.keyword_processor.check_domain_patterns(domain, sender_provider)
        features['domain_pattern_match'] = int(domain_pattern_result is not None)
        features['domain_pattern_type'] = self._encode_domain_pattern(domain_pattern_result)
        
        # Use modular processor for brand impersonation detection
        brand_result = self.keyword_processor.check_brand_impersonation("", domain, sender_provider, features.get('suspicious_domain', 0))
        features['brand_impersonation'] = int(brand_result is not None)
        
        return features
    
    def _extract_structural_features(self, subject: str, sender: str) -> Dict[str, Any]:
        """Extract structural email features."""
        features = {}
        
        # Subject line analysis
        features['subject_question_marks'] = subject.count('?')
        features['subject_exclamation_marks'] = subject.count('!')
        features['subject_all_caps_words'] = sum(1 for word in subject.split() if word.isupper() and len(word) > 1)
        
        # Sender analysis
        features['sender_has_noreply'] = int('noreply' in sender.lower() or 'no-reply' in sender.lower())
        features['sender_has_numbers'] = int(any(char.isdigit() for char in sender))
        
        return features
    
    def _extract_provider_features(self, sender_provider: str) -> Dict[str, Any]:
        """Extract email provider-related features."""
        features = {}
        
        # One-hot encoding for provider
        providers = ['gmail', 'icloud', 'outlook', 'yahoo', 'aol', 'unknown']
        for provider in providers:
            features[f'provider_{provider}'] = int(sender_provider == provider)
        
        # Provider tier classification
        tier1_providers = ['gmail', 'icloud', 'outlook']
        tier2_providers = ['yahoo', 'aol']
        
        features['provider_tier_1'] = int(sender_provider in tier1_providers)
        features['provider_tier_2'] = int(sender_provider in tier2_providers)
        features['provider_unknown'] = int(sender_provider == 'unknown')
        
        return features
    
    def _extract_emoji_features(self, subject: str, all_text: str) -> Dict[str, Any]:
        """Extract emoji-related features using modular processor."""
        features = {}
        
        # Use modular processor for emoji analysis
        subject_emoji_count, subject_scam_count = self.keyword_processor.count_emojis(subject)
        total_emoji_count, total_scam_count = self.keyword_processor.count_emojis(all_text)
        
        features['subject_emoji_count'] = subject_emoji_count
        features['subject_scam_emoji_count'] = subject_scam_count
        features['total_emoji_count'] = total_emoji_count
        features['total_scam_emoji_count'] = total_scam_count
        
        # Emoji ratios
        features['emoji_density'] = total_emoji_count / len(all_text) if all_text else 0
        features['scam_emoji_ratio'] = total_scam_count / total_emoji_count if total_emoji_count > 0 else 0
        
        # Use modular processor for emoji spam detection
        emoji_spam_result = self.keyword_processor.check_emoji_spam(subject, all_text)
        features['emoji_spam_detected'] = int(emoji_spam_result is not None)
        
        return features
    
    def _encode_feedback_type(self, feedback_type: str) -> int:
        """Encode feedback type as integer."""
        encoding = {'correct': 1, 'incorrect': 2, 'false_positive': 3}
        return encoding.get(feedback_type, 0)
    
    def _encode_domain_pattern(self, pattern_result: Optional[str]) -> int:
        """Encode domain pattern result as integer."""
        if pattern_result is None:
            return 0
        elif "Investment" in pattern_result:
            return 1
        elif "Gambling" in pattern_result:
            return 2
        else:
            return 3
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names for ML model training."""
        # Create a dummy feature extraction to get all feature names
        dummy_features = self.extract_features_from_email("test@example.com", "test subject")
        return list(dummy_features.keys())
    
    def prepare_training_matrix(self, feature_dicts: List[Dict], feature_names: List[str] = None) -> List[List]:
        """
        Convert feature dictionaries to matrix for ML training.
        
        Args:
            feature_dicts: List of feature dictionaries
            feature_names: Optional list of feature names to include
            
        Returns:
            List of lists representing feature matrix
        """
        if not feature_names:
            feature_names = self.get_feature_names()
        
        # Convert to matrix
        matrix = []
        for feature_dict in feature_dicts:
            row = [feature_dict.get(name, 0) for name in feature_names]
            matrix.append(row)
        
        return matrix


# Example usage and testing
if __name__ == "__main__":
    # Initialize extractor
    extractor = MLFeatureExtractor()
    
    # Extract training data
    print("🔍 Extracting training data from processed emails...")
    features, labels = extractor.extract_training_data(limit=100)
    print(f"✅ Extracted {len(features)} email records")
    
    # Extract user feedback data
    print("🔍 Extracting user feedback data...")
    feedback_features, feedback_labels = extractor.extract_user_feedback_data()
    print(f"✅ Extracted {len(feedback_features)} feedback records")
    
    # Show feature summary
    if features:
        feature_names = list(features[0].keys())
        print(f"📊 Feature count: {len(feature_names)}")
        print(f"📊 Sample features: {feature_names[:10]}")
        
        # Convert to training matrix
        training_matrix = extractor.prepare_training_matrix(features)
        print(f"📊 Training matrix shape: {len(training_matrix)} x {len(training_matrix[0]) if training_matrix else 0}")