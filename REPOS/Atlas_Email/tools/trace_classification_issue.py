#!/usr/bin/env python3
"""Trace the classification issue for specific emails"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from atlas_email.models.database import DatabaseManager

def trace_issue():
    """Trace why emails are getting Error category"""
    db = DatabaseManager()
    
    # Find these specific emails
    test_subjects = [
        "%Trump%infrastructure%",
        "%Horrifying%Laser%",
        "%Payment-Declined%"
    ]
    
    print("🔍 Tracing classification issues...\n")
    
    for subject_pattern in test_subjects:
        emails = db.get_processed_emails_by_pattern(
            subject_pattern=subject_pattern,
            limit=5
        )
        
        for email in emails:
            print(f"📧 UID: {email['uid']}")
            print(f"   Subject: {email['subject'][:60]}...")
            print(f"   Sender: {email['sender_email']}")
            print(f"   Category: {email['category']}")
            print(f"   Action: {email['action']}")
            print(f"   Reason: {email.get('reason', 'N/A')}")
            print(f"   Account: {email.get('account_id', 'N/A')}")
            print(f"   Folder: {email.get('folder_name', 'N/A')}")
            print(f"   Timestamp: {email['created_at']}")
            print()

if __name__ == "__main__":
    trace_issue()