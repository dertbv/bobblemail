## Current Projects

### Advanced IMAP Mail Filter with ML

**Location:** `REPOS/email-filter/`

```
REPOS/email-filter/
├── main.py                          # Main CLI entry point
├── web_app.py                       # FastAPI web interface
├── requirements.txt                 # Python dependencies
├── mail_filter.db                   # SQLite database
├── my_keywords.txt                  # User keyword definitions
│
├── Core Processing/
│   ├── database.py                  # Database operations
│   ├── email_processor.py           # Email processing engine
│   ├── config_auth.py              # IMAP authentication
│   ├── session_bridge.py           # Session management
│   └── processing_controls.py      # Processing flow control
│
├── ML Classification/
│   ├── ml_classifier.py            # Main ML classification
│   ├── random_forest_classifier.py # Random Forest model
│   ├── ensemble_hybrid_classifier.py # Ensemble approach
│   ├── spam_classifier.py          # Spam detection
│   ├── ml_feature_extractor.py     # Feature extraction
│   ├── logical_classifier.py       # Logical classification
│   └── ml_category_classifier.py   # Category classification
│
├── Keywords & Filters/
│   ├── keyword_processor.py        # Keyword processing
│   ├── category_keywords.py        # Category management
│   ├── builtin_keywords_manager.py # Built-in keywords
│   ├── unified_keyword_manager.py  # Unified keyword system
│   └── selective_vendor_filter.py  # Vendor filtering
│
├── Analytics & Logging/
│   ├── db_analytics.py            # Database analytics
│   ├── db_logger.py               # Database logging
│   ├── learning_analytics.py      # ML performance analytics
│   ├── email_action_viewer.py     # Action viewing
│   └── binary_feedback_processor.py # Feedback processing
│
├── Domain & Validation/
│   ├── domain_validator.py        # Domain validation
│   ├── domain_cache.py           # Domain caching
│   ├── email_authentication.py    # Email auth validation
│   ├── two_factor_email_validator.py # 2FA validation
│   └── vendor_preferences_schema.py # Vendor preferences
│
├── Utilities/
│   ├── utils.py                   # General utilities
│   ├── provider_utils.py         # Email provider utilities
│   ├── constants.py              # System constants
│   ├── regex_optimizer.py        # Regex optimization
│   ├── smart_regex_selector.py   # Smart regex selection
│   ├── auto_batch_timer.py       # Batch timing
│   ├── session_memory.py         # Session management
│   └── legitimate_business_prefixes.py # Business validation
│
├── Configuration/
│   ├── ml_settings.py            # ML configuration
│   ├── db_credentials.py         # Database credentials
│   ├── vendor_filter_integration.py # Vendor integration
│   ├── ml_settings.json          # ML settings file
│   ├── ensemble_hybrid_config.json # Ensemble config
│   ├── ml_ensemble_config.json   # ML ensemble config
│   ├── ml_category_classifier.json # Category config
│   └── naive_bayes_model.json    # Naive Bayes config
│
├── ML Models/
│   ├── random_forest_model.pkl           # Random Forest model
│   ├── ml_category_classifier_binary.pkl # Binary classifier
│   ├── ml_category_classifier_category.pkl # Category classifier
│   ├── ml_category_classifier_encoder.pkl # Encoder model
│   └── ml_category_classifier_scaler.pkl  # Scaler model
│
├── tests/                         # Test suites
│   ├── test_complete_vendor_integration.py
│   ├── test_domain_validation.py
│   ├── test_ml_category_system.py
│   ├── test_random_forest_integration.py
│   ├── test_user_keyword_priority.py
│   ├── test_email_authentication.py
│   └── test_authenticated_whitelist_clean.py
│
├── tools/                         # Development tools
│   ├── keyword_usage_analyzer.py
│   ├── regex_performance_test.py
│   └── verify_ml_enabled.py
│
├── logs/
│   └── web_app.log               # Application logs
│
└── who                           # Identity script
```

**Key Files:**
- `main.py` - CLI interface for email filtering
- `web_app.py` - Web dashboard for management (5,626 lines - needs refactoring)
- `database.py` - Core database operations
- `email_processor.py` - Email processing engine (2,009 lines - needs refactoring)
- `ml_classifier.py` - Machine learning classification
- `requirements.txt` - Python dependencies

**Architecture Notes:**
- SQLite database for all data storage
- Multiple ML classification approaches working together
- FastAPI web interface for monitoring and management
- Modular design with separate concerns for ML, keywords, validation
- **Refactoring needed:** Several large files violate KISS/SRP principles

**Last Updated:** 2025-06-21

---