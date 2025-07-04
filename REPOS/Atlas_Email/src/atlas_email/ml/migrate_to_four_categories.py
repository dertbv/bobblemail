"""
Database Migration Script for 4-Category Classification System
=============================================================

This script migrates the existing email classification database to support
the new 4-category system while preserving all existing data.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from atlas_email.models.database import DB_FILE


class FourCategoryMigration:
    """Handle database migration to 4-category system."""
    
    # Category mappings from old to new system
    CATEGORY_MAPPING = {
        # Dangerous mappings
        'Phishing': ('Dangerous', 'Phishing attempts'),
        'Encoded Phishing': ('Dangerous', 'Phishing attempts'),
        'Brand Impersonation': ('Dangerous', 'Account compromise attempts'),
        'Encoded Brand Impersonation': ('Dangerous', 'Account compromise attempts'),
        
        # Commercial Spam mappings - INCLUDING AUTO WARRANTY FIX
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
        
        # Scams mappings
        'Payment Scam': ('Scams', 'Advance fee fraud'),
        'Encoded Payment Scam': ('Scams', 'Advance fee fraud'),
        'Legal & Compensation Scams': ('Scams', 'Advance fee fraud'),
        
        # Legitimate Marketing mappings
        'Promotional Email': ('Legitimate Marketing', 'Promotional emails'),
        'Encoded Marketing Spam': ('Legitimate Marketing', 'Promotional emails'),
        
        # Generic mappings
        'Encoded Spam': ('Commercial Spam', 'General product marketing'),
        'User Keyword': ('Commercial Spam', 'General product marketing'),
        'Unknown': ('Commercial Spam', 'General product marketing'),
    }
    
    def __init__(self, db_path: str = None):
        """Initialize migration handler."""
        self.db_path = db_path or DB_FILE
        self.backup_path = None
        
    def backup_database(self) -> str:
        """Create a backup of the database before migration."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        # Create backup using SQLite backup API
        source = sqlite3.connect(self.db_path)
        backup = sqlite3.connect(backup_path)
        
        with backup:
            source.backup(backup)
        
        source.close()
        backup.close()
        
        self.backup_path = backup_path
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    
    def add_new_columns(self):
        """Add new columns to support 4-category system."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Add new columns to processed_emails_bulletproof
            print("📊 Adding new columns to processed_emails_bulletproof...")
            
            # Check if columns already exist
            cursor = conn.execute("PRAGMA table_info(processed_emails_bulletproof)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            if 'category_v2' not in existing_columns:
                conn.execute("""
                    ALTER TABLE processed_emails_bulletproof 
                    ADD COLUMN category_v2 TEXT
                """)
                print("   ✓ Added category_v2 column")
            
            if 'subcategory' not in existing_columns:
                conn.execute("""
                    ALTER TABLE processed_emails_bulletproof 
                    ADD COLUMN subcategory TEXT
                """)
                print("   ✓ Added subcategory column")
            
            if 'category_confidence_v2' not in existing_columns:
                conn.execute("""
                    ALTER TABLE processed_emails_bulletproof 
                    ADD COLUMN category_confidence_v2 REAL
                """)
                print("   ✓ Added category_confidence_v2 column")
            
            if 'classification_version' not in existing_columns:
                conn.execute("""
                    ALTER TABLE processed_emails_bulletproof 
                    ADD COLUMN classification_version INTEGER DEFAULT 1
                """)
                print("   ✓ Added classification_version column")
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error adding columns: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_mapping_tables(self):
        """Create tables for category mapping and tracking."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Category mappings table
            print("📊 Creating category mapping tables...")
            
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
            
            # Subcategory patterns table (if not exists from subcategory_tagger)
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
            
            # Migration tracking table
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
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def populate_category_mappings(self):
        """Populate the category mappings table."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            print("📊 Populating category mappings...")
            
            for old_cat, (new_cat, subcat) in self.CATEGORY_MAPPING.items():
                conn.execute("""
                    INSERT OR REPLACE INTO category_mappings 
                    (old_category, new_category, subcategory, mapping_confidence)
                    VALUES (?, ?, ?, 1.0)
                """, (old_cat, new_cat, subcat))
            
            conn.commit()
            print(f"   ✓ Added {len(self.CATEGORY_MAPPING)} category mappings")
            
        except Exception as e:
            print(f"❌ Error populating mappings: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def migrate_existing_data(self, batch_size: int = 1000):
        """Migrate existing email classifications to new system."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Start migration log
            cursor = conn.execute("""
                INSERT INTO migration_log (migration_name, details)
                VALUES ('4-category-migration', 'Migrating to 4-category classification system')
            """)
            migration_id = cursor.lastrowid
            
            # Count total records
            cursor = conn.execute("""
                SELECT COUNT(*) FROM processed_emails_bulletproof 
                WHERE category IS NOT NULL AND category_v2 IS NULL
            """)
            total_records = cursor.fetchone()[0]
            print(f"📊 Migrating {total_records} email records...")
            
            migrated = 0
            auto_warranty_fixed = 0
            
            while True:
                # Get batch of records
                cursor = conn.execute("""
                    SELECT id, category, subject, sender_domain 
                    FROM processed_emails_bulletproof 
                    WHERE category IS NOT NULL AND category_v2 IS NULL
                    LIMIT ?
                """, (batch_size,))
                
                records = cursor.fetchall()
                if not records:
                    break
                
                # Process each record
                for record_id, old_category, subject, domain in records:
                    new_category, subcategory = self.CATEGORY_MAPPING.get(
                        old_category, 
                        ('Commercial Spam', 'General product marketing')
                    )
                    
                    # Special handling for misclassified auto warranty emails
                    if old_category == 'Adult & Dating Spam' and subject:
                        subject_lower = subject.lower()
                        if any(keyword in subject_lower for keyword in 
                               ['warranty', 'auto', 'vehicle', 'endurance', 'car protection']):
                            new_category = 'Commercial Spam'
                            subcategory = 'Auto warranty & insurance'
                            auto_warranty_fixed += 1
                    
                    # Update record
                    conn.execute("""
                        UPDATE processed_emails_bulletproof
                        SET category_v2 = ?,
                            subcategory = ?,
                            classification_version = 2
                        WHERE id = ?
                    """, (new_category, subcategory, record_id))
                
                migrated += len(records)
                conn.commit()
                
                if migrated % 5000 == 0:
                    print(f"   ✓ Migrated {migrated}/{total_records} records...")
            
            # Complete migration log
            conn.execute("""
                UPDATE migration_log
                SET completed_at = CURRENT_TIMESTAMP,
                    records_migrated = ?,
                    status = 'completed',
                    details = ?
                WHERE id = ?
            """, (migrated, f"Fixed {auto_warranty_fixed} auto warranty misclassifications", migration_id))
            
            conn.commit()
            print(f"✅ Migration completed: {migrated} records migrated")
            print(f"   ✓ Fixed {auto_warranty_fixed} auto warranty misclassifications")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
            
            # Update migration log with error
            conn.execute("""
                UPDATE migration_log
                SET status = 'failed',
                    details = ?
                WHERE id = ?
            """, (str(e), migration_id))
            conn.commit()
            raise
        finally:
            conn.close()
    
    def create_indexes(self):
        """Create indexes for performance optimization."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            print("📊 Creating performance indexes...")
            
            # Index for new category columns
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category_v2 
                ON processed_emails_bulletproof(category_v2)
            """)
            print("   ✓ Created category_v2 index")
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_subcategory 
                ON processed_emails_bulletproof(subcategory)
            """)
            print("   ✓ Created subcategory index")
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_classification_version 
                ON processed_emails_bulletproof(classification_version)
            """)
            print("   ✓ Created classification_version index")
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def verify_migration(self) -> Dict[str, any]:
        """Verify the migration was successful."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            results = {}
            
            # Count migrated records
            cursor = conn.execute("""
                SELECT COUNT(*) FROM processed_emails_bulletproof 
                WHERE category_v2 IS NOT NULL
            """)
            results['migrated_count'] = cursor.fetchone()[0]
            
            # Category distribution
            cursor = conn.execute("""
                SELECT category_v2, COUNT(*) as count
                FROM processed_emails_bulletproof
                WHERE category_v2 IS NOT NULL
                GROUP BY category_v2
                ORDER BY count DESC
            """)
            results['category_distribution'] = cursor.fetchall()
            
            # Check auto warranty fixes
            cursor = conn.execute("""
                SELECT COUNT(*) FROM processed_emails_bulletproof
                WHERE subcategory = 'Auto warranty & insurance'
                AND category = 'Adult & Dating Spam'
            """)
            results['auto_warranty_fixes'] = cursor.fetchone()[0]
            
            # Subcategory distribution
            cursor = conn.execute("""
                SELECT subcategory, COUNT(*) as count
                FROM processed_emails_bulletproof
                WHERE subcategory IS NOT NULL
                GROUP BY subcategory
                ORDER BY count DESC
                LIMIT 10
            """)
            results['top_subcategories'] = cursor.fetchall()
            
            return results
            
        finally:
            conn.close()
    
    def run_migration(self):
        """Run the complete migration process."""
        print("🚀 Starting 4-Category Classification Migration")
        print("=" * 60)
        
        try:
            # Step 1: Backup
            self.backup_database()
            
            # Step 2: Add new columns
            self.add_new_columns()
            
            # Step 3: Create mapping tables
            self.create_mapping_tables()
            
            # Step 4: Populate mappings
            self.populate_category_mappings()
            
            # Step 5: Migrate data
            self.migrate_existing_data()
            
            # Step 6: Create indexes
            self.create_indexes()
            
            # Step 7: Verify
            print("\n📊 Verification Results:")
            results = self.verify_migration()
            print(f"   Total migrated: {results['migrated_count']}")
            print(f"   Auto warranty fixes: {results['auto_warranty_fixes']}")
            print("\n   Category distribution:")
            for cat, count in results['category_distribution']:
                print(f"      {cat}: {count}")
            
            print("\n✅ Migration completed successfully!")
            print(f"   Backup saved at: {self.backup_path}")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print(f"   Backup available at: {self.backup_path}")
            raise


# Command-line interface
if __name__ == "__main__":
    import sys
    
    print("4-Category Classification System Migration")
    print("=========================================")
    print("\nThis will migrate your email classification database to the new")
    print("4-category system and fix auto warranty misclassifications.")
    print("\nA backup will be created before any changes are made.")
    
    response = input("\nProceed with migration? (yes/no): ")
    
    if response.lower() == 'yes':
        migration = FourCategoryMigration()
        migration.run_migration()
    else:
        print("Migration cancelled.")