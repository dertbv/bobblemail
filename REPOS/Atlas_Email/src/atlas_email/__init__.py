"""
Atlas Email - Professional email management system with ML-powered spam filtering.

A comprehensive email processing and spam filtering system that combines:
- Advanced ML ensemble classification (95.6% accuracy)
- IMAP email processing and management
- Provider-aware spam detection
- Real-time classification and filtering
- Professional Python package architecture

Example usage:
    from atlas_email import EnsembleHybridClassifier, EmailProcessor
    
    # Initialize the spam classifier
    classifier = EnsembleHybridClassifier()
    
    # Process emails with spam detection
    processor = EmailProcessor()
    processor.process_account("your_email@gmail.com")
"""

__version__ = "0.1.0"
__author__ = "Atlas Engineering"
__email__ = "atlas@example.com"

# Core spam classification
from .core.spam_classifier import classify_spam_type, classify_spam_type_legacy

# Email processing
from .core.email_processor import EmailProcessor

# Machine Learning components
from .ml.ensemble_classifier import EnsembleHybridClassifier
from .ml.naive_bayes import NaiveBayesClassifier
from .ml.feature_extractor import MLFeatureExtractor

# Keyword and filter processing
from .filters.keyword_processor import KeywordProcessor

# Database models
from .models.database import db

# Utilities
from .utils.domain_validator import DomainValidator

__all__ = [
    # Core functions
    "classify_spam_type",
    "classify_spam_type_legacy",
    
    # Email processing
    "EmailProcessor",
    
    # Machine Learning
    "EnsembleHybridClassifier",
    "NaiveBayesClassifier", 
    "MLFeatureExtractor",
    
    # Filters
    "KeywordProcessor",
    
    # Database
    "db",
    
    # Utilities
    "DomainValidator",
]