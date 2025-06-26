"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_email():
    """Sample email for testing."""
    return {
        "subject": "Test Email",
        "from": "test@example.com",
        "body": "This is a test email body.",
        "date": "2025-06-26 07:00:00"
    }


@pytest.fixture
def spam_email():
    """Sample spam email for testing."""
    return {
        "subject": "🎉 CONGRATULATIONS! You've Won $1,000,000!!!",
        "from": "winner@scam.com",
        "body": "Click here to claim your prize! Act now!!!",
        "date": "2025-06-26 07:00:00"
    }