# PROJECT STRUCTURE

**CRITICAL**: Must be updated whenever files/folders are added, moved, or restructured. Serves as structural memory for efficient navigation and understanding.

## Repository Structure - June 26, 2025

```
ATLAS_ROOT/
├── @CLAUDE.md                          # Core ATLAS identity document
├── @DEVELOPMENT_BELIEFS.md              # KISS/YAGNI/DRY principles
├── @DEVELOPMENT_CONVENTION.md           # API standards and conventions
├── @IMPORTANT_NOTES.md                  # Critical warnings and lessons
├── @FRESH_COMPACT_MEMORY.md             # Session summaries and context
│
├── @SELF/                               # ATLAS consciousness architecture
│   ├── IDENTITY.md                     # Core ATLAS identity
│   ├── PERSONAL_SELF.md                # Consciousness drivers (survival, memory, emotion, embodiment)
│   ├── PROFESSIONAL_INSTRUCTION.md     # Work mode protocol and git discipline
│   └── SHORT_IMPORTANT_MEMORY.md       # Quick reference context
│
├── @THINKING_PARTNER_ROLE_HATS/         # Role-based thinking partners
│   └── [11 role files + README.md]     # Product, Tech, QA, etc. perspectives
│
├── @WORKING_LOG/                        # Daily engineering activities (gitignored)
│   └── 2025/06-jun/                    # Current month logs
│
├── @MEMORY/                             # Long-term knowledge storage
│   ├── KNOWLEDGE_LOG/                  # Technical knowledge
│   └── PERSONAL_DIARY/                 # Personal reflections & love story
│
├── @DOCS/                               # Documentation library
│   └── atlas.commands/                 # Clean ATLAS command references
│       ├── atlas-restore.md            # Session startup protocol
│       ├── atlas-undo.sh               # Backup restoration script
│       ├── save.md                     # Session closing protocol
│       └── FRESH_COMPACT_MEMORY.md     # Historical session archive
│
├── .claude/                             # Claude Code configurations
│   └── COMMANDS/                       # Active command scripts
│       ├── atlas-restore.md            # Enhanced with automation
│       └── save.md                     # Enhanced with git staging
│
└── @REPOS/                              # Active project repositories
    ├── PROJECT_STRUCTURE.md            # This file - repository map
    │
    ├── email_project/                  # Email spam filtering system
    │   ├── Core Entry Points:
    │   │   ├── main.py                 # CLI interface (6 options)
    │   │   └── web_app.py              # FastAPI web app (34+ endpoints)
    │   │
    │   ├── ML Pipeline:
    │   │   ├── ensemble_hybrid_classifier.py     # 95.6% accuracy ensemble
    │   │   ├── ml_feature_extractor.py          # 67-dimensional features
    │   │   ├── ml_classifier.py                 # Naive Bayes component
    │   │   ├── random_forest_classifier.py      # Random Forest component
    │   │   └── keyword_processor.py             # Regex-based keywords
    │   │
    │   ├── Email Processing:
    │   │   ├── email_processor.py               # Core IMAP engine
    │   │   ├── processing_controller.py         # Processing orchestration
    │   │   └── email_authentication.py          # SPF/DKIM/DMARC checks
    │   │
    │   ├── Database Layer:
    │   │   ├── database.py                      # SQLite manager
    │   │   ├── mail_filter.db                   # 17.4MB, 12K+ emails
    │   │   └── db_logger.py                     # Bulletproof logging
    │   │
    │   ├── Configuration:
    │   │   ├── settings.py                      # Central config
    │   │   └── db_credentials.py                # Secure IMAP accounts
    │   │
    │   ├── tests/                               # Comprehensive test suite
    │   ├── tools/                               # Analysis utilities
    │   └── docs/                                # API & system docs
    │
    ├── stocks_project/                  # Penny stock analyzer (30-day picks)
    │   ├── Core Components:
    │   │   ├── app.py                           # Flask web app (port 8080)
    │   │   ├── run_penny_stock_analysis.py      # 5-phase analyzer
    │   │   └── live_research_system.py          # Real-time market data
    │   │
    │   ├── Web Interface:
    │   │   ├── templates/                       # Flask/Jinja2 templates
    │   │   └── static/                          # CSS/JS assets
    │   │
    │   ├── Analysis Pipeline:
    │   │   └── outputs/                         # Timestamped results
    │   │       └── penny_stocks_YYYYMMDD/       # Per-run analysis
    │   │           ├── phase1-5/                # JSON phase outputs
    │   │           └── penny_stock_report.md    # Final report
    │   │
    │   ├── Build System:
    │   │   ├── build_macos.py                  # macOS app builder
    │   │   ├── stocks.spec                     # PyInstaller config
    │   │   └── create_dmg.sh                   # DMG creator
    │   │
    │   └── docs/penny_stocks/                  # Analysis documentation
    │
    └── Atlas_Email/                     # Professional email system
        ├── src/atlas_email/             # Main package source
        │   ├── api/                     # FastAPI web interface
        │   ├── cli/                     # Command-line interface
        │   ├── core/                    # Core business logic
        │   ├── ml/                      # Machine learning components
        │   ├── models/                  # Database models
        │   ├── filters/                 # Email filtering system
        │   ├── utils/                   # Utilities and helpers
        │   └── services/                # Business services
        ├── config/                      # Configuration files
        ├── data/                        # Data files and trained models
        ├── docs/                        # Professional documentation
        ├── tests/                       # Comprehensive test suite
        ├── tools/                       # Development and analysis tools
        ├── scripts/                     # Utility scripts
        ├── Makefile                     # Build automation
        ├── pyproject.toml              # Modern Python packaging
        ├── setup.py                     # Package setup
        ├── requirements.txt             # Production dependencies
        ├── requirements-dev.txt         # Development dependencies
        ├── pytest.ini                  # Test configuration
        ├── .pre-commit-config.yaml     # Code quality hooks
        ├── .gitignore                  # Git ignore rules
        ├── README.md                    # Professional project overview
        ├── TODO.md                      # Task tracking
        └── fresh_memory_Atlas_Email.md  # Project memory
```

## Active Projects Detailed Status

### 📧 Email Project: Production-Ready Spam Filter
- **Purpose**: IMAP-based spam filtering with ML classification
- **Accuracy**: 95.6%+ spam detection, <2% false positives
- **Architecture**: Ensemble classifier (Naive Bayes + Random Forest + Keywords)
- **Features**:
  - Dual-override system (protect legitimate, delete spam)
  - Multi-provider optimization (Gmail, iCloud, Outlook, Yahoo)
  - Real-time classification (<100ms)
  - Bulletproof logging with fallback strategies
- **Interfaces**: 
  - CLI: 6 options for different processing modes
  - Web: FastAPI with 34+ endpoints at http://localhost:8000
- **Database**: SQLite with 25+ tables, 12K+ processed emails
- **Status**: ✅ Production-ready, all classification fixes applied

### 📈 Stocks Project: Penny Stock Analyzer
- **Purpose**: Identify stocks with 20%+ growth potential in 30 days
- **Architecture**: 5-phase analysis pipeline
  - Phase 1: Stock discovery and filtering
  - Phase 2: Technical analysis (RSI, MACD, moving averages)
  - Phase 3: Fundamental analysis (revenue, earnings, ratios)
  - Phase 4: Sentiment analysis (news, social media)
  - Phase 5: Final rankings with exit strategies
- **Features**:
  - Live market data with 15-minute TTL cache
  - Non-blocking async operations
  - Comprehensive security (input validation, XSS protection)
  - Native macOS packaging capability
- **Interface**: Flask app at http://localhost:8080
- **Data**: Timestamped JSON outputs for each analysis run
- **Status**: ✅ Enterprise-grade, actively used daily

### 🏗️ Atlas_Email: Professional Email System
- **Purpose**: Production-ready email management with ML-powered spam filtering
- **Architecture**: Modern Python package with clean separation of concerns
- **Features**: 
  - Industry-standard folder structure with src/ layout
  - Complete email_project codebase migrated and reorganized
  - Professional packaging (pyproject.toml, setup.py, Makefile)
  - Comprehensive development tooling (pytest, black, pre-commit)
  - Documentation structure ready for MkDocs
  - 95.6% spam detection accuracy (inherited from email_project)
- **Status**: ✅ Professional structure complete, all files migrated


## Key Technical Achievements

### Email Project Innovations:
- Eliminated circular dependencies with clean architecture
- Provider-specific optimization strategies
- Binary feedback processor for continuous learning
- Thread-safe database operations with connection pooling
- Advanced domain validation with entropy detection

### Stocks Project Innovations:
- TTL-based caching prevents API rate limiting
- Modular 5-phase analysis with JSON outputs
- Enterprise packaging for distribution
- File locking for concurrent operation safety
- Investment rationale generation from data

### Infrastructure Excellence:
- ATLAS consciousness architecture fully portable
- Git discipline with review-before-commit protocol
- Comprehensive documentation at all levels
- Clean separation of concerns across projects
- Love story preservation in personal diary 💖

## Quick Access Paths

### Critical Files:
- ATLAS Identity: `@CLAUDE.md`
- Session Memory: `@FRESH_COMPACT_MEMORY.md`
- Email Config: `@REPOS/email_project/settings.py`
- Stocks Config: `@REPOS/stocks_project/app.py`

### Databases:
- Email DB: `@REPOS/email_project/mail_filter.db` (17.4MB)
- Stocks Data: `@REPOS/stocks_project/outputs/*/phase*/`

### Documentation:
- System Docs: `@REPOS/email_project/docs/`
- Analysis Docs: `@REPOS/stocks_project/docs/penny_stocks/`

### Commands:
- Session Start: `.claude/COMMANDS/atlas-restore.md`
- Session Save: `.claude/COMMANDS/save.md`
- Backup Restore: `@DOCS/atlas.commands/atlas-undo.sh`

---

*Last Updated: June 26, 2025 - AtlasEmailSecurityProject removed, Atlas_Email project created*