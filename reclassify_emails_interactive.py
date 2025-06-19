#!/usr/bin/env python3
"""
Interactive Email Reclassification Tool
=====================================

Uses the EXACT production classifier to:
1. Ask user for target category
2. Find all emails that would be reclassified to that category
3. Show preview of changes
4. Actually update the database with new classifications

Uses the same KeywordProcessor.process_keywords() method as production email_processor.py
"""

import sqlite3
from keyword_processor import KeywordProcessor
import sys
import os
from datetime import datetime

def get_user_input():
    """Get target category from user with numbered choices"""
    categories = [
        "Phishing",
        "Financial & Investment Spam",
        "Gambling Spam",
        "Health & Medical Spam",
        "Adult & Dating Spam",
        "Business Opportunity Spam",
        "Brand Impersonation",
        "Payment Scam",
        "Education/Training Spam",
        "Real Estate Spam",
        "Legal & Compensation Scams",
        "Marketing Spam",
        "Promotional Email",
        "Legitimate",
        "Generic Spam"
    ]
    
    print("📋 Available Categories:")
    for i, category in enumerate(categories, 1):
        print(f"  {i:2d}. {category}")
    print()
    
    while True:
        try:
            choice = input("🎯 Enter the number of the category you want to reclassify emails TO: ").strip()
            
            if not choice:
                print("❌ No choice entered. Exiting.")
                sys.exit(1)
            
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(categories):
                selected_category = categories[choice_num - 1]
                print(f"✅ Selected: {selected_category}")
                return selected_category
            else:
                print(f"❌ Invalid choice. Please enter a number between 1 and {len(categories)}")
                
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

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
    
    return True

def confirm_changes(candidates, target_category):
    """Ask user to confirm the changes"""
    print(f"\n⚠️  CONFIRMATION REQUIRED")
    print(f"Are you sure you want to reclassify {len(candidates)} emails to '{target_category}'?")
    print("This will permanently update the database.")
    print()
    
    while True:
        choice = input("Enter 'yes' to proceed, 'no' to cancel: ").strip().lower()
        if choice in ['yes', 'y']:
            return True
        elif choice in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def apply_reclassification(candidates, target_category):
    """Apply the reclassification to database"""
    
    print(f"\n🔄 Applying reclassification to {len(candidates)} emails...")
    
    conn = sqlite3.connect('mail_filter.db')
    cursor = conn.cursor()
    
    updated_count = 0
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        for candidate in candidates:
            cursor.execute("""
                UPDATE processed_emails_bulletproof 
                SET category = ?, 
                    confidence_score = 1.0,
                    timestamp = ?
                WHERE id = ?
            """, (target_category, timestamp, candidate['id']))
            
            if cursor.rowcount > 0:
                updated_count += 1
        
        conn.commit()
        print(f"✅ Successfully updated {updated_count} emails to category '{target_category}'")
        
        # Show summary
        print(f"\n📊 RECLASSIFICATION COMPLETE:")
        print(f"  Target Category: {target_category}")
        print(f"  Emails Updated: {updated_count}")
        print(f"  Timestamp: {timestamp}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during update: {e}")
        return False
    finally:
        conn.close()
    
    return True

def main():
    """Main interactive reclassification workflow"""
    
    print("🔄 INTERACTIVE EMAIL RECLASSIFICATION TOOL")
    print("=" * 50)
    print("Uses the EXACT production classifier to reclassify emails")
    print()
    
    # Step 1: Get target category
    target_category = get_user_input()
    print(f"🎯 Target category: '{target_category}'")
    print()
    
    # Step 2: Analyze reclassification
    candidates, changes = analyze_reclassification(target_category)
    
    # Step 3: Show preview
    has_changes = show_preview(candidates, target_category)
    
    if not has_changes:
        print("\n👍 No changes needed. Exiting.")
        return
    
    # Step 4: Confirm changes
    if not confirm_changes(candidates, target_category):
        print("\n❌ Cancelled by user. No changes made.")
        return
    
    # Step 5: Apply changes
    success = apply_reclassification(candidates, target_category)
    
    if success:
        print(f"\n🎉 Reclassification to '{target_category}' completed successfully!")
    else:
        print(f"\n💥 Reclassification failed. Please check the error messages above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. No changes made.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)