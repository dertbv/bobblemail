#!/usr/bin/env python3
"""Check whitelist issue in email processor"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def check_database():
    """Check database for Whitelisted entries"""
    print("=== DATABASE CHECK ===")
    try:
        conn = sqlite3.connect('../data/mail_filter.db')
        cursor = conn.cursor()
        
        # Count Whitelisted emails
        cursor.execute("SELECT COUNT(*) FROM processed_emails_bulletproof WHERE category = 'Whitelisted'")
        whitelist_count = cursor.fetchone()[0]
        print(f"Emails with 'Whitelisted' category: {whitelist_count}")
        
        # Get category breakdown
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM processed_emails_bulletproof 
            WHERE category IS NOT NULL
            GROUP BY category 
            ORDER BY count DESC
            LIMIT 15
        """)
        
        print("\nTop categories in database:")
        for category, count in cursor.fetchall():
            print(f"  {category}: {count}")
        
        # Check recent Whitelisted entries
        if whitelist_count > 0:
            cursor.execute("""
                SELECT timestamp, sender_email, subject, reason
                FROM processed_emails_bulletproof 
                WHERE category = 'Whitelisted'
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            print("\nRecent Whitelisted entries:")
            for row in cursor.fetchall():
                print(f"  {row[0]} - {row[1]} - {row[2][:50]}... - {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

def check_code():
    """Check if _check_whitelist_protection method exists"""
    print("\n=== CODE CHECK ===")
    try:
        with open('../src/atlas_email/core/email_processor.py', 'r') as f:
            content = f.read()
            
        # Check if method is called
        if '_check_whitelist_protection' in content:
            print("✓ _check_whitelist_protection is referenced in the code")
            
            # Check if method is defined
            if 'def _check_whitelist_protection' in content:
                print("✓ Method is properly defined")
            else:
                print("✗ METHOD IS CALLED BUT NOT DEFINED!")
                print("  This will cause an AttributeError when executed")
                
                # Find where it's called
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '_check_whitelist_protection' in line and 'def' not in line:
                        print(f"  Called at line {i+1}: {line.strip()}")
        else:
            print("✗ _check_whitelist_protection not found in file")
            
    except Exception as e:
        print(f"Code check error: {e}")

def main():
    print("Checking whitelist issue...\n")
    check_database()
    check_code()
    
    print("\n=== SUMMARY ===")
    print("The issue is that _check_whitelist_protection is being called but the method")
    print("doesn't exist in the EmailProcessor class. This causes the code to fail and")
    print("the 'Whitelisted' category is being stored in the database from previous runs.")

if __name__ == "__main__":
    main()