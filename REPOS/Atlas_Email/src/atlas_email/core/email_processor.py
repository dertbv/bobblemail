#!/usr/bin/env python3
"""
Email Processing Module - Updated for Split Architecture
Handles IMAP operations, folder management, and email processing workflows.
Now uses spam_classifier.py and domain_validator.py instead of mail_filter_engine.py
"""

import imaplib
import email
import re
import sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Add project root to path so config module can be found
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our new split modules  
from atlas_email.filters.keyword_processor import KeywordProcessor
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
from atlas_email.utils.domain_validator import DomainValidator, decode_header_value
from atlas_email.models.db_logger import write_log, logger
from config.constants import ML_SETTINGS_FILE
from atlas_email.utils.general import safe_json_load
from atlas_email.models.database import db

# ATLAS Integration
try:
    from atlas_integration import log_email_processing_session, atlas
    ATLAS_ENABLED = True
except ImportError:
    ATLAS_ENABLED = False

# ============================================================================
# PROVIDER DETECTION AND OPTIMIZATION
# ============================================================================

def get_provider_type(email_address):
    """Simple domain-based provider detection for optimization"""
    if not email_address or '@' not in email_address:
        return 'generic'
    
    domain = email_address.split('@')[1].lower()
    
    if domain in ['icloud.com', 'me.com', 'mac.com']:
        return 'icloud'
    elif domain == 'gmail.com':
        return 'gmail'
    elif domain in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']:
        return 'outlook'
    elif domain in ['yahoo.com', 'yahoo.co.uk', 'yahoo.ca']:
        return 'yahoo'
    elif domain == 'aol.com':
        return 'aol'
    else:
        return 'generic'

def get_provider_settings(provider_type):
    """Get provider-specific optimization settings"""
    settings = {
        'icloud': {
            'skip_individual_marking': True,
            'use_bulk_operations': True,
            'batch_size': 25,
            'requires_parentheses': True,
            'folder_reselect_frequency': 5
        },
        'gmail': {
            'skip_individual_marking': False,
            'use_bulk_operations': False,
            'batch_size': 50,
            'requires_parentheses': False,
            'folder_reselect_frequency': 10
        },
        'outlook': {
            'skip_individual_marking': False,
            'use_bulk_operations': False,
            'batch_size': 30,
            'requires_parentheses': False,
            'folder_reselect_frequency': 8
        },
        'yahoo': {
            'skip_individual_marking': False,
            'use_bulk_operations': False,
            'batch_size': 40,
            'requires_parentheses': False,
            'folder_reselect_frequency': 8
        },
        'aol': {
            'skip_individual_marking': False,
            'use_bulk_operations': False,
            'batch_size': 30,
            'requires_parentheses': False,
            'folder_reselect_frequency': 8
        },
        'generic': {
            'skip_individual_marking': False,
            'use_bulk_operations': False,
            'batch_size': 25,
            'requires_parentheses': False,
            'folder_reselect_frequency': 5
        }
    }
    
    return settings.get(provider_type, settings['generic'])

# ============================================================================
# EMAIL HEADER PROCESSING
# ============================================================================

def get_email_headers_batch_uid(mail, uids, batch_size=50):
    """Get email headers using UIDs in batches for better performance"""
    headers_dict = {}

    for i in range(0, len(uids), batch_size):
        batch = uids[i:i+batch_size]
        try:
            uid_set = ','.join(batch)
            _, data = mail.uid('fetch', uid_set, '(RFC822.HEADER)')

            # Process batch results with robust encoding handling
            for j, response in enumerate(data):
                if response and len(response) > 1:
                    uid = batch[j // 2]  # Account for IMAP response format
                    
                    # Handle encoding issues in batch responses
                    raw_headers = response[1]
                    if isinstance(raw_headers, bytes):
                        # Try multiple encoding approaches
                        for encoding in ['utf-8', 'iso-8859-1', 'ascii', 'cp1252']:
                            try:
                                headers_dict[uid] = raw_headers.decode(encoding, errors="ignore")
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        else:
                            # Last resort: decode with replacement characters
                            headers_dict[uid] = raw_headers.decode('utf-8', errors="replace")
                    else:
                        headers_dict[uid] = str(raw_headers)

        except Exception as e:
            write_log(f"Error getting batch UID headers: {e}", False)
            # Fallback to individual fetching for this batch
            for uid in batch:
                headers_dict[uid] = get_email_headers_single_uid(mail, uid)

    return headers_dict

def get_email_headers_single_uid(mail, uid):
    """Get single email header using UID with robust encoding handling"""
    try:
        _, data = mail.uid('fetch', uid, '(RFC822.HEADER)')
        if data[0] is None:
            return ""
        
        # Handle encoding issues in raw headers
        raw_headers = data[0][1]
        if isinstance(raw_headers, bytes):
            # Try multiple encoding approaches
            for encoding in ['utf-8', 'iso-8859-1', 'ascii', 'cp1252']:
                try:
                    return raw_headers.decode(encoding, errors="ignore")
                except (UnicodeDecodeError, LookupError):
                    continue
            # Last resort: decode with replacement characters
            return raw_headers.decode('utf-8', errors="replace")
        else:
            return str(raw_headers)
            
    except Exception as e:
        write_log(f"Error getting email UID headers: {e}", False)
        return ""

def compile_filter_patterns(filters):
    """Compile filter patterns for optimized matching"""
    compiled_patterns = []
    simple_filters = []

    for term in filters:
        if any(char in term for char in '*?[]()'):
            try:
                pattern = re.compile(term, re.IGNORECASE)
                compiled_patterns.append((pattern, term))
            except re.error:
                # If regex compilation fails, treat as simple string
                simple_filters.append(term.lower())
        else:
            simple_filters.append(term.lower())

    return simple_filters, compiled_patterns

def check_message_optimized(headers, simple_filters, compiled_patterns):
    """Optimized message checking logic"""
    headers_lower = headers.lower()

    # Check simple string filters first (faster)
    for term in simple_filters:
        if term in headers_lower:
            return True, f"Matched: {term}"

    # Check regex patterns
    for pattern, original_term in compiled_patterns:
        if pattern.search(headers):
            return True, f"Matched regex: {original_term}"

    return False, ""

# ============================================================================
# FOLDER MANAGEMENT
# ============================================================================

class FolderManager:
    """Manages folder discovery and processing coordination"""

    def __init__(self, mail_connection):
        self.mail = mail_connection
        self.target_types = ['bulk', 'spam', 'junk', 'trash', 'deleted']
        self.folder_cache = {}

    def find_target_folders(self):
        """Find all target folders with message counts"""
        target_candidates = []

        try:
            # Get all folders
            status, folders = self.mail.list()
            write_log("=== Searching for target folders ===", False)

            for folder in folders:
                try:
                    decoded = folder.decode('utf-8', errors='ignore')
                    folder_name = self._extract_folder_name(decoded)

                    write_log(f"Found folder: {folder_name}", False)

                    # Check if this is a target folder
                    if self._is_target_folder(folder_name):
                        count = self._get_message_count(folder_name)
                        if count > 0:
                            target_candidates.append((folder_name, count))
                            write_log(f"Target folder found: {folder_name} with {count} messages", False)

                except Exception as e:
                    write_log(f"Error processing folder {folder}: {e}", False)
                    continue

        except Exception as e:
            write_log(f"Error listing folders: {e}", False)

        return target_candidates

    def _extract_folder_name(self, decoded_folder):
        """Extract clean folder name from IMAP LIST response"""
        # Handle quoted folder names
        if '"' in decoded_folder:
            quoted_parts = [part for part in decoded_folder.split('\"') if part.strip()]
            folder_name = quoted_parts[-1] if quoted_parts else decoded_folder.split()[-1]
        else:
            # Handle space-separated format
            parts = decoded_folder.split()
            folder_name = parts[-1] if parts else decoded_folder

        return folder_name.strip()

    def _is_target_folder(self, folder_name):
        """Check if folder is a target for processing"""
        folder_lower = folder_name.lower()
        return any(target_type in folder_lower for target_type in self.target_types)

    def _get_message_count(self, folder_name):
        """Get message count for a folder"""
        try:
            # Use folder name in quotes to handle special characters
            try:
                self.mail.select(f'"{folder_name}"')
            except:
                self.mail.select(folder_name)

            _, messages = self.mail.search(None, 'ALL')
            count = len(messages[0].split()) if messages[0] else 0
            return count

        except Exception as e:
            write_log(f"Error checking folder {folder_name}: {e}", False)
            return 0

    def select_folders_to_process(self, target_candidates):
        """Interactive folder selection with enhanced UI and single-key navigation"""
        print(f"\n📁 SELECT FOLDERS TO PROCESS")
        print("=" * 50)

        for i, (folder_name, count) in enumerate(target_candidates, 1):
            folder_type = "📧" if any(x in folder_name.lower() for x in ['bulk', 'spam', 'junk']) else "🗑️"
            print(f"{i:2d}. {folder_type} {folder_name:<20} {count:>8,} messages")

        print(f"{len(target_candidates)+1:2d}. 📋 All folders")
        print(" 9. ❌ Cancel")
        print("=" * 50)

        # Create valid choices dynamically 
        valid_choices = [str(i) for i in range(1, len(target_candidates) + 2)] + ['9']
        
        while True:
            # Import the function from config_auth
            from config.auth import get_single_choice
            
            choice = get_single_choice(f"Press a key (1-{len(target_candidates)+1}, 9):", valid_choices)
            if choice is None or choice == '9':
                return []
            
            choice_num = int(choice)
            
            if choice_num == len(target_candidates)+1:  # All folders
                return target_candidates
            elif 1 <= choice_num <= len(target_candidates):  # Single folder
                selected_folder = target_candidates[choice_num-1]
                print(f"\n✅ Selected folder:")
                print(f"  • {selected_folder[0]}: {selected_folder[1]:,} messages")
                return [selected_folder]
            else:
                print(f"❌ Invalid selection: {choice}")
                continue

    def _get_all_folders_with_details(self):
        """Get all folders with message counts, including empty folders"""
        all_folders = []
        
        try:
            status, folders = self.mail.list()
            
            for folder in folders:
                try:
                    decoded = folder.decode('utf-8', errors='ignore')
                    folder_name = self._extract_folder_name(decoded)
                    
                    # Skip only container folders that can't be selected
                    # Don't skip [Gmail]/All Mail, [Gmail]/Important, etc. - user might want them
                    if (folder_name.lower() == '[gmail]' or
                        folder_name.lower().endswith('/all mail') and not folder_name.lower() == '[gmail]/all mail'):
                        continue
                    
                    count = self._get_message_count(folder_name)
                    # Include ALL folders, even empty ones (count >= 0)
                    # Only exclude folders that return -1 (error accessing)
                    if count >= 0:
                        all_folders.append((folder_name, count))
                        
                except Exception as e:
                    write_log(f"Error processing folder {folder}: {e}", False)
                    continue
                    
        except Exception as e:
            write_log(f"Error listing all folders: {e}", False)
        
        return all_folders

    def setup_account_folders(self, account_email, credential_manager):
        """Interactive first-time folder setup for an account"""
        print(f"\n📁 Setting up folder preferences for {account_email}...")
        print("=" * 60)
        
        # Get all folders
        all_folders = self._get_all_folders_with_details()
        if not all_folders:
            print("❌ No folders found")
            return []
        
        # Separate auto-detected vs additional folders
        auto_detected = []
        additional_folders = []
        risky_folders = []
        
        risky_keywords = ['inbox', 'sent', 'important', 'all mail']
        
        for folder_name, count in all_folders:
            if self._is_target_folder(folder_name):
                auto_detected.append((folder_name, count))
            elif any(risky in folder_name.lower() for risky in risky_keywords):
                risky_folders.append((folder_name, count))
            else:
                # Include all other folders, even empty ones
                additional_folders.append((folder_name, count))
        
        selected_folders = []
        
        # Show auto-detected folders (pre-selected)
        if auto_detected:
            print("🎯 AUTO-DETECTED SPAM/BULK FOLDERS:")
            for folder_name, count in auto_detected:
                count_str = f"{count:,}" if count > 0 else "empty"
                print(f"✅ {folder_name:<30} ({count_str} messages)")
            
            # Import the function from config_auth
            from config.auth import get_single_choice
            
            auto_choice = get_single_choice("Include all auto-detected folders? (y/n):", ['y', 'n'])
            if auto_choice == 'y':
                selected_folders.extend([folder for folder, _ in auto_detected])
            else:
                # Let user choose individual auto-detected folders
                for folder_name, count in auto_detected:
                    choice = get_single_choice(f"Include {folder_name}? (y/n):", ['y', 'n'])
                    if choice == 'y':
                        selected_folders.append(folder_name)
        
        # Show additional safe folders
        if additional_folders:
            print(f"\n📂 ADDITIONAL FOLDERS FOUND:")
            for folder_name, count in additional_folders:
                count_str = f"{count:,}" if count > 0 else "empty"
                print(f"☐ {folder_name:<30} ({count_str} messages)")
            
            print(f"\nSelect additional folders to include:")
            for folder_name, count in additional_folders:
                choice = get_single_choice(f"Include {folder_name}? (y/n):", ['y', 'n'])
                if choice == 'y':
                    selected_folders.append(folder_name)
        
        # Show risky folders with warnings
        if risky_folders:
            print(f"\n⚠️  RISKY FOLDERS (require confirmation):")
            for folder_name, count in risky_folders:
                count_str = f"{count:,}" if count > 0 else "empty"
                print(f"⚠️  {folder_name:<30} ({count_str} messages)")
            
            print(f"\n⚠️  WARNING: These folders may contain important emails!")
            print(f"Type 'YES' (all caps) to confirm selection:")
            
            for folder_name, count in risky_folders:
                choice = input(f"Include RISKY folder {folder_name}? (YES/no): ").strip()
                if choice == 'YES':
                    selected_folders.append(folder_name)
                    print(f"⚠️  Added {folder_name} to target list")
        
        # Save folder preferences
        if credential_manager.update_folder_preferences(account_email, selected_folders):
            print(f"\n✅ Saved folder preferences for {account_email}")
            print(f"📁 Selected {len(selected_folders)} folders:")
            for folder in selected_folders:
                print(f"  • {folder}")
        else:
            print(f"\n❌ Failed to save folder preferences")
        
        return selected_folders

    def update_account_folders(self, account_email, current_folders, credential_manager):
        """Update existing folder preferences with fresh folder discovery"""
        print(f"\n📁 Updating folder preferences for {account_email}...")
        print("=" * 60)
        
        # Get fresh folder list
        print("🔄 Refreshing folder list from server...")
        all_folders = self._get_all_folders_with_details()
        if not all_folders:
            print("❌ No folders found")
            return current_folders
        
        current_folder_names = set(current_folders)
        available_folder_names = {folder for folder, _ in all_folders}
        
        # Check for missing folders
        missing_folders = current_folder_names - available_folder_names
        if missing_folders:
            print(f"\n⚠️  MISSING FOLDERS:")
            for folder in missing_folders:
                print(f"❌ {folder} (no longer exists)")
            print(f"   These will be removed from your preferences.")
        
        # Check for new folders
        existing_folder_names = {folder for folder, _ in all_folders if folder in current_folder_names}
        new_folders = [(folder, count) for folder, count in all_folders 
                      if folder not in current_folder_names]
        
        if new_folders:
            print(f"\n🆕 NEW FOLDERS FOUND:")
            for folder_name, count in new_folders:
                count_str = f"{count:,}" if count > 0 else "empty"
                print(f"☐ {folder_name:<30} ({count_str} messages)")
        
        # Show current selections
        current_existing = [(folder, count) for folder, count in all_folders 
                           if folder in existing_folder_names]
        
        print(f"\n📋 CURRENT FOLDER SELECTIONS:")
        updated_folders = []
        
        # Import the function from config_auth
        from config.auth import get_single_choice
        
        for folder_name, count in current_existing:
            count_str = f"{count:,}" if count > 0 else "empty"
            print(f"✅ {folder_name:<30} ({count_str} messages)")
            choice = get_single_choice(f"Keep {folder_name}? (y/n):", ['y', 'n'])
            if choice == 'y':
                updated_folders.append(folder_name)
        
        # Let user add new folders
        if new_folders:
            print(f"\n📂 SELECT NEW FOLDERS TO ADD:")
            risky_keywords = ['inbox', 'sent', 'important', 'all mail']
            
            for folder_name, count in new_folders:
                is_risky = any(risky in folder_name.lower() for risky in risky_keywords)
                
                if is_risky:
                    print(f"⚠️  WARNING: {folder_name} may contain important emails!")
                    choice = input(f"Add RISKY folder {folder_name}? (YES/no): ").strip()
                    if choice == 'YES':
                        updated_folders.append(folder_name)
                        print(f"⚠️  Added {folder_name} to target list")
                else:
                    choice = get_single_choice(f"Add {folder_name}? (y/n):", ['y', 'n'])
                    if choice == 'y':
                        updated_folders.append(folder_name)
        
        # Save updated preferences
        if credential_manager.update_folder_preferences(account_email, updated_folders):
            print(f"\n✅ Updated folder preferences for {account_email}")
            print(f"📁 Now targeting {len(updated_folders)} folders:")
            for folder in updated_folders:
                print(f"  • {folder}")
        else:
            print(f"\n❌ Failed to update folder preferences")
            return current_folders
        
        return updated_folders

# ============================================================================
# EMAIL PROCESSOR CLASS
# ============================================================================

class EmailProcessor:
    """Main class for processing emails in folders with provider optimization"""

    def __init__(self, mail_connection, domain_validator=None, account_email=None, account_id=None):
        self.mail = mail_connection
        # Initialize with new split architecture
        self.domain_validator = domain_validator or DomainValidator(logger=write_log)
        self.account_email = account_email
        self.account_id = account_id
        if account_id:
            print(f"🔍 EmailProcessor initialized with account_id: {account_id}")
        else:
            print(f"⚠️  EmailProcessor initialized WITHOUT account_id - flag checking disabled!")
        
        # Initialize Unified Keyword Processor (content-first classification)
        self.keyword_processor = KeywordProcessor()
        
        # Detect provider type for optimization
        self.provider_type = get_provider_type(account_email) if account_email else 'generic'
        self.provider_settings = get_provider_settings(self.provider_type)
        
        write_log(f"Email processor initialized for {self.provider_type} provider with unified keyword processor (CONTENT-FIRST)", False)
        
        self.stats = {
            'total_fetched': 0,
            'total_analyzed': 0,
            'total_matched': 0,
            'total_deleted': 0,
            'total_preserved': 0,
            'total_validated': 0,
            'total_legitimate': 0
        }
    
    def _is_appointment_confirmation(self, sender_email, subject):
        """
        Detect appointment confirmations and scheduling emails that should never be deleted
        """
        if not sender_email or not subject:
            return False
            
        sender_lower = sender_email.lower()
        subject_lower = subject.lower()
        
        # Appointment confirmation patterns
        appointment_patterns = [
            'appointment scheduled',
            'appointment confirmed',
            'appointment booked',
            'booking confirmation',
            'service appointment',
            'your appointment',
            'upcoming appointment',
            'appointment reminder',
            'scheduled for',
            'appointment details'
        ]
        
        # Trusted appointment/scheduling platforms
        trusted_scheduling_domains = [
            'xtime.com',           # XTime - automotive scheduling
            'calendly.com',        # Calendly scheduling
            'acuityscheduling.com', # Acuity scheduling
            'appointmentplus.com', # AppointmentPlus
            'setmore.com',         # Setmore scheduling
            'bookingbug.com',      # BookingBug
            'simplybook.me',       # SimplyBook
            'schedulicity.com',    # Schedulicity
            'appointy.com',        # Appointy
            'appointmentquest.com' # AppointmentQuest
        ]
        
        # Check for appointment patterns in subject
        has_appointment_pattern = any(pattern in subject_lower for pattern in appointment_patterns)
        
        # Check for trusted scheduling platform
        is_scheduling_platform = any(domain in sender_lower for domain in trusted_scheduling_domains)
        
        # Automotive service appointments (like Sheehy Hyundai case)
        automotive_indicators = [
            'dealership', 'honda', 'toyota', 'ford', 'chevrolet', 'hyundai', 'nissan',
            'bmw', 'mercedes', 'audi', 'volkswagen', 'subaru', 'mazda', 'kia',
            'service center', 'auto service', 'car service', 'vehicle service'
        ]
        is_automotive = any(indicator in sender_lower or indicator in subject_lower 
                           for indicator in automotive_indicators)
        
        return (has_appointment_pattern and (is_scheduling_platform or is_automotive))
    
    def _is_business_transactional(self, sender_email, subject):
        """
        Detect legitimate business transactional emails (receipts, confirmations, etc.)
        """
        if not sender_email or not subject:
            return False
            
        sender_lower = sender_email.lower()
        subject_lower = subject.lower()
        
        # Transactional patterns
        transactional_patterns = [
            'order confirmation',
            'payment confirmation',
            'receipt for',
            'invoice #',
            'shipping confirmation',
            'delivery confirmation',
            'pickup ready',
            'account statement',
            'password reset',
            'account verification',
            'subscription renewal',
            'membership renewal',
            'billing statement',
            'service notification',
            'warranty information',
            'product registration'
        ]
        
        # Check for transactional patterns
        has_transactional_pattern = any(pattern in subject_lower for pattern in transactional_patterns)
        
        # Legitimate business domains (banks, major retailers, etc.)
        legitimate_business_domains = [
            'paypal.com', 'stripe.com', 'square.com',
            'amazon.com', 'walmart.com', 'target.com', 'bestbuy.com',
            'ups.com', 'fedex.com', 'usps.com',
            'chase.com', 'bankofamerica.com', 'wellsfargo.com',
            'apple.com', 'microsoft.com', 'google.com',
            'ebay.com', 'etsy.com', 'shopify.com'
        ]
        
        is_legitimate_business = any(domain in sender_lower for domain in legitimate_business_domains)
        
        return has_transactional_pattern and is_legitimate_business

    def _check_whitelist_protection(self, sender_email, subject=""):
        """Check if sender or subject is protected by custom whitelist"""
        try:
            # Load whitelist from centralized settings
            try:
                from config.settings import Settings
                whitelist_config = Settings.get_whitelist()
                custom_whitelist = whitelist_config.get('custom_whitelist', [])
                custom_keyword_whitelist = whitelist_config.get('custom_keyword_whitelist', [])
            except ImportError:
                # Fallback to JSON if settings.py not available
                ml_settings = safe_json_load(ML_SETTINGS_FILE, {})
                custom_whitelist = ml_settings.get('custom_whitelist', [])
                custom_keyword_whitelist = ml_settings.get('custom_keyword_whitelist', [])
            
            # Check domain whitelist
            if custom_whitelist and sender_email and '@' in sender_email:
                sender_lower = sender_email.lower()
                for whitelist_domain in custom_whitelist:
                    if whitelist_domain.lower() in sender_lower:
                        return True, "domain"
            
            # Check keyword whitelist
            if custom_keyword_whitelist and subject:
                subject_lower = subject.lower()
                for keyword in custom_keyword_whitelist:
                    if keyword.lower() in subject_lower:
                        return True, "keyword"
            
            return False, ""
            
        except Exception as e:
            write_log(f"Error checking whitelist protection: {e}", True)
            return False, ""

    def process_folder_messages(self, folder_name, filters=None, auto_confirm=False, preview_mode=False, debug_mode=False, quiet_mode=False):
        """Process messages in a specific folder with optional preview mode and debugging - Updated for single classifier architecture"""
        deleted_count = 0
        processed_count = 0  # Messages that matched classifiers (deleted + preserved)
        preserved_count = 0
        validated_count = 0
        
        print(f"\n🔍 DEBUG: process_folder called - account_id={self.account_id}, preview_mode={preview_mode}")
        legitimate_count = 0  # Messages classified as legitimate (not spam)
        category_counts = {}

        try:
            write_log(f"Processing folder: {folder_name} (Provider: {self.provider_type})", False)
            # if debug_mode:
            #     # Legacy filters are now optional - system uses HybridClassifier
            #     filter_count = len(filters) if filters else 0
            #     write_log(f"DEBUG: Starting folder processing with HybridClassifier + {filter_count} custom filters", True)

            # Select the folder
            if not self._ensure_folder_selected(folder_name):
                raise Exception(f"Could not select folder {folder_name}")

            # Use UID search for reliability (avoids renumbering issues)
            _, message_data = self.mail.uid('search', None, 'ALL')
            
            if not message_data[0]:
                write_log(f"No messages found in {folder_name}")
                return 0, 0, 0, 0, 0, {}

            uids = [x.decode() for x in message_data[0].split()]
            total_messages = len(uids)

            # Debug logging
            if uids:
                uid_min, uid_max = min(uids), max(uids)
                write_log(f"PROCESSING {folder_name}: UIDs {uid_min} to {uid_max} ({total_messages} total)", False)
                # if debug_mode:
                #     write_log(f"DEBUG: Processing UIDs: {uids[:10]}{'...' if len(uids) > 10 else ''}", True)
                #     # Save all UIDs for debugging
                #     print(f"🔍 ALL UIDs FOUND: {uids}")
                #     if len(uids) > 50:
                #         print(f"🔍 FIRST 25 UIDs: {uids[:25]}")
                #         print(f"🔍 LAST 25 UIDs: {uids[-25:]}")
                #     else:
                #         print(f"🔍 ALL UIDs: {uids}")

            # Compile optional custom filter patterns 
            simple_filters, compiled_patterns = compile_filter_patterns(filters or [])
            if debug_mode:
                write_log(f"DEBUG: Compiled {len(simple_filters)} custom filters: {simple_filters}", True)
                write_log(f"DEBUG: Compiled {len(compiled_patterns)} custom regex patterns: {[p[1] for p in compiled_patterns]}", True)

            if not quiet_mode:
                print(f"📥 Fetching headers for {total_messages:,} messages...")
            
            # Use provider-specific batch size
            batch_size = self.provider_settings['batch_size']
            headers_dict = get_email_headers_batch_uid(self.mail, uids, batch_size)
            
            # DEBUG: Check how many headers were actually retrieved
            headers_retrieved = len([uid for uid, headers in headers_dict.items() if headers])
            if headers_retrieved < total_messages:
                missing_headers = total_messages - headers_retrieved
                print(f"⚠️  WARNING: {missing_headers} messages have missing headers and will be SKIPPED")
                # if debug_mode:
                #     # Show which UIDs have missing headers
                #     missing_uids = [uid for uid in uids if not headers_dict.get(uid, "")]
                #     print(f"🔍 UIDs with missing headers: {missing_uids[:20]}{'...' if len(missing_uids) > 20 else ''}")
                #     successful_uids = [uid for uid in uids if headers_dict.get(uid, "")]
                #     print(f"🔍 UIDs with successful headers: {successful_uids[:20]}{'...' if len(successful_uids) > 20 else ''}")

            messages_to_delete = []
            if not quiet_mode:
                print(f"🔍 Analyzing {total_messages:,} messages against {len(simple_filters)} filter terms...")

            # Debug: Track processing before individual email loop
            processed_count_tracker = 0
            successful_headers_count = 0
            
            # Process each message
            for i, uid in enumerate(uids):
                self.stats['total_fetched'] += 1
                processed_count_tracker += 1

                if (i + 1) % 100 == 0 and not quiet_mode:
                    print(f"   📊 Analyzed {i + 1:,}/{total_messages:,} messages...")

                headers = headers_dict.get(uid, "")
                if not headers:
                    # Try to get headers individually for this UID
                    if debug_mode:
                        print(f"🔄 Retrying header fetch for UID {uid}")
                    headers = get_email_headers_single_uid(self.mail, uid)
                
                if headers:
                    successful_headers_count += 1
                    if debug_mode and i < 10:
                        print(f"📧 Processing UID {uid} ({i+1}/{total_messages}) - Headers retrieved successfully")
                    self.stats['total_analyzed'] += 1
                    
                    # Parse message first to get sender and subject for comprehensive analysis
                    try:
                        msg = email.message_from_bytes(headers.encode("utf-8", errors="ignore"))
                    except Exception:
                        msg = email.message_from_string(headers)
                    
                    try:
                        subject = decode_header_value(msg.get('Subject', ''))
                    except Exception as e:
                        subject = str(msg.get('Subject', '')).replace('\n', ' ').replace('\r', ' ')
                        if debug_mode:
                            write_log(f"DEBUG UID {uid}: Subject decode error: {e}", True)
                    
                    try:
                        sender = decode_header_value(msg.get('From', ''))
                    except Exception as e:
                        sender = str(msg.get('From', '')).replace('\n', ' ').replace('\r', ' ')
                        if debug_mode:
                            write_log(f"DEBUG UID {uid}: Sender decode error: {e}", True)

                    # DEBUG: Show header analysis for first few messages or specific UIDs
                    if debug_mode and (i < 5 or uid in ['60158', '60159', '60161', '582058', '582069', '582071', '582074', '582173']):
                        write_log(f"DEBUG UID {uid}: Analyzing - Subject: '{subject}' | Sender: '{sender}'", True)
                    
                    # NEW ARCHITECTURE: Run sophisticated spam analysis FIRST on ALL emails
                    should_delete = False
                    deletion_reason = ""
                    match_source = ""
                    
                    # STEP 1: Email Authentication Check (NEW SECURITY ENHANCEMENT)
                    authentication_result = None
                    try:
                        from atlas_email.core.email_authentication import authenticate_email_headers
                        authentication_result = authenticate_email_headers(headers)
                        
                        if debug_mode:
                            auth_summary = authentication_result.get('auth_summary', 'Unknown')
                            is_authentic = authentication_result.get('is_authentic', False)
                            write_log(f"DEBUG UID {uid}: Authentication - {auth_summary} | Authentic: {is_authentic}", True)
                            
                    except Exception as e:
                        if debug_mode:
                            write_log(f"DEBUG UID {uid}: Authentication error: {e}", True)
                        authentication_result = {'confidence_modifier': 0.0, 'is_authentic': False}
                    
                    # STEP 2: Content Classification
                    # Initialize confidence to avoid None values
                    hybrid_confidence = 75.0  # Default medium confidence
                    
                    try:
                        # Use unified keyword system for classification
                        hybrid_category = self.keyword_processor.process_keywords(
                            headers="",
                            sender=sender,
                            subject=subject
                        )
                        
                        # Determine if it's spam based on category
                        spam_categories = [
                            'Financial & Investment Spam', 'Gambling Spam', 'Health & Medical Spam',
                            'Adult & Dating Spam', 'Business Opportunity Spam', 'Brand Impersonation',
                            'Payment Scam', 'Phishing', 'Education/Training Spam', 'Real Estate Spam',
                            'Legal & Compensation Scams', 'Marketing Spam', 'Promotional Email'
                        ]
                        hybrid_spam = hybrid_category in spam_categories
                        
                        # Get confidence from logical classifier if available, otherwise use category-based confidence
                        if hasattr(self.keyword_processor, 'last_classification_confidence') and self.keyword_processor.last_classification_confidence > 0:
                            # Use logical classifier confidence (convert from 0.0-1.0 to 0-100 scale)
                            hybrid_confidence = self.keyword_processor.last_classification_confidence * 100.0
                        else:
                            # Fallback to category-based confidence
                            if hybrid_category in ['Phishing', 'Health & Medical Spam', 'Financial & Investment Spam']:
                                hybrid_confidence = 85.0  # High confidence for specific categories
                            elif hybrid_category in ['Generic Spam', 'Promotional Email']:
                                hybrid_confidence = 60.0  # Lower confidence for generic categories
                            elif hybrid_category in ['Trusted Domain', 'Legitimate Billing/Delivery', 'Community Email']:
                                hybrid_confidence = 90.0  # Very high confidence for trusted, legitimate billing, and community content
                            else:
                                hybrid_confidence = 75.0  # Medium confidence for other specific categories
                        
                        # Debug: show unified keyword system results
                        if debug_mode and i < 3:
                            write_log(f"DEBUG UID {uid}: Unified keyword result - Category: {hybrid_category}, Spam: {hybrid_spam}, Confidence: {hybrid_confidence:.1f}%, Method: content-first", True)
                        
                    except Exception as e:
                        write_log(f"DEBUG UID {uid}: Unified Keyword Processor ERROR: {e}", True)
                        hybrid_spam = False
                        hybrid_category = "ERROR"
                        hybrid_confidence = 0.0
                    
                    # Debug comparison for first few emails (DISABLED for clean output)
                    # if debug_mode and i < 10:
                    
                    # Use Hybrid classifier results
                    spam_classifier_detected = hybrid_spam
                    spam_category = hybrid_category
                    spam_confidence = hybrid_confidence
                    
                    # Apply authentication confidence modifier (NEW SECURITY ENHANCEMENT)
                    if authentication_result:
                        auth_modifier = authentication_result.get('confidence_modifier', 0.0)
                        original_confidence = spam_confidence
                        spam_confidence += auth_modifier
                        
                        # Cap confidence between 0-100
                        spam_confidence = max(0.0, min(100.0, spam_confidence))
                        
                        if debug_mode and abs(auth_modifier) > 1.0:  # Only log significant adjustments
                            auth_summary = authentication_result.get('auth_summary', 'Unknown')
                            write_log(f"DEBUG UID {uid}: Auth adjustment - {original_confidence:.1f}% → {spam_confidence:.1f}% ({auth_modifier:+.1f}) | {auth_summary}", True)
                    
                    # Ensure confidence is never None - convert to 0.0 if needed
                    if spam_confidence is None:
                        spam_confidence = 0.0
                    
                    # if debug_mode and (i < 5 or uid in ['582058', '582069', '582071', '582074', '582173']):
                    #     write_log(f"DEBUG UID {uid}: Hybrid result: '{spam_category}' (confidence={spam_confidence:.1f}%, is_spam={spam_classifier_detected})", True)
                    
                    if spam_classifier_detected:
                        should_delete = True
                        deletion_reason = f"Hybrid Classifier: {spam_category} ({spam_confidence:.1f}% confidence)"
                        match_source = "HYBRID_CLASSIFIER"
                        # if debug_mode:
                        #     write_log(f"DEBUG UID {uid}: FLAGGED by spam classifier - {spam_category}", True)
                    
                    # STEP 2: Check custom keywords (optional - only if filters provided)
                    if simple_filters or compiled_patterns:
                        keyword_match, keyword_reason = check_message_optimized(headers, simple_filters, compiled_patterns)
                        
                        if keyword_match:
                            if not should_delete:
                                # First detection by keywords
                                should_delete = True
                                deletion_reason = keyword_reason
                                match_source = "USER_KEYWORD"
                            else:
                                # Additional keyword match - enhance the reason
                                deletion_reason += f" + {keyword_reason}"
                                match_source += "+USER_KEYWORD"
                            
                            # if debug_mode:
                            #     write_log(f"DEBUG UID {uid}: FLAGGED by custom keyword filter - {keyword_reason}", True)
                    # elif debug_mode and i < 3:
                    #     write_log(f"DEBUG UID {uid}: No custom filters provided - using HybridClassifier only", True)
                    
                    # if debug_mode and (i < 5 or uid in ['582058', '582069', '582071', '582074', '582173']):
                    #     write_log(f"DEBUG UID {uid}: Overall decision: should_delete={should_delete}, reason='{deletion_reason}'", True)

                    if should_delete:
                        self.stats['total_matched'] += 1
                        processed_count += 1

                        # STEP 2.5: Check if email is flagged for deletion (overrides preservation decisions)
                        # This allows users to manually flag emails for deletion through the web interface,
                        # which will override domain validation and whitelist protection (but not user keyword protection)
                        is_flagged_for_deletion = False
                        if self.account_id:
                            try:
                                is_flagged_for_deletion = db.is_email_flagged_for_deletion(uid, folder_name, self.account_id)
                                if is_flagged_for_deletion and debug_mode:
                                    write_log(f"DEBUG UID {uid}: Email is FLAGGED FOR DELETION - will override preservation decisions", True)
                            except Exception as e:
                                if debug_mode:
                                    write_log(f"DEBUG UID {uid}: Error checking deletion flag: {e}", True)

                        # STEP 3: Domain validation (safety check - can still override)
                        domain_check_passed, domain_reason, was_validated = self.domain_validator.validate_domain_before_deletion(sender, subject)

                        # if debug_mode and uid in ['582058', '582069', '582071', '582074', '582173']:
                        #     write_log(f"DEBUG UID {uid}: Domain validation - passed={domain_check_passed}, reason='{domain_reason}', validated={was_validated}", True)

                        if was_validated:
                            validated_count += 1
                            self.stats['total_validated'] += 1

                        # Check if this is a user keyword match - those override domain validation
                        user_keyword_override = "USER_KEYWORD" in match_source
                        
                        # CRITICAL: Check for appointment confirmations and transactional emails
                        # These should NEVER be deleted regardless of ML classification
                        is_appointment_confirmation = self._is_appointment_confirmation(sender, subject)
                        is_business_transactional = self._is_business_transactional(sender, subject)
                        
                        # Skip domain validation override for spam content from any domain (except very high-risk categories)
                        # Allow deletion of promotional, marketing, and common spam even from legitimate domains
                        # BUT always preserve legitimate business communications
                        is_promotional_content = spam_category in [
                            'Promotional Email', 'Marketing Spam', 'Health & Medical Spam', 'Payment Scam',
                            'Phishing', 'Brand Impersonation', 'Financial & Investment Spam', 'Adult & Dating Spam',
                            'Real Estate Spam', 'Crypto & Investment Spam', 'Tech Support Scam'
                        ]
                        
                        # Always preserve essential business communications regardless of domain
                        is_legitimate_business_communication = spam_category in [
                            'Legitimate Billing/Delivery', 'Community Email', 'Transactional Email',
                            'Account Notification', 'Subscription Management'
                        ]
                        
                        # CRITICAL PROTECTION: Appointment confirmations and business transactions
                        # Override ML classification if this is clearly a legitimate business communication
                        if is_appointment_confirmation or is_business_transactional:
                            preserved_count += 1
                            self.stats['total_preserved'] += 1
                            protection_type = "Appointment Confirmation" if is_appointment_confirmation else "Business Transaction"
                            write_log(f"BUSINESS PROTECTED ({folder_name}): '{subject}' from {sender} - {protection_type} override (ML said: {spam_category})", False)
                            logger.log_email_action("PRESERVED", uid, sender, subject, folder_name, f"{protection_type} protection override", "BUSINESS_TRANSACTION", confidence_score=100, print_to_screen=False)
                            continue
                        
                        if not domain_check_passed and not user_keyword_override and not is_flagged_for_deletion and (not is_promotional_content or is_legitimate_business_communication):
                            # Domain validation overrides spam classifier, but NOT user keywords, deletion flags, or promotional content  
                            # Allow deletion of promotional/marketing content even from legitimate domains
                            preserved_count += 1
                            self.stats['total_preserved'] += 1
                            write_log(f"PRESERVED ({folder_name}): '{subject}' from {sender} - {domain_reason} [HYBRID_CLASSIFIER override]", False)
                            # Log to bulletproof table for tracking
                            logger.log_email_action("PRESERVED", uid, sender, subject, folder_name, f"{domain_reason} [HYBRID_CLASSIFIER override]", spam_category, confidence_score=spam_confidence, print_to_screen=False)
                            continue
                        elif not domain_check_passed and is_flagged_for_deletion:
                            # Deletion flag overrides domain validation
                            write_log(f"DELETION FLAG OVERRIDE ({folder_name}): Domain validation would preserve, but email is flagged for deletion: '{subject}' from {sender} - {domain_reason}", False)
                        elif not domain_check_passed and user_keyword_override:
                            # User keyword overrides domain validation
                            write_log(f"KEYWORD OVERRIDE ({folder_name}): Domain validation would preserve, but my_keywords.txt takes authority: '{subject}' from {sender} - {domain_reason}", False)

                        # STEP 4: Whitelist protection check (overrides everything except user keywords and deletion flags)
                        whitelist_protected, whitelist_type = self._check_whitelist_protection(sender, subject)
                        if whitelist_protected and not user_keyword_override and not is_flagged_for_deletion:
                            # Whitelist protection overrides spam detection including promotional content from legitimate domains
                            # Full protection for domains explicitly added to whitelist (like unraid.net)
                            preserved_count += 1
                            self.stats['total_preserved'] += 1
                            protection_reason = f"Sender {whitelist_type} is whitelisted" if whitelist_type == "domain" else f"Subject contains whitelisted {whitelist_type}"
                            write_log(f"WHITELIST PROTECTED ({folder_name}): '{subject}' from {sender} - {protection_reason} [WHITELIST override]", False)
                            # Log to bulletproof table for tracking
                            logger.log_email_action("PRESERVED", uid, sender, subject, folder_name, f"{protection_reason} [WHITELIST override]", spam_category, confidence_score=spam_confidence, print_to_screen=False)
                            continue
                        elif whitelist_protected and is_flagged_for_deletion:
                            # Deletion flag overrides whitelist protection
                            write_log(f"DELETION FLAG OVERRIDE ({folder_name}): Whitelist would protect, but email is flagged for deletion: '{subject}' from {sender}", False)
                        elif whitelist_protected and user_keyword_override:
                            # User keyword still takes priority even over whitelist
                            write_log(f"USER KEYWORD OVERRIDE ({folder_name}): Whitelist would protect, but user keyword takes priority: '{subject}' from {sender}", False)

                        # Prepare enhanced reason with source information
                        if is_flagged_for_deletion:
                            # Deletion flag takes precedence in the reason
                            if match_source == "HYBRID_CLASSIFIER":
                                enhanced_reason = f"{deletion_reason} [FLAGGED_FOR_DELETION]"
                                final_category = "Flagged for Deletion"
                            elif match_source == "USER_KEYWORD":
                                enhanced_reason = f"{deletion_reason} [FLAGGED_FOR_DELETION+USER_KEYWORD]"
                                final_category = "Flagged for Deletion"
                            else:
                                enhanced_reason = f"{deletion_reason} [FLAGGED_FOR_DELETION]"
                                final_category = "Flagged for Deletion"
                        elif match_source == "HYBRID_CLASSIFIER":
                            enhanced_reason = f"{deletion_reason} [AUTO_DETECTED]"
                            final_category = spam_category
                        elif match_source == "USER_KEYWORD":
                            enhanced_reason = f"{deletion_reason} [USER_KEYWORD]"
                            final_category = "User Keyword"  # User preferences take precedence
                        elif "HYBRID_CLASSIFIER" in match_source and "USER_KEYWORD" in match_source:
                            enhanced_reason = f"{deletion_reason} [MULTI_MATCH] | Category: {spam_category}"
                            final_category = "User Keyword"  # User keyword still takes precedence
                        else:
                            # Fallback for any other detection method
                            enhanced_reason = f"{deletion_reason} [AUTO_DETECTED]"
                            final_category = spam_category

                        if final_category not in category_counts:
                            category_counts[final_category] = {"count": 0, "reason": deletion_reason}
                        category_counts[final_category]["count"] += 1

                        messages_to_delete.append((uid, sender, subject, enhanced_reason, final_category, spam_confidence))
                        write_log(f"MARKED FOR DELETION ({folder_name}): UID {uid} '{subject}' from {sender} ({enhanced_reason})", False)

                    else:
                        # Email had no spam indicators - but check if manually flagged for deletion
                        # This handles the case where users manually flag legitimate emails for deletion
                        is_flagged_for_deletion = False
                        if self.account_id:
                            try:
                                is_flagged_for_deletion = db.is_email_flagged_for_deletion(uid, folder_name, self.account_id)
                                if is_flagged_for_deletion:
                                    # Override the preservation decision
                                    should_delete = True
                                    deletion_reason = "Manually flagged for deletion"
                                    match_source = "MANUAL_FLAG"
                                    enhanced_reason = f"{deletion_reason} [FLAGGED_FOR_DELETION]"
                                    final_category = "Flagged for Deletion"
                                    
                                    if final_category not in category_counts:
                                        category_counts[final_category] = {"count": 0, "reason": deletion_reason}
                                    category_counts[final_category]["count"] += 1
                                    
                                    messages_to_delete.append((uid, sender, subject, enhanced_reason, final_category, spam_confidence))
                                    write_log(f"MANUAL FLAG OVERRIDE ({folder_name}): UID {uid} '{subject}' from {sender} ({enhanced_reason})", False)
                                    
                                    # Update stats
                                    self.stats['total_matched'] += 1
                                    processed_count += 1
                                    
                                    if debug_mode:
                                        write_log(f"DEBUG UID {uid}: Email was manually FLAGGED FOR DELETION - overriding legitimate classification", True)
                                    
                                    continue  # Skip the legitimate processing below
                            except Exception as e:
                                if debug_mode:
                                    write_log(f"DEBUG UID {uid}: Error checking deletion flag in else block: {e}", True)
                        
                        # Email had no spam indicators and is not flagged - count as legitimate
                        legitimate_count += 1
                        self.stats['total_legitimate'] += 1
                        
                        # Log to bulletproof table for tracking legitimate emails
                        try:
                            preservation_reason = f"Not flagged by spam detection (category: {spam_category})"
                            logger.log_email_action("PRESERVED", uid, sender, subject, folder_name, preservation_reason, spam_category, confidence_score=spam_confidence, print_to_screen=False)
                        except Exception as e:
                            write_log(f"Error logging legitimate email: {e}", True)
                        
                        # DEBUG: Log why messages are NOT being flagged
                        if debug_mode and (i < 10 or uid in ['582058', '582069', '582071', '582074', '582173']):
                            write_log(f"DEBUG UID {uid}: PRESERVED - Subject: '{subject}' | Sender: '{sender}' | Spam category: {spam_category} | No keyword match", True)
                            
                            # Check if domain would be suspicious
                            domain_check_passed, domain_reason, was_validated = self.domain_validator.validate_domain_before_deletion(sender, subject)
                            if was_validated and not domain_check_passed:
                                write_log(f"DEBUG UID {uid}: Domain IS suspicious ({domain_reason}) but spam classifier didn't catch it", True)
                
                else:
                    # Handle emails with no headers - still count them but log the issue
                    if debug_mode:
                        print(f"⚠️  UID {uid}: No headers available after retry - SKIPPING email analysis")
                    write_log(f"SKIPPED ({folder_name}): UID {uid} - No headers available for analysis", False)

            # Debug: Final processing summary
            print(f"🔍 PROCESSING SUMMARY:")
            print(f"   📧 Total UIDs found: {total_messages}")
            print(f"   🔄 UIDs processed in loop: {processed_count_tracker}")
            print(f"   ✅ UIDs with successful headers: {successful_headers_count}")
            print(f"   🗑️ Messages marked for deletion: {len(messages_to_delete)}")
            print(f"   🛡️  Messages preserved: {preserved_count}")
            print(f"   ✅ Messages classified as legitimate: {legitimate_count}")

            # Summary of analysis
            # Count all processed emails: spam detected + legitimate
            total_spam_detected = len(messages_to_delete) + preserved_count
            total_classified = total_spam_detected + legitimate_count
            if not quiet_mode:
                print(f"\n📊 ANALYSIS COMPLETE:")
                print(f"   📧 Total messages classified: {total_classified:,} (out of {total_messages:,} total)")
                
                if total_spam_detected > 0:
                    print(f"   🔍 {total_spam_detected:,} messages flagged as spam")
                if legitimate_count > 0:
                    print(f"   ✅ {legitimate_count:,} messages classified as legitimate")

                if preserved_count > 0:
                    print(f"   🛡️  {preserved_count:,} spam messages preserved by domain validation")

                if len(messages_to_delete) > 0:
                    print(f"   🗑️  {len(messages_to_delete):,} confirmed spam messages ready for deletion")
                else:
                    print(f"   ✅ No spam messages found to delete in {folder_name}")

            # Handle deletions or preview
            if messages_to_delete:
                if preview_mode:
                    deleted_count = len(messages_to_delete)
                    print(f"\n📋 PREVIEW: Would delete {deleted_count:,} messages from {folder_name}")
                    
                    # Log ALL emails to database in preview mode (not just examples)
                    for uid, sender, subject, reason, spam_category, confidence_score in messages_to_delete:
                        logger.log_email_action("DELETED", uid, sender, subject, folder_name, f"{reason} [PREVIEW]", spam_category, confidence_score=confidence_score, print_to_screen=False)
                    
                    self._log_preview_examples(folder_name, messages_to_delete)
                else:
                    deleted_count = self._delete_messages(folder_name, messages_to_delete, quiet_mode)
                    self.stats['total_deleted'] += deleted_count

            actual_processed = deleted_count + preserved_count
            
            # ATLAS Integration: Log processing session
            if ATLAS_ENABLED and not preview_mode:
                processing_time = getattr(self, 'last_processing_time', 0)
                atlas.memory.log_work_activity(
                    f"Email Processing Session - {folder_name}",
                    {
                        "Total Messages": total_messages,
                        "Spam Detected": len(messages_to_delete),
                        "Detection Rate": f"{(len(messages_to_delete)/total_messages)*100:.1f}%" if total_messages > 0 else "0%",
                        "Processing Performance": f"{total_messages/processing_time:.1f} emails/sec" if processing_time > 0 else "N/A",
                        "Legitimate Preserved": legitimate_count,
                        "Domain Validation Preserved": preserved_count
                    }
                )
            
            return deleted_count, actual_processed, preserved_count, validated_count, legitimate_count, category_counts

        except Exception as e:
            write_log(f"Error in process_folder_messages ({folder_name}): {e}", False)
            if debug_mode:
                import traceback
                write_log(f"DEBUG: Full traceback: {traceback.format_exc()}", True)
            return 0, 0, 0, 0, 0, {}

    def process_folder_messages_with_new_architecture(self, folder_name, filters=None, domain_validator=None, auto_confirm=False, preview_mode=False, debug_mode=False, quiet_mode=False):
        """Process messages using the hybrid classifier architecture - this is the method called by updated main.py"""
        # Update the domain validator if provided
        if domain_validator:
            self.domain_validator = domain_validator
        
        # Call the updated main processing method with debug support
        return self.process_folder_messages(folder_name, filters, auto_confirm, preview_mode, debug_mode, quiet_mode)

    def _log_preview_examples(self, folder_name, messages_to_delete):
        """Log examples for preview mode"""
        examples_to_show = min(5, len(messages_to_delete))

        for _, sender, subject, reason, _, _ in messages_to_delete[:examples_to_show]:
            write_log(f"WOULD DELETE ({folder_name}): '{subject}' from {sender} ({reason})", False)

        if len(messages_to_delete) > examples_to_show:
            write_log(f"... and {len(messages_to_delete) - examples_to_show} more messages would be deleted from {folder_name}", False)

    def _delete_messages(self, folder_name, messages_to_delete, quiet_mode=False):
        """Provider-optimized message deletion with domain-based strategy"""
        if not quiet_mode:
            print(f"\n🗑️  DELETING {len(messages_to_delete):,} MESSAGES")
            print("=" * 50)
        
        # FLAGGING SYSTEM: Check for protected emails before deletion
        flagged_emails = []
        messages_to_actually_delete = []
        
        if hasattr(self, 'account_id') and self.account_id:
            account_id = self.account_id
        else:
            # Try to get account_id from database using email address
            try:
                account_records = db.execute_query(
                    "SELECT id FROM accounts WHERE email_address = ?", 
                    (self.account_email,)
                )
                account_id = account_records[0]['id'] if account_records else None
            except:
                account_id = None
        
        if account_id:
            for uid, sender, subject, reason, category, confidence in messages_to_delete:
                if db.is_email_flagged(uid, folder_name, account_id):
                    flagged_emails.append((uid, sender, subject, reason, category, confidence))
                    # Log as preserved due to flag protection
                    logger.log_email_action("PRESERVED", uid, sender, subject, folder_name, 
                                           f"Protected by user flag [FLAG_PROTECTED]", category, 
                                           confidence_score=confidence, print_to_screen=False)
                    if not quiet_mode:
                        print(f"🛡️  PROTECTED: UID {uid} '{subject}' from {sender} - User flagged for protection")
                else:
                    messages_to_actually_delete.append((uid, sender, subject, reason, category, confidence))
        else:
            # No account ID available, proceed with all deletions (safety fallback)
            messages_to_actually_delete = messages_to_delete
            if not quiet_mode and account_id is None:
                print("⚠️  Warning: Could not verify flag protection (account ID not found)")
        
        # Update messages_to_delete to only include non-flagged emails
        messages_to_delete = messages_to_actually_delete
        
        if flagged_emails:
            if not quiet_mode:
                print(f"🛡️  {len(flagged_emails)} emails protected by user flags (will not be deleted)")
            write_log(f"Flag protection prevented deletion of {len(flagged_emails)} emails in {folder_name}", False)
        
        if not messages_to_delete:
            if not quiet_mode:
                print("✅ No emails to delete (all protected or none marked)")
            return 0
        
        # Log provider optimization
        write_log(f"Using {self.provider_type} optimized deletion strategy", False)
        
        # Pre-deletion folder refresh to validate UIDs
        try:
            self.mail.select(folder_name)
            write_log(f"Refreshed folder {folder_name} before deletion", False)
        except Exception as e:
            write_log(f"Warning: Could not refresh folder {folder_name}: {e}", False)

        # Sort UIDs in descending order for better IMAP compatibility
        messages_to_delete.sort(key=lambda x: int(x[0]), reverse=True)

        # ENHANCED: Use provider-specific deletion strategy with better detection
        write_log(f"Detected provider type: {self.provider_type} for account: {self.account_email}", False)
        
        # Check if this is actually an iCloud account (improved detection)
        is_icloud_account = (
            self.provider_type == 'icloud' or
            (self.account_email and any(domain in self.account_email.lower() for domain in ['icloud.com', 'me.com', 'mac.com']))
        )
        
        if is_icloud_account:
            if not quiet_mode:
                print("🍎 Using iCloud special deletion protocol (UID EXPUNGE required)")
            return self._icloud_special_deletion(folder_name, messages_to_delete, quiet_mode)
        elif self.provider_settings['use_bulk_operations']:
            if not quiet_mode:
                print(f"📧 Using {self.provider_type} bulk operations mode")
            return self._bulk_flag_and_expunge(folder_name, messages_to_delete, quiet_mode)
        else:
            if not quiet_mode:
                print(f"📧 Using {self.provider_type} standard deletion mode (with UID validation)")
            return self._standard_deletion(folder_name, messages_to_delete, quiet_mode)
    
    def _icloud_optimized_deletion(self, folder_name, messages_to_delete, quiet_mode=False):
        """iCloud-specific optimized deletion - skips failing individual operations"""
        write_log("ICLOUD OPTIMIZATION: Using bulk flagging with UID validation", False)
        
        # Extract UIDs and validate them upfront
        uids_to_delete = [uid for uid, _, _, _, _, _ in messages_to_delete]
        total_to_delete = len(uids_to_delete)
        
        # Ensure folder is properly selected
        if not self._ensure_folder_selected(folder_name):
            write_log(f"Failed to select folder {folder_name} for iCloud deletion", False)
            print(f"❌ Could not access folder {folder_name}")
            return 0
        
        # ENHANCED: Validate all UIDs upfront to avoid Parse Errors
        print("🔍 Validating UIDs against current folder state...")
        valid_uids = self._validate_uids_against_folder(folder_name, uids_to_delete)
        
        if not valid_uids:
            print(f"❌ No valid UIDs found for deletion in {folder_name}")
            write_log(f"iCloud deletion aborted: No valid UIDs in {folder_name}", False)
            return 0
        
        successful_deletions = 0
        successfully_deleted_uids = []
        
        print(f"🏷️  Applying iCloud bulk flagging to {len(valid_uids)} validated UIDs...")
        
        # Process in smaller chunks for iCloud stability
        chunk_size = min(10, self.provider_settings['batch_size'])  # Smaller chunks for iCloud reliability
        start_time = datetime.now()
        
        for i in range(0, len(valid_uids), chunk_size):
            chunk_uids = valid_uids[i:i+chunk_size]
            chunk_start = i + 1
            chunk_end = min(i + chunk_size, len(valid_uids))
            
            # Show progress
            progress_pct = (i / len(valid_uids)) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed > 0 and successful_deletions > 0:
                rate = successful_deletions / elapsed
                eta_seconds = (len(valid_uids) - successful_deletions) / rate if rate > 0 else 0
                eta_str = f"ETA: {int(eta_seconds//60)}m{int(eta_seconds%60)}s" if eta_seconds > 0 else "calculating..."
            else:
                eta_str = "calculating..."
            
            print(f"\r🏷️  Processing {chunk_start:,}-{chunk_end:,}/{len(valid_uids):,} ({progress_pct:.1f}%) | ✅ {successful_deletions:,} | {eta_str}", end="", flush=True)
            
            # Re-select folder before each chunk for iCloud stability
            if not self._ensure_folder_selected(folder_name):
                write_log(f"Lost folder selection for {folder_name}, skipping chunk {chunk_start}-{chunk_end}", False)
                continue
            
            try:
                # Use the bulk flag combination that works for iCloud
                uid_range = ','.join(chunk_uids)
                result = self.mail.uid('store', uid_range, '+FLAGS (\\Deleted)')
                
                if result[0] == 'OK':
                    successful_deletions += len(chunk_uids)
                    successfully_deleted_uids.extend(chunk_uids)
                    write_log(f"iCloud bulk flagged {len(chunk_uids)} messages in chunk {chunk_start}-{chunk_end}", False)
                else:
                    write_log(f"iCloud bulk flagging failed for chunk {chunk_start}-{chunk_end}: {result}", False)
                    
            except Exception as e:
                error_msg = str(e)
                if "Parse Error" in error_msg:
                    write_log(f"Parse Error in iCloud chunk {chunk_start}-{chunk_end}: UIDs may be stale, trying individual validation", False)
                    # Try individual validation for this chunk
                    for uid in chunk_uids:
                        if self._validate_single_uid(folder_name, uid):
                            try:
                                result = self.mail.uid('store', uid, '+FLAGS (\\Deleted)')
                                if result[0] == 'OK':
                                    successful_deletions += 1
                                    successfully_deleted_uids.append(uid)
                                    write_log(f"iCloud individual flagged UID {uid}", False)
                            except:
                                write_log(f"iCloud individual flagging failed for UID {uid}", False)
                else:
                    write_log(f"Error in iCloud bulk flagging chunk {chunk_start}-{chunk_end}: {e}", False)
                continue
        
        print(f"\n🏷️  FLAGGING COMPLETE: {successful_deletions:,}/{len(valid_uids):,} messages flagged for deletion")
        
        # Now expunge all flagged messages at once
        if successful_deletions > 0:
            print("🧹 Expunging all flagged messages...")
            
            # Ensure folder is selected for expunge
            if not self._ensure_folder_selected(folder_name):
                write_log(f"Could not select folder {folder_name} for expunge", False)
                print(f"⚠️  Could not expunge - folder selection failed")
                return successful_deletions
            
            try:
                expunge_result = self.mail.expunge()
                if expunge_result[0] == 'OK':
                    write_log(f"iCloud successfully expunged {successful_deletions} messages from {folder_name}", False)
                    print(f"✅ Successfully expunged {successful_deletions:,} messages from {folder_name}")
                else:
                    write_log(f"iCloud expunge returned: {expunge_result}", False)
                    print(f"⚠️  Expunge completed with status: {expunge_result[0]}")
            except Exception as e:
                write_log(f"Error during iCloud expunge in {folder_name}: {e}", False)
                print(f"⚠️  Expunge error: {e}")
                if not quiet_mode:
                    print(f"   📋 {successful_deletions:,} messages were flagged but may need manual cleanup")
        
        # Log successful deletions for actually deleted messages
        successfully_deleted_set = set(successfully_deleted_uids)
        for uid, sender, subject, reason, spam_category, confidence_score in messages_to_delete:
            if uid in successfully_deleted_set:
                write_log(f"DELETED ({folder_name}): UID {uid} '{subject}' from {sender} ({reason}) [iCloud-Optimized]", False)
                # Log to bulletproof table for tracking
                logger.log_email_action("DELETED", uid, sender, subject, folder_name, f"{reason} [iCloud-Optimized]", spam_category, confidence_score=confidence_score, print_to_screen=False)
        
        return successful_deletions

    def _icloud_special_deletion(self, folder_name, messages_to_delete, quiet_mode=False):
        """iCloud-specific deletion using UID EXPUNGE instead of global EXPUNGE"""
        write_log("ICLOUD SPECIAL: Using UID EXPUNGE protocol for iCloud compatibility", False)
        
        # Extract UIDs and validate them upfront
        uids_to_delete = [uid for uid, _, _, _, _, _ in messages_to_delete]
        total_to_delete = len(uids_to_delete)
        
        # Ensure folder is properly selected
        if not self._ensure_folder_selected(folder_name):
            write_log(f"Failed to select folder {folder_name} for iCloud deletion", False)
            print(f"❌ Could not access folder {folder_name}")
            return 0
        
        # Validate all UIDs upfront to avoid Parse Errors
        print("🔍 Validating UIDs against current folder state...")
        valid_uids = self._validate_uids_against_folder(folder_name, uids_to_delete)
        
        if not valid_uids:
            print(f"❌ No valid UIDs found for deletion in {folder_name}")
            write_log(f"iCloud deletion aborted: No valid UIDs in {folder_name}", False)
            return 0
        
        successful_deletions = 0
        successfully_deleted_uids = []
        
        print(f"🍎 Applying iCloud UID EXPUNGE protocol to {len(valid_uids)} validated UIDs...")
        
        # Process individually for iCloud using UID EXPUNGE
        start_time = datetime.now()
        
        for i, uid in enumerate(valid_uids):
            current_pos = i + 1
            
            # Show progress
            progress_pct = (i / len(valid_uids)) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed > 0 and successful_deletions > 0:
                rate = successful_deletions / elapsed
                eta_seconds = (len(valid_uids) - successful_deletions) / rate if rate > 0 else 0
                eta_str = f"ETA: {int(eta_seconds//60)}m{int(eta_seconds%60)}s" if eta_seconds > 0 else "calculating..."
            else:
                eta_str = "calculating..."
            
            print(f"\r🍎 Processing {current_pos:,}/{len(valid_uids):,} ({progress_pct:.1f}%) | ✅ {successful_deletions:,} | {eta_str}", end="", flush=True)
            
            # Re-select folder periodically for iCloud stability
            if i > 0 and i % 5 == 0:
                if not self._ensure_folder_selected(folder_name):
                    write_log(f"Lost folder selection for {folder_name}, aborting at UID {uid}", False)
                    break
            
            # Validate individual UID before attempting deletion
            if not self._validate_single_uid(folder_name, uid):
                write_log(f"SKIPPING UID {uid} in {folder_name}: UID validation failed", False)
                continue
            
            try:
                # STEP 1: Mark message for deletion with UID STORE
                store_result = self.mail.uid('store', uid, '+FLAGS (\\Deleted)')
                
                if store_result[0] != 'OK':
                    write_log(f"iCloud flagging failed for UID {uid}: {store_result}", False)
                    continue
                
                # STEP 2: Immediately expunge this specific UID (iCloud requirement)
                expunge_result = self.mail.uid('expunge', uid)
                
                if expunge_result[0] == 'OK':
                    successful_deletions += 1
                    successfully_deleted_uids.append(uid)
                    write_log(f"iCloud UID EXPUNGE successful for UID {uid}", False)
                else:
                    write_log(f"iCloud UID EXPUNGE failed for UID {uid}: {expunge_result}", False)
                    
            except Exception as e:
                error_msg = str(e)
                if "Parse Error" in error_msg:
                    write_log(f"PARSE ERROR - UID {uid} in {folder_name}: {error_msg} (UID may be stale)", False)
                elif "NO" in error_msg and "not found" in error_msg.lower():
                    write_log(f"MESSAGE NOT FOUND - UID {uid} in {folder_name}: Message may have been already deleted", False)
                    successful_deletions += 1  # Count as success since it's already gone
                else:
                    write_log(f"iCloud UID EXPUNGE failed for UID {uid}: {error_msg}", False)
        
        print(f"\n🍎 iCloud UID EXPUNGE COMPLETE: {successful_deletions:,}/{len(valid_uids):,} messages deleted")
        
        # Log successful deletions for actually deleted messages
        successfully_deleted_set = set(successfully_deleted_uids)
        for uid, sender, subject, reason, spam_category, confidence_score in messages_to_delete:
            if uid in successfully_deleted_set:
                write_log(f"DELETED ({folder_name}): UID {uid} '{subject}' from {sender} ({reason}) [iCloud-UID-EXPUNGE]", False)
                # Log to bulletproof table for tracking
                logger.log_email_action("DELETED", uid, sender, subject, folder_name, f"{reason} [iCloud-UID-EXPUNGE]", spam_category, confidence_score=confidence_score, print_to_screen=False)
        
        return successful_deletions

    def _bulk_flag_and_expunge(self, folder_name, messages_to_delete, quiet_mode=False):
        """Generic bulk flag and expunge approach for providers that support it"""
        if not quiet_mode:
            print("🚀 Starting bulk flagging process...")
        
        # Extract UIDs and track successful deletions
        uids_to_delete = [uid for uid, _, _, _, _, _ in messages_to_delete]
        total_to_delete = len(uids_to_delete)
        successful_deletions = 0
        successfully_deleted_uids = []
        
        # Ensure folder is properly selected before starting
        if not self._ensure_folder_selected(folder_name):
            write_log(f"Failed to select folder {folder_name} for bulk flagging", False)
            print(f"❌ Could not access folder {folder_name}")
            return 0
        
        # Process in chunks
        chunk_size = self.provider_settings['batch_size']
        start_time = datetime.now()
        
        for i in range(0, len(uids_to_delete), chunk_size):
            chunk_uids = uids_to_delete[i:i+chunk_size]
            chunk_start = i + 1
            chunk_end = min(i + chunk_size, total_to_delete)
            
            # Show progress
            progress_pct = (i / total_to_delete) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed > 0 and successful_deletions > 0:
                rate = successful_deletions / elapsed
                eta_seconds = (total_to_delete - successful_deletions) / rate if rate > 0 else 0
                eta_str = f"ETA: {int(eta_seconds//60)}m{int(eta_seconds%60)}s" if eta_seconds > 0 else "calculating..."
            else:
                eta_str = "calculating..."
            
            print(f"\r🏷️  Flagging {chunk_start:,}-{chunk_end:,}/{total_to_delete:,} ({progress_pct:.1f}%) | ✅ {successful_deletions:,} | {eta_str}", end="", flush=True)
            
            # Re-select folder if needed
            folder_reselect_freq = self.provider_settings['folder_reselect_frequency']
            if i > 0 and (i // chunk_size) % folder_reselect_freq == 0:
                if not self._ensure_folder_selected(folder_name):
                    write_log(f"Lost folder selection for {folder_name}, skipping chunk {chunk_start}-{chunk_end}", False)
                    continue
            
            try:
                # Use provider-appropriate flag syntax
                uid_range = ','.join(chunk_uids)
                flag_syntax = '+FLAGS (\\Deleted)' if self.provider_settings['requires_parentheses'] else '+FLAGS \\Deleted'
                result = self.mail.uid('store', uid_range, flag_syntax)
                
                if result[0] == 'OK':
                    successful_deletions += len(chunk_uids)
                    successfully_deleted_uids.extend(chunk_uids)
                    write_log(f"Bulk flagged {len(chunk_uids)} messages in chunk {chunk_start}-{chunk_end}", False)
                else:
                    write_log(f"Bulk flagging failed for chunk {chunk_start}-{chunk_end}: {result}", False)
                    
            except Exception as e:
                write_log(f"Error in bulk flagging chunk {chunk_start}-{chunk_end}: {e}", False)
                continue
        
        print(f"\n🏷️  FLAGGING COMPLETE: {successful_deletions:,}/{total_to_delete:,} messages flagged for deletion")
        
        # Expunge all flagged messages
        if successful_deletions > 0:
            print("🧹 Expunging all flagged messages...")
            
            if not self._ensure_folder_selected(folder_name):
                write_log(f"Could not select folder {folder_name} for expunge", False)
                print(f"⚠️  Could not expunge - folder selection failed")
                return successful_deletions
            
            try:
                expunge_result = self.mail.expunge()
                if expunge_result[0] == 'OK':
                    write_log(f"Successfully expunged {successful_deletions} messages from {folder_name}", False)
                    print(f"✅ Successfully expunged {successful_deletions:,} messages from {folder_name}")
                else:
                    write_log(f"Expunge returned: {expunge_result}", False)
                    print(f"⚠️  Expunge completed with status: {expunge_result[0]}")
            except Exception as e:
                write_log(f"Error during bulk expunge in {folder_name}: {e}", False)
                print(f"⚠️  Expunge error: {e}")
                print(f"   📋 {successful_deletions:,} messages were flagged but may need manual cleanup")
        
        # Log successful deletions for actually deleted messages
        successfully_deleted_set = set(successfully_deleted_uids)
        for uid, sender, subject, reason, spam_category, confidence_score in messages_to_delete:
            if uid in successfully_deleted_set:
                write_log(f"DELETED ({folder_name}): UID {uid} '{subject}' from {sender} ({reason}) [Bulk-Optimized]", False)
                # Log to bulletproof table for tracking
                logger.log_email_action("DELETED", uid, sender, subject, folder_name, f"{reason} [Bulk-Optimized]", spam_category, confidence_score=confidence_score, print_to_screen=False)
        
        return successful_deletions

    def _ensure_folder_selected(self, folder_name):
        """Ensure folder is properly selected, with provider-specific retry logic"""
        max_attempts = 3 if self.provider_type == 'icloud' else 2
        
        for attempt in range(max_attempts):
            try:
                # Try with quoted folder name first
                result = self.mail.select(f'"{folder_name}"')
                if result[0] == 'OK':
                    return True
            except:
                pass
            
            try:
                # Try without quotes
                result = self.mail.select(folder_name)
                if result[0] == 'OK':
                    return True
            except:
                pass
            
            # If failed, try to close and pause (especially helpful for iCloud)
            if attempt < max_attempts - 1:
                try:
                    self.mail.close()
                    import time
                    pause_time = 0.2 if self.provider_type == 'icloud' else 0.1
                    time.sleep(pause_time)
                except:
                    pass
        
        return False

    def _standard_deletion(self, folder_name, messages_to_delete, quiet_mode=False):
        """Standard deletion approach for providers that support individual operations"""
        batch_size = self.provider_settings['batch_size']
        successful_deletions = 0
        failed_deletions = 0
        total_to_delete = len(messages_to_delete)
        start_time = datetime.now()

        for i in range(0, len(messages_to_delete), batch_size):
            batch = messages_to_delete[i:i+batch_size]
            batch_start = i + 1
            batch_end = min(i + batch_size, total_to_delete)

            # Show progress
            progress_pct = (i / total_to_delete) * 100
            elapsed = (datetime.now() - start_time).total_seconds()

            if elapsed > 0 and successful_deletions > 0:
                rate = successful_deletions / elapsed
                eta_seconds = (total_to_delete - successful_deletions) / rate if rate > 0 else 0
                eta_str = f"ETA: {int(eta_seconds//60)}m{int(eta_seconds%60)}s" if eta_seconds > 0 else "calculating..."
            else:
                eta_str = "calculating..."

            print(f"\r🗑️  Deleting {batch_start:,}-{batch_end:,}/{total_to_delete:,} ({progress_pct:.1f}%) | ✅ {successful_deletions:,} | ❌ {failed_deletions} | {eta_str}", end="", flush=True)

            # Try batch deletion first
            batch_success = self._try_batch_deletion(folder_name, batch)

            if batch_success:
                successful_deletions += len(batch)
            else:
                # Fallback to individual deletion
                individual_successes = self._try_individual_deletion(folder_name, batch, i, total_to_delete)
                successful_deletions += individual_successes
                failed_deletions += len(batch) - individual_successes

        print(f"\n✅ DELETION COMPLETE: {successful_deletions:,}/{total_to_delete:,} messages deleted successfully")

        if failed_deletions > 0:
            print(f"⚠️  {failed_deletions} messages could not be deleted (may require manual cleanup)")

        # Expunge to finalize deletions
        self._expunge_folder(folder_name, successful_deletions)

        return successful_deletions

    def _try_batch_deletion(self, folder_name, batch):
        """Try to delete a batch of messages using UID STORE with enhanced error handling"""
        try:
            uids_to_delete = [uid for uid, _, _, _, _, _ in batch]
            
            # ENHANCED: Validate UIDs against current folder state
            valid_uids = self._validate_uids_against_folder(folder_name, uids_to_delete)
            
            if not valid_uids:
                write_log(f"Batch deletion failed for {folder_name}: No valid UIDs in batch after validation", False)
                return False
            
            # Try batch deletion with valid UIDs only
            uid_set = ','.join(valid_uids)
            flag_syntax = '+FLAGS (\\Deleted)' if self.provider_settings['requires_parentheses'] else '+FLAGS \\Deleted'
            self.mail.uid('store', uid_set, flag_syntax)

            # Log successful batch (only for messages with valid UIDs)
            for uid, sender, subject, reason, spam_category, confidence_score in batch:
                if uid in valid_uids:
                    write_log(f"DELETED ({folder_name}): UID {uid} '{subject}' from {sender} ({reason})", False)
                    # Log to bulletproof table for tracking
                    logger.log_email_action("DELETED", uid, sender, subject, folder_name, reason, spam_category, confidence_score=confidence_score, print_to_screen=False)

            return True

        except Exception as e:
            error_msg = str(e)
            if "Parse Error" in error_msg:
                write_log(f"Batch deletion failed for {folder_name}: IMAP Parse Error - switching to individual deletion", False)
            elif "BAD" in error_msg:
                write_log(f"Batch deletion failed for {folder_name}: IMAP server error - switching to individual deletion", False)
            else:
                write_log(f"Batch deletion failed for {folder_name}: {error_msg} - switching to individual deletion", False)
            return False

    def _validate_uids_against_folder(self, folder_name, uids_to_check):
        """Validate UIDs against current folder state to avoid Parse Errors"""
        valid_uids = []
        
        try:
            # Ensure folder is selected
            if not self._ensure_folder_selected(folder_name):
                write_log(f"Cannot validate UIDs - folder {folder_name} not accessible", False)
                return []
            
            # Get current UIDs in folder
            _, current_messages = self.mail.uid('search', None, 'ALL')
            if not current_messages[0]:
                write_log(f"No messages found in {folder_name} during UID validation", False)
                return []
            
            current_uids = set(x.decode() for x in current_messages[0].split())
            
            # Validate each UID
            for uid in uids_to_check:
                try:
                    # Check if UID is numeric and reasonable
                    uid_num = int(uid)
                    if uid_num > 0 and uid_num < 999999999:
                        # Check if UID still exists in folder
                        if uid in current_uids:
                            valid_uids.append(uid)
                        else:
                            write_log(f"UID {uid} no longer exists in {folder_name} (may have been deleted)", False)
                    else:
                        write_log(f"INVALID UID {uid} in {folder_name}: UID out of reasonable range", False)
                except ValueError:
                    write_log(f"INVALID UID {uid} in {folder_name}: UID is not numeric", False)
            
            write_log(f"UID Validation: {len(valid_uids)}/{len(uids_to_check)} UIDs are valid in {folder_name}", False)
            return valid_uids
            
        except Exception as e:
            write_log(f"UID validation failed for {folder_name}: {e}", False)
            # Fallback to basic validation
            basic_valid = []
            for uid in uids_to_check:
                try:
                    uid_num = int(uid)
                    if 0 < uid_num < 999999999:
                        basic_valid.append(uid)
                except ValueError:
                    pass
            return basic_valid

    def _try_individual_deletion(self, folder_name, batch, batch_start_index, total_to_delete):
        """Individual deletion fallback with enhanced error handling for iCloud Parse Errors"""
        individual_successes = 0

        for j, (uid, sender, subject, reason, spam_category, confidence_score) in enumerate(batch):
            current_pos = batch_start_index + j + 1
            print(f"\r🔄 Individual delete {current_pos:,}/{total_to_delete:,} | ✅ {individual_successes}", end="", flush=True)

            # ENHANCED: Validate individual UID before attempting deletion
            if not self._validate_single_uid(folder_name, uid):
                write_log(f"SKIPPING UID {uid} in {folder_name}: UID validation failed", False)
                continue

            try:
                # Use provider-appropriate flag syntax
                flag_syntax = '+FLAGS (\\Deleted)' if self.provider_settings['requires_parentheses'] else '+FLAGS \\Deleted'
                result = self.mail.uid('store', uid, flag_syntax)
                
                if result[0] == 'OK':
                    individual_successes += 1
                    write_log(f"DELETED ({folder_name}): UID {uid} '{subject}' from {sender} ({reason})", False)
                    # Log to bulletproof table for tracking
                    logger.log_email_action("DELETED", uid, sender, subject, folder_name, reason, spam_category, confidence_score=confidence_score, print_to_screen=False)
                else:
                    write_log(f"Failed to delete UID {uid}: {result}", False)
                    
            except Exception as e:
                error_msg = str(e)
                if "Parse Error" in error_msg:
                    write_log(f"PARSE ERROR - UID {uid} in {folder_name}: {error_msg} (UID may be stale)", False)
                elif "NO" in error_msg and "not found" in error_msg.lower():
                    write_log(f"MESSAGE NOT FOUND - UID {uid} in {folder_name}: Message may have been already deleted", False)
                    individual_successes += 1  # Count as success since it's already gone
                    # Log to bulletproof table for tracking
                    logger.log_email_action("DELETED", uid, sender, subject, folder_name, f"{reason} [Already Deleted]", spam_category, confidence_score=confidence_score, print_to_screen=False)
                else:
                    write_log(f"DELETION FAILED - UID {uid} in {folder_name}: {error_msg}", False)

        return individual_successes

    def _validate_single_uid(self, folder_name, uid):
        """Quick validation for a single UID"""
        try:
            # Basic numeric validation
            uid_num = int(uid)
            if not (0 < uid_num < 999999999):
                return False
            
            # Try a lightweight UID operation to see if it exists
            result = self.mail.uid('fetch', uid, '(UID)')
            return result[0] == 'OK' and result[1] and result[1][0] is not None
            
        except Exception:
            return False

    def _expunge_folder(self, folder_name, deleted_count):
        """Expunge folder to finalize deletions"""
        if deleted_count == 0:
            return

        print("🔄 Finalizing deletions...")
        
        try:
            expunge_result = self.mail.expunge()
            if expunge_result[0] == 'OK':
                write_log(f"Successfully expunged {deleted_count} messages from {folder_name}", False)
                print(f"✅ Expunged {deleted_count:,} messages from {folder_name}")
            else:
                write_log(f"Expunge returned: {expunge_result}", False)
                print(f"⚠️  Expunge completed with status: {expunge_result[0]}")
                
        except Exception as e:
            write_log(f"Error during expunge in {folder_name}: {e}", False)
            print(f"⚠️  Expunge error: {e}")
            print(f"   📋 {deleted_count:,} messages were flagged but may need manual cleanup")

    def get_processing_stats(self):
        """Get processing statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset processing statistics"""
        for key in self.stats:
            self.stats[key] = 0

# ============================================================================
# BATCH PROCESSOR FOR MULTIPLE ACCOUNTS
# ============================================================================

class BatchProcessor:
    """Handles batch processing across multiple email accounts with provider optimization"""

    def __init__(self, credential_manager, connection_manager):
        self.credential_manager = credential_manager
        self.connection_manager = connection_manager
        self.results = []

    def process_all_accounts(self, filters, auto_yes=False):
        """Process all saved accounts with provider-specific optimization"""
        accounts = self.credential_manager.load_credentials()
        if not accounts:
            print("❌ No saved accounts found for batch processing")
            return []

        print(f"🤖 BATCH PROCESSING: {len(accounts)} accounts")
        print("=" * 50)

        self.results = []

        for i, account in enumerate(accounts, 1):
            account_email = account.get('email_address', 'Unknown')
            provider_type = get_provider_type(account_email)
            
            print(f"\n--- Processing account {i}/{len(accounts)}: {account_email} ({provider_type}) ---")

            try:
                result = self._process_single_account(account, filters, auto_yes, quiet_mode=True)
                self.results.append({
                    'account': account_email,
                    'provider': provider_type,
                    'success': True,
                    'result': result
                })

            except Exception as e:
                print(f"❌ Error processing {account_email}: {e}")
                self.results.append({
                    'account': account_email,
                    'provider': provider_type,
                    'success': False,
                    'error': str(e)
                })
                continue

        self._display_batch_summary()
        return self.results

    def process_all_accounts_with_new_architecture(self, filters, auto_yes=False):
        """Process all accounts using the new split architecture - called by updated main.py"""
        # This method uses the updated architecture internally
        return self.process_all_accounts(filters, auto_yes)

    def _process_single_account(self, account, filters, auto_yes, quiet_mode=True):
        """Process a single account with provider optimization and new architecture"""
        # Connect to account
        mail = self.connection_manager.connect_to_imap(account, quiet_mode=quiet_mode)
        if not mail:
            raise Exception(f"Could not connect to {account['email_address']}")

        try:
            account_email = account.get('email_address')
            account_provider = account.get('provider', 'unknown').lower()
            start_time = datetime.now()
            
            # Get account_id from database
            account_id = None
            account_records = db.execute_query(
                "SELECT id FROM accounts WHERE email_address = ?", 
                (account_email,)
            )
            if account_records:
                account_id = account_records[0]['id']
            else:
                # Account doesn't exist in database - this shouldn't happen in normal operation
                # but we'll handle it gracefully by creating a placeholder account record
                write_log(f"Warning: Account {account_email} not found in database, creating placeholder record", True)
                account_id = db.execute_insert("""
                    INSERT INTO accounts (email_address, provider, host, port, encrypted_password)
                    VALUES (?, ?, '', 0, '')
                """, (account_email, account_provider))
            
            # Create session in database for batch processing
            session_id = db.execute_insert("""
                INSERT INTO sessions (account_id, session_type, is_preview)
                VALUES (?, ?, ?)
            """, (account_id, 'batch', False))
            
            # Set logger session context
            logger.set_session_context(session_id, account_id)
            logger.log_session_start(account_email, account_id or 0, session_id)
            
            # Create domain validator with account provider context (new architecture)
            domain_validator = DomainValidator(logger=write_log, account_provider=account_provider)
            
            # Create processor with account email for provider detection and domain validator
            processor = EmailProcessor(mail, domain_validator=domain_validator, account_email=account_email)
            folder_manager = FolderManager(mail)

            # Use account's saved folder preferences or fall back to auto-detection
            target_folders = account.get('target_folders', [])
            if target_folders:
                # Use saved preferences
                target_candidates = []
                for folder_name in target_folders:
                    count = folder_manager._get_message_count(folder_name)
                    if count >= 0:
                        target_candidates.append((folder_name, count))
            else:
                # Fall back to auto-detection
                target_candidates = folder_manager.find_target_folders()

            if not target_candidates:
                return (0, 0, 0, 0)

            total_deleted = 0
            total_processed = 0
            total_preserved = 0
            total_validated = 0

            # Process all folders for this account
            for folder_name, count in target_candidates:
                print(f"  📁 Processing {folder_name} ({count:,} messages)...")

                # Use the updated method with new architecture
                deleted, processed, preserved, validated, legitimate, _ = processor.process_folder_messages(
                    folder_name, filters, auto_confirm=auto_yes, quiet_mode=True
                )

                total_deleted += deleted
                total_processed += processed
                total_preserved += preserved
                total_validated += validated

                print(f"     ✅ {deleted} deleted, {preserved} preserved, {validated} validated")

            # End session logging
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            logger.log_session_end(total_deleted, total_preserved, total_validated, elapsed_seconds)
            
            # Update session end time in database
            db.execute_update("""
                UPDATE sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    total_deleted = ?, 
                    total_preserved = ?, 
                    total_validated = ?,
                    folders_processed = ?
                WHERE id = ?
            """, (total_deleted, total_preserved, total_validated, len(target_candidates), session_id))

            return (total_deleted, total_processed, total_preserved, total_validated)

        finally:
            self.connection_manager.disconnect()

    def _display_batch_summary(self):
        """Display summary of batch processing results with provider breakdown"""
        # Clear screen before showing clean summary
        from atlas_email.utils.general import clear_screen
        clear_screen()
        
        print("\n" + "=" * 60)
        print("BATCH PROCESSING COMPLETE - SUMMARY")
        print("=" * 60)

        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]

        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")

        if successful:
            total_deleted = sum(r['result'][0] for r in successful)
            total_preserved = sum(r['result'][2] for r in successful)
            print(f"\n📊 OVERALL TOTALS:")
            print(f"   🗑️  Total Deleted: {total_deleted:,}")
            print(f"   🛡️  Total Preserved: {total_preserved:,}")
            
            # Provider breakdown
            provider_stats = defaultdict(lambda: {'deleted': 0, 'preserved': 0, 'count': 0})
            for result in successful:
                provider = result.get('provider', 'unknown')
                provider_stats[provider]['deleted'] += result['result'][0]
                provider_stats[provider]['preserved'] += result['result'][2]
                provider_stats[provider]['count'] += 1
            
            if len(provider_stats) > 1:
                print(f"\n📊 PROVIDER BREAKDOWN:")
                for provider, stats in provider_stats.items():
                    print(f"   {provider.upper()}: {stats['count']} accounts, {stats['deleted']:,} deleted, {stats['preserved']:,} preserved")

        if failed:
            print(f"\n❌ FAILED ACCOUNTS:")
            for result in failed:
                provider = result.get('provider', 'unknown')
                print(f"   • {result['account']} ({provider}): {result['error']}")

        print("=" * 60)

# ============================================================================
# PREVIEW MODE HANDLER
# ============================================================================

class PreviewModeHandler:
    """Handles preview mode operations with provider awareness"""

    def __init__(self, processor, folder_manager):
        self.processor = processor
        self.folder_manager = folder_manager

    def run_preview_analysis(self, target_candidates, filters):
        """Run comprehensive preview analysis with provider optimization info"""
        print("\n🔍 PREVIEW MODE - ANALYZING WHAT WOULD BE DELETED")
        print("=" * 60)
        
        # Show provider optimization info
        if hasattr(self.processor, 'provider_type'):
            provider_info = f" (Provider: {self.processor.provider_type})"
            optimization_info = get_provider_settings(self.processor.provider_type)
            print(f"📧 Account Provider{provider_info}")
            if self.processor.provider_type == 'icloud':
                print("🍎 Using iCloud-optimized deletion strategy")
            elif optimization_info['use_bulk_operations']:
                print(f"📊 Using {self.processor.provider_type} bulk operations")
            print("-" * 60)

        total_would_delete = 0
        total_would_preserve = 0
        total_would_validate = 0
        preview_results = {}

        for folder_name, count in target_candidates:
            print(f"\n📂 Analyzing {folder_name} ({count:,} messages)...")

            try:
                deleted, processed, preserved, validated, category_counts = self.processor.process_folder_messages(
                    folder_name, filters, auto_confirm=False, preview_mode=True
                )

                preview_results[folder_name] = {
                    'would_delete': deleted,
                    'would_preserve': preserved,
                    'would_validate': validated,
                    'categories': category_counts
                }

                total_would_delete += deleted
                total_would_preserve += preserved
                total_would_validate += validated

                print(f"   📊 Would delete: {deleted:,} | preserve: {preserved:,} | validate: {validated:,}")

            except Exception as e:
                print(f"   ❌ Error analyzing {folder_name}: {e}")
                preview_results[folder_name] = {
                    'would_delete': 0,
                    'would_preserve': 0,
                    'would_validate': 0,
                    'error': str(e)
                }

        # Display comprehensive preview summary
        self._display_preview_summary(preview_results, total_would_delete, total_would_preserve, total_would_validate)

        # Option to proceed with actual deletion
        return self._prompt_for_actual_processing(preview_results)

    def _display_preview_summary(self, preview_results, total_would_delete, total_would_preserve, total_would_validate):
        """Display detailed preview summary"""
        print("\n" + "=" * 70)
        print("PREVIEW SUMMARY")
        print("=" * 70)
        print(f"{'Folder':<25} {'Would Delete':>12} {'Would Preserve':>15} {'Would Validate':>15}")
        print("-" * 70)

        for folder_name, results in preview_results.items():
            if 'error' in results:
                print(f"{folder_name:<25} {'ERROR':>12} {'':>15} {'':>15}")
            else:
                print(f"{folder_name:<25} {results['would_delete']:>12,} {results['would_preserve']:>15,} {results['would_validate']:>15,}")

        print("-" * 70)
        print(f"{'TOTAL':<25} {total_would_delete:>12,} {total_would_preserve:>15,} {total_would_validate:>15,}")
        print("=" * 70)

        # Category breakdown
        all_categories = defaultdict(int)
        for results in preview_results.values():
            if 'categories' in results:
                for category, data in results['categories'].items():
                    all_categories[category] += data['count']

        if all_categories:
            print(f"\n📊 SPAM CATEGORIES THAT WOULD BE DELETED:")
            print("-" * 40)
            total_flagged = sum(all_categories.values())
            for category, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_flagged * 100) if total_flagged > 0 else 0
                print(f"{category:<25} {count:>3,} ({percentage:>5.1f}%)")

        print(f"\n🔍 This was PREVIEW MODE - no emails were actually deleted")

    def _prompt_for_actual_processing(self, preview_results):
        """Prompt user whether to proceed with actual deletion"""
        while True:
            print("\n" + "=" * 50)
            print("PREVIEW COMPLETE - NEXT ACTION")
            print("=" * 50)
            print("1. Proceed with actual deletion")
            print("2. Exit without deleting anything")
            print("3. Show detailed breakdown")

            choice = input("\nEnter choice (1-3): ").strip()

            if choice == "1":
                confirm = input("Are you sure you want to proceed with deletion? (yes/no): ").strip().lower()
                if confirm in ('yes', 'y'):
                    return True
                else:
                    print("Deletion cancelled.")
                    return False
            elif choice == "2":
                print("Exiting without making any changes.")
                return False
            elif choice == "3":
                self._show_detailed_breakdown(preview_results)
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def _show_detailed_breakdown(self, preview_results):
        """Show detailed breakdown of what would be deleted"""
        print("\n📋 DETAILED BREAKDOWN:")
        print("=" * 50)

        for folder_name, results in preview_results.items():
            if 'error' in results:
                print(f"\n❌ {folder_name}: Error - {results['error']}")
                continue

            print(f"\n📁 {folder_name}:")
            print(f"   Would delete: {results['would_delete']:,} messages")
            print(f"   Would preserve: {results['would_preserve']:,} messages")
            print(f"   Would validate: {results['would_validate']:,} domains")

            if 'categories' in results and results['categories']:
                print("   Categories:")
                for category, data in sorted(results['categories'].items(), key=lambda x: x[1]['count'], reverse=True):
                    print(f"     • {category}: {data['count']:,}")

        print("\nPress any key to continue...")
        from config.auth import get_single_key
        get_single_key()

# Export main classes and functions
__all__ = [
    'EmailProcessor',
    'FolderManager',
    'BatchProcessor',
    'PreviewModeHandler',
    'get_email_headers_batch_uid',
    'get_email_headers_single_uid',
    'compile_filter_patterns',
    'check_message_optimized',
    'get_provider_type',
    'get_provider_settings'
]