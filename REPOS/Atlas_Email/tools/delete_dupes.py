#!/usr/bin/env python3
import sqlite3
import shutil

# Backup first
shutil.copy2("/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db", 
             "/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter_backup.db")

conn = sqlite3.connect("/Users/Badman/Desktop/email/REPOS/Atlas_Email/data/mail_filter.db")
cursor = conn.cursor()

cursor.execute("""
    DELETE FROM processed_emails_bulletproof
    WHERE rowid NOT IN (
        SELECT MAX(rowid)
        FROM processed_emails_bulletproof
        WHERE uid IS NOT NULL AND uid != ''
        GROUP BY uid, folder_name
    )
    AND uid IS NOT NULL AND uid != ''
""")

print(f"Deleted {cursor.rowcount} duplicates")
conn.commit()
conn.close()