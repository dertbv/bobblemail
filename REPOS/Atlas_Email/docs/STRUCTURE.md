# Atlas_Email Project Structure

## Professional Email System
- **Purpose**: Production-ready email management with ML-powered spam filtering
- **Architecture**: Modern Python package with clean separation of concerns
- **Status**: ✅ Professional structure complete, all files migrated

## Directory Structure

```
Atlas_Email/                     # Professional email system
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

## Features
- Industry-standard folder structure with src/ layout
- Complete email_project codebase migrated and reorganized
- Professional packaging (pyproject.toml, setup.py, Makefile)
- Comprehensive development tooling (pytest, black, pre-commit)
- Documentation structure ready for MkDocs
- 95.6% spam detection accuracy (inherited from email_project)

## Key Components

### API Layer (`src/atlas_email/api/`)
- FastAPI web interface with Jinja2 templates
- REST endpoints for email management
- Security middleware and XSS protection

### CLI Layer (`src/atlas_email/cli/`)
- Command-line interface for direct email processing
- Independent of web dependencies
- Menu-driven email management

### Core Logic (`src/atlas_email/core/`)
- Email processing engine
- Classification orchestration
- Business rule enforcement

### ML Pipeline (`src/atlas_email/ml/`)
- Ensemble classifier (Naive Bayes + Random Forest + Keywords)
- Feature extraction and model training
- 95.6% accuracy spam detection

### Data Models (`src/atlas_email/models/`)
- Database schema definitions
- Analytics and logging models
- Configuration management

## Development Workflow
- Use `make install` for dependency installation
- Use `make test` for running test suite
- Use `make lint` for code quality checks
- Use `make build` for package building