#!/usr/bin/env python3
"""Tag all emails without subcategories based on comprehensive pattern matching."""

import sqlite3
import re
from datetime import datetime
import json

class SubcategoryTagger:
    def __init__(self):
        self.conn = sqlite3.connect('data/mail_filter.db')
        self.cursor = self.conn.cursor()
        self.stats = {
            'total_processed': 0,
            'total_tagged': 0,
            'tags_by_category': {},
            'tags_by_subcategory': {}
        }
    
    def tag_email(self, uid, sender, subject, category):
        """Determine subcategory based on patterns."""
        subject_lower = subject.lower() if subject else ''
        sender_lower = sender.lower() if sender else ''
        
        # Auto warranty & insurance
        if any(word in subject_lower for word in ['warranty', 'expir', 'coverage', 'vehicle protection', 'car protection']):
            return 'Auto Warranty & Insurance', 0.9
        
        # Cryptocurrency scams
        if any(word in subject_lower for word in ['crypto', 'bitcoin', 'btc', 'ethereum', 'blockchain', 'coin']) and \
           any(word in subject_lower for word in ['trump', 'elon', 'musk', 'executive order', 'bombshell']):
            return 'Cryptocurrency Scams', 0.95
        
        # Package delivery phishing
        if any(word in subject_lower for word in ['package', 'delivery', 'shipment', 'tracking', 'parcel']) and \
           any(word in subject_lower for word in ['usps', 'ups', 'fedex', 'dhl', 'pending', 'failed']):
            return 'Package Delivery Phishing', 0.9
        
        # Tech support scams
        if any(word in subject_lower for word in ['virus', 'malware', 'infected', 'security alert', 'microsoft', 'windows']) or \
           ('icloud' in subject_lower and 'account' in subject_lower):
            return 'Tech Support Scams', 0.85
        
        # Investment fraud
        if any(word in subject_lower for word in ['stock', 'invest', 'trader', 'portfolio', 'buffett', 'market crash']) and \
           any(word in subject_lower for word in ['secret', 'insider', 'millionaire', 'alert']):
            return 'Investment Fraud', 0.9
        
        # Health/pharma spam
        if any(word in subject_lower for word in ['viagra', 'cialis', 'pill', 'medication', 'prescription', 
                                                   'weight loss', 'fat removal', 'keto', 'wegovy']):
            return 'Health & Pharma Spam', 0.85
        
        # Adult content
        if any(word in subject_lower for word in ['sex', 'adult', 'dating', 'single', 'horny', 'inch', 'd*ck', 
                                                   'p*ssy', 'johnson', 'erect']) or \
           any(emoji in subject for emoji in ['🍆', '🍑', '💦', '🍌']):
            return 'Adult Content', 0.95
        
        # Prize/lottery scams
        if any(word in subject_lower for word in ['winner', 'won', 'prize', 'lottery', 'gift card', 
                                                   'congratulations', '$500', '$1000', 'reward']) or \
           (any(emoji in subject for emoji in ['🎁', '🎉', '✅']) and 'won' in subject_lower):
            return 'Prize & Lottery Scams', 0.9
        
        # Job scams
        if any(word in subject_lower for word in ['job offer', 'hiring', 'remote work', 'work from home', 
                                                   'earn from home', '$5000/week']):
            return 'Job Scams', 0.85
        
        # Fake invoices/bills
        if any(word in subject_lower for word in ['invoice', 'receipt', 'payment', 'bill', 'statement']) and \
           any(word in subject_lower for word in ['due', 'overdue', 'pending', 'confirm']):
            return 'Fake Invoices & Bills', 0.8
        
        # Political/news spam (often investment related)
        if any(word in subject_lower for word in ['trump', 'biden', 'ukraine', 'russia', 'china']) and \
           any(word in subject_lower for word in ['leaked', 'secret', 'caught on camera', 'bombshell']):
            return 'Political News Spam', 0.75
        
        # General marketing
        if category == 'Commercial Spam' and not any(above_matched for above_matched in [False]):  # If no specific match
            if any(word in subject_lower for word in ['sale', 'offer', 'discount', 'deal', 'save']):
                return 'General Marketing', 0.6
        
        # Phishing attempts (general)
        if category == 'Dangerous':
            if any(word in subject_lower for word in ['account', 'verify', 'confirm', 'suspended', 'locked']):
                return 'Phishing Attempts', 0.7
        
        return None, 0
    
    def process_untagged_emails(self, batch_size=1000):
        """Process all emails without subcategories."""
        print(f"Starting subcategory tagging at {datetime.now()}")
        
        # Get count of untagged emails
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM processed_emails_bulletproof 
            WHERE subcategory IS NULL OR subcategory = ''
        ''')
        total_untagged = self.cursor.fetchone()[0]
        print(f"Found {total_untagged} emails without subcategories")
        
        offset = 0
        while True:
            # Fetch batch of untagged emails
            self.cursor.execute('''
                SELECT uid, sender_email, subject, category
                FROM processed_emails_bulletproof
                WHERE subcategory IS NULL OR subcategory = ''
                LIMIT ? OFFSET ?
            ''', (batch_size, offset))
            
            batch = self.cursor.fetchall()
            if not batch:
                break
            
            # Process batch
            updates = []
            for uid, sender, subject, category in batch:
                subcategory, confidence = self.tag_email(uid, sender, subject, category)
                
                if subcategory and confidence >= 0.7:  # Only tag if confidence is high enough
                    updates.append((subcategory, uid))
                    
                    # Update stats
                    self.stats['total_tagged'] += 1
                    self.stats['tags_by_category'][category] = self.stats['tags_by_category'].get(category, 0) + 1
                    self.stats['tags_by_subcategory'][subcategory] = self.stats['tags_by_subcategory'].get(subcategory, 0) + 1
                
                self.stats['total_processed'] += 1
            
            # Batch update database
            if updates:
                self.cursor.executemany('''
                    UPDATE processed_emails_bulletproof 
                    SET subcategory = ? 
                    WHERE uid = ?
                ''', updates)
                self.conn.commit()
            
            # Progress report
            print(f"Processed {self.stats['total_processed']}/{total_untagged} emails, tagged {len(updates)} in this batch")
            
            offset += batch_size
        
        print("\nTagging complete!")
        self.print_final_stats()
    
    def print_final_stats(self):
        """Print summary statistics."""
        print("\n" + "="*80)
        print("TAGGING SUMMARY")
        print("="*80)
        print(f"Total emails processed: {self.stats['total_processed']}")
        print(f"Total emails tagged: {self.stats['total_tagged']}")
        print(f"Tagging rate: {self.stats['total_tagged']/self.stats['total_processed']*100:.1f}%")
        
        print("\nTags by category:")
        for cat, count in sorted(self.stats['tags_by_category'].items()):
            print(f"  {cat}: {count}")
        
        print("\nTags by subcategory:")
        for subcat, count in sorted(self.stats['tags_by_subcategory'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {subcat}: {count}")
        
        # Save stats to file
        with open('subcategory_tagging_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)
        print("\nStats saved to subcategory_tagging_stats.json")
    
    def verify_results(self):
        """Verify tagging results."""
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        # Check overall stats
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN subcategory IS NOT NULL AND subcategory != '' THEN 1 ELSE 0 END) as tagged,
                SUM(CASE WHEN subcategory IS NULL OR subcategory = '' THEN 1 ELSE 0 END) as untagged
            FROM processed_emails_bulletproof
        ''')
        total, tagged, untagged = self.cursor.fetchone()
        print(f"Total emails: {total}")
        print(f"Tagged emails: {tagged}")
        print(f"Untagged emails: {untagged}")
        
        # Show sample of newly tagged emails
        print("\nSample of newly tagged emails:")
        self.cursor.execute('''
            SELECT category, subcategory, subject
            FROM processed_emails_bulletproof
            WHERE subcategory IS NOT NULL AND subcategory != ''
            ORDER BY RANDOM()
            LIMIT 20
        ''')
        
        for cat, subcat, subject in self.cursor.fetchall():
            print(f"\n[{cat}] → [{subcat}]")
            print(f"  {subject}")
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    tagger = SubcategoryTagger()
    
    try:
        # Process all untagged emails
        tagger.process_untagged_emails()
        
        # Verify results
        tagger.verify_results()
        
    finally:
        tagger.close()

if __name__ == '__main__':
    main()