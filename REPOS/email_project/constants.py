#!/usr/bin/env python3
"""
Constants and Configuration Values
Central location for all magic numbers, strings, and configuration values
"""

# File paths and configuration
import os

BASE_DIR = os.path.abspath(os.getcwd())
CONFIG_FILE = os.path.join(BASE_DIR, "my_keywords.txt")
LOG_FILE = os.path.join(BASE_DIR, "mail_filter_imap_log.txt")
CREDS_FILE = os.path.join(BASE_DIR, ".mail_filter_creds.json")
ANALYTICS_OUTPUT = os.path.join(BASE_DIR, "mail_filter_analytics_report.txt")
JSON_OUTPUT = os.path.join(BASE_DIR, "mail_filter_analytics_data.json")
ML_SETTINGS_FILE = "ml_settings.json"

# Provider configurations
PROVIDER_CONFIGS = {
    "icloud": {
        "domains": ['icloud.com', 'me.com', 'mac.com'],
        "host": "imap.mail.me.com",
        "port": 993,
        "requires_app_password": True,
        "deletion_strategy": "icloud_special",
        "batch_size": 10,
        "supports_individual_uid": False,
        "emoji": "🍎",
        "reselect_frequency": 3,
        "requires_parentheses": True,
        "requires_immediate_expunge": True,
        "use_uid_expunge": True
    },
    "gmail": {
        "domains": ['gmail.com'],
        "host": "imap.gmail.com",
        "port": 993,
        "requires_app_password": True,
        "deletion_strategy": "standard",
        "batch_size": 50,
        "supports_individual_uid": True,
        "emoji": "📧",
        "reselect_frequency": 10
    },
    "outlook": {
        "domains": ['outlook.com', 'hotmail.com', 'live.com', 'msn.com'],
        "host": "outlook.office365.com",
        "port": 993,
        "requires_app_password": False,
        "deletion_strategy": "standard",
        "batch_size": 30,
        "supports_individual_uid": True,
        "emoji": "🏢",
        "reselect_frequency": 8
    },
    "yahoo": {
        "domains": ['yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.fr', 'yahoo.de'],
        "host": "imap.mail.yahoo.com",
        "port": 993,
        "requires_app_password": True,
        "deletion_strategy": "standard",
        "batch_size": 40,
        "supports_individual_uid": True,
        "emoji": "📮",
        "reselect_frequency": 8
    },
    "aol": {
        "domains": ['aol.com'],
        "host": "imap.aol.com",
        "port": 993,
        "requires_app_password": False,
        "deletion_strategy": "standard",
        "batch_size": 30,
        "supports_individual_uid": True,
        "emoji": "📧",
        "reselect_frequency": 8
    }
}

# Default provider configuration
DEFAULT_PROVIDER_CONFIG = {
    "domains": [],
    "host": "",
    "port": 993,
    "requires_app_password": False,
    "deletion_strategy": "standard",
    "batch_size": 25,
    "supports_individual_uid": True,
    "emoji": "🔧",
    "reselect_frequency": 5
}

# ML Classification defaults
ML_DEFAULT_SETTINGS = {
    'confidence_threshold': 70,
    'entropy_threshold': 3.2,
    'domain_age_threshold': 90,
    'provider_specific': True,
    'enabled_categories': {
        'Financial & Investment Spam': True,
        'Gambling Spam': True,
        'Financial Product Spam': True,
        'Health Scam': True,
        'Payment Scam': True,
        'Phishing': True,
        'Brand Impersonation': True,
        'Marketing Email': False,  # Legitimate promotional content - preserve by default
        'Adult Content Spam': False,
        'Business Opportunity Spam': True,
        'Education/Training Spam': True,
        'Real Estate Spam': True,
        'Legal Settlement Scam': True,
        'Social/Dating Spam': True
    },
    'provider_thresholds': {
        'gmail': 80,
        'icloud': 75,
        'outlook': 70,
        'yahoo': 70,
        'aol': 70,
        'unknown': 50
    },
    'custom_whitelist': [],
    'custom_keyword_whitelist': []
}

# Spam classification constants
MAX_DOMAIN_LENGTH = 15
MAX_DOMAIN_PARTS = 2
SUSPICIOUS_DOMAIN_EXTENSIONS = [".us", ".tk", ".ml", ".ga", ".cf"]
TRUSTED_DOMAIN_KEYWORDS = [
    "gmail", "yahoo", "outlook", "hotmail", "icloud", "me", "mac", 
    "facebook", "temu", "amazon", "apple"
]

# Processing constants
DEFAULT_BATCH_SIZE = 50
MAX_EMAIL_HEADER_LENGTH = 2000
MAX_FILTER_COUNT = 100
MIN_FILTER_LENGTH = 2
MAX_WILDCARD_COUNT = 3

# UI constants
MAIN_MENU_WIDTH = 70
SUBMENU_WIDTH = 50
MAX_EXAMPLES_TO_SHOW = 5

# Timeout and retry constants
DEFAULT_TIMEOUT_SECONDS = 120
MAX_CONNECTION_ATTEMPTS = 3
WHOIS_TIMEOUT_SECONDS = 5
DOMAIN_CACHE_HOURS = 24

# Progress display constants
PROGRESS_UPDATE_INTERVAL = 100
ETA_CALCULATION_MIN_SAMPLES = 10

# Special keys for navigation
ESCAPE_KEYS = ['\x03', '\x1b']  # Ctrl+C, Esc
CONFIRMATION_KEYWORDS = ['yes', 'y']
STRICT_CONFIRMATION_KEYWORD = 'YES'

# Risk level indicators
RISK_LEVELS = {
    'high': "⚠️  (High false positive risk)",
    'medium': "🔶 (Medium risk)",
    'low': "🟢 (Low risk)"
}

# Category risk mappings
HIGH_RISK_CATEGORIES = ['Financial Product Spam', 'Adult Content Spam']
MEDIUM_RISK_CATEGORIES = ['Financial & Investment Spam', 'Health Scam', 'Payment Scam']

# Folder types for processing
TARGET_FOLDER_TYPES = ['bulk', 'spam', 'junk', 'trash', 'deleted']
RISKY_FOLDER_KEYWORDS = ['inbox', 'sent', 'important', 'all mail']

# Unicode emoji ranges for detection
EMOJI_UNICODE_RANGES = [
    "\U0001F600-\U0001F64F",  # emoticons
    "\U0001F300-\U0001F5FF",  # symbols & pictographs
    "\U0001F680-\U0001F6FF",  # transport & map symbols
    "\U0001F1E0-\U0001F1FF",  # flags (iOS)
    "\U00002600-\U000027BF",  # misc symbols
    "\U0001F900-\U0001F9FF",  # supplemental symbols
    "\U0001FA70-\U0001FAFF",  # symbols and pictographs extended-A
]

# Scam emoji indicators
SCAM_EMOJIS = [
    "💲", "💰", "💵", "💴", "💶", "💷", "🤑", "💳", "💎", "🎁", "🎉", "🎊",
    "🔥", "⚡", "✨", "🌟", "⭐", "🏆", "🎯", "🚀", "📈", "📊", "👑", "💯",
    "🎪", "🎭", "🎨", "🎬", "🎮", "🕹️", "🎲", "🃏", "🎰", "🎱", "🏅", "🥇"
]

# Encoding attempts for email headers
ENCODING_ATTEMPTS = ['utf-8', 'iso-8859-1', 'ascii', 'cp1252']

# UID validation constants
MIN_VALID_UID = 1
MAX_VALID_UID = 999999999

# Provider-specific deletion delays
PROVIDER_DELAYS = {
    'icloud': 0.2,
    'default': 0.1
}