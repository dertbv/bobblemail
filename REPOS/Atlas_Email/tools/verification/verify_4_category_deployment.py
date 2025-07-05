#!/usr/bin/env python3
"""
Verification Script for 4-Category Classification Deployment
===========================================================

This script verifies that all components are properly deployed.
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

def check_file_exists(filepath, description):
    """Check if a required file exists."""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {'Found' if exists else 'Missing'}")
    if exists:
        print(f"   Path: {filepath}")
    return exists

def check_database_schema(db_path):
    """Verify database schema changes."""
    print("\n📊 Database Schema Verification:")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check new columns
        cursor = conn.execute("PRAGMA table_info(processed_emails_bulletproof)")
        columns = {col[1] for col in cursor.fetchall()}
        
        required_columns = ['category_v2', 'subcategory', 'category_confidence_v2', 'classification_version']
        for col in required_columns:
            status = "✅" if col in columns else "❌"
            print(f"{status} Column {col}: {'Present' if col in columns else 'Missing'}")
        
        # Check new tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required_tables = ['category_mappings', 'subcategory_patterns', 'ab_testing_results', 'migration_log']
        for table in required_tables:
            status = "✅" if table in tables else "❌"
            print(f"{status} Table {table}: {'Present' if table in tables else 'Missing'}")
        
        # Check category mappings
        cursor = conn.execute("SELECT COUNT(*) FROM category_mappings")
        mapping_count = cursor.fetchone()[0]
        print(f"✅ Category mappings: {mapping_count} entries")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def check_code_files():
    """Verify all code files are in place."""
    print("\n📁 Code Files Verification:")
    
    ml_dir = "src/atlas_email/ml"
    required_files = [
        (f"{ml_dir}/four_category_classifier.py", "4-Category Classifier"),
        (f"{ml_dir}/subcategory_tagger.py", "Subcategory Tagger"),
        (f"{ml_dir}/ab_classifier_integration.py", "A/B Testing Integration"),
        (f"{ml_dir}/migrate_to_four_categories.py", "Migration Script"),
        ("tests/test_four_category_classifier.py", "Test Suite"),
        ("docs/ml/four-category-classification.md", "Documentation"),
        ("INTEGRATION_GUIDE.md", "Integration Guide"),
    ]
    
    all_present = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_present = False
    
    return all_present

def check_deployment_status():
    """Check deployment status file."""
    print("\n📋 Deployment Status:")
    
    status_file = "4_category_deployment_status.json"
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        print(f"✅ Deployment Date: {status['deployment_date']}")
        print(f"{'✅' if status['database_migrated'] else '❌'} Database Migration: {'Complete' if status['database_migrated'] else 'Pending'}")
        print(f"{'✅' if status['classifier_trained'] else '⚠️'} Classifier Training: {'Complete' if status['classifier_trained'] else 'Pending'}")
        print(f"{'✅' if status['ab_testing_enabled'] else '⚠️'} A/B Testing: {'Enabled' if status['ab_testing_enabled'] else 'Not Enabled'}")
        print(f"📊 Rollout Percentage: {status['rollout_percentage']}%")
        
        return status
    else:
        print("❌ Deployment status file not found")
        return None

def find_database():
    """Find the mail_filter.db database."""
    # Check current directory
    if os.path.exists("mail_filter.db"):
        return "mail_filter.db"
    
    # Check parent directories
    current = Path.cwd()
    while current != current.parent:
        db_path = current / "mail_filter.db"
        if db_path.exists():
            return str(db_path)
        current = current.parent
    
    # Check home directory
    home_db = Path.home() / "mail_filter.db"
    if home_db.exists():
        return str(home_db)
    
    return None

def generate_summary_report():
    """Generate a summary report of the deployment."""
    print("\n" + "="*60)
    print("📊 4-CATEGORY DEPLOYMENT VERIFICATION REPORT")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find database
    db_path = find_database()
    if db_path:
        print(f"\n✅ Database found: {db_path}")
        db_ok = check_database_schema(db_path)
    else:
        print("\n❌ Database not found")
        db_ok = False
    
    # Check code files
    code_ok = check_code_files()
    
    # Check deployment status
    status = check_deployment_status()
    
    # Overall summary
    print("\n" + "="*60)
    print("DEPLOYMENT SUMMARY")
    print("="*60)
    
    if db_ok and code_ok:
        print("✅ All components successfully deployed!")
        print("\n📋 Next Steps:")
        print("1. Train the classifier on production server")
        print("2. Update email processor to use A/B testing")
        print("3. Start with 10% rollout and monitor")
        print("4. Gradually increase rollout based on metrics")
    else:
        print("⚠️  Some components need attention")
        if not db_ok:
            print("   - Database schema needs verification")
        if not code_ok:
            print("   - Some code files are missing")
    
    print("\n💡 Tips:")
    print("- Use INTEGRATION_GUIDE.md for step-by-step instructions")
    print("- Monitor ab_testing_results table for performance")
    print("- Auto warranty emails should now classify correctly!")

def main():
    """Run verification."""
    generate_summary_report()

if __name__ == "__main__":
    main()