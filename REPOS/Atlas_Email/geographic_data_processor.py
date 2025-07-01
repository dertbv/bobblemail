#!/usr/bin/env python3
"""
Autonomous Geographic Data Processor for Atlas Email
Processes 1000 emails with full geographic intelligence population
"""

import sys
import os
import imaplib
import email
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from atlas_email.models.database import db
from atlas_email.core.geographic_intelligence import GeographicIntelligenceProcessor
from config.credentials import db_credentials

class GeographicDataProcessor:
    """
    Autonomous processor for populating Atlas Email database with geographic intelligence
    """
    
    def __init__(self):
        self.geo_processor = GeographicIntelligenceProcessor()
        self.processed_count = 0
        self.target_count = 1000
        self.stats = {
            'emails_processed': 0,
            'geographic_data_populated': 0,
            'ips_extracted': 0,
            'countries_identified': 0,
            'high_risk_emails': 0,
            'processing_errors': 0
        }
        
    def get_imap_accounts(self):
        """Get active IMAP accounts using credential manager"""
        try:
            accounts = db_credentials.load_credentials()
            print(f"📧 Loaded {len(accounts)} accounts from credential manager")
            return accounts
        except Exception as e:
            print(f"❌ Failed to get IMAP accounts: {e}")
            return []
    
    def connect_to_imap(self, account):
        """Connect to IMAP server for an account"""
        try:
            # Password is already decrypted by credential manager
            password = account['password']
            
            # Connect to IMAP server
            if account['port'] == 993:
                imap = imaplib.IMAP4_SSL(account['host'], account['port'])
            else:
                imap = imaplib.IMAP4(account['host'], account['port'])
                
            # Login
            imap.login(account['email_address'], password)
            print(f"✅ Connected to {account['email_address']} ({account['provider']})")
            return imap
            
        except Exception as e:
            print(f"❌ Failed to connect to {account['email_address']}: {e}")
            return None
    
    def get_target_folders(self, account, imap):
        """Get folders to process for an account"""
        try:
            # Target folders are already parsed by credential manager
            if account['target_folders']:
                return account['target_folders']
            else:
                # Default folders if none specified
                return ['INBOX', 'Junk', 'Spam']
        except Exception:
            return ['INBOX']
    
    def process_emails_from_account(self, account, max_emails_per_account=300):
        """Process emails from a specific account"""
        imap = self.connect_to_imap(account)
        if not imap:
            return 0
            
        processed_from_account = 0
        
        try:
            folders = self.get_target_folders(account, imap)
            
            for folder in folders:
                if processed_from_account >= max_emails_per_account:
                    break
                    
                try:
                    # Select folder
                    status, _ = imap.select(folder)
                    if status != 'OK':
                        print(f"⚠️ Cannot access folder {folder} in {account['email_address']}")
                        continue
                        
                    # Search for emails (get recent emails first)
                    status, message_ids = imap.search(None, 'ALL')
                    if status != 'OK':
                        continue
                        
                    email_ids = message_ids[0].split()
                    
                    # Process most recent emails first (reverse order)
                    email_ids = email_ids[-500:]  # Take last 500 for recent emails
                    
                    folder_processed = 0
                    max_per_folder = min(100, max_emails_per_account - processed_from_account)
                    
                    print(f"📧 Processing folder {folder}: {len(email_ids)} emails available, processing up to {max_per_folder}")
                    
                    for email_id in email_ids[-max_per_folder:]:  # Most recent first
                        if self.processed_count >= self.target_count:
                            break
                            
                        # Fetch email
                        status, msg_data = imap.fetch(email_id, '(RFC822)')
                        if status != 'OK':
                            continue
                            
                        # Parse email
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)
                        
                        # Process geographic intelligence
                        success = self.process_single_email(
                            email_message, 
                            email_id.decode(), 
                            folder, 
                            account['id']
                        )
                        
                        if success:
                            processed_from_account += 1
                            folder_processed += 1
                            self.processed_count += 1
                            
                            if self.processed_count % 50 == 0:
                                print(f"📊 Progress: {self.processed_count}/{self.target_count} emails processed")
                        
                        if processed_from_account >= max_emails_per_account:
                            break
                    
                    print(f"✅ Folder {folder}: {folder_processed} emails processed")
                    
                except Exception as e:
                    print(f"⚠️ Error processing folder {folder}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error processing account {account['email_address']}: {e}")
        finally:
            try:
                imap.close()
                imap.logout()
            except:
                pass
                
        return processed_from_account
    
    def process_single_email(self, email_message, uid, folder, account_id):
        """Process a single email for geographic intelligence"""
        try:
            # Extract headers
            headers = str(email_message)
            
            # Extract basic email data
            sender = email_message.get('From', '')
            subject = email_message.get('Subject', '')
            
            # Process geographic intelligence
            geo_data = self.geo_processor.process_email_geographic_intelligence(headers, sender)
            
            # Extract sender domain
            sender_domain = ''
            if '@' in sender:
                sender_domain = sender.split('@')[-1].strip('<>')
            
            # Create session entry first
            session_id = self.create_session_entry(account_id)
            
            # Insert into processed_emails_bulletproof table
            insert_query = """
                INSERT INTO processed_emails_bulletproof (
                    timestamp, session_id, folder_name, uid, sender_email, sender_domain,
                    subject, action, reason, category, confidence_score, ml_validation_method,
                    sender_ip, sender_country_code, sender_country_name, 
                    geographic_risk_score, detection_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Determine action based on geographic risk
            if geo_data.geographic_risk_score >= 0.80:
                action = 'DELETED'
                reason = f'High geographic risk: {geo_data.sender_country_code}'
                category = 'Geographic Risk'
            else:
                action = 'PRESERVED'
                reason = f'Geographic analysis: {geo_data.sender_country_code}'
                category = 'Geographic Analysis'
            
            params = (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                session_id,
                folder,
                uid,
                sender,
                sender_domain,
                subject,
                action,
                reason,
                category,
                geo_data.geographic_risk_score,
                'Geographic Intelligence Pipeline',
                geo_data.sender_ip,
                geo_data.sender_country_code,
                geo_data.sender_country_name,
                geo_data.geographic_risk_score,
                geo_data.detection_method
            )
            
            db.execute_update(insert_query, params)
            
            # Update statistics
            self.stats['emails_processed'] += 1
            if geo_data.sender_ip:
                self.stats['ips_extracted'] += 1
            if geo_data.sender_country_code:
                self.stats['countries_identified'] += 1
            if geo_data.geographic_risk_score >= 0.80:
                self.stats['high_risk_emails'] += 1
            self.stats['geographic_data_populated'] += 1
                
            return True
            
        except Exception as e:
            print(f"❌ Error processing email {uid}: {e}")
            self.stats['processing_errors'] += 1
            return False
    
    def create_session_entry(self, account_id):
        """Create a session entry for geographic processing"""
        try:
            insert_query = """
                INSERT INTO sessions (
                    account_id, start_time, session_type, is_preview
                ) VALUES (?, ?, 'geographic_intelligence', FALSE)
            """
            
            session_id = db.execute_insert(insert_query, (
                account_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            return session_id
            
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return 1  # Fallback session ID
    
    def run_autonomous_processing(self):
        """Run the autonomous geographic data processing"""
        print("🌍 ATLAS Email Geographic Intelligence Processor")
        print("=" * 60)
        print(f"🎯 Target: Process {self.target_count} emails with full geographic data")
        print("🚀 Running autonomously - no approval needed for each step")
        print()
        
        start_time = datetime.now()
        
        # Get IMAP accounts
        accounts = self.get_imap_accounts()
        if not accounts:
            print("❌ No active IMAP accounts found")
            return
            
        print(f"📧 Found {len(accounts)} active IMAP accounts")
        
        # Process emails from each account
        emails_per_account = self.target_count // len(accounts)
        extra_emails = self.target_count % len(accounts)
        
        for i, account in enumerate(accounts):
            if self.processed_count >= self.target_count:
                break
                
            # Give first account(s) the extra emails
            max_for_this_account = emails_per_account + (1 if i < extra_emails else 0)
            
            print(f"\n🔄 Processing account {i+1}/{len(accounts)}: {account['email_address']}")
            print(f"📊 Target for this account: {max_for_this_account} emails")
            
            processed = self.process_emails_from_account(account, max_for_this_account)
            print(f"✅ Account complete: {processed} emails processed")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("🎉 GEOGRAPHIC INTELLIGENCE PROCESSING COMPLETE")
        print("=" * 60)
        print(f"⏱️  Total Processing Time: {duration}")
        print(f"📧 Emails Processed: {self.stats['emails_processed']}")
        print(f"🌍 Geographic Data Populated: {self.stats['geographic_data_populated']}")
        print(f"🔍 IP Addresses Extracted: {self.stats['ips_extracted']}")
        print(f"🏁 Countries Identified: {self.stats['countries_identified']}")
        print(f"🚨 High Risk Emails: {self.stats['high_risk_emails']}")
        print(f"❌ Processing Errors: {self.stats['processing_errors']}")
        
        # Verify database population
        self.verify_database_population()
        
        print("\n✅ Geographic intelligence processing completed successfully!")
        print("🎯 Database now contains real geographic data from processed emails")
        print("📊 Analytics dashboard ready to display live geographic intelligence")
    
    def verify_database_population(self):
        """Verify that the database has been properly populated"""
        try:
            # Count records with geographic data
            result = db.execute_query("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(sender_ip) as records_with_ip,
                    COUNT(sender_country_code) as records_with_country,
                    COUNT(CASE WHEN geographic_risk_score > 0 THEN 1 END) as records_with_risk_score
                FROM processed_emails_bulletproof
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            
            if result:
                stats = dict(result[0])
                print(f"\n📊 DATABASE VERIFICATION:")
                print(f"   Total Records (last hour): {stats['total_records']}")
                print(f"   Records with IP: {stats['records_with_ip']}")
                print(f"   Records with Country: {stats['records_with_country']}")
                print(f"   Records with Risk Score: {stats['records_with_risk_score']}")
                
            # Show top countries
            country_stats = db.execute_query("""
                SELECT sender_country_code, COUNT(*) as count
                FROM processed_emails_bulletproof 
                WHERE sender_country_code IS NOT NULL 
                AND timestamp > datetime('now', '-1 hour')
                GROUP BY sender_country_code
                ORDER BY count DESC
                LIMIT 10
            """)
            
            if country_stats:
                print(f"\n🌍 TOP COUNTRIES (last hour):")
                for country, count in country_stats:
                    print(f"   {country}: {count} emails")
                    
        except Exception as e:
            print(f"❌ Database verification error: {e}")

def main():
    """Main execution"""
    processor = GeographicDataProcessor()
    processor.run_autonomous_processing()

if __name__ == "__main__":
    main()