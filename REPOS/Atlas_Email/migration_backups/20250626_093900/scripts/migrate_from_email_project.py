#!/usr/bin/env python3
"""Migrate files from email_project to Atlas_Email with proper structure."""

import os
import shutil
from pathlib import Path

# Define source and destination paths
SOURCE_DIR = Path("../../email_project")
DEST_DIR = Path("..")

# File mapping: source -> destination
FILE_MAPPING = {
    # Core business logic -> src/atlas_email/core/
    "email_processor.py": "src/atlas_email/core/email_processor.py",
    "processing_controller.py": "src/atlas_email/core/processing_controller.py",
    "spam_classifier.py": "src/atlas_email/core/spam_classifier.py",
    "logical_classifier.py": "src/atlas_email/core/logical_classifier.py",
    "classification_utils.py": "src/atlas_email/core/classification_utils.py",
    "email_authentication.py": "src/atlas_email/core/email_authentication.py",
    "two_factor_email_validator.py": "src/atlas_email/core/two_factor_validator.py",
    
    # API/Web interface -> src/atlas_email/api/
    "web_app.py": "src/atlas_email/api/app.py",
    "web_app_manager.py": "src/atlas_email/api/app_manager.py",
    "email_action_viewer.py": "src/atlas_email/api/email_action_viewer.py",
    
    # CLI interface -> src/atlas_email/cli/
    "main.py": "src/atlas_email/cli/main.py",
    "menu_handler.py": "src/atlas_email/cli/menu_handler.py",
    
    # Database/Models -> src/atlas_email/models/
    "database.py": "src/atlas_email/models/database.py",
    "db_logger.py": "src/atlas_email/models/db_logger.py",
    "db_analytics.py": "src/atlas_email/models/analytics.py",
    "db_keyword_inspector.py": "src/atlas_email/models/keyword_inspector.py",
    "vendor_preferences_schema.py": "src/atlas_email/models/vendor_preferences.py",
    
    # ML/AI components -> src/atlas_email/ml/
    "ensemble_hybrid_classifier.py": "src/atlas_email/ml/ensemble_classifier.py",
    "ml_classifier.py": "src/atlas_email/ml/naive_bayes.py",
    "random_forest_classifier.py": "src/atlas_email/ml/random_forest.py",
    "ml_feature_extractor.py": "src/atlas_email/ml/feature_extractor.py",
    "ml_category_classifier.py": "src/atlas_email/ml/category_classifier.py",
    "ml_settings.py": "src/atlas_email/ml/settings.py",
    "binary_feedback_processor.py": "src/atlas_email/ml/feedback_processor.py",
    "learning_analytics.py": "src/atlas_email/ml/analytics.py",
    
    # Filters/Keywords -> src/atlas_email/filters/
    "keyword_processor.py": "src/atlas_email/filters/keyword_processor.py",
    "unified_keyword_manager.py": "src/atlas_email/filters/unified_manager.py",
    "builtin_keywords_manager.py": "src/atlas_email/filters/builtin_keywords.py",
    "category_keywords.py": "src/atlas_email/filters/category_keywords.py",
    "selective_vendor_filter.py": "src/atlas_email/filters/vendor_filter.py",
    "vendor_filter_integration.py": "src/atlas_email/filters/vendor_integration.py",
    "legitimate_business_prefixes.py": "src/atlas_email/filters/business_prefixes.py",
    
    # Utilities -> src/atlas_email/utils/
    "utils.py": "src/atlas_email/utils/general.py",
    "domain_validator.py": "src/atlas_email/utils/domain_validator.py",
    "domain_cache.py": "src/atlas_email/utils/domain_cache.py",
    "provider_utils.py": "src/atlas_email/utils/provider_utils.py",
    "regex_optimizer.py": "src/atlas_email/utils/regex_optimizer.py",
    "smart_regex_selector.py": "src/atlas_email/utils/smart_regex.py",
    "auto_batch_timer.py": "src/atlas_email/utils/batch_timer.py",
    "processing_controls.py": "src/atlas_email/utils/processing_controls.py",
    
    # Configuration -> config/
    "settings.py": "config/settings.py",
    "constants.py": "config/constants.py",
    "config_loader.py": "config/loader.py",
    "config_auth.py": "config/auth.py",
    "configuration_manager.py": "config/manager.py",
    "db_credentials.py": "config/credentials.py",
    
    # Requirements
    "requirements.txt": "requirements.txt",
    
    # Data files -> data/
    "my_keywords.txt": "data/keywords.txt",
    "naive_bayes_model.json": "data/models/naive_bayes_model.json",
    "ml_category_classifier.json": "data/models/category_classifier.json",
}

# Documentation mapping
DOC_MAPPING = {
    "docs/README.md": "docs/overview.md",
    "docs/api-reference.md": "docs/api/reference.md",
    "docs/database-schema.md": "docs/database/schema.md",
    "docs/deployment.md": "docs/deployment/guide.md",
    "docs/index.md": "docs/index.md",
    "docs/ml-architecture.md": "docs/architecture/ml.md",
    "docs/system-architecture.md": "docs/architecture/system.md",
    "docs/troubleshooting.md": "docs/guides/troubleshooting.md",
}

# Tools mapping
TOOL_MAPPING = {
    "tools/keyword_usage_analyzer.py": "tools/analyzers/keyword_usage.py",
    "tools/regex_performance_test.py": "tools/tests/regex_performance.py",
    "tools/verify_ml_enabled.py": "tools/verification/ml_check.py",
    "tools/KEYWORD_ANALYZER_DOCUMENTATION.md": "tools/docs/keyword_analyzer.md",
    "tools/README.md": "tools/README.md",
}


def create_directories():
    """Create all necessary directories."""
    directories = [
        "src/atlas_email/core",
        "src/atlas_email/api",
        "src/atlas_email/cli", 
        "src/atlas_email/models",
        "src/atlas_email/ml",
        "src/atlas_email/filters",
        "src/atlas_email/utils",
        "src/atlas_email/services",
        "config",
        "data/models",
        "docs/api",
        "docs/database",
        "docs/deployment",
        "docs/architecture",
        "docs/guides",
        "tools/analyzers",
        "tools/tests",
        "tools/verification",
        "tools/docs",
        "logs",
    ]
    
    for directory in directories:
        Path(DEST_DIR / directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")


def copy_files():
    """Copy files according to mapping."""
    # Copy main files
    for source, dest in FILE_MAPPING.items():
        source_path = SOURCE_DIR / source
        dest_path = DEST_DIR / dest
        
        if source_path.exists():
            shutil.copy2(source_path, dest_path)
            print(f"Copied: {source} -> {dest}")
        else:
            print(f"Warning: Source file not found: {source}")
    
    # Copy documentation
    for source, dest in DOC_MAPPING.items():
        source_path = SOURCE_DIR / source
        dest_path = DEST_DIR / dest
        
        if source_path.exists():
            shutil.copy2(source_path, dest_path)
            print(f"Copied doc: {source} -> {dest}")
    
    # Copy tools
    for source, dest in TOOL_MAPPING.items():
        source_path = SOURCE_DIR / source
        dest_path = DEST_DIR / dest
        
        if source_path.exists():
            shutil.copy2(source_path, dest_path)
            print(f"Copied tool: {source} -> {dest}")


def main():
    """Run the migration."""
    print("Starting migration from email_project to Atlas_Email...")
    print(f"Source: {SOURCE_DIR.absolute()}")
    print(f"Destination: {DEST_DIR.absolute()}")
    
    create_directories()
    copy_files()
    
    print("\nMigration complete!")
    print("\nNext steps:")
    print("1. Update import statements in all Python files")
    print("2. Create proper __init__.py files with exports")
    print("3. Update configuration paths")
    print("4. Set up environment variables")
    print("5. Run tests to ensure everything works")


if __name__ == "__main__":
    main()