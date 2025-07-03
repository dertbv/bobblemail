troubleshooting_guide:
  title: "Email Project - Comprehensive Troubleshooting Guide"
  system_status: "Production-ready with 95.6%+ ML accuracy"
  common_issues: "Database, IMAP, ML models, configuration"
  emergency_recovery: "Complete system reset procedures included"
  
  quick_health_check:
    system_verification_commands: |
      # Database integrity check
      python3 -c "from database import db; print(db.get_database_stats())"
      
      # ML models verification
      python3 tools/verify_ml_enabled.py
      
      # Web app status
      cat webapp.pid && curl -s http://localhost:8000/api/accounts
      
      # Provider connection test
      python3 -m config_auth
    
    current_system_status_indicators:
      database: "mail_filter.db (17.4MB, schema v5)"
      web_app: "http://localhost:8000 with webapp.pid file"
      ml_models: "95.6%+ accuracy with 3-model ensemble"
      accounts: "4 configured email accounts"
  
  database_issues:
    database_file_path_problems:
      symptoms:
        - "sqlite3.OperationalError: no such table"
        - "FileNotFoundError: mail_filter.db"
        - "Empty or corrupted database"
      
      common_causes:
        - "Database file missing from expected location"
        - "Working directory path inconsistencies (FIXED in recent refactor)"
        - "File permissions issues"
        - "Corrupted database file"
      
      solutions: |
        # Verify database location and permissions
        ls -la /Users/Badman/Desktop/email/REPOS/email_project/mail_filter.db
        chmod 644 mail_filter.db
        
        # Check database integrity
        sqlite3 mail_filter.db "PRAGMA integrity_check;"
        
        # Emergency database recreation
        mv mail_filter.db mail_filter.db.backup
        # Restart application - will recreate schema
      
      recent_fix: "All database path issues resolved with centralized absolute path resolution in 8 critical files."
    
    schema_version_mismatch:
      symptoms:
        - "sqlite3.OperationalError: no such column"
        - "Schema migration failures"
        - "Missing table errors"
      
      diagnosis: |
        -- Check current schema version
        SELECT version FROM schema_version ORDER BY id DESC LIMIT 1;
        -- Should return: 5 (latest)
      
      solutions:
        automatic_migration: "System auto-upgrades from v1-v4 to v5"
        manual_recovery: "Delete database to force recreation with latest schema"
        backup_first: "Always backup before schema changes"
    
    database_locking_issues:
      symptoms:
        - "sqlite3.OperationalError: database is locked"
        - "Connection timeouts"
        - "Hanging database operations"
      
      common_causes:
        - "Multiple application instances running"
        - "Incomplete transactions"
        - "Zombie processes holding connections"
      
      solutions: |
        # Check for multiple instances
        ps aux | grep python | grep email
        
        # Kill zombie processes
        pkill -f "python.*email"
        
        # Clear any webapp.pid locks
        rm -f webapp.pid
        
        # Database unlock (emergency)
        sqlite3 mail_filter.db ".timeout 30000" "BEGIN IMMEDIATE; ROLLBACK;"
  
  email_provider_connection_issues:
    imap_authentication_failures:
      symptoms:
        - "imaplib.IMAP4.error: [AUTHENTICATIONFAILED]"
        - "Connection refused by provider"
        - "Invalid credentials errors"
      
      provider_specific_solutions:
        gmail_configuration: |
          # Gmail requires App Password (not regular password)
          host = 'imap.gmail.com'
          port = 993
          # Steps:
          # 1. Enable 2FA on Google Account
          # 2. Generate App Password: myaccount.google.com/apppasswords
          # 3. Use App Password in configuration
        
        icloud_configuration: |
          # iCloud requires App-Specific Password
          host = 'imap.mail.me.com'  
          port = 993
          # Steps:
          # 1. Go to appleid.apple.com
          # 2. Generate App-Specific Password
          # 3. Use generated password in configuration
        
        outlook_configuration: |
          # Outlook requires OAuth or App Password
          host = 'outlook.office365.com'
          port = 993
          # Modern Auth required for new connections
    
    connection_timeout_issues:
      symptoms:
        - "socket.timeout exceptions"
        - "Very slow IMAP responses"
        - "Processing hangs on large mailboxes"
      
      optimized_provider_settings: |
        # Provider-specific batch sizes (email_processor.py)
        PROVIDER_OPTIMIZATIONS = {
            'icloud': {'batch_size': 25, 'delay': 0.1},
            'gmail': {'batch_size': 50, 'delay': 0.05}, 
            'outlook': {'batch_size': 30, 'delay': 0.1}
        }
      
      solutions:
        - "Reduce Batch Size: Smaller chunks for slow providers"
        - "Implement Delays: Prevent provider throttling"
        - "Use UID Operations: More efficient than sequence numbers"
        - "Connection Pooling: Reuse IMAP connections"
    
    folder_selection_problems:
      symptoms:
        - "imaplib.IMAP4.error: SELECT failed"
        - "Folder not found errors"
        - "Localized folder name issues"
      
      provider_specific_folder_names:
        - provider: "Gmail"
          spam_folder: "[Gmail]/Spam"
          sent_folder: "[Gmail]/Sent Mail"
          trash_folder: "[Gmail]/Trash"
        - provider: "iCloud"
          spam_folder: "Junk"
          sent_folder: "Sent Messages"
          trash_folder: "Deleted Messages"
        - provider: "Outlook"
          spam_folder: "Junk Email"
          sent_folder: "Sent Items"
          trash_folder: "Deleted Items"
      
      diagnostic_commands: |
        # List all folders for debugging
        import imaplib
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(username, password)
        print(mail.list())
  
  machine_learning_issues:
    model_loading_failures:
      symptoms:
        - "FileNotFoundError: random_forest_model.pkl"
        - "Classification returning default values"
        - "Model accuracy suddenly drops"
      
      required_model_files: |
        REPOS/email_project/
        ├── random_forest_model.pkl (40% ensemble weight)
        ├── naive_bayes_model.json (30% ensemble weight)  
        ├── ml_category_classifier.json (category classification)
        └── ml_category_classifier_scaler.pkl (feature scaling)
      
      solutions: |
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
    
    classification_accuracy_issues:
      symptoms:
        - "Too many false positives (legitimate emails marked spam)"
        - "Too many false negatives (spam emails preserved)"
        - "Confidence scores consistently low"
      
      provider_specific_confidence_thresholds: |
        ML_CONFIDENCE_THRESHOLDS = {
            'gmail': 85,    # Higher threshold (more conservative)
            'icloud': 80,   # Medium threshold
            'outlook': 75,  # Lower threshold (more aggressive)
            'default': 75
        }
      
      adjustment_guidelines:
        - "Too Many False Positives: Lower threshold by 5-10%"
        - "Too Many False Negatives: Raise threshold by 5-10%"
        - "Monitor Results: Use web interface analytics to track changes"
    
    feature_extraction_problems:
      symptoms:
        - "UnicodeDecodeError during processing"
        - "Empty feature vectors"
        - "Encoding-related crashes"
      
      robust_encoding_solution: |
        def safe_decode(raw_data):
            """Robust encoding with multiple fallbacks"""
            encodings = ['utf-8', 'iso-8859-1', 'ascii', 'cp1252', 'latin1']
            for encoding in encodings:
                try:
                    return raw_data.decode(encoding, errors="ignore")
                except (UnicodeDecodeError, LookupError):
                    continue
            return str(raw_data, errors="replace")  # Final fallback
  
  configuration_issues:
    missing_configuration_files:
      symptoms:
        - "Configuration not found errors"
        - "Default settings always used"
        - "Credentials not persisting"
      
      current_configuration_system:
        centralized: "All settings in settings.py (no JSON files)"
        database_storage: "Credentials encrypted in accounts table"
        environment_override: "Use env vars for customization"
      
      recovery_steps: |
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
    
    environment_variable_issues:
      available_environment_overrides: |
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
    
    import_dependency_issues:
      status: "RESOLVED"
      previous_symptoms:
        - "ImportError: cannot import name"
        - "Circular import errors"
        - "Module resolution failures"
      
      fixed_in_recent_refactor:
        - "Created classification_utils.py bridge module"
        - "Created config_loader.py bridge module"
        - "Eliminated all circular dependencies"
        - "Clean module boundaries established"
  
  web_interface_issues:
    fastapi_service_problems:
      symptoms:
        - "ImportError: fastapi or ImportError: uvicorn"
        - "Web interface not responding"
        - "API endpoints return 500 errors"
      
      dependencies_check: |
        # Install required packages
        pip install fastapi uvicorn
        
        # Verify web app can start
        python3 web_app.py
        # Should show: "Uvicorn running on http://localhost:8000"
    
    memory_issues_web_app:
      symptoms:
        - "High memory usage over time"
        - "Slow web interface responses"
        - "Browser timeouts"
      
      memory_optimization: |
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
    
    port_conflicts:
      symptoms:
        - "Address already in use on port 8000"
        - "Cannot start web interface"
        - "Connection refused errors"
      
      solutions: |
        # Check what's using port 8000
        lsof -i :8000
        
        # Kill existing process
        kill $(lsof -t -i:8000)
        
        # Alternative port (if needed)
        python3 web_app.py --port 8001
  
  performance_issues:
    slow_email_processing:
      symptoms:
        - "Processing takes hours for large mailboxes"
        - "Frequent timeouts"
        - "High CPU usage"
      
      performance_optimizations: |
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
    
    memory_leaks:
      symptoms:
        - "Memory usage grows over time"
        - "Application becomes unresponsive"
        - "OS memory pressure warnings"
      
      memory_management: |
        # Clear large objects after use
        def process_emails_batch(emails):
            features = extract_features(emails)
            results = classify_batch(features)
            
            # Explicit cleanup
            del features
            del emails
            gc.collect()
            
            return results
    
    database_performance:
      symptoms:
        - "Slow web interface queries"
        - "Long application startup"
        - "Database locks"
      
      optimization_strategies:
        - "Indexes: Strategic indexing on timestamp, action, session_id"
        - "Query Limits: Pagination for large result sets"
        - "Connection Pooling: Reuse database connections"
        - "Vacuum: Periodic database optimization"
      
      performance_monitoring_queries: |
        -- Performance monitoring queries
        SELECT COUNT(*) FROM processed_emails_bulletproof;  -- 12,238 emails
        SELECT COUNT(*) FROM sessions;                       -- 634 sessions
        SELECT COUNT(*) FROM logs;                          -- 9,112 logs
        
        -- Index usage verification
        EXPLAIN QUERY PLAN SELECT * FROM processed_emails_bulletproof 
        WHERE timestamp > '2025-06-01' ORDER BY timestamp DESC;
  
  domain_validation_issues:
    dns_resolution_problems:
      symptoms:
        - "Domain validation failures"
        - "DNS timeout errors"
        - "False positives on legitimate domains"
      
      dns_configuration: |
        # Multiple DNS servers with fallback
        DNS_SERVERS = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        DNS_TIMEOUT = 3  # seconds
        DNS_CACHE_TTL = 86400  # 24 hours
    
    gibberish_detection_issues:
      symptoms:
        - "Legitimate domains flagged as suspicious"
        - "International domains failing validation"
        - "Entropy calculation errors"
      
      current_settings: |
        # Entropy threshold for gibberish detection
        ML_ENTROPY_THRESHOLD = 3.2  # Balanced setting
        
        # Whitelist bypass for known domains
        LEGITIMATE_DOMAINS = [
            'unraid.net', 'inova.org', 'aetna.com', 
            'dertbv@gmail.com', 'genesismotorsamerica.com'
        ]
      
      adjustment_guidelines:
        - "Too Aggressive: Increase threshold to 3.5-4.0"
        - "Too Permissive: Decrease threshold to 2.8-3.0"
        - "Add Whitelists: For known legitimate domains"
  
  emergency_recovery_procedures:
    complete_system_reset:
      when_to_use:
        - "Multiple system failures"
        - "Corrupted database"
        - "Configuration completely broken"
        - "Major version upgrade issues"
      
      steps: |
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
    
    configuration_recovery:
      partial_reset: |
        # Reset configuration only
        python3 -c "
        from database import db
        db.execute('DELETE FROM configurations WHERE config_type != \"ACCOUNT\"')
        "
        
        # Restart with defaults
        python3 main.py
    
    model_recovery:
      retrain_all_models: |
        from binary_feedback_processor import BinaryFeedbackProcessor
        from ensemble_hybrid_classifier import EnsembleHybridClassifier
        
        # Retrain from database
        processor = BinaryFeedbackProcessor()
        processor.retrain_models()
        
        # Verify ensemble loading
        classifier = EnsembleHybridClassifier()
        print(f"Models loaded successfully: {classifier.models_loaded}")
  
  monitoring_prevention:
    health_monitoring_dashboard:
      key_metrics_to_watch:
        - metric: "Classification accuracy"
          target: ">95%"
        - metric: "Processing speed"
          target: "<100ms/email"
        - metric: "Database size"
          current: "17.4MB"
        - metric: "Memory usage"
          target: "<200MB"
        - metric: "Error rates"
          target: "<1%"
      
      web_interface_monitoring:
        - "Visit http://localhost:8000/analytics for performance metrics"
        - "Check /api/user-stats for classification statistics"
        - "Monitor /api/feedback/stats for user correction patterns"
    
    regular_maintenance_tasks:
      weekly: |
        # Database health check
        python3 -c "from database import db; print(db.get_database_stats())"
        
        # Clear old logs (optional)
        sqlite3 mail_filter.db "DELETE FROM logs WHERE timestamp < date('now', '-30 days')"
        
        # Verify ML model performance
        python3 tools/verify_ml_enabled.py
      
      monthly: |
        # Database optimization
        sqlite3 mail_filter.db "VACUUM; ANALYZE;"
        
        # Model retraining with accumulated feedback
        python3 -c "
        from binary_feedback_processor import BinaryFeedbackProcessor
        processor = BinaryFeedbackProcessor()
        processor.retrain_models()
        "
    
    prevention_best_practices:
      - "Regular Backups: Database and configuration"
      - "Monitor Logs: Check for recurring error patterns"
      - "Update Feedback: Provide user feedback for misclassifications"
      - "Performance Monitoring: Watch for degradation trends"
      - "Provider Changes: Stay updated on email provider authentication changes"
  
  getting_help:
    debug_information_to_collect: |
      # System information
      python3 --version
      pip list | grep -E "(fastapi|sqlite|scikit|numpy)"
      
      # Database status
      python3 -c "from database import db; print(db.get_database_stats())"
      
      # ML model status
      ls -la *.pkl *.json
      
      # Recent errors
      sqlite3 mail_filter.db "SELECT * FROM logs WHERE level='ERROR' ORDER BY timestamp DESC LIMIT 10"
    
    log_analysis:
      important_log_categories:
        - category: "SESSION"
          description: "Processing session errors"
        - category: "EMAIL"
          description: "Individual email processing issues"
        - category: "DOMAIN"
          description: "Domain validation problems"
        - category: "ML"
          description: "Machine learning classification issues"
        - category: "CONFIG"
          description: "Configuration loading problems"
      
      common_error_patterns:
        - "Database connection failures"
        - "IMAP authentication issues"
        - "Model loading problems"
        - "Feature extraction errors"
        - "Memory pressure warnings"
  
  metadata:
    built_by: "ATLAS & Bobble - Reliable Email Security Through Intelligent Troubleshooting"
    last_updated: "2025-06-23"