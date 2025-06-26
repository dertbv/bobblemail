"""
Atlas Email API Module - Web interface and API endpoints.

This module contains the web interface components:
- FastAPI web application
- REST API endpoints
- Email action viewer
- Web-based management interface
- API authentication and security
"""

from .app import app

__all__ = [
    "app",
]