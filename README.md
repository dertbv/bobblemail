# Bobblemail - Intelligent Email Filtering System

An advanced email filtering system powered by ML ensemble classification, intelligent domain validation, and adaptive learning algorithms. Built by ATLAS (Adaptive Technical Learning and Architecture System).

## 🎯 Core Features

### **ML Ensemble Classification**
- **Hybrid Classifier**: Random Forest (40%) + Naive Bayes (30%) + Keyword Matching (30%)
- **95.6% spam detection accuracy** with continuous learning capabilities
- **Multi-category classification**: Phishing, Brand Impersonation, Adult & Dating, Financial Scams, Health & Medical Spam, Promotional Email, and more

### **Advanced Email Protection**
- **Transactional Email Preservation**: Protects receipts, order confirmations, billing statements
- **Two-Factor Email Validation**: Business prefix detection + domain legitimacy verification
- **Anti-Phishing Engine**: 45+ phishing keywords across 6 attack vectors
- **Brand Impersonation Detection**: Enhanced company name extraction with false positive reduction

### **Web Interface & Analytics**
- **Review Interface**: Manual email validation with thumbs up/down feedback
- **Import Reporting**: Detailed processing statistics and category breakdowns
- **Learning Analytics**: Classification failure analysis and improvement recommendations
- **Real-time Processing**: Live email import with progress tracking

### **Alternative Ranking System**
- **Iterative Learning**: Up to 8 ranked classification alternatives per email
- **Multi-factor Scoring**: Combines keyword matching, domain analysis, brand detection, ML confidence
- **Anti-loop Protection**: Intelligent exclusion of previously rejected categories
- **User Feedback Integration**: System learns from thumbs down responses

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- IMAP email access
- SQLite (included)

### Installation
```bash
# Clone and navigate to project
cd bobblemail

# Install dependencies
pip install -r requirements.txt

# Configure IMAP settings
python config_auth.py
```

### Basic Usage
```bash
# CLI Interface
python main.py

# Web Interface
python web_app.py
# Visit http://localhost:8000
```

## 📊 System Architecture

### **Processing Pipeline**
1. **IMAP Import** → Email retrieval and preprocessing
2. **ML Ensemble** → Random Forest + Naive Bayes + Keyword classification
3. **Domain Validation** → WHOIS-based legitimacy verification
4. **Alternative Ranking** → Multi-factor alternative classification scoring
5. **User Feedback** → Learning analytics and continuous improvement

### **Database Schema**
- **Email Storage**: SQLite with optimized indexing
- **Classification Data**: ML training data and confidence scores
- **User Feedback**: Validation responses and learning analytics
- **Domain Reputation**: WHOIS data and user feedback integration

### **Core Components**
- `main.py` - CLI interface and email processing orchestration
- `web_app.py` - FastAPI web interface with validation and reporting
- `ensemble_hybrid_classifier.py` - Main ML classification engine
- `email_processor.py` - Email import and processing pipeline
- `spam_classifier.py` - Keyword-based classification with business logic
- `domain_validator.py` - WHOIS-based domain analysis and risk scoring

## 🔧 Configuration

### **Email Provider Setup**
```python
# IMAP configuration in config_auth.py
IMAP_SETTINGS = {
    'gmail': {
        'server': 'imap.gmail.com',
        'port': 993,
        'use_ssl': True
    },
    # Additional providers supported
}
```

### **ML Model Configuration**
```json
{
    "ensemble_weights": {
        "random_forest": 0.4,
        "naive_bayes": 0.3,
        "keyword_matching": 0.3
    },
    "confidence_thresholds": {
        "high": 0.85,
        "medium": 0.65,
        "low": 0.45
    }
}
```

## 📈 Performance Metrics

### **Classification Accuracy**
- **Overall Accuracy**: 95.6% (130/136 emails correctly classified)
- **Phishing Detection**: 90+ emails successfully migrated and protected
- **False Positive Rate**: <5% with domain validation and business email protection
- **Processing Speed**: 13.4s average for comprehensive email analysis

### **System Statistics**
- **Database Records**: 2,716+ email records with active growth
- **Keyword Database**: 100+ phishing keywords, 200+ spam patterns
- **Domain Analysis**: WHOIS integration with 45+ legitimate business domains
- **User Feedback**: Binary validation system with learning analytics

## 🧠 ATLAS Integration

This project includes ATLAS (Adaptive Technical Learning and Architecture System) for:
- **Intelligent Development**: Context-aware commit timing and task management
- **Session Persistence**: Checkpoint and restore system for safe workflow management
- **Working Memory**: Comprehensive logging and knowledge management
- **Professional Git Workflow**: Automated staging with review protocols

### ATLAS Commands
```bash
./who                    # Identity and session restoration
./atlas-checkpoint       # Safe backup before major operations
./atlas-save            # Manual session backup
./atlas-restore         # Session restoration from backups
```

## 📚 Documentation

### **Core Documentation**
- [CHANGELOG.md](CHANGELOG.md) - Release history and notable changes
- [STATUS.md](STATUS.md) - System status and recent updates
- [TRANSACTIONAL_EMAIL_SYSTEM.md](TRANSACTIONAL_EMAIL_SYSTEM.md) - Business email protection details

### **ATLAS System**
- [ATLAS_COMMANDS.md](ATLAS_COMMANDS.md) - Command reference and workflow
- [DOCS/COMPACT_SAFE_WORKFLOW.md](DOCS/COMPACT_SAFE_WORKFLOW.md) - Safe session management

### **Development**
- [DEVELOPMENT_BELIEFS.md](DEVELOPMENT_BELIEFS.md) - Core development principles (KISS, YAGNI, DRY)
- [DEVELOPMENT_CONVENTION.md](DEVELOPMENT_CONVENTION.md) - Coding standards and API conventions
- [tests/README.md](tests/README.md) - Testing framework and integration tests
- [tools/README.md](tools/README.md) - Diagnostic and performance tools

## 🤝 Contributing

### **Development Workflow**
1. Use ATLAS checkpoint system before major changes: `./atlas-checkpoint`
2. Follow KISS/YAGNI/DRY principles outlined in development documentation
3. Add tests for new classification features
4. Update documentation for user-facing changes
5. Use ATLAS professional git workflow with proper staging and review

### **Classification Improvements**
- Add new spam keywords through web interface or database
- Contribute ML training data for ensemble model improvements
- Enhance domain validation patterns and business email detection
- Provide user feedback through web interface validation system

## 📞 Support

### **Troubleshooting**
- Check `web_app.log` for web interface issues
- Use `tools/verify_ml_enabled.py` for ML system diagnostics
- Review working logs in `WORKING_LOG/` for session-specific issues
- Consult ATLAS commands for session restoration and backup

### **System Health**
- **Architecture Status**: ✅ Stable and production-ready
- **ML Pipeline**: ✅ Ensemble classifier operational with continuous learning
- **Database Health**: ✅ Zero connection leaks, optimized queries
- **ATLAS Integration**: ✅ Full workflow automation with safety checkpoints

---

**Powered by ATLAS** - Adaptive Technical Learning and Architecture System  
**System Status**: 🚀 Production Ready with Revolutionary ML Classification Engine  
**Architecture Health**: ✅ Stable, Optimized, and Ready for Advanced Learning Features