#!/usr/bin/env python3
"""Enhanced subcategory tagger with more comprehensive patterns."""

import sqlite3
import re
from datetime import datetime
import json

class EnhancedSubcategoryTagger:
    def __init__(self):
        self.conn = sqlite3.connect('data/mail_filter.db')
        self.cursor = self.conn.cursor()
        self.stats = {
            'total_processed': 0,
            'total_tagged': 0,
            'tags_by_category': {},
            'tags_by_subcategory': {}
        }
    
    def extract_domain(self, email):
        """Extract domain from email address."""
        if '@' in email:
            return email.split('@')[1].lower().strip('>')
        return ''
    
    def tag_email(self, uid, sender, subject, category):
        """Enhanced subcategory detection with more patterns."""
        subject_lower = subject.lower() if subject else ''
        sender_lower = sender.lower() if sender else ''
        domain = self.extract_domain(sender)
        
        # Enhanced Auto warranty & insurance
        if any(pattern in subject_lower for pattern in [
            'warranty', 'expir', 'coverage', 'vehicle protection', 'car protection',
            'carshield', 'endurance', 'auto protection', 'car warranty', 'vehicle warranty',
            'siriusxm', 'sirius xm', 'mcafee', 'norton', 'subscription expir'
        ]):
            return 'Auto Warranty & Insurance', 0.9
        
        # Enhanced Cryptocurrency scams
        if any(word in subject_lower for word in ['crypto', 'bitcoin', 'btc', 'ethereum', 'blockchain', 'coin', 'token']) or \
           ('trump' in subject_lower and 'executive order' in subject_lower):
            return 'Cryptocurrency Scams', 0.9
        
        # Enhanced Package delivery phishing
        if any(pattern in subject_lower for pattern in [
            'package', 'delivery', 'shipment', 'tracking', 'parcel',
            'usps', 'ups', 'fedex', 'dhl', 'amazon delivery'
        ]) and any(word in subject_lower for word in ['pending', 'failed', 'attempt', 'notification']):
            return 'Package Delivery Phishing', 0.9
        
        # Enhanced Tech support scams
        if any(pattern in subject_lower for pattern in [
            'virus', 'malware', 'infected', 'security alert', 'microsoft', 'windows',
            'icloud', 'apple id', 'account suspended', 'account locked', 'verify account',
            'antivirus', 'system infected', 'cyber attack', 'botnet'
        ]):
            return 'Tech Support Scams', 0.9
        
        # Enhanced Investment fraud
        if (any(word in subject_lower for word in ['stock', 'invest', 'trader', 'portfolio', 'buffett', 
                                                    'market', 'retirement', 'tesla', 'ai stock']) and \
            any(word in subject_lower for word in ['secret', 'insider', 'millionaire', 'alert', 
                                                    'crash', 'bombshell', 'revealed'])) or \
           any(pattern in subject_lower for pattern in ['trump stock', 'elon musk', 'one tiny stock']):
            return 'Investment Fraud', 0.9
        
        # Enhanced Health/pharma spam
        if any(pattern in subject_lower for pattern in [
            'viagra', 'cialis', 'pill', 'medication', 'prescription', 'weight loss',
            'fat removal', 'keto', 'wegovy', 'ozempic', 'health monitor', 'ed cure',
            'erectile', 'stiff', 'johnson', 'grow', 'enhancement', 'boost'
        ]):
            return 'Health & Pharma Spam', 0.85
        
        # Enhanced Adult content
        if any(pattern in subject_lower for pattern in [
            'sex', 'adult', 'dating', 'single', 'horny', 'inch', 'd*ck', 'dick',
            'p*ssy', 'pussy', 'johnson', 'erect', 'nailing', 'pu$$y', 'c*m', 'cum',
            'women', 'girl', 'obsessed', 'desperate', 'surprise your woman'
        ]) or any(emoji in subject for emoji in ['🍆', '🍑', '💦', '🍌', '🤤', '😋']):
            return 'Adult Content', 0.95
        
        # Enhanced Prize/lottery scams - MAJOR CATEGORY
        if any(pattern in subject_lower for pattern in [
            'winner', 'won', 'prize', 'lottery', 'gift card', 'congratulations',
            '$500', '$1000', 'reward', 'giveaway', 'sweepstake', 'claim your',
            'you have won', 'pending reward', 'unclaimed', 'walmart gift', 'amazon gift',
            'yeti', 'keurig', 'hp laptop', 'lenovo', 'temu', 'dominion energy',
            'loyalty reward', 'selected', 'chosen'
        ]) or (any(emoji in subject for emoji in ['🎁', '🎉', '✅', '🏆', '💰']) and 
               any(word in subject_lower for word in ['won', 'win', 'reward', 'claim'])):
            return 'Prize & Lottery Scams', 0.95
        
        # Job scams
        if any(pattern in subject_lower for pattern in [
            'job offer', 'hiring', 'remote work', 'work from home', 'earn from home',
            '$5000/week', 'part-time', 'full-time position', 'employment opportunity'
        ]):
            return 'Job Scams', 0.85
        
        # Enhanced Fake invoices/bills
        if any(pattern in subject_lower for pattern in [
            'invoice', 'receipt', 'payment', 'bill', 'statement', 'charge',
            'transaction', 'order confirmation', 'purchase'
        ]) and any(word in subject_lower for word in ['due', 'overdue', 'pending', 'confirm', 'verify']):
            return 'Fake Invoices & Bills', 0.85
        
        # Political/news spam
        if any(name in subject_lower for name in ['trump', 'biden', 'musk', 'buffett']) and \
           any(pattern in subject_lower for pattern in [
               'leaked', 'secret', 'caught on camera', 'bombshell', 'breaking',
               'horrifying', 'shocking', 'footage', 'revealed', 'warns'
           ]):
            return 'Political News Spam', 0.8
        
        # Generic marketing based on sender domains
        if category == 'Commercial Spam':
            # Check known marketing domains
            if any(domain.endswith(d) for d in [
                'futureslabresearch.com', 'economicrulebook.com', 'tradesprophet.com',
                'onlineinvestingdaily.com', 'girlsrockinvesting.com', 'smartearns.com',
                'economicage.com', 'financefreedompath.com', 'wealthinsightsjournal.com'
            ]):
                return 'Newsletter Marketing', 0.7
        
        # Enhanced phishing attempts for Dangerous category
        if category == 'Dangerous':
            if any(pattern in subject_lower for pattern in [
                'account', 'verify', 'confirm', 'suspended', 'locked', 'expire',
                'action required', 'update payment', 'security alert', 'unusual activity',
                'click here', 'act now', 'immediate action', 'urgent'
            ]):
                return 'Phishing Attempts', 0.8
            
            # Catch-all for suspicious dangerous emails
            if any(char in subject for char in ['🚨', '⚠️', '❌', '‼️']):
                return 'Suspicious Activity', 0.7
        
        # Category-specific catch-alls
        if category == 'Scams' and not subject_lower:
            return 'General Scam', 0.6
        
        if category == 'Commercial Spam':
            # Look for sales/marketing keywords
            if any(word in subject_lower for word in ['sale', 'offer', 'discount', 'deal', 'save', 'free', 'limited']):
                return 'General Marketing', 0.6
        
        return None, 0
    
    def process_untagged_emails(self, batch_size=1000):
        """Process all emails without subcategories."""
        print(f"Starting enhanced subcategory tagging at {datetime.now()}")
        
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
                
                if subcategory and confidence >= 0.6:  # Lower threshold for better coverage
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
            print(f"Processed {offset + len(batch)}/{total_untagged} emails, tagged {len(updates)} in this batch")
            
            offset += batch_size
        
        print("\nTagging complete!")
        self.print_final_stats()
    
    def print_final_stats(self):
        """Print summary statistics."""
        print("\n" + "="*80)
        print("ENHANCED TAGGING SUMMARY")
        print("="*80)
        print(f"Total emails processed: {self.stats['total_processed']}")
        print(f"Total emails tagged: {self.stats['total_tagged']}")
        print(f"Tagging rate: {self.stats['total_tagged']/self.stats['total_processed']*100:.1f}%")
        
        print("\nTags by category:")
        for cat, count in sorted(self.stats['tags_by_category'].items()):
            print(f"  {cat}: {count}")
        
        print("\nTop 15 subcategories:")
        sorted_subcats = sorted(self.stats['tags_by_subcategory'].items(), key=lambda x: x[1], reverse=True)
        for subcat, count in sorted_subcats[:15]:
            print(f"  {subcat}: {count}")
        
        # Save stats to file
        with open('enhanced_tagging_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)
        print("\nStats saved to enhanced_tagging_stats.json")
    
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
        print(f"Overall tagging rate: {tagged/total*100:.1f}%")
        
        # Subcategory distribution
        print("\nSubcategory distribution:")
        self.cursor.execute('''
            SELECT subcategory, COUNT(*) as count
            FROM processed_emails_bulletproof
            WHERE subcategory IS NOT NULL AND subcategory != ''
            GROUP BY subcategory
            ORDER BY count DESC
        ''')
        
        for subcat, count in self.cursor.fetchall():
            print(f"  {subcat}: {count}")
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    tagger = EnhancedSubcategoryTagger()
    
    try:
        # Process all untagged emails
        tagger.process_untagged_emails()
        
        # Verify results
        tagger.verify_results()
        
    finally:
        tagger.close()

if __name__ == '__main__':
    main()