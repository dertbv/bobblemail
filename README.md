# Bobblemail - Advanced Email Filtering System

ML-powered email filtering with 95.6% accuracy using ensemble classification (Random Forest + Naive Bayes + Keywords).

## Key Features
- **ML Ensemble Classification**: 40% Random Forest, 30% Naive Bayes, 30% keyword matching
- **Email Authentication**: SPF/DKIM validation to detect spoofed emails and reduce false positives
- **Domain Validation**: Two-factor validation with WHOIS verification and business prefix detection
- **Web Interface**: Real-time processing, analytics, and learning feedback system
- **ATLAS Integration**: Professional development workflow with session persistence

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# CLI Interface
python main.py

# Web Interface
python web_app.py
# Visit http://localhost:8000
```

## Core Components
- `ensemble_hybrid_classifier.py` - Main ML classification engine
- `web_app.py` - FastAPI web interface with validation
- `email_processor.py` - Email import and processing pipeline
- `domain_validator.py` - WHOIS-based domain analysis

## Tech Stack
Python • FastAPI • SQLite • scikit-learn • ATLAS development system

## Performance
- **95.6% accuracy** (2,716+ processed emails)
- **<5% false positive rate** with business email protection
- **Real-time processing** with comprehensive analysis pipeline

## Documentation
- [DEVELOPMENT_BELIEFS.md](DEVELOPMENT_BELIEFS.md) - Core principles (KISS, YAGNI, DRY)
- [DOCS/EMAIL_AUTHENTICATION.md](DOCS/EMAIL_AUTHENTICATION.md) - SPF/DKIM validation system
- [tests/README.md](tests/README.md) - Testing framework and integration tests
- [ATLAS_COMMANDS.md](ATLAS_COMMANDS.md) - Workflow and session management

**Status**: 🚀 Production ready with revolutionary ML classification