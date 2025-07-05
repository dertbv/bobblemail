#!/usr/bin/env python3
"""Analyze emails without subcategories to understand patterns."""

import sqlite3
import json
from collections import Counter, defaultdict
import re

def analyze_untagged_emails():
    # Connect to database
    conn = sqlite3.connect('data/mail_filter.db')
    cursor = conn.cursor()
    
    # First, get stats on current state
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN subcategory IS NULL OR subcategory = '' THEN 1 ELSE 0 END) as no_subcategory,
            SUM(CASE WHEN subcategory IS NOT NULL AND subcategory != '' THEN 1 ELSE 0 END) as has_subcategory
        FROM processed_emails_bulletproof
    ''')
    stats = cursor.fetchone()
    print(f'Total emails: {stats[0]}')
    print(f'Without subcategory: {stats[1]}')
    print(f'With subcategory: {stats[2]}')
    print()
    
    # Get category distribution for untagged emails
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM processed_emails_bulletproof
        WHERE subcategory IS NULL OR subcategory = ''
        GROUP BY category
        ORDER BY count DESC
    ''')
    category_dist = cursor.fetchall()
    print('Category distribution for untagged emails:')
    for cat, count in category_dist:
        print(f'  {cat}: {count}')
    print()
    
    # Get sample of emails without subcategory
    cursor.execute('''
        SELECT uid, sender_email, subject, category
        FROM processed_emails_bulletproof
        WHERE subcategory IS NULL OR subcategory = ''
        LIMIT 100
    ''')
    samples = cursor.fetchall()
    
    print('Sample of emails without subcategory:')
    print('-' * 100)
    for i, (uid, sender, subject, category) in enumerate(samples[:20]):
        print(f'{i+1}. Category: {category}')
        print(f'   Sender: {sender}')
        print(f'   Subject: {subject}')
        print()
    
    # Analyze common patterns
    subject_words = Counter()
    sender_domains = Counter()
    
    cursor.execute('''
        SELECT sender_email, subject
        FROM processed_emails_bulletproof
        WHERE subcategory IS NULL OR subcategory = ''
    ''')
    
    for sender, subject in cursor:
        # Extract domain from sender
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            sender_domains[domain] += 1
        
        # Extract words from subject
        if subject:
            words = re.findall(r'\b\w+\b', subject.lower())
            subject_words.update(words)
    
    print('\nTop 30 sender domains:')
    for domain, count in sender_domains.most_common(30):
        print(f'  {domain}: {count}')
    
    print('\nTop 50 subject keywords:')
    for word, count in subject_words.most_common(50):
        if len(word) > 3:  # Skip short words
            print(f'  {word}: {count}')
    
    conn.close()

if __name__ == '__main__':
    analyze_untagged_emails()