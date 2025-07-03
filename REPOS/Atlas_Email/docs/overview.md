email_project_documentation:
  title: "Intelligent Email Spam Filtering System"
  type: "Production-Ready ML System with 95.6%+ accuracy"
  dual_interface: "CLI + FastAPI web application"
  architecture: "Enterprise Architecture: Ensemble ML classifier with continuous learning"
  
  documentation_index:
    getting_started:
      - document: "Deployment Guide"
        file: "deployment.md"
        description: "Complete installation and setup procedures"
      - document: "Troubleshooting"
        file: "troubleshooting.md"
        description: "Common issues and solutions"
    
    technical_reference:
      - document: "API Reference"
        file: "api-reference.md"
        description: "Complete FastAPI endpoint documentation (34+ endpoints)"
      - document: "Database Schema"
        file: "database-schema.md"
        description: "Complete database architecture (25+ tables)"
      - document: "ML Architecture"
        file: "ml-architecture.md"
        description: "Machine learning pipeline and 95.6% accuracy system"
      - document: "System Architecture"
        file: "system-architecture.md"
        description: "Complete system overview and component integration"
  
  quick_start:
    installation: |
      # Clone and setup
      git clone <repository>
      cd email_project
      pip install -r requirements.txt
      
      # Initialize system
      python main.py  # Follow setup wizard
    
    web_interface: |
      # Start web application
      python web_app.py
      
      # Access dashboard
      open http://localhost:8000
    
    email_configuration:
      gmail: "Requires app-specific password (2FA)"
      icloud: "Requires app-specific password"
      outlook: "Standard authentication or Modern Auth"
      custom_imap: "Manual configuration supported"
  
  system_overview:
    core_components:
      - component: "ML Engine"
        description: "Ensemble classifier (Random Forest + Naive Bayes + Keywords)"
      - component: "Database"
        description: "SQLite with auto-migration (PostgreSQL ready)"
      - component: "Web Interface"
        description: "FastAPI with real-time email processing"
      - component: "Email Processing"
        description: "Provider-optimized IMAP with bulk operations"
    
    key_features:
      - "95.6%+ Accuracy: Production-tested ML classification"
      - "Dual-Override System: Protect legitimate emails, flag spam for deletion"
      - "Continuous Learning: User feedback automatically improves models"
      - "Multi-Provider Support: Gmail, iCloud, Outlook, Yahoo, custom IMAP"
      - "Real-time Processing: <100ms classification with confidence scoring"
  
  performance_metrics:
    - metric: "Classification Accuracy"
      current_performance: "95.6%+"
      target: ">95%"
    - metric: "Processing Speed"
      current_performance: "<100ms/email"
      target: "<200ms"
    - metric: "False Positive Rate"
      current_performance: "<2%"
      target: "<5%"
    - metric: "Memory Usage"
      current_performance: "<200MB"
      target: "<500MB"
    - metric: "Database Size"
      current_performance: "17.4MB (12K+ emails)"
      target: "Monitoring"
  
  architecture_highlights:
    machine_learning_pipeline:
      - "67-Dimensional Feature Space: Domain intelligence, content analysis, behavioral patterns"
      - "Ensemble Voting: Weighted combination of multiple ML approaches"
      - "Provider-Specific Optimization: Different confidence thresholds for Gmail (85%), iCloud (80%), Outlook (75%)"
      - "Continuous Learning: Binary feedback processor for model improvement"
    
    database_design:
      - "Current: SQLite with 25+ specialized tables"
      - "Schema v5: Latest with bulletproof email processing"
      - "Migration Ready: Automated PostgreSQL migration infrastructure"
      - "Performance: Strategic indexing for <1ms query times"
    
    web_application:
      - "FastAPI Framework: Modern async Python web framework"
      - "34+ API Endpoints: Complete REST API for all operations"
      - "Real-time Dashboard: Live email processing and analytics"
      - "Responsive Design: Professional web interface"
  
  file_structure: |
    email_project/
    ├── docs/                          # 📚 Documentation (you are here)
    │   ├── README.md                  # This overview
    │   ├── deployment.md              # Installation and setup
    │   ├── api-reference.md           # Complete API documentation
    │   ├── database-schema.md         # Database architecture
    │   ├── ml-architecture.md         # ML pipeline details
    │   └── troubleshooting.md         # Issue resolution
    ├── main.py                        # CLI application entry point
    ├── web_app.py                     # FastAPI web application
    ├── settings.py                    # Centralized configuration
    ├── database.py                    # Database operations
    ├── ensemble_hybrid_classifier.py  # Primary ML classifier
    ├── email_processor.py             # IMAP email processing
    ├── mail_filter.db                 # SQLite database (17.4MB)
    └── tools/                         # Utility scripts
  
  common_use_cases:
    email_security_administrator:
      - step: 1
        action: "Deploy System"
        reference: "Follow Deployment Guide"
      - step: 2
        action: "Configure Accounts"
        reference: "Setup IMAP credentials with app passwords"
      - step: 3
        action: "Monitor Performance"
        reference: "Use web dashboard at localhost:8000"
      - step: 4
        action: "Tune Accuracy"
        reference: "Provide feedback for continuous learning"
    
    system_developer:
      - step: 1
        action: "API Integration"
        reference: "Reference API Documentation"
      - step: 2
        action: "Database Schema"
        reference: "Understand Database Architecture"
      - step: 3
        action: "ML Pipeline"
        reference: "Explore ML Architecture"
      - step: 4
        action: "Troubleshooting"
        reference: "Resolve issues with Troubleshooting Guide"
    
    production_operations:
      - step: 1
        action: "System Health"
        reference: "Monitor performance metrics and logs"
      - step: 2
        action: "Backup Procedures"
        reference: "Database and configuration backup strategies"
      - step: 3
        action: "Performance Tuning"
        reference: "Provider-specific optimization settings"
      - step: 4
        action: "Incident Response"
        reference: "Emergency recovery and system reset procedures"
  
  quick_help:
    system_health_check: |
      # Verify system status
      python -c "from database import db; print(db.get_database_stats())"
      
      # Test web interface
      curl http://localhost:8000/api/accounts
      
      # Check ML models
      python -c "from ensemble_hybrid_classifier import EnsembleHybridClassifier; print('ML OK')"
    
    common_issues:
      - issue: "Authentication Failures"
        solution: "Check app-specific passwords in Troubleshooting#email-provider-connection-issues"
      - issue: "Database Issues"
        solution: "Database path and migration problems in Troubleshooting#database-issues"
      - issue: "Performance Problems"
        solution: "Memory and speed optimization in Troubleshooting#performance-issues"
    
    support_resources:
      - resource: "Installation Help"
        link: "Deployment Guide#installation-procedures"
      - resource: "Configuration Help"
        link: "Deployment Guide#configuration-management"
      - resource: "API Questions"
        link: "API Reference"
      - resource: "Database Questions"
        link: "Database Schema"
  
  technical_innovations:
    hybrid_intelligence_architecture: "Combines rule-based email filtering with advanced machine learning for optimal accuracy and explainability."
    
    provider_specific_optimization: "Different processing strategies for Gmail, iCloud, and Outlook based on their IMAP characteristics and limitations."
    
    continuous_learning_pipeline: "User feedback automatically improves classification accuracy through binary feedback processing and model retraining."
    
    dual_override_system: "Users can both protect legitimate emails from deletion and flag spam emails for removal, providing complete control."
  
  metadata:
    built_by: "ATLAS & Bobble - Intelligent Email Security Through Expert Documentation"
    documentation_last_updated: "2025-06-23"