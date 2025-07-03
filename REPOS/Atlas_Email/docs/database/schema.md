database_schema:
  title: "Email Project - Complete Database Architecture"
  database_system: "SQLite"
  current_version: "Schema v5"
  database_file: "mail_filter.db"
  file_size: "17.4MB"
  migration_system: "Automated with fallback strategy"
  
  database_overview:
    current_statistics:
      schema_version: 5
      total_tables: "25+ specialized tables"
      email_records: 12238
      session_records: 634
      log_entries: 9112
      flag_records: 90
    
    architecture_principles:
      - "Normalized Design: Separate concerns with clear relationships"
      - "Performance-First: Strategic indexing for fast queries"
      - "Audit Trail: Complete tracking of all operations"
      - "ML Integration: Native support for machine learning workflows"
      - "User Feedback Loop: Built-in learning and improvement system"
  
  core_database_tables:
    email_processing_engine:
      processed_emails_bulletproof:
        type: "PRIMARY TABLE"
        purpose: "Main table tracking all email processing actions and decisions"
        columns:
          - name: "id"
            type: "INTEGER"
            constraints: "PRIMARY KEY AUTOINCREMENT"
            description: "Unique email processing record"
          - name: "timestamp"
            type: "TEXT"
            constraints: "DEFAULT current_timestamp"
            description: "When email was processed"
          - name: "session_id"
            type: "INTEGER"
            constraints: "FK → sessions.id"
            description: "Processing session reference"
          - name: "folder_name"
            type: "TEXT"
            constraints: "NOT NULL"
            description: "Email folder (INBOX, Sent, etc.)"
          - name: "uid"
            type: "TEXT"
            constraints: "NOT NULL"
            description: "Email unique identifier"
          - name: "sender_email"
            type: "TEXT"
            description: "Sender email address"
          - name: "sender_domain"
            type: "TEXT"
            description: "Extracted sender domain"
          - name: "subject"
            type: "TEXT"
            description: "Email subject line"
          - name: "action"
            type: "TEXT"
            constraints: "CHECK: 'DELETED' OR 'PRESERVED'"
            description: "Final processing decision"
          - name: "reason"
            type: "TEXT"
            description: "Why this action was taken"
          - name: "category"
            type: "TEXT"
            description: "Spam classification category"
          - name: "confidence_score"
            type: "REAL"
            description: "ML model confidence (0.0-1.0)"
          - name: "ml_validation_method"
            type: "TEXT"
            description: "Which ML method was used"
          - name: "raw_data"
            type: "TEXT"
            description: "JSON backup of original email"
          - name: "reviewed"
            type: "BOOLEAN"
            constraints: "DEFAULT FALSE"
            description: "Has been manually reviewed"
          - name: "user_validated"
            type: "BOOLEAN"
            constraints: "DEFAULT FALSE"
            description: "User confirmed classification"
          - name: "user_protected"
            type: "BOOLEAN"
            constraints: "DEFAULT FALSE"
            description: "User manually protected"
        indexes: ["timestamp", "action", "session_id", "sender_domain"]
      
      sessions:
        purpose: "Track email processing sessions with comprehensive statistics"
        columns:
          - name: "id"
            type: "INTEGER PRIMARY KEY"
            description: "Session identifier"
          - name: "account_id"
            type: "INTEGER FK"
            description: "Account being processed"
          - name: "start_time"
            type: "TEXT"
            description: "Session start timestamp"
          - name: "end_time"
            type: "TEXT"
            description: "Session completion timestamp"
          - name: "folders_processed"
            type: "TEXT JSON"
            description: "Array of processed folders"
          - name: "total_deleted"
            type: "INTEGER"
            description: "Count of deleted emails"
          - name: "total_preserved"
            type: "INTEGER"
            description: "Count of preserved emails"
          - name: "total_validated"
            type: "INTEGER"
            description: "Count of validated emails"
          - name: "categories_summary"
            type: "TEXT JSON"
            description: "Category breakdown"
          - name: "session_type"
            type: "TEXT"
            description: "'manual', 'batch', 'preview'"
          - name: "is_preview"
            type: "BOOLEAN"
            description: "Preview mode flag"
      
      email_flags:
        purpose: "Flag emails for protection from deletion or force deletion override"
        columns:
          - name: "email_uid"
            type: "TEXT"
            constraints: "NOT NULL"
            description: "Email unique identifier"
          - name: "folder_name"
            type: "TEXT"
            constraints: "NOT NULL"
            description: "Email folder name"
          - name: "account_id"
            type: "INTEGER"
            constraints: "NOT NULL, FK"
            description: "Account reference"
          - name: "flag_type"
            type: "TEXT"
            constraints: "CHECK: 'PROTECT' OR 'DELETE'"
            description: "Flag purpose"
          - name: "flag_reason"
            type: "TEXT"
            description: "Why email was flagged"
          - name: "created_by"
            type: "TEXT"
            description: "Who created the flag"
          - name: "created_at"
            type: "TEXT"
            constraints: "DEFAULT current_timestamp"
            description: "When flag was created"
          - name: "is_active"
            type: "BOOLEAN"
            constraints: "DEFAULT TRUE"
            description: "Soft delete flag"
        unique_constraint: "(email_uid, folder_name, account_id) - One active flag per email"
    
    account_management_system:
      accounts:
        purpose: "Store encrypted email account credentials and settings"
        columns:
          - name: "id"
            type: "INTEGER"
            constraints: "PRIMARY KEY"
            description: "Account identifier"
          - name: "email_address"
            type: "VARCHAR(255)"
            constraints: "UNIQUE, NOT NULL"
            description: "Account email address"
          - name: "provider"
            type: "TEXT"
            description: "Email provider name"
          - name: "host"
            type: "TEXT"
            description: "IMAP server hostname"
          - name: "port"
            type: "INTEGER"
            description: "IMAP server port"
          - name: "encrypted_password"
            type: "TEXT"
            description: "Encrypted password"
          - name: "target_folders"
            type: "TEXT JSON"
            description: "Array of folders to process"
          - name: "folder_setup_complete"
            type: "BOOLEAN"
            constraints: "DEFAULT FALSE"
            description: "Setup completion flag"
          - name: "provider_optimizations"
            type: "TEXT JSON"
            description: "Provider-specific settings"
          - name: "is_active"
            type: "BOOLEAN"
            constraints: "DEFAULT TRUE"
            description: "Account enabled flag"
          - name: "last_used"
            type: "TEXT"
            description: "Last processing timestamp"
        security: "Passwords encrypted with Fernet symmetric encryption"
    
    machine_learning_intelligence:
      domains:
        purpose: "Track and analyze domain-based spam patterns"
        columns:
          - name: "domain"
            type: "VARCHAR(255) UNIQUE"
            description: "Domain name"
          - name: "risk_score"
            type: "FLOAT"
            description: "Calculated risk score (0.0-1.0)"
          - name: "ml_confidence_scores"
            type: "TEXT JSON"
            description: "Array of ML confidence scores"
          - name: "total_occurrences"
            type: "INTEGER"
            description: "How many times seen"
          - name: "action_taken"
            type: "TEXT"
            description: "Most common action"
          - name: "is_whitelisted"
            type: "BOOLEAN"
            description: "Protected domain flag"
          - name: "validation_results"
            type: "TEXT JSON"
            description: "Validation history"
          - name: "associated_categories"
            type: "TEXT JSON"
            description: "Spam categories seen"
      
      spam_categories:
        purpose: "Track effectiveness of spam categorization"
        columns:
          - name: "category"
            type: "VARCHAR(100) UNIQUE"
            description: "Spam category name"
          - name: "total_count"
            type: "INTEGER"
            description: "Total emails in category"
          - name: "deletion_rate"
            type: "FLOAT"
            description: "Percentage deleted"
          - name: "common_keywords"
            type: "TEXT JSON"
            description: "Most common keywords"
          - name: "associated_domains"
            type: "TEXT JSON"
            description: "Associated domain list"
      
      user_feedback:
        purpose: "Store user corrections for continuous model improvement"
        columns:
          - name: "id"
            type: "INTEGER PRIMARY KEY"
            description: "Feedback record ID"
          - name: "email_uid"
            type: "TEXT"
            description: "Email being corrected"
          - name: "original_classification"
            type: "TEXT"
            description: "What ML predicted"
          - name: "user_classification"
            type: "TEXT"
            description: "What user says is correct"
          - name: "feedback_type"
            type: "TEXT"
            description: "'correct', 'incorrect', 'false_positive'"
          - name: "confidence_rating"
            type: "INTEGER"
            description: "User confidence (1-5)"
          - name: "user_comments"
            type: "TEXT"
            description: "Additional user notes"
          - name: "processed"
            type: "BOOLEAN"
            description: "Fed back to ML model"
          - name: "contributed_to_accuracy"
            type: "BOOLEAN"
            description: "Helped improve accuracy"
    
    advanced_ml_learning_system:
      adaptive_patterns:
        purpose: "Learn and adapt to new spam patterns automatically"
        columns:
          - name: "pattern_id"
            type: "INTEGER PRIMARY KEY"
            description: "Pattern identifier"
          - name: "pattern_type"
            type: "TEXT"
            description: "Type of pattern detected"
          - name: "pattern_text"
            type: "TEXT"
            description: "The actual pattern"
          - name: "confidence_score"
            type: "REAL"
            description: "Pattern reliability"
          - name: "effectiveness"
            type: "REAL"
            description: "How well it works"
          - name: "occurrence_count"
            type: "INTEGER"
            description: "Times pattern seen"
          - name: "campaign_id"
            type: "TEXT"
            description: "Related spam campaign"
      
      model_performance_history:
        purpose: "Track machine learning model performance over time"
        columns:
          - name: "model_version"
            type: "TEXT"
            description: "Model version identifier"
          - name: "accuracy"
            type: "REAL"
            description: "Overall model accuracy"
          - name: "precision"
            type: "REAL"
            description: "Precision metric"
          - name: "recall"
            type: "REAL"
            description: "Recall metric"
          - name: "false_positive_rate"
            type: "REAL"
            description: "False positive rate"
          - name: "sample_count"
            type: "INTEGER"
            description: "Sample size for metrics"
          - name: "recorded_at"
            type: "TEXT"
            description: "When metrics recorded"
      
      learning_events:
        purpose: "Track all learning events for model improvement"
        columns:
          - name: "event_type"
            type: "TEXT"
            description: "Type of learning event"
          - name: "true_label"
            type: "TEXT"
            description: "Actual correct classification"
          - name: "predicted_label"
            type: "TEXT"
            description: "What model predicted"
          - name: "confidence"
            type: "REAL"
            description: "Model confidence"
          - name: "correction_type"
            type: "TEXT"
            description: "How it was corrected"
          - name: "model_version"
            type: "TEXT"
            description: "Model version used"
    
    vendor_intelligence_system:
      vendor_email_patterns:
        purpose: "Intelligent classification of vendor/business emails"
        columns:
          - name: "vendor_domain"
            type: "TEXT"
            description: "Vendor domain"
          - name: "pattern_type"
            type: "TEXT"
            description: "transactional, marketing, support"
          - name: "pattern_category"
            type: "TEXT"
            description: "sender, keyword, regex, subject"
          - name: "pattern_value"
            type: "TEXT"
            description: "The actual pattern"
          - name: "confidence_weight"
            type: "REAL"
            description: "Pattern reliability weight"
      
      user_vendor_preferences:
        purpose: "Store user preferences for different vendor email types"
        columns:
          - name: "user_id"
            type: "INTEGER"
            description: "User identifier"
          - name: "vendor_domain"
            type: "TEXT"
            description: "Vendor domain"
          - name: "email_type"
            type: "TEXT"
            description: "Type of email"
          - name: "allow_emails"
            type: "BOOLEAN"
            description: "User preference"
        unique_constraint: "(user_id, vendor_domain, email_type)"
      
      vendor_classification_history:
        purpose: "Track vendor email classification accuracy and user feedback"
        columns:
          - name: "vendor_domain"
            type: "TEXT"
            description: "Vendor domain"
          - name: "classified_intent"
            type: "TEXT"
            description: "Detected email intent"
          - name: "confidence_score"
            type: "REAL"
            description: "Classification confidence"
          - name: "user_feedback"
            type: "TEXT"
            description: "User correction if any"
          - name: "should_preserve"
            type: "BOOLEAN"
            description: "Should be preserved"
          - name: "actual_action"
            type: "TEXT"
            description: "Action actually taken"
          - name: "matched_patterns"
            type: "TEXT JSON"
            description: "Patterns that matched"
          - name: "reasoning"
            type: "TEXT"
            description: "Why classified this way"
    
    system_operations_monitoring:
      logs:
        purpose: "Replace file-based logging with structured database logging"
        columns:
          - name: "id"
            type: "INTEGER PRIMARY KEY"
            description: "Log entry ID"
          - name: "timestamp"
            type: "TEXT"
            description: "When logged"
          - name: "level"
            type: "TEXT"
            description: "DEBUG, INFO, WARN, ERROR"
          - name: "category"
            type: "TEXT"
            description: "SESSION, EMAIL, DOMAIN, CONFIG"
          - name: "message"
            type: "TEXT"
            description: "Log message"
          - name: "metadata"
            type: "TEXT JSON"
            description: "Additional structured data"
          - name: "account_id"
            type: "INTEGER FK"
            description: "Related account if any"
          - name: "session_id"
            type: "INTEGER FK"
            description: "Related session if any"
        current_records: 9112
      
      configurations:
        purpose: "Store application configuration (replaces JSON config files)"
        columns:
          - name: "config_type"
            type: "TEXT"
            description: "FILTERS, ML_SETTINGS, PROVIDER"
          - name: "config_key"
            type: "TEXT"
            description: "Configuration key"
          - name: "config_value"
            type: "TEXT"
            description: "Value (JSON or text)"
          - name: "account_id"
            type: "INTEGER FK"
            description: "Account-specific config"
          - name: "created_at"
            type: "TEXT"
            description: "When configuration created"
          - name: "updated_at"
            type: "TEXT"
            description: "When last updated"
      
      filter_terms:
        purpose: "Manage spam detection keywords (replaces my_keywords.txt)"
        columns:
          - name: "term"
            type: "TEXT UNIQUE"
            description: "Filter keyword/phrase"
          - name: "category"
            type: "TEXT"
            description: "Category of term"
          - name: "confidence_threshold"
            type: "REAL"
            description: "Minimum confidence needed"
          - name: "created_by"
            type: "TEXT"
            description: "user or system"
          - name: "is_active"
            type: "BOOLEAN"
            description: "Term enabled flag"
        current_records: 1980
    
    performance_analytics:
      performance_metrics:
        purpose: "Monitor and track system performance metrics"
        columns:
          - name: "operation_type"
            type: "TEXT"
            description: "Type of operation measured"
          - name: "duration_seconds"
            type: "REAL"
            description: "How long operation took"
          - name: "items_processed"
            type: "INTEGER"
            description: "Number of items processed"
          - name: "memory_usage_mb"
            type: "REAL"
            description: "Memory usage during operation"
          - name: "recorded_at"
            type: "TEXT"
            description: "When metric recorded"
      
      error_reports:
        purpose: "Structured error logging and resolution tracking"
        columns:
          - name: "error_type"
            type: "TEXT"
            description: "Type/category of error"
          - name: "error_message"
            type: "TEXT"
            description: "Error message"
          - name: "stack_trace"
            type: "TEXT"
            description: "Full stack trace"
          - name: "context_data"
            type: "TEXT JSON"
            description: "Context when error occurred"
          - name: "resolved"
            type: "BOOLEAN"
            description: "Has been resolved"
          - name: "occurred_at"
            type: "TEXT"
            description: "When error happened"
      
      user_analytics:
        purpose: "Track user contributions and activity patterns"
        columns:
          - name: "user_id"
            type: "INTEGER"
            description: "User identifier"
          - name: "emails_analyzed"
            type: "INTEGER"
            description: "Emails user has reviewed"
          - name: "feedback_given"
            type: "INTEGER"
            description: "Feedback submissions"
          - name: "emails_deleted"
            type: "INTEGER"
            description: "User-initiated deletions"
          - name: "accuracy_contributions"
            type: "INTEGER"
            description: "Contributions to accuracy"
          - name: "last_activity"
            type: "TEXT"
            description: "Last user activity"
  
  database_indexes_performance:
    primary_performance_indexes:
      core_email_processing: |
        CREATE INDEX idx_processed_emails_bulletproof_timestamp ON processed_emails_bulletproof(timestamp);
        CREATE INDEX idx_processed_emails_bulletproof_action ON processed_emails_bulletproof(action);
        CREATE INDEX idx_processed_emails_bulletproof_session ON processed_emails_bulletproof(session_id);
        CREATE INDEX idx_processed_emails_bulletproof_domain ON processed_emails_bulletproof(sender_domain);
      
      session_account_management: |
        CREATE INDEX idx_accounts_email ON accounts(email_address);
        CREATE INDEX idx_sessions_account ON sessions(account_id);
        CREATE INDEX idx_sessions_time ON sessions(start_time);
      
      domain_spam_analysis: |
        CREATE INDEX idx_domains_domain ON domains(domain);
        CREATE INDEX idx_domains_risk ON domains(risk_score);
        CREATE INDEX idx_spam_categories_category ON spam_categories(category);
      
      user_feedback_flags: |
        CREATE INDEX idx_user_feedback_uid ON user_feedback(email_uid);
        CREATE INDEX idx_user_feedback_timestamp ON user_feedback(timestamp);
        CREATE INDEX idx_email_flags_lookup ON email_flags(email_uid, folder_name, account_id);
        CREATE UNIQUE INDEX idx_email_flags_unique ON email_flags(email_uid, folder_name, account_id) 
          WHERE is_active = TRUE;
      
      vendor_intelligence_system: |
        CREATE INDEX idx_vendor_preferences_lookup ON user_vendor_preferences(user_id, vendor_domain);
        CREATE INDEX idx_vendor_patterns_lookup ON vendor_email_patterns(vendor_domain, pattern_type);
        CREATE INDEX idx_classification_history_vendor ON vendor_classification_history(vendor_domain);
      
      system_operations: |
        CREATE INDEX idx_logs_timestamp ON logs(timestamp);
        CREATE INDEX idx_logs_level ON logs(level);
        CREATE INDEX idx_logs_category ON logs(category);
        CREATE INDEX idx_performance_metrics_time ON performance_metrics(recorded_at);
    
    query_optimization_strategies:
      - "Email Processing Queries: Optimized for timestamp and action filtering"
      - "Domain Analysis: Fast lookups by domain name and risk score"
      - "User Feedback: Indexed for rapid feedback retrieval and processing"
      - "Session Management: Optimized for account-based and time-based queries"
      - "Flag Operations: Composite index for unique constraint and fast lookups"
  
  schema_evolution_migration_system:
    version_management:
      current_schema: "Version 5"
      version_tracking: "schema_version table with timestamps"
      migration_strategy: "Automated detection and upgrade"
      fallback_plan: "Complete database recreation if migration fails"
    
    migration_history:
      - version: "v1"
        date: "2025-06-04"
        changes: "Initial schema with core tables"
      - version: "v2"
        date: "2025-06-08"
        changes: "Added user_feedback table"
      - version: "v3"
        date: "2025-06-09"
        changes: "Added user_analytics and immediate_deletions"
      - version: "v4"
        date: "2025-06-15"
        changes: "Added vendor intelligence tables"
      - version: "v5"
        date: "2025-06-22"
        changes: "Added processed_emails_bulletproof as primary table"
    
    migration_features:
      - "Automatic Detection: Checks version on database connection"
      - "Data Preservation: Existing data maintained during upgrades"
      - "Error Recovery: Graceful fallback to database recreation"
      - "Logging: All migration steps logged for audit trail"
  
  table_relationships_foreign_keys:
    primary_relationships: |
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
    
    data_flow_architecture:
      - flow: "Setup Flow"
        path: "accounts → configurations → filter_terms"
      - flow: "Processing Flow"
        path: "accounts → sessions → processed_emails_bulletproof"
      - flow: "Analysis Flow"
        path: "domains → spam_categories → adaptive_patterns"
      - flow: "Learning Flow"
        path: "user_feedback → learning_events → model_performance_history"
      - flow: "Protection Flow"
        path: "email_flags → flag checking during processing"
      - flow: "Monitoring Flow"
        path: "logs → performance_metrics → error_reports"
  
  database_configuration_operations:
    connection_management:
      file_location: "mail_filter.db in project root directory"
      connection_pool: "Thread-local connections with automatic cleanup"
      timeout_settings: "30-second connection timeout"
      journal_mode: "DELETE mode (not WAL) to reduce file handles"
      foreign_keys: "Enabled for referential integrity"
    
    backup_recovery_strategy:
      raw_data_backup: "JSON backup stored in raw_data columns"
      emergency_logging: "Fallback to file logging on database failure"
      connection_redundancy: "Multiple connection attempt strategies"
      schema_recreation: "Automatic fallback for corrupted databases"
    
    performance_characteristics:
      database_size: "17.4MB (efficient for current scale)"
      query_performance: "Sub-millisecond for indexed queries"
      concurrent_access: "Thread-safe with proper locking"
      memory_usage: "Minimal memory footprint with lazy loading"
  
  future_scalability_considerations:
    current_limitations:
      - "SQLite: Single-writer limitation for high concurrency"
      - "File Size: Will need sharding/partitioning as data grows"
      - "Complex Queries: Some analytics queries could benefit from OLAP database"
    
    migration_path_postgresql:
      - "Database Abstraction Layer: Already designed in database.py"
      - "Schema Translation: SQLite → PostgreSQL type mapping"
      - "Connection Pooling: Upgrade to production-grade pool"
      - "Partitioning Strategy: Time-based partitioning for large tables"
      - "Replication: Master-replica setup for read scaling"
    
    optimization_opportunities:
      - "Table Partitioning: By date for processed_emails_bulletproof"
      - "Archive Strategy: Move old data to archive tables"
      - "Materialized Views: For complex analytics queries"
      - "Read Replicas: For reporting and analytics workloads"
  
  metadata:
    built_by: "ATLAS & Bobble - Intelligent Email Security Through Data"
    last_updated: "2025-06-23"