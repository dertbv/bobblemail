#!/usr/bin/env python3
"""
Tag existing emails with subcategories for detailed analytics
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlite3
from atlas_email.ml.subcategory_tagger import SubcategoryTagger, create_database_schema
from collections import Counter, defaultdict
import json

def tag_all_emails(db_path: str, limit: int = None):
    """Tag all existing emails with subcategories"""
    
    # Ensure schema exists
    print("📋 Creating database schema...")
    create_database_schema(db_path)
    
    # Initialize tagger
    print("🏷️  Initializing subcategory tagger...")
    tagger = SubcategoryTagger(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get emails to tag
    query = """
        SELECT id, sender_email, sender_domain, subject, category, 
               action, raw_data
        FROM processed_emails_bulletproof
        WHERE action = 'DELETED'
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    emails = cursor.fetchall()
    print(f"\n📧 Found {len(emails)} emails to tag")
    
    # Statistics
    stats = {
        'total': len(emails),
        'tagged': 0,
        'by_primary': defaultdict(int),
        'by_subcategory': Counter(),
        'by_threat_level': Counter(),
        'high_confidence': 0,
        'examples': defaultdict(list)
    }
    
    # Tag each email
    print("\n🔄 Tagging emails...")
    for i, email in enumerate(emails):
        if i % 100 == 0:
            print(f"   Progress: {i}/{len(emails)} ({i/len(emails)*100:.1f}%)")
        
        email_data = {
            'subject': email['subject'],
            'sender_email': email['sender_email'],
            'sender_domain': email['sender_domain'],
            'raw_data': email['raw_data']
        }
        
        # Get primary category (use existing category)
        primary = email['category'] or 'Unknown'
        
        # Tag with subcategory
        subcategory, confidence, match_details = tagger.tag_email(email_data, primary)
        threat_level = tagger.get_threat_level(primary, subcategory)
        
        # Update database
        cursor.execute("""
            UPDATE processed_emails_bulletproof
            SET primary_category = ?,
                subcategory = ?,
                threat_level = ?,
                subcategory_confidence = ?
            WHERE id = ?
        """, (primary, subcategory, threat_level, confidence, email['id']))
        
        # Update statistics
        stats['tagged'] += 1
        stats['by_primary'][primary] += 1
        stats['by_subcategory'][subcategory] += 1
        stats['by_threat_level'][threat_level] += 1
        
        if confidence > 0.7:
            stats['high_confidence'] += 1
        
        # Collect examples
        if len(stats['examples'][subcategory]) < 3:
            stats['examples'][subcategory].append({
                'subject': email['subject'][:60] + '...' if len(email['subject'] or '') > 60 else email['subject'],
                'sender': email['sender_email'],
                'confidence': confidence
            })
    
    # Commit changes
    conn.commit()
    
    # Print results
    print(f"\n✅ Successfully tagged {stats['tagged']} emails!")
    
    print("\n📊 SUBCATEGORY DISTRIBUTION:")
    for subcat, count in stats['by_subcategory'].most_common(20):
        percentage = count / stats['total'] * 100
        print(f"   {subcat}: {count} ({percentage:.1f}%)")
    
    print("\n⚠️  THREAT LEVEL DISTRIBUTION:")
    for level in sorted(stats['by_threat_level'].keys()):
        count = stats['by_threat_level'][level]
        percentage = count / stats['total'] * 100
        threat_name = ['', 'Low', 'Medium', 'High', 'Critical', 'Extreme'][level]
        print(f"   Level {level} ({threat_name}): {count} ({percentage:.1f}%)")
    
    print(f"\n🎯 High confidence tags (>70%): {stats['high_confidence']} ({stats['high_confidence']/stats['total']*100:.1f}%)")
    
    # Show some examples
    print("\n📝 SUBCATEGORY EXAMPLES:")
    for subcat in list(stats['by_subcategory'].keys())[:10]:
        if subcat in stats['examples']:
            print(f"\n{subcat}:")
            for ex in stats['examples'][subcat]:
                print(f"   - {ex['subject']}")
                print(f"     From: {ex['sender']} (confidence: {ex['confidence']:.2f})")
    
    # Analyze misclassifications
    print("\n🤔 INTERESTING FINDINGS:")
    
    # Find auto warranty emails
    cursor.execute("""
        SELECT COUNT(*) 
        FROM processed_emails_bulletproof 
        WHERE subcategory = 'Financial - Auto Warranty'
    """)
    auto_warranty_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM processed_emails_bulletproof 
        WHERE subcategory = 'Financial - Auto Warranty'
        GROUP BY category
        ORDER BY count DESC
        LIMIT 5
    """)
    
    print(f"\n🚗 Auto Warranty emails ({auto_warranty_count} total) were classified as:")
    for cat, count in cursor.fetchall():
        print(f"   - {cat}: {count}")
    
    # Find potential false positives
    cursor.execute("""
        SELECT COUNT(*) 
        FROM processed_emails_bulletproof 
        WHERE threat_level = 1 
        AND action = 'DELETED'
        AND subcategory LIKE '%Transactional%'
    """)
    potential_false_positives = cursor.fetchone()[0]
    print(f"\n⚠️  Potential false positives (low threat but deleted): {potential_false_positives}")
    
    conn.close()

def analyze_patterns(db_path: str):
    """Analyze pattern effectiveness"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📈 PATTERN EFFECTIVENESS:")
    
    # Most effective subcategories
    cursor.execute("""
        SELECT subcategory, 
               COUNT(*) as matches,
               AVG(subcategory_confidence) as avg_confidence
        FROM processed_emails_bulletproof
        WHERE subcategory IS NOT NULL
        GROUP BY subcategory
        HAVING matches > 10
        ORDER BY avg_confidence DESC
        LIMIT 10
    """)
    
    print("\nMost confident subcategory matches:")
    for subcat, matches, avg_conf in cursor.fetchall():
        print(f"   {subcat}: {matches} matches (avg confidence: {avg_conf:.2f})")
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tag emails with subcategories")
    parser.add_argument('--limit', type=int, help='Limit number of emails to tag')
    parser.add_argument('--analyze', action='store_true', help='Analyze pattern effectiveness')
    args = parser.parse_args()
    
    db_path = Path(__file__).parent.parent / "data" / "mail_filter.db"
    
    if args.analyze:
        analyze_patterns(str(db_path))
    else:
        tag_all_emails(str(db_path), limit=args.limit)
        analyze_patterns(str(db_path))