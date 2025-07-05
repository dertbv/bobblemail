#!/usr/bin/env python3
"""
View detailed subcategory analytics
"""
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def view_analytics(db_path: str):
    """Display comprehensive subcategory analytics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 SPAM INTELLIGENCE DASHBOARD")
    print("=" * 80)
    
    # 1. Overall Statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN subcategory IS NOT NULL THEN 1 END) as tagged,
            COUNT(CASE WHEN threat_level >= 4 THEN 1 END) as high_threat
        FROM processed_emails_bulletproof
        WHERE action = 'DELETED'
    """)
    total, tagged, high_threat = cursor.fetchone()
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Total Spam Emails: {total:,}")
    print(f"   Tagged with Subcategories: {tagged:,} ({tagged/total*100:.1f}%)")
    print(f"   High Threat (4-5): {high_threat:,} ({high_threat/total*100:.1f}%)")
    
    # 2. Threat Level Distribution
    print(f"\n⚠️  THREAT LEVEL DISTRIBUTION:")
    cursor.execute("""
        SELECT threat_level, COUNT(*) as count
        FROM processed_emails_bulletproof
        WHERE threat_level IS NOT NULL
        GROUP BY threat_level
        ORDER BY threat_level DESC
    """)
    
    threat_names = {5: '🔴 Critical', 4: '🟠 High', 3: '🟡 Medium', 2: '🟢 Low', 1: '⚪ Minimal'}
    for level, count in cursor.fetchall():
        bar = '█' * int(count / total * 50)
        print(f"   {threat_names.get(level, f'Level {level}')}: {bar} {count:,}")
    
    # 3. Top Subcategories
    print(f"\n🏷️  TOP 15 SUBCATEGORIES:")
    cursor.execute("""
        SELECT subcategory, COUNT(*) as count, AVG(subcategory_confidence) as avg_conf
        FROM processed_emails_bulletproof
        WHERE subcategory IS NOT NULL
        GROUP BY subcategory
        ORDER BY count DESC
        LIMIT 15
    """)
    
    for i, (subcat, count, avg_conf) in enumerate(cursor.fetchall(), 1):
        print(f"   {i:2}. {subcat}: {count:,} emails (confidence: {avg_conf:.2f})")
    
    # 4. Geographic + Subcategory Analysis
    print(f"\n🌍 GEOGRAPHIC SPECIALIZATION (Top 5 countries):")
    countries = ['US', 'GB', 'RU', 'ZA', 'CN']
    
    for country in countries:
        cursor.execute("""
            SELECT subcategory, COUNT(*) as count
            FROM processed_emails_bulletproof
            WHERE sender_country_code = ? 
            AND subcategory IS NOT NULL
            GROUP BY subcategory
            ORDER BY count DESC
            LIMIT 3
        """, (country,))
        
        results = cursor.fetchall()
        if results:
            print(f"\n   {country}:")
            for subcat, count in results:
                print(f"      → {subcat}: {count:,}")
    
    # 5. High-Threat Categories
    print(f"\n🚨 HIGH-THREAT SUBCATEGORIES (Level 4-5):")
    cursor.execute("""
        SELECT subcategory, COUNT(*) as count, threat_level
        FROM processed_emails_bulletproof
        WHERE threat_level >= 4
        AND subcategory IS NOT NULL
        GROUP BY subcategory, threat_level
        ORDER BY threat_level DESC, count DESC
        LIMIT 10
    """)
    
    for subcat, count, level in cursor.fetchall():
        threat_icon = '🔴' if level == 5 else '🟠'
        print(f"   {threat_icon} {subcat}: {count:,} emails")
    
    # 6. Misclassification Analysis
    print(f"\n❓ POTENTIAL MISCLASSIFICATIONS:")
    
    # Transactional emails marked as deleted
    cursor.execute("""
        SELECT COUNT(*), subcategory
        FROM processed_emails_bulletproof
        WHERE subcategory LIKE '%Transactional%'
        AND action = 'DELETED'
        GROUP BY subcategory
    """)
    for count, subcat in cursor.fetchall():
        print(f"   ⚠️  {count} {subcat} emails were deleted")
    
    # Auto warranty classification
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM processed_emails_bulletproof
        WHERE subject LIKE '%auto%warranty%'
        OR subject LIKE '%vehicle%protection%'
        GROUP BY category
        ORDER BY count DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"\n   🚗 Auto Warranty emails classified as:")
        for cat, count in results:
            print(f"      - {cat}: {count}")
    
    # 7. Trending Analysis (last 7 days)
    print(f"\n📈 TRENDING SUBCATEGORIES (Last 7 days vs Previous 7):")
    
    cursor.execute("""
        WITH recent AS (
            SELECT subcategory, COUNT(*) as recent_count
            FROM processed_emails_bulletproof
            WHERE datetime(timestamp) > datetime('now', '-7 days')
            AND subcategory IS NOT NULL
            GROUP BY subcategory
        ),
        previous AS (
            SELECT subcategory, COUNT(*) as prev_count
            FROM processed_emails_bulletproof
            WHERE datetime(timestamp) BETWEEN datetime('now', '-14 days') AND datetime('now', '-7 days')
            AND subcategory IS NOT NULL
            GROUP BY subcategory
        )
        SELECT 
            r.subcategory,
            r.recent_count,
            COALESCE(p.prev_count, 0) as prev_count,
            CASE 
                WHEN COALESCE(p.prev_count, 0) = 0 THEN 100
                ELSE ((r.recent_count - COALESCE(p.prev_count, 0)) * 100.0 / COALESCE(p.prev_count, 1))
            END as change_pct
        FROM recent r
        LEFT JOIN previous p ON r.subcategory = p.subcategory
        WHERE ABS(change_pct) > 20
        ORDER BY change_pct DESC
        LIMIT 10
    """)
    
    for subcat, recent, prev, change in cursor.fetchall():
        if change > 0:
            print(f"   📈 {subcat}: +{change:.0f}% ({prev} → {recent})")
        else:
            print(f"   📉 {subcat}: {change:.0f}% ({prev} → {recent})")
    
    # 8. Sample High-Threat Emails
    print(f"\n🔍 SAMPLE HIGH-THREAT EMAILS (Level 5):")
    cursor.execute("""
        SELECT sender_email, subject, subcategory
        FROM processed_emails_bulletproof
        WHERE threat_level = 5
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    
    for sender, subject, subcat in cursor.fetchall():
        sender_display = sender[:30] + '...' if len(sender) > 30 else sender
        subject_display = subject[:40] + '...' if subject and len(subject) > 40 else subject or 'No subject'
        print(f"   • {sender_display}")
        print(f"     \"{subject_display}\"")
        print(f"     Category: {subcat}\n")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("💡 Use --export to save detailed analytics to CSV")

def export_analytics(db_path: str, output_file: str):
    """Export detailed analytics to CSV"""
    import csv
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            timestamp, sender_email, sender_domain, subject,
            category, subcategory, threat_level, subcategory_confidence,
            sender_country_code, action
        FROM processed_emails_bulletproof
        WHERE subcategory IS NOT NULL
        ORDER BY timestamp DESC
    """)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Timestamp', 'Sender Email', 'Sender Domain', 'Subject',
            'Primary Category', 'Subcategory', 'Threat Level', 'Confidence',
            'Country', 'Action'
        ])
        
        for row in cursor.fetchall():
            writer.writerow(row)
    
    conn.close()
    print(f"✅ Analytics exported to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View subcategory analytics")
    parser.add_argument('--export', help='Export analytics to CSV file')
    args = parser.parse_args()
    
    db_path = Path(__file__).parent.parent / "data" / "mail_filter.db"
    
    if args.export:
        export_analytics(str(db_path), args.export)
    else:
        view_analytics(str(db_path))