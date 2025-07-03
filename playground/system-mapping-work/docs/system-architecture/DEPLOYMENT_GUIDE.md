# ATLAS EMAIL DEPLOYMENT GUIDE

## EXECUTIVE SUMMARY

This comprehensive deployment guide covers setup procedures for Atlas_Email from development environment to production deployment. Includes system requirements, installation procedures, configuration management, security hardening, and operational maintenance.

**DEPLOYMENT SCOPE**:
- **Development Setup**: Local development environment configuration
- **Staging Deployment**: Testing and validation environment
- **Production Deployment**: Enterprise-grade production setup
- **Security Hardening**: Production security best practices
- **Monitoring Setup**: Operational monitoring and alerting
- **Backup Strategy**: Data protection and disaster recovery

## SYSTEM REQUIREMENTS

### Hardware Requirements

#### **Minimum Requirements (Development/Testing)**
```
CPU: 2 cores, 2.0 GHz
RAM: 4 GB
Storage: 20 GB available space
Network: Stable internet connection for IMAP access
```

#### **Recommended Requirements (Production)**
```
CPU: 4+ cores, 3.0+ GHz
RAM: 8+ GB (16 GB recommended for high volume)
Storage: 100+ GB SSD with backup storage
Network: High-speed internet with redundant connections
```

#### **High-Volume Requirements (Enterprise)**
```
CPU: 8+ cores, 3.5+ GHz
RAM: 32+ GB
Storage: 500+ GB NVMe SSD with RAID configuration
Network: Dedicated bandwidth with failover
Load Balancer: For multi-instance deployment
```

### Software Requirements

#### **Operating System Support**
```bash
# Primary support
Ubuntu 20.04+ LTS
CentOS 8+
macOS 11+ (development)
Windows 10+ (development only)

# Container support
Docker 20.10+
Kubernetes 1.21+ (for enterprise deployment)
```

#### **Runtime Dependencies**
```bash
# Core requirements
Python 3.8+ (3.9+ recommended)
SQLite 3.30+
Git 2.20+

# System libraries
libssl-dev      # SSL/TLS support
libffi-dev      # Cryptographic functions
libjpeg-dev     # Image processing (optional)
libxml2-dev     # XML processing
libxslt-dev     # XSLT processing
```

## INSTALLATION PROCEDURES

### 1. Development Environment Setup

#### **Quick Start Installation**
```bash
# 1. System preparation
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git sqlite3 -y

# 2. Clone repository
git clone https://github.com/your-org/atlas_email.git
cd atlas_email

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 5. Install development dependencies (optional)
pip install -r requirements-dev.txt

# 6. Initialize database
python3 -c "from atlas_email.models.database import db; db.initialize_database()"

# 7. Create configuration files
cp config/settings.py.example config/settings.py
cp config/credentials.py.example config/credentials.py

# 8. Test installation
python3 tools/analyzers/email_classification_analyzer.py
```

#### **Development Configuration**
```python
# config/settings.py - Development settings
class Settings:
    @staticmethod
    def get_development_config():
        return {
            'debug': True,
            'log_level': 'DEBUG',
            'database_path': 'data/mail_filter_dev.db',
            'enable_hot_reload': True,
            'mock_external_services': True,
            'detailed_error_pages': True
        }
```

### 2. Staging Environment Setup

#### **Staging Server Preparation**
```bash
# 1. Server setup (Ubuntu 20.04+)
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# 2. Create application user
sudo useradd -m -s /bin/bash atlas_email
sudo usermod -aG sudo atlas_email

# 3. Application directory setup
sudo mkdir -p /opt/atlas_email
sudo chown atlas_email:atlas_email /opt/atlas_email
sudo -u atlas_email bash

# 4. Application installation
cd /opt/atlas_email
git clone https://github.com/your-org/atlas_email.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Directory structure creation
mkdir -p data logs backup config
chmod 750 data logs backup
```

#### **Staging Configuration**
```python
# config/settings.py - Staging settings
staging_config = {
    'debug': False,
    'log_level': 'INFO',
    'database_path': '/opt/atlas_email/data/mail_filter.db',
    'log_path': '/opt/atlas_email/logs/',
    'backup_path': '/opt/atlas_email/backup/',
    'enable_performance_monitoring': True,
    'rate_limiting': True,
    'cors_origins': ['https://staging.yourdomain.com']
}
```

#### **Nginx Configuration for Staging**
```nginx
# /etc/nginx/sites-available/atlas_email_staging
server {
    listen 80;
    server_name staging.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/staging.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Static files
    location /static {
        alias /opt/atlas_email/src/atlas_email/api/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

### 3. Production Deployment

#### **Production Server Setup**
```bash
# 1. Security hardening
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# 2. System optimization
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 3. Application user with restricted permissions
sudo useradd -r -s /bin/false atlas_email
sudo mkdir -p /opt/atlas_email /var/log/atlas_email
sudo chown atlas_email:atlas_email /opt/atlas_email /var/log/atlas_email
```

#### **Production Installation**
```bash
# 1. Application deployment
sudo -u atlas_email bash
cd /opt/atlas_email
git clone --branch production https://github.com/your-org/atlas_email.git .
python3 -m venv venv
source venv/bin/activate
pip install --no-dev -r requirements.txt

# 2. Production directory structure
mkdir -p data/{main,backup} logs/{app,access,error} config
chmod 700 data config
chmod 755 logs

# 3. Database initialization with production data
python3 scripts/init_production_db.py

# 4. Configuration deployment
cp production/config/* config/
chmod 600 config/credentials.py
```

#### **Production Configuration**
```python
# config/settings.py - Production settings
production_config = {
    'debug': False,
    'log_level': 'WARNING',
    'database_path': '/opt/atlas_email/data/main/mail_filter.db',
    'backup_database_path': '/opt/atlas_email/data/backup/',
    'log_path': '/var/log/atlas_email/',
    
    # Security settings
    'ssl_verification': True,
    'csrf_protection': True,
    'secure_cookies': True,
    'session_timeout': 7200,  # 2 hours
    
    # Performance settings
    'connection_pool_size': 20,
    'max_workers': 4,
    'request_timeout': 30,
    'rate_limit_per_hour': 1000,
    
    # Monitoring
    'enable_metrics': True,
    'metrics_endpoint': '/metrics',
    'health_check_interval': 30
}
```

#### **Supervisor Configuration**
```ini
# /etc/supervisor/conf.d/atlas_email.conf
[program:atlas_email]
command=/opt/atlas_email/venv/bin/uvicorn atlas_email.api.app:app --host 127.0.0.1 --port 8000 --workers 4
directory=/opt/atlas_email/src
user=atlas_email
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/atlas_email/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=ATLAS_ENV="production",ATLAS_CONFIG="/opt/atlas_email/config/settings.py"

[program:atlas_email_worker]
command=/opt/atlas_email/venv/bin/python -m atlas_email.workers.batch_processor
directory=/opt/atlas_email/src
user=atlas_email
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/atlas_email/worker.log
```

## SECURITY HARDENING

### SSL/TLS Configuration
```bash
# 1. Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y

# 2. Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 3. Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Database Security
```python
# config/security.py
database_security = {
    # Encryption at rest
    'enable_encryption': True,
    'encryption_key_file': '/opt/atlas_email/keys/db.key',
    
    # Access control
    'require_authentication': True,
    'connection_encryption': True,
    'audit_logging': True,
    
    # Backup encryption
    'encrypt_backups': True,
    'backup_key_rotation': True,
    'backup_retention_encrypted': 90  # days
}
```

### Application Security
```python
# Security middleware configuration
security_middleware = {
    # HTTPS enforcement
    'force_https': True,
    'hsts_max_age': 31536000,  # 1 year
    'hsts_include_subdomains': True,
    
    # Content Security Policy
    'csp_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'connect-src': "'self'"
    },
    
    # Additional security headers
    'x_frame_options': 'DENY',
    'x_content_type_options': 'nosniff',
    'referrer_policy': 'strict-origin-when-cross-origin'
}
```

### Firewall Configuration
```bash
# UFW firewall rules
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH access (restrict to specific IPs)
sudo ufw allow from 192.168.1.0/24 to any port 22

# Web traffic
sudo ufw allow 80
sudo ufw allow 443

# SMTP/IMAP (if hosting email)
sudo ufw allow 25
sudo ufw allow 993
sudo ufw allow 995

sudo ufw enable
```

## DATABASE DEPLOYMENT

### Production Database Setup
```bash
# 1. Database directory setup
sudo mkdir -p /opt/atlas_email/data/{main,backup,archive}
sudo chown atlas_email:atlas_email /opt/atlas_email/data/*
sudo chmod 700 /opt/atlas_email/data/*

# 2. Database initialization
sudo -u atlas_email python3 scripts/init_production_db.py

# 3. Initial data migration
sudo -u atlas_email python3 migrations/migrate.py --upgrade
```

### Backup Strategy
```bash
# /opt/atlas_email/scripts/backup_database.sh
#!/bin/bash
set -e

BACKUP_DIR="/opt/atlas_email/data/backup"
ARCHIVE_DIR="/opt/atlas_email/data/archive"
DB_PATH="/opt/atlas_email/data/main/mail_filter.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Daily backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/mail_filter_daily_$DATE.db"

# Compress and archive weekly backups
if [ $(date +%u) -eq 7 ]; then
    gzip -c $BACKUP_DIR/mail_filter_daily_$DATE.db > $ARCHIVE_DIR/mail_filter_weekly_$DATE.db.gz
fi

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "mail_filter_daily_*.db" -mtime +30 -delete
find $ARCHIVE_DIR -name "mail_filter_weekly_*.db.gz" -mtime +365 -delete

# Verify backup integrity
sqlite3 $BACKUP_DIR/mail_filter_daily_$DATE.db "PRAGMA integrity_check;"
```

### Database Monitoring
```python
# scripts/db_health_check.py
import sqlite3
import time
import logging
from pathlib import Path

def check_database_health():
    """Comprehensive database health check"""
    db_path = "/opt/atlas_email/data/main/mail_filter.db"
    
    checks = {
        'file_exists': Path(db_path).exists(),
        'file_readable': os.access(db_path, os.R_OK),
        'file_writable': os.access(db_path, os.W_OK),
        'integrity_ok': False,
        'connection_ok': False,
        'performance_ok': False
    }
    
    try:
        # Connection test
        conn = sqlite3.connect(db_path, timeout=10)
        checks['connection_ok'] = True
        
        # Integrity test
        cursor = conn.cursor()
        result = cursor.execute("PRAGMA integrity_check;").fetchone()
        checks['integrity_ok'] = result[0] == 'ok'
        
        # Performance test
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM processed_emails_bulletproof;")
        end_time = time.time()
        checks['performance_ok'] = (end_time - start_time) < 1.0
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
    
    return checks

if __name__ == "__main__":
    health = check_database_health()
    if all(health.values()):
        print("✅ Database health: OK")
        exit(0)
    else:
        print("❌ Database health: ISSUES DETECTED")
        print(health)
        exit(1)
```

## MONITORING AND LOGGING

### Application Monitoring
```python
# monitoring/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
email_processed_total = Counter('atlas_emails_processed_total', 'Total emails processed')
classification_duration = Histogram('atlas_classification_duration_seconds', 'Time spent classifying emails')
active_sessions = Gauge('atlas_active_sessions', 'Number of active processing sessions')
database_connections = Gauge('atlas_db_connections', 'Number of active database connections')

# Export metrics
start_http_server(8001)  # Metrics available at :8001/metrics
```

### Log Management
```bash
# /etc/logrotate.d/atlas_email
/var/log/atlas_email/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 644 atlas_email atlas_email
    postrotate
        supervisorctl restart atlas_email
    endscript
}
```

### Health Check Endpoints
```python
# src/atlas_email/api/health.py
from fastapi import APIRouter
from atlas_email.models.database import db

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check"""
    checks = {
        "database": db.test_connection(),
        "ml_models": test_ml_models(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}
```

## DOCKER DEPLOYMENT

### Production Dockerfile
```dockerfile
# Dockerfile
FROM python:3.9-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -r -s /bin/false atlas_email

# Application directory
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY migrations/ ./migrations/

# Set ownership and permissions
RUN chown -R atlas_email:atlas_email /app
USER atlas_email

# Create data directories
RUN mkdir -p data logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "atlas_email.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for Production
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  atlas_email:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - atlas_data:/app/data
      - atlas_logs:/app/logs
      - atlas_config:/app/config
    environment:
      - ATLAS_ENV=production
      - ATLAS_LOG_LEVEL=WARNING
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - atlas_email
    restart: unless-stopped

volumes:
  atlas_data:
  atlas_logs:
  atlas_config:
```

## OPERATIONAL PROCEDURES

### Daily Operations
```bash
# Daily maintenance script
#!/bin/bash
# /opt/atlas_email/scripts/daily_maintenance.sh

# Database backup
/opt/atlas_email/scripts/backup_database.sh

# Log cleanup
find /var/log/atlas_email -name "*.log" -mtime +7 -delete

# Health check
python3 /opt/atlas_email/scripts/db_health_check.py

# Performance report
python3 /opt/atlas_email/scripts/performance_report.py
```

### Emergency Procedures
```bash
# Emergency restart procedure
sudo supervisorctl stop atlas_email
sudo -u atlas_email cp /opt/atlas_email/data/backup/mail_filter_latest.db /opt/atlas_email/data/main/mail_filter.db
sudo supervisorctl start atlas_email

# Emergency rollback
git checkout previous-stable-tag
sudo supervisorctl restart atlas_email
```

This deployment guide provides comprehensive procedures for setting up Atlas_Email in any environment with enterprise-grade security, monitoring, and operational procedures.

---
*Deployment Guide - Version 1.0*  
*Generated: 2025-07-03*  
*Status: Production Ready*