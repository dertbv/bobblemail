#!/usr/bin/env python3
"""
Advanced IMAP Mail Filter with ML Domain Validation - Database Edition
Enhanced with database storage, logging, and analytics
Updated to use database architecture for all data storage
"""

import sys
import os
import json
from datetime import datetime
from collections import defaultdict

# Import database modules
from database import db
from db_logger import logger, write_log, LogCategory
from db_credentials import db_credentials
from db_analytics import DatabaseAnalyticsMenu
from email_action_viewer import BulletproofEmailActionViewer
from category_keywords import CategoryKeywordManager
from builtin_keywords_manager import BuiltinKeywordsManager
from auto_batch_timer import AutoBatchTimer

# Import original modules (updated to work with database)
from config_auth import IMAPConnectionManager, parse_config_file
from email_processor import EmailProcessor, FolderManager, BatchProcessor

# Import new split modules
from domain_validator import DomainValidator
from utils import get_user_choice as get_single_choice, clear_screen


def get_filters():
    """Get filters from config file"""
    filters = parse_config_file()
    if filters is False or not filters:
        # Return empty list if config file doesn't exist or is empty
        # The system now uses database-driven spam detection, so no fallback keywords needed
        return []
    return filters

def initialize_application():
    """Initialize the mail filter application with database"""
    print("🚀 Initializing Mail Filter Application - Database Edition...")
    print("🔧 Initializing Database and Configuration...")
    
    try:
        # Initialize database
        db_stats = db.get_database_stats()
        print(f"📊 Database: {db_stats['db_size_mb']:.1f}MB, {db_stats['logs_count']} logs, {db_stats['accounts_count']} accounts")
        
        # Migrate credentials from JSON if needed
        if os.path.exists('.mail_filter_creds.json'):
            print("🔄 Migrating credentials from JSON to database...")
            db_credentials.migrate_from_json('.mail_filter_creds.json')
            
        # Load filters
        filters = get_filters()
        print(f"✅ Configuration loaded: {len(filters)} filter terms")
        
        # Log application start
        logger.info("=== Mail Filter Application Started (Database Edition) ===", 
                   category=LogCategory.SYSTEM,
                   metadata={"version": "database_edition", "filters_count": len(filters)})
        
        print("✅ Database application initialized successfully")
        return filters
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        logger.error(e, "initialize_application")
        return []

# Global timer instance for automated batch processing
auto_timer = None

def initialize_auto_timer():
    """Initialize the auto batch timer"""
    global auto_timer
    
    def batch_processor_callback():
        """Callback function for automated batch processing"""
        return batch_processing_for_timer()
    
    auto_timer = AutoBatchTimer(batch_processor_callback)
    return auto_timer

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

def display_main_menu():
    """Display the main application menu with database stats"""
    from utils import display_application_header
    
    display_application_header("MAIN MENU")
    print("1. ⚙️  Configuration Management")
    print("2. 🎯 Single Account Filtering")
    print("3. 🤖 Batch Processing (All Accounts)")
    print("4. 📧 Email Action Viewer & Export")
    print("5. ❓ Help & Documentation")
    print("0. 🚪 Exit")
    print()

def get_menu_choice():
    """Get user's menu choice with input fallback"""
    choice = get_single_choice("Press a key (0-5, or Enter/Escape to exit):", ['0', '1', '2', '3', '4', '5'], allow_enter=True)
    
    if choice is None:
        print("\n👋 Goodbye!")
        if auto_timer:
            auto_timer.stop_all_timers()
        sys.exit(0)
    
    return int(choice)


def configuration_management():
    """Handle configuration management"""
    from config_auth import ConfigurationManager

    config_manager = ConfigurationManager()

    # Initialize configuration (creates config file if needed)
    if not config_manager.initialize():
        print("❌ Failed to initialize configuration")
        input("Press Enter to continue...")
        return

    while True:
        from utils import display_application_header
        display_application_header("CONFIGURATION MANAGEMENT")
        print("1. 📝 Edit Filter Terms")
        print("2. 📊 Category Manager")
        print("3. 📊 ML Detection Thresholds")
        print("4. 🗃️  Export/Import Configuration")
        print("5. 🔄 Reset to Defaults")
        print("6. 🛡️  Whitelist Management")
        print("9. ⬅️  Back to Main Menu")

        choice = get_single_choice("Press a key (1-6, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '9'], allow_enter=True)
        if choice is None or choice == '9':
            break

        clear_screen()
        if choice == '1':
            config_manager.edit_config_interactive()
        elif choice == '2':
            unified_category_manager()
        elif choice == '3':
            ml_classification_tuning()
        elif choice == '4':
            export_import_config()
        elif choice == '5':
            reset_to_defaults()
        elif choice == '6':
            whitelist_management()
        
        # Clear screen after each submenu operation
        clear_screen()

def unified_category_manager():
    """Unified Category Manager - combines category enable/disable with keyword management"""
    try:
        from ml_settings import MLSettingsManager, CategoryManager
        from category_keywords import CategoryKeywordManager
        
        # Initialize managers
        ml_settings_manager = MLSettingsManager()
        ml_category_manager = CategoryManager(ml_settings_manager)
        keyword_manager = CategoryKeywordManager()
        
        while True:
            _display_unified_category_menu(ml_settings_manager, keyword_manager)
            
            # Use regular input to allow two-digit numbers
            try:
                choice_input = input("Choose option (1-19, or press Enter to exit): ").strip()
                if not choice_input:  # Empty input (Enter pressed)
                    break
                
                choice_num = int(choice_input)
                if not (1 <= choice_num <= 19):
                    print("❌ Please enter a number between 1 and 19")
                    input("Press Enter to continue...")
                    clear_screen()
                    continue
                    
            except ValueError:
                print("❌ Please enter a valid number")
                input("Press Enter to continue...")
                clear_screen()
                continue
            except KeyboardInterrupt:
                break
            
            clear_screen()
            
            # Handle category toggles (1-12)
            if 1 <= choice_num <= 12:
                _handle_category_toggle(choice_num, ml_settings_manager)
            # Handle management options (13-18)
            elif choice_num == 13:
                keyword_manager._view_all_categories()
            elif choice_num == 14:
                keyword_manager._manage_category_keywords_menu()
            elif choice_num == 15:
                keyword_manager._add_keyword_to_category()
            elif choice_num == 16:
                keyword_manager._remove_keyword_from_category()
            elif choice_num == 17:
                keyword_manager._import_category_keywords()
            elif choice_num == 18:
                keyword_manager._export_category_keywords()
            
            input("\nPress Enter to continue...")
            clear_screen()
            
    except Exception as e:
        logger.error(e, "unified_category_manager")
        print(f"❌ Error loading category manager: {e}")
        input("Press Enter to continue...")


def _display_unified_category_menu(ml_settings_manager, keyword_manager):
    """Display the unified category management menu"""
    from utils import display_application_header
    settings = ml_settings_manager.settings
    
    display_application_header("CATEGORY MANAGER")
    print("📂 SPAM CATEGORIES (Auto-save enabled):")
    
    # Get category stats
    enabled_count = sum(1 for enabled in settings['enabled_categories'].values() if enabled)
    total_count = len(settings['enabled_categories'])
    print(f"📊 {enabled_count}/{total_count} enabled")
    
    # Display categories with toggle numbers 1-12
    for i, (category, enabled) in enumerate(settings['enabled_categories'].items(), 1):
        status = "✅" if enabled else "❌"
        risk_level = _get_category_risk_icon(category)
        print(f"{i:2d}. {status} {category} {risk_level}")
    
    # Get keyword stats
    try:
        keyword_stats = keyword_manager.get_category_stats()
        total_keywords = keyword_stats.get('total_keywords', 0)
        categories_with_terms = keyword_stats.get('categories_with_terms', 0)
        print(f"📋 Custom keywords: {total_keywords}")
        print(f"📂 Categories with custom terms: {categories_with_terms}")
    except Exception as e:
        print("📋 Custom keywords: Loading...")
        # Note: Keyword loading failed, continuing with defaults
    
    print()
    print("13. 📋 View All Categories & Keywords")
    print("14. 🎯 Manage Specific Category")
    print("15. ➕ Add Keyword to Category")
    print("16. ➖ Remove Keyword from Category")
    print("17. 📤 Import Category Keywords")
    print("18. 📥 Export Category Keywords")
    print("19. ⬅️  Back to Configuration")


def _get_category_risk_icon(category: str) -> str:
    """Get risk level icon for category"""
    from constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES
    
    if category in HIGH_RISK_CATEGORIES:
        return "⚠️"
    elif category in MEDIUM_RISK_CATEGORIES:
        return "🔶"
    else:
        return "🟢"


def _handle_category_toggle(choice_num: int, ml_settings_manager):
    """Handle toggling a specific category"""
    settings = ml_settings_manager.settings
    categories = list(settings['enabled_categories'].keys())
    
    if choice_num - 1 < len(categories):
        category_name = categories[choice_num - 1]
        current_status = settings['enabled_categories'][category_name]
        settings['enabled_categories'][category_name] = not current_status
        
        status = "ENABLED" if not current_status else "DISABLED"
        print(f"🔄 {category_name} → {status}")
        ml_settings_manager.save_settings()
    else:
        print("❌ Invalid category selection")


def builtin_keywords_management():
    """Handle built-in keywords management"""
    try:
        manager = BuiltinKeywordsManager()
        manager.manage_builtin_keywords()
    except Exception as e:
        logger.error(e, "builtin_keywords_management")
        print(f"❌ Error loading built-in keywords manager: {e}")
        input("Press Enter to continue...")

def auto_timer_management():
    """Handle auto batch timer management"""
    try:
        if auto_timer:
            auto_timer.manage_auto_batch_timer()
        else:
            print("❌ Auto timer not initialized")
            input("Press Enter to continue...")
    except Exception as e:
        logger.error(e, "auto_timer_management")
        print(f"❌ Error loading auto timer manager: {e}")
        input("Press Enter to continue...")

def run_preview_for_account(account_id, debug_mode=False, preview_mode=True):
    """Run processing for a specific account - callable from web interface"""
    from collections import defaultdict
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
            processor = EmailProcessor(mail, account['email_address'])
            domain_validator = DomainValidator()
            
            # Get filters (empty list is OK - system uses database spam detection)
            filters = get_filters()
            # Note: Empty filters list is valid - system uses database-driven spam detection
            
            # Get target folders from account
            target_folders = account.get('target_folders', [])
            if not target_folders:
                connection_manager.disconnect()
                return {"success": False, "message": "No folders configured for this account"}
            
            # Create session in database
            from database import db
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
    from collections import defaultdict
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
            filters = get_filters()
            if not filters:
                filters = None  # Pass None instead of empty list for cleaner logic like CLI
            
            # Get target folders from account
            target_folders = account.get('target_folders', [])
            if not target_folders:
                connection_manager.disconnect()
                return {"success": False, "message": "No folders configured for this account"}
            
            # Create processing session EXACTLY like CLI
            from database import db
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
            from database import db
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
            display_processing_summary(total_deleted, total_preserved, total_validated, total_legitimate,
                                     all_categories, start_time, preview_mode)

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

def account_management():
    """Handle account management with database"""

    while True:
        from utils import display_application_header
        display_application_header("ACCOUNT MANAGEMENT")
        print("1. 📝 Add New Account")
        print("2. 📋 List Saved Accounts")
        print("3. 🗑️  Remove Account")
        print("4. 🔄 Test Connection")
        print("9. ⬅️  Back to Main Menu")

        choice = get_single_choice("Press a key (1-4, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '9'], allow_enter=True)
        if choice is None or choice == '9':
            break

        if choice == '1':
            add_new_account()
        elif choice == '2':
            list_saved_accounts()
        elif choice == '3':
            remove_account_interactive()
        elif choice == '4':
            test_account_connection()

def add_new_account():
    """Add a new account interactively"""
    connection_manager = IMAPConnectionManager(db_credentials)

    # This will trigger the interactive setup process
    mail = connection_manager.connect_to_imap()
    if mail:
        print("✅ Account added successfully!")
        connection_manager.disconnect()
    else:
        print("❌ Failed to add account")

def remove_account_interactive():
    """Remove an account interactively"""
    accounts = db_credentials.load_credentials()
    if not accounts:
        print("📭 No saved accounts found")
        return

    print("\n📋 SAVED ACCOUNTS:")
    print("-" * 40)
    for i, account in enumerate(accounts, 1):
        print(f"{i}. {account['email_address']} ({account['provider']})")
    print("-" * 40)

    try:
        choice = int(input("Enter account number to remove (0 to cancel): "))
        if choice == 0:
            print("❌ Cancelled")
            return
        if 1 <= choice <= len(accounts):
            account = accounts[choice - 1]
            confirm = input(f"Remove {account['email_address']}? (yes/no): ").strip().lower()
            if confirm in ('yes', 'y'):
                db_credentials.delete_account(account['email_address'])
            else:
                print("❌ Cancelled")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")

def utilities():
    """Handle utilities menu"""
    while True:
        from utils import display_application_header
        display_application_header("UTILITIES")
        print("1. 🧹 Clear Log Files")
        print("2. 🗂️  Export/Import Configuration")
        print("3. 🔄 Migrate Old Log File to Database")
        print("9. ⬅️  Back to Main Menu")

        choice = get_single_choice("Press a key (1-3, 9, or Enter/Escape to exit):", ['1', '2', '3', '9'], allow_enter=True)
        if choice is None or choice == '9':
            break

        if choice == '1':
            clear_log_files()
        elif choice == '2':
            export_import_config()
        elif choice == '3':
            migrate_old_log_file()

def help_documentation():
    """Show help and documentation"""
    while True:
        from utils import display_application_header
        display_application_header("HELP & DOCUMENTATION")
        print("1. 📖 User Guide")
        print("2. ℹ️  About")
        print("3. ⏰ Auto Batch Timer")
        print("4. 📊 Analytics & Reporting")
        print("5. 👤 Account Management")
        print("6. 🔧 Utilities")
        print("9. ⬅️  Back to Main Menu")

        choice = get_single_choice("Press a key (1-6, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '9'], allow_enter=True)
        if choice is None or choice == '9':
            break

        clear_screen()
        if choice == '1':
            show_user_guide()
        elif choice == '2':
            show_about()
        elif choice == '3':
            auto_timer_management()
        elif choice == '4':
            analytics_reporting()
        elif choice == '5':
            account_management()
        elif choice == '6':
            utilities()
        
        # Clear screen after each submenu operation
        clear_screen()

def domain_validation_settings():
    print("🔧 Domain validation settings coming soon...")
    print("Current settings:")
    print("  • Entropy threshold: 3.2")
    print("  • Confidence threshold: 50%")
    print("  • WHOIS timeout: 5 seconds")
    print("  • Domain age threshold: 90 days")

def ml_classification_tuning():
    """Advanced ML Classification Tuning Interface - Refactored"""
    from ml_settings import ml_classification_tuning as ml_tuning
    ml_tuning()


def whitelist_management():
    """Whitelist Management Interface"""
    from ml_settings import WhitelistManager
    whitelist_manager = WhitelistManager()
    whitelist_manager.manage_whitelist()


def export_import_config():
    from config_auth import backup_configuration, get_file_paths
    
    while True:
        from utils import display_application_header
        display_application_header("EXPORT/IMPORT CONFIGURATION")
        print("1. 📤 Backup current configuration")
        print("2. 📋 Show file locations")
        print("9. ⬅️  Back to Utilities")

        choice = get_single_choice("Press a key (1-2, 9, or Enter/Escape to exit):", ['1', '2', '9'], allow_enter=True)
        if choice is None or choice == '9':
            break

        clear_screen()
        if choice == '1':
            backup_file = backup_configuration()
            if backup_file:
                print(f"✅ Configuration backed up successfully")
            else:
                print("❌ Backup failed")
        elif choice == '2':
            paths = get_file_paths()
            print("\n📁 Configuration file locations:")
            for name, path in paths.items():
                print(f"  {name}: {path}")
            input("\nPress Enter to continue...")
        
        # Clear screen after each operation
        clear_screen()

def reset_to_defaults():
    print("🔄 RESET TO DEFAULTS")
    print("⚠️  This will reset all filter terms to defaults")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    if confirm in ('yes', 'y'):
        print("🔄 Reset functionality coming soon...")
    else:
        print("❌ Cancelled")

def list_saved_accounts():
    accounts = db_credentials.load_credentials()
    if accounts:
        print("\n📋 Saved Accounts:")
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. {account['email_address']} ({account['provider']})")
    else:
        print("📭 No saved accounts found")

def test_account_connection():
    connection_manager = IMAPConnectionManager(db_credentials)
    mail = connection_manager.connect_to_imap()
    if mail:
        print("✅ Connection successful!")
        connection_manager.disconnect()
    else:
        print("❌ Connection failed")

def clear_log_files():
    """Clear database logs with confirmation"""
    from db_logger import logger
    
    print("\n🧹 CLEAR DATABASE LOGS")
    print("=" * 50)
    
    # Get log statistics
    try:
        recent_logs = db.execute_query("SELECT COUNT(*) as count FROM logs WHERE timestamp > datetime('now', '-7 days')")[0]['count']
        total_logs = db.execute_query("SELECT COUNT(*) as count FROM logs")[0]['count']
        
        print(f"📊 Total logs in database: {total_logs:,}")
        print(f"📊 Recent logs (7 days): {recent_logs:,}")
        
        if total_logs > 0:
            print("\nOptions:")
            print("1. Clear logs older than 30 days (recommended)")
            print("2. Clear ALL logs (not recommended)")
            print("3. Cancel")
            
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == '1':
                deleted = logger.cleanup_old_logs(30)
                print(f"✅ Cleaned up {deleted} old log entries (kept 30 days)")
            elif choice == '2':
                confirm = input("Are you SURE you want to delete ALL logs? (type YES): ").strip()
                if confirm == 'YES':
                    deleted = db.execute_update("DELETE FROM logs")
                    db.execute_update("DELETE FROM performance_metrics")
                    db.execute_update("DELETE FROM error_reports")
                    print(f"✅ Deleted all {deleted} log entries")
                else:
                    print("❌ Cancelled")
            else:
                print("❌ Cancelled")
        else:
            print("📭 No logs found in database")
            
    except Exception as e:
        print(f"❌ Error accessing database logs: {e}")
    
    input("\nPress Enter to continue...")

def show_user_guide():
    """Show basic user guide"""
    print("\n📖 USER GUIDE")
    print("=" * 50)
    print("""
🎯 QUICK START:
1. Add your email account via 'Account Management'
2. Configure filter terms via 'Configuration Management'
3. Run 'Single Account Filtering' to process emails

🔧 MAIN FEATURES:
• Automatic spam detection using ML classification
• Domain validation to prevent false positives
• Batch processing for multiple accounts
• Provider-specific optimizations (iCloud, Gmail, etc.)

⚙️ CONFIGURATION:
• Keywords file: my_keywords.txt
• ML settings: ml_settings.json
• Account data: .mail_filter_creds.json

🛡️ SAFETY FEATURES:
• Preview mode to see what would be deleted
• Domain whitelist protection
• Provider-aware spam thresholds
• Backup and restore functionality

📋 SPAM CATEGORIES:
• Investment/Financial scams
• Gambling/Casino spam
• Health/Pharmaceutical scams
• Brand impersonation
• Legal settlement scams
• Business opportunity MLM
""")
    input("\nPress Enter to continue...")

def show_about():
    print("\nℹ️  ABOUT")
    print("=" * 30)
    print("🛡️  Advanced IMAP Mail Filter")
    print("🔧 Version: 2.1 - Split Architecture")
    print("👤 Your Email Security Assistant")
    print("🔧 Enhanced with modular spam classification")
    print("=" * 30)

def display_processing_summary(total_deleted, total_preserved, total_validated, total_legitimate,
                             all_categories, start_time, preview_mode=False):
    """Display comprehensive processing summary"""
    # Clear screen before showing clean summary
    clear_screen()
    
    elapsed_time = datetime.now() - start_time

    print("\n" + "=" * 70)
    action_word = "WOULD DELETE" if preview_mode else "DELETED"
    print(f"✅ PROCESSING COMPLETE - {action_word} SUMMARY")
    print("=" * 70)

    print(f"🗑️  Total {action_word.lower()}: {total_deleted:,} messages")
    print(f"🛡️  Total preserved: {total_preserved:,} messages")
    print(f"✅ Total legitimate: {total_legitimate:,} messages")
    print(f"🔍 Domains validated: {total_validated:,}")
    print(f"⏱️  Processing time: {elapsed_time.total_seconds():.1f} seconds")

    if all_categories:
        print(f"\n📊 SPAM CATEGORIES {action_word}:")
        print("-" * 40)
        for category, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_deleted * 100) if total_deleted > 0 else 0
            print(f"{category:<25} {count:>3,} ({percentage:>5.1f}%)")

    total_processed = total_deleted + total_preserved + total_legitimate
    if total_processed > 0:
        print(f"\n📊 PROCESSING BREAKDOWN:")
        print(f"   🗑️  Deleted: {(total_deleted / total_processed * 100):>5.1f}%")
        print(f"   🛡️  Preserved: {(total_preserved / total_processed * 100):>5.1f}%") 
        print(f"   ✅ Legitimate: {(total_legitimate / total_processed * 100):>5.1f}%")
        
        spam_detection_rate = ((total_deleted + total_preserved) / total_processed * 100) if total_processed > 0 else 0
        print(f"\n🎯 Spam detection rate: {spam_detection_rate:.1f}%")
    else:
        print(f"\n🎯 No emails processed")

    if preview_mode:
        print(f"\n🔍 This was PREVIEW MODE - no emails were actually deleted")
    else:
        print(f"\n🎉 Email cleanup complete!")

    print("=" * 70)

def main():
    """Main application entry point"""
    global auto_timer
    
    try:
        # Initialize application
        filters = initialize_application()
        
        # Initialize auto timer
        auto_timer = initialize_auto_timer()
        
        # Clear screen initially
        clear_screen()

        while True:
            display_main_menu()
            choice = get_menu_choice()

            if choice == 1:
                clear_screen()
                configuration_management()
                clear_screen()
            elif choice == 2:
                # Don't clear screen for filtering - keep scrolling output
                single_account_filtering()
                input("\nPress Enter to continue...")
                clear_screen()
            elif choice == 3:
                # Don't clear screen for batch processing - keep scrolling output
                batch_processing()
                input("\nPress Enter to continue...")
                clear_screen()
            elif choice == 4:
                clear_screen()
                email_action_viewer()
                clear_screen()
            elif choice == 5:
                clear_screen()
                help_documentation()
                clear_screen()
            elif choice == 0:
                clear_screen()
                print("\n👋 Thank you for using Advanced IMAP Mail Filter - Database Edition!")
                print("🛡️  Your email security is our priority!")
                
                # Stop any running timers
                if auto_timer:
                    auto_timer.stop_all_timers()
                
                try:
                    logger.info("=== Mail Filter Application Exited ===", category=LogCategory.SYSTEM)
                except Exception:
                    pass  # Don't let logging errors crash the application
                break

            # No pause between operations - return directly to menu

    except KeyboardInterrupt:
        clear_screen()
        print("\n\n⚠️  Process interrupted by user")
        print("👋 Goodbye!")
        # Stop any running timers
        if auto_timer:
            auto_timer.stop_all_timers()
        try:
            logger.info("=== Mail Filter Application Interrupted by User ===", category=LogCategory.SYSTEM)
        except Exception:
            pass  # Don't let logging errors crash the application
    except Exception as e:
        clear_screen()
        print(f"\n❌ Unexpected error: {e}")
        # Stop any running timers
        if auto_timer:
            auto_timer.stop_all_timers()
        try:
            logger.error(f"Error in main application loop: {e}")
        except Exception:
            pass  # Don't let logging errors crash the application
    finally:
        # Ensure timers are stopped
        if auto_timer:
            auto_timer.stop_all_timers()
        try:
            logger.info("=== Mail Filter Application Exited ===", category=LogCategory.SYSTEM)
        except Exception:
            pass  # Don't let logging errors crash the application

if __name__ == "__main__":
    main()