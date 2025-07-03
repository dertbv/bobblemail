# ATLAS EMAIL TROUBLESHOOTING GUIDE

## EXECUTIVE SUMMARY

This comprehensive troubleshooting guide covers common issues, diagnostic procedures, and solutions for the Atlas_Email system. Organized by functional area with step-by-step resolution procedures and prevention strategies.

**TROUBLESHOOTING SCOPE**:
- **Email Processing Issues**: IMAP connection, authentication, processing failures
- **ML Classification Problems**: Model loading, accuracy issues, training failures  
- **Database Issues**: Connection errors, schema problems, performance issues
- **Geographic Intelligence**: IP extraction, GeoIP lookup failures
- **Web Interface Problems**: API errors, template issues, performance
- **Configuration Issues**: Settings, credentials, environment setup

## QUICK DIAGNOSTIC CHECKLIST

### System Health Check (Run First)
```bash
# 1. Check database connectivity
python3 -c "from atlas_email.models.database import db; print('DB OK:', db.test_connection())"

# 2. Verify ML models
python3 -c "from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier; c = EnsembleHybridClassifier(); print('ML OK')"

# 3. Test geographic intelligence
python3 -c "from atlas_email.core.geographic_intelligence import GeographicIntelligenceProcessor; g = GeographicIntelligenceProcessor(); print('Geo OK')"

# 4. Check web server
curl -f http://localhost:8000/ || echo "Web server not responding"

# 5. Verify email research tool
cd /Users/Badman/Desktop/email/REPOS/Atlas_Email && python3 tools/analyzers/email_classification_analyzer.py
```

## EMAIL PROCESSING ISSUES

### IMAP Connection Failures

#### **Problem**: "IMAP connection failed" or "Authentication error"
```bash
# Error patterns
Error: LOGIN failed
Error: [AUTHENTICATIONFAILED] Invalid credentials
Error: Connection timed out
```

**Diagnosis Steps**:
```python
# Test IMAP connection manually
import imaplib
try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login('email@gmail.com', 'password')
    print("✅ IMAP connection successful")
except Exception as e:
    print(f"❌ IMAP error: {e}")
```

**Solutions**:
1. **Gmail App Passwords**:
   ```bash
   # Gmail requires app-specific passwords
   # Generate at: https://security.google.com/settings/security/apppasswords
   # Use app password instead of account password
   ```

2. **iCloud 2FA Issues**:
   ```bash
   # iCloud requires app-specific passwords
   # Generate at: https://appleid.apple.com/account/manage
   # Use format: xxxx-xxxx-xxxx-xxxx
   ```

3. **Connection Timeouts**:
   ```python
   # Increase timeout in provider settings
   provider_settings = {
       'connection_timeout': 30,  # Increase from default 10
       'read_timeout': 60,        # Increase from default 30
       'retry_attempts': 3        # Add retry logic
   }
   ```

#### **Problem**: "Folder not found" or "Permission denied"
**Solutions**:
```python
# List available folders
mail.list()
# Common folder names by provider:
# Gmail: '[Gmail]/Spam', '[Gmail]/Trash' 
# iCloud: 'Junk', 'Deleted Messages'
# Outlook: 'Junk Email', 'Deleted Items'
```

### Email Processing Performance Issues

#### **Problem**: Very slow email processing (> 5 seconds per email)
**Diagnosis**:
```sql
-- Check processing performance
SELECT 
    operation_type,
    AVG(duration_seconds) as avg_duration,
    MAX(duration_seconds) as max_duration,
    COUNT(*) as operations
FROM performance_metrics 
WHERE timestamp > datetime('now', '-1 hour')
GROUP BY operation_type;
```

**Solutions**:
1. **Optimize batch sizes**:
   ```python
   # Reduce batch size for slow providers
   provider_settings = {
       'icloud': {'batch_size': 15},    # Down from 25
       'gmail': {'batch_size': 30},     # Down from 50
       'outlook': {'batch_size': 20}    # Down from 30
   }
   ```

2. **Enable provider optimizations**:
   ```python
   # iCloud bulk operations
   'icloud': {
       'use_bulk_operations': True,
       'skip_individual_marking': True
   }
   ```

## MACHINE LEARNING CLASSIFICATION ISSUES

### Model Loading Failures

#### **Problem**: "Model file not found" or "Model loading failed"
```bash
# Error patterns
FileNotFoundError: naive_bayes_model.json not found
AttributeError: 'NoneType' object has no attribute 'predict'
```

**Diagnosis**:
```bash
# Check model files
ls -la data/models/
find . -name "*.json" -o -name "*.pkl" | grep -E "(naive|forest|model)"
```

**Solutions**:
1. **Initialize missing models**:
   ```python
   # Force model retraining
   from atlas_email.ml.naive_bayes import NaiveBayesClassifier
   from atlas_email.ml.random_forest import ProductionRandomForestClassifier
   
   nb = NaiveBayesClassifier()
   nb.initialize_model()  # Creates default model
   
   rf = ProductionRandomForestClassifier()
   rf.initialize_model()  # Creates default model
   ```

2. **Model corruption recovery**:
   ```bash
   # Backup and recreate models
   mv data/models/ data/models_backup/
   mkdir -p data/models/
   python3 -c "from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier; EnsembleHybridClassifier()"
   ```

### Classification Accuracy Problems

#### **Problem**: High false positive rate (legitimate emails marked as spam)
**Diagnosis**:
```sql
-- Check false positive patterns
SELECT 
    sender_domain,
    category,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM processed_emails_bulletproof 
WHERE action = 'DELETED' 
  AND user_validated = -1  -- Thumbs down
GROUP BY sender_domain, category
ORDER BY count DESC;
```

**Solutions**:
1. **Add domain to whitelist**:
   ```sql
   INSERT INTO domains (domain, is_whitelisted, notes) 
   VALUES ('legitimate-domain.com', TRUE, 'User confirmed legitimate');
   ```

2. **Adjust confidence thresholds**:
   ```python
   # Lower confidence threshold for borderline cases
   classification_config = {
       'high_confidence_threshold': 0.8,  # Up from 0.7
       'low_confidence_threshold': 0.3    # Down from 0.4
   }
   ```

3. **Retrain with feedback**:
   ```bash
   # Process user feedback for model improvement
   python3 -c "from atlas_email.ml.feedback_processor import BinaryFeedbackProcessor; BinaryFeedbackProcessor().process_all_unprocessed_feedback()"
   ```

## DATABASE ISSUES

### Database Connection Problems

#### **Problem**: "Database locked" or "Database is locked"
```bash
# Error patterns
sqlite3.OperationalError: database is locked
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions**:
1. **Release database locks**:
   ```bash
   # Find processes using database
   lsof data/mail_filter.db
   
   # Kill blocking processes if safe
   pkill -f "atlas_email"
   pkill -f "mail_filter"
   ```

2. **Database integrity check**:
   ```bash
   # Check database integrity
   sqlite3 data/mail_filter.db "PRAGMA integrity_check;"
   
   # Vacuum database to fix minor corruption
   sqlite3 data/mail_filter.db "VACUUM;"
   ```

3. **Database recovery**:
   ```bash
   # Backup current database
   cp data/mail_filter.db data/mail_filter.db.backup
   
   # Dump and restore
   sqlite3 data/mail_filter.db .dump > backup.sql
   rm data/mail_filter.db
   sqlite3 data/mail_filter.db < backup.sql
   ```

### Schema Migration Issues

#### **Problem**: "Table doesn't exist" or "Column not found"
**Solutions**:
```sql
-- Check current schema version
SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;

-- Add missing columns (example for geographic columns)
ALTER TABLE processed_emails_bulletproof ADD COLUMN sender_ip TEXT;
ALTER TABLE processed_emails_bulletproof ADD COLUMN sender_country_code TEXT;
ALTER TABLE processed_emails_bulletproof ADD COLUMN sender_country_name TEXT;
ALTER TABLE processed_emails_bulletproof ADD COLUMN geographic_risk_score REAL;
ALTER TABLE processed_emails_bulletproof ADD COLUMN detection_method TEXT;

-- Update schema version
INSERT INTO schema_version (version) VALUES (5);
```

## GEOGRAPHIC INTELLIGENCE ISSUES

### GeoIP Lookup Failures

#### **Problem**: "Geographic lookup failed" or "GeoIP database not found"
**Diagnosis**:
```python
# Test GeoIP functionality
from atlas_email.core.geographic_intelligence import GeographicIntelligenceProcessor
processor = GeographicIntelligenceProcessor()

# Test with known IP
result = processor.get_geographic_data("8.8.8.8")
print(f"Result: {result}")
```

**Solutions**:
1. **Install/update GeoIP2Fast**:
   ```bash
   pip install --upgrade geoip2fast
   python3 -c "import geoip2fast; print('GeoIP2Fast version:', geoip2fast.__version__)"
   ```

2. **Handle lookup failures gracefully**:
   ```python
   # Fallback when GeoIP fails
   try:
       geo_data = processor.get_geographic_data(ip_address)
   except Exception as e:
       geo_data = GeographicData(
           sender_ip=ip_address,
           detection_method="GEOIP_LOOKUP_ERROR",
           geographic_risk_score=0.35  # Default moderate risk
       )
   ```

### IP Extraction Issues

#### **Problem**: "No external IP found" for emails with geographic data
**Diagnosis**:
```python
# Debug IP extraction
processor = GeographicIntelligenceProcessor()
headers = "Received: from mail.example.com [203.0.113.123] by ..."

ip = processor.extract_ip_from_headers(headers)
print(f"Extracted IP: {ip}")

# Check private IP filtering
print(f"Is external: {processor._is_external_ip(ip)}")
```

**Solutions**:
```python
# Enhance IP extraction patterns
additional_patterns = [
    r'X-Originating-IP:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
    r'X-Sender-IP:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
    r'X-Real-IP:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
]
```

## WEB INTERFACE ISSUES

### FastAPI Server Problems

#### **Problem**: "Internal Server Error" or "500 Error"
**Diagnosis**:
```bash
# Check server logs
tail -f logs/webapp.log

# Test specific endpoints
curl -v http://localhost:8000/api/user-stats
curl -v http://localhost:8000/analytics
```

**Solutions**:
1. **Restart with debug mode**:
   ```bash
   # Kill existing server
   pkill -f uvicorn
   
   # Start with debug logging
   cd src/atlas_email/api
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level debug
   ```

2. **Template issues**:
   ```bash
   # Check template directory
   ls -la src/atlas_email/api/templates/
   
   # Verify template syntax
   python3 -c "from jinja2 import Template; Template(open('templates/pages/analytics.html').read())"
   ```

### Analytics Dashboard Problems

#### **Problem**: "No data displayed" or "Chart not loading"
**Solutions**:
```sql
-- Verify analytics data exists
SELECT COUNT(*) FROM processed_emails_bulletproof WHERE timestamp > datetime('now', '-30 days');

-- Check geographic data
SELECT COUNT(*) FROM processed_emails_bulletproof WHERE sender_country_code IS NOT NULL;

-- Verify sessions
SELECT COUNT(*) FROM sessions WHERE start_time > datetime('now', '-30 days');
```

## CONFIGURATION ISSUES

### Missing Configuration Files

#### **Problem**: "Config file not found" or "Settings not loaded"
**Solutions**:
```bash
# Create missing config directories
mkdir -p config data logs

# Initialize default settings
cat > config/settings.py << 'EOF'
class Settings:
    @staticmethod
    def get_hybrid_config():
        return {
            'confidence_threshold': 0.7,
            'enable_geographic': True,
            'enable_strategic': True
        }
EOF
```

### Credential Issues

#### **Problem**: "Database credentials not found"
**Solutions**:
```python
# Create credentials file
cat > config/credentials.py << 'EOF'
db_credentials = {
    'database_path': 'data/mail_filter.db',
    'backup_path': 'data/backup/',
    'log_level': 'INFO'
}
EOF
```

## PERFORMANCE OPTIMIZATION

### Memory Issues

#### **Problem**: High memory usage or "Out of memory" errors
**Solutions**:
```python
# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Optimize batch processing
batch_config = {
    'max_emails_per_batch': 25,  # Reduce from 50
    'memory_threshold_mb': 500,  # Stop if memory exceeds
    'gc_frequency': 10           # Garbage collect every 10 emails
}
```

### Database Performance

#### **Problem**: Slow database queries
**Solutions**:
```sql
-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_processed_timestamp 
    ON processed_emails_bulletproof(timestamp);
CREATE INDEX IF NOT EXISTS idx_processed_country 
    ON processed_emails_bulletproof(sender_country_code);

-- Analyze query performance
EXPLAIN QUERY PLAN SELECT * FROM processed_emails_bulletproof 
WHERE timestamp > datetime('now', '-30 days');

-- Database maintenance
VACUUM;
ANALYZE;
```

## EMERGENCY RECOVERY PROCEDURES

### Complete System Reset

#### **When**: System completely broken, multiple component failures
```bash
# 1. Backup current state
mkdir -p recovery/$(date +%Y%m%d_%H%M%S)
cp -r data/ recovery/$(date +%Y%m%d_%H%M%S)/
cp -r config/ recovery/$(date +%Y%m%d_%H%M%S)/

# 2. Stop all processes
pkill -f atlas_email
pkill -f uvicorn
pkill -f mail_filter

# 3. Reset database (DESTRUCTIVE)
mv data/mail_filter.db data/mail_filter.db.broken
python3 -c "from atlas_email.models.database import db; db.initialize_database()"

# 4. Reinitialize ML models
python3 -c "from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier; EnsembleHybridClassifier()"

# 5. Test basic functionality
python3 tools/analyzers/email_classification_analyzer.py
```

### Rollback to Previous Version

#### **When**: New deployment broke the system
```bash
# 1. Stop current services
pkill -f atlas_email

# 2. Restore from backup
cp data/backup/mail_filter.db.last_good data/mail_filter.db

# 3. Restore previous models
cp -r data/models_backup/ data/models/

# 4. Restart services
cd src/atlas_email/api && uvicorn app:app --host 0.0.0.0 --port 8000
```

## PREVENTION STRATEGIES

### Monitoring Setup
```bash
# 1. Setup log rotation
echo "/path/to/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}" > /etc/logrotate.d/atlas_email

# 2. Database backup automation
echo "0 2 * * * cp data/mail_filter.db data/backup/mail_filter_$(date +\%Y\%m\%d).db" | crontab -

# 3. Health check script
cat > monitor.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/ || echo "Web server down"
python3 -c "from atlas_email.models.database import db; db.test_connection()" || echo "Database issue"
EOF
```

### Regular Maintenance
```bash
# Weekly maintenance script
#!/bin/bash
# Database maintenance
sqlite3 data/mail_filter.db "VACUUM; ANALYZE;"

# Log cleanup
find logs/ -name "*.log" -mtime +30 -delete

# Model performance check
python3 -c "from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier; c = EnsembleHybridClassifier(); print('Models OK')"
```

This troubleshooting guide provides systematic approaches to diagnose and resolve common Atlas_Email issues with preventive measures to avoid future problems.

---
*Troubleshooting Guide - Version 1.0*  
*Generated: 2025-07-03*  
*Status: Production Ready*