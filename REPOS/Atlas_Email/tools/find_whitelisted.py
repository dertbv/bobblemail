#!/usr/bin/env python3
"""Find an actual whitelisted email to trace"""

import sqlite3

db = sqlite3.connect("data/mail_filter.db")
cursor = db.cursor()

# Find any recent email that might be whitelisted
cursor.execute("""
    SELECT sender_email, subject, category, reason, uid, folder_name
    FROM processed_emails_bulletproof 
    ORDER BY id DESC 
    LIMIT 10
""")

recent_emails = cursor.fetchall()
print("RECENT EMAILS:")
for i, email in enumerate(recent_emails):
    print(f"{i+1}. {email[0]} | {email[2]} | {email[1][:50]}...")

# Also check for any with user protection flags
cursor.execute("""
    SELECT DISTINCT p.sender_email, p.subject, p.category, s.flag_status
    FROM processed_emails_bulletproof p
    JOIN spam_user_actions s ON p.uid = s.uid AND p.folder_name = s.folder_name
    WHERE s.flag_status = 'not_spam'
    LIMIT 5
""")

protected_emails = cursor.fetchall()
print(f"\nEMAILS FLAGGED AS 'not_spam' (PROTECTED):")
for email in protected_emails:
    print(f"- {email[0]} | Category: {email[2]} | Flag: {email[3]}")
    print(f"  Subject: {email[1][:60]}...")

db.close()