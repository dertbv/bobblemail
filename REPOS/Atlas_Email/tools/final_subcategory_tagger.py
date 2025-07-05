#!/usr/bin/env python3
"""Final comprehensive subcategory tagger to maximize coverage."""

import sqlite3
import re
from datetime import datetime
import json

class FinalSubcategoryTagger:
    def __init__(self):
        self.conn = sqlite3.connect('data/mail_filter.db')
        self.cursor = self.conn.cursor()
        self.stats = {
            'total_processed': 0,
            'total_tagged': 0,
            'tags_by_category': {},
            'tags_by_subcategory': {},
            'skipped_patterns': []
        }
    
    def extract_domain(self, email):
        """Extract domain from email address."""
        if '@' in email:
            domain = email.split('@')[1].lower().strip('>')
            # Clean up domain
            domain = re.sub(r'[<>\s]', '', domain)
            return domain
        return ''
    
    def analyze_remaining_patterns(self):
        """Analyze patterns in remaining untagged emails."""
        print("Analyzing remaining untagged emails...")
        
        self.cursor.execute('''
            SELECT sender_email, subject, category
            FROM processed_emails_bulletproof
            WHERE subcategory IS NULL OR subcategory = ''
            LIMIT 500
        ''')
        
        samples = self.cursor.fetchall()
        patterns = {
            'subjects': [],
            'domains': [],
            'categories': {}
        }
        
        for sender, subject, category in samples:
            patterns['subjects'].append(subject or '')
            domain = self.extract_domain(sender)
            if domain:
                patterns['domains'].append(domain)
            patterns['categories'][category] = patterns['categories'].get(category, 0) + 1
        
        print(f"\nRemaining emails by category:")
        for cat, count in patterns['categories'].items():
            print(f"  {cat}: {count}")
        
        return patterns
    
    def tag_email(self, uid, sender, subject, category):
        """Comprehensive tagging with catch-all patterns."""
        subject_lower = subject.lower() if subject else ''
        sender_lower = sender.lower() if sender else ''
        domain = self.extract_domain(sender)
        
        # === HIGH CONFIDENCE PATTERNS (0.9+) ===
        
        # Prize/lottery - be very aggressive here
        if ('$' in subject and any(num in subject for num in ['500', '1000', '100', '250'])) or \
           any(pattern in subject_lower for pattern in [
               'gift card', 'walmart', 'amazon', 'target gift', 'bestbuy',
               'claim', 'reward', 'winner', 'won', 'congratulations',
               'selected', 'chosen', 'pending', 'unclaimed'
           ]) or \
           (domain and any(spam_domain in domain for spam_domain in ['reinhardt.us.com', 'yamam.ots'])):
            return 'Prize & Lottery Scams', 0.95
        
        # Adult content - expanded patterns
        if any(pattern in subject_lower for pattern in [
            'sex', 'xxx', 'porn', 'nude', 'naked', 'horny', 'fuck',
            'dick', 'd*ck', 'd!ck', 'cock', 'penis', 'pussy', 'p*ssy',
            'cum', 'c*m', 'orgasm', 'erect', 'inch', 'size matter',
            'girl', 'women', 'milf', 'teen', 'hot singles'
        ]) or \
           any(emoji in subject for emoji in ['🍆', '🍑', '💦', '🍌', '🔞']):
            return 'Adult Content', 0.95
        
        # Cryptocurrency
        if any(word in subject_lower for word in ['crypto', 'bitcoin', 'btc', 'ethereum', 'coin', 'token', 'blockchain']):
            return 'Cryptocurrency Scams', 0.9
        
        # Investment fraud
        if any(pattern in subject_lower for pattern in [
            'stock', 'invest', 'trader', 'trading', 'market', 'portfolio',
            'warren buffett', 'wall street', 'nasdaq', 's&p'
        ]) and category in ['Commercial Spam', 'Scams']:
            return 'Investment Fraud', 0.85
        
        # Health/medical
        if any(pattern in subject_lower for pattern in [
            'viagra', 'cialis', 'pill', 'drug', 'medication', 'prescription',
            'weight', 'diet', 'keto', 'fat', 'slim', 'burn', 'detox',
            'cbd', 'gummies', 'supplement', 'vitamin'
        ]):
            return 'Health & Pharma Spam', 0.85
        
        # === MEDIUM CONFIDENCE PATTERNS (0.7-0.8) ===
        
        # Tech/service subscriptions
        if any(pattern in subject_lower for pattern in [
            'mcafee', 'norton', 'antivirus', 'vpn', 'siriusxm', 'sirius',
            'spotify', 'netflix', 'hulu', 'subscription', 'renewal'
        ]):
            return 'Service Subscriptions', 0.8
        
        # Political/news clickbait
        if any(name in subject_lower for name in ['trump', 'biden', 'musk', 'putin', 'zelensky']) or \
           any(pattern in subject_lower for pattern in [
               'breaking', 'leaked', 'exposed', 'caught', 'shocking',
               'horrifying', 'bombshell', 'urgent', 'alert'
           ]):
            return 'Political News Spam', 0.75
        
        # === CATEGORY-SPECIFIC CATCH-ALLS ===
        
        if category == 'Dangerous':
            # Look for unicode/special characters typical of dangerous emails
            if re.search(r'[^\x00-\x7F]', subject) or \
               any(char in subject for char in ['➤', '✅', '🚨', '⚠️', '❌', '📢', '🔔']):
                return 'Suspicious Activity', 0.7
            
            # Generic dangerous patterns
            if any(word in subject_lower for word in ['account', 'verify', 'suspend', 'expire', 'update']):
                return 'Phishing Attempts', 0.7
            
            # Catch remaining dangerous
            return 'Potentially Harmful', 0.6
        
        if category == 'Commercial Spam':
            # Newsletter marketing by domain
            marketing_domains = [
                'futureslabresearch.com', 'economicrulebook.com', 'tradesprophet.com',
                'onlineinvestingdaily.com', 'smartearns.com', 'economicage.com',
                'financefreedompath.com', 'wealthinsightsjournal.com', 'vagaro.com',
                'facebookmail.com', 'zappos.com', 'people.com', 'southernliving.com'
            ]
            if domain and any(domain.endswith(d) for d in marketing_domains):
                return 'Newsletter Marketing', 0.75
            
            # Sales/promotions
            if any(word in subject_lower for word in ['sale', 'save', 'discount', 'offer', 'deal', 'free', '%']):
                return 'Sales & Promotions', 0.7
            
            # Generic commercial
            return 'General Marketing', 0.6
        
        if category == 'Legitimate Marketing':
            # E-commerce
            if domain and any(d in domain for d in ['amazon', 'ebay', 'etsy', 'shopify', 'walmart']):
                return 'E-commerce Updates', 0.8
            
            # Social media
            if domain and any(d in domain for d in ['facebook', 'twitter', 'instagram', 'linkedin']):
                return 'Social Media Updates', 0.8
            
            # Generic legitimate
            return 'Business Communications', 0.6
        
        if category == 'Scams':
            # Money/financial scams
            if any(pattern in subject_lower for pattern in ['money', 'cash', 'loan', 'debt', 'credit']):
                return 'Financial Scams', 0.7
            
            # Generic scam
            return 'General Scam', 0.6
        
        # Last resort - tag by sender pattern
        if re.search(r'[0-9]{5,}', sender):  # Sender has long number sequence
            return 'Suspicious Sender', 0.5
        
        return None, 0
    
    def process_untagged_emails(self, batch_size=1000):
        """Process all remaining untagged emails."""
        # First analyze patterns
        self.analyze_remaining_patterns()
        
        print(f"\nStarting final subcategory tagging at {datetime.now()}")
        
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
                
                if subcategory and confidence >= 0.5:  # Very low threshold for maximum coverage
                    updates.append((subcategory, uid))
                    
                    # Update stats
                    self.stats['total_tagged'] += 1
                    self.stats['tags_by_category'][category] = self.stats['tags_by_category'].get(category, 0) + 1
                    self.stats['tags_by_subcategory'][subcategory] = self.stats['tags_by_subcategory'].get(subcategory, 0) + 1
                else:
                    # Track what we're missing
                    if self.stats['total_processed'] < 100:  # Only track first 100
                        self.stats['skipped_patterns'].append({
                            'category': category,
                            'subject': subject[:50],
                            'domain': self.extract_domain(sender)
                        })
                
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
        """Print comprehensive summary statistics."""
        print("\n" + "="*80)
        print("FINAL TAGGING SUMMARY")
        print("="*80)
        print(f"Total emails processed: {self.stats['total_processed']}")
        print(f"Total emails tagged: {self.stats['total_tagged']}")
        print(f"Tagging rate: {self.stats['total_tagged']/self.stats['total_processed']*100:.1f}%")
        
        print("\nTags by category:")
        for cat, count in sorted(self.stats['tags_by_category'].items()):
            print(f"  {cat}: {count}")
        
        print("\nAll subcategories:")
        sorted_subcats = sorted(self.stats['tags_by_subcategory'].items(), key=lambda x: x[1], reverse=True)
        for subcat, count in sorted_subcats:
            print(f"  {subcat}: {count}")
        
        # Show what we couldn't tag
        if self.stats['skipped_patterns']:
            print("\nExamples of untagged emails:")
            for i, pattern in enumerate(self.stats['skipped_patterns'][:10]):
                print(f"  {i+1}. [{pattern['category']}] {pattern['subject']} (domain: {pattern['domain']})")
        
        # Save stats to file
        with open('final_tagging_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=2)
        print("\nStats saved to final_tagging_stats.json")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print("\n" + "="*80)
        print("COMPREHENSIVE TAGGING REPORT")
        print("="*80)
        
        # Overall stats
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN subcategory IS NOT NULL AND subcategory != '' THEN 1 ELSE 0 END) as tagged,
                SUM(CASE WHEN subcategory IS NULL OR subcategory = '' THEN 1 ELSE 0 END) as untagged
            FROM processed_emails_bulletproof
        ''')
        total, tagged, untagged = self.cursor.fetchone()
        
        print(f"OVERALL STATISTICS:")
        print(f"  Total emails in database: {total:,}")
        print(f"  Emails with subcategories: {tagged:,} ({tagged/total*100:.1f}%)")
        print(f"  Emails without subcategories: {untagged:,} ({untagged/total*100:.1f}%)")
        
        # Top subcategories with threat analysis
        print(f"\nTOP 20 SUBCATEGORIES BY VOLUME:")
        self.cursor.execute('''
            SELECT subcategory, COUNT(*) as count, 
                   GROUP_CONCAT(DISTINCT category) as categories
            FROM processed_emails_bulletproof
            WHERE subcategory IS NOT NULL AND subcategory != ''
            GROUP BY subcategory
            ORDER BY count DESC
            LIMIT 20
        ''')
        
        for i, (subcat, count, categories) in enumerate(self.cursor.fetchall(), 1):
            threat_level = self.assess_threat_level(subcat)
            print(f"  {i:2d}. {subcat}: {count:,} emails [{categories}] - Threat: {threat_level}")
    
    def assess_threat_level(self, subcategory):
        """Assess threat level of subcategory."""
        high_threat = ['Phishing Attempts', 'Tech Support Scams', 'Package Delivery Phishing', 
                       'Fake Invoices & Bills', 'Suspicious Activity', 'Potentially Harmful']
        medium_threat = ['Prize & Lottery Scams', 'Cryptocurrency Scams', 'Investment Fraud',
                         'Job Scams', 'Financial Scams', 'Adult Content']
        
        if subcategory in high_threat:
            return "HIGH"
        elif subcategory in medium_threat:
            return "MEDIUM"
        else:
            return "LOW"
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    tagger = FinalSubcategoryTagger()
    
    try:
        # Process all remaining untagged emails
        tagger.process_untagged_emails()
        
        # Generate comprehensive report
        tagger.generate_summary_report()
        
    finally:
        tagger.close()

if __name__ == '__main__':
    main()