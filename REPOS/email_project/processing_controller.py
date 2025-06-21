"""
Processing Controller Module - Extracted from main.py
Handles all email processing, batch operations, and core business logic
"""

import json
from datetime import datetime
from collections import defaultdict

# Import database modules
from database import db
from db_logger import logger, write_log, LogCategory
from db_credentials import db_credentials
from db_analytics import DatabaseAnalyticsMenu
from email_action_viewer import BulletproofEmailActionViewer

# Import original modules
from config_auth import IMAPConnectionManager
from email_processor import EmailProcessor, FolderManager, BatchProcessor
from domain_validator import DomainValidator
from utils import get_user_choice as get_single_choice, clear_screen


def batch_processing_for_timer():
    """Batch processing function for timer (returns success boolean)"""
    try:
        logger.info("=== Automated Batch Processing Started ===", 
                   category=LogCategory.SYSTEM)
        
        # Run the same batch processing logic
        result = batch_processing()
        
        logger.info("=== Automated Batch Processing Completed ===", 
                   category=LogCategory.SYSTEM)
        
        return result if result is not None else True
        
    except Exception as e:
        logger.error(e, "automated_batch_processing")
        return False


def run_preview_for_account(account_id, debug_mode=False, preview_mode=True):
    """Run processing for a specific account - callable from web interface"""
    try:
        # Load account from database using array index (matching web interface)
        accounts = db_credentials.load_credentials()
        if account_id >= len(accounts):
            return {"success": False, "message": f"Account index {account_id} not found"}
        
        account = accounts[account_id]
        
        # Initialize connection manager
        connection_manager = IMAPConnectionManager(db_credentials)
        
        # Connect to account using correct method
        mail = connection_manager.connect_to_imap(account=account)
        if not mail:
            return {"success": False, "message": "Failed to connect to email account"}
        
        try:
            # Initialize processors
            processor = EmailProcessor(mail, account_email=account['email_address'], account_id=account['id'])
            domain_validator = DomainValidator()
            
            # Get filters (empty list is OK - system uses database spam detection)
            from configuration_manager import get_filters
            filters = get_filters()
            # Note: Empty filters list is valid - system uses database-driven spam detection
            
            # Get target folders from account
            target_folders = account.get('target_folders', [])
            if not target_folders:
                connection_manager.disconnect()
                return {"success": False, "message": "No folders configured for this account"}
            
            # Create session in database
            session_type = 'web_preview' if preview_mode else 'web_process'
            session_id = db.execute_insert("""
                INSERT INTO sessions (account_id, session_type, is_preview)
                VALUES (?, ?, ?)
            """, (account['id'], session_type, preview_mode))
            
            # Set logger session context
            logger.set_session_context(session_id, account['id'])
            logger.log_session_start(account['email_address'], account['id'], session_id)
            
            total_deleted = 0
            total_preserved = 0
            total_validated = 0
            all_categories = defaultdict(int)
            
            # Process each target folder (like CLI does)
            for folder_name in target_folders:
                print(f"🔍 Processing folder: {folder_name}")
                
                # Process folder with specified mode
                deleted, _, preserved, validated, legitimate, categories = processor.process_folder_messages_with_new_architecture(
                    folder_name, filters, domain_validator, auto_confirm=True, preview_mode=preview_mode, debug_mode=False
                )
                
                # Update totals
                total_deleted += deleted
                total_preserved += preserved
                total_validated += validated
                
                # Track categories
                for category, data in categories.items():
                    all_categories[category] += data['count']
            
            # End session logging
            logger.log_session_end(total_deleted, total_preserved, total_validated, 0)
            
            connection_manager.disconnect()
            
            return {
                "success": True,
                "account_email": account['email_address'],
                "session_id": session_id,
                "total_deleted": total_deleted,
                "total_preserved": total_preserved,
                "total_validated": total_validated,
                "categories": dict(all_categories),
                "folders_processed": target_folders,
                "message": f"{'Preview' if preview_mode else 'Processing'} complete: {total_deleted} {'to delete' if preview_mode else 'deleted'}, {total_preserved} {'to preserve' if preview_mode else 'preserved'}"
            }
            
        finally:
            connection_manager.disconnect()
            
    except Exception as e:
        print(f"❌ Preview error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error running preview: {str(e)}"}


def run_exact_cli_processing_for_account(account_id, preview_mode=False):
    """Run processing using EXACT CLI flow - for web interface to call exact CLI deletion path"""
    try:
        # Load account from database using array index (matching web interface)
        accounts = db_credentials.load_credentials()
        if account_id >= len(accounts):
            return {"success": False, "message": f"Account index {account_id} not found"}
        
        account = accounts[account_id]
        account_email = account['email_address']
        account_provider = account.get('provider', 'unknown').lower()
        
        print(f"🍎 Starting EXACT CLI processing for {account_email} (Provider: {account_provider})")
        
        # Initialize connection manager EXACTLY like CLI
        connection_manager = IMAPConnectionManager(db_credentials)
        
        # Connect to account using EXACT CLI method
        mail = connection_manager.connect_to_imap(account=account)
        if not mail:
            return {"success": False, "message": "Failed to connect to email account"}
        
        try:
            # Get current account info EXACTLY like CLI
            current_account = connection_manager.current_account
            if not current_account:
                return {"success": False, "message": "No account information available"}

            # Initialize domain validator with account provider context EXACTLY like CLI
            domain_validator = DomainValidator(logger=write_log, account_provider=account_provider)

            # Initialize processors with new architecture EXACTLY like CLI (including account email for provider detection)
            processor = EmailProcessor(mail, domain_validator=domain_validator, account_email=account_email)
            
            # Get filters EXACTLY like CLI
            from configuration_manager import get_filters
            filters = get_filters()
            if not filters:
                filters = None  # Pass None instead of empty list for cleaner logic like CLI
            
            # Get target folders from account
            target_folders = account.get('target_folders', [])
            if not target_folders:
                connection_manager.disconnect()
                return {"success": False, "message": "No folders configured for this account"}
            
            # Create processing session EXACTLY like CLI
            account_id_db = current_account.get('id')
            if not account_id_db:
                # Find account ID by email if not available - EXACTLY like CLI
                account_records = db.execute_query("SELECT id FROM accounts WHERE email_address = ?", (account_email,))
                account_id_db = account_records[0]['id'] if account_records else None
            
            # Create session in database EXACTLY like CLI
            session_id = db.execute_insert("""
                INSERT INTO sessions (account_id, session_type, is_preview)
                VALUES (?, ?, ?)
            """, (account_id_db, 'manual', preview_mode))
            
            # Set logger session context EXACTLY like CLI
            logger.set_session_context(session_id, account_id_db)
            logger.log_session_start(account_email, account_id_db, session_id)
            
            total_deleted = 0
            total_preserved = 0
            total_validated = 0
            total_legitimate = 0
            all_categories = defaultdict(int)
            
            start_time = datetime.now()
            
            # Process each target folder EXACTLY like CLI
            for folder_name in target_folders:
                print(f"🔍 Processing folder: {folder_name}")
                
                # Process folder with EXACT CLI parameters
                deleted, _, preserved, validated, legitimate, categories = processor.process_folder_messages_with_new_architecture(
                    folder_name, filters, domain_validator, 
                    auto_confirm=True,      # CLI uses True for non-interactive
                    preview_mode=preview_mode,  # CLI uses False for actual deletion
                    debug_mode=False        # CLI uses False for clean output
                )
                
                # Update totals EXACTLY like CLI
                total_deleted += deleted
                total_preserved += preserved
                total_validated += validated
                total_legitimate += legitimate
                
                # Track categories EXACTLY like CLI
                for category, data in categories.items():
                    all_categories[category] += data['count']
                
                if preview_mode:
                    print(f"   📊 Would delete: {deleted:,} | preserve: {preserved:,} | legitimate: {legitimate:,}")
                else:
                    print(f"   📊 Deleted: {deleted:,} | preserved: {preserved:,} | legitimate: {legitimate:,}")
            
            # End session logging EXACTLY like CLI
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            try:
                logger.log_session_end(total_deleted, total_preserved, total_validated, elapsed_seconds)
            except Exception as e:
                print(f"⚠️  Warning: Could not log session end: {e}")
            
            # Update session end time in database EXACTLY like CLI
            try:
                db.execute_update("""
                    UPDATE sessions 
                    SET end_time = CURRENT_TIMESTAMP, 
                        folders_processed = ?, 
                        total_deleted = ?, 
                        total_preserved = ?, 
                        total_validated = ?,
                        categories_summary = ?
                    WHERE id = ?
                """, (
                    json.dumps(target_folders),
                    total_deleted,
                    total_preserved, 
                    total_validated,
                    json.dumps(dict(all_categories)),
                    session_id
                ))
            except Exception as e:
                print(f"⚠️  Warning: Could not update session data: {e}")
            
            connection_manager.disconnect()
            
            return {
                "success": True,
                "account_email": account['email_address'],
                "session_id": session_id,
                "total_deleted": total_deleted,
                "total_preserved": total_preserved,
                "total_validated": total_validated,
                "total_legitimate": total_legitimate,
                "categories": dict(all_categories),
                "folders_processed": target_folders,
                "message": f"{'Preview' if preview_mode else 'Processing'} complete: {total_deleted} {'to delete' if preview_mode else 'deleted'}, {total_preserved} {'to preserve' if preview_mode else 'preserved'}"
            }
            
        finally:
            connection_manager.disconnect()
            
    except Exception as e:
        print(f"❌ EXACT CLI processing error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error running exact CLI processing: {str(e)}"}


def single_account_filtering():
    """Handle single account filtering with smart confirmation logic"""
    # Clear screen and show clean interface
    clear_screen()
    print("📋 SINGLE ACCOUNT FILTERING:")
    print("-" * 60)

    # Initialize managers with database
    connection_manager = IMAPConnectionManager(db_credentials)

    # Connect to account - now handles exit option
    mail = connection_manager.connect_to_imap()
    if not mail:
        print("❌ Failed to connect to email account or user cancelled")
        return False

    try:
        # Get current account info
        current_account = connection_manager.current_account
        if not current_account:
            print("❌ No account information available")
            return False

        account_email = current_account['email_address']

        # Clear screen and show clean interface after connection
        clear_screen()
        from utils import display_application_header
        display_application_header("SINGLE ACCOUNT FILTERING")
        
        # Show provider-specific notes if available
        account_provider = current_account.get('provider', 'unknown').lower()
        if account_provider in ['icloud', 'gmail', 'outlook']:
            from provider_utils import ProviderDetector
            notes = ProviderDetector.get_optimization_notes(account_provider)
            print(f"📋 {account_provider.upper()} ACCOUNT NOTES:")
            for note in notes:
                print(f"   {note}")
            print()

        # Initialize domain validator with account provider context
        domain_validator = DomainValidator(logger=write_log, account_provider=account_provider)

        # Initialize processors with new architecture (including account email for provider detection)
        processor = EmailProcessor(mail, domain_validator=domain_validator, account_email=account_email)
        folder_manager = FolderManager(mail)

        target_candidates = []
        if not current_account.get('folder_setup_complete', False):
            print(f"🆕 First time setup for {account_email}")
            target_folders = folder_manager.setup_account_folders(account_email, db_credentials)
            if not target_folders:
                print("❌ No folders selected for processing. Returning to main menu.")
                return True

            # Build target_candidates from selected folders
            for folder_name in target_folders:
                count = folder_manager._get_message_count(folder_name)
                if count >= 0:
                    target_candidates.append((folder_name, count))
        else:
            # Use existing folder preferences
            target_folders = current_account.get('target_folders', [])

            # Verify folders still exist and get message counts
            print("📁 Loading your folder preferences...")
            missing_folders = []

            for folder_name in target_folders:
                count = folder_manager._get_message_count(folder_name)
                if count >= 0:  # Folder exists
                    target_candidates.append((folder_name, count))
                else:
                    missing_folders.append(folder_name)

            # Handle missing folders
            if missing_folders:
                print(f"\n⚠️  WARNING: Some previously selected folders no longer exist:")
                for folder in missing_folders:
                    print(f"❌ {folder}")
                print(f"   These folders will be skipped.")

        # Check if we have valid target folders
        if not target_candidates:
            print("❌ No valid target folders currently selected for this account.")
            print("💡 Please use 'Update Folder Selection' to choose folders before processing.")
        else:
            # Show current target folders
            print(f"\n📁 CURRENT TARGET FOLDERS FOR {account_email}:")
            for folder_name, count in target_candidates:
                print(f"  • {folder_name}: {count:,} messages")

        while True:
            # Show processing options
            print("\n📋 PROCESSING OPTIONS:")
            print("1. 🚀 Process Selected Folders")
            print("2. 🔍 Preview Mode (see what would be deleted)")
            print("3. 📁 Update Folder Selection")
            print("9. ⬅️  Back to Main Menu")

            choice = get_single_choice("Press a key (1-3, 9, or Enter/Escape to exit):", ['1', '2', '3', '9'], allow_enter=True)
            if choice is None or choice == '9':
                return True

            if choice == '3':
                current_folders_for_update = current_account.get('target_folders', [])
                updated_folders = folder_manager.update_account_folders(account_email, current_folders_for_update, db_credentials)

                # Rebuild target_candidates with updated folders
                target_candidates = []
                for folder_name in updated_folders:
                    count = folder_manager._get_message_count(folder_name)
                    if count >= 0:
                        target_candidates.append((folder_name, count))

                if not target_candidates:
                    print("❌ No folders selected for processing. Returning to main menu.")
                    return True

                # Show updated selection
                print(f"\n📁 UPDATED TARGET FOLDERS:")
                for folder_name, count in target_candidates:
                    print(f"  • {folder_name}: {count:,} messages")

                continue

            # Process or preview
            if not target_candidates:
                print("❌ No folders are selected for processing. Please select folders first via 'Update Folder Selection'.")
                continue

            # Load optional custom filters (system primarily uses hybrid classifier)
            from configuration_manager import get_filters
            filters = get_filters()
            if not filters:
                print("🧠 Using hybrid classifier (no additional custom keywords)")
                filters = None  # Pass None instead of empty list for cleaner logic
            else:
                print(f"📝 Using hybrid classifier + {len(filters)} custom keywords from my_keywords.txt")

            # Handle different processing modes
            if choice == '2':
                print("🔍 Running preview analysis...")
                selected_folders = target_candidates
                preview_mode = True
                needs_confirmation = False
                debug_mode = False  # Disable debug output for cleaner preview
            elif choice == '1':
                print("🚀 Processing selected folders...")
                selected_folders = target_candidates
                preview_mode = False
                needs_confirmation = False  # No confirmation for direct processing
                debug_mode = False  # No debug for actual processing

            # Smart confirmation logic - only for manual confirmation mode
            if needs_confirmation:
                print(f"\n📋 You selected {len(selected_folders)} folder(s) for processing:")
                for folder_name, count in selected_folders:
                    print(f"  • {folder_name}: {count:,} messages")

                confirm = input("\nProceed with deletion of selected folders? (yes/no): ").strip().lower()
                if confirm not in ('yes', 'y'):
                    print("👋 Processing cancelled")
                    return True

            # Process folders with new architecture
            print(f"\n🚀 STARTING EMAIL PROCESSING")
            print("=" * 50)

            total_deleted = 0
            total_preserved = 0
            total_validated = 0
            total_legitimate = 0
            all_categories = defaultdict(int)

            start_time = datetime.now()

            # Create processing session for database logging
            account_id = current_account.get('id')  # Get account ID from database
            if not account_id:
                # Find account ID by email if not available
                account_records = db.execute_query("SELECT id FROM accounts WHERE email_address = ?", (account_email,))
                account_id = account_records[0]['id'] if account_records else None
            
            # Create session in database
            session_id = db.execute_insert("""
                INSERT INTO sessions (account_id, session_type, is_preview)
                VALUES (?, ?, ?)
            """, (account_id, 'manual', preview_mode))
            
            # Set logger session context
            logger.set_session_context(session_id, account_id)
            logger.log_session_start(account_email, account_id, session_id)

            for folder_name, message_count in selected_folders:
                print(f"\n📂 Processing {folder_name} ({message_count:,} messages)")

                # Process folder with updated architecture and debug support
                deleted, _, preserved, validated, legitimate, categories = processor.process_folder_messages_with_new_architecture(
                    folder_name, filters, domain_validator, auto_confirm=not needs_confirmation, preview_mode=preview_mode, debug_mode=debug_mode
                )

                # Update totals
                total_deleted += deleted
                total_preserved += preserved
                total_validated += validated
                total_legitimate += legitimate

                # Track categories
                for category, data in categories.items():
                    all_categories[category] += data['count']

                if preview_mode:
                    print(f"   📊 Would delete: {deleted:,} | preserve: {preserved:,} | legitimate: {legitimate:,}")
                else:
                    print(f"   📊 Deleted: {deleted:,} | preserved: {preserved:,} | legitimate: {legitimate:,}")

            # End session logging with error handling
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            try:
                logger.log_session_end(total_deleted, total_preserved, total_validated, elapsed_seconds)
            except Exception as e:
                print(f"⚠️  Warning: Could not log session end: {e}")
            
            # Update session end time in database
            try:
                db.execute_update("""
                    UPDATE sessions 
                    SET end_time = CURRENT_TIMESTAMP, 
                        folders_processed = ?, 
                        total_deleted = ?, 
                        total_preserved = ?, 
                        total_validated = ?,
                        categories_summary = ?
                    WHERE id = ?
                """, (
                    json.dumps([f[0] for f in selected_folders]),
                    total_deleted,
                    total_preserved, 
                    total_validated,
                    json.dumps(dict(all_categories)),
                    session_id
                ))
            except Exception as e:
                print(f"⚠️  Warning: Could not update session data: {e}")

            # Display summary
            from menu_handler import display_processing_summary
            display_processing_summary(total_deleted, total_preserved, total_validated, total_legitimate,
                                     sum(f[1] for f in selected_folders), account_email, preview_mode)

            return True  # Return immediately to main menu

    finally:
        connection_manager.disconnect()


def batch_processing():
    """Handle batch processing of all accounts"""
    from utils import display_application_header
    display_application_header("BATCH PROCESSING (All Accounts)")

    connection_manager = IMAPConnectionManager(db_credentials)
    batch_processor = BatchProcessor(db_credentials, connection_manager)

    accounts = db_credentials.load_credentials()
    if not accounts:
        print("❌ No saved accounts found")
        return False

    print(f"📋 Found {len(accounts)} saved accounts:")
    for i, account in enumerate(accounts, 1):
        print(f"  {i}. {account['email_address']} ({account['provider']})")

    # Process all accounts immediately without confirmation
    print(f"\n🚀 PROCESSING ALL {len(accounts)} ACCOUNTS")
    print("=" * 50)

    from configuration_manager import get_filters
    filters = get_filters()
    if not filters:
        print("📊 Using database-driven spam detection (no custom keywords loaded)")
    else:
        print(f"📝 Loaded {len(filters)} custom keywords from my_keywords.txt")

    print("\n🚀 Starting batch processing...")
    # Updated to use new architecture
    results = batch_processor.process_all_accounts_with_new_architecture(filters, auto_yes=True)

    return len([r for r in results if r['success']]) > 0


def analytics_reporting():
    """Handle analytics and reporting with database"""
    try:
        analytics_menu = DatabaseAnalyticsMenu()
        analytics_menu.run()
    except Exception as e:
        logger.error(e, "analytics_reporting")
        print(f"❌ Error loading database analytics: {e}")
        input("Press Enter to continue...")


def email_action_viewer():
    """Handle email action viewer and export"""
    try:
        viewer = BulletproofEmailActionViewer()
        viewer.run()
    except Exception as e:
        logger.error(f"Error loading email action viewer: {e}")
        print(f"❌ Error loading email action viewer: {e}")
        input("Press Enter to continue...")