# Email Project Structure

## Email Spam Filtering System
- **Purpose**: IMAP-based spam filtering with ML classification
- **Accuracy**: 95.6%+ spam detection, <2% false positives
- **Status**: ✅ Production-ready, all classification fixes applied

## Directory Structure

```
email_project/                  # Email spam filtering system
├── Core Entry Points:
│   ├── main.py                 # CLI interface (6 options)
│   └── web_app.py              # FastAPI web app (34+ endpoints)
│
├── ML Pipeline:
│   ├── ensemble_hybrid_classifier.py     # 95.6% accuracy ensemble
│   ├── ml_feature_extractor.py          # 67-dimensional features
│   ├── ml_classifier.py                 # Naive Bayes component
│   ├── random_forest_classifier.py      # Random Forest component
│   └── keyword_processor.py             # Regex-based keywords
│
├── Email Processing:
│   ├── email_processor.py               # Core IMAP engine
│   ├── processing_controller.py         # Processing orchestration
│   └── email_authentication.py          # SPF/DKIM/DMARC checks
│
├── Database Layer:
│   ├── database.py                      # SQLite manager
│   ├── mail_filter.db                   # 17.4MB, 12K+ emails
│   └── db_logger.py                     # Bulletproof logging
│
├── Configuration:
│   ├── settings.py                      # Central config
│   └── db_credentials.py                # Secure IMAP accounts
│
├── tests/                               # Comprehensive test suite
├── tools/                               # Analysis utilities
└── docs/                                # API & system docs
```

## Architecture
- **Ensemble Classifier**: Naive Bayes + Random Forest + Keywords
- **Dual-Override System**: Protect legitimate, delete spam
- **Multi-Provider Optimization**: Gmail, iCloud, Outlook, Yahoo
- **Real-Time Classification**: <100ms processing time
- **Bulletproof Logging**: Fallback strategies for reliable operation

## Interfaces
- **CLI**: 6 options for different processing modes
- **Web**: FastAPI with 34+ endpoints at http://localhost:8000

## Database
- **SQLite**: 25+ tables, 12K+ processed emails
- **Size**: 17.4MB with comprehensive analytics
- **Logging**: Bulletproof fallback strategies

## Key Features
- Real-time IMAP email processing
- Provider-specific optimization strategies
- Circular dependency resolution
- Advanced domain validation with entropy detection
- Binary feedback processor for continuous learning

## Technical Innovations
- Eliminated circular dependencies with clean architecture
- Provider-specific optimization strategies
- Binary feedback processor for continuous learning
- Thread-safe database operations with connection pooling
- Advanced domain validation with entropy detection

## Quick Access
- **Config**: `settings.py` (Central configuration)
- **Database**: `mail_filter.db` (17.4MB, 12K+ emails)
- **Documentation**: `docs/` (API & system docs)
- **Web Interface**: http://localhost:8000 (FastAPI, 34+ endpoints)