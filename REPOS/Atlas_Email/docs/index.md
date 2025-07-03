email_project_documentation_hub:
  title: "Email Project - Technical Documentation Hub"
  type: "Professional Documentation Suite"
  description: "Complete technical documentation for the Email Project - a production-ready, ML-powered spam filtering system achieving 95.6%+ accuracy with enterprise-grade architecture"
  
  documentation_library:
    getting_started:
      deployment_guide:
        file: "deployment.md"
        description: "Complete installation, configuration, and deployment procedures"
        contents:
          - "System requirements and dependencies"
          - "Step-by-step installation procedures"
          - "Email provider configuration (Gmail, iCloud, Outlook)"
          - "Production deployment with Docker and systemd"
          - "Environment variables and security configuration"
          - "Performance optimization and monitoring setup"
      
      troubleshooting_guide:
        file: "troubleshooting.md"
        description: "Comprehensive issue resolution and system recovery"
        contents:
          - "Database connection and schema issues"
          - "Email provider authentication problems"
          - "ML model loading and accuracy issues"
          - "Web interface and performance problems"
          - "Emergency recovery procedures"
          - "Health checks and diagnostic commands"
    
    technical_reference:
      api_reference:
        file: "api-reference.md"
        description: "Complete FastAPI endpoint documentation (34+ endpoints)"
        contents:
          - "Web pages and HTML responses"
          - "Timer management and batch processing APIs"
          - "User feedback and ML training endpoints"
          - "Email flagging and protection systems"
          - "Account management and validation APIs"
          - "Request/response examples and usage patterns"
      
      database_schema:
        file: "database-schema.md"
        description: "Complete database architecture (25+ tables, 17.4MB)"
        contents:
          - "Core email processing engine with bulletproof table"
          - "Machine learning training and feedback systems"
          - "Vendor intelligence and user preference management"
          - "Performance indexes and query optimization"
          - "Schema evolution and migration procedures"
          - "PostgreSQL migration readiness"
      
      ml_architecture:
        file: "ml-architecture.md"
        description: "Machine learning pipeline and 95.6% accuracy system"
        contents:
          - "Ensemble hybrid classifier architecture"
          - "67-dimensional feature extraction pipeline"
          - "Training data sources and continuous learning"
          - "Real-time prediction and confidence scoring"
          - "Performance metrics and model optimization"
          - "User feedback integration and model improvement"
      
      system_architecture:
        file: "system-architecture.md"
        description: "Complete system overview and component integration"
        contents:
          - "High-level system flow and data architecture"
          - "Component relationships and integration points"
          - "Performance characteristics and scalability"
          - "Security and reliability design principles"
          - "Analytics and reporting capabilities"
          - "Future architecture considerations"
  
  system_architecture_overview:
    diagram: |
      ┌─────────────────────────────────────────────────────────────┐
      │                     Email Project Architecture              │
      ├─────────────────────────────────────────────────────────────┤
      │                                                             │
      │  ┌─────────────────┐    ┌──────────────────┐               │
      │  │   CLI Interface │    │  Web Interface   │               │
      │  │    (main.py)    │    │   (web_app.py)   │               │
      │  └─────────────────┘    └──────────────────┘               │
      │           │                       │                        │
      │           └───────────┬───────────┘                        │
      │                       │                                    │
      │  ┌─────────────────────────────────────────────────────────┐ │
      │  │              Processing Controller                       │ │
      │  └─────────────────────────────────────────────────────────┘ │
      │                       │                                    │
      │  ┌─────────────────────────────────────────────────────────┐ │
      │  │              Ensemble ML Classifier                     │ │
      │  │  Random Forest (40%) + Naive Bayes (30%) + Keywords    │ │
      │  └─────────────────────────────────────────────────────────┘ │
      │                       │                                    │
      │  ┌─────────────────────────────────────────────────────────┐ │
      │  │                 SQLite Database                         │ │
      │  │         25+ Tables, Schema v5, 17.4MB                  │ │
      │  └─────────────────────────────────────────────────────────┘ │
      └─────────────────────────────────────────────────────────────┘
  
  quick_reference:
    performance_metrics:
      - component: "ML Accuracy"
        current_performance: "95.6%+"
        documentation_link: "ML Architecture#performance-metrics"
      - component: "Processing Speed"
        current_performance: "<100ms/email"
        documentation_link: "ML Architecture#real-time-prediction-pipeline"
      - component: "API Endpoints"
        current_performance: "34+ endpoints"
        documentation_link: "API Reference"
      - component: "Database Size"
        current_performance: "17.4MB (12K+ emails)"
        documentation_link: "Database Schema#database-overview"
      - component: "False Positive Rate"
        current_performance: "<2%"
        documentation_link: "ML Architecture#model-performance-analysis"
    
    system_components:
      - component: "CLI App"
        file_location: "main.py"
        documentation_link: "Deployment Guide#local-development-deployment"
      - component: "Web App"
        file_location: "web_app.py"
        documentation_link: "API Reference"
      - component: "Database"
        file_location: "mail_filter.db"
        documentation_link: "Database Schema"
      - component: "ML Models"
        file_location: "*.pkl, *.json"
        documentation_link: "ML Architecture"
      - component: "Configuration"
        file_location: "settings.py"
        documentation_link: "Deployment Guide#configuration-management"
    
    provider_support:
      - email_provider: "Gmail"
        authentication: "App Password"
        batch_size: "50 emails"
        documentation_link: "Deployment Guide#email-account-configuration"
      - email_provider: "iCloud"
        authentication: "App Password"
        batch_size: "25 emails"
        documentation_link: "Troubleshooting#icloud-configuration"
      - email_provider: "Outlook"
        authentication: "Standard/OAuth"
        batch_size: "30 emails"
        documentation_link: "Deployment Guide#provider-specific-solutions"
      - email_provider: "Yahoo"
        authentication: "App Password"
        batch_size: "40 emails"
        documentation_link: "Deployment Guide#supported-providers-with-optimizations"
  
  navigation_by_role:
    system_administrator:
      - step: 1
        action: "Start with Deployment Guide for complete setup"
        link: "deployment.md"
      - step: 2
        action: "Reference Troubleshooting for operational issues"
        link: "troubleshooting.md"
      - step: 3
        action: "Monitor using web interface at http://localhost:8000"
    
    developer_integrator:
      - step: 1
        action: "Review API Reference for integration endpoints"
        link: "api-reference.md"
      - step: 2
        action: "Study Database Schema for data structures"
        link: "database-schema.md"
      - step: 3
        action: "Understand ML Architecture for ML integration"
        link: "ml-architecture.md"
    
    data_scientist_ml_engineer:
      - step: 1
        action: "Deep dive into ML Architecture for model details"
        link: "ml-architecture.md"
      - step: 2
        action: "Reference Database Schema for training data"
        link: "database-schema.md"
      - step: 3
        action: "Use API Reference for feedback endpoints"
        link: "api-reference.md"
    
    operations_support:
      - step: 1
        action: "Master Troubleshooting Guide for issue resolution"
        link: "troubleshooting.md"
      - step: 2
        action: "Use Deployment Guide for maintenance procedures"
        link: "deployment.md"
      - step: 3
        action: "Monitor system health with diagnostic commands"
  
  quick_actions:
    system_health_check: |
      # Verify all components
      python -c "from database import db; print('Database:', 'OK' if db.get_connection() else 'FAIL')"
      curl -s http://localhost:8000/api/accounts > /dev/null && echo "Web API: OK" || echo "Web API: FAIL"
      python -c "from ensemble_hybrid_classifier import EnsembleHybridClassifier; print('ML Models: OK')"
    
    emergency_procedures:
      - procedure: "System Reset"
        link: "Troubleshooting Guide#emergency-recovery-procedures"
      - procedure: "Database Recovery"
        link: "Troubleshooting Guide#database-issues"
      - procedure: "Configuration Reset"
        link: "Deployment Guide#configuration-recovery"
    
    performance_optimization:
      - area: "ML Tuning"
        link: "ML Architecture#performance-optimization"
      - area: "Database Optimization"
        link: "Database Schema#performance-characteristics"
      - area: "Provider Settings"
        link: "Deployment Guide#imap-performance-optimization"
  
  documentation_standards:
    format_conventions:
      - "File Names: kebab-case (e.g., api-reference.md)"
      - "Headers: Hierarchical with emoji indicators"
      - "Code Blocks: Language-specific syntax highlighting"
      - "Cross-References: Relative links between documents"
      - "Examples: Production-ready code samples"
    
    update_frequency:
      documentation_version: "Synchronized with code releases"
      last_updated: "2025-06-23"
      review_cycle: "Updated with each major feature release"
      accuracy_verification: "Tested against production system"
  
  about_documentation:
    description: "This documentation suite represents the culmination of extensive system development and real-world production testing. Every procedure, configuration, and troubleshooting step has been validated against the actual running system."
    
    built_by: "ATLAS & Bobble - where technical excellence meets intelligent documentation design"
    
    achievement: "The architecture achieves 95.6%+ classification accuracy while maintaining <100ms processing speed, demonstrating that sophisticated ML systems can be both powerful and practical."
  
  metadata:
    type: "Professional Documentation Suite"
    last_updated: "2025-06-23"