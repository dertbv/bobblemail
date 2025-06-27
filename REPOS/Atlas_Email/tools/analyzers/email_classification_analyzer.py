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
    
    cursor.execute('''
    SELECT DISTINCT pe.uid, pe.sender_email, pe.subject, pe.category
    FROM processed_emails_bulletproof pe
    JOIN email_flags ef ON pe.uid = ef.email_uid
    WHERE ef.flag_type = 'RESEARCH'
    ''')
    
    results = cursor.fetchall()
    print('Research Flagged Emails:')
    for i, row in enumerate(results, 1):
        print(f'{i}. {row[1]} - "{row[2]}" -> {row[3]}')
    
    conn.close()

def show_email(number):
    """Show email details by number"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT DISTINCT pe.uid, pe.sender_email, pe.subject, pe.category, pe.raw_data
    FROM processed_emails_bulletproof pe
    JOIN email_flags ef ON pe.uid = ef.email_uid
    WHERE ef.flag_type = 'RESEARCH'
    ''')
    
    results = cursor.fetchall()
    
    if 1 <= number <= len(results):
        email = results[number-1]
        print(f'Email {number}:')
        print(f'From: {email[1]}')
        print(f'Subject: {email[2]}')
        print(f'Current Classification: {email[3]}')
        print(f'Body Preview: {email[4][:200]}...')
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