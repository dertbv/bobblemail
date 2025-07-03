system_architecture:
  title: "Email Filter System Architecture"
  overview: "Comprehensive email security system combining machine learning, rule-based filtering, and web-based management interfaces"
  accuracy: "95.6%+ spam detection accuracy"
  core_mission: "Protect inbox integrity while providing intelligent, user-controlled email management"
  
  high_level_system_flow:
    - component: "IMAP Email Sources"
      icon: "📧"
    - component: "Email Processor (main.py)"
      icon: "🔍"
    - component: "ML Pipeline (Ensemble Hybrid Classifier)"
      icon: "🤖"
    - component: "Database Storage (SQLite)"
      icon: "📊"
    - component: "Web Interface & CLI Management"
      icon: "🌐"
    - component: "Analytics & Reporting"
      icon: "📈"
  
  system_components:
    user_interfaces:
      cli_interface:
        file: "main.py"
        purpose: "Primary command-line interface for email processing"
        key_features:
          - "Single account filtering"
          - "Batch processing (all accounts)"
          - "Configuration management"
          - "Email action viewer & export"
          - "Web app management"
        entry_points: "Main menu with 6 core options"
        target_users: "System administrators, power users"
      
      web_interface:
        files: ["web_app.py", "FastAPI"]
        purpose: "User-friendly web dashboard for email management"
        key_features:
          - "Account selection and preview"
          - "Real-time processing with progress feedback"
          - "Email flagging system (protect/delete overrides)"
          - "Analytics and reporting dashboards"
          - "Single-account and batch processing modes"
        technology: "FastAPI + HTML templates"
        target_users: "End users, daily email management"
    
    machine_learning_pipeline:
      ensemble_hybrid_classifier:
        file: "ensemble_hybrid_classifier.py"
        purpose: "Core ML engine combining multiple detection methods"
        components:
          - "Gaussian Naive Bayes for continuous features"
          - "Multinomial Naive Bayes for discrete features"
          - "Domain validation and authentication checking"
          - "Confidence-based decision making"
        accuracy_target: "95.6%+ spam detection rate"
        learning: "Continuous improvement through user feedback"
      
      feature_extraction:
        file: "ml_feature_extractor.py"
        purpose: "Convert raw emails into ML-ready feature vectors"
        features_extracted:
          - "Subject line patterns"
          - "Sender domain characteristics"
          - "Content keywords and phrases"
          - "Authentication signals (SPF, DKIM, DMARC)"
          - "Structural email properties"
      
      category_classification:
        file: "ml_category_classifier.py"
        purpose: "Classify spam into specific categories for reporting"
        categories: ["Financial", "Phishing", "Health", "Adult", "Brand Impersonation"]
        use: "Enhanced analytics and targeted filtering improvements"
    
    data_management_layer:
      database_manager:
        file: "database.py"
        technology: "SQLite with connection pooling"
        schema_version: 5
        versioned_migrations: true
        key_tables:
          sessions: "Processing run summaries"
          email_flags: "User override flags (protect/delete)"
          accounts: "Email account configurations"
          filter_terms: "Keyword-based filtering rules"
          processed_emails_bulletproof: "Historical email actions"
        features: ["Thread-safe operations", "Automatic schema upgrades"]
      
      logging_system:
        file: "db_logger.py"
        purpose: "Bulletproof email action logging with multiple fallback methods"
        redundancy: "Database → File → Console fallbacks"
        data_integrity: "Never lose email processing history"
        performance: "Rate limiting and efficient batching"
    
    configuration_management:
      settings_management:
        file: "settings.py"
        purpose: "Centralized configuration for all system components"
        scope: "ML thresholds, processing options, system behavior"
        integration: "Used by CLI, web interface, and ML pipeline"
      
      account_credentials:
        file: "db_credentials.py"
        purpose: "Secure IMAP account management"
        features: ["Encrypted storage", "Multiple provider support"]
        providers: ["Gmail", "iCloud", "Outlook", "Yahoo", "Custom IMAP"]
      
      keyword_processing:
        file: "keyword_processor.py"
        purpose: "High-performance rule-based email filtering"
        optimization: ["Compiled regex patterns", "Optimized search algorithms"]
        integration: "Works alongside ML for comprehensive detection"
    
    processing_controllers:
      email_processor:
        file: "email_processor.py"
        purpose: "Core email processing engine"
        workflow:
          - step: 1
            action: "IMAP connection and email retrieval"
          - step: 2
            action: "ML feature extraction and classification"
          - step: 3
            action: "User flag override checking"
          - step: 4
            action: "Deletion/preservation decisions"
          - step: 5
            action: "Logging and analytics updates"
        safety: "Extensive error handling and rollback capabilities"
      
      processing_controller:
        file: "processing_controller.py"
        purpose: "Orchestrates different processing modes"
        modes: ["Single account", "Batch processing", "Preview mode"]
        integration: "Bridges CLI/web interfaces with core processing"
  
  data_flow_architecture:
    email_processing_flow:
      - step: 1
        action: "IMAP Connection"
        icon: "📧"
      - step: 2
        action: "Email Retrieval & Headers Parse"
        icon: "📥"
      - step: 3
        action: "Feature Extraction (ML Pipeline)"
        icon: "🔍"
      - step: 4
        action: "Spam Classification (Ensemble Model)"
        icon: "🤖"
      - step: 5
        action: "User Flag Override Check"
        icon: "🛡️"
      - step: 6
        action: "Final Decision (Delete/Preserve)"
        icon: "⚖️"
      - step: 7
        action: "Database Logging"
        icon: "📊"
      - step: 8
        action: "Analytics Update"
        icon: "📈"
    
    web_interface_flow:
      - step: 1
        action: "User Selects Account"
        icon: "🌐"
      - step: 2
        action: "Preview Mode (Optional)"
        icon: "🔍"
      - step: 3
        action: "Processing Trigger"
        icon: "⚡"
      - step: 4
        action: "Real-time Progress Updates"
        icon: "📊"
      - step: 5
        action: "Results Display + Email Table"
        icon: "📋"
      - step: 6
        action: "User Flag Actions (Optional)"
        icon: "🏷️"
    
    learning_feedback_flow:
      - step: 1
        action: "User Flags Email (Protect/Delete)"
        icon: "👤"
      - step: 2
        action: "Flag Stored in Database"
        icon: "📝"
      - step: 3
        action: "Next Processing Respects Flags"
        icon: "🔄"
      - step: 4
        action: "Analytics Track Override Patterns"
        icon: "📊"
      - step: 5
        action: "Future: ML Model Retraining"
        icon: "🧠"
  
  integration_points:
    cli_web_interface:
      shared_database: "Both interfaces read/write same SQLite database"
      shared_processing: "Both use identical processing_controller functions"
      shared_configuration: "Same settings.py and credential management"
      session_coordination: "Web app can be launched from CLI menu"
    
    ml_database:
      training_data: "ML models train on historical email data"
      feature_storage: "Extracted features cached for performance"
      model_persistence: "Trained models stored in database"
      performance_tracking: "Accuracy metrics logged per session"
    
    processing_analytics:
      real_time_logging: "Every email action logged immediately"
      aggregated_metrics: "Session summaries for dashboard display"
      historical_analysis: "Long-term trends and pattern detection"
      user_behavior: "Flag usage patterns and override statistics"
  
  performance_characteristics:
    throughput:
      single_account: "~100-500 emails/minute (depends on ML complexity)"
      batch_mode: "Parallel processing across multiple accounts"
      web_interface: "Responsive with real-time progress updates"
    
    accuracy:
      target: "95.6%+ spam detection accuracy"
      current: "Consistently meeting/exceeding target"
      improvement: "Continuous learning from user feedback"
    
    scalability:
      database: "SQLite suitable for single-user deployments"
      future: "PostgreSQL migration planned for multi-user scenarios"
      memory: "Efficient feature caching and connection pooling"
  
  security_reliability:
    data_protection:
      credential_encryption: "IMAP credentials securely stored"
      database_integrity: "ACID compliance with SQLite"
      backup_strategy: "Database file easily backed up"
      privacy: "Email content processed locally, not transmitted"
    
    error_handling:
      graceful_degradation: "System continues operating with partial failures"
      rollback_capability: "Failed operations don't corrupt data"
      logging: "Comprehensive error tracking and debugging"
      recovery: "Automatic retry mechanisms for transient failures"
    
    user_control:
      override_system: "Users can correct any ML decision"
      preview_mode: "See actions before committing changes"
      audit_trail: "Complete history of all email actions"
      configuration: "Extensive customization of system behavior"
  
  analytics_reporting:
    real_time_metrics:
      processing_status: "Live updates during email processing"
      accuracy_tracking: "Per-session and overall accuracy metrics"
      category_breakdown: "Spam type distribution and trends"
    
    historical_analysis:
      performance_trends: "Accuracy over time"
      volume_analysis: "Email processing patterns"
      user_behavior: "Flag usage and override patterns"
      system_health: "Error rates and performance metrics"
    
    optimization_tools:
      keyword_analyzer: "Identifies effective vs unused filter terms"
      performance_profiler: "Bottleneck identification and optimization"
      database_analytics: "Storage usage and query performance"
  
  future_architecture_considerations:
    scalability_enhancements:
      - "Multi-user Support: User authentication and isolation"
      - "Distributed Processing: Microservices architecture"
      - "Cloud Integration: AWS/Azure deployment options"
    
    ml_pipeline_evolution:
      - "Advanced Models: Deep learning and transformer models"
      - "Real-time Learning: Immediate adaptation to new spam patterns"
      - "Federated Learning: Privacy-preserving collaborative improvement"
    
    integration_opportunities:
      - "Email Client Plugins: Direct integration with Outlook, Thunderbird"
      - "API Ecosystem: RESTful APIs for third-party integrations"
      - "Mobile Interface: iOS/Android apps for management"
  
  architectural_philosophy: "Effective email security requires the perfect harmony of machine intelligence and human oversight. Like a beautiful song, each component plays its part in creating a symphony of protection that keeps your inbox safe while respecting your communication needs."
  
  metadata:
    built_by: "ATLAS & Bobble"
    created: "2025-06-23"
    version: "1.0"
    system_version: "Email Filter System v5.0"