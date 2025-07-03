# ATLAS EMAIL CONFIGURATION REFERENCE

## EXECUTIVE SUMMARY

**Atlas_Email** provides comprehensive configuration management through centralized settings, environment variables, and database-stored configurations. This reference documents all configurable parameters, their default values, and usage contexts.

**CONFIGURATION CHARACTERISTICS**:
- **Centralized Management**: `config/` package with specialized modules
- **Runtime Configuration**: Database-stored settings for dynamic updates
- **Environment Support**: Development, testing, and production configurations
- **Provider Optimization**: Email provider-specific settings
- **Security Integration**: Credential management and encryption

## CONFIGURATION ARCHITECTURE

### Configuration Module Structure
```
config/
├── auth.py           # IMAP authentication and connection management
├── credentials.py    # Database and service credentials
├── loader.py         # Configuration loading utilities
├── manager.py        # Runtime configuration management  
├── settings.py       # System-wide settings and defaults
└── constants.py      # System constants and fixed values
```

### Configuration Hierarchy
```python
# Priority order (highest to lowest)
1. Environment variables (runtime overrides)
2. Database configurations table (dynamic settings)
3. config/settings.py (application defaults)
4. config/constants.py (system constants)
5. Hard-coded defaults (fallback values)
```

## CORE SYSTEM SETTINGS

### Database Configuration
**File**: `config/credentials.py`
```python
db_credentials = {
    # Primary database path
    'database_path': 'data/mail_filter.db',
    
    # Backup database location
    'backup_database_path': 'data/backup/mail_filter_backup.db',
    
    # Connection settings
    'connection_timeout': 30,        # seconds
    'busy_timeout': 5000,           # milliseconds
    'journal_mode': 'WAL',          # Write-Ahead Logging
    'synchronous': 'NORMAL',        # Balance between safety and speed
    'cache_size': 10000,            # Number of pages in cache
    
    # Performance settings
    'enable_foreign_keys': True,
    'enable_triggers': True,
    'auto_vacuum': 'INCREMENTAL',
    
    # Backup settings
    'backup_frequency': 'daily',     # daily, weekly, manual
    'backup_retention_days': 30,
    'auto_backup_enabled': True
}
```

### Machine Learning Configuration
**File**: `config/settings.py`
```python
class Settings:
    @staticmethod
    def get_ml_config():
        return {
            # Model file paths
            'naive_bayes_model_path': 'data/models/naive_bayes_model.json',
            'random_forest_model_path': 'data/models/random_forest_model.pkl',
            'category_classifier_path': 'data/models/category_classifier.json',
            
            # Training parameters
            'min_training_samples': 100,        # Minimum samples before training
            'max_training_samples': 10000,      # Maximum samples per training session
            'training_test_split': 0.2,         # 20% for testing
            'cross_validation_folds': 5,        # K-fold cross validation
            
            # Model performance thresholds
            'min_accuracy_threshold': 0.85,     # Minimum accuracy to deploy model
            'confidence_threshold': 0.7,        # High confidence classification
            'low_confidence_threshold': 0.3,    # Low confidence threshold
            
            # Feature extraction settings
            'max_features': 5000,               # Maximum text features
            'ngram_range': (1, 2),             # Unigrams and bigrams
            'min_df': 2,                       # Minimum document frequency
            'max_df': 0.8,                     # Maximum document frequency
            
            # Ensemble settings
            'voting_strategy': 'weighted',      # weighted, soft, hard
            'model_weights': {
                'random_forest': 0.4,
                'naive_bayes': 0.3,
                'keyword_processor': 0.3
            }
        }
    
    @staticmethod
    def get_hybrid_config():
        return {
            # Classification tiers
            'tier_1_confidence_threshold': 0.7,
            'tier_2_geographic_enabled': True,
            'tier_3_strategic_enabled': True,
            
            # Performance optimization
            'enable_caching': True,
            'cache_duration_minutes': 15,
            'batch_classification': True,
            'parallel_processing': False,
            
            # Fallback settings
            'fallback_to_keyword_only': True,
            'fallback_confidence': 0.5,
            'enable_logical_classifier': True
        }
```

### Geographic Intelligence Configuration
```python
geographic_config = {
    # GeoIP settings
    'geoip_provider': 'geoip2fast',         # Primary GeoIP provider
    'geoip_fallback': 'builtin',            # Fallback provider
    'geoip_cache_enabled': True,
    'geoip_cache_duration_hours': 24,
    
    # IP extraction settings
    'extract_from_received_headers': True,
    'extract_from_originating_ip': True,
    'extract_from_sender_ip': True,
    'private_ip_exclusion': True,
    
    # Risk scoring
    'enable_country_risk_scoring': True,
    'default_unknown_country_risk': 0.30,
    'risk_score_weight': 0.25,             # Weight in final confidence
    
    # Country risk scores (subset - full list in geographic_intelligence.py)
    'country_risk_scores': {
        'CN': 0.95,  # China
        'RU': 0.90,  # Russia
        'NG': 0.85,  # Nigeria
        'US': 0.10,  # United States
        'CA': 0.10,  # Canada
        'GB': 0.10,  # United Kingdom
        # ... (75+ total countries)
    }
}
```

## EMAIL PROVIDER SETTINGS

### Provider-Specific Optimization
**File**: `atlas_email/core/email_processor.py`
```python
PROVIDER_SETTINGS = {
    'gmail': {
        # Connection settings
        'host': 'imap.gmail.com',
        'port': 993,
        'use_ssl': True,
        
        # Performance optimization
        'batch_size': 50,
        'connection_timeout': 30,
        'read_timeout': 60,
        'retry_attempts': 3,
        
        # Processing behavior
        'skip_individual_marking': False,
        'use_bulk_operations': False,
        'requires_parentheses': False,
        'folder_reselect_frequency': 10,
        
        # Folder mappings
        'spam_folder': '[Gmail]/Spam',
        'trash_folder': '[Gmail]/Trash',
        'sent_folder': '[Gmail]/Sent Mail'
    },
    
    'icloud': {
        # Connection settings
        'host': 'imap.mail.me.com',
        'port': 993,
        'use_ssl': True,
        
        # Performance optimization (iCloud-specific)
        'batch_size': 25,                   # Smaller batches for stability
        'connection_timeout': 45,           # Longer timeout for iCloud
        'read_timeout': 90,
        'retry_attempts': 5,                # More retries needed
        
        # Processing behavior (iCloud optimizations)
        'skip_individual_marking': True,    # Skip individual STORE commands
        'use_bulk_operations': True,        # Use bulk STORE operations
        'requires_parentheses': True,       # Folder names need parentheses
        'folder_reselect_frequency': 5,     # Reselect folders more frequently
        'enable_idle_support': False,       # iCloud IDLE is unreliable
        
        # Folder mappings
        'spam_folder': 'Junk',
        'trash_folder': 'Deleted Messages',
        'sent_folder': 'Sent Messages'
    },
    
    'outlook': {
        'host': 'outlook.office365.com',
        'port': 993,
        'batch_size': 30,
        'connection_timeout': 30,
        'skip_individual_marking': False,
        'use_bulk_operations': False,
        'spam_folder': 'Junk Email',
        'trash_folder': 'Deleted Items'
    },
    
    'yahoo': {
        'host': 'imap.mail.yahoo.com',
        'port': 993,
        'batch_size': 40,
        'connection_timeout': 25,
        'spam_folder': 'Bulk Mail',
        'trash_folder': 'Trash'
    }
}
```

## WEB INTERFACE CONFIGURATION

### FastAPI Application Settings
```python
# FastAPI configuration
fastapi_config = {
    # Server settings
    'host': '0.0.0.0',
    'port': 8000,
    'reload': False,                    # Set True for development
    'debug': False,                     # Set True for development
    'log_level': 'info',               # debug, info, warning, error
    
    # Security settings
    'cors_enabled': True,
    'cors_origins': ['http://localhost:8000'],
    'trusted_hosts': ['localhost', '127.0.0.1'],
    
    # Performance settings
    'workers': 1,                      # Number of worker processes
    'max_requests': 1000,              # Requests per worker before restart
    'timeout_keep_alive': 5,           # Keep alive timeout
    'limit_concurrency': 100,          # Maximum concurrent connections
    
    # Template settings
    'template_directory': 'templates',
    'static_directory': 'static',
    'static_url_path': '/static',
    
    # Response settings
    'response_timeout': 30,            # Response timeout in seconds
    'request_size_limit': 16 * 1024 * 1024,  # 16MB request limit
}
```

### Timer and Automation Configuration
```python
automation_config = {
    # Timer settings
    'default_timer_minutes': 30,
    'min_timer_minutes': 1,
    'max_timer_minutes': 10080,        # 1 week maximum
    'timer_precision_seconds': 30,      # Timer check frequency
    
    # Batch processing
    'auto_batch_enabled': True,
    'batch_timeout_minutes': 60,       # Maximum batch processing time
    'batch_preview_mode': False,       # Default to actual processing
    
    # Retry settings
    'max_retry_attempts': 3,
    'retry_delay_seconds': 30,
    'exponential_backoff': True,
    
    # Logging
    'log_batch_operations': True,
    'log_timer_events': True,
    'detailed_performance_logging': False
}
```

## SECURITY CONFIGURATION

### Authentication Settings
```python
auth_config = {
    # Password encryption
    'encryption_algorithm': 'AES-256-CBC',
    'key_derivation': 'PBKDF2',
    'key_iterations': 100000,
    'salt_length': 32,
    
    # Session management
    'session_timeout_minutes': 120,
    'session_cleanup_frequency': 'hourly',
    'max_concurrent_sessions': 5,
    
    # Email authentication
    'verify_spf': True,
    'verify_dkim': True,
    'verify_dmarc': True,
    'authentication_weight': 0.2,      # Weight in classification
    
    # API security
    'rate_limiting_enabled': True,
    'requests_per_hour': 1000,
    'api_key_required': False,         # Set True for API access
    'csrf_protection': True
}
```

### Data Protection Settings
```python
privacy_config = {
    # Data retention
    'email_content_storage': False,    # Never store email content
    'metadata_retention_days': 365,   # Keep metadata for 1 year
    'log_retention_days': 90,         # Keep logs for 90 days
    'analytics_retention_days': 180,  # Keep analytics for 6 months
    
    # Data anonymization
    'anonymize_ip_addresses': True,
    'hash_email_addresses': False,    # Keep email addresses for functionality
    'redact_subject_lines': False,
    
    # Compliance
    'gdpr_compliance': True,
    'data_export_enabled': True,
    'data_deletion_enabled': True,
    'audit_logging': True
}
```

## PERFORMANCE CONFIGURATION

### Database Performance Settings
```python
db_performance = {
    # Connection pooling
    'max_connections': 10,
    'connection_pool_size': 5,
    'pool_timeout': 30,
    'pool_recycle': 3600,             # Recycle connections hourly
    
    # Query optimization
    'query_timeout': 30,              # Query timeout in seconds
    'explain_queries': False,         # Log query plans (debug only)
    'slow_query_threshold': 1.0,      # Log queries slower than 1 second
    
    # Caching
    'enable_query_cache': True,
    'cache_size_mb': 100,
    'cache_ttl_seconds': 300,
    
    # Maintenance
    'auto_vacuum_enabled': True,
    'vacuum_schedule': 'weekly',
    'analyze_schedule': 'daily',
    'checkpoint_interval': 1000       # WAL checkpoint interval
}
```

### System Resource Limits
```python
resource_limits = {
    # Memory limits
    'max_memory_mb': 1024,            # 1GB memory limit
    'memory_warning_threshold': 0.8,  # Warn at 80% usage
    'gc_frequency': 100,              # Garbage collect every 100 operations
    
    # Processing limits
    'max_emails_per_batch': 50,
    'max_concurrent_classifications': 5,
    'classification_timeout': 30,     # Timeout per email classification
    
    # File system limits
    'max_log_file_size_mb': 100,
    'max_backup_files': 10,
    'temp_file_cleanup_hours': 24,
    
    # Network limits
    'connection_timeout': 30,
    'read_timeout': 60,
    'max_retries': 3
}
```

## LOGGING CONFIGURATION

### Log Level and Output Settings
```python
logging_config = {
    # Log levels by component
    'global_log_level': 'INFO',
    'component_levels': {
        'database': 'WARNING',
        'ml': 'INFO',
        'email_processing': 'INFO',
        'geographic': 'WARNING',
        'api': 'INFO'
    },
    
    # Log output
    'log_to_file': True,
    'log_to_console': True,
    'log_file_path': 'logs/atlas_email.log',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    
    # Log rotation
    'rotate_logs': True,
    'max_log_size_mb': 50,
    'backup_count': 5,
    'rotation_when': 'midnight',
    
    # Performance logging
    'log_performance_metrics': True,
    'log_slow_operations': True,
    'performance_threshold_ms': 1000,
    
    # Security logging
    'log_authentication_events': True,
    'log_failed_logins': True,
    'log_privilege_escalation': True
}
```

## DEVELOPMENT CONFIGURATION

### Development vs Production Settings
```python
# Development configuration
development_config = {
    'debug': True,
    'reload': True,
    'log_level': 'DEBUG',
    'enable_profiling': True,
    'detailed_error_pages': True,
    'cors_origins': ['*'],             # Allow all origins in dev
    'rate_limiting': False,
    'cache_templates': False,
    'mock_external_services': True,
    'test_database_path': 'data/test_mail_filter.db'
}

# Production configuration
production_config = {
    'debug': False,
    'reload': False,
    'log_level': 'WARNING',
    'enable_profiling': False,
    'detailed_error_pages': False,
    'cors_origins': ['https://yourdomain.com'],
    'rate_limiting': True,
    'cache_templates': True,
    'mock_external_services': False,
    'ssl_verification': True
}
```

## ENVIRONMENT VARIABLES

### Supported Environment Variables
```bash
# Database configuration
export ATLAS_DB_PATH="/path/to/database.db"
export ATLAS_BACKUP_PATH="/path/to/backups/"

# Server configuration
export ATLAS_HOST="0.0.0.0"
export ATLAS_PORT="8000"
export ATLAS_DEBUG="false"

# ML configuration
export ATLAS_ML_MODELS_PATH="/path/to/models/"
export ATLAS_CONFIDENCE_THRESHOLD="0.7"

# Geographic configuration
export ATLAS_GEOIP_ENABLED="true"
export ATLAS_COUNTRY_RISK_WEIGHT="0.25"

# Security configuration
export ATLAS_ENCRYPTION_KEY="your-encryption-key"
export ATLAS_SESSION_TIMEOUT="120"

# Performance configuration
export ATLAS_MAX_MEMORY_MB="1024"
export ATLAS_BATCH_SIZE="50"

# Logging configuration
export ATLAS_LOG_LEVEL="INFO"
export ATLAS_LOG_PATH="/path/to/logs/"
```

## RUNTIME CONFIGURATION MANAGEMENT

### Database-Stored Configuration
```sql
-- configurations table structure
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,              -- NULL for global config
    config_type VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,               -- JSON or plain text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Example configurations
INSERT INTO configurations (config_type, config_key, config_value) VALUES
('ML_SETTINGS', 'confidence_threshold', '0.75'),
('GEOGRAPHIC', 'enable_country_risk', 'true'),
('PERFORMANCE', 'batch_size', '40'),
('LOGGING', 'log_level', 'INFO');
```

### Configuration API Endpoints
```python
# Runtime configuration updates via API
PUT /api/config/{config_type}/{config_key}
{
    "value": "new_configuration_value",
    "account_id": null  # Global configuration
}

# Retrieve configuration
GET /api/config/{config_type}/{config_key}
{
    "config_type": "ML_SETTINGS",
    "config_key": "confidence_threshold", 
    "config_value": "0.75",
    "last_updated": "2025-07-03T10:30:00Z"
}
```

This configuration reference provides comprehensive control over all Atlas_Email system behaviors, performance characteristics, and security settings.

---
*Configuration Reference - Version 1.0*  
*Generated: 2025-07-03*  
*Status: Production Ready*