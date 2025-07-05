#!/usr/bin/env python3
"""
Fix Category Misclassifications
Moves emails from Legitimate Marketing to their correct categories based on subcategory
"""

import sqlite3
import os

def fix_misclassifications():
    """Move misclassified emails to correct categories based on subcategory"""
    # Connect directly to database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mail_filter.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Define mappings from subcategory to correct category
    subcategory_fixes = {
        # Scams that should be in "Scams" category
        'Prize & Lottery Scams': 'Scams',
        'Tech Support Scams': 'Scams',
        'Investment Fraud': 'Scams',
        'Cryptocurrency Scams': 'Scams',
        
        # Commercial spam that should be in "Commercial Spam" category  
        'Health & Pharma Spam': 'Commercial Spam',
        'Adult Content': 'Commercial Spam',
        'Auto Warranty & Insurance': 'Commercial Spam',
        'Political News Spam': 'Commercial Spam',
    }
    
    print("🔧 Fixing category misclassifications...")
    
    total_fixed = 0
    cursor = conn.cursor()
    
    for subcategory, correct_category in subcategory_fixes.items():
        # Count affected emails
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM processed_emails_bulletproof 
            WHERE category = 'Legitimate Marketing' 
            AND subcategory = ?
        """, (subcategory,))
        
        count = cursor.fetchone()['count']
        
        if count > 0:
            print(f"\n📋 Moving {count} emails with subcategory '{subcategory}'")
            print(f"   From: Legitimate Marketing → To: {correct_category}")
            
            # Update the category
            cursor.execute("""
                UPDATE processed_emails_bulletproof 
                SET category = ?
                WHERE category = 'Legitimate Marketing' 
                AND subcategory = ?
            """, (correct_category, subcategory))
            
            conn.commit()
            total_fixed += count
            print(f"   ✅ Updated {count} emails")
    
    # Show summary
    print(f"\n🎯 Total emails reclassified: {total_fixed}")
    
    # Show updated category counts
    print("\n📊 Updated category distribution:")
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM processed_emails_bulletproof 
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY category 
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        print(f"   {row['category']}: {row['count']:,}")
    
    # Show remaining subcategories in Legitimate Marketing
    print("\n📋 Remaining subcategories in Legitimate Marketing:")
    cursor.execute("""
        SELECT subcategory, COUNT(*) as count 
        FROM processed_emails_bulletproof 
        WHERE category = 'Legitimate Marketing' 
        AND subcategory IS NOT NULL
        GROUP BY subcategory 
        ORDER BY count DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"   {row['subcategory']}: {row['count']:,}")
    
    conn.close()

if __name__ == "__main__":
    fix_misclassifications()