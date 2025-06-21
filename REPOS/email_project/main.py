#!/usr/bin/env python3
"""
Advanced IMAP Mail Filter with ML Domain Validation - Database Edition
Enhanced with database storage, logging, and analytics
Updated to use database architecture for all data storage
Refactored with modular architecture: MenuHandler, ProcessingController, ConfigurationManager
"""

import sys
from db_logger import logger, LogCategory
from utils import clear_screen

# Import the new modular components
from menu_handler import display_main_menu, get_menu_choice
from processing_controller import single_account_filtering, batch_processing, email_action_viewer
from configuration_manager import initialize_application, initialize_auto_timer, configuration_management, help_documentation


# Global timer instance for automated batch processing
auto_timer = None


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