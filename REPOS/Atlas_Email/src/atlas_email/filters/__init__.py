"""
Atlas Email Filters Module - Email filtering and keyword processing.

This module contains the email filtering components:
- Keyword-based spam detection
- Provider-specific filtering
- Business prefix validation
- Vendor filter management
- Category-based classification
"""

from .keyword_processor import KeywordProcessor
from .unified_manager import UnifiedKeywordManager

__all__ = [
    "KeywordProcessor",
    "UnifiedKeywordManager",
]