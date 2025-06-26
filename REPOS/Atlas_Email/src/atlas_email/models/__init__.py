"""
Atlas Email Models Module - Database models and data management.

This module contains the data layer components:
- Database connection and management
- Logging and analytics
- Email storage models
- Vendor preferences and settings
- Data inspection tools
"""

from .database import db, DB_FILE
from .db_logger import logger, write_log, LogCategory
from .analytics import DatabaseAnalytics

__all__ = [
    "db",
    "DB_FILE",
    "logger",
    "write_log", 
    "LogCategory",
    "DatabaseAnalytics",
]