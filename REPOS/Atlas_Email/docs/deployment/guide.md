deployment_guide:
  title: "Email Project - Complete Deployment Guide"
  system: "Production-ready ML spam filtering with 95.6% accuracy"
  interfaces: "CLI + FastAPI web app on localhost:8000"
  database: "SQLite (17.4MB) with auto-migration to PostgreSQL ready"
  ml_stack: "Ensemble hybrid classifier with 3-model voting system"
  
  system_overview:
    architecture_components:
      - component: "CLI Application"
        description: "Full-featured terminal interface (main.py)"
      - component: "Web Interface"
        description: "FastAPI-based dashboard (web_app.py)"
      - component: "ML Engine"
        description: "Ensemble classifier (Random Forest + Naive Bayes + Keywords)"
      - component: "Database"
        description: "SQLite with 25+ tables, schema v5 with auto-migration"
      - component: "Email Processing"
        description: "Provider-optimized IMAP with bulk operations"
    
    key_features:
      - "95.6%+ Classification Accuracy with real-time processing"
      - "Multi-Provider Support: Gmail, iCloud, Outlook, Yahoo, custom IMAP"
      - "Continuous Learning: User feedback improves ML models automatically"
      - "Dual-Override System: Protect legitimate emails, flag spam for deletion"
      - "Production Monitoring: Comprehensive logging and analytics"
  
  system_requirements:
    python_environment:
      - requirement: "Python Version"
        minimum: "3.8+"
        recommended: "3.13+"
      - requirement: "Operating System"
        minimum: "Linux/macOS/Windows"
        recommended: "Linux/macOS"
      - requirement: "Memory"
        minimum: "2GB RAM"
        recommended: "4GB+ RAM"
      - requirement: "Storage"
        minimum: "1GB available"
        recommended: "5GB+ (database growth)"
      - requirement: "CPU"
        minimum: "Single core"
        recommended: "Multi-core (ML processing)"
    
    network_requirements:
      internet_connection: "Stable broadband for IMAP operations"
      ports: "8000 (web interface), 993 (IMAP SSL)"
      email_access: "IMAP-enabled accounts with app-specific passwords"
  
  installation_procedures:
    quick_start_installation:
      steps: |
        # 1. Clone repository
        git clone <repository_url>
        cd email_project
        
        # 2. Install Python dependencies
        pip install -r requirements.txt
        
        # 3. Initial setup and database creation
        python main.py
        
        # 4. Start web interface (optional)
        python web_app.py
    
    dependencies_installation:
      core_dependencies: |
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
      
      development_dependencies: |
        pip install pytest pytest-cov black flake8 jupyter
    
    system_verification: |
      # Verify Python version
      python --version  # Should be 3.8+
      
      # Test core dependencies
      python -c "import fastapi, uvicorn, sklearn, numpy; print('Dependencies OK')"
      
      # Verify ML models can load
      python -c "from ensemble_hybrid_classifier import EnsembleHybridClassifier; print('ML OK')"
  
  database_setup:
    sqlite_database:
      automatic_initialization: |
        # Database auto-creates on first run
        from database import db
        connection = db.get_connection()  # Creates mail_filter.db with schema v5
      
      database_specifications:
        file: "mail_filter.db (currently 17.4MB with production data)"
        schema_version: "5 (latest with bulletproof email processing)"
        tables:
          - name: "processed_emails_bulletproof"
            records: 12238
          - name: "sessions"
            records: 634
          - name: "email_flags"
            records: 90
          - name: "user_feedback"
            records: 25
          - name: "logs"
            records: 9112
      
      migration_system:
        automatic: "Detects schema version and auto-upgrades"
        fallback: "Recreation if migration fails"
        backup: "Manual backup recommended before upgrades"
    
    future_postgresql_migration:
      infrastructure_ready: |
        # Environment variables for PostgreSQL
        export DATABASE_URL="postgresql://user:pass@localhost:5432/email_filter"
        export DB_TYPE="postgresql"  # Switches from SQLite
        
        # Docker composition ready
        docker-compose up -d postgres redis
  
  configuration_management:
    centralized_configuration:
      file: "settings.py"
      description: "All settings consolidated in single file with environment variable overrides"
      
      core_ml_settings: |
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
    
    email_account_configuration:
      credential_storage: "Encrypted in database (migrated from JSON)"
      setup_process: "Interactive CLI configuration wizard"
      
      supported_providers:
        - provider: "Gmail"
          authentication: "App Password"
          batch_size: 50
          special_features: "UID operations, high threshold"
        - provider: "iCloud"
          authentication: "App Password"
          batch_size: 25
          special_features: "Bulk operations only, conservative"
        - provider: "Outlook"
          authentication: "Standard/OAuth"
          batch_size: 30
          special_features: "Standard IMAP operations"
        - provider: "Yahoo"
          authentication: "App Password"
          batch_size: 40
          special_features: "Standard with authentication"
        - provider: "Custom IMAP"
          authentication: "Manual config"
          batch_size: 35
          special_features: "Full manual configuration"
      
      app_password_setup: |
        # Gmail: https://myaccount.google.com/apppasswords
        # iCloud: https://appleid.apple.com/account/manage  
        # Yahoo: https://login.yahoo.com/account/security
  
  security_configuration:
    email_authentication_security:
      provider_requirements:
        gmail: "App-specific password (2FA required)"
        icloud: "App-specific password (2FA recommended)"
        outlook: "Standard auth or Modern Auth"
        yahoo: "App-specific password for IMAP access"
      
      connection_security:
        ssl_tls: "All connections use port 993 with SSL"
        certificate_validation: "Full certificate chain verification"
        timeout_settings: "30-second connection timeout"
    
    data_security:
      credential_protection: |
        # Database storage with Fernet encryption
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        encrypted_password = Fernet(key).encrypt(password.encode())
      
      file_permissions: |
        # Set secure permissions
        chmod 600 mail_filter.db          # Database read/write owner only
        chmod 644 *.py                     # Python files readable
        chmod 700 .                       # Directory access control
    
    web_interface_security:
      development_security:
        cors: "Configured for localhost development"
        input_validation: "XSS protection on all form inputs"
        sql_injection: "Parameterized queries throughout"
        authentication: "None (localhost development setup)"
      
      production_security_considerations: |
        # For production deployment
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://yourdomain.com"],  # Restrict origins
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
  
  deployment_procedures:
    local_development_deployment:
      complete_setup: |
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
      
      email_account_configuration: |
        # CLI setup wizard
        python main.py
        # Select option 1: "Email Account Management"
        # Add accounts with provider auto-detection
        # Test connections before proceeding
      
      verification: |
        # Test email processing
        python main.py
        # Select option 3: "Preview Emails" to test classification
        
        # Test web interface
        curl http://localhost:8000/api/accounts
        # Should return JSON with configured accounts
    
    production_deployment:
      docker_deployment:
        docker_environment: |
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
        
        deployment_commands: |
          # Build and deploy
          docker-compose up -d
          
          # Check status
          docker-compose ps
          
          # View logs
          docker-compose logs -f app
      
      manual_production_setup:
        system_preparation: |
          # Ubuntu/Debian
          sudo apt-get update
          sudo apt-get install python3 python3-pip python3-venv sqlite3 nginx
          
          # CentOS/RHEL
          sudo yum install python3 python3-pip sqlite nginx
          
          # Create application user
          sudo useradd -m -s /bin/bash email-filter
          sudo su - email-filter
        
        application_installation: |
          # Setup application
          git clone <repository> /opt/email-filter
          cd /opt/email-filter
          python3 -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          
          # Initialize database
          python main.py  # Run initial setup
        
        service_configuration: |
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
        
        nginx_reverse_proxy: |
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
  
  performance_optimization:
    ml_model_optimization:
      current_production_settings: |
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
    
    imap_performance_optimization:
      provider_specific_optimizations: |
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
    
    database_performance:
      sqlite_optimizations: |
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
      
      performance_metrics:
        classification_speed: "<100ms per email"
        batch_processing: "1000+ emails/minute"
        memory_usage: "<200MB steady state"
        database_size: "17.4MB with 12K+ emails"
  
  monitoring_logging:
    application_monitoring:
      log_files:
        - file: "webapp.log"
          description: "General web app activity (260KB)"
        - file: "web_app_debug.log"
          description: "Detailed debugging information"
        - file: "webapp.pid"
          description: "Process ID for running web app"
        - file: "mail_filter_imap_log.txt"
          description: "IMAP operations and errors"
      
      database_logging: |
        -- Structured logging in SQLite
        SELECT level, category, message, timestamp 
        FROM logs 
        WHERE level IN ('ERROR', 'WARN') 
        ORDER BY timestamp DESC LIMIT 10;
        
        -- Current log statistics: 9,112 entries
        SELECT level, COUNT(*) FROM logs GROUP BY level;
    
    health_checks:
      system_health_endpoints: |
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
    
    performance_monitoring:
      key_metrics_dashboard:
        - metric: "Classification Accuracy"
          target: "95.6%+"
        - metric: "Processing Speed"
          target: "<100ms per email"
        - metric: "Memory Usage"
          target: "<200MB"
        - metric: "Database Growth"
          monitor: "Weekly"
        - metric: "Error Rates"
          target: "<1%"
      
      command_line_monitoring: |
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
  
  backup_maintenance:
    database_backup_procedures:
      daily_backup: |
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
      
      configuration_backup: |
        # Backup all configuration
        tar -czf config_backup_$(date +%Y%m%d).tar.gz \
            settings.py \
            my_keywords.txt \
            *.log
        
        # Backup ML models
        tar -czf models_backup_$(date +%Y%m%d).tar.gz \
            *.pkl *.json
    
    maintenance_tasks:
      weekly_maintenance: |
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
      
      monthly_maintenance: |
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
  
  environment_variables_reference:
    core_configuration: |
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
    
    production_environment_setup: |
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
  
  troubleshooting_common_issues:
    installation_issues:
      dependency_conflicts: |
        # Clean installation
        pip uninstall -y scikit-learn numpy matplotlib pandas
        pip install --no-cache-dir -r requirements.txt
        
        # Virtual environment (recommended)
        python -m venv email_filter_env
        source email_filter_env/bin/activate
        pip install -r requirements.txt
      
      python_version_issues: |
        # Check Python version
        python --version  # Must be 3.8+
        
        # Use specific Python version
        python3.9 -m venv email_filter_env
    
    configuration_issues:
      email_authentication_failures: |
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
      
      database_issues: |
        # Check database integrity
        sqlite3 mail_filter.db "PRAGMA integrity_check;"
        
        # Reset database (emergency)
        mv mail_filter.db mail_filter.db.backup
        python main.py  # Will recreate database
    
    performance_issues:
      slow_processing: |
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
  
  support_resources:
    directory_structure: |
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
    
    key_file_locations:
      - file: "mail_filter.db"
        description: "Database (current: 17.4MB)"
      - file: "settings.py"
        description: "Configuration (centralized)"
      - file: "webapp.log, web_app_debug.log"
        description: "Logs"
      - file: "*.pkl, *.json"
        description: "Models"
      - file: "webapp.pid"
        description: "Process (web app process tracking)"
    
    support_commands: |
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
  
  metadata:
    built_by: "ATLAS & Bobble - Intelligent Email Security Through Expert Deployment"
    last_updated: "2025-06-23"