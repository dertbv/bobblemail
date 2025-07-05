#!/usr/bin/env python3
"""Trace why emails are being marked as Whitelisted"""

import sqlite3
import json

# Connect to database
db_path = "data/mail_filter.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "="*80)
print("WHITELIST BUG INVESTIGATION")
print("="*80)

# 1. Check all emails marked as Whitelisted
print("\n1. EMAILS MARKED AS 'Whitelisted':")
print("-" * 40)
cursor.execute("""
    SELECT uid, sender, subject, reason, confidence_score, processed_date 
    FROM processed_emails_bulletproof 
    WHERE category = 'Whitelisted' 
    ORDER BY processed_date DESC
""")
whitelisted = cursor.fetchall()
print(f"Found {len(whitelisted)} emails marked as 'Whitelisted'")
for email in whitelisted:
    print(f"  - UID {email[0]}: {email[1]} | {email[2][:50]}...")
    print(f"    Reason: {email[3]}")
    print(f"    Date: {email[5]}")

# 2. Check recent emails from the preview session
print("\n\n2. RECENT EMAILS FROM dertbv@gmail.com ACCOUNT:")
print("-" * 40)
cursor.execute("""
    SELECT uid, sender, subject, category, reason, confidence_score, processed_date 
    FROM processed_emails_bulletproof 
    WHERE account_id IN (
        SELECT id FROM email_accounts WHERE email = 'dertbv@gmail.com'
    )
    ORDER BY processed_date DESC 
    LIMIT 20
""")
recent = cursor.fetchall()
print(f"Found {len(recent)} recent emails")

category_count = {}
for email in recent:
    category = email[3]
    if category not in category_count:
        category_count[category] = 0
    category_count[category] += 1
    
    if len(recent) <= 10:  # Show details if few emails
        print(f"  - UID {email[0]}: {email[1]}")
        print(f"    Subject: {email[2][:60]}...")
        print(f"    Category: {category}")
        print(f"    Reason: {email[4]}")
        print(f"    Date: {email[6]}")
        print()

print("\nCategory Summary:")
for cat, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat}: {count}")

# 3. Check if there's a flag protection mechanism
print("\n\n3. CHECKING FOR FLAG PROTECTION:")
print("-" * 40)
cursor.execute("""
    SELECT COUNT(*) as count, flag_status 
    FROM spam_user_actions 
    WHERE flag_status = 'not_spam' 
    GROUP BY flag_status
""")
protected = cursor.fetchall()
if protected:
    print(f"Found {protected[0][0]} emails flagged as 'not_spam' (protected)")
else:
    print("No emails found with 'not_spam' flag")

# 4. Check ML settings from database
print("\n\n4. ML SETTINGS IN DATABASE:")
print("-" * 40)
cursor.execute("""
    SELECT config_key, config_value 
    FROM configurations 
    WHERE config_key LIKE '%whitelist%' OR config_key LIKE '%ml%'
    ORDER BY config_key
""")
configs = cursor.fetchall()
for key, value in configs:
    print(f"  {key}: {value}")

# 5. Check if preview is counting something else as "Whitelisted Protected"
print("\n\n5. ANALYZING PREVIEW LOGIC:")
print("-" * 40)
print("Preview shows: 68 'Whitelisted Protected' out of 73 emails")
print("Database shows: 6 'Whitelisted' total (historical)")
print("\nPossible explanations:")
print("1. Preview is counting emails with flag_status='not_spam' as 'Whitelisted Protected'")
print("2. Preview is using different categorization logic than actual processing")
print("3. Preview is including emails that were preserved for other reasons")

# Check what might add up to 68
cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM processed_emails_bulletproof 
    WHERE account_id IN (
        SELECT id FROM email_accounts WHERE email = 'dertbv@gmail.com'
    )
    AND processed_date >= datetime('now', '-1 hour')
    GROUP BY category
    ORDER BY count DESC
""")
recent_categories = cursor.fetchall()
print("\n\nRecent processing (last hour) for this account:")
for cat, count in recent_categories:
    print(f"  {cat}: {count}")

conn.close()
print("\n" + "="*80)