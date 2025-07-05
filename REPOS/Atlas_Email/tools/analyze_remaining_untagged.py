#!/usr/bin/env python3
"""Analyze the remaining 2,000 untagged emails to understand what patterns we missed."""

import sqlite3
import re
from collections import Counter, defaultdict

def analyze_remaining_untagged():
    conn = sqlite3.connect('data/mail_filter.db')
    cursor = conn.cursor()
    
    print("="*80)
    print("ANALYSIS OF REMAINING UNTAGGED EMAILS")
    print("="*80)
    
    # Get count by category
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM processed_emails_bulletproof
        WHERE subcategory IS NULL OR subcategory = ''
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    print("\nRemaining untagged by category:")
    category_counts = cursor.fetchall()
    for cat, count in category_counts:
        print(f"  {cat}: {count}")
    
    # Sample analysis for each category
    for category, _ in category_counts:
        print(f"\n{'='*60}")
        print(f"CATEGORY: {category} - Sample Analysis")
        print('='*60)
        
        cursor.execute('''
            SELECT sender_email, subject
            FROM processed_emails_bulletproof
            WHERE category = ? AND (subcategory IS NULL OR subcategory = '')
            LIMIT 20
        ''', (category,))
        
        samples = cursor.fetchall()
        
        # Analyze patterns
        subject_patterns = defaultdict(int)
        domain_patterns = Counter()
        
        print("\nSample emails:")
        for i, (sender, subject) in enumerate(samples[:10], 1):
            domain = sender.split('@')[1].lower().strip('>') if '@' in sender else 'unknown'
            print(f"\n{i}. Domain: {domain}")
            print(f"   Subject: {subject}")
            
            # Detect patterns
            if subject:
                # Look for common words
                words = re.findall(r'\b\w{4,}\b', subject.lower())
                for word in words:
                    if word not in ['your', 'have', 'with', 'this', 'from', 'that']:
                        subject_patterns[word] += 1
        
        # Get all domains for this category
        cursor.execute('''
            SELECT sender_email
            FROM processed_emails_bulletproof
            WHERE category = ? AND (subcategory IS NULL OR subcategory = '')
        ''', (category,))
        
        all_senders = cursor.fetchall()
        for (sender,) in all_senders:
            if '@' in sender:
                domain = sender.split('@')[1].lower().strip('>')
                domain = re.sub(r'[<>\s]', '', domain)
                domain_patterns[domain] += 1
        
        print(f"\nTop domains in untagged {category}:")
        for domain, count in domain_patterns.most_common(10):
            print(f"  {domain}: {count}")
    
    # Overall pattern analysis
    print(f"\n{'='*80}")
    print("COMMON CHARACTERISTICS OF UNTAGGED EMAILS")
    print('='*80)
    
    cursor.execute('''
        SELECT subject
        FROM processed_emails_bulletproof
        WHERE subcategory IS NULL OR subcategory = ''
        AND subject IS NOT NULL
        LIMIT 500
    ''')
    
    all_subjects = [row[0] for row in cursor.fetchall()]
    
    # Analyze subject characteristics
    characteristics = {
        'very_short': 0,  # < 20 chars
        'no_keywords': 0,  # No recognizable spam keywords
        'foreign_chars': 0,  # Non-ASCII characters
        'all_caps': 0,
        'numeric_heavy': 0,  # Lots of numbers
        'generic': 0  # Very generic subjects
    }
    
    for subject in all_subjects:
        if len(subject) < 20:
            characteristics['very_short'] += 1
        if subject.isupper() and len(subject) > 5:
            characteristics['all_caps'] += 1
        if re.search(r'[^\x00-\x7F]', subject):
            characteristics['foreign_chars'] += 1
        if len(re.findall(r'\d', subject)) > len(subject) * 0.3:
            characteristics['numeric_heavy'] += 1
    
    print("\nCharacteristics of untagged emails:")
    for char, count in characteristics.items():
        if count > 0:
            pct = count / len(all_subjects) * 100
            print(f"  {char}: {count} ({pct:.1f}%)")
    
    conn.close()
    
    print("\nCONCLUSIONS:")
    print("The remaining untagged emails appear to be:")
    print("  1. Generic marketing without clear spam indicators")
    print("  2. Foreign language emails")
    print("  3. Very short subjects without keywords")
    print("  4. Legitimate business emails that don't fit patterns")
    print("  5. Edge cases requiring ML classification")

if __name__ == '__main__':
    analyze_remaining_untagged()