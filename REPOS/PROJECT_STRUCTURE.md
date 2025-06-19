## Current Projects

### Email Filtering System
```
email/
├── Core System
│   ├── main.py                     # Main CLI application entry point
│   ├── web_app.py                  # FastAPI web interface
│   ├── database.py                 # Core database operations
│   ├── requirements.txt            # Python dependencies
│   └── constants.py                # System constants
├── Email Processing
│   ├── email_processor.py          # Core email processing logic
│   ├── config_auth.py              # IMAP connection management
│   ├── provider_utils.py           # Email provider utilities
│   └── utils.py                    # General utilities
├── ML Classification System
│   ├── ensemble_hybrid_classifier.py    # Main ML classifier
│   ├── ml_feature_extractor.py         # Feature extraction
│   ├── ml_classifier.py                # Base ML classifier
│   ├── random_forest_classifier.py     # Random Forest implementation
│   ├── logical_classifier.py           # Logic-based classifier
│   └── ml_system_integration.py        # ML system integration
├── Domain & Validation
│   ├── domain_validator.py         # Domain validation logic
│   ├── two_factor_email_validator.py   # Two-factor validation
│   └── domain_cache.py             # Domain caching
├── Keyword & Filter Management
│   ├── keyword_processor.py        # Keyword processing
│   ├── category_keywords.py        # Category keyword management
│   ├── builtin_keywords_manager.py # Built-in keywords
│   ├── unified_keyword_manager.py  # Unified keyword system
│   └── vendor_filter_integration.py # Vendor filtering
├── Database & Analytics
│   ├── db_logger.py                # Database logging
│   ├── db_analytics.py             # Analytics and reporting
│   ├── db_credentials.py           # Credential management
│   └── learning_analytics.py       # Learning analytics
├── Tests & Tools
│   ├── tests/                      # Test suite
│   │   ├── test_complete_vendor_integration.py
│   │   ├── test_domain_validation.py
│   │   └── test_ml_category_system.py
│   └── tools/                      # Utility tools
├── ATLAS AI System
│   ├── CLAUDE.md                   # ATLAS core instructions
│   ├── SELF/                       # ATLAS identity and instructions
│   ├── MEMORY/                     # Long-term memory storage
│   ├── WORKING_LOG/                # Daily activity logs
│   └── REPOS/                      # Project repositories
└── Configuration & Data
    ├── *.db files                  # SQLite databases
    ├── *.json files                # ML model configs
    └── *.pkl files                 # Trained ML models
```

**Key Entry Points:**
- `main.py` - CLI interface for email processing
- `web_app.py` - Web interface (FastAPI)
- `ensemble_hybrid_classifier.py` - Main ML classification system

**Core Technologies:**
- **Backend**: Python, FastAPI, SQLite
- **ML Stack**: scikit-learn, pandas, numpy
- **Email**: IMAP, cryptography, tldextract
- **Web**: uvicorn server

**Database Files:**
- `mail_filter.db` - Main database with comprehensive schema (emails, classifications, analytics, logs, sessions)

**Last Updated:** June 18, 2025