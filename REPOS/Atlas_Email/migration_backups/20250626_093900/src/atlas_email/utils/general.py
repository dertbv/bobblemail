#!/usr/bin/env python3
"""
Utility Functions and Common Error Handling
Centralized utilities to reduce code duplication
"""

import os
import json
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from config.constants import ESCAPE_KEYS, CONFIRMATION_KEYWORDS, STRICT_CONFIRMATION_KEYWORD
import sys


def safe_file_operation(operation: str, file_path: str, data: Any = None, 
                       encoding: str = 'utf-8') -> Tuple[bool, Any]:
    """
    Safely perform file operations with consistent error handling
    
    Args:
        operation: 'read', 'write', 'append', 'delete'
        file_path: Path to the file
        data: Data to write (for write/append operations)
        encoding: File encoding
    
    Returns:
        Tuple of (success: bool, result: Any)
    """
    try:
        if operation == 'read':
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            with open(file_path, 'r', encoding=encoding) as f:
                if file_path.endswith('.json'):
                    return True, json.load(f)
                else:
                    return True, f.read()
                    
        elif operation == 'write':
            # Only create directories if file path contains directories
            dirname = os.path.dirname(file_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(file_path, 'w', encoding=encoding) as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2)
                else:
                    f.write(str(data))
            return True, None
            
        elif operation == 'append':
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(str(data))
            return True, None
            
        elif operation == 'delete':
            if os.path.exists(file_path):
                os.remove(file_path)
            return True, None
            
        else:
            return False, f"Unknown operation: {operation}"
            
    except Exception as e:
        error_msg = f"File operation '{operation}' failed for {file_path}: {e}"
        return False, error_msg


def safe_json_load(file_path: str, default_value: Any = None) -> Any:
    """
    Safely load JSON file with fallback to default value
    
    Args:
        file_path: Path to JSON file
        default_value: Value to return if loading fails
    
    Returns:
        Loaded data or default value
    """
    success, result = safe_file_operation('read', file_path)
    if success:
        return result
    else:
        return default_value


def safe_json_save(file_path: str, data: Any) -> bool:
    """
    Safely save data to JSON file
    
    Args:
        file_path: Path to JSON file
        data: Data to save
    
    Returns:
        True if successful, False otherwise
    """
    success, _ = safe_file_operation('write', file_path, data)
    return success


def handle_keyboard_interrupt(operation_name: str = "operation") -> None:
    """
    Consistent handling of keyboard interrupts
    
    Args:
        operation_name: Name of the operation being interrupted
    """
    print(f"\n⚠️  {operation_name.capitalize()} interrupted by user")
    print("👋 Goodbye!")


def clear_screen():
    """Clear the terminal screen for a cleaner interface"""
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')


def display_application_header(menu_title: str = None):
    """
    Display the standardized application header with status info
    
    Args:
        menu_title: Optional menu title to display below header
    """
    try:
        # Import here to avoid circular imports
        from atlas_email.models.database import db
        from config.credentials import db_credentials
        
        # Get account count from database
        accounts = db_credentials.load_credentials()
        account_count = len(accounts) if accounts else 0

        # Get filter count
        from config.loader import get_filters
        filters = get_filters()
        filter_count = len(filters)

        # Get database stats for enhanced status
        db_stats = db.get_database_stats()
        recent_sessions = db_stats.get('sessions_last_7d', 0)
        recent_logs = db_stats.get('logs_last_24h', 0)
        
        # Get timer status
        timer_status = "Inactive"
        try:
            from atlas_email.cli.main import auto_timer
            if auto_timer and auto_timer.is_timer_active():
                timer_status = auto_timer.get_timer_status()
        except:
            # Handle case where auto_timer might not be available
            pass
        
        print("\n" + "=" * 80)
        print("🛡️  ADVANCED IMAP MAIL FILTER - DATABASE EDITION")
        print("=" * 80)
        print(f"📊 Status: {account_count} accounts | {filter_count} filter terms | {recent_sessions} sessions (7d)")
        print(f"💾 Database: {db_stats['db_size_mb']:.1f}MB | {format_number(recent_logs)} logs (24h)")
        print(f"⏰ Auto Timer: {timer_status}")
        
        if menu_title:
            print()
            print(f"📋 {menu_title.upper()}:")
        print()
            
    except Exception as e:
        # Fallback header if database access fails
        print("\n" + "=" * 80)
        print("🛡️  ADVANCED IMAP MAIL FILTER - DATABASE EDITION")
        print("=" * 80)
        if menu_title:
            print()
            print(f"📋 {menu_title.upper()}:")
        print()


def show_status_and_refresh(message: str, pause_time: float = 1.5):
    """Show a status message briefly, then clear and refresh"""
    print(f"\n{message}")
    import time
    time.sleep(pause_time)
    clear_screen()


def handle_unexpected_error(error: Exception, operation_name: str = "operation", 
                          include_traceback: bool = False) -> None:
    """
    Consistent handling of unexpected errors
    
    Args:
        error: The exception that occurred
        operation_name: Name of the operation that failed
        include_traceback: Whether to include full traceback
    """
    print(f"\n❌ Unexpected error during {operation_name}: {error}")
    
    if include_traceback:
        print(f"Full traceback:")
        traceback.print_exc()


def get_single_key() -> Optional[str]:
    """
    Get a single key press without requiring Enter
    Cross-platform implementation with error handling
    
    Returns:
        The pressed key or None if error occurred
    """
    try:
        # Windows
        import msvcrt
        return msvcrt.getch().decode('utf-8')
    except ImportError:
        try:
            # Unix/Linux/Mac
            import tty
            import termios
            import sys

            # Check if stdin is a tty (interactive terminal)
            if not sys.stdin.isatty():
                return None
                
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (OSError, termios.error, Exception) as e:
            # Specific handling for terminal operation errors
            if "Inappropriate ioctl for device" in str(e) or "Operation not supported" in str(e):
                return None
            return None
    except Exception:
        return None


def get_user_choice(prompt: str, valid_choices: List[str], 
                   allow_escape: bool = True, allow_enter: bool = False) -> Optional[str]:
    """
    Get user choice with consistent error handling and escape options
    
    Args:
        prompt: Prompt to display to user
        valid_choices: List of valid choice strings
        allow_escape: Whether to allow escape keys
        allow_enter: Whether to allow Enter key to exit/return
    
    Returns:
        User's choice or None if cancelled/escaped
    """
    # Check if we should use regular input from the start
    import sys
    use_regular_input = not sys.stdin.isatty()
    
    while True:
        try:
            if not use_regular_input:
                # Try single key input
                print(f"{prompt} ", end="", flush=True)
                key = get_single_key()
                
                if key is None:
                    # Single key input failed, switch to regular input permanently
                    use_regular_input = True
                    print("\n🔄 Switching to regular input mode...")
                    continue
                    
                print(key)  # Echo the key pressed

                if key in valid_choices:
                    return key
                elif allow_escape and key in ESCAPE_KEYS:
                    return None
                elif allow_enter and key in ['\n', '\r']:
                    return None
                else:
                    valid_str = "', '".join(valid_choices)
                    escape_msg = " or Escape" if allow_escape else ""
                    enter_msg = " or Enter" if allow_enter else ""
                    print(f"❌ Invalid key '{key}'. Please press '{valid_str}'{escape_msg}{enter_msg}.")
            else:
                # Use regular input
                try:
                    choice = input(f"{prompt} ").strip()
                    
                    if choice in valid_choices:
                        return choice
                    elif allow_escape and choice.lower() in ['q', 'quit', 'exit']:
                        return None
                    elif allow_enter and choice == '':
                        return None
                    else:
                        valid_str = "', '".join(valid_choices)
                        escape_msg = " or 'q' to quit" if allow_escape else ""
                        enter_msg = " or Enter to exit" if allow_enter else ""
                        print(f"❌ Invalid choice '{choice}'. Please enter: {valid_str}{escape_msg}{enter_msg}.")
                except EOFError:
                    # Handle end of input stream
                    if allow_escape:
                        return None
                    else:
                        raise
                
        except KeyboardInterrupt:
            if allow_escape:
                return None
            else:
                handle_keyboard_interrupt("input")
                raise
        except Exception as e:
            # Force switch to regular input on any error
            if not use_regular_input:
                use_regular_input = True
                print(f"\n🔄 Input error detected. Switching to regular input mode...")
                continue
            else:
                print(f"❌ Error reading input: {e}. Please try again.")


def get_confirmation(prompt: str, require_strict: bool = False) -> bool:
    """
    Get user confirmation with consistent handling
    
    Args:
        prompt: Confirmation prompt
        require_strict: Whether to require exact 'YES' for confirmation
    
    Returns:
        True if confirmed, False otherwise
    """
    try:
        response = input(prompt).strip()
        
        if require_strict:
            return response == STRICT_CONFIRMATION_KEYWORD
        else:
            return response.lower() in CONFIRMATION_KEYWORDS
            
    except KeyboardInterrupt:
        return False
    except Exception:
        return False


def format_number(number: int) -> str:
    """
    Format number with thousands separator
    
    Args:
        number: Number to format
    
    Returns:
        Formatted number string
    """
    return f"{number:,}"


def format_percentage(value: float, total: float) -> str:
    """
    Format percentage with consistent precision
    
    Args:
        value: Numerator value
        total: Denominator value
    
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0.0%"
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"


def format_elapsed_time(start_time: datetime) -> str:
    """
    Format elapsed time since start
    
    Args:
        start_time: Start datetime
    
    Returns:
        Formatted elapsed time string
    """
    elapsed = datetime.now() - start_time
    return format_duration_seconds(elapsed.total_seconds())


def format_duration_seconds(total_seconds: float) -> str:
    """
    Format duration in seconds to human-readable format
    
    Args:
        total_seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if total_seconds < 60:
        return f"{total_seconds:.1f} seconds"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_duration_minutes(minutes: int) -> str:
    """
    Format duration in minutes to human-readable format
    
    Args:
        minutes: Duration in minutes
    
    Returns:
        Formatted duration string (e.g., "1h 30m", "45m", "2h")
    """
    if minutes < 60:
        return f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes}m"


def format_time_remaining(end_time: datetime) -> str:
    """
    Format time remaining until a specific datetime
    
    Args:
        end_time: Target datetime
    
    Returns:
        Formatted time remaining string with emoji indicators
    """
    now = datetime.now()
    if end_time <= now:
        return "⏰ Expired"
    
    remaining = end_time - now
    total_seconds = remaining.total_seconds()
    
    if total_seconds < 60:
        return f"⏰ {int(total_seconds)}s"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"⏰ {minutes}:{seconds:02d}"
    else:
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"⏰ {hours}:{minutes:02d}:00"


def parse_user_time_input(user_input: str) -> Optional[int]:
    """
    Parse user-friendly time input into minutes
    
    Supports formats like:
    - "30m", "45 minutes", "1h", "2 hours", "1h30m", "90 minutes"
    - "1.5h" (converts to 90 minutes)
    - Plain numbers default to minutes: "30" = 30 minutes
    
    Args:
        user_input: User's time input string
    
    Returns:
        Number of minutes, or None if invalid
    """
    if not user_input:
        return None
    
    # Clean input
    input_str = user_input.strip().lower().replace(' ', '')
    
    # Handle plain numbers (default to minutes)
    if input_str.isdigit():
        minutes = int(input_str)
        return minutes if 1 <= minutes <= 10080 else None  # Max 1 week
    
    # Handle decimal hours (e.g., "1.5h")
    if 'h' in input_str and '.' in input_str:
        try:
            hours_str = input_str.replace('h', '').replace('hour', '').replace('hours', '')
            hours = float(hours_str)
            minutes = int(hours * 60)
            return minutes if 1 <= minutes <= 10080 else None
        except ValueError:
            pass
    
    # Handle combined formats (e.g., "1h30m")
    if 'h' in input_str and 'm' in input_str:
        try:
            parts = input_str.replace('hour', 'h').replace('minute', 'm').replace('hours', 'h').replace('minutes', 'm')
            h_pos = parts.find('h')
            m_pos = parts.find('m')
            
            hours = int(parts[:h_pos]) if h_pos > 0 else 0
            minutes_part = parts[h_pos+1:m_pos] if m_pos > h_pos+1 else '0'
            minutes = int(minutes_part) if minutes_part else 0
            
            total_minutes = hours * 60 + minutes
            return total_minutes if 1 <= total_minutes <= 10080 else None
        except ValueError:
            pass
    
    # Handle hours only (e.g., "2h", "3 hours")
    if 'h' in input_str or 'hour' in input_str:
        try:
            hours_str = input_str.replace('h', '').replace('hour', '').replace('hours', '')
            hours = int(hours_str)
            minutes = hours * 60
            return minutes if 1 <= minutes <= 10080 else None
        except ValueError:
            pass
    
    # Handle minutes only (e.g., "30m", "45 minutes")
    if 'm' in input_str or 'minute' in input_str:
        try:
            minutes_str = input_str.replace('m', '').replace('minute', '').replace('minutes', '')
            minutes = int(minutes_str)
            return minutes if 1 <= minutes <= 10080 else None
        except ValueError:
            pass
    
    return None


def get_user_time_input(prompt: str, max_minutes: int = 10080) -> Optional[int]:
    """
    Get time duration from user with helpful prompts and validation
    
    Args:
        prompt: Base prompt message
        max_minutes: Maximum allowed minutes (default: 1 week)
    
    Returns:
        Number of minutes, or None if cancelled
    """
    print(f"\n{prompt}")
    print("📝 Enter time in any of these formats:")
    print("   • Minutes: 30, 45m, 90 minutes")
    print("   • Hours: 1h, 2 hours, 1.5h")
    print("   • Combined: 1h30m, 2h15m")
    print("   • Enter 0 to clear/cancel")
    print()
    
    while True:
        try:
            user_input = input("⏰ Time: ").strip()
            
            if not user_input or user_input == '0':
                return 0
            
            minutes = parse_user_time_input(user_input)
            
            if minutes is None:
                print("❌ Invalid format. Try examples like: 30m, 1h, 1h30m, 90")
                continue
            
            if minutes == 0:
                return 0
            
            if minutes > max_minutes:
                max_formatted = format_duration_minutes(max_minutes)
                print(f"❌ Too long. Maximum allowed: {max_formatted}")
                continue
            
            # Show confirmation
            formatted = format_duration_minutes(minutes)
            print(f"✅ Set to {formatted} ({minutes} minutes)")
            return minutes
            
        except KeyboardInterrupt:
            return None
        except Exception:
            print("❌ Invalid input. Please try again.")


def parse_user_time_of_day(user_input: str) -> Optional[tuple]:
    """
    Parse user-friendly time of day input
    
    Supports formats like:
    - "14:30", "2:30pm", "2:30 PM", "14:30:00"
    - "2pm", "14", "midnight", "noon"
    
    Args:
        user_input: User's time input string
    
    Returns:
        Tuple of (hour, minute) or None if invalid
    """
    if not user_input:
        return None
    
    input_str = user_input.strip().lower().replace(' ', '')
    
    # Handle special cases
    if input_str in ['midnight', '12am']:
        return (0, 0)
    elif input_str in ['noon', '12pm']:
        return (12, 0)
    
    # Remove common separators and normalize
    input_str = input_str.replace(':', '').replace('.', '')
    
    # Handle AM/PM
    is_pm = 'pm' in input_str
    is_am = 'am' in input_str
    input_str = input_str.replace('pm', '').replace('am', '')
    
    try:
        # Parse different formats
        if len(input_str) == 1 or len(input_str) == 2:
            # "2", "14" format
            hour = int(input_str)
            minute = 0
        elif len(input_str) == 3:
            # "230" format (2:30)
            hour = int(input_str[0])
            minute = int(input_str[1:3])
        elif len(input_str) == 4:
            # "1430" or "0230" format
            hour = int(input_str[0:2])
            minute = int(input_str[2:4])
        elif len(input_str) == 6:
            # "143000" format (with seconds)
            hour = int(input_str[0:2])
            minute = int(input_str[2:4])
        else:
            return None
        
        # Handle AM/PM conversion
        if is_pm and hour != 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0
        
        # Validate
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
        else:
            return None
            
    except ValueError:
        return None


def get_user_time_of_day(prompt: str) -> Optional[tuple]:
    """
    Get time of day from user with helpful prompts and validation
    
    Args:
        prompt: Base prompt message
    
    Returns:
        Tuple of (hour, minute) or None if cancelled
    """
    print(f"\n{prompt}")
    print("📝 Enter time in any of these formats:")
    print("   • 24-hour: 14:30, 09:15, 23:45")
    print("   • 12-hour: 2:30pm, 9:15am, 11:45pm")
    print("   • Short: 2pm, 9am, 14, noon, midnight")
    print()
    
    while True:
        try:
            user_input = input("🕐 Time: ").strip()
            
            if not user_input:
                return None
            
            result = parse_user_time_of_day(user_input)
            
            if result is None:
                print("❌ Invalid format. Try examples like: 14:30, 2:30pm, 9am")
                continue
            
            hour, minute = result
            
            # Show confirmation with both formats
            time_24 = f"{hour:02d}:{minute:02d}"
            if hour == 0:
                time_12 = f"12:{minute:02d} AM"
            elif hour < 12:
                time_12 = f"{hour}:{minute:02d} AM"
            elif hour == 12:
                time_12 = f"12:{minute:02d} PM"
            else:
                time_12 = f"{hour-12}:{minute:02d} PM"
            
            print(f"✅ Set to {time_24} ({time_12})")
            return (hour, minute)
            
        except KeyboardInterrupt:
            return None
        except Exception:
            print("❌ Invalid input. Please try again.")


def format_eta(processed: int, total: int, elapsed_seconds: float) -> str:
    """
    Calculate and format estimated time of arrival
    
    Args:
        processed: Number of items processed
        total: Total number of items
        elapsed_seconds: Elapsed time in seconds
    
    Returns:
        Formatted ETA string
    """
    if processed == 0 or elapsed_seconds == 0:
        return "calculating..."
    
    rate = processed / elapsed_seconds
    remaining = total - processed
    
    if rate == 0:
        return "calculating..."
    
    eta_seconds = remaining / rate
    
    if eta_seconds < 60:
        return f"ETA: {int(eta_seconds)}s"
    elif eta_seconds < 3600:
        minutes = int(eta_seconds // 60)
        seconds = int(eta_seconds % 60)
        return f"ETA: {minutes}m{seconds}s"
    else:
        hours = int(eta_seconds // 3600)
        minutes = int((eta_seconds % 3600) // 60)
        return f"ETA: {hours}h{minutes}m"


def clean_email_header(raw_header: str, max_length: int = 200) -> str:
    """
    Clean and truncate email header for safe display
    
    Args:
        raw_header: Raw header string
        max_length: Maximum length to truncate to
    
    Returns:
        Cleaned header string
    """
    if not raw_header:
        return ""
    
    # Remove newlines and excessive whitespace
    cleaned = ' '.join(raw_header.replace('\n', ' ').replace('\r', ' ').split())
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned


def validate_email_address(email: str) -> bool:
    """
    Basic email address validation
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid format, False otherwise
    """
    if not email or '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local, domain = parts
    if not local or not domain:
        return False
    
    if '.' not in domain:
        return False
    
    return True


def validate_uid(uid: str) -> bool:
    """
    Validate IMAP UID format
    
    Args:
        uid: UID string to validate
    
    Returns:
        True if valid UID, False otherwise
    """
    try:
        uid_num = int(uid)
        return 1 <= uid_num <= 999999999
    except (ValueError, TypeError):
        return False


def create_backup_filename(original_path: str) -> str:
    """
    Create a backup filename with timestamp
    
    Args:
        original_path: Original file path
    
    Returns:
        Backup filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base, ext = os.path.splitext(original_path)
    return f"{base}.backup.{timestamp}{ext}"


def ensure_directory_exists(file_path: str) -> bool:
    """
    Ensure the directory for a file path exists
    
    Args:
        file_path: File path to check
    
    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return True
    except Exception:
        return False


# Export all utility functions
__all__ = [
    'safe_file_operation',
    'safe_json_load', 
    'safe_json_save',
    'handle_keyboard_interrupt',
    'handle_unexpected_error',
    'get_single_key',
    'get_user_choice',
    'get_confirmation',
    'format_number',
    'format_percentage', 
    'format_elapsed_time',
    'format_duration_seconds',
    'format_duration_minutes',
    'format_time_remaining',
    'parse_user_time_input',
    'get_user_time_input',
    'parse_user_time_of_day',
    'get_user_time_of_day',
    'format_eta',
    'clean_email_header',
    'validate_email_address',
    'validate_uid',
    'create_backup_filename',
    'ensure_directory_exists'
]