"""
Configuration Manager Module - Extracted from main.py
Handles all configuration, settings, and management functions
"""

import os
import json

# Import database modules
from atlas_email.models.database import db
from atlas_email.models.db_logger import logger, LogCategory
from config.credentials import db_credentials
from atlas_email.utils.batch_timer import AutoBatchTimer

# Import original modules
from config.auth import parse_config_file, IMAPConnectionManager
from atlas_email.utils.general import get_user_choice as get_single_choice, clear_screen


# Import get_filters from config_loader to avoid circular dependency
from config.loader import get_filters


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


def initialize_auto_timer():
    """Initialize the auto batch timer"""
    def batch_processor_callback():
        """Callback function for automated batch processing"""
        from atlas_email.core.processing_controller import batch_processing_for_timer
        return batch_processing_for_timer()
    
    auto_timer = AutoBatchTimer(batch_processor_callback)
    return auto_timer


def configuration_management():
    """Handle configuration management"""
    from config.auth import ConfigurationManager

    config_manager = ConfigurationManager()

    # Initialize configuration (creates config file if needed)
    if not config_manager.initialize():
        print("❌ Failed to initialize configuration")
        input("Press Enter to continue...")
        return

    while True:
        from atlas_email.utils.general import display_application_header
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
        from atlas_email.ml.settings import MLSettingsManager, CategoryManager
        from atlas_email.filters.category_keywords import CategoryKeywordManager
        
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
    from atlas_email.utils.general import display_application_header
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
    from config.constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES
    
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
        new_status = not current_status
        
        # Update the setting
        settings['enabled_categories'][category_name] = new_status
        ml_settings_manager.save_settings()
        
        status_text = "✅ ENABLED" if new_status else "❌ DISABLED"
        print(f"\n🔄 {category_name} → {status_text}")


def builtin_keywords_management():
    """Handle built-in keywords management"""
    try:
        from atlas_email.filters.builtin_keywords import BuiltinKeywordsManager
        manager = BuiltinKeywordsManager()
        manager.manage_builtin_keywords()
    except Exception as e:
        logger.error(e, "builtin_keywords_management")
        print(f"❌ Error loading built-in keywords manager: {e}")
        input("Press Enter to continue...")


def auto_timer_management():
    """Handle auto batch timer management"""
    try:
        # Note: Auto timer management requires access to global auto_timer
        # This function is a placeholder for now
        print("🤖 AUTO BATCH TIMER MANAGEMENT")
        print("Auto timer management functionality will be available through main application.")
        input("Press Enter to continue...")
    except Exception as e:
        logger.error(e, "auto_timer_management")
        print(f"❌ Error loading auto timer manager: {e}")
        input("Press Enter to continue...")


def account_management():
    """Handle account management with database"""
    while True:
        from atlas_email.utils.general import display_application_header
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
                print(f"✅ Removed {account['email_address']}")
            else:
                print("❌ Cancelled")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")


def utilities():
    """Handle utilities menu"""
    while True:
        from atlas_email.utils.general import display_application_header
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
    """Handle help and documentation"""
    while True:
        from atlas_email.utils.general import display_application_header
        display_application_header("HELP & DOCUMENTATION")
        print("1. 📖 User Guide")
        print("2. ℹ️  About")
        print("3. 🧪 Test Features")
        print("4. ⚙️  Account Management")
        print("5. 🔧 Utilities")
        print("6. 🔍 Domain Validation Settings")
        print("7. 🤖 Auto Batch Timer Management")
        print("8. 📝 Built-in Keywords Management")
        print("9. ⬅️  Back to Main Menu")

        choice = get_single_choice("Press a key (1-9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '7', '8', '9'], allow_enter=True)
        if choice is None or choice == '9':
            break

        clear_screen()
        if choice == '1':
            from atlas_email.cli.menu_handler import show_user_guide
            show_user_guide()
        elif choice == '2':
            from atlas_email.cli.menu_handler import show_about
            show_about()
        elif choice == '3':
            domain_validation_settings()
        elif choice == '4':
            account_management()
        elif choice == '5':
            utilities()
        elif choice == '6':
            domain_validation_settings()
        elif choice == '7':
            auto_timer_management()
        elif choice == '8':
            builtin_keywords_management()
        
        clear_screen()


def domain_validation_settings():
    """Domain validation settings"""
    print("🔍 DOMAIN VALIDATION SETTINGS")
    print("Domain validation is automatically enabled for all processing.")
    print("This feature helps protect legitimate business domains from false positives.")
    input("Press Enter to continue...")


def ml_classification_tuning():
    """Advanced ML Classification Tuning Interface - Refactored"""
    from atlas_email.ml.settings import ml_classification_tuning as ml_tuning
    ml_tuning()


def whitelist_management():
    """Whitelist Management Interface"""
    from atlas_email.ml.settings import WhitelistManager
    whitelist_manager = WhitelistManager()
    whitelist_manager.manage_whitelist()


def export_import_config():
    """Handle export/import configuration"""
    from config.auth import backup_configuration, get_file_paths
    
    while True:
        from atlas_email.utils.general import display_application_header
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
    """Reset configuration to defaults"""
    print("🔄 RESET TO DEFAULTS")
    print("⚠️  This will reset all filter terms to defaults")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    if confirm in ('yes', 'y'):
        print("🔄 Reset functionality coming soon...")
    else:
        print("❌ Cancelled")


def list_saved_accounts():
    """List all saved accounts"""
    accounts = db_credentials.load_credentials()
    if accounts:
        print("\n📋 Saved Accounts:")
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. {account['email_address']} ({account['provider']})")
    else:
        print("📭 No saved accounts found")


def test_account_connection():
    """Test connection to an account"""
    connection_manager = IMAPConnectionManager(db_credentials)
    mail = connection_manager.connect_to_imap()
    if mail:
        print("✅ Connection successful!")
        connection_manager.disconnect()
    else:
        print("❌ Connection failed")


def clear_log_files():
    """Clear database logs with confirmation"""
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


def migrate_old_log_file():
    """Migrate old log file to database"""
    print("🔄 MIGRATE OLD LOG FILE TO DATABASE")
    print("This feature will be implemented to migrate legacy log files.")
    input("Press Enter to continue...")