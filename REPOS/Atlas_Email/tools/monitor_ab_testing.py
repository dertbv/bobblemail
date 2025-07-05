#!/usr/bin/env python3
"""
Monitor A/B Testing Results
"""

import sys
import sqlite3
from pathlib import Path
from collections import defaultdict

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from atlas_email.models.database import DB_FILE

def monitor_ab_results():
    """Display A/B testing results and statistics."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if A/B testing table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ab_testing_results'
        """)
        
        if not cursor.fetchone():
            print("❌ No A/B testing results found. The table hasn't been created yet.")
            print("   Process some emails with A/B testing enabled to see results.")
            return
        
        # Get overall stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN selected_classifier = 'new' THEN 1 ELSE 0 END) as new_classifier_count,
                SUM(CASE WHEN categories_match = 1 THEN 1 ELSE 0 END) as matches,
                AVG(processing_time_old) as avg_old_time,
                AVG(processing_time_new) as avg_new_time
            FROM ab_testing_results
        """)
        
        row = cursor.fetchone()
        if row and row[0] > 0:
            total, new_count, matches, avg_old_time, avg_new_time = row
            old_count = total - new_count
            match_rate = (matches / total * 100) if total > 0 else 0
            
            print("📊 A/B Testing Statistics:")
            print(f"   Total emails tested: {total}")
            print(f"   Old classifier used: {old_count} ({old_count/total*100:.1f}%)")
            print(f"   New classifier used: {new_count} ({new_count/total*100:.1f}%)")
            print(f"   Category match rate: {match_rate:.1f}%")
            print(f"   Avg processing time (old): {avg_old_time:.1f}ms")
            print(f"   Avg processing time (new): {avg_new_time:.1f}ms")
            
            # Get category differences
            cursor.execute("""
                SELECT 
                    old_category,
                    new_category,
                    COUNT(*) as count
                FROM ab_testing_results
                WHERE categories_match = 0
                GROUP BY old_category, new_category
                ORDER BY count DESC
                LIMIT 10
            """)
            
            differences = cursor.fetchall()
            if differences:
                print("\n🔄 Top Category Differences:")
                for old_cat, new_cat, count in differences:
                    print(f"   {old_cat} → {new_cat}: {count} times")
            
            # Show some example classifications
            cursor.execute("""
                SELECT 
                    subject,
                    sender,
                    old_category,
                    new_category,
                    new_subcategory,
                    selected_classifier
                FROM ab_testing_results
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            examples = cursor.fetchall()
            if examples:
                print("\n📧 Recent Classifications:")
                for subject, sender, old_cat, new_cat, subcategory, selected in examples:
                    print(f"\n   Subject: {subject[:60]}...")
                    print(f"   From: {sender}")
                    print(f"   Old: {old_cat}")
                    print(f"   New: {new_cat} ({subcategory or 'No subcategory'})")
                    print(f"   Used: {selected} classifier")
        else:
            print("📊 No A/B testing results recorded yet.")
            
    except Exception as e:
        print(f"❌ Error reading A/B testing results: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    monitor_ab_results()