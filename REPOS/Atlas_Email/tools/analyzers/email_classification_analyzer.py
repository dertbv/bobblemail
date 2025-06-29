#!/usr/bin/env python3

import sqlite3
import sys
import os
from pathlib import Path

def get_db_path():
    """Find the database file from any location"""
    # Try current directory first
    if os.path.exists('data/mail_filter.db'):
        return 'data/mail_filter.db'
    
    # Try from tools directory (go up to Atlas_Email root)
    script_dir = Path(__file__).parent
    atlas_root = script_dir.parent.parent
    db_path = atlas_root / 'data' / 'mail_filter.db'
    
    if db_path.exists():
        return str(db_path)
    
    # Try original email_project location
    email_project_db = atlas_root.parent / 'email_project' / 'mail_filter.db'
    if email_project_db.exists():
        return str(email_project_db)
    
    raise FileNotFoundError("Cannot find mail_filter.db database file")

def list_flagged_emails():
    """Show numbered list of research flagged emails"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get emails that are actually flagged for research
    cursor.execute('''
    SELECT pe.sender_email, pe.subject, pe.category, pe.reason, pe.id
    FROM processed_emails_bulletproof pe
    JOIN email_flags ef ON pe.uid = ef.email_uid
    WHERE ef.flag_type = 'RESEARCH' AND ef.is_active = 1
    ORDER BY pe.timestamp DESC
    ''')
    
    results = cursor.fetchall()
    print('Research Flagged Emails:')
    for i, row in enumerate(results, 1):
        sender_short = row[0].split('<')[-1].replace('>', '') if '<' in row[0] else row[0]
        print(f'{i}. {sender_short} - "{row[1]}" -> {row[2]}')
    
    conn.close()

def show_email(number):
    """Show email details by number with full analysis"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the same emails as the list function - actual research flagged emails
    cursor.execute('''
    SELECT pe.id, pe.sender_email, pe.subject, pe.category, pe.raw_data, 
           pe.reason, pe.confidence_score, pe.timestamp, pe.sender_domain
    FROM processed_emails_bulletproof pe
    JOIN email_flags ef ON pe.uid = ef.email_uid
    WHERE ef.flag_type = 'RESEARCH' AND ef.is_active = 1
    ORDER BY pe.timestamp DESC
    ''')
    
    results = cursor.fetchall()
    
    if 1 <= number <= len(results):
        email = results[number-1]
        print(f'\n📧 Email #{number} Analysis:')
        print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        print(f'From: {email[1]}')
        print(f'Domain: {email[8]}')
        print(f'Subject: {email[2]}')
        print(f'Classification: {email[3]}')
        print(f'Reason: {email[5]}')
        print(f'Confidence: {email[6]}')
        print(f'Timestamp: {email[7]}')
        print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        
        # Parse raw data for body content
        if email[4]:
            try:
                import json
                raw_data = json.loads(email[4])
                if 'body' in raw_data:
                    print(f'Body Preview: {raw_data["body"][:300]}...')
                elif 'content' in raw_data:
                    print(f'Content Preview: {raw_data["content"][:300]}...')
                else:
                    print(f'Raw Data: {email[4][:300]}...')
            except:
                print(f'Raw Data: {email[4][:300]}...')
        
        print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    else:
        print(f'Invalid number. Choose 1-{len(results)}')
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        list_flagged_emails()
    elif len(sys.argv) == 2:
        try:
            number = int(sys.argv[1])
            show_email(number)
        except ValueError:
            print("Usage: python script.py [number]")
    else:
        print("Usage: python script.py [number]")