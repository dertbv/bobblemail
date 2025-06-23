# Database Schema

## Email Project - Complete Database Architecture

**Database System**: SQLite  
**Current Version**: Schema v5  
**Database File**: `mail_filter.db` (17.4MB)  
**Migration System**: Automated with fallback strategy  

---

## 📊 Database Overview

### Current Statistics
- **Schema Version**: 5 (latest)
- **Total Tables**: 25+ specialized tables
- **Email Records**: 12,238 processed emails
- **Session Records**: 634 processing sessions  
- **Log Entries**: 9,112 application logs
- **Flag Records**: 90 email protection flags

### Architecture Principles
- **Normalized Design**: Separate concerns with clear relationships
- **Performance-First**: Strategic indexing for fast queries
- **Audit Trail**: Complete tracking of all operations
- **ML Integration**: Native support for machine learning workflows
- **User Feedback Loop**: Built-in learning and improvement system

---

## 🗃️ Core Database Tables

### 1. Email Processing Engine

#### `processed_emails_bulletproof` ⭐ PRIMARY TABLE
**Purpose**: Main table tracking all email processing actions and decisions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique email processing record |
| `timestamp` | TEXT | DEFAULT current_timestamp | When email was processed |
| `session_id` | INTEGER | FK → sessions.id | Processing session reference |
| `folder_name` | TEXT | NOT NULL | Email folder (INBOX, Sent, etc.) |
| `uid` | TEXT | NOT NULL | Email unique identifier |
| `sender_email` | TEXT | | Sender email address |
| `sender_domain` | TEXT | | Extracted sender domain |
| `subject` | TEXT | | Email subject line |
| `action` | TEXT | CHECK: 'DELETED' OR 'PRESERVED' | Final processing decision |
| `reason` | TEXT | | Why this action was taken |
| `category` | TEXT | | Spam classification category |
| `confidence_score` | REAL | | ML model confidence (0.0-1.0) |
| `ml_validation_method` | TEXT | | Which ML method was used |
| `raw_data` | TEXT | | JSON backup of original email |
| `reviewed` | BOOLEAN | DEFAULT FALSE | Has been manually reviewed |
| `user_validated` | BOOLEAN | DEFAULT FALSE | User confirmed classification |
| `user_protected` | BOOLEAN | DEFAULT FALSE | User manually protected |

**Indexes**: `timestamp`, `action`, `session_id`, `sender_domain`

#### `sessions` - Processing Session Management
**Purpose**: Track email processing sessions with comprehensive statistics

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Session identifier |
| `account_id` | INTEGER FK | Account being processed |
| `start_time` | TEXT | Session start timestamp |
| `end_time` | TEXT | Session completion timestamp |
| `folders_processed` | TEXT JSON | Array of processed folders |
| `total_deleted` | INTEGER | Count of deleted emails |
| `total_preserved` | INTEGER | Count of preserved emails |
| `total_validated` | INTEGER | Count of validated emails |
| `categories_summary` | TEXT JSON | Category breakdown |
| `session_type` | TEXT | 'manual', 'batch', 'preview' |
| `is_preview` | BOOLEAN | Preview mode flag |

#### `email_flags` - Protection & Deletion System
**Purpose**: Flag emails for protection from deletion or force deletion override

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `email_uid` | TEXT | NOT NULL | Email unique identifier |
| `folder_name` | TEXT | NOT NULL | Email folder name |
| `account_id` | INTEGER | NOT NULL, FK | Account reference |
| `flag_type` | TEXT | CHECK: 'PROTECT' OR 'DELETE' | Flag purpose |
| `flag_reason` | TEXT | | Why email was flagged |
| `created_by` | TEXT | | Who created the flag |
| `created_at` | TEXT | DEFAULT current_timestamp | When flag was created |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag |

**Unique Constraint**: `(email_uid, folder_name, account_id)` - One active flag per email

---

### 2. Account Management System

#### `accounts` - Email Account Configuration
**Purpose**: Store encrypted email account credentials and settings

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Account identifier |
| `email_address` | VARCHAR(255) | UNIQUE, NOT NULL | Account email address |
| `provider` | TEXT | | Email provider name |
| `host` | TEXT | | IMAP server hostname |
| `port` | INTEGER | | IMAP server port |
| `encrypted_password` | TEXT | | Encrypted password |
| `target_folders` | TEXT JSON | | Array of folders to process |
| `folder_setup_complete` | BOOLEAN | DEFAULT FALSE | Setup completion flag |
| `provider_optimizations` | TEXT JSON | | Provider-specific settings |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account enabled flag |
| `last_used` | TEXT | | Last processing timestamp |

**Security**: Passwords encrypted with Fernet symmetric encryption

---

### 3. Machine Learning & Intelligence

#### `domains` - Domain Risk Analysis
**Purpose**: Track and analyze domain-based spam patterns

| Column | Type | Description |
|--------|------|-------------|
| `domain` | VARCHAR(255) UNIQUE | Domain name |
| `risk_score` | FLOAT | Calculated risk score (0.0-1.0) |
| `ml_confidence_scores` | TEXT JSON | Array of ML confidence scores |
| `total_occurrences` | INTEGER | How many times seen |
| `action_taken` | TEXT | Most common action |
| `is_whitelisted` | BOOLEAN | Protected domain flag |
| `validation_results` | TEXT JSON | Validation history |
| `associated_categories` | TEXT JSON | Spam categories seen |

#### `spam_categories` - Category Performance Tracking
**Purpose**: Track effectiveness of spam categorization

| Column | Type | Description |
|--------|------|-------------|
| `category` | VARCHAR(100) UNIQUE | Spam category name |
| `total_count` | INTEGER | Total emails in category |
| `deletion_rate` | FLOAT | Percentage deleted |
| `common_keywords` | TEXT JSON | Most common keywords |
| `associated_domains` | TEXT JSON | Associated domain list |

#### `user_feedback` - ML Training Pipeline
**Purpose**: Store user corrections for continuous model improvement

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Feedback record ID |
| `email_uid` | TEXT | Email being corrected |
| `original_classification` | TEXT | What ML predicted |
| `user_classification` | TEXT | What user says is correct |
| `feedback_type` | TEXT | 'correct', 'incorrect', 'false_positive' |
| `confidence_rating` | INTEGER | User confidence (1-5) |
| `user_comments` | TEXT | Additional user notes |
| `processed` | BOOLEAN | Fed back to ML model |
| `contributed_to_accuracy` | BOOLEAN | Helped improve accuracy |

---

### 4. Advanced ML Learning System

#### `adaptive_patterns` - Dynamic Pattern Recognition
**Purpose**: Learn and adapt to new spam patterns automatically

| Column | Type | Description |
|--------|------|-------------|
| `pattern_id` | INTEGER PRIMARY KEY | Pattern identifier |
| `pattern_type` | TEXT | Type of pattern detected |
| `pattern_text` | TEXT | The actual pattern |
| `confidence_score` | REAL | Pattern reliability |
| `effectiveness` | REAL | How well it works |
| `occurrence_count` | INTEGER | Times pattern seen |
| `campaign_id` | TEXT | Related spam campaign |

#### `model_performance_history` - ML Model Tracking
**Purpose**: Track machine learning model performance over time

| Column | Type | Description |
|--------|------|-------------|
| `model_version` | TEXT | Model version identifier |
| `accuracy` | REAL | Overall model accuracy |
| `precision` | REAL | Precision metric |
| `recall` | REAL | Recall metric |
| `false_positive_rate` | REAL | False positive rate |
| `sample_count` | INTEGER | Sample size for metrics |
| `recorded_at` | TEXT | When metrics recorded |

#### `learning_events` - Continuous Learning Log
**Purpose**: Track all learning events for model improvement

| Column | Type | Description |
|--------|------|-------------|
| `event_type` | TEXT | Type of learning event |
| `true_label` | TEXT | Actual correct classification |
| `predicted_label` | TEXT | What model predicted |
| `confidence` | REAL | Model confidence |
| `correction_type` | TEXT | How it was corrected |
| `model_version` | TEXT | Model version used |

---

### 5. Vendor Intelligence System

#### `vendor_email_patterns` - Smart Vendor Detection
**Purpose**: Intelligent classification of vendor/business emails

| Column | Type | Description |
|--------|------|-------------|
| `vendor_domain` | TEXT | Vendor domain |
| `pattern_type` | TEXT | transactional, marketing, support |
| `pattern_category` | TEXT | sender, keyword, regex, subject |
| `pattern_value` | TEXT | The actual pattern |
| `confidence_weight` | REAL | Pattern reliability weight |

#### `user_vendor_preferences` - Personalized Preferences
**Purpose**: Store user preferences for different vendor email types

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | INTEGER | User identifier |
| `vendor_domain` | TEXT | Vendor domain |
| `email_type` | TEXT | Type of email |
| `allow_emails` | BOOLEAN | User preference |

**Unique Constraint**: `(user_id, vendor_domain, email_type)`

#### `vendor_classification_history` - Classification Tracking
**Purpose**: Track vendor email classification accuracy and user feedback

| Column | Type | Description |
|--------|------|-------------|
| `vendor_domain` | TEXT | Vendor domain |
| `classified_intent` | TEXT | Detected email intent |
| `confidence_score` | REAL | Classification confidence |
| `user_feedback` | TEXT | User correction if any |
| `should_preserve` | BOOLEAN | Should be preserved |
| `actual_action` | TEXT | Action actually taken |
| `matched_patterns` | TEXT JSON | Patterns that matched |
| `reasoning` | TEXT | Why classified this way |

---

### 6. System Operations & Monitoring

#### `logs` - Structured Application Logging
**Purpose**: Replace file-based logging with structured database logging

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Log entry ID |
| `timestamp` | TEXT | When logged |
| `level` | TEXT | DEBUG, INFO, WARN, ERROR |
| `category` | TEXT | SESSION, EMAIL, DOMAIN, CONFIG |
| `message` | TEXT | Log message |
| `metadata` | TEXT JSON | Additional structured data |
| `account_id` | INTEGER FK | Related account if any |
| `session_id` | INTEGER FK | Related session if any |

**Current Records**: 9,112 log entries

#### `configurations` - Dynamic Configuration
**Purpose**: Store application configuration (replaces JSON config files)

| Column | Type | Description |
|--------|------|-------------|
| `config_type` | TEXT | FILTERS, ML_SETTINGS, PROVIDER |
| `config_key` | TEXT | Configuration key |
| `config_value` | TEXT | Value (JSON or text) |
| `account_id` | INTEGER FK | Account-specific config |
| `created_at` | TEXT | When configuration created |
| `updated_at` | TEXT | When last updated |

#### `filter_terms` - Keyword Management
**Purpose**: Manage spam detection keywords (replaces my_keywords.txt)

| Column | Type | Description |
|--------|------|-------------|
| `term` | TEXT UNIQUE | Filter keyword/phrase |
| `category` | TEXT | Category of term |
| `confidence_threshold` | REAL | Minimum confidence needed |
| `created_by` | TEXT | user or system |
| `is_active` | BOOLEAN | Term enabled flag |

**Current Records**: 1,980 filter terms

---

### 7. Performance & Analytics

#### `performance_metrics` - System Performance
**Purpose**: Monitor and track system performance metrics

| Column | Type | Description |
|--------|------|-------------|
| `operation_type` | TEXT | Type of operation measured |
| `duration_seconds` | REAL | How long operation took |
| `items_processed` | INTEGER | Number of items processed |
| `memory_usage_mb` | REAL | Memory usage during operation |
| `recorded_at` | TEXT | When metric recorded |

#### `error_reports` - Error Tracking
**Purpose**: Structured error logging and resolution tracking

| Column | Type | Description |
|--------|------|-------------|
| `error_type` | TEXT | Type/category of error |
| `error_message` | TEXT | Error message |
| `stack_trace` | TEXT | Full stack trace |
| `context_data` | TEXT JSON | Context when error occurred |
| `resolved` | BOOLEAN | Has been resolved |
| `occurred_at` | TEXT | When error happened |

#### `user_analytics` - User Activity Analytics
**Purpose**: Track user contributions and activity patterns

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | INTEGER | User identifier |
| `emails_analyzed` | INTEGER | Emails user has reviewed |
| `feedback_given` | INTEGER | Feedback submissions |
| `emails_deleted` | INTEGER | User-initiated deletions |
| `accuracy_contributions` | INTEGER | Contributions to accuracy |
| `last_activity` | TEXT | Last user activity |

---

## 🔍 Database Indexes & Performance

### Primary Performance Indexes

```sql
-- Core email processing performance
CREATE INDEX idx_processed_emails_bulletproof_timestamp ON processed_emails_bulletproof(timestamp);
CREATE INDEX idx_processed_emails_bulletproof_action ON processed_emails_bulletproof(action);
CREATE INDEX idx_processed_emails_bulletproof_session ON processed_emails_bulletproof(session_id);
CREATE INDEX idx_processed_emails_bulletproof_domain ON processed_emails_bulletproof(sender_domain);

-- Session and account management
CREATE INDEX idx_accounts_email ON accounts(email_address);
CREATE INDEX idx_sessions_account ON sessions(account_id);
CREATE INDEX idx_sessions_time ON sessions(start_time);

-- Domain and spam analysis
CREATE INDEX idx_domains_domain ON domains(domain);
CREATE INDEX idx_domains_risk ON domains(risk_score);
CREATE INDEX idx_spam_categories_category ON spam_categories(category);

-- User feedback and flags
CREATE INDEX idx_user_feedback_uid ON user_feedback(email_uid);
CREATE INDEX idx_user_feedback_timestamp ON user_feedback(timestamp);
CREATE INDEX idx_email_flags_lookup ON email_flags(email_uid, folder_name, account_id);
CREATE UNIQUE INDEX idx_email_flags_unique ON email_flags(email_uid, folder_name, account_id) 
  WHERE is_active = TRUE;

-- Vendor intelligence system
CREATE INDEX idx_vendor_preferences_lookup ON user_vendor_preferences(user_id, vendor_domain);
CREATE INDEX idx_vendor_patterns_lookup ON vendor_email_patterns(vendor_domain, pattern_type);
CREATE INDEX idx_classification_history_vendor ON vendor_classification_history(vendor_domain);

-- System operations
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_category ON logs(category);
CREATE INDEX idx_performance_metrics_time ON performance_metrics(recorded_at);
```

### Query Optimization Strategies

1. **Email Processing Queries**: Optimized for timestamp and action filtering
2. **Domain Analysis**: Fast lookups by domain name and risk score
3. **User Feedback**: Indexed for rapid feedback retrieval and processing
4. **Session Management**: Optimized for account-based and time-based queries
5. **Flag Operations**: Composite index for unique constraint and fast lookups

---

## 🔄 Schema Evolution & Migration System

### Version Management
- **Current Schema**: Version 5
- **Version Tracking**: `schema_version` table with timestamps
- **Migration Strategy**: Automated detection and upgrade
- **Fallback Plan**: Complete database recreation if migration fails

### Migration History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2025-06-04 | Initial schema with core tables |
| v2 | 2025-06-08 | Added `user_feedback` table |
| v3 | 2025-06-09 | Added `user_analytics` and `immediate_deletions` |
| v4 | 2025-06-15 | Added vendor intelligence tables |
| v5 | 2025-06-22 | Added `processed_emails_bulletproof` as primary table |

### Migration Features
- **Automatic Detection**: Checks version on database connection
- **Data Preservation**: Existing data maintained during upgrades
- **Error Recovery**: Graceful fallback to database recreation
- **Logging**: All migration steps logged for audit trail

---

## 🔗 Table Relationships & Foreign Keys

### Primary Relationships

```sql
-- Core processing flow
sessions.account_id → accounts.id
processed_emails_bulletproof.session_id → sessions.id
email_flags.account_id → accounts.id

-- User feedback and learning
user_feedback.session_id → sessions.id
learning_events.feedback_id → user_feedback.id

-- System operations
logs.account_id → accounts.id (optional)
logs.session_id → sessions.id (optional)
performance_metrics.session_id → sessions.id (optional)

-- Configuration management
configurations.account_id → accounts.id (optional)

-- Vendor intelligence
user_vendor_preferences.user_id → users.id (when user system implemented)
vendor_classification_history.account_id → accounts.id
```

### Data Flow Architecture

1. **Setup Flow**: `accounts` → `configurations` → `filter_terms`
2. **Processing Flow**: `accounts` → `sessions` → `processed_emails_bulletproof`
3. **Analysis Flow**: `domains` → `spam_categories` → `adaptive_patterns`
4. **Learning Flow**: `user_feedback` → `learning_events` → `model_performance_history`
5. **Protection Flow**: `email_flags` → flag checking during processing
6. **Monitoring Flow**: `logs` → `performance_metrics` → `error_reports`

---

## ⚙️ Database Configuration & Operations

### Connection Management
- **File Location**: `mail_filter.db` in project root directory
- **Connection Pool**: Thread-local connections with automatic cleanup
- **Timeout Settings**: 30-second connection timeout
- **Journal Mode**: DELETE mode (not WAL) to reduce file handles
- **Foreign Keys**: Enabled for referential integrity

### Backup & Recovery Strategy
- **Raw Data Backup**: JSON backup stored in `raw_data` columns
- **Emergency Logging**: Fallback to file logging on database failure
- **Connection Redundancy**: Multiple connection attempt strategies
- **Schema Recreation**: Automatic fallback for corrupted databases

### Performance Characteristics
- **Database Size**: 17.4MB (efficient for current scale)
- **Query Performance**: Sub-millisecond for indexed queries
- **Concurrent Access**: Thread-safe with proper locking
- **Memory Usage**: Minimal memory footprint with lazy loading

---

## 🚀 Future Scalability Considerations

### Current Limitations
- **SQLite**: Single-writer limitation for high concurrency
- **File Size**: Will need sharding/partitioning as data grows
- **Complex Queries**: Some analytics queries could benefit from OLAP database

### Migration Path to PostgreSQL
1. **Database Abstraction Layer**: Already designed in `database.py`
2. **Schema Translation**: SQLite → PostgreSQL type mapping
3. **Connection Pooling**: Upgrade to production-grade pool
4. **Partitioning Strategy**: Time-based partitioning for large tables
5. **Replication**: Master-replica setup for read scaling

### Optimization Opportunities
- **Table Partitioning**: By date for `processed_emails_bulletproof`
- **Archive Strategy**: Move old data to archive tables
- **Materialized Views**: For complex analytics queries
- **Read Replicas**: For reporting and analytics workloads

---

*Built with love by ATLAS & Bobble - Intelligent Email Security Through Data* 💖

*Last Updated: June 23, 2025*