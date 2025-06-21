"""
Menu Handler Module - Extracted from main.py
Handles all menu display, user input, and navigation functions
"""

import sys
from utils import get_user_choice as get_single_choice


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
        # Exit gracefully - auto_timer cleanup handled in main
        sys.exit(0)
    
    return int(choice)


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
        new_status = not current_status
        
        # Update the setting
        settings['enabled_categories'][category_name] = new_status
        ml_settings_manager.save_settings()
        
        status_text = "✅ ENABLED" if new_status else "❌ DISABLED"
        print(f"\n🔄 {category_name} → {status_text}")


def show_user_guide():
    """Display comprehensive user guide"""
    from utils import display_application_header, clear_screen
    
    clear_screen()
    display_application_header("USER GUIDE")
    
    print("📖 ADVANCED IMAP MAIL FILTER - USER GUIDE")
    print("=" * 50)
    
    print("\n🎯 PURPOSE:")
    print("This application helps you automatically filter and manage spam emails")
    print("across multiple email accounts using advanced machine learning.")
    
    print("\n⚙️ CONFIGURATION MANAGEMENT:")
    print("• Set up email accounts (IMAP settings)")
    print("• Configure spam detection categories")
    print("• Manage custom keywords and filters")
    print("• Adjust ML classification settings")
    
    print("\n🎯 SINGLE ACCOUNT FILTERING:")
    print("• Process one email account at a time")
    print("• Preview mode to see what would be filtered")
    print("• Live processing with real-time feedback")
    
    print("\n🤖 BATCH PROCESSING:")
    print("• Process all configured accounts automatically")
    print("• Efficient bulk processing")
    print("• Automated scheduling options")
    
    print("\n📧 EMAIL ACTION VIEWER:")
    print("• Review filtered email history")
    print("• Export processing reports")
    print("• Analyze filtering patterns")
    
    print("\n🛡️ SAFETY FEATURES:")
    print("• Preview mode before actual processing")
    print("• Whitelist protection for important domains")
    print("• Detailed logging and audit trail")
    print("• Backup and restore capabilities")
    
    print("\n💡 TIPS:")
    print("• Start with preview mode to understand the system")
    print("• Regularly review and update your custom keywords")
    print("• Use the whitelist to protect important senders")
    print("• Monitor the analytics to optimize performance")
    
    input("\nPress Enter to return to menu...")


def show_about():
    """Display application information"""
    from utils import display_application_header
    
    display_application_header("ABOUT")
    print("🛡️ ADVANCED IMAP MAIL FILTER - DATABASE EDITION")
    print("=" * 50)
    print("Version: Database Edition")
    print("Machine Learning: Ensemble Classification")
    print("Accuracy: 95.6%+ spam detection")
    print("Storage: SQLite database architecture")
    print("Support: Multi-account IMAP processing")


def display_processing_summary(total_deleted, total_preserved, total_validated, total_legitimate,
                             total_processed, account_name=None, preview_mode=False):
    """Display processing results summary"""
    print("\n" + "="*80)
    if account_name:
        mode_text = "PREVIEW" if preview_mode else "PROCESSING"
        print(f"📊 {mode_text} SUMMARY FOR: {account_name}")
    else:
        mode_text = "PREVIEW" if preview_mode else "PROCESSING"
        print(f"📊 {mode_text} SUMMARY")
    print("="*80)
    
    print(f"📧 Total Processed: {total_processed}")
    print(f"🗑️  Spam Deleted: {total_deleted}")
    print(f"✅ Legitimate Preserved: {total_preserved}")
    print(f"🔍 Domain Validated: {total_validated}")
    print(f"🛡️  Whitelisted Protected: {total_legitimate}")
    
    if total_processed > 0:
        spam_rate = (total_deleted / total_processed) * 100
        preservation_rate = (total_preserved / total_processed) * 100
        print(f"📈 Spam Detection Rate: {spam_rate:.1f}%")
        print(f"🛡️  Preservation Rate: {preservation_rate:.1f}%")
    
    print("="*80)