#!/usr/bin/env python3
"""
Re-classify ALL Existing Emails with 4-Category System - Fixed Version
======================================================================
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import time

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from atlas_email.ml.four_category_classifier import FourCategoryClassifier
from atlas_email.ml.subcategory_tagger import SubcategoryTagger
from atlas_email.models.database import DB_FILE

def reclassify_all_emails():
    """Re-classify all emails with the new 4-category system."""
    print("🚀 Starting email re-classification with 4-category system...")
    print(f"📊 Database: {DB_FILE}")
    
    # Initialize classifiers
    classifier = FourCategoryClassifier(DB_FILE)
    try:
        classifier.load_model()
        print("✅ Loaded trained 4-category classifier")
    except Exception as e:
        print(f"❌ Error loading classifier: {e}")
        return
        
    subcategory_tagger = SubcategoryTagger(DB_FILE)
    
    # Connect to database
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all emails at once
    print("📥 Loading all emails from database...")
    cursor.execute("""
        SELECT uid, sender_email, subject, category, confidence_score, subcategory
        FROM processed_emails_bulletproof
        ORDER BY id
    """)
    
    all_emails = cursor.fetchall()
    total_count = len(all_emails)
    print(f"📧 Total emails to process: {total_count:,}")
    
    # Category statistics
    old_categories = {}
    new_categories = {}
    category_changes = []
    processed = 0
    errors = 0
    
    print("\n⏳ Processing emails...")
    start_time = time.time()
    
    # Process all emails
    for row in all_emails:
        uid = row['uid']
        sender = row['sender_email']
        subject = row['subject']
        old_category = row['category']
        old_confidence = row['confidence_score']
        old_subcategory = row['subcategory']
        
        # Track old categories
        old_categories[old_category] = old_categories.get(old_category, 0) + 1
        
        try:
            # Classify with new system
            result = classifier.classify(sender, subject)
            new_category = result['category']
            new_confidence = result['confidence'] * 100  # Convert to percentage
            
            # Get subcategory
            subcategory_result = subcategory_tagger.tag_email(
                sender=sender,
                subject=subject,
                category=new_category
            )
            new_subcategory = subcategory_result.get('subcategory', '')
            subcategory_confidence = subcategory_result.get('confidence', 0.0)
            
            # Track new categories
            new_categories[new_category] = new_categories.get(new_category, 0) + 1
            
            # Track changes
            if old_category != new_category:
                category_changes.append({
                    'uid': uid,
                    'old': old_category,
                    'new': new_category,
                    'subject': subject[:50] if subject else ''
                })
            
            # Update database
            cursor.execute("""
                UPDATE processed_emails_bulletproof 
                SET category = ?, 
                    confidence_score = ?,
                    subcategory = ?,
                    subcategory_confidence = ?
                WHERE uid = ?
            """, (new_category, new_confidence, new_subcategory, 
                  subcategory_confidence, uid))
            
            processed += 1
            
            # Progress update every 500 emails
            if processed % 500 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed
                remaining = (total_count - processed) / rate
                print(f"   Processed: {processed:,}/{total_count:,} ({processed/total_count*100:.1f}%) "
                      f"| Rate: {rate:.0f}/sec | ETA: {remaining/60:.1f} min")
                # Commit periodically
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error processing UID {uid}: {e}")
            errors += 1
    
    # Final commit
    conn.commit()
    
    # Final statistics
    elapsed_total = time.time() - start_time
    print(f"\n✅ Re-classification complete!")
    print(f"   Total processed: {processed:,}")
    print(f"   Errors: {errors}")
    print(f"   Time taken: {elapsed_total/60:.1f} minutes")
    print(f"   Average rate: {processed/elapsed_total:.0f} emails/second")
    
    # Show category distribution changes
    print(f"\n📊 Category Distribution Changes:")
    print(f"{'Old Category':<30} {'Count':>10}")
    print("-" * 42)
    for cat, count in sorted(old_categories.items(), key=lambda x: x[1], reverse=True):
        print(f"{cat:<30} {count:>10,}")
    
    print(f"\n{'New Category':<30} {'Count':>10}")
    print("-" * 42)
    for cat, count in sorted(new_categories.items(), key=lambda x: x[1], reverse=True):
        print(f"{cat:<30} {count:>10,}")
    
    # Show percentage breakdown
    print(f"\n📊 New Category Percentages:")
    for cat, count in sorted(new_categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"   {cat}: {percentage:.1f}% ({count:,} emails)")
    
    # Show some examples of changes
    if category_changes:
        print(f"\n🔄 Example Category Changes (showing first 20):")
        for i, change in enumerate(category_changes[:20]):
            print(f"   {change['old']} → {change['new']}: {change['subject']}...")
    
    print(f"\n📈 Summary:")
    print(f"   Total emails: {total_count:,}")
    print(f"   Successfully processed: {processed:,}")
    print(f"   Category changes: {len(category_changes):,} ({len(category_changes)/processed*100:.1f}%)")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    print("🔍 4-Category Email Re-classifier")
    print("=" * 60)
    print("\nThis will update ALL emails in your database with the new")
    print("4-category classification system.")
    print("\nCategories: Dangerous, Commercial Spam, Scams, Legitimate Marketing")
    print("\n⚠️  This will process ALL {:,} emails!".format(6999))
    print("\n🚀 Starting re-classification...")
    reclassify_all_emails()