#!/usr/bin/env python3
"""
Analyze spam patterns to suggest detailed subcategory tracking
"""
import sqlite3
import json
from collections import Counter, defaultdict
import re

db_path = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Analyzing Spam Patterns for Subcategory Insights\n")

# 1. Analyze subject patterns within each category
print("1. SUBJECT LINE PATTERNS BY CATEGORY:\n")
cursor.execute("""
    SELECT category, subject, COUNT(*) as count
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED' 
    AND category IS NOT NULL
    AND subject IS NOT NULL
    GROUP BY category, subject
    HAVING count > 2
    ORDER BY category, count DESC
""")

category_patterns = defaultdict(lambda: defaultdict(int))
category_keywords = defaultdict(Counter)

for row in cursor.fetchall():
    category = row[0]
    subject = row[1].lower()
    count = row[2]
    
    # Extract key patterns
    if 'auto' in subject and ('warranty' in subject or 'protection' in subject):
        category_patterns[category]['Auto Warranty'] += count
    elif 'insurance' in subject:
        category_patterns[category]['Insurance'] += count
    elif 'loan' in subject or 'credit' in subject:
        category_patterns[category]['Loans/Credit'] += count
    elif 'crypto' in subject or 'bitcoin' in subject or 'btc' in subject:
        category_patterns[category]['Cryptocurrency'] += count
    elif 'cbd' in subject or 'gumm' in subject:
        category_patterns[category]['CBD/Cannabis'] += count
    elif 'weight' in subject or 'diet' in subject or 'keto' in subject:
        category_patterns[category]['Weight Loss'] += count
    elif 'viagra' in subject or 'cialis' in subject or 'ed' in subject:
        category_patterns[category]['ED Medication'] += count
    elif 'casino' in subject or 'slot' in subject or 'bet' in subject:
        category_patterns[category]['Casino/Betting'] += count
    elif 'solar' in subject:
        category_patterns[category]['Solar Panels'] += count
    elif 'amazon' in subject or 'walmart' in subject or 'target' in subject:
        category_patterns[category]['Retail Impersonation'] += count
    elif 'fedex' in subject or 'ups' in subject or 'usps' in subject or 'delivery' in subject:
        category_patterns[category]['Shipping/Delivery'] += count
    elif 'irs' in subject or 'tax' in subject:
        category_patterns[category]['Tax Scams'] += count
    elif 'survey' in subject or 'opinion' in subject:
        category_patterns[category]['Survey Scams'] += count
    elif 'winner' in subject or 'won' in subject or 'prize' in subject:
        category_patterns[category]['Prize/Lottery'] += count
    elif 'invoice' in subject or 'receipt' in subject or 'order' in subject:
        category_patterns[category]['Fake Transactions'] += count
    elif 'dating' in subject or 'singles' in subject or 'meet' in subject:
        category_patterns[category]['Dating Services'] += count
    elif 'job' in subject or 'career' in subject or 'hiring' in subject:
        category_patterns[category]['Job Scams'] += count

# Print findings by category
for category in sorted(category_patterns.keys()):
    patterns = category_patterns[category]
    if patterns:
        print(f"{category}:")
        for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pattern}: {count} emails")
        print()

# 2. Analyze domain patterns
print("\n2. DOMAIN PATTERN ANALYSIS:\n")
cursor.execute("""
    SELECT 
        CASE 
            WHEN sender_domain LIKE '%.ru' THEN 'Russian domains (.ru)'
            WHEN sender_domain LIKE '%.cn' THEN 'Chinese domains (.cn)'
            WHEN sender_domain LIKE '%.tk' THEN 'Free domains (.tk)'
            WHEN sender_domain LIKE '%.ml' THEN 'Free domains (.ml)'
            WHEN sender_domain LIKE '%.ga' THEN 'Free domains (.ga)'
            WHEN sender_domain LIKE '%.click' THEN 'Click-tracking domains'
            WHEN sender_domain LIKE '%.online' THEN 'Generic TLD (.online)'
            WHEN sender_domain LIKE '%.shop' THEN 'Shopping domains (.shop)'
            WHEN sender_domain LIKE '%.store' THEN 'Store domains (.store)'
            WHEN LENGTH(sender_domain) - LENGTH(REPLACE(sender_domain, '.', '')) > 3 THEN 'Multi-subdomain (4+ levels)'
            WHEN sender_domain LIKE '%amazon%' AND sender_domain != 'amazon.com' THEN 'Fake Amazon'
            WHEN sender_domain LIKE '%paypal%' AND sender_domain != 'paypal.com' THEN 'Fake PayPal'
            WHEN sender_domain LIKE '%google%' AND sender_domain NOT LIKE '%.google.com' THEN 'Fake Google'
            ELSE 'Other'
        END as domain_pattern,
        COUNT(*) as count,
        COUNT(DISTINCT category) as category_variety
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    GROUP BY domain_pattern
    HAVING count > 10
    ORDER BY count DESC
""")

print("Domain Patterns (>10 emails):")
for row in cursor.fetchall():
    if row[0] != 'Other':
        print(f"  - {row[0]}: {row[1]} emails across {row[2]} categories")

# 3. Time-based patterns
print("\n\n3. SPAM TIMING PATTERNS:\n")
cursor.execute("""
    SELECT 
        CAST(strftime('%H', timestamp) AS INTEGER) as hour,
        COUNT(*) as count,
        COUNT(DISTINCT category) as categories
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    GROUP BY hour
    ORDER BY hour
""")

print("Hourly spam distribution (UTC):")
hourly = cursor.fetchall()
peak_hours = sorted(hourly, key=lambda x: x[1], reverse=True)[:3]
print(f"  Peak hours: {', '.join([f'{h[0]}:00 ({h[1]} emails)' for h in peak_hours])}")

# 4. Geographic subcategories
print("\n\n4. GEOGRAPHIC SPAM SUBCATEGORIES:\n")
cursor.execute("""
    SELECT 
        sender_country_code,
        category,
        COUNT(*) as count
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED' 
    AND sender_country_code IS NOT NULL
    GROUP BY sender_country_code, category
    HAVING count > 20
    ORDER BY sender_country_code, count DESC
""")

geo_categories = defaultdict(list)
for row in cursor.fetchall():
    geo_categories[row[0]].append((row[1], row[2]))

for country in ['US', 'GB', 'RU', 'ZA']:
    if country in geo_categories:
        print(f"\n{country} specializes in:")
        for cat, count in geo_categories[country][:3]:
            print(f"  - {cat}: {count} emails")

# 5. Emerging patterns (recent 30 days)
print("\n\n5. EMERGING SPAM PATTERNS (Last 30 days):\n")
cursor.execute("""
    SELECT subject, COUNT(*) as count
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND datetime(timestamp) > datetime('now', '-30 days')
    AND subject IS NOT NULL
    GROUP BY subject
    HAVING count > 3
    ORDER BY count DESC
    LIMIT 10
""")

recent_subjects = cursor.fetchall()
emerging_patterns = Counter()
for subject, count in recent_subjects:
    subject_lower = subject.lower()
    if 'ai' in subject_lower or 'chatgpt' in subject_lower:
        emerging_patterns['AI/ChatGPT Tools'] += count
    elif 'nft' in subject_lower:
        emerging_patterns['NFT Scams'] += count
    elif 'covid' in subject_lower or 'vaccine' in subject_lower:
        emerging_patterns['COVID-related'] += count
    elif 'remote' in subject_lower or 'work from home' in subject_lower:
        emerging_patterns['Remote Work Scams'] += count
    elif 'tiktok' in subject_lower or 'instagram' in subject_lower:
        emerging_patterns['Social Media'] += count

if emerging_patterns:
    print("Emerging themes:")
    for pattern, count in emerging_patterns.most_common():
        print(f"  - {pattern}: {count} emails")

# 6. Suggested subcategory structure
print("\n\n6. SUGGESTED SUBCATEGORY TRACKING STRUCTURE:\n")

suggestions = {
    "Financial & Investment Spam": [
        "Auto Warranty/Protection",
        "Insurance Offers",
        "Loan/Credit Offers", 
        "Cryptocurrency/Bitcoin",
        "Investment Schemes",
        "Tax/IRS Scams"
    ],
    "Health & Medical Spam": [
        "Weight Loss/Diet",
        "CBD/Cannabis",
        "ED Medication",
        "General Pharma",
        "Medical Devices",
        "Health Insurance"
    ],
    "Marketing Spam": [
        "Retail Sales",
        "B2B Services",
        "Solar/Home Improvement",
        "Software/SaaS",
        "Survey/Opinion",
        "Newsletter Spam"
    ],
    "Scam/Fraud": [
        "Phishing Attempts",
        "Fake Transactions",
        "Prize/Lottery",
        "Job Scams",
        "Shipping/Delivery",
        "Account Verification"
    ],
    "Adult & Entertainment": [
        "Dating Services",
        "Adult Content",
        "Casino/Gambling",
        "Gaming/Apps"
    ],
    "Brand Impersonation": [
        "Fake Amazon",
        "Fake PayPal",
        "Fake Banking",
        "Fake Streaming Services",
        "Fake Social Media"
    ]
}

for main_cat, subcats in suggestions.items():
    print(f"\n{main_cat}:")
    for subcat in subcats:
        print(f"  → {subcat}")

conn.close()