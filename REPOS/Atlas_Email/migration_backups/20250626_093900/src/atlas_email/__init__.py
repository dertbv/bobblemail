"""Atlas Email - Professional email management system with ML-powered spam filtering."""

__version__ = "0.1.0"
__author__ = "Atlas Engineering"
__email__ = "atlas@example.com"

# Core exports
from .core.spam_classifier import SpamClassifier
from .core.email_processor import EmailProcessor
from .ml.ensemble_classifier import EnsembleHybridClassifier

__all__ = [
    "SpamClassifier",
    "EmailProcessor", 
    "EnsembleHybridClassifier",
]