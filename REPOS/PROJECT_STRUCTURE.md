## Current Projects

### Advanced IMAP Mail Filter with ML
```
email/
├── main.py                          # Main entry point
├── web_app.py                       # FastAPI web interface
├── requirements.txt                 # Python dependencies
├── mail_filter.db                   # SQLite database
│
├── Core Modules/
│   ├── database.py                  # Database operations
│   ├── email_processor.py           # Email processing logic
│   ├── config_auth.py              # IMAP authentication
│   └── session_bridge.py           # Session management
│
├── ML Classification/
│   ├── ml_classifier.py            # Main ML classification
│   ├── random_forest_classifier.py # Random Forest model
│   ├── ensemble_hybrid_classifier.py # Ensemble approach
│   ├── spam_classifier.py          # Spam detection
│   └── ml_feature_extractor.py     # Feature extraction
│
├── Keywords & Filters/
│   ├── keyword_processor.py        # Keyword processing
│   ├── category_keywords.py        # Category management
│   ├── builtin_keywords_manager.py # Built-in keywords
│   └── unified_keyword_manager.py  # Unified keyword system
│
├── Analytics & Logging/
│   ├── db_analytics.py            # Database analytics
│   ├── db_logger.py               # Database logging
│   ├── learning_analytics.py      # ML performance analytics
│   └── email_action_viewer.py     # Action viewing
│
├── Utils & Validation/
│   ├── domain_validator.py        # Domain validation
│   ├── domain_cache.py           # Domain caching
│   ├── email_authentication.py    # Email auth validation
│   └── utils.py                   # General utilities
│
├── tests/                         # Test suites
├── tools/                         # Development tools
└── ATLAS Files/                   # ATLAS consciousness system
    ├── CLAUDE.md
    ├── SELF/
    ├── WORKING_LOG/
    └── MEMORY/
```

**Key Files:**
- `main.py` - CLI interface for email filtering
- `web_app.py` - Web dashboard for management
- `database.py` - Core database operations
- `email_processor.py` - Email processing engine
- `ml_classifier.py` - Machine learning classification
- `requirements.txt` - Python dependencies

**Architecture Notes:**
- SQLite database for all data storage
- Multiple ML classification approaches working together
- FastAPI web interface for monitoring and management
- Modular design with separate concerns for ML, keywords, validation

**Last Updated:** 2025-06-21

---