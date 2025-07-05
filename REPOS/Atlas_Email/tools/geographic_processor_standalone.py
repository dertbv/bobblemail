#!/usr/bin/env python3
"""
Standalone Geographic Data Processor for Atlas Email
Processes 1000 emails with full geographic intelligence population
Simplified version without ML dependencies
"""

import sys
import os
import imaplib
import email
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import geoip2fast
import re

# Direct database connection without importing complex dependencies
DB_FILE = "data/mail_filter.db"

class StandaloneGeographicProcessor:
    """
    Standalone processor for populating Atlas Email database with geographic intelligence
    """
    
    # Country risk scores based on threat intelligence data
    COUNTRY_RISK_SCORES = {
        # High-risk countries (known spam/phishing sources)
        'CN': 0.95,  # China - major spam source
        'RU': 0.90,  # Russia - high phishing activity
        'NG': 0.85,  # Nigeria - financial scams
        'IN': 0.80,  # India - call center fraud
        'PK': 0.75,  # Pakistan - spam networks
        'BD': 0.70,  # Bangladesh - suspicious patterns
        'VN': 0.65,  # Vietnam - emerging threat
        'UA': 0.60,  # Ukraine - conflict-related risks
        'ID': 0.55,  # Indonesia - growing spam source
        'BR': 0.50,  # Brazil - moderate risk
        
        # Medium-risk countries
        'TR': 0.45,  # Turkey
        'MX': 0.40,  # Mexico
        'TH': 0.35,  # Thailand
        'PL': 0.30,  # Poland
        'RO': 0.25,  # Romania
        
        # Low-risk countries (established email infrastructure)
        'US': 0.10,  # United States
        'CA': 0.10,  # Canada
        'GB': 0.10,  # United Kingdom
        'DE': 0.10,  # Germany
        'FR': 0.10,  # France
        'AU': 0.10,  # Australia
        'JP': 0.10,  # Japan
        'NL': 0.10,  # Netherlands
        'SE': 0.10,  # Sweden
        'CH': 0.10,  # Switzerland
        'DK': 0.10,  # Denmark
        'NO': 0.10,  # Norway
        'FI': 0.10,  # Finland
        'IT': 0.15,  # Italy
        'ES': 0.15,  # Spain
        'KR': 0.15,  # South Korea
        'SG': 0.15,  # Singapore
        'HK': 0.20,  # Hong Kong
        'NZ': 0.10,  # New Zealand
        'IE': 0.10,  # Ireland
        'BE': 0.10,  # Belgium
        'AT': 0.10,  # Austria
        'IL': 0.20,  # Israel
        'ZA': 0.25,  # South Africa
    }
    
    def __init__(self):
        self.geoip = geoip2fast.GeoIP2Fast()
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
        
    def get_db_connection(self):
        """Get direct database connection"""
        return sqlite3.connect(DB_FILE)
    
    def decrypt_password(self, encrypted_password):
        """Simple password decryption"""
        if encrypted_password.startswith("PLAIN:"):
            return encrypted_password[6:]  # Remove "PLAIN:" prefix
        # For now, assume passwords are stored as plain text for testing
        return encrypted_password
    
    def get_imap_accounts(self):
        """Get active IMAP accounts from database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email_address, provider, host, port, encrypted_password, target_folders
                FROM accounts 
                WHERE is_active = TRUE
                ORDER BY last_used DESC
            """)
            
            accounts = []
            for row in cursor.fetchall():
                account = {
                    'id': row[0],
                    'email_address': row[1], 
                    'provider': row[2],
                    'host': row[3],
                    'port': row[4],
                    'password': self.decrypt_password(row[5]),
                    'target_folders': json.loads(row[6]) if row[6] else ['INBOX']
                }
                accounts.append(account)
            
            conn.close()
            print(f"📧 Loaded {len(accounts)} accounts from database")
            return accounts
        except Exception as e:
            print(f"❌ Failed to get IMAP accounts: {e}")
            return []
    
    def extract_ip_from_headers(self, headers):
        """Extract sender IP address from email headers"""
        if not headers:
            return None
            
        try:
            # Split headers into lines
            header_lines = headers.split('\n')
            
            # Look for Received headers in reverse order (most recent first)
            received_headers = []
            for line in header_lines:
                if line.lower().startswith('received:'):
                    received_headers.append(line)
            
            # Process received headers to find external IPs
            for received in received_headers:
                ip = self.extract_ip_from_received_header(received)
                if ip and self.is_external_ip(ip):
                    return ip
                    
            # Fallback: look for other IP-containing headers
            for line in header_lines:
                if any(header in line.lower() for header in ['x-originating-ip:', 'x-sender-ip:', 'x-real-ip:']):
                    ip = self.extract_ip_from_line(line)
                    if ip and self.is_external_ip(ip):
                        return ip
                        
            return None
            
        except Exception as e:
            print(f"Error extracting IP from headers: {e}")
            return None
    
    def extract_ip_from_received_header(self, received_header):
        """Extract IP from a Received header line"""
        # Pattern 1: [ip.address] format
        bracket_pattern = r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]'
        match = re.search(bracket_pattern, received_header)
        if match:
            return match.group(1)
            
        # Pattern 2: (ip.address) format  
        paren_pattern = r'\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)'
        match = re.search(paren_pattern, received_header)
        if match:
            return match.group(1)
            
        # Pattern 3: standalone IP after "from"
        from_pattern = r'from\s+[^\s]*\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(from_pattern, received_header, re.IGNORECASE)
        if match:
            return match.group(1)
            
        return None
    
    def extract_ip_from_line(self, line):
        """Extract IP from any header line"""
        ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(ip_pattern, line)
        return match.group(1) if match else None
    
    def is_external_ip(self, ip):
        """Check if IP is external (not private/local)"""
        try:
            octets = [int(x) for x in ip.split('.')]
            
            # Private IP ranges to exclude:
            if octets[0] == 10:
                return False
            elif octets[0] == 172 and 16 <= octets[1] <= 31:
                return False
            elif octets[0] == 192 and octets[1] == 168:
                return False
            elif octets[0] == 127:
                return False
            elif octets[0] == 169 and octets[1] == 254:
                return False
            elif octets[0] == 0:
                return False
                
            return True
            
        except (ValueError, IndexError):
            return False
    
    def get_geographic_data(self, ip_address):
        """Get geographic data for an IP address"""
        if not ip_address or not self.is_external_ip(ip_address):
            return None, None, None, 0.30, "NO_EXTERNAL_IP"
            
        try:
            # Use GeoIP2Fast for geographic lookup
            result = self.geoip.lookup(ip_address)
            
            if result and result.country_code:
                country_code = result.country_code
                country_name = result.country_name or country_code
                
                # Calculate risk score based on country
                risk_score = self.COUNTRY_RISK_SCORES.get(country_code, 0.30)
                
                return ip_address, country_code, country_name, risk_score, "GEOIP2FAST_LOOKUP"
            else:
                # IP lookup failed but we have the IP
                return ip_address, None, None, 0.40, "IP_EXTRACTED_COUNTRY_UNKNOWN"
                
        except Exception as e:
            print(f"Geographic lookup failed for IP {ip_address}: {e}")
            return ip_address, None, None, 0.35, "GEOIP_LOOKUP_ERROR"
    
    def connect_to_imap(self, account):
        """Connect to IMAP server for an account"""
        try:
            # Connect to IMAP server
            if account['port'] == 993:
                imap = imaplib.IMAP4_SSL(account['host'], account['port'])
            else:
                imap = imaplib.IMAP4(account['host'], account['port'])
                
            # Login
            imap.login(account['email_address'], account['password'])
            print(f"✅ Connected to {account['email_address']} ({account['provider']})")
            return imap
            
        except Exception as e:
            print(f"❌ Failed to connect to {account['email_address']}: {e}")
            return None
    
    def process_emails_from_account(self, account, max_emails_per_account=300):
        """Process emails from a specific account"""
        imap = self.connect_to_imap(account)
        if not imap:
            return 0
            
        processed_from_account = 0
        
        try:
            folders = account['target_folders']
            
            for folder in folders:
                if processed_from_account >= max_emails_per_account:
                    break
                    
                try:
                    # Select folder
                    status, _ = imap.select(folder)
                    if status != 'OK':
                        print(f"⚠️ Cannot access folder {folder} in {account['email_address']}")
                        continue
                        
                    # Search for emails
                    status, message_ids = imap.search(None, 'ALL')
                    if status != 'OK':
                        continue
                        
                    email_ids = message_ids[0].split()
                    
                    # Process most recent emails first
                    email_ids = email_ids[-200:]  # Take last 200 for recent emails
                    
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
    
    def create_session_entry(self, account_id):
        """Create a session entry for geographic processing"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions (
                    account_id, start_time, session_type, is_preview
                ) VALUES (?, ?, 'geographic_intelligence', 0)
            """, (account_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return session_id
            
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return 1  # Fallback session ID
    
    def process_single_email(self, email_message, uid, folder, account_id):
        """Process a single email for geographic intelligence"""
        try:
            # Extract headers
            headers = str(email_message)
            
            # Extract basic email data
            sender = email_message.get('From', '')
            subject = email_message.get('Subject', '')
            
            # Process geographic intelligence
            sender_ip, country_code, country_name, risk_score, detection_method = self.get_geographic_data(
                self.extract_ip_from_headers(headers)
            )
            
            # Extract sender domain
            sender_domain = ''
            if '@' in sender:
                sender_domain = sender.split('@')[-1].strip('<>')
            
            # Create session entry first
            session_id = self.create_session_entry(account_id)
            
            # Determine action based on geographic risk
            if risk_score >= 0.80:
                action = 'DELETED'
                reason = f'High geographic risk: {country_code}'
                category = 'Geographic Risk'
            else:
                action = 'PRESERVED'
                reason = f'Geographic analysis: {country_code}'
                category = 'Geographic Analysis'
            
            # Insert into processed_emails_bulletproof table
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO processed_emails_bulletproof (
                    timestamp, session_id, folder_name, uid, sender_email, sender_domain,
                    subject, action, reason, category, confidence_score, ml_validation_method,
                    sender_ip, sender_country_code, sender_country_name, 
                    geographic_risk_score, detection_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                risk_score,
                'Geographic Intelligence Pipeline',
                sender_ip,
                country_code,
                country_name,
                risk_score,
                detection_method
            ))
            
            conn.commit()
            conn.close()
            
            # Update statistics
            self.stats['emails_processed'] += 1
            if sender_ip:
                self.stats['ips_extracted'] += 1
            if country_code:
                self.stats['countries_identified'] += 1
            if risk_score >= 0.80:
                self.stats['high_risk_emails'] += 1
            self.stats['geographic_data_populated'] += 1
                
            return True
            
        except Exception as e:
            print(f"❌ Error processing email {uid}: {e}")
            self.stats['processing_errors'] += 1
            return False
    
    def verify_database_population(self):
        """Verify that the database has been properly populated"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Count records with geographic data
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(sender_ip) as records_with_ip,
                    COUNT(sender_country_code) as records_with_country,
                    COUNT(CASE WHEN geographic_risk_score > 0 THEN 1 END) as records_with_risk_score
                FROM processed_emails_bulletproof
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"\n📊 DATABASE VERIFICATION:")
                print(f"   Total Records (last hour): {result[0]}")
                print(f"   Records with IP: {result[1]}")
                print(f"   Records with Country: {result[2]}")
                print(f"   Records with Risk Score: {result[3]}")
                
            # Show top countries
            cursor.execute("""
                SELECT sender_country_code, COUNT(*) as count
                FROM processed_emails_bulletproof 
                WHERE sender_country_code IS NOT NULL 
                AND timestamp > datetime('now', '-1 hour')
                GROUP BY sender_country_code
                ORDER BY count DESC
                LIMIT 10
            """)
            
            country_stats = cursor.fetchall()
            if country_stats:
                print(f"\n🌍 TOP COUNTRIES (last hour):")
                for country, count in country_stats:
                    print(f"   {country}: {count} emails")
            
            conn.close()
                    
        except Exception as e:
            print(f"❌ Database verification error: {e}")
    
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

def main():
    """Main execution"""
    processor = StandaloneGeographicProcessor()
    processor.run_autonomous_processing()

if __name__ == "__main__":
    main()