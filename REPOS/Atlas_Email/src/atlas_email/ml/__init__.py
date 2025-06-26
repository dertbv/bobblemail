"""
Atlas Email ML Module - Machine Learning components for spam detection.

This module contains the advanced machine learning pipeline:
- Ensemble hybrid classifier (95.6% accuracy)
- Naive Bayes classifier
- Random Forest classifier  
- Feature extraction and analytics
- ML model training and evaluation
"""

from .ensemble_classifier import EnsembleHybridClassifier
from .naive_bayes import NaiveBayesClassifier
from .feature_extractor import MLFeatureExtractor
from .random_forest import RandomForestClassifier

__all__ = [
    "EnsembleHybridClassifier",
    "NaiveBayesClassifier",
    "MLFeatureExtractor", 
    "RandomForestClassifier",
]