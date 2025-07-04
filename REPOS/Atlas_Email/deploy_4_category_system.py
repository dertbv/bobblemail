#!/usr/bin/env python3
"""
Standalone Deployment Script for 4-Category Classification System
================================================================

This script deploys the new classification system without requiring
the full Atlas Email import chain.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import shutil
import os

# Database path
DB_FILE = "mail_filter.db"

def find_database():
    """Find the mail_filter.db database."""
    # Check current directory
    if os.path.exists(DB_FILE):
        return DB_FILE
    
    # Check parent directories
    current = Path.cwd()
    while current != current.parent:
        db_path = current / DB_FILE
        if db_path.exists():
            return str(db_path)
        current = current.parent
    
    raise FileNotFoundError("Could not find mail_filter.db")

def backup_database(db_path):
    """Create a backup of the database."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"📦 Creating backup at: {backup_path}")
    shutil.copy2(db_path, backup_path)
    return backup_path

def add_new_columns(db_path):
    """Add new columns for 4-category system."""
    conn = sqlite3.connect(db_path)
    
    print("📊 Adding new columns to database...")
    
    # Check existing columns
    cursor = conn.execute("PRAGMA table_info(processed_emails_bulletproof)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    columns_to_add = [
        ("category_v2", "TEXT"),
        ("subcategory", "TEXT"),
        ("category_confidence_v2", "REAL"),
        ("classification_version", "INTEGER DEFAULT 1")
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                conn.execute(f"""
                    ALTER TABLE processed_emails_bulletproof 
                    ADD COLUMN {col_name} {col_type}
                """)
                print(f"   ✓ Added {col_name} column")
            except Exception as e:
                print(f"   ⚠️  Could not add {col_name}: {e}")
    
    conn.commit()
    conn.close()

def create_mapping_tables(db_path):
    """Create category mapping and tracking tables."""
    conn = sqlite3.connect(db_path)
    
    print("📊 Creating mapping tables...")
    
    # Category mappings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS category_mappings (
            old_category TEXT PRIMARY KEY,
            new_category TEXT NOT NULL,
            subcategory TEXT,
            mapping_confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Created category_mappings table")
    
    # Subcategory patterns table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subcategory_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            pattern_value TEXT NOT NULL,
            effectiveness REAL DEFAULT 0.5,
            occurrence_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, subcategory, pattern_type, pattern_value)
        )
    """)
    print("   ✓ Created subcategory_patterns table")
    
    # A/B testing results table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ab_testing_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT NOT NULL,
            email_uid TEXT,
            sender TEXT,
            subject TEXT,
            old_category TEXT,
            old_confidence REAL,
            new_category TEXT,
            new_subcategory TEXT,
            new_confidence REAL,
            categories_match BOOLEAN,
            processing_time_old REAL,
            processing_time_new REAL,
            selected_classifier TEXT,
            user_feedback TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Created ab_testing_results table")
    
    # Migration log table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migration_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT NOT NULL,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            records_migrated INTEGER DEFAULT 0,
            status TEXT DEFAULT 'in_progress',
            details TEXT
        )
    """)
    print("   ✓ Created migration_log table")
    
    conn.commit()
    conn.close()

def populate_category_mappings(db_path):
    """Populate the category mappings."""
    conn = sqlite3.connect(db_path)
    
    print("📊 Populating category mappings...")
    
    mappings = {
        # Dangerous
        'Phishing': ('Dangerous', 'Phishing attempts'),
        'Encoded Phishing': ('Dangerous', 'Phishing attempts'),
        'Brand Impersonation': ('Dangerous', 'Account compromise attempts'),
        'Encoded Brand Impersonation': ('Dangerous', 'Account compromise attempts'),
        
        # Commercial Spam - INCLUDING AUTO WARRANTY FIX
        'Financial & Investment Spam': ('Commercial Spam', 'General product marketing'),
        'Encoded Financial & Investment Spam': ('Commercial Spam', 'General product marketing'),
        'Business Opportunity Spam': ('Commercial Spam', 'General product marketing'),
        'Health & Medical Spam': ('Commercial Spam', 'Health & medical products'),
        'Encoded Pharmaceutical Spam': ('Commercial Spam', 'Health & medical products'),
        'Adult & Dating Spam': ('Commercial Spam', 'Adult & dating services'),
        'Encoded Adult Content Spam': ('Commercial Spam', 'Adult & dating services'),
        'Encoded Social/Dating Spam': ('Commercial Spam', 'Adult & dating services'),
        'Gambling Spam': ('Commercial Spam', 'Gambling promotions'),
        'Encoded Gambling Spam': ('Commercial Spam', 'Gambling promotions'),
        'Real Estate Spam': ('Commercial Spam', 'General product marketing'),
        
        # Scams
        'Payment Scam': ('Scams', 'Advance fee fraud'),
        'Encoded Payment Scam': ('Scams', 'Advance fee fraud'),
        'Legal & Compensation Scams': ('Scams', 'Advance fee fraud'),
        
        # Legitimate Marketing
        'Promotional Email': ('Legitimate Marketing', 'Promotional emails'),
        'Encoded Marketing Spam': ('Legitimate Marketing', 'Promotional emails'),
        
        # Generic
        'Encoded Spam': ('Commercial Spam', 'General product marketing'),
        'User Keyword': ('Commercial Spam', 'General product marketing'),
        'Unknown': ('Commercial Spam', 'General product marketing'),
    }
    
    for old_cat, (new_cat, subcat) in mappings.items():
        conn.execute("""
            INSERT OR REPLACE INTO category_mappings 
            (old_category, new_category, subcategory, mapping_confidence)
            VALUES (?, ?, ?, 1.0)
        """, (old_cat, new_cat, subcat))
    
    conn.commit()
    print(f"   ✓ Added {len(mappings)} category mappings")
    conn.close()

def migrate_data(db_path):
    """Migrate existing email data to new system."""
    conn = sqlite3.connect(db_path)
    
    # Start migration log
    cursor = conn.execute("""
        INSERT INTO migration_log (migration_name, details)
        VALUES ('4-category-deployment', 'Migrating to 4-category classification system')
    """)
    migration_id = cursor.lastrowid
    
    # Count emails to migrate
    cursor = conn.execute("""
        SELECT COUNT(*) FROM processed_emails_bulletproof 
        WHERE category IS NOT NULL AND category_v2 IS NULL
    """)
    total = cursor.fetchone()[0]
    
    print(f"📊 Migrating {total} email records...")
    
    # Get category mappings
    cursor = conn.execute("SELECT old_category, new_category, subcategory FROM category_mappings")
    mappings = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    
    # Migrate in batches
    batch_size = 1000
    migrated = 0
    auto_warranty_fixed = 0
    
    while True:
        cursor = conn.execute("""
            SELECT id, category, subject, sender_email
            FROM processed_emails_bulletproof 
            WHERE category IS NOT NULL AND category_v2 IS NULL
            LIMIT ?
        """, (batch_size,))
        
        records = cursor.fetchall()
        if not records:
            break
        
        for record_id, old_cat, subject, sender in records:
            # Default mapping
            new_cat, subcat = mappings.get(old_cat, ('Commercial Spam', 'General product marketing'))
            
            # Fix auto warranty misclassification
            if old_cat == 'Adult & Dating Spam' and subject:
                subject_lower = subject.lower()
                if any(kw in subject_lower for kw in ['warranty', 'auto', 'vehicle', 'endurance', 'car protection']):
                    new_cat = 'Commercial Spam'
                    subcat = 'Auto warranty & insurance'
                    auto_warranty_fixed += 1
            
            # Update record
            conn.execute("""
                UPDATE processed_emails_bulletproof
                SET category_v2 = ?, subcategory = ?, classification_version = 2
                WHERE id = ?
            """, (new_cat, subcat, record_id))
        
        migrated += len(records)
        conn.commit()
        
        if migrated % 5000 == 0:
            print(f"   ✓ Migrated {migrated}/{total} records...")
    
    # Complete migration
    conn.execute("""
        UPDATE migration_log
        SET completed_at = CURRENT_TIMESTAMP,
            records_migrated = ?,
            status = 'completed',
            details = ?
        WHERE id = ?
    """, (migrated, f"Fixed {auto_warranty_fixed} auto warranty misclassifications", migration_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Migration completed: {migrated} records migrated")
    print(f"   ✓ Fixed {auto_warranty_fixed} auto warranty misclassifications")

def create_indexes(db_path):
    """Create performance indexes."""
    conn = sqlite3.connect(db_path)
    
    print("📊 Creating performance indexes...")
    
    indexes = [
        ("idx_category_v2", "processed_emails_bulletproof(category_v2)"),
        ("idx_subcategory", "processed_emails_bulletproof(subcategory)"),
        ("idx_classification_version", "processed_emails_bulletproof(classification_version)"),
        ("idx_ab_test_id", "ab_testing_results(test_id)"),
    ]
    
    for idx_name, idx_def in indexes:
        try:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            print(f"   ✓ Created {idx_name}")
        except Exception as e:
            print(f"   ⚠️  Could not create {idx_name}: {e}")
    
    conn.commit()
    conn.close()

def verify_deployment(db_path):
    """Verify the deployment was successful."""
    conn = sqlite3.connect(db_path)
    
    print("\n📊 Deployment Verification:")
    
    # Check migrated records
    cursor = conn.execute("SELECT COUNT(*) FROM processed_emails_bulletproof WHERE category_v2 IS NOT NULL")
    migrated = cursor.fetchone()[0]
    print(f"   ✓ Migrated records: {migrated}")
    
    # Check category distribution
    cursor = conn.execute("""
        SELECT category_v2, COUNT(*) as count
        FROM processed_emails_bulletproof
        WHERE category_v2 IS NOT NULL
        GROUP BY category_v2
        ORDER BY count DESC
    """)
    
    print("   ✓ Category distribution:")
    for cat, count in cursor.fetchall():
        print(f"      {cat}: {count}")
    
    # Check auto warranty fixes
    cursor = conn.execute("""
        SELECT COUNT(*) FROM processed_emails_bulletproof
        WHERE subcategory = 'Auto warranty & insurance'
    """)
    auto_warranty = cursor.fetchone()[0]
    print(f"   ✓ Auto warranty emails (fixed): {auto_warranty}")
    
    conn.close()

def main():
    """Run the deployment."""
    print("🚀 4-Category Classification System Deployment")
    print("=" * 60)
    
    try:
        # Find database
        db_path = find_database()
        print(f"📍 Found database at: {db_path}")
        
        # Create backup
        backup_path = backup_database(db_path)
        
        # Run deployment steps
        add_new_columns(db_path)
        create_mapping_tables(db_path)
        populate_category_mappings(db_path)
        migrate_data(db_path)
        create_indexes(db_path)
        
        # Verify
        verify_deployment(db_path)
        
        print("\n✅ Deployment completed successfully!")
        print(f"   Backup saved at: {backup_path}")
        print("\n📌 Next steps:")
        print("   1. Train the new classifier with: python3 train_4_category_classifier.py")
        print("   2. Enable A/B testing in the application")
        print("   3. Monitor performance metrics")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print("   Check the error and try again")
        raise

if __name__ == "__main__":
    main()