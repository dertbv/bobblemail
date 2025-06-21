## Current Projects

### Email Filtering System (email_project)
```
email_project/
├── main.py                        # CLI entry point with menu system
├── web_app.py                     # FastAPI web interface
├── database.py                    # SQLite database management
├── email_processor.py             # IMAP email processing
├── ensemble_hybrid_classifier.py  # Core ML ensemble classifier
├── ml_classifier.py              # Machine learning base implementations
├── random_forest_classifier.py   # Random Forest classifier
├── domain_validator.py           # Domain legitimacy checking
├── keyword_processor.py          # Rule-based keyword matching
├── tests/                        # Test suite
├── tools/                        # Utility scripts
├── requirements.txt              # Python dependencies
└── mail_filter.db               # SQLite database
```

**Purpose:** Advanced IMAP-based email filtering and classification system with ML capabilities
**Technologies:** Python, SQLite, scikit-learn, FastAPI, IMAP
**Key Features:**
- Ensemble ML classification (95.6%+ accuracy)
- Multi-account batch processing
- Domain validation with WHOIS
- User feedback learning system
- Web and CLI interfaces

**Last Updated:** June 21, 2025

---

### Penny Stock Analysis Tool (stocks_project)
```
stocks_project/
├── app.py                    # Main Flask application
├── app_real_data.py         # Real data implementation
├── run_penny_stock_analysis.py  # Analysis runner
├── agent.md                 # Agentic loop architecture docs
├── docs/
│   └── penny_stocks/       # Agent context and instructions
├── outputs/                # Analysis results by timestamp
├── static/                 # CSS and JavaScript
├── templates/              # HTML templates
├── requirements.txt        # Python dependencies
└── venv/                   # Virtual environment
```

**Purpose:** Identifies top 10 penny stocks with greatest 30-day potential
**Technologies:** Python, Flask, pandas, yfinance, BeautifulSoup4
**Architecture:** Agentic Loop with 3 AI agents:
- Atlas (Orchestrator)
- Mercury (Specialist) 
- Apollo (Evaluator)

**Key Features:**
- 5-phase analysis pipeline
- Real-time web dashboard
- RESTful API endpoints
- Quality scoring system
- Responsive design

**Last Updated:** June 21, 2025