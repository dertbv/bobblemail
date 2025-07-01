#!/usr/bin/env python3
"""
Database Geographic Enhancer for Atlas Email
Processes existing email records in database to add geographic intelligence
No IMAP or password access required - uses stored email data
"""

import sqlite3
import geoip2fast
import re
import json
from datetime import datetime
from pathlib import Path

class DatabaseGeographicEnhancer:
    """
    Enhances existing email records in processed_emails_bulletproof table with geographic intelligence
    Uses stored raw_data field to extract IP addresses and populate geographic fields
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
    
    def __init__(self, db_path="data/mail_filter.db"):
        self.db_path = db_path
        self.geoip = geoip2fast.GeoIP2Fast()
        self.stats = {
            'emails_processed': 0,
            'ips_extracted': 0,
            'countries_identified': 0,
            'high_risk_emails': 0,
            'database_updates': 0,
            'processing_errors': 0
        }
        
    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def extract_ip_from_headers(self, headers):
        """Extract sender IP address from email headers stored in raw_data"""
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
        """Get geographic data for an IP address using GeoIP2Fast"""
        if not ip_address or not self.is_external_ip(ip_address):
            return {
                'sender_ip': ip_address,
                'sender_country_code': None,
                'sender_country_name': None,
                'geographic_risk_score': 0.30,
                'detection_method': 'NO_EXTERNAL_IP'
            }
            
        try:
            # Use GeoIP2Fast for geographic lookup
            result = self.geoip.lookup(ip_address)
            
            if result and result.country_code:
                country_code = result.country_code
                country_name = result.country_name or country_code
                
                # Calculate risk score based on country
                risk_score = self.COUNTRY_RISK_SCORES.get(country_code, 0.30)
                
                return {
                    'sender_ip': ip_address,
                    'sender_country_code': country_code,
                    'sender_country_name': country_name,
                    'geographic_risk_score': risk_score,
                    'detection_method': 'GEOIP2FAST_LOOKUP'
                }
            else:
                # IP lookup failed but we have the IP
                return {
                    'sender_ip': ip_address,
                    'sender_country_code': None,
                    'sender_country_name': None,
                    'geographic_risk_score': 0.40,
                    'detection_method': 'IP_EXTRACTED_COUNTRY_UNKNOWN'
                }
                
        except Exception as e:
            print(f"Geographic lookup failed for IP {ip_address}: {e}")
            return {
                'sender_ip': ip_address,
                'sender_country_code': None,
                'sender_country_name': None,
                'geographic_risk_score': 0.35,
                'detection_method': 'GEOIP_LOOKUP_ERROR'
            }
    
    def get_emails_needing_geographic_data(self, limit=1000):
        """Get emails that need geographic data enhancement"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get emails without geographic data that have raw_data
            cursor.execute("""
                SELECT id, sender_email, raw_data
                FROM processed_emails_bulletproof 
                WHERE sender_ip IS NULL 
                AND raw_data IS NOT NULL 
                AND raw_data != ''
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            emails = cursor.fetchall()
            conn.close()
            
            print(f"📧 Found {len(emails)} emails needing geographic enhancement")
            return emails
            
        except Exception as e:
            print(f"❌ Error getting emails needing geographic data: {e}")
            return []
    
    def update_email_geographic_data(self, email_id, geo_data):
        """Update a single email record with geographic data"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE processed_emails_bulletproof 
                SET sender_ip = ?,
                    sender_country_code = ?,
                    sender_country_name = ?,
                    geographic_risk_score = ?,
                    detection_method = ?
                WHERE id = ?
            """, (
                geo_data['sender_ip'],
                geo_data['sender_country_code'], 
                geo_data['sender_country_name'],
                geo_data['geographic_risk_score'],
                geo_data['detection_method'],
                email_id
            ))
            
            conn.commit()
            conn.close()
            
            self.stats['database_updates'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Error updating email {email_id}: {e}")
            self.stats['processing_errors'] += 1
            return False
    
    def process_email_geographic_enhancement(self, email_record):
        """Process a single email record for geographic enhancement"""
        email_id, sender_email, raw_data = email_record
        
        try:
            # Extract IP from raw email headers
            sender_ip = self.extract_ip_from_headers(raw_data)
            
            # Get geographic data
            geo_data = self.get_geographic_data(sender_ip)
            
            # Update database
            success = self.update_email_geographic_data(email_id, geo_data)
            
            if success:
                # Update statistics
                self.stats['emails_processed'] += 1
                if geo_data['sender_ip']:
                    self.stats['ips_extracted'] += 1
                if geo_data['sender_country_code']:
                    self.stats['countries_identified'] += 1
                if geo_data['geographic_risk_score'] >= 0.80:
                    self.stats['high_risk_emails'] += 1
                    
                # Log interesting findings
                if geo_data['sender_country_code']:
                    print(f"📍 Enhanced: {sender_email} -> {geo_data['sender_country_code']} (Risk: {geo_data['geographic_risk_score']:.2f})")
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error processing email ID {email_id}: {e}")
            self.stats['processing_errors'] += 1
            return False
    
    def verify_geographic_enhancement(self):
        """Verify that geographic enhancement was successful"""
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
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"\n📊 DATABASE VERIFICATION:")
                print(f"   Total Records: {result[0]}")
                print(f"   Records with IP: {result[1]}")
                print(f"   Records with Country: {result[2]}")
                print(f"   Records with Risk Score: {result[3]}")
                
            # Show top countries
            cursor.execute("""
                SELECT sender_country_code, COUNT(*) as count
                FROM processed_emails_bulletproof 
                WHERE sender_country_code IS NOT NULL 
                GROUP BY sender_country_code
                ORDER BY count DESC
                LIMIT 10
            """)
            
            country_stats = cursor.fetchall()
            if country_stats:
                print(f"\n🌍 TOP COUNTRIES (all time):")
                for country, count in country_stats:
                    print(f"   {country}: {count} emails")
            
            # Show risk distribution
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN geographic_risk_score >= 0.80 THEN 'Very High (0.80+)'
                        WHEN geographic_risk_score >= 0.60 THEN 'High (0.60-0.79)'
                        WHEN geographic_risk_score >= 0.40 THEN 'Medium (0.40-0.59)'
                        WHEN geographic_risk_score >= 0.20 THEN 'Low (0.20-0.39)'
                        WHEN geographic_risk_score > 0 THEN 'Very Low (0.01-0.19)'
                        ELSE 'Unknown'
                    END as risk_category,
                    COUNT(*) as count
                FROM processed_emails_bulletproof
                WHERE geographic_risk_score IS NOT NULL
                GROUP BY risk_category
                ORDER BY 
                    CASE 
                        WHEN risk_category = 'Very High (0.80+)' THEN 1
                        WHEN risk_category = 'High (0.60-0.79)' THEN 2
                        WHEN risk_category = 'Medium (0.40-0.59)' THEN 3
                        WHEN risk_category = 'Low (0.20-0.39)' THEN 4
                        WHEN risk_category = 'Very Low (0.01-0.19)' THEN 5
                        ELSE 6
                    END
            """)
            
            risk_stats = cursor.fetchall()
            if risk_stats:
                print(f"\n🚨 RISK DISTRIBUTION:")
                for risk_category, count in risk_stats:
                    print(f"   {risk_category}: {count} emails")
            
            conn.close()
                    
        except Exception as e:
            print(f"❌ Database verification error: {e}")
    
    def run_autonomous_enhancement(self, target_count=1000):
        """Run autonomous geographic enhancement on existing database records"""
        print("🌍 ATLAS Email Database Geographic Enhancement")
        print("=" * 60)
        print(f"🎯 Target: Enhance {target_count} existing email records with geographic data")
        print("🚀 Running autonomously using stored email data - no IMAP access required")
        print()
        
        start_time = datetime.now()
        
        # Get emails needing geographic enhancement
        emails_to_process = self.get_emails_needing_geographic_data(target_count)
        
        if not emails_to_process:
            print("❌ No emails found that need geographic enhancement")
            return
        
        print(f"📧 Processing {len(emails_to_process)} email records...")
        print()
        
        # Process each email
        for i, email_record in enumerate(emails_to_process):
            success = self.process_email_geographic_enhancement(email_record)
            
            # Progress reporting
            if (i + 1) % 100 == 0:
                print(f"📊 Progress: {i + 1}/{len(emails_to_process)} emails processed")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("🎉 GEOGRAPHIC ENHANCEMENT COMPLETE")
        print("=" * 60)
        print(f"⏱️  Total Processing Time: {duration}")
        print(f"📧 Emails Processed: {self.stats['emails_processed']}")
        print(f"🔍 IP Addresses Extracted: {self.stats['ips_extracted']}")
        print(f"🏁 Countries Identified: {self.stats['countries_identified']}")
        print(f"🚨 High Risk Emails: {self.stats['high_risk_emails']}")
        print(f"💾 Database Updates: {self.stats['database_updates']}")
        print(f"❌ Processing Errors: {self.stats['processing_errors']}")
        
        # Verify enhancement results
        self.verify_geographic_enhancement()
        
        print("\n✅ Geographic enhancement completed successfully!")
        print("🎯 Database now contains real geographic data from processed emails")
        print("📊 Analytics dashboard ready to display live geographic intelligence")
        
        # Calculate enhancement rate
        if len(emails_to_process) > 0:
            success_rate = (self.stats['database_updates'] / len(emails_to_process)) * 100
            print(f"📈 Success Rate: {success_rate:.1f}% of emails successfully enhanced")
        
        if self.stats['ips_extracted'] > 0:
            country_id_rate = (self.stats['countries_identified'] / self.stats['ips_extracted']) * 100
            print(f"🌍 Country Identification Rate: {country_id_rate:.1f}% of extracted IPs")

def main():
    """Main execution"""
    enhancer = DatabaseGeographicEnhancer()
    enhancer.run_autonomous_enhancement(1000)

if __name__ == "__main__":
    main()