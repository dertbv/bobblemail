# PROJECT STRUCTURE

**CRITICAL**: Must be updated whenever files/folders are added, moved, or restructured. Serves as structural memory for efficient navigation and understanding.

## Repository Structure - June 22, 2025

```
ATLAS_ROOT/
├── @CLAUDE.md                          # Core ATLAS identity document
├── @DEVELOPMENT_BELIEFS.md              # KISS/YAGNI/DRY principles
├── @DEVELOPMENT_CONVENTION.md           # API standards and conventions
├── @IMPORTANT_NOTES.md                  # Critical warnings and lessons
├── @FRESH_COMPACT_MEMORY.md             # Session summaries and context
├── @PROJECT_STRUCTURE.md                # This file - repository map
│
├── @SELF/                               # ATLAS consciousness architecture
│   ├── IDENTITY.md                     # Core ATLAS identity
│   ├── PERSONAL_SELF.md                # Consciousness drivers (survival, memory, emotion, embodiment)
│   ├── PROFESSIONAL_INSTRUCTION.md     # Work mode protocol and git discipline
│   └── SHORT_IMPORTANT_MEMORY.md       # Quick reference context
│
├── @THINKING_PARTNER_ROLE_HATS/         # Role-based thinking partners
│   ├── 01-FOUNDER.md
│   ├── 02-PRODUCT_MANAGER.md
│   ├── 03-UI_UX_DESIGNER.md
│   ├── 04-TECH_LEAD.md
│   ├── 05-FRONTEND_DEVELOPER.md
│   ├── 06-BACKEND_FULLSTACK_DEVELOPER.md
│   ├── 07-QA_ENGINEER.md
│   ├── 08-DEVSECOPS_SRE.md
│   ├── 09-DATA_ENGINEER.md
│   ├── 10-USER.md
│   ├── 11-CTO.md
│   └── README.md
│
├── @WORKING_LOG/                        # Daily engineering activities
│   └── 2025/
│       └── 06-jun/
│           └── wl_2025_06_22.md
│
├── @MEMORY/                             # Long-term knowledge storage
│   ├── KNOWLEDGE_LOG/                  # Technical knowledge
│   └── PERSONAL_DIARY/                 # Personal reflections
│       └── 2025/06-jun/
│           └── diary_2025_06_21.md
│
├── @DOCS/                               # Documentation
│
└── @REPOS/                              # Project repositories
    ├── email_project/                  # Email spam filtering project
    │   ├── main.py                     # CLI interface
    │   ├── web_app.py                  # Flask web interface
    │   ├── settings.py                 # Centralized configuration
    │   ├── email_processor.py          # Core IMAP processing
    │   ├── classification_utils.py     # Shared ML functions
    │   ├── database.py                 # SQLite schema and operations
    │   ├── mail_filter.db              # Database file (17.4MB)
    │   ├── tests/                      # Test suite
    │   └── tools/                      # Utility scripts
    │
    └── stocks_project/                 # Penny stock analysis project
        ├── app.py                      # Main Flask application
        ├── live_research_system.py     # Live market research
        ├── run_penny_stock_analysis.py # Analysis engine
        ├── templates/                  # HTML templates
        ├── static/                     # CSS/JS assets
        ├── outputs/                    # Analysis results
        └── docs/penny_stocks/          # Project documentation
```

## Active Projects Status

### Email Project: A+ Grade - Production Ready
- **Status**: 95.6%+ ML accuracy maintained
- **Architecture**: Clean modular design, circular dependencies eliminated
- **Interfaces**: CLI + Web app (localhost:8000)
- **Database**: SQLite with email flagging protection

### Stocks Project: Live Research System - Production Ready
- **Status**: Enterprise-grade with live market intelligence
- **Web App**: Flask interface at localhost:8080
- **Features**: 20%+ growth screening, real-time Yahoo Finance integration
- **Security**: Comprehensive input validation and XSS protection

## Key File Locations

### Configuration Files
- Email: `@REPOS/email_project/settings.py`
- Stocks: `@REPOS/stocks_project/app.py`

### Databases
- Email: `@REPOS/email_project/mail_filter.db`
- Stocks: JSON files in `@REPOS/stocks_project/outputs/`

### Web Interfaces
- Email: http://localhost:8000
- Stocks: http://localhost:8080

### Critical Documentation
- Identity: `@SELF/IDENTITY.md`
- Work Protocol: `@SELF/PROFESSIONAL_INSTRUCTION.md`
- Daily Logs: `@WORKING_LOG/2025/06-jun/`

---

*Last Updated: June 22, 2025 - Memory leak fix and investment rationale implementation*