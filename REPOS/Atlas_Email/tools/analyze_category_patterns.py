#!/usr/bin/env python3
"""Analyze patterns by category to develop subcategory rules."""

import sqlite3
import re
from collections import Counter, defaultdict

def analyze_category_patterns():
    conn = sqlite3.connect('data/mail_filter.db')
    cursor = conn.cursor()
    
    categories = ['Commercial Spam', 'Dangerous', 'Legitimate Marketing', 'Scams']
    
    for category in categories:
        print(f"\n{'='*100}")
        print(f"CATEGORY: {category}")
        print('='*100)
        
        # Get samples for this category
        cursor.execute('''
            SELECT uid, sender_email, subject
            FROM processed_emails_bulletproof
            WHERE category = ? AND (subcategory IS NULL OR subcategory = '')
            LIMIT 50
        ''', (category,))
        
        samples = cursor.fetchall()
        
        # Analyze patterns
        patterns = defaultdict(list)
        
        for uid, sender, subject in samples:
            subject_lower = subject.lower() if subject else ''
            
            # Auto warranty/insurance patterns
            if any(word in subject_lower for word in ['warranty', 'insurance', 'coverage', 'expire', 'expir']):
                patterns['auto_warranty'].append(subject)
            
            # Cryptocurrency patterns
            if any(word in subject_lower for word in ['crypto', 'bitcoin', 'btc', 'ethereum', 'blockchain', 'coin']):
                patterns['cryptocurrency'].append(subject)
            
            # Package delivery patterns
            if any(word in subject_lower for word in ['package', 'delivery', 'shipment', 'usps', 'ups', 'fedex', 'dhl']):
                patterns['package_delivery'].append(subject)
            
            # Tech support patterns
            if any(word in subject_lower for word in ['virus', 'malware', 'security', 'microsoft', 'windows', 'apple', 'icloud']):
                patterns['tech_support'].append(subject)
            
            # Investment/financial patterns
            if any(word in subject_lower for word in ['invest', 'stock', 'trader', 'market', 'retirement', 'portfolio', 'buffett']):
                patterns['investment'].append(subject)
            
            # Health/pharma patterns
            if any(word in subject_lower for word in ['viagra', 'cialis', 'pill', 'medication', 'prescription', 'health', 'weight loss', 'fat', 'keto']):
                patterns['health_pharma'].append(subject)
            
            # Adult content patterns
            if any(word in subject_lower for word in ['sex', 'adult', 'dating', 'single', 'women', 'inch', 'd*ck', 'p*ssy', '🍆', '🍑']):
                patterns['adult_content'].append(subject)
            
            # Prize/lottery patterns
            if any(word in subject_lower for word in ['winner', 'won', 'prize', 'lottery', 'gift card', 'congratulations', '$500', '$1000']):
                patterns['prize_lottery'].append(subject)
            
            # Political/news patterns
            if any(word in subject_lower for word in ['trump', 'biden', 'ukraine', 'russia', 'china', 'war', 'breaking']):
                patterns['political_news'].append(subject)
            
            # Job scam patterns
            if any(word in subject_lower for word in ['job', 'hiring', 'remote work', 'salary', 'earn from home']):
                patterns['job_scams'].append(subject)
        
        # Print findings
        for pattern_type, subjects in patterns.items():
            if subjects:
                print(f"\n{pattern_type.upper()} ({len(subjects)} found):")
                for subj in subjects[:5]:  # Show first 5
                    print(f"  - {subj}")
    
    conn.close()

if __name__ == '__main__':
    analyze_category_patterns()