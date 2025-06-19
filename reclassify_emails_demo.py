#!/usr/bin/env python3
"""
Demo Email Reclassification Tool - Command Line Version
======================================================

Demo version that takes category as command line argument for testing.
Usage: python3 reclassify_emails_demo.py "Phishing"
"""

import sqlite3
from keyword_processor import KeywordProcessor
import sys
import os
from datetime import datetime

def analyze_reclassification(target_category):
    """Analyze what emails would be reclassified to target category"""
    
    # Initialize the EXACT same classifier used in production (suppress debug output)
    print(f"🤖 Initializing PRODUCTION classifier (KeywordProcessor)...")
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    keyword_processor = KeywordProcessor()
    sys.stdout.close()
    sys.stdout = old_stdout
    
    # Connect to database
    conn = sqlite3.connect('mail_filter.db')
    cursor = conn.cursor()
    
    # Get all emails with their current classifications
    cursor.execute("""
        SELECT id, sender_email, subject, category, action, confidence_score
        FROM processed_emails_bulletproof 
        ORDER BY id DESC
    """)
    
    emails = cursor.fetchall()
    print(f"📊 Analyzing {len(emails)} emails for reclassification to '{target_category}'...")
    
    # Track candidates
    reclassification_candidates = []
    category_changes = {}
    
    # Process each email with EXACT production method
    for i, (email_id, sender, subject, current_category, current_action, confidence) in enumerate(emails):
        if i % 500 == 0:
            print(f"Progress: {i}/{len(emails)} ({i/len(emails)*100:.1f}%)")
        
        try:
            # Use the EXACT same method call as production (suppress output)
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            new_category = keyword_processor.process_keywords(
                headers="",  # Production uses empty string
                sender=sender,
                subject=subject
            )
            sys.stdout.close()
            sys.stdout = old_stdout
            
            # Check if this email would be reclassified to target category
            if new_category == target_category and current_category != target_category:
                candidate_info = {
                    'id': email_id,
                    'sender': sender,
                    'subject': subject[:60] + "..." if len(subject) > 60 else subject,
                    'old_category': current_category,
                    'new_category': new_category,
                    'action': current_action
                }
                reclassification_candidates.append(candidate_info)
                
                # Track change pattern
                change_key = f"{current_category} → {new_category}"
                category_changes[change_key] = category_changes.get(change_key, 0) + 1
        
        except Exception as e:
            continue
    
    conn.close()
    
    return reclassification_candidates, category_changes

def show_preview(candidates, target_category):
    """Show preview of reclassification changes"""
    
    print("\n" + "="*80)
    print(f"📋 RECLASSIFICATION PREVIEW - TARGET: {target_category}")
    print("="*80)
    
    if not candidates:
        print(f"✅ NO EMAILS FOUND that would be reclassified to '{target_category}'")
        print("All emails are already correctly classified by the production system.")
        return False
    
    print(f"\n📊 SUMMARY:")
    print(f"  Found {len(candidates)} emails that would be reclassified to '{target_category}'")
    
    # Group by old category
    by_old_category = {}
    for candidate in candidates:
        old_cat = candidate['old_category']
        if old_cat not in by_old_category:
            by_old_category[old_cat] = []
        by_old_category[old_cat].append(candidate)
    
    print(f"\n📈 BREAKDOWN BY CURRENT CATEGORY:")
    for old_category, items in sorted(by_old_category.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {old_category} → {target_category}: {len(items)} emails")
    
    print(f"\n📧 SAMPLE EMAILS (first 10):")
    print("-" * 80)
    for i, candidate in enumerate(candidates[:10]):
        print(f"  {i+1}. ID: {candidate['id']}")
        print(f"     From: {candidate['sender']}")
        print(f"     Subject: {candidate['subject']}")
        print(f"     Change: {candidate['old_category']} → {candidate['new_category']}")
        print(f"     Current Action: {candidate['action']}")
        print()
    
    if len(candidates) > 10:
        print(f"     ... and {len(candidates) - 10} more emails")
    
    print(f"\n⚠️  DEMO MODE - NO CHANGES WILL BE MADE")
    print(f"To actually update the database, use the interactive version:")
    print(f"python3 reclassify_emails_interactive.py")
    
    return True

def main():
    """Main demo workflow"""
    
    if len(sys.argv) != 2:
        print("🔄 DEMO EMAIL RECLASSIFICATION TOOL")
        print("=" * 40)
        print("Usage: python3 reclassify_emails_demo.py \"Category Name\"")
        print()
        print("📋 Available Categories:")
        print("  - Phishing")
        print("  - Financial & Investment Spam")
        print("  - Marketing Spam")
        print("  - Payment Scam")
        print("  - Brand Impersonation")
        print("  - etc...")
        print()
        print("Example: python3 reclassify_emails_demo.py \"Phishing\"")
        sys.exit(1)
    
    target_category = sys.argv[1]
    
    print("🔄 DEMO EMAIL RECLASSIFICATION TOOL")
    print("=" * 40)
    print(f"🎯 Target category: '{target_category}'")
    print("📝 DEMO MODE - Analysis only, no database changes")
    print()
    
    # Analyze reclassification
    candidates, changes = analyze_reclassification(target_category)
    
    # Show preview
    show_preview(candidates, target_category)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)