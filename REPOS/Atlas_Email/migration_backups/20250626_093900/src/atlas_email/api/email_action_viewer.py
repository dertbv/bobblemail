#!/usr/bin/env python3
"""
BULLETPROOF Email Action Viewer - Shows email processing actions from bulletproof table
Format: Date, Time, Action, Reason, Sender, Subject
"""

import csv
import json
from datetime import datetime
from atlas_email.models.database import db  # Use our main database instead of bulletproof_logger
from atlas_email.utils.general import get_user_choice, clear_screen, show_status_and_refresh

class BulletproofEmailActionViewer:
    """Bulletproof viewer for email processing actions"""
    
    def __init__(self):
        self.page_size = 100
    
    def run(self):
        """Main email action viewer menu"""
        clear_screen()
        while True:
            self._show_main_menu()
            choice = get_user_choice("Press a key (1-5, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            clear_screen()
            if choice == '1':
                self._show_all_actions()
            elif choice == '2':
                self._show_deleted_only()
            elif choice == '3':
                self._show_preserved_only()
            elif choice == '4':
                self._search_actions()
            elif choice == '5':
                self._export_menu()
            
            input("\nPress Enter to continue...")
            clear_screen()
    
    def _show_main_menu(self):
        """Display email action viewer menu"""
        from atlas_email.utils.general import display_application_header
        # Get quick stats
        stats = self._get_action_stats()
        
        display_application_header("📋 EMAIL ACTION VIEWER (BULLETPROOF)")
        
        print(f"\n📊 Total Actions: {stats['total']} | Deleted: {stats['deleted']} | Preserved: {stats['preserved']}")
        print("\n🎯 VIEWER OPTIONS:")
        print("   [1] 📋 All Email Actions")
        print("   [2] 🗑️  Deleted Emails Only")
        print("   [3] 🛡️  Preserved Emails Only")
        print("   [4] 🔍 Search Actions")
        print("   [5] 📤 Export Data")
        print("   [9] 🔙 Return to Main Menu")
    
    def _get_action_stats(self):
        """Get quick statistics from session data"""
        try:
            # Get all recent emails and calculate stats
            all_emails = db.get_session_email_actions(1000)  # Get more for accurate stats
            
            total = len(all_emails)
            deleted = len([e for e in all_emails if e['action'] == 'DELETED'])
            preserved = len([e for e in all_emails if e['action'] == 'PRESERVED'])
            
            return {
                'total': total,
                'deleted': deleted,
                'preserved': preserved
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'total': 0, 'deleted': 0, 'preserved': 0}
    
    def _show_all_actions(self):
        """Show all email actions"""
        print(f"\n📋 ALL EMAIL ACTIONS (Recent {self.page_size})")
        print("=" * 120)
        
        emails = db.get_session_email_actions(self.page_size)
        
        # Sort by timestamp ascending for chronological display
        emails.sort(key=lambda x: x['timestamp'])
        
        self._display_email_actions(emails)
    
    def _show_deleted_only(self):
        """Show deleted emails only"""
        print(f"\n🗑️  DELETED EMAILS (Recent {self.page_size})")
        print("=" * 120)
        
        emails = db.get_session_email_actions(self.page_size, 'DELETED')
        
        # Sort by timestamp ascending for chronological display
        emails.sort(key=lambda x: x['timestamp'])
        
        self._display_email_actions(emails)
    
    def _show_preserved_only(self):
        """Show preserved emails only"""
        print(f"\n🛡️  PRESERVED EMAILS (Recent {self.page_size})")
        print("=" * 120)
        
        emails = db.get_session_email_actions(self.page_size, 'PRESERVED')
        
        # Sort by timestamp ascending for chronological display
        emails.sort(key=lambda x: x['timestamp'])
        
        self._display_email_actions(emails)
    
    def _search_actions(self):
        """Search email actions"""
        print("\n🔍 SEARCH EMAIL ACTIONS")
        print("=" * 50)
        
        search_term = input("Enter search term (sender, subject, or reason): ").strip().lower()
        
        if not search_term:
            print("No search term provided.")
            return
        
        # Get all emails and filter
        all_emails = db.get_session_email_actions(1000)
        
        matching_emails = []
        for email in all_emails:
            if (search_term in str(email.get('sender_email', '')).lower() or
                search_term in str(email.get('subject', '')).lower() or
                search_term in str(email.get('reason', '')).lower() or
                search_term in str(email.get('category', '')).lower()):
                matching_emails.append(email)
        
        print(f"\n🔍 SEARCH RESULTS for '{search_term}' ({len(matching_emails)} found)")
        print("=" * 120)
        
        if matching_emails:
            # Sort by timestamp ascending
            matching_emails.sort(key=lambda x: x['timestamp'])
            self._display_email_actions(matching_emails[:self.page_size])
        else:
            print("No matching emails found.")
    
    def _export_menu(self):
        """Export data menu"""
        print("\n📤 EXPORT EMAIL ACTIONS")
        print("=" * 30)
        print("   [1] Export All Actions (CSV)")
        print("   [2] Export Deleted Only (CSV)")
        print("   [3] Export Preserved Only (CSV)")
        print("   [4] Export All Actions (JSON)")
        
        choice = get_user_choice("Select export option:", ['1', '2', '3', '4'])
        
        if choice == '1':
            self._export_to_csv(db.get_session_email_actions(1000), "all_actions")
        elif choice == '2':
            self._export_to_csv(db.get_session_email_actions(1000, 'DELETED'), "deleted_actions")
        elif choice == '3':
            self._export_to_csv(db.get_session_email_actions(1000, 'PRESERVED'), "preserved_actions")
        elif choice == '4':
            self._export_to_json(db.get_session_email_actions(1000), "all_actions")
    
    def _export_to_csv(self, emails, filename_prefix):
        """Export emails to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'action', 'sender_email', 'subject', 'folder_name', 'reason', 'category']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for email in emails:
                    writer.writerow({
                        'timestamp': email.get('timestamp', ''),
                        'action': email.get('action', ''),
                        'sender_email': email.get('sender_email', ''),
                        'subject': email.get('subject', ''),
                        'folder_name': email.get('folder_name', ''),
                        'reason': email.get('reason', ''),
                        'category': email.get('category', '')
                    })
            
            print(f"✅ Exported {len(emails)} records to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def _export_to_json(self, emails, filename_prefix):
        """Export emails to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(emails, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(emails)} records to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def _display_email_actions(self, emails):
        """Display emails in a formatted table"""
        if not emails:
            print("No email actions found.")
            return
        
        # Header
        print("Date         Time     Action    Reason                    Sender                         Subject                                 ")
        print("-" * 130)
        
        for email in emails:
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(email['timestamp'])
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M:%S")
            except:
                date_str = "Unknown"
                time_str = "Unknown"
            
            # Format fields
            action = (email.get('action') or '')[:8]
            sender = (email.get('sender_email') or '')[:29]
            subject = (email.get('subject') or '')[:39]
            
            # Determine what to show in "Reason" column
            if email.get('action') == 'DELETED':
                # For deleted emails, show the spam category
                reason_display = (email.get('category') or 'Unknown')[:24]
            else:
                # For preserved emails, show preservation reason
                try:
                    preservation_reason = email.get('reason') or ''
                    if 'gmail' in preservation_reason.lower() or 'major email provider' in preservation_reason.lower():
                        reason_display = "Trusted Domain"[:24]
                    elif 'whitelist' in preservation_reason.lower():
                        reason_display = "Whitelisted"[:24]
                    else:
                        reason_display = "Not Spam"[:24]
                except:
                    reason_display = "Not Spam"[:24]
            
            # Action emoji
            action_display = f"🗑️{action}" if action == "DELETED" else f"🛡️{action}"
            
            print(f"{date_str:<12} {time_str:<8} {action_display:<10} {reason_display:<25} {sender:<30} {subject:<40}")
        
        print("-" * 130)
        print(f"Showing {len(emails)} email actions")

def main():
    """Main function for standalone execution"""
    viewer = BulletproofEmailActionViewer()
    viewer.run()

if __name__ == "__main__":
    main()