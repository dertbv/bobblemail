#!/usr/bin/env python3
"""
Analyze emails to find better patterns for subcategory tagging
"""
import sqlite3
from collections import Counter
import re

db_path = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Analyzing subjects to find better patterns...\n")

# Get all subjects
cursor.execute("""
    SELECT subject, category, sender_domain
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND subject IS NOT NULL
""")

# Common spam indicators
indicators = {
    'ED/Pharma': [
        r'(erect|hard|last|long|perform|stamina|satisfy)',
        r'(pill|med|rx|pharma|drug)',
        r'(male|men|manhood|bedroom)',
        r'(doctor|clinic|prescription)',
        r'\b(ed|pe)\b',
        r'(penis|dick|size)',
        r'(sexual|sex)',
    ],
    'Weight Loss': [
        r'(weight|pound|kg|lbs|fat|slim|skinny|thin)',
        r'(loss|lose|burn|shed|drop)',
        r'(diet|keto|appetite|hungry)',
        r'(belly|stomach|waist)',
    ],
    'Financial/Investment': [
        r'(stock|invest|crypto|bitcoin|trading)',
        r'(profit|earn|income|money|cash|\$)',
        r'(opportunity|secret|system|method)',
        r'(millionaire|rich|wealth)',
    ],
    'Auto/Warranty': [
        r'(auto|car|vehicle|truck)',
        r'(warranty|protection|coverage|service)',
        r'(expire|ending|final|last)',
    ],
    'Prize/Lottery': [
        r'(win|won|winner|congratul)',
        r'(prize|reward|gift|free)',
        r'(claim|collect|redeem)',
        r'(\$\d+|million|thousand)',
    ],
    'Phishing': [
        r'(verify|confirm|update|validate)',
        r'(account|password|security|identity)',
        r'(suspend|lock|expire|urgent)',
        r'(click|act now|immediate)',
    ],
    'Shipping/Delivery': [
        r'(deliver|ship|package|parcel)',
        r'(track|order|usps|ups|fedex)',
        r'(arrived|ready|waiting)',
    ]
}

# Analyze subjects
pattern_hits = Counter()
examples = {}

for subject, category, domain in cursor.fetchall():
    if not subject:
        continue
    
    subject_lower = subject.lower()
    
    # Check each pattern category
    for pattern_cat, patterns in indicators.items():
        for pattern in patterns:
            if re.search(pattern, subject_lower):
                pattern_hits[pattern_cat] += 1
                if pattern_cat not in examples:
                    examples[pattern_cat] = []
                if len(examples[pattern_cat]) < 3:
                    examples[pattern_cat].append((subject[:60], category))
                break

print("📊 PATTERN MATCHES FOUND:\n")
for pattern_cat, count in pattern_hits.most_common():
    print(f"{pattern_cat}: {count} emails")
    if pattern_cat in examples:
        print("  Examples:")
        for subj, cat in examples[pattern_cat]:
            print(f"    - {subj}... [{cat}]")
    print()

# Look for common words in subjects
print("\n🔤 MOST COMMON WORDS IN SPAM SUBJECTS:\n")
words = Counter()
for row in cursor.execute("SELECT subject FROM processed_emails_bulletproof WHERE action = 'DELETED' AND subject IS NOT NULL"):
    subject = row[0].lower()
    # Extract words
    for word in re.findall(r'\b[a-z]{4,}\b', subject):
        if word not in ['your', 'from', 'with', 'this', 'that', 'have', 'will', 'been', 'were']:
            words[word] += 1

for word, count in words.most_common(30):
    print(f"  '{word}': {count}")

# Analyze sender domains
print("\n\n🌐 SUSPICIOUS DOMAIN PATTERNS:\n")
cursor.execute("""
    SELECT sender_domain, COUNT(*) as count
    FROM processed_emails_bulletproof
    WHERE action = 'DELETED'
    AND sender_domain IS NOT NULL
    GROUP BY sender_domain
    HAVING count > 5
    ORDER BY count DESC
    LIMIT 20
""")

for domain, count in cursor.fetchall():
    # Check for suspicious patterns
    suspicious = []
    if len(domain.split('.')) > 3:
        suspicious.append("multi-subdomain")
    if any(char.isdigit() for char in domain):
        suspicious.append("contains numbers")
    if len(domain) > 30:
        suspicious.append("very long")
    
    if suspicious:
        print(f"  {domain}: {count} emails ({', '.join(suspicious)})")

conn.close()