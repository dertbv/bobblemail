# Deployment Guide

## Email Project - Complete Deployment Guide

**System**: Production-ready ML spam filtering with 95.6% accuracy  
**Interfaces**: CLI + FastAPI web app on localhost:8000  
**Database**: SQLite (17.4MB) with auto-migration to PostgreSQL ready  
**ML Stack**: Ensemble hybrid classifier with 3-model voting system  

---

## 🎯 System Overview

### Architecture Components
- **CLI Application**: Full-featured terminal interface (`main.py`)
- **Web Interface**: FastAPI-based dashboard (`web_app.py`)
- **ML Engine**: Ensemble classifier (Random Forest + Naive Bayes + Keywords)
- **Database**: SQLite with 25+ tables, schema v5 with auto-migration
- **Email Processing**: Provider-optimized IMAP with bulk operations

### Key Features
- **95.6%+ Classification Accuracy** with real-time processing
- **Multi-Provider Support**: Gmail, iCloud, Outlook, Yahoo, custom IMAP
- **Continuous Learning**: User feedback improves ML models automatically
- **Dual-Override System**: Protect legitimate emails, flag spam for deletion
- **Production Monitoring**: Comprehensive logging and analytics

---

## 🔧 System Requirements

### Python Environment
| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python Version** | 3.8+ | 3.13+ |
| **Operating System** | Linux/macOS/Windows | Linux/macOS |
| **Memory** | 2GB RAM | 4GB+ RAM |
| **Storage** | 1GB available | 5GB+ (database growth) |
| **CPU** | Single core | Multi-core (ML processing) |

### Network Requirements
- **Internet Connection**: Stable broadband for IMAP operations
- **Ports**: 8000 (web interface), 993 (IMAP SSL)
- **Email Access**: IMAP-enabled accounts with app-specific passwords

---

## 📦 Installation Procedures

### 1. Quick Start Installation

```bash
# 1. Clone repository
git clone <repository_url>
cd email_project

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Initial setup and database creation
python main.py

# 4. Start web interface (optional)
python web_app.py
```

### 2. Dependencies Installation

#### Core Dependencies
```bash
# Create requirements.txt
cat > requirements.txt << EOF
# Core Dependencies
fastapi>=0.68.0
uvicorn>=0.15.0
tldextract>=3.1.0
python-whois>=0.7.0
cryptography>=3.4.0

# ML Dependencies  
numpy>=1.21.0
matplotlib>=3.4.0
scikit-learn>=1.0.0
seaborn>=0.11.0
pandas>=1.3.0

# Future PostgreSQL Support
# psycopg2-binary>=2.9.0
# redis>=4.0.0
EOF

pip install -r requirements.txt
```

#### Development Dependencies (Optional)
```bash
pip install pytest pytest-cov black flake8 jupyter
```

### 3. System Verification

```bash
# Verify Python version
python --version  # Should be 3.8+

# Test core dependencies
python -c "import fastapi, uvicorn, sklearn, numpy; print('Dependencies OK')"

# Verify ML models can load
python -c "from ensemble_hybrid_classifier import EnsembleHybridClassifier; print('ML OK')"
```

---

## 🗄️ Database Setup

### SQLite Database (Current Production)

**Automatic Initialization**:
```python
# Database auto-creates on first run
from database import db
connection = db.get_connection()  # Creates mail_filter.db with schema v5
```

**Database Specifications**:
- **File**: `mail_filter.db` (currently 17.4MB with production data)
- **Schema Version**: 5 (latest with bulletproof email processing)
- **Tables**: 25+ specialized tables including:
  - `processed_emails_bulletproof` (12,238 emails)
  - `sessions` (634 processing sessions)
  - `email_flags` (90 protection flags)
  - `user_feedback` (25 ML training corrections)
  - `logs` (9,112 structured log entries)

**Migration System**:
- **Automatic**: Detects schema version and auto-upgrades
- **Fallback**: Recreation if migration fails
- **Backup**: Manual backup recommended before upgrades

### Future PostgreSQL Migration

**Infrastructure Ready**:
```bash
# Environment variables for PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost:5432/email_filter"
export DB_TYPE="postgresql"  # Switches from SQLite

# Docker composition ready
docker-compose up -d postgres redis
```

---

## ⚙️ Configuration Management

### Centralized Configuration (`settings.py`)

All settings consolidated in single file with environment variable overrides:

```python
# Core ML Settings (with defaults)
ML_CONFIDENCE_THRESHOLD = int(os.getenv('ML_CONFIDENCE_THRESHOLD', 75))
ML_ENTROPY_THRESHOLD = float(os.getenv('ML_ENTROPY_THRESHOLD', 3.2))
ML_DOMAIN_AGE_THRESHOLD = int(os.getenv('ML_DOMAIN_AGE_THRESHOLD', 90))

# Provider-Specific Thresholds
ML_PROVIDER_THRESHOLDS = {
    'gmail': int(os.getenv('ML_GMAIL_THRESHOLD', 85)),
    'icloud': int(os.getenv('ML_ICLOUD_THRESHOLD', 80)),
    'outlook': int(os.getenv('ML_OUTLOOK_THRESHOLD', 75)),
    'yahoo': int(os.getenv('ML_YAHOO_THRESHOLD', 75))
}

# Ensemble Model Weights
ENSEMBLE_WEIGHTS = {
    'random_forest': float(os.getenv('ENSEMBLE_RF_WEIGHT', 0.4)),
    'naive_bayes': float(os.getenv('ENSEMBLE_NB_WEIGHT', 0.3)),
    'keyword_matching': float(os.getenv('ENSEMBLE_KW_WEIGHT', 0.3))
}
```

### Email Account Configuration

**Credential Storage**: Encrypted in database (migrated from JSON)
**Setup Process**: Interactive CLI configuration wizard

**Supported Providers with Optimizations**:

| Provider | Authentication | Batch Size | Special Features |
|----------|---------------|------------|------------------|
| **Gmail** | App Password | 50 emails | UID operations, high threshold |
| **iCloud** | App Password | 25 emails | Bulk operations only, conservative |
| **Outlook** | Standard/OAuth | 30 emails | Standard IMAP operations |
| **Yahoo** | App Password | 40 emails | Standard with authentication |
| **Custom IMAP** | Manual config | 35 emails | Full manual configuration |

**App Password Setup**:
```bash
# Gmail: https://myaccount.google.com/apppasswords
# iCloud: https://appleid.apple.com/account/manage  
# Yahoo: https://login.yahoo.com/account/security
```

---

## 🔒 Security Configuration

### Email Authentication Security

**Provider Requirements**:
- **Gmail**: App-specific password (2FA required)
- **iCloud**: App-specific password (2FA recommended)
- **Outlook**: Standard auth or Modern Auth
- **Yahoo**: App-specific password for IMAP access

**Connection Security**:
- **SSL/TLS**: All connections use port 993 with SSL
- **Certificate Validation**: Full certificate chain verification
- **Timeout Settings**: 30-second connection timeout

### Data Security

**Credential Protection**:
```python
# Database storage with Fernet encryption
from cryptography.fernet import Fernet
key = Fernet.generate_key()
encrypted_password = Fernet(key).encrypt(password.encode())
```

**File Permissions**:
```bash
# Set secure permissions
chmod 600 mail_filter.db          # Database read/write owner only
chmod 644 *.py                     # Python files readable
chmod 700 .                       # Directory access control
```

### Web Interface Security

**Development Security** (localhost only):
- **CORS**: Configured for localhost development
- **Input Validation**: XSS protection on all form inputs
- **SQL Injection**: Parameterized queries throughout
- **Authentication**: None (localhost development setup)

**Production Security Considerations**:
```python
# For production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 🚀 Deployment Procedures

### Local Development Deployment

#### 1. Complete Setup
```bash
# Clone and setup
git clone <repository>
cd email_project
pip install -r requirements.txt

# Initialize database and configuration
python main.py
# Follow interactive setup for email accounts

# Start web interface
python web_app.py
# Access: http://localhost:8000
```

#### 2. Email Account Configuration
```bash
# CLI setup wizard
python main.py
# Select option 1: "Email Account Management"
# Add accounts with provider auto-detection
# Test connections before proceeding
```

#### 3. Verification
```bash
# Test email processing
python main.py
# Select option 3: "Preview Emails" to test classification

# Test web interface
curl http://localhost:8000/api/accounts
# Should return JSON with configured accounts
```

### Production Deployment

#### Docker Deployment (Infrastructure Ready)

**Docker Environment**:
```yaml
# docker-compose.yml (ready for PostgreSQL/Redis)
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/email_filter
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: email_filter
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      
  redis:
    image: redis:6-alpine
```

**Deployment Commands**:
```bash
# Build and deploy
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

#### Manual Production Setup

**System Preparation**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv sqlite3 nginx

# CentOS/RHEL
sudo yum install python3 python3-pip sqlite nginx

# Create application user
sudo useradd -m -s /bin/bash email-filter
sudo su - email-filter
```

**Application Installation**:
```bash
# Setup application
git clone <repository> /opt/email-filter
cd /opt/email-filter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python main.py  # Run initial setup
```

**Service Configuration**:
```bash
# Create systemd service
sudo tee /etc/systemd/system/email-filter.service << EOF
[Unit]
Description=Email Filter Web Application
After=network.target

[Service]
Type=simple
User=email-filter
WorkingDirectory=/opt/email-filter
Environment=PATH=/opt/email-filter/venv/bin
ExecStart=/opt/email-filter/venv/bin/python web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable email-filter
sudo systemctl start email-filter
sudo systemctl status email-filter
```

**Nginx Reverse Proxy**:
```nginx
# /etc/nginx/sites-available/email-filter
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/email-filter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## ⚡ Performance Optimization

### ML Model Optimization

**Current Production Settings**:
```python
# Optimized ensemble weights (tested in production)
ENSEMBLE_WEIGHTS = {
    'random_forest': 0.4,    # Highest weight - best performance
    'naive_bayes': 0.3,      # Fast probabilistic predictions
    'keyword_matching': 0.3  # Rule-based reliability
}

# Provider-specific confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'gmail': 85,    # Conservative (fewer false positives)
    'icloud': 80,   # Balanced
    'outlook': 75,  # Aggressive (catch more spam)
    'default': 75
}
```

### IMAP Performance Optimization

**Provider-Specific Optimizations**:
```python
# Built into email_processor.py
PROVIDER_OPTIMIZATIONS = {
    'icloud': {
        'batch_size': 25,           # Small batches for stability
        'use_bulk_operations': True, # Apple prefers bulk operations
        'delay_between_batches': 0.1,
        'max_retries': 3
    },
    'gmail': {
        'batch_size': 50,           # Google handles larger batches
        'use_uid_operations': True,  # More efficient for Gmail
        'delay_between_batches': 0.05,
        'max_retries': 5
    },
    'outlook': {
        'batch_size': 30,           # Microsoft balanced approach
        'delay_between_batches': 0.1,
        'max_retries': 3
    }
}
```

### Database Performance

**SQLite Optimizations**:
```python
# Applied in database.py
PRAGMA_SETTINGS = {
    'journal_mode': 'DELETE',           # Reduce file handles
    'synchronous': 'NORMAL',            # Balance safety/speed
    'cache_size': 10000,                # 10MB cache
    'temp_store': 'memory',             # Temporary tables in RAM
    'mmap_size': 268435456              # 256MB memory map
}

# Optimized connection pooling
connection_timeout = 30.0              # 30-second timeout
```

**Performance Metrics** (Current Production):
- **Classification Speed**: <100ms per email
- **Batch Processing**: 1000+ emails/minute
- **Memory Usage**: <200MB steady state
- **Database Size**: 17.4MB with 12K+ emails

---

## 📊 Monitoring and Logging

### Application Monitoring

**Log Files**:
```bash
# Web application logs
webapp.log              # General web app activity (260KB)
web_app_debug.log      # Detailed debugging information
webapp.pid             # Process ID for running web app

# Email processing logs
mail_filter_imap_log.txt    # IMAP operations and errors
```

**Database Logging**:
```sql
-- Structured logging in SQLite
SELECT level, category, message, timestamp 
FROM logs 
WHERE level IN ('ERROR', 'WARN') 
ORDER BY timestamp DESC LIMIT 10;

-- Current log statistics: 9,112 entries
SELECT level, COUNT(*) FROM logs GROUP BY level;
```

### Health Checks

**System Health Endpoints**:
```bash
# Web interface health
curl http://localhost:8000/
curl http://localhost:8000/api/accounts

# Database health
python -c "from database import db; print(db.get_database_stats())"

# ML model health
python -c "
from ensemble_hybrid_classifier import EnsembleHybridClassifier
classifier = EnsembleHybridClassifier()
print(f'Models loaded: {classifier.models_loaded}')
print(f'Accuracy: {classifier.get_accuracy()}%')
"
```

### Performance Monitoring

**Key Metrics Dashboard** (Web Interface):
- **Classification Accuracy**: 95.6%+ target
- **Processing Speed**: <100ms per email target
- **Memory Usage**: <200MB target
- **Database Growth**: Monitor weekly
- **Error Rates**: <1% target

**Command-Line Monitoring**:
```bash
# Database statistics
sqlite3 mail_filter.db "
SELECT 
  'Emails Processed' as metric, COUNT(*) as value FROM processed_emails_bulletproof
UNION ALL
SELECT 
  'Sessions Completed' as metric, COUNT(*) as value FROM sessions
UNION ALL  
SELECT 
  'User Feedback' as metric, COUNT(*) as value FROM user_feedback;
"

# Recent error analysis
sqlite3 mail_filter.db "
SELECT timestamp, level, category, message 
FROM logs 
WHERE level = 'ERROR' 
ORDER BY timestamp DESC LIMIT 5;
"
```

---

## 💾 Backup and Maintenance

### Database Backup Procedures

**Daily Backup** (Recommended):
```bash
#!/bin/bash
# backup_database.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/email-filter/backups"
mkdir -p $BACKUP_DIR

# SQLite backup
sqlite3 mail_filter.db ".backup $BACKUP_DIR/mail_filter_$DATE.db"

# Compress old backups
find $BACKUP_DIR -name "*.db" -mtime +7 -exec gzip {} \;

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: mail_filter_$DATE.db"
```

**Configuration Backup**:
```bash
# Backup all configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    settings.py \
    my_keywords.txt \
    *.log

# Backup ML models
tar -czf models_backup_$(date +%Y%m%d).tar.gz \
    *.pkl *.json
```

### Maintenance Tasks

**Weekly Maintenance**:
```bash
#!/bin/bash
# weekly_maintenance.sh

# Database optimization
sqlite3 mail_filter.db "VACUUM; ANALYZE;"

# Log cleanup (keep 30 days)
sqlite3 mail_filter.db "
DELETE FROM logs 
WHERE timestamp < date('now', '-30 days');
"

# Clear old temporary files
find . -name "*.tmp" -mtime +7 -delete
find . -name "*.log.*" -mtime +7 -delete

# ML model health check
python -c "
from ensemble_hybrid_classifier import EnsembleHybridClassifier
from binary_feedback_processor import BinaryFeedbackProcessor

# Check model accuracy
classifier = EnsembleHybridClassifier()
print(f'Current accuracy: {classifier.get_accuracy()}%')

# Process any pending feedback
processor = BinaryFeedbackProcessor()
if processor.has_pending_feedback():
    print('Processing user feedback...')
    processor.process_feedback()
    print('Model retraining completed')
else:
    print('No pending feedback to process')
"
```

**Monthly Maintenance**:
```bash
# Deep database optimization
sqlite3 mail_filter.db "
-- Rebuild indexes
REINDEX;

-- Update statistics
ANALYZE;

-- Check database integrity
PRAGMA integrity_check;
"

# Model retraining with accumulated feedback
python -c "
from binary_feedback_processor import BinaryFeedbackProcessor
processor = BinaryFeedbackProcessor()
processor.retrain_models()
print('Monthly model retraining completed')
"
```

---

## 🎛️ Environment Variables Reference

### Core Configuration
```bash
# ML Model Settings
export ML_CONFIDENCE_THRESHOLD=75          # Default spam confidence threshold
export ML_ENTROPY_THRESHOLD=3.2            # Domain entropy for gibberish detection
export ML_DOMAIN_AGE_THRESHOLD=90          # Domain age threshold (days)
export ML_PROVIDER_SPECIFIC=true           # Enable provider-specific optimization

# Provider-Specific Thresholds
export ML_GMAIL_THRESHOLD=85               # Gmail confidence threshold (conservative)
export ML_ICLOUD_THRESHOLD=80              # iCloud confidence threshold
export ML_OUTLOOK_THRESHOLD=75             # Outlook confidence threshold
export ML_YAHOO_THRESHOLD=75               # Yahoo confidence threshold

# Ensemble Model Configuration
export ENSEMBLE_RF_WEIGHT=0.4              # Random Forest weight (40%)
export ENSEMBLE_NB_WEIGHT=0.3              # Naive Bayes weight (30%)
export ENSEMBLE_KEYWORD_WEIGHT=0.3         # Keyword matching weight (30%)
export ENSEMBLE_HIGH_CONFIDENCE=0.85       # High confidence threshold
export ENSEMBLE_REQUIRE_MAJORITY=true      # Require majority consensus

# Hybrid Classifier Settings
export HYBRID_HIGH_CONFIDENCE=0.85         # High confidence threshold
export HYBRID_SPAM_THRESHOLD=0.5           # Binary spam classification threshold
export HYBRID_ENABLE_ENSEMBLE=true         # Enable ensemble processing
export HYBRID_ENABLE_STATS=true            # Enable performance statistics

# Category-Specific Thresholds
export ML_PHISHING_THRESHOLD=90            # Phishing detection (high sensitivity)
export ML_PAYMENT_SCAM_THRESHOLD=85        # Payment scam detection
export ML_HEALTH_SCAM_THRESHOLD=80         # Health scam detection
export ML_ADULT_THRESHOLD=75               # Adult content threshold

# Database Configuration
export DATABASE_URL="sqlite:///mail_filter.db"  # Current SQLite
# export DATABASE_URL="postgresql://user:pass@localhost:5432/email_filter"  # Future PostgreSQL
export DB_CONNECTION_TIMEOUT=30            # Database connection timeout
export DB_MAX_CONNECTIONS=10               # Connection pool size (PostgreSQL)

# Web Application
export WEB_HOST="0.0.0.0"                  # Web app host (all interfaces)
export WEB_PORT=8000                       # Web app port
export WEB_WORKERS=1                       # Uvicorn workers (SQLite requires 1)
export WEB_RELOAD=false                    # Auto-reload (development only)
```

### Production Environment Setup
```bash
# Create environment file
cat > /opt/email-filter/.env << EOF
# Production ML Configuration
ML_CONFIDENCE_THRESHOLD=80
ML_GMAIL_THRESHOLD=85
ML_ICLOUD_THRESHOLD=80
ML_OUTLOOK_THRESHOLD=75

# Production Performance
ENSEMBLE_RF_WEIGHT=0.4
ENSEMBLE_NB_WEIGHT=0.3
ENSEMBLE_KEYWORD_WEIGHT=0.3

# Production Database
DATABASE_URL=sqlite:///opt/email-filter/mail_filter.db
DB_CONNECTION_TIMEOUT=30

# Production Web App
WEB_HOST=127.0.0.1
WEB_PORT=8000
WEB_WORKERS=1
WEB_RELOAD=false
EOF

# Load environment
source /opt/email-filter/.env
```

---

## 🔧 Troubleshooting Common Issues

### Installation Issues

**Dependency Conflicts**:
```bash
# Clean installation
pip uninstall -y scikit-learn numpy matplotlib pandas
pip install --no-cache-dir -r requirements.txt

# Virtual environment (recommended)
python -m venv email_filter_env
source email_filter_env/bin/activate
pip install -r requirements.txt
```

**Python Version Issues**:
```bash
# Check Python version
python --version  # Must be 3.8+

# Use specific Python version
python3.9 -m venv email_filter_env
```

### Configuration Issues

**Email Authentication Failures**:
```bash
# Test provider connection
python -c "
import imaplib
try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login('your_email@gmail.com', 'your_app_password')
    print('Gmail connection: SUCCESS')
    mail.logout()
except Exception as e:
    print(f'Gmail connection: FAILED - {e}')
"
```

**Database Issues**:
```bash
# Check database integrity
sqlite3 mail_filter.db "PRAGMA integrity_check;"

# Reset database (emergency)
mv mail_filter.db mail_filter.db.backup
python main.py  # Will recreate database
```

### Performance Issues

**Slow Processing**:
```bash
# Check batch sizes
python -c "
from settings import EMAIL_PROVIDER_SETTINGS
for provider, settings in EMAIL_PROVIDER_SETTINGS.items():
    print(f'{provider}: batch_size={settings.get(\"batch_size\", \"default\")}')
"

# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

---

## 📞 Support and Resources

### Directory Structure
```
email_project/
├── main.py                    # CLI application entry point
├── web_app.py                 # FastAPI web application
├── settings.py                # Centralized configuration
├── database.py                # Database operations and schema
├── ensemble_hybrid_classifier.py  # Primary ML classifier
├── email_processor.py         # IMAP email processing
├── ml_feature_extractor.py    # ML feature extraction
├── requirements.txt           # Python dependencies
├── mail_filter.db            # SQLite database (17.4MB)
├── webapp.pid                # Web app process ID
├── *.log                     # Application logs
├── *.pkl, *.json            # ML model files
└── tools/                    # Utility scripts and analyzers
```

### Key File Locations
- **Database**: `mail_filter.db` (current: 17.4MB)
- **Configuration**: `settings.py` (centralized)
- **Logs**: `webapp.log`, `web_app_debug.log`
- **Models**: `*.pkl`, `*.json` files
- **Process**: `webapp.pid` (web app process tracking)

### Support Commands
```bash
# System status overview
python -c "
from database import db
from ensemble_hybrid_classifier import EnsembleHybridClassifier

print('=== SYSTEM STATUS ===')
print(f'Database: {db.get_database_stats()}')
print(f'ML Models: Available')
classifier = EnsembleHybridClassifier()
print(f'Accuracy: {classifier.get_accuracy()}%')
print(f'Web App: http://localhost:8000')
"

# Comprehensive health check
curl -s http://localhost:8000/api/accounts | python -m json.tool
```

---

*Built with love by ATLAS & Bobble - Intelligent Email Security Through Expert Deployment* 💖

*Last Updated: June 23, 2025*