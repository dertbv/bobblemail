#!/usr/bin/env python3
"""
Update main database with geographic data from sandbox database
"""
import sqlite3

# Database paths
main_db = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db"
sandbox_db = "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter_sandbox.db"

# Connect to both databases
main_conn = sqlite3.connect(main_db)
sandbox_conn = sqlite3.connect(sandbox_db)

try:
    # Get geographic data from sandbox
    sandbox_cursor = sandbox_conn.cursor()
    sandbox_cursor.execute("""
        SELECT id, sender_country_code, geographic_risk_score, detection_method
        FROM processed_emails_bulletproof
        WHERE sender_country_code IS NOT NULL
    """)
    
    updates = sandbox_cursor.fetchall()
    print(f"Found {len(updates)} emails with geographic data in sandbox")
    
    # Update main database
    main_cursor = main_conn.cursor()
    updated = 0
    
    for email_id, country_code, risk_score, detection_method in updates:
        main_cursor.execute("""
            UPDATE processed_emails_bulletproof
            SET sender_country_code = ?, 
                geographic_risk_score = ?,
                detection_method = ?
            WHERE id = ?
        """, (country_code, risk_score, detection_method, email_id))
        updated += main_cursor.rowcount
    
    main_conn.commit()
    print(f"Updated {updated} emails in main database")
    
    # Verify the update
    main_cursor.execute("""
        SELECT COUNT(*) as total, 
               COUNT(sender_country_code) as with_geo
        FROM processed_emails_bulletproof
    """)
    total, with_geo = main_cursor.fetchone()
    print(f"\nMain database now has {with_geo}/{total} emails with geographic data")
    print(f"Coverage: {with_geo/total*100:.1f}%")

finally:
    main_conn.close()
    sandbox_conn.close()