#!/usr/bin/env python3
"""
Configuration and Authentication Module - Enhanced with Provider Detection
Handles configuration files, credential management, and IMAP server settings.
"""

import os
import json
import imaplib
import ssl
import getpass
from datetime import datetime

# Import centralized constants and utilities
from config.constants import (
    BASE_DIR, CONFIG_FILE, LOG_FILE, CREDS_FILE, ANALYTICS_OUTPUT, JSON_OUTPUT,
    PROVIDER_CONFIGS, DEFAULT_PROVIDER_CONFIG, ESCAPE_KEYS, CONFIRMATION_KEYWORDS
)
from atlas_email.utils.general import get_single_key, get_user_choice, safe_json_load, safe_json_save
from atlas_email.utils.provider_utils import ProviderDetector, ProviderOptimizer

# Use centralized utility functions
get_single_choice = get_user_choice

# IMAP server configurations with provider-specific settings
IMAP_SERVERS = {
    "icloud": {
        "host": "imap.mail.me.com", 
        "port": 993,
        "requires_app_password": True,
        "deletion_strategy": "bulk_only",
        "batch_size": 25,
        "supports_individual_uid": False
    },
    "gmail": {
        "host": "imap.gmail.com", 
        "port": 993,
        "requires_app_password": True,
        "deletion_strategy": "standard",
        "batch_size": 50,
        "supports_individual_uid": True
    },
    "outlook": {
        "host": "outlook.office365.com", 
        "port": 993,
        "requires_app_password": False,
        "deletion_strategy": "standard",
        "batch_size": 30,
        "supports_individual_uid": True
    },
    "yahoo": {
        "host": "imap.mail.yahoo.com", 
        "port": 993,
        "requires_app_password": True,
        "deletion_strategy": "standard",
        "batch_size": 40,
        "supports_individual_uid": True
    },
    "aol": {
        "host": "imap.aol.com", 
        "port": 993,
        "requires_app_password": False,
        "deletion_strategy": "standard",
        "batch_size": 30,
        "supports_individual_uid": True
    },
    "custom": {
        "host": "", 
        "port": 993,
        "requires_app_password": False,
        "deletion_strategy": "standard",
        "batch_size": 25,
        "supports_individual_uid": True
    }
}

# ============================================================================
# PROVIDER DETECTION UTILITIES
# ============================================================================

# Use centralized provider detection functions
detect_provider_from_email = ProviderDetector.detect_provider_from_email
get_provider_config = ProviderDetector.get_provider_config
get_provider_deletion_notes = ProviderDetector.get_optimization_notes

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def write_log(message, print_to_screen=True):
    """DEPRECATED: Legacy function - redirects to database logger"""
    # Import here to avoid circular imports
    from atlas_email.models.db_logger import write_log as db_write_log
    return db_write_log(message, print_to_screen)

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

def create_config_file():
    """Create blank configuration file with instructions"""
    sample_config = """# Mail Filter Keywords File
# Lines starting with # are comments and will be ignored
# Use [FILTERS] section for all keywords and sender patterns
#
# IMPORTANT: This system now uses a database for built-in spam keywords.
# This file is for your CUSTOM keywords only.
#
# Add your own custom filter terms below:
# - Email addresses or domains you want to filter
# - Specific keywords for your use case
# - Custom sender patterns
#
# The system already includes comprehensive built-in spam detection,
# so you typically only need to add specific terms for your needs.

[FILTERS]
# Add your custom keywords below (one per line)
# Example:
# unwanted-sender@example.com
# specific-promotional-term
# custom-filter-keyword

"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(sample_config)
    print(f"✅ Blank keywords file created at: {CONFIG_FILE}")
    print("📝 This file is for your CUSTOM keywords only.")
    print("📊 The system includes comprehensive built-in spam detection.")
    print("✏️  Edit this file to add any custom filter terms, then run the script again.")
    return False

def parse_config_file():
    """Parse keywords file and return filter list"""
    if not os.path.exists(CONFIG_FILE):
        return create_config_file()
    
    filters = []
    current_section = None
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line == '[FILTERS]':
                    current_section = 'filters'
                elif current_section == 'filters':
                    if line:  # Only add non-empty lines
                        filters.append(line.lower())
                else:
                    # Handle potential configuration sections in the future
                    pass
    except Exception as e:
        print(f"Error reading keywords file: {e}")
        return []
    
    return filters

def validate_config(filters):
    """Validate configuration settings"""
    if not filters:
        print("ℹ️ No custom filter terms found - using built-in spam detection only.")
        print("💡 This is normal! The system has comprehensive built-in spam detection.")
        return True  # Empty filter list is now valid since system has built-in detection
    
    if len(filters) > 100:
        print("Warning: Large number of filters may impact performance.")
    
    # Check for potentially problematic patterns
    problematic = []
    for f in filters:
        if len(f) < 2:
            problematic.append(f"Filter too short: '{f}'")
        elif f.count('*') > 3:
            problematic.append(f"Too many wildcards: '{f}'")
    
    if problematic:
        print("Configuration warnings:")
        for warning in problematic[:5]:  # Show max 5 warnings
            print(f"  - {warning}")
        if len(problematic) > 5:
            print(f"  ... and {len(problematic) - 5} more warnings")
    
    return True

# ============================================================================
# CREDENTIAL MANAGEMENT
# ============================================================================

class CredentialManager:
    """Secure credential management for email accounts with provider detection"""
    
    def __init__(self, creds_file=CREDS_FILE):
        self.creds_file = creds_file
    
    def save_credentials(self, account):
        """Save account credentials to file with provider detection and optimization settings"""
        creds = self.load_credentials()
        
        # Detect provider if not already set
        if 'provider' not in account or account['provider'] == 'custom':
            detected_provider = detect_provider_from_email(account.get('email_address', ''))
            if detected_provider != 'custom':
                account['provider'] = detected_provider
                provider_config = get_provider_config(detected_provider)
                account['host'] = provider_config['host']
                account['port'] = provider_config['port']
                write_log(f"Auto-detected provider: {detected_provider} for {account['email_address']}", True)
        
        # Remove existing entry for this email
        creds = [c for c in creds if c.get("email_address") != account["email_address"]]
        
        # Add new/updated entry with timestamp
        account["last_used"] = datetime.now().isoformat()
        
        # Ensure folder preferences and provider settings exist
        if "target_folders" not in account:
            account["target_folders"] = []
        if "folder_setup_complete" not in account:
            account["folder_setup_complete"] = False
        if "provider_optimizations" not in account:
            provider_config = get_provider_config(account.get('provider', 'custom'))
            account["provider_optimizations"] = {
                "deletion_strategy": provider_config.get('deletion_strategy', 'standard'),
                "batch_size": provider_config.get('batch_size', 25),
                "supports_individual_uid": provider_config.get('supports_individual_uid', True)
            }
            
        creds.append(account)
        
        try:
            with open(self.creds_file, "w", encoding='utf-8') as f:
                json.dump(creds, f, indent=2)
            print(f"✅ Credentials saved for {account['email_address']} ({account.get('provider', 'custom')})")
            return True
        except Exception as e:
            print(f"❌ Failed to save credentials: {e}")
            return False
    
    def update_folder_preferences(self, email_address, target_folders):
        """Update folder preferences for a specific account"""
        creds = self.load_credentials()
        
        for account in creds:
            if account.get("email_address") == email_address:
                account["target_folders"] = target_folders
                account["folder_setup_complete"] = True
                account["folder_last_updated"] = datetime.now().isoformat()
                break
        else:
            print(f"❌ Account {email_address} not found")
            return False
        
        try:
            with open(self.creds_file, "w", encoding='utf-8') as f:
                json.dump(creds, f, indent=2)
            print(f"✅ Folder preferences updated for {email_address}")
            return True
        except Exception as e:
            print(f"❌ Failed to update folder preferences: {e}")
            return False
    
    def load_credentials(self):
        """Load saved credentials with provider migration"""
        if not os.path.exists(self.creds_file):
            return []
        
        try:
            with open(self.creds_file, "r", encoding='utf-8') as f:
                creds = json.load(f)
            
            # Ensure all entries are valid dictionaries
            creds = [c for c in creds if isinstance(c, dict) and 'email_address' in c]
            
            # Migrate old accounts without provider detection
            migration_needed = False
            for account in creds:
                if 'provider' not in account or account['provider'] == 'unknown':
                    detected_provider = detect_provider_from_email(account.get('email_address', ''))
                    account['provider'] = detected_provider
                    provider_config = get_provider_config(detected_provider)
                    
                    # Update host/port if they match default settings or are missing
                    if 'host' not in account or account['host'] in [config['host'] for config in IMAP_SERVERS.values()]:
                        account['host'] = provider_config['host']
                        account['port'] = provider_config['port']
                    
                    # Add provider optimizations
                    if "provider_optimizations" not in account:
                        account["provider_optimizations"] = {
                            "deletion_strategy": provider_config.get('deletion_strategy', 'standard'),
                            "batch_size": provider_config.get('batch_size', 25),
                            "supports_individual_uid": provider_config.get('supports_individual_uid', True)
                        }
                    
                    migration_needed = True
                    write_log(f"Migrated account {account['email_address']} to provider: {detected_provider}", False)
            
            # Save migrated data
            if migration_needed:
                try:
                    with open(self.creds_file, "w", encoding='utf-8') as f:
                        json.dump(creds, f, indent=2)
                    write_log("Provider migration completed for saved accounts", False)
                except Exception as e:
                    write_log(f"Failed to save provider migration: {e}", False)
            
            return creds
        except Exception as e:
            print(f"Failed to load credentials: {e}")
            return []
    
    def select_account(self):
        """Interactive account selection with provider information"""
        creds = self.load_credentials()
        if not creds:
            print("No saved accounts found.")
            return None
        
        print("\n📧 SAVED ACCOUNTS:")
        print("-" * 60)
        for idx, c in enumerate(creds):
            try:
                provider = c.get('provider', 'custom')
                provider_emoji = {
                    'icloud': '🍎',
                    'gmail': '📧', 
                    'outlook': '🏢',
                    'yahoo': '📮',
                    'aol': '📧',
                    'custom': '🔧'
                }.get(provider, '🔧')
                
                last_used = ""
                if 'last_used' in c:
                    try:
                        last_date = datetime.fromisoformat(c['last_used'])
                        last_used = f" (last used: {last_date.strftime('%Y-%m-%d')})"
                    except:
                        pass
                
                optimization_note = ""
                if provider == 'icloud':
                    optimization_note = " [Optimized]"
                
                print(f"{idx+1}. {provider_emoji} {c['email_address']} ({provider}){optimization_note}{last_used}")
            except Exception:
                continue
        
        print(f"{len(creds)+1}. ➕ Add new account")
        print(f"{len(creds)+2}. ❌ Cancel/Exit")
        print("-" * 60)
        
        # Create valid choices dynamically
        valid_choices = [str(i) for i in range(1, len(creds) + 3)]
        
        choice = get_single_choice(f"Press a key (1-{len(creds)+2}):", valid_choices)
        if choice is None:
            return "exit"
        
        idx = int(choice) - 1
        if idx == len(creds):
            return None  # Add new account
        elif idx == len(creds) + 1:
            return "exit"  # Cancel/Exit
        elif 0 <= idx < len(creds):
            selected_account = creds[idx]
            # Show provider-specific info
            provider = selected_account.get('provider', 'custom')
            if provider in ['icloud', 'gmail', 'outlook']:
                notes = get_provider_deletion_notes(provider)
                print(f"\n📋 {provider.upper()} ACCOUNT NOTES:")
                for note in notes:
                    print(f"   {note}")
                print()
            return selected_account
        else:
            return "exit"
    
    def delete_account(self, email_address):
        """Delete saved account credentials"""
        creds = self.load_credentials()
        original_count = len(creds)
        creds = [c for c in creds if c.get("email_address") != email_address]
        
        if len(creds) < original_count:
            try:
                with open(self.creds_file, "w", encoding='utf-8') as f:
                    json.dump(creds, f, indent=2)
                print(f"✅ Deleted credentials for {email_address}")
                return True
            except Exception as e:
                print(f"❌ Failed to delete credentials: {e}")
                return False
        else:
            print(f"❌ Account {email_address} not found")
            return False

# ============================================================================
# IMAP CONNECTION MANAGEMENT
# ============================================================================

class IMAPConnectionManager:
    """Manages IMAP connections with provider-specific optimization"""
    
    def __init__(self, credential_manager=None):
        self.credential_manager = credential_manager or CredentialManager()
        self.connection = None
        self.current_account = None
    
    def connect_to_imap(self, account=None, quiet_mode=False):
        """Establish IMAP connection with provider-specific optimization"""
        if account:
            return self._connect_with_account(account, quiet_mode)
        else:
            return self._interactive_connect()
    
    def _connect_with_account(self, account, quiet_mode=False):
        """Connect using provided account details with provider detection"""
        try:
            # Ensure provider is detected
            if 'provider' not in account:
                account['provider'] = detect_provider_from_email(account.get('email_address', ''))
            
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(account["host"], account["port"], ssl_context=context)
            mail.login(account["email_address"], account["password"])
            
            provider = account.get('provider', 'custom')
            provider_emoji = {
                'icloud': '🍎',
                'gmail': '📧', 
                'outlook': '🏢',
                'yahoo': '📮',
                'aol': '📧',
                'custom': '🔧'
            }.get(provider, '🔧')
            
            write_log(f"✅ Connected to {account['email_address']} ({provider})")
            if not quiet_mode:
                print(f"{provider_emoji} Connected to {provider.upper()} account")
                
                # Show provider-specific optimization notes
                if provider == 'icloud':
                    print("🍎 Using iCloud-optimized deletion strategy")
                elif provider in ['gmail', 'outlook', 'yahoo']:
                    print(f"⚡ Using {provider} standard operations")
            
            self.connection = mail
            self.current_account = account
            return mail
            
        except imaplib.IMAP4.error as e:
            print(f"❌ IMAP authentication failed for {account['email_address']}: {e}")
            
            # Provider-specific troubleshooting hints
            provider = account.get('provider', 'custom')
            if provider == 'gmail' and 'authentication failed' in str(e).lower():
                print("💡 Gmail Tip: Make sure you're using an app-specific password, not your regular Gmail password")
                print("   Generate one at: https://myaccount.google.com/apppasswords")
            elif provider == 'icloud':
                print("💡 iCloud Tip: Make sure you're using an app-specific password")
                print("   Generate one in your Apple ID settings")
                
            return None
        except Exception as e:
            print(f"❌ Connection failed for {account['email_address']}: {e}")
            return None
    
    def _interactive_connect(self):
        """Interactive connection setup with provider detection"""
        # Check for saved accounts
        selected_account = self.credential_manager.select_account()
        
        if selected_account == "exit":
            print("👋 Cancelled by user")
            return None
        elif selected_account:
            mail = self._connect_with_account(selected_account)
            if mail:
                return mail
            else:
                print("Failed to connect with saved credentials. Let's try manual setup.")
        
        # Manual setup
        return self._manual_setup()
    
    def _manual_setup(self):
        """Manual IMAP setup process with provider detection"""
        print("\n🔧 MANUAL IMAP SETUP")
        print("=" * 30)
        
        # Get email address first for auto-detection
        email_address = input("Enter your email address: ").strip()
        detected_provider = detect_provider_from_email(email_address)
        
        print(f"\n🔍 Detected provider: {detected_provider.upper()}")
        
        # Provider selection with auto-detection
        providers = list(IMAP_SERVERS.keys())
        print("Select your email provider:")
        
        default_idx = None
        for i, provider in enumerate(providers):
            marker = " [DETECTED]" if provider == detected_provider else ""
            print(f"{i + 1}. {provider.capitalize()}{marker}")
            if provider == detected_provider:
                default_idx = i + 1
        
        while True:
            prompt = f"Enter number (1-{len(providers)})"
            if default_idx:
                prompt += f" [press Enter for {default_idx}]"
            prompt += ": "
            
            choice = input(prompt).strip()
            
            if not choice and default_idx:
                provider = providers[default_idx - 1]
                break
            
            try:
                provider = providers[int(choice) - 1]
                break
            except (ValueError, IndexError):
                print("Invalid choice. Please try again.")
        
        # Server configuration
        server_info = IMAP_SERVERS[provider]
        if provider == "custom":
            host = input("Enter IMAP server address: ").strip()
            while True:
                port_input = input("Enter IMAP port (default 993): ").strip()
                try:
                    port = int(port_input) if port_input else 993
                    break
                except ValueError:
                    print("Please enter a valid port number.")
        else:
            host = server_info["host"]
            port = server_info["port"]
            print(f"Using {provider} server: {host}:{port}")
        
        # Provider-specific setup instructions
        if provider == "gmail":
            print("\n📝 GMAIL SETUP INSTRUCTIONS:")
            print("For Gmail, you MUST use an app-specific password:")
            print("1. Go to: https://myaccount.google.com/apppasswords")
            print("2. Generate a new app password for 'Mail'")
            print("3. Use that 16-character password below (not your regular Gmail password)")
            print("4. Enable 2-Factor Authentication if not already enabled")
            print("")
        elif provider == "icloud":
            print("\n📝 ICLOUD SETUP INSTRUCTIONS:")
            print("For iCloud, you MUST use an app-specific password:")
            print("1. Go to: https://appleid.apple.com/account/manage")
            print("2. Sign in and go to 'Security' section")
            print("3. Generate an app-specific password for 'Mail'")
            print("4. Use that password below (not your regular Apple ID password)")
            print("")
        elif provider == "yahoo":
            print("\n📝 YAHOO SETUP INSTRUCTIONS:")
            print("For Yahoo, you may need an app password:")
            print("1. Go to Yahoo Account Security")
            print("2. Generate an app password if regular password fails")
            print("3. Enable 'Less secure app access' if needed")
            print("")
        
        password = getpass.getpass("Enter your password (or app-specific password): ")
        
        # Test connection
        account = {
            "provider": provider,
            "email_address": email_address,
            "password": password,
            "host": host,
            "port": port
        }
        
        print(f"Testing connection to {provider} server...")
        mail = self._connect_with_account(account)
        
        if mail:
            # Show provider optimization info
            provider_config = get_provider_config(provider)
            print(f"\n✅ Connection successful!")
            print(f"📊 Provider: {provider.upper()}")
            print(f"🔧 Deletion Strategy: {provider_config.get('deletion_strategy', 'standard')}")
            print(f"📦 Batch Size: {provider_config.get('batch_size', 25)}")
            
            if provider == 'icloud':
                print("🍎 iCloud optimizations will be applied automatically")
            
            # Offer to save credentials
            save = input("\nSave credentials for future use? (yes/no): ").strip().lower()
            if save in ('yes', 'y'):
                self.credential_manager.save_credentials(account)
            return mail
        else:
            print(f"\n❌ Connection failed")
            if provider in ['gmail', 'icloud', 'yahoo'] and server_info.get('requires_app_password'):
                print(f"💡 Make sure you're using an app-specific password for {provider}")
            return None
    
    def disconnect(self):
        """Safely disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.logout()
                if self.current_account:
                    provider = self.current_account.get('provider', 'unknown')
                    write_log(f"Disconnected from {provider} server")
                else:
                    write_log("Disconnected from IMAP server")
            except:
                pass
            finally:
                self.connection = None
                self.current_account = None
    
    def test_connection(self, account):
        """Test IMAP connection without saving"""
        try:
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(account["host"], account["port"], ssl_context=context)
            mail.login(account["email_address"], account["password"])
            mail.logout()
            return True
        except Exception:
            return False

# ============================================================================
# DEPENDENCY CHECKER
# ============================================================================

def check_dependencies():
    """Check for required Python packages"""
    missing_packages = []
    optional_packages = []
    
    # Required packages
    try:
        import tldextract
    except ImportError:
        missing_packages.append("tldextract")
    
    # Optional packages
    try:
        import whois
    except ImportError:
        optional_packages.append("python-whois")
    
    if missing_packages:
        print("❌ MISSING REQUIRED PACKAGES:")
        for pkg in missing_packages:
            print(f"   pip install {pkg}")
        return False
    
    if optional_packages:
        print("⚠️  OPTIONAL PACKAGES (recommended):")
        for pkg in optional_packages:
            print(f"   pip install {pkg}")
        print("   (Domain age validation will be limited without python-whois)")
    
    return True

# ============================================================================
# CONFIGURATION VALIDATION AND SETUP
# ============================================================================

class ConfigurationManager:
    """Comprehensive configuration management with provider awareness"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.filters = []
        self.settings = {}
    
    def initialize(self):
        """Initialize configuration system"""
        # print("🔧 Initializing Mail Filter Configuration...")
        
        # Check dependencies
        if not check_dependencies():
            print("\nPlease install required packages before continuing.")
            return False
        
        # Load or create keywords file
        self.filters = parse_config_file()
        if self.filters is False:
            return False
        
        # Validate configuration
        if not validate_config(self.filters):
            return False
        
        # print(f"✅ Keywords loaded: {len(self.filters)} filter terms")
        return True
    
    def get_filters(self):
        """Get current filter list"""
        return self.filters
    
    def add_filter(self, filter_term):
        """Add new filter term"""
        if filter_term.lower() not in self.filters:
            self.filters.append(filter_term.lower())
            return self._save_filters()
        return True
    
    def remove_filter(self, filter_term):
        """Remove filter term"""
        try:
            self.filters.remove(filter_term.lower())
            return self._save_filters()
        except ValueError:
            return False
    
    def _save_filters(self):
        """Save filters back to keywords file"""
        try:
            # Read current file to preserve comments and structure
            lines = []
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Find [FILTERS] section
            filter_section_start = -1
            for i, line in enumerate(lines):
                if line.strip() == '[FILTERS]':
                    filter_section_start = i
                    break
            
            if filter_section_start == -1:
                # Add [FILTERS] section
                lines.append('\n[FILTERS]\n')
                filter_section_start = len(lines) - 1
            
            # Remove old filter lines
            new_lines = lines[:filter_section_start + 1]
            
            # Add current filters
            for filter_term in sorted(self.filters):
                new_lines.append(f"{filter_term}\n")
            
            # Write back to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            print(f"Failed to save keywords file: {e}")
            return False
    
    def edit_config_interactive(self):
        """Interactive keywords editor"""
        while True:
            print("\n📝 KEYWORDS EDITOR")
            print("=" * 30)
            print(f"Current filters: {len(self.filters)}")
            print("\n1. View all filters")
            print("2. Add filter")
            print("3. Remove filter")
            print("4. Edit keywords file")
            print("5. Provider optimization info")
            print("9. Back to configuration menu")
            
            choice = get_single_choice("Press a key (1-5, 9):", ['1', '2', '3', '4', '5', '9'])
            if choice is None or choice == "9":
                break
            
            if choice == "1":
                self._show_all_filters()
            elif choice == "2":
                self._add_filter_interactive()
            elif choice == "3":
                self._remove_filter_interactive()
            elif choice == "4":
                self._edit_config_file()
                # Reload after external edit
                self.filters = parse_config_file()
            elif choice == "5":
                self._show_provider_optimization_info()
    
    def _show_all_filters(self):
        """Display all current filters"""
        if not self.filters:
            print("No filters configured.")
            return
        
        print(f"\n📋 CURRENT FILTERS ({len(self.filters)}):")
        print("-" * 40)
        for i, f in enumerate(sorted(self.filters), 1):
            print(f"{i:3d}. {f}")
        print("-" * 40)
        print("Press any key to continue...")
        get_single_key()
    
    def _add_filter_interactive(self):
        """Interactive filter addition"""
        filter_term = input("Enter new filter term: ").strip()
        if filter_term:
            if self.add_filter(filter_term):
                print(f"✅ Added filter: {filter_term}")
            else:
                print(f"❌ Failed to add filter: {filter_term}")
        else:
            print("Empty filter term ignored.")
    
    def _remove_filter_interactive(self):
        """Interactive filter removal"""
        if not self.filters:
            print("No filters to remove.")
            return
        
        print("Current filters:")
        for i, f in enumerate(sorted(self.filters), 1):
            print(f"{i}. {f}")
        
        try:
            choice = int(input("Enter filter number to remove: ")) - 1
            filter_list = sorted(self.filters)
            if 0 <= choice < len(filter_list):
                filter_term = filter_list[choice]
                if self.remove_filter(filter_term):
                    print(f"✅ Removed filter: {filter_term}")
                else:
                    print(f"❌ Failed to remove filter: {filter_term}")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    def _edit_config_file(self):
        """Open keywords file in external editor"""
        editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")
        try:
            os.system(f'"{editor}" "{self.config_file}"')
        except Exception as e:
            print(f"Failed to open editor: {e}")
            print(f"Please manually edit: {self.config_file}")
    
    def _show_provider_optimization_info(self):
        """Show provider-specific optimization information"""
        print("\n🔧 PROVIDER OPTIMIZATION INFO")
        print("=" * 50)
        
        for provider, config in IMAP_SERVERS.items():
            if provider == 'custom':
                continue
                
            provider_emoji = {
                'icloud': '🍎',
                'gmail': '📧', 
                'outlook': '🏢',
                'yahoo': '📮',
                'aol': '📧'
            }.get(provider, '🔧')
            
            print(f"\n{provider_emoji} {provider.upper()}:")
            print(f"   Strategy: {config.get('deletion_strategy', 'standard')}")
            print(f"   Batch Size: {config.get('batch_size', 25)}")
            print(f"   Individual UID: {config.get('supports_individual_uid', True)}")
            
            if provider == 'icloud':
                print("   🍎 Special: Skips individual operations due to parse errors")
            elif config.get('requires_app_password'):
                print("   🔑 Requires: App-specific password")
        
        print("\nPress any key to continue...")
        get_single_key()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_file_paths():
    """Get all important file paths"""
    return {
        'keywords': CONFIG_FILE,
        'log': LOG_FILE,
        'credentials': CREDS_FILE,
        'analytics': ANALYTICS_OUTPUT,
        'json_data': JSON_OUTPUT
    }

def ensure_directories():
    """Ensure all necessary directories exist"""
    paths = get_file_paths()
    for path in paths.values():
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")

def backup_configuration():
    """Create backup of current keywords file"""
    if os.path.exists(CONFIG_FILE):
        backup_name = f"{CONFIG_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(CONFIG_FILE, backup_name)
            print(f"✅ Keywords file backed up to: {backup_name}")
            return backup_name
        except Exception as e:
            print(f"❌ Failed to backup keywords file: {e}")
            return None
    return None

def get_provider_stats():
    """Get statistics about saved accounts by provider"""
    credential_manager = CredentialManager()
    accounts = credential_manager.load_credentials()
    
    provider_counts = {}
    for account in accounts:
        provider = account.get('provider', 'custom')
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
    
    return provider_counts

# Export main classes and functions
__all__ = [
    'write_log',
    'create_config_file',
    'parse_config_file',
    'validate_config',
    'CredentialManager',
    'IMAPConnectionManager',
    'check_dependencies',
    'ConfigurationManager',
    'get_file_paths',
    'ensure_directories',
    'backup_configuration',
    'detect_provider_from_email',
    'get_provider_config',
    'get_provider_deletion_notes',
    'get_provider_stats',
    'CONFIG_FILE',
    'LOG_FILE',
    'CREDS_FILE',
    'IMAP_SERVERS'
]