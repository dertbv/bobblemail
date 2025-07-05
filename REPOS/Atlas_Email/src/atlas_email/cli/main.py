#!/usr/bin/env python3
"""
Advanced IMAP Mail Filter with ML Domain Validation - Database Edition
Enhanced with database storage, logging, and analytics
Updated to use database architecture for all data storage
Refactored with modular architecture: MenuHandler, ProcessingController, ConfigurationManager
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path for package imports
src_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_root))

from atlas_email.models.db_logger import logger, LogCategory
from atlas_email.utils.general import clear_screen
from atlas_email.models.database import db

# Import the new modular components
from atlas_email.cli.menu_handler import display_main_menu, get_menu_choice
from atlas_email.core.processing_controller import single_account_filtering, batch_processing, email_action_viewer
from config.manager import initialize_application, initialize_auto_timer, configuration_management, help_documentation


# Global timer instance for automated batch processing
auto_timer = None


def cleanup_duplicates_command():
    """Execute the cleanup duplicates command"""
    try:
        print("🔍 Checking for duplicate emails...")
        deleted_count = db.cleanup_duplicates()
        
        if deleted_count > 0:
            print(f"✅ Cleaned up {deleted_count} duplicate entries")
        else:
            print("✅ No duplicates found")
        
        return 0  # Success
    except Exception as e:
        print(f"❌ Error cleaning up duplicates: {e}")
        return 1  # Error


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Atlas Email - Advanced IMAP Mail Filter with ML Domain Validation"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add cleanup-duplicates command
    subparsers.add_parser(
        'cleanup-duplicates', 
        help='Clean up duplicate email entries from the database'
    )
    
    return parser.parse_args()


def main():
    """Main application entry point"""
    global auto_timer
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle specific commands
    if args.command == 'cleanup-duplicates':
        return cleanup_duplicates_command()
    
    # If no command specified, run the interactive menu
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
            elif choice == 6:
                clear_screen()
                # Import and run web app management
                try:
                    from atlas_email.api.app_manager import web_app_management_menu
                    web_app_management_menu()
                except ImportError as e:
                    print("❌ Web app management requires FastAPI dependencies")
                    print("💡 Install with: pip install fastapi uvicorn")
                    print(f"📝 Error details: {e}")
                    input("\nPress Enter to continue...")
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
    sys.exit(main())