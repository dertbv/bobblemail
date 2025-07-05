#!/usr/bin/env python3
"""
Fix "General X" subcategories by removing redundant prefix
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "data" / "mail_filter.db"

def fix_general_subcategories():
    """Remove 'General' prefix from subcategories that just repeat the category."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Find all the "General X" subcategories
    cursor.execute("""
        SELECT DISTINCT category, subcategory 
        FROM processed_emails_bulletproof 
        WHERE subcategory LIKE 'General %'
    """)
    
    updates = []
    for category, subcategory in cursor.fetchall():
        # If subcategory is just "General [Category]", clear it
        if subcategory == f"General {category}":
            updates.append(category)
    
    print(f"Found {len(updates)} categories with redundant 'General' prefix")
    
    # Update each one
    for category in updates:
        cursor.execute("""
            UPDATE processed_emails_bulletproof 
            SET subcategory = '' 
            WHERE category = ? AND subcategory = ?
        """, (category, f"General {category}"))
        
        count = cursor.rowcount
        print(f"  Fixed {count:,} emails in category '{category}'")
    
    # Show remaining subcategories
    cursor.execute("""
        SELECT subcategory, COUNT(*) as count 
        FROM processed_emails_bulletproof 
        WHERE subcategory != '' 
        GROUP BY subcategory 
        ORDER BY count DESC
        LIMIT 20
    """)
    
    print("\n📊 Remaining subcategories:")
    for subcat, count in cursor.fetchall():
        print(f"  {subcat}: {count:,}")
    
    conn.commit()
    conn.close()
    print("\n✅ Subcategory cleanup complete!")

if __name__ == "__main__":
    fix_general_subcategories()