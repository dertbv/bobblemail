# Troubleshooting Guide

## Email Project - Comprehensive Troubleshooting Guide

**System Status**: Production-ready with 95.6%+ ML accuracy  
**Common Issues**: Database, IMAP, ML models, configuration  
**Emergency Recovery**: Complete system reset procedures included  

---

## 🩺 Quick Health Check

### System Verification Commands
```bash
# Database integrity check
python3 -c "from database import db; print(db.get_database_stats())"

# ML models verification
python3 tools/verify_ml_enabled.py

# Web app status
cat webapp.pid && curl -s http://localhost:8000/api/accounts

# Provider connection test
python3 -m config_auth
```

### Current System Status Indicators
- **Database**: `mail_filter.db` (17.4MB, schema v5)
- **Web App**: `http://localhost:8000` with webapp.pid file
- **ML Models**: 95.6%+ accuracy with 3-model ensemble
- **Accounts**: 4 configured email accounts

---

## 🗄️ Database Issues

### 1. Database File Path Problems

**Symptoms**:
- `sqlite3.OperationalError: no such table`
- `FileNotFoundError: mail_filter.db`
- Empty or corrupted database

**Common Causes**:
- Database file missing from expected location
- Working directory path inconsistencies (FIXED in recent refactor)
- File permissions issues
- Corrupted database file

**Solutions**:

```bash
# Verify database location and permissions
ls -la /Users/Badman/Desktop/email/REPOS/email_project/mail_filter.db
chmod 644 mail_filter.db

# Check database integrity
sqlite3 mail_filter.db "PRAGMA integrity_check;"

# Emergency database recreation
mv mail_filter.db mail_filter.db.backup
# Restart application - will recreate schema
```

**Recent Fix**: All database path issues resolved with centralized absolute path resolution in 8 critical files.

### 2. Schema Version Mismatch

**Symptoms**:
- `sqlite3.OperationalError: no such column`
- Schema migration failures
- Missing table errors

**Diagnosis**:
```sql
-- Check current schema version
SELECT version FROM schema_version ORDER BY id DESC LIMIT 1;
-- Should return: 5 (latest)
```

**Solutions**:
- **Automatic Migration**: System auto-upgrades from v1-v4 to v5
- **Manual Recovery**: Delete database to force recreation with latest schema
- **Backup First**: Always backup before schema changes

### 3. Database Locking Issues

**Symptoms**:
- `sqlite3.OperationalError: database is locked`
- Connection timeouts
- Hanging database operations

**Common Causes**:
- Multiple application instances running
- Incomplete transactions
- Zombie processes holding connections

**Solutions**:
```bash
# Check for multiple instances
ps aux | grep python | grep email

# Kill zombie processes
pkill -f "python.*email"

# Clear any webapp.pid locks
rm -f webapp.pid

# Database unlock (emergency)
sqlite3 mail_filter.db ".timeout 30000" "BEGIN IMMEDIATE; ROLLBACK;"
```

---

## 📧 Email Provider Connection Issues

### 1. IMAP Authentication Failures

**Symptoms**:
- `imaplib.IMAP4.error: [AUTHENTICATIONFAILED]`
- Connection refused by provider
- "Invalid credentials" errors

**Provider-Specific Solutions**:

#### **Gmail Configuration**
```python
# Gmail requires App Password (not regular password)
host = 'imap.gmail.com'
port = 993
# Steps:
# 1. Enable 2FA on Google Account
# 2. Generate App Password: myaccount.google.com/apppasswords
# 3. Use App Password in configuration
```

#### **iCloud Configuration**
```python
# iCloud requires App-Specific Password
host = 'imap.mail.me.com'  
port = 993
# Steps:
# 1. Go to appleid.apple.com
# 2. Generate App-Specific Password
# 3. Use generated password in configuration
```

#### **Outlook/Hotmail Configuration**
```python
# Outlook requires OAuth or App Password
host = 'outlook.office365.com'
port = 993
# Modern Auth required for new connections
```

### 2. Connection Timeout Issues

**Symptoms**:
- `socket.timeout` exceptions
- Very slow IMAP responses
- Processing hangs on large mailboxes

**Optimized Provider Settings** (built into system):
```python
# Provider-specific batch sizes (email_processor.py)
PROVIDER_OPTIMIZATIONS = {
    'icloud': {'batch_size': 25, 'delay': 0.1},
    'gmail': {'batch_size': 50, 'delay': 0.05}, 
    'outlook': {'batch_size': 30, 'delay': 0.1}
}
```

**Solutions**:
- **Reduce Batch Size**: Smaller chunks for slow providers
- **Implement Delays**: Prevent provider throttling
- **Use UID Operations**: More efficient than sequence numbers
- **Connection Pooling**: Reuse IMAP connections

### 3. Folder Selection Problems

**Symptoms**:
- `imaplib.IMAP4.error: SELECT failed`
- "Folder not found" errors
- Localized folder name issues

**Provider-Specific Folder Names**:
| Provider | Spam Folder | Sent Folder | Trash Folder |
|----------|-------------|-------------|--------------|
| **Gmail** | `[Gmail]/Spam` | `[Gmail]/Sent Mail` | `[Gmail]/Trash` |
| **iCloud** | `Junk` | `Sent Messages` | `Deleted Messages` |
| **Outlook** | `Junk Email` | `Sent Items` | `Deleted Items` |

**Diagnostic Commands**:
```python
# List all folders for debugging
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(username, password)
print(mail.list())
```

---

## 🤖 Machine Learning Issues

### 1. Model Loading Failures

**Symptoms**:
- `FileNotFoundError: random_forest_model.pkl`
- Classification returning default values
- Model accuracy suddenly drops

**Required Model Files**:
```
REPOS/email_project/
├── random_forest_model.pkl (40% ensemble weight)
├── naive_bayes_model.json (30% ensemble weight)  
├── ml_category_classifier.json (category classification)
└── ml_category_classifier_scaler.pkl (feature scaling)
```

**Solutions**:
```bash
# Verify model files exist
ls -la *.pkl *.json | grep -E "(random_forest|naive_bayes|category)"

# Check model loading in Python
python3 -c "
from ensemble_hybrid_classifier import EnsembleHybridClassifier
classifier = EnsembleHybridClassifier()
print(f'Models loaded: {classifier.models_loaded}')
"

# Retrain models if corrupted
python3 -c "
from binary_feedback_processor import BinaryFeedbackProcessor
processor = BinaryFeedbackProcessor()
processor.retrain_models()
"
```

### 2. Classification Accuracy Issues

**Symptoms**:
- Too many false positives (legitimate emails marked spam)
- Too many false negatives (spam emails preserved)
- Confidence scores consistently low

**Provider-Specific Confidence Thresholds** (in `settings.py`):
```python
ML_CONFIDENCE_THRESHOLDS = {
    'gmail': 85,    # Higher threshold (more conservative)
    'icloud': 80,   # Medium threshold
    'outlook': 75,  # Lower threshold (more aggressive)
    'default': 75
}
```

**Adjustment Guidelines**:
- **Too Many False Positives**: Lower threshold by 5-10%
- **Too Many False Negatives**: Raise threshold by 5-10%
- **Monitor Results**: Use web interface analytics to track changes

### 3. Feature Extraction Problems

**Symptoms**:
- `UnicodeDecodeError` during processing
- Empty feature vectors
- Encoding-related crashes

**Robust Encoding Solution** (implemented in `ml_feature_extractor.py`):
```python
def safe_decode(raw_data):
    """Robust encoding with multiple fallbacks"""
    encodings = ['utf-8', 'iso-8859-1', 'ascii', 'cp1252', 'latin1']
    for encoding in encodings:
        try:
            return raw_data.decode(encoding, errors="ignore")
        except (UnicodeDecodeError, LookupError):
            continue
    return str(raw_data, errors="replace")  # Final fallback
```

---

## ⚙️ Configuration Issues

### 1. Missing Configuration Files

**Symptoms**:
- "Configuration not found" errors
- Default settings always used
- Credentials not persisting

**Current Configuration System**:
- **Centralized**: All settings in `settings.py` (no JSON files)
- **Database Storage**: Credentials encrypted in `accounts` table
- **Environment Override**: Use env vars for customization

**Recovery Steps**:
```bash
# Check configuration loading
python3 -c "from settings import *; print(f'DB: {DB_FILE}, ML: {ML_SETTINGS}')"

# Reset to defaults
python3 -c "
import os
# Clear problematic environment variables
for key in os.environ:
    if key.startswith('ML_') or key.startswith('EMAIL_'):
        del os.environ[key]
"
```

### 2. Environment Variable Issues

**Available Environment Overrides**:
```bash
# ML Configuration
export ML_CONFIDENCE_THRESHOLD=75
export ML_GMAIL_THRESHOLD=85
export ML_ICLOUD_THRESHOLD=80

# Ensemble Weights  
export ENSEMBLE_NB_WEIGHT=0.3
export ENSEMBLE_RF_WEIGHT=0.4
export ENSEMBLE_KW_WEIGHT=0.3

# Performance Tuning
export EMAIL_BATCH_SIZE=50
export ML_ENTROPY_THRESHOLD=3.2
```

### 3. Import Dependency Issues (RESOLVED)

**Previous Symptoms**:
- `ImportError: cannot import name`
- Circular import errors
- Module resolution failures

**Fixed in Recent Refactor**:
- ✅ Created `classification_utils.py` bridge module
- ✅ Created `config_loader.py` bridge module  
- ✅ Eliminated all circular dependencies
- ✅ Clean module boundaries established

---

## 🌐 Web Interface Issues

### 1. FastAPI Service Problems

**Symptoms**:
- `ImportError: fastapi` or `ImportError: uvicorn`
- Web interface not responding
- API endpoints return 500 errors

**Dependencies Check**:
```bash
# Install required packages
pip install fastapi uvicorn

# Verify web app can start
python3 web_app.py
# Should show: "Uvicorn running on http://localhost:8000"
```

### 2. Memory Issues in Web App

**Symptoms**:
- High memory usage over time
- Slow web interface responses
- Browser timeouts

**Memory Optimization**:
```python
# Clear classifier cache periodically (implemented)
def clear_classifier_cache():
    global ensemble_classifier
    if ensemble_classifier:
        del ensemble_classifier
        ensemble_classifier = None

# Database query optimization (implemented)
def get_emails_paginated(limit=100, offset=0):
    return db.execute(
        "SELECT * FROM processed_emails_bulletproof "
        "ORDER BY timestamp DESC LIMIT ? OFFSET ?", 
        (limit, offset)
    )
```

### 3. Port Conflicts

**Symptoms**:
- `Address already in use` on port 8000
- Cannot start web interface
- Connection refused errors

**Solutions**:
```bash
# Check what's using port 8000
lsof -i :8000

# Kill existing process
kill $(lsof -t -i:8000)

# Alternative port (if needed)
python3 web_app.py --port 8001
```

---

## 🚀 Performance Issues

### 1. Slow Email Processing

**Symptoms**:
- Processing takes hours for large mailboxes
- Frequent timeouts
- High CPU usage

**Performance Optimizations** (implemented):

```python
# Provider-specific batch processing
BATCH_SIZES = {
    'gmail': 50,     # Google handles larger batches well
    'icloud': 25,    # Apple more conservative
    'outlook': 30    # Microsoft moderate
}

# Parallel processing for multiple accounts
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(process_account, account) for account in accounts]
```

### 2. Memory Leaks

**Symptoms**:
- Memory usage grows over time
- Application becomes unresponsive
- OS memory pressure warnings

**Memory Management** (implemented):
```python
# Clear large objects after use
def process_emails_batch(emails):
    features = extract_features(emails)
    results = classify_batch(features)
    
    # Explicit cleanup
    del features
    del emails
    gc.collect()
    
    return results
```

### 3. Database Performance

**Symptoms**:
- Slow web interface queries
- Long application startup
- Database locks

**Optimization Strategies** (implemented):
- **Indexes**: Strategic indexing on timestamp, action, session_id
- **Query Limits**: Pagination for large result sets
- **Connection Pooling**: Reuse database connections
- **Vacuum**: Periodic database optimization

```sql
-- Performance monitoring queries
SELECT COUNT(*) FROM processed_emails_bulletproof;  -- 12,238 emails
SELECT COUNT(*) FROM sessions;                       -- 634 sessions
SELECT COUNT(*) FROM logs;                          -- 9,112 logs

-- Index usage verification
EXPLAIN QUERY PLAN SELECT * FROM processed_emails_bulletproof 
WHERE timestamp > '2025-06-01' ORDER BY timestamp DESC;
```

---

## 🔍 Domain Validation Issues

### 1. DNS Resolution Problems

**Symptoms**:
- Domain validation failures
- DNS timeout errors
- False positives on legitimate domains

**DNS Configuration** (implemented):
```python
# Multiple DNS servers with fallback
DNS_SERVERS = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
DNS_TIMEOUT = 3  # seconds
DNS_CACHE_TTL = 86400  # 24 hours
```

### 2. Gibberish Detection Issues

**Symptoms**:
- Legitimate domains flagged as suspicious
- International domains failing validation
- Entropy calculation errors

**Current Settings**:
```python
# Entropy threshold for gibberish detection
ML_ENTROPY_THRESHOLD = 3.2  # Balanced setting

# Whitelist bypass for known domains
LEGITIMATE_DOMAINS = [
    'unraid.net', 'inova.org', 'aetna.com', 
    'dertbv@gmail.com', 'genesismotorsamerica.com'
]
```

**Adjustment Guidelines**:
- **Too Aggressive**: Increase threshold to 3.5-4.0
- **Too Permissive**: Decrease threshold to 2.8-3.0
- **Add Whitelists**: For known legitimate domains

---

## 🆘 Emergency Recovery Procedures

### Complete System Reset

**When to Use**:
- Multiple system failures
- Corrupted database
- Configuration completely broken
- Major version upgrade issues

**Steps**:
```bash
# 1. Create backup
cp mail_filter.db mail_filter.db.emergency_backup
cp -r . ../email_project_backup

# 2. Reset database
rm mail_filter.db
rm -f webapp.pid

# 3. Clear environment
unset $(env | grep -E '^(ML_|EMAIL_|ENSEMBLE_)' | cut -d= -f1)

# 4. Restart application
python3 main.py
# Follow setup wizard to reconfigure accounts

# 5. Retrain ML models
python3 -c "
from binary_feedback_processor import BinaryFeedbackProcessor
processor = BinaryFeedbackProcessor()
processor.retrain_models()
"
```

### Configuration Recovery

**Partial Reset** (preserve data):
```bash
# Reset configuration only
python3 -c "
from database import db
db.execute('DELETE FROM configurations WHERE config_type != \"ACCOUNT\"')
"

# Restart with defaults
python3 main.py
```

### Model Recovery

**Retrain All Models**:
```python
from binary_feedback_processor import BinaryFeedbackProcessor
from ensemble_hybrid_classifier import EnsembleHybridClassifier

# Retrain from database
processor = BinaryFeedbackProcessor()
processor.retrain_models()

# Verify ensemble loading
classifier = EnsembleHybridClassifier()
print(f"Models loaded successfully: {classifier.models_loaded}")
```

---

## 📊 Monitoring and Prevention

### Health Monitoring Dashboard

**Key Metrics to Watch**:
- Classification accuracy (target: >95%)
- Processing speed (target: <100ms/email)
- Database size (current: 17.4MB)
- Memory usage (target: <200MB)
- Error rates (target: <1%)

**Web Interface Monitoring**:
- Visit `http://localhost:8000/analytics` for performance metrics
- Check `/api/user-stats` for classification statistics
- Monitor `/api/feedback/stats` for user correction patterns

### Regular Maintenance Tasks

**Weekly**:
```bash
# Database health check
python3 -c "from database import db; print(db.get_database_stats())"

# Clear old logs (optional)
sqlite3 mail_filter.db "DELETE FROM logs WHERE timestamp < date('now', '-30 days')"

# Verify ML model performance
python3 tools/verify_ml_enabled.py
```

**Monthly**:
```bash
# Database optimization
sqlite3 mail_filter.db "VACUUM; ANALYZE;"

# Model retraining with accumulated feedback
python3 -c "
from binary_feedback_processor import BinaryFeedbackProcessor
processor = BinaryFeedbackProcessor()
processor.retrain_models()
"
```

### Prevention Best Practices

1. **Regular Backups**: Database and configuration
2. **Monitor Logs**: Check for recurring error patterns
3. **Update Feedback**: Provide user feedback for misclassifications
4. **Performance Monitoring**: Watch for degradation trends
5. **Provider Changes**: Stay updated on email provider authentication changes

---

## 📞 Getting Help

### Debug Information to Collect

When reporting issues:
```bash
# System information
python3 --version
pip list | grep -E "(fastapi|sqlite|scikit|numpy)"

# Database status
python3 -c "from database import db; print(db.get_database_stats())"

# ML model status
ls -la *.pkl *.json

# Recent errors
sqlite3 mail_filter.db "SELECT * FROM logs WHERE level='ERROR' ORDER BY timestamp DESC LIMIT 10"
```

### Log Analysis

**Important Log Categories**:
- `SESSION`: Processing session errors
- `EMAIL`: Individual email processing issues
- `DOMAIN`: Domain validation problems
- `ML`: Machine learning classification issues
- `CONFIG`: Configuration loading problems

**Common Error Patterns**:
- Database connection failures
- IMAP authentication issues
- Model loading problems
- Feature extraction errors
- Memory pressure warnings

---

*Built with love by ATLAS & Bobble - Reliable Email Security Through Intelligent Troubleshooting* 💖

*Last Updated: June 23, 2025*