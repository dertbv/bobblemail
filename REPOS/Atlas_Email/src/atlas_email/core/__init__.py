"""
Atlas Email Core Module - Core email processing and classification functionality.

This module contains the fundamental email processing components:
- Spam classification algorithms
- Email processing and IMAP handling
- Email authentication and validation
- Core business logic for email management
"""

from .spam_classifier import classify_spam_type, classify_spam_type_legacy
from .email_processor import EmailProcessor
from .email_authentication import authenticate_email_headers

__all__ = [
    "classify_spam_type",
    "classify_spam_type_legacy", 
    "EmailProcessor",
    "authenticate_email_headers",
]