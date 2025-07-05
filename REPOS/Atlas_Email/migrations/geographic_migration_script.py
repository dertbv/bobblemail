#!/usr/bin/env python3
"""
Safe Geographic Database Migration Script
Adds geographic columns to Atlas Email database without breaking existing system
Author: ATLAS Database Architect
Date: July 1, 2025
"""

import sqlite3
import os
import sys
import time
from datetime import datetime

DB_FILE = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db"

class GeographicMigration:
    def __init__(self, db_path):
        self.db_path = db_path
        self.backup_path = None
        self.migration_log = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
        
    def backup_database(self):
        """Create a backup of the database before migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = f"{self.db_path}.backup_{timestamp}"
        
        self.log(f"Creating backup at: {self.backup_path}")
        
        # Use SQLite backup API for safe backup
        source_conn = sqlite3.connect(self.db_path)
        backup_conn = sqlite3.connect(self.backup_path)
        
        with backup_conn:
            source_conn.backup(backup_conn)
            
        source_conn.close()
        backup_conn.close()
        
        self.log("✅ Backup created successfully")
        return self.backup_path
        
    def check_current_schema(self):
        """Check current database schema and version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check schema version
        cursor.execute("SELECT MAX(version) FROM schema_version")
        current_version = cursor.fetchone()[0]
        self.log(f"Current schema version: {current_version}")
        
        # Check for geographic columns
        cursor.execute("PRAGMA table_info(processed_emails_bulletproof)")
        columns = [col[1] for col in cursor.fetchall()]
        
        geographic_columns = ['sender_ip', 'sender_country_code', 'sender_country_name', 
                            'geographic_risk_score', 'detection_method']
        
        missing_columns = [col for col in geographic_columns if col not in columns]
        existing_columns = [col for col in geographic_columns if col in columns]
        
        conn.close()
        
        return {
            'version': current_version,
            'existing_columns': existing_columns,
            'missing_columns': missing_columns,
            'all_columns': columns
        }
        
    def add_geographic_columns(self):
        """Add missing geographic columns to the database"""
        schema_info = self.check_current_schema()
        
        if not schema_info['missing_columns']:
            self.log("✅ All geographic columns already exist!")
            return True
            
        self.log(f"Adding {len(schema_info['missing_columns'])} missing columns...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Begin transaction for atomicity
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Add each missing column
            column_definitions = {
                'sender_ip': 'TEXT',
                'sender_country_code': 'TEXT',
                'sender_country_name': 'TEXT',
                'geographic_risk_score': 'REAL',
                'detection_method': 'TEXT'
            }
            
            for column in schema_info['missing_columns']:
                col_type = column_definitions.get(column, 'TEXT')
                alter_sql = f"ALTER TABLE processed_emails_bulletproof ADD COLUMN {column} {col_type}"
                
                self.log(f"Adding column: {column} ({col_type})")
                cursor.execute(alter_sql)
                
            # Create index for country code queries
            self.log("Creating index for geographic queries...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_emails_bulletproof_country 
                ON processed_emails_bulletproof(sender_country_code)
            """)
            
            # Update schema version if needed
            if schema_info['version'] < 6:
                self.log("Updating schema version to 6...")
                cursor.execute("INSERT INTO schema_version (version) VALUES (6)")
                
            # Commit the transaction
            cursor.execute("COMMIT")
            self.log("✅ Geographic columns added successfully!")
            
            conn.close()
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            self.log(f"❌ Migration failed: {e}", "ERROR")
            conn.close()
            return False
            
    def verify_migration(self):
        """Verify the migration was successful"""
        self.log("Verifying migration...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check all columns exist
        cursor.execute("PRAGMA table_info(processed_emails_bulletproof)")
        columns = [col[1] for col in cursor.fetchall()]
        
        geographic_columns = ['sender_ip', 'sender_country_code', 'sender_country_name', 
                            'geographic_risk_score', 'detection_method']
        
        all_present = all(col in columns for col in geographic_columns)
        
        if all_present:
            self.log("✅ All geographic columns verified!")
            
            # Test insert with geographic data
            self.log("Testing insert with geographic data...")
            try:
                cursor.execute("""
                    INSERT INTO processed_emails_bulletproof 
                    (timestamp, sender_email, subject, action, sender_ip, 
                     sender_country_code, sender_country_name, geographic_risk_score, detection_method)
                    VALUES (datetime('now'), 'test@example.com', 'Migration Test', 'PRESERVED',
                            '192.168.1.1', 'US', 'United States', 0.1, 'MIGRATION_TEST')
                """)
                
                # Delete test record
                cursor.execute("""
                    DELETE FROM processed_emails_bulletproof 
                    WHERE subject = 'Migration Test' AND detection_method = 'MIGRATION_TEST'
                """)
                
                conn.commit()
                self.log("✅ Insert test successful!")
                
            except Exception as e:
                self.log(f"⚠️  Insert test failed: {e}", "WARNING")
                
        else:
            missing = [col for col in geographic_columns if col not in columns]
            self.log(f"❌ Missing columns: {missing}", "ERROR")
            
        conn.close()
        return all_present
        
    def rollback(self):
        """Rollback to backup if needed"""
        if not self.backup_path or not os.path.exists(self.backup_path):
            self.log("❌ No backup available for rollback!", "ERROR")
            return False
            
        self.log(f"Rolling back to backup: {self.backup_path}")
        
        try:
            # Close any connections
            time.sleep(1)
            
            # Replace current DB with backup
            os.replace(self.backup_path, self.db_path)
            
            self.log("✅ Rollback successful!")
            return True
            
        except Exception as e:
            self.log(f"❌ Rollback failed: {e}", "ERROR")
            return False
            
    def save_migration_log(self):
        """Save migration log to file"""
        log_file = f"geographic_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, 'w') as f:
            f.write("\n".join(self.migration_log))
        self.log(f"Migration log saved to: {log_file}")
        

def main():
    print("🌍 Geographic Database Migration Tool")
    print("=" * 60)
    
    if not os.path.exists(DB_FILE):
        print(f"❌ Database not found at: {DB_FILE}")
        return 1
        
    migrator = GeographicMigration(DB_FILE)
    
    # Step 1: Check current schema
    print("\n📋 Checking current schema...")
    schema_info = migrator.check_current_schema()
    print(f"Current version: {schema_info['version']}")
    print(f"Existing geographic columns: {schema_info['existing_columns']}")
    print(f"Missing geographic columns: {schema_info['missing_columns']}")
    
    if not schema_info['missing_columns']:
        print("\n✅ Database already has all geographic columns!")
        return 0
        
    # Step 2: Create backup
    print("\n💾 Creating backup...")
    backup_path = migrator.backup_database()
    
    # Step 3: Perform migration
    print("\n🔧 Performing migration...")
    success = migrator.add_geographic_columns()
    
    if success:
        # Step 4: Verify migration
        print("\n✔️  Verifying migration...")
        verified = migrator.verify_migration()
        
        if verified:
            print("\n🎉 Migration completed successfully!")
            print(f"Backup saved at: {backup_path}")
            print("You can delete the backup after confirming the system works correctly.")
        else:
            print("\n❌ Verification failed! Rolling back...")
            migrator.rollback()
            return 1
    else:
        print("\n❌ Migration failed! Rolling back...")
        migrator.rollback()
        return 1
        
    # Save migration log
    migrator.save_migration_log()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())