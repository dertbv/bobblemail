#!/usr/bin/env python3
"""
Analyze potentially misclassified legitimate emails
"""
import sqlite3
import json

db_path = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Analyzing Potentially Misclassified Emails\n")

# 1. Check deleted emails from major legitimate providers
print("1. DELETED emails from typically legitimate providers:")
cursor.execute("""
    SELECT sender_domain, COUNT(*) as count
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND sender_domain IN (
        'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 
        'icloud.com', 'aol.com', 'protonmail.com', 'me.com',
        'live.com', 'msn.com', 'mac.com'
    )
    GROUP BY sender_domain
    ORDER BY count DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} emails deleted")

# 2. Check deleted emails with high confidence but from US/UK
print("\n2. High confidence SPAM from US/UK (potentially legitimate):")
cursor.execute("""
    SELECT 
        sender_country_code,
        category,
        COUNT(*) as count,
        AVG(confidence_score) as avg_confidence
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND sender_country_code IN ('US', 'GB')
    AND confidence_score > 0.8
    AND category NOT IN ('Phishing', 'Suspicious', 'Blacklisted', 'Spam')
    GROUP BY sender_country_code, category
    ORDER BY count DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]} - {row[1]}: {row[2]} emails (avg confidence: {row[3]:.2f})")

# 3. Check for patterns in deleted emails that might indicate legitimacy
print("\n3. Deleted emails with potentially legitimate patterns:")
cursor.execute("""
    SELECT 
        CASE 
            WHEN subject LIKE '%invoice%' THEN 'Invoice-related'
            WHEN subject LIKE '%order%' THEN 'Order-related'
            WHEN subject LIKE '%receipt%' THEN 'Receipt-related'
            WHEN subject LIKE '%confirm%' THEN 'Confirmation-related'
            WHEN subject LIKE '%account%' THEN 'Account-related'
            WHEN subject LIKE '%payment%' THEN 'Payment-related'
            WHEN subject LIKE '%subscription%' THEN 'Subscription-related'
            WHEN subject LIKE '%newsletter%' THEN 'Newsletter'
            ELSE 'Other'
        END as pattern,
        COUNT(*) as count
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND (
        subject LIKE '%invoice%' OR
        subject LIKE '%order%' OR
        subject LIKE '%receipt%' OR
        subject LIKE '%confirm%' OR
        subject LIKE '%account%' OR
        subject LIKE '%payment%' OR
        subject LIKE '%subscription%' OR
        subject LIKE '%newsletter%'
    )
    GROUP BY pattern
    ORDER BY count DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} emails")

# 4. Look for emails marked as Marketing/Promotional that were deleted
print("\n4. Marketing/Promotional emails that were DELETED (might want to preserve):")
cursor.execute("""
    SELECT 
        category,
        COUNT(*) as count,
        COUNT(DISTINCT sender_domain) as unique_domains
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND category IN ('Marketing', 'Promotional', 'Marketing Spam', 'Promotional Email')
    GROUP BY category
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} emails from {row[2]} unique domains")

# 5. Check for any user feedback on false positives
print("\n5. User feedback on misclassifications:")
cursor.execute("""
    SELECT 
        feedback_type,
        COUNT(*) as count
    FROM user_feedback
    WHERE feedback_type IN ('incorrect', 'wrong', 'false_positive')
    GROUP BY feedback_type
""")
feedback_results = cursor.fetchall()
if feedback_results:
    for row in feedback_results:
        print(f"  {row[0]}: {row[1]} reports")
else:
    print("  No user feedback on misclassifications found")

# 6. Sample of recent deleted emails for manual review
print("\n6. Sample of 10 recent DELETED emails for review:")
cursor.execute("""
    SELECT 
        sender_email,
        subject,
        category,
        confidence_score,
        sender_country_code
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND datetime(timestamp) > datetime('now', '-7 days')
    ORDER BY timestamp DESC
    LIMIT 10
""")
print("  Sender | Subject | Category | Confidence | Country")
print("  " + "-" * 80)
for row in cursor.fetchall():
    sender = row[0][:30] + "..." if len(row[0]) > 30 else row[0]
    subject = row[1][:30] + "..." if row[1] and len(row[1]) > 30 else row[1] or "No subject"
    print(f"  {sender} | {subject} | {row[2]} | {row[3]:.2f} | {row[4] or 'Unknown'}")

conn.close()