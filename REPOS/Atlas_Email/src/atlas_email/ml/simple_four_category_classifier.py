"""
Simple Rule-Based Four-Category Email Classifier
===============================================

A lightweight classifier that doesn't require numpy or sklearn.
Uses keyword matching and pattern recognition to categorize emails.
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class SimpleFourCategoryClassifier:
    """Rule-based 4-category classifier without ML dependencies."""
    
    # Main categories
    DANGEROUS = "Dangerous"
    COMMERCIAL_SPAM = "Commercial Spam"
    SCAMS = "Scams"
    LEGITIMATE_MARKETING = "Legitimate Marketing"
    
    def __init__(self):
        """Initialize the classifier with keyword patterns."""
        self.initialize_patterns()
        
    def initialize_patterns(self):
        """Define keyword patterns for each category."""
        
        # Dangerous patterns (highest priority)
        self.dangerous_patterns = {
            'phishing': [
                r'verify\s+your\s+account',
                r'suspended\s+account',
                r'confirm\s+your\s+identity',
                r'update\s+payment\s+information',
                r'security\s+alert',
                r'unusual\s+activity',
                r'click\s+here\s+immediately'
            ],
            'malware': [
                r'download\s+attachment',
                r'open\s+attached\s+file',
                r'invoice\s+attached',
                r'document\s+scan'
            ],
            'crypto_scam': [
                r'bitcoin\s+investment',
                r'cryptocurrency\s+opportunity',
                r'double\s+your\s+bitcoin'
            ]
        }
        
        # Commercial Spam patterns
        self.commercial_patterns = {
            'auto_warranty': [
                r'auto\s+warranty',
                r'vehicle\s+warranty',
                r'car\s+warranty',
                r'extended\s+warranty',
                r'warranty\s+expir'
            ],
            'health': [
                r'weight\s+loss',
                r'diet\s+pill',
                r'miracle\s+cure',
                r'cbd\s+oil',
                r'testosterone'
            ],
            'adult': [
                r'adult\s+dating',
                r'singles\s+in\s+your\s+area',
                r'hot\s+singles',
                r'adult\s+content'
            ],
            'gambling': [
                r'online\s+casino',
                r'poker\s+bonus',
                r'betting\s+site',
                r'gambling\s+offer'
            ]
        }
        
        # Scam patterns
        self.scam_patterns = {
            'advance_fee': [
                r'nigerian\s+prince',
                r'inheritance\s+fund',
                r'unclaimed\s+money',
                r'beneficiary'
            ],
            'lottery': [
                r'won\s+the\s+lottery',
                r'prize\s+winner',
                r'claim\s+your\s+prize',
                r'congratulations\s+winner'
            ],
            'work_from_home': [
                r'work\s+from\s+home',
                r'make\s+money\s+online',
                r'earn\s+\$\d+\s+per\s+day',
                r'home\s+based\s+job'
            ]
        }
        
        # Legitimate marketing patterns (lowest priority)
        self.legitimate_patterns = {
            'newsletter': [
                r'newsletter',
                r'unsubscribe',
                r'email\s+preferences',
                r'update\s+preferences'
            ],
            'promotion': [
                r'sale\s+ends',
                r'limited\s+time\s+offer',
                r'discount\s+code',
                r'special\s+offer'
            ]
        }
        
    def extract_features(self, subject: str, sender: str, body: str) -> Dict[str, int]:
        """Extract simple features from email."""
        text = f"{subject} {body}".lower()
        
        features = {
            'length': len(text),
            'exclamation_count': text.count('!'),
            'dollar_count': text.count('$'),
            'uppercase_ratio': sum(1 for c in subject + body if c.isupper()) / max(len(subject + body), 1),
            'has_url': 1 if re.search(r'https?://', text) else 0,
            'suspicious_sender': 1 if re.search(r'noreply|no-reply|donotreply', sender.lower()) else 0
        }
        
        return features
        
    def classify(self, subject: str, sender: str, body: str = "") -> Dict[str, any]:
        """
        Classify email into one of four categories.
        
        Returns:
            Dictionary with category, confidence, and subcategory
        """
        text = f"{subject} {body}".lower()
        
        # Score each category
        scores = defaultdict(float)
        matched_patterns = defaultdict(list)
        
        # Check dangerous patterns (highest priority)
        for subcat, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[self.DANGEROUS] += 2.0
                    matched_patterns[self.DANGEROUS].append(subcat)
                    
        # Check scam patterns
        for subcat, patterns in self.scam_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[self.SCAMS] += 1.5
                    matched_patterns[self.SCAMS].append(subcat)
                    
        # Check commercial spam patterns
        for subcat, patterns in self.commercial_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[self.COMMERCIAL_SPAM] += 1.0
                    matched_patterns[self.COMMERCIAL_SPAM].append(subcat)
                    
        # Check legitimate patterns (lowest priority)
        for subcat, patterns in self.legitimate_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[self.LEGITIMATE_MARKETING] += 0.5
                    matched_patterns[self.LEGITIMATE_MARKETING].append(subcat)
                    
        # Extract features for additional scoring
        features = self.extract_features(subject, sender, body)
        
        # Adjust scores based on features
        if features['uppercase_ratio'] > 0.3:
            scores[self.COMMERCIAL_SPAM] += 0.5
        if features['dollar_count'] > 3:
            scores[self.SCAMS] += 0.3
        if features['exclamation_count'] > 5:
            scores[self.COMMERCIAL_SPAM] += 0.3
            
        # Determine category
        if not scores:
            # Default to commercial spam if no patterns match
            category = self.COMMERCIAL_SPAM
            confidence = 0.3
            subcategory = "General spam"
        else:
            # Get highest scoring category
            category = max(scores.items(), key=lambda x: x[1])[0]
            max_score = scores[category]
            
            # Calculate confidence
            if max_score > 3.0:
                confidence = 0.9
            elif max_score > 2.0:
                confidence = 0.7
            elif max_score > 1.0:
                confidence = 0.5
            else:
                confidence = 0.3
                
            # Get most common subcategory
            if matched_patterns[category]:
                subcat_counts = defaultdict(int)
                for subcat in matched_patterns[category]:
                    subcat_counts[subcat] += 1
                subcategory = max(subcat_counts.items(), key=lambda x: x[1])[0]
            else:
                subcategory = "General"
                
        # Special handling for auto warranty emails
        if re.search(r'auto\s+warranty|vehicle\s+warranty|car\s+warranty', text, re.IGNORECASE):
            category = self.COMMERCIAL_SPAM
            subcategory = "Auto warranty & insurance"
            confidence = 0.95
            
        return {
            'category': category,
            'subcategory': subcategory,
            'confidence': confidence,
            'scores': dict(scores),
            'matched_patterns': dict(matched_patterns)
        }
        
    def get_category_stats(self) -> Dict[str, List[str]]:
        """Return the category hierarchy for reference."""
        return {
            self.DANGEROUS: list(self.dangerous_patterns.keys()),
            self.COMMERCIAL_SPAM: list(self.commercial_patterns.keys()),
            self.SCAMS: list(self.scam_patterns.keys()),
            self.LEGITIMATE_MARKETING: list(self.legitimate_patterns.keys())
        }
        
        
def test_classifier():
    """Test the classifier with sample emails."""
    classifier = SimpleFourCategoryClassifier()
    
    test_cases = [
        {
            'subject': 'Your auto warranty is about to expire',
            'sender': 'warranty@autoprotect.com',
            'body': 'Final notice about your vehicle warranty. Act now!',
            'expected': 'Commercial Spam'
        },
        {
            'subject': 'Verify your PayPal account immediately',
            'sender': 'noreply@paypal-secure.com',
            'body': 'Click here to verify your account or it will be suspended.',
            'expected': 'Dangerous'
        },
        {
            'subject': 'You won $1,000,000!',
            'sender': 'lottery@winner.com',
            'body': 'Congratulations! Claim your prize money now.',
            'expected': 'Scams'
        },
        {
            'subject': 'Summer Sale - 20% off everything',
            'sender': 'news@legitimate-store.com',
            'body': 'Shop our summer collection. Unsubscribe at any time.',
            'expected': 'Legitimate Marketing'
        }
    ]
    
    print("🧪 Testing Simple Four Category Classifier")
    print("=" * 60)
    
    for test in test_cases:
        result = classifier.classify(
            test['subject'],
            test['sender'],
            test['body']
        )
        
        status = "✅" if result['category'] == test['expected'] else "❌"
        print(f"\n{status} Subject: {test['subject']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Got: {result['category']} (confidence: {result['confidence']:.2f})")
        print(f"   Subcategory: {result['subcategory']}")
        

if __name__ == "__main__":
    test_classifier()