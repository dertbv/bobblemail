#!/usr/bin/env python3
"""
Database Credential Manager
Secure database-based credential storage replacing JSON files
"""

import json
import base64
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import getpass
from atlas_email.models.database import db
from atlas_email.models.db_logger import logger, LogCategory

# Optional cryptography import
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: cryptography package not found. Install with: pip install cryptography")
    print("   Passwords will be stored in plain text until cryptography is installed.")
    CRYPTO_AVAILABLE = False

class DatabaseCredentialManager:
    """Secure database credential management with encryption"""
    
    def __init__(self):
        self.encryption_key = None
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists or create one"""
        if not CRYPTO_AVAILABLE:
            self.encryption_key = None
            return
            
        # Check if encryption key exists in config
        key_config = db.execute_query("""
            SELECT config_value FROM configurations 
            WHERE config_type = 'SYSTEM' AND config_key = 'encryption_salt'
        """)
        
        if not key_config:
            # Generate new salt and store it
            salt = os.urandom(16)
            salt_b64 = base64.b64encode(salt).decode()
            
            db.execute_insert("""
                INSERT INTO configurations (config_type, config_key, config_value)
                VALUES ('SYSTEM', 'encryption_salt', ?)
            """, (salt_b64,))
            
            logger.info("Generated new encryption salt for credential storage", 
                       category=LogCategory.AUTH)
        else:
            salt = base64.b64decode(key_config[0]['config_value'])
        
        # Derive encryption key from master password
        self._derive_encryption_key(salt)
    
    def _derive_encryption_key(self, salt: bytes):
        """Derive encryption key from master password"""
        if not CRYPTO_AVAILABLE:
            return
            
        # For now, use a default password. In production, this should be:
        # 1. Prompted from user on first run
        # 2. Stored securely in system keychain
        # 3. Or use system-specific secure storage
        
        master_password = "mail_filter_2024_secure"  # TODO: Make this configurable
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.encryption_key = Fernet(key)
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage"""
        if not CRYPTO_AVAILABLE or self.encryption_key is None:
            # Store as plain text with warning prefix
            return f"PLAIN:{password}"
        return self.encryption_key.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password from storage"""
        if encrypted_password.startswith("PLAIN:"):
            # Plain text password
            return encrypted_password[6:]  # Remove "PLAIN:" prefix
        
        if not CRYPTO_AVAILABLE or self.encryption_key is None:
            # Fallback for encrypted passwords when crypto not available
            logger.warn("Cannot decrypt password - cryptography package not available", 
                       category=LogCategory.AUTH)
            return ""
            
        return self.encryption_key.decrypt(encrypted_password.encode()).decode()
    
    def save_credentials(self, account: Dict[str, Any]) -> bool:
        """
        Save account credentials to database with encryption
        
        Args:
            account: Account dictionary with credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt the password
            encrypted_password = self._encrypt_password(account['password'])
            
            # Prepare data for database
            target_folders_json = json.dumps(account.get('target_folders', []))
            provider_opts_json = json.dumps(account.get('provider_optimizations', {}))
            
            # Check if account already exists
            existing = db.execute_query("""
                SELECT id FROM accounts WHERE email_address = ?
            """, (account['email_address'],))
            
            if existing:
                # Update existing account
                account_id = existing[0]['id']
                db.execute_update("""
                    UPDATE accounts SET
                        provider = ?, host = ?, port = ?, encrypted_password = ?,
                        target_folders = ?, folder_setup_complete = ?,
                        provider_optimizations = ?, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    account['provider'],
                    account['host'],
                    account['port'],
                    encrypted_password,
                    target_folders_json,
                    account.get('folder_setup_complete', False),
                    provider_opts_json,
                    account_id
                ))
                
                logger.info(f"Updated credentials for {account['email_address']}", 
                           category=LogCategory.AUTH,
                           metadata={"account_id": account_id, "provider": account['provider']})
            else:
                # Insert new account
                account_id = db.execute_insert("""
                    INSERT INTO accounts 
                    (email_address, provider, host, port, encrypted_password,
                     target_folders, folder_setup_complete, provider_optimizations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account['email_address'],
                    account['provider'],
                    account['host'],
                    account['port'],
                    encrypted_password,
                    target_folders_json,
                    account.get('folder_setup_complete', False),
                    provider_opts_json
                ))
                
                logger.info(f"Saved new credentials for {account['email_address']}", 
                           category=LogCategory.AUTH,
                           metadata={"account_id": account_id, "provider": account['provider']})
            
            return True
            
        except Exception as e:
            logger.error(e, "save_credentials")
            return False
    
    def load_credentials(self) -> List[Dict[str, Any]]:
        """
        Load all saved credentials from database
        
        Returns:
            List of account dictionaries with decrypted passwords
        """
        try:
            accounts_data = db.execute_query("""
                SELECT id, email_address, provider, host, port, encrypted_password,
                       target_folders, folder_setup_complete, provider_optimizations,
                       created_at, last_used, is_active
                FROM accounts 
                WHERE is_active = TRUE
                ORDER BY last_used DESC
            """)
            
            accounts = []
            for row in accounts_data:
                try:
                    # Decrypt password
                    password = self._decrypt_password(row['encrypted_password'])
                    
                    # Parse JSON fields
                    target_folders = json.loads(row['target_folders']) if row['target_folders'] else []
                    provider_opts = json.loads(row['provider_optimizations']) if row['provider_optimizations'] else {}
                    
                    account = {
                        'id': row['id'],
                        'email_address': row['email_address'],
                        'provider': row['provider'],
                        'host': row['host'],
                        'port': row['port'],
                        'password': password,
                        'target_folders': target_folders,
                        'folder_setup_complete': row['folder_setup_complete'],
                        'provider_optimizations': provider_opts,
                        'created_at': row['created_at'],
                        'last_used': row['last_used']
                    }
                    accounts.append(account)
                    
                except Exception as e:
                    logger.warn(f"Failed to decrypt credentials for account ID {row['id']}: {e}",
                               category=LogCategory.AUTH)
                    continue
            # logger.debug(f"Loaded {len(accounts)} accounts from database",
            #             category=LogCategory.AUTH)
            
            return accounts
            
        except Exception as e:
            logger.error(e, "load_credentials")
            return []
    
    def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get specific account by email address"""
        accounts = self.load_credentials()
        for account in accounts:
            if account['email_address'] == email:
                return account
        return None
    
    def select_account(self) -> Optional[Dict[str, Any]]:
        """Interactive account selection with provider information"""
        accounts = self.load_credentials()
        if not accounts:
            print("No saved accounts found.")
            return None
        
        print("\n📧 SAVED ACCOUNTS:")
        print("-" * 60)
        for idx, account in enumerate(accounts):
            try:
                provider = account.get('provider', 'custom')
                provider_emoji = {
                    'icloud': '🍎',
                    'gmail': '📧', 
                    'outlook': '🏢',
                    'yahoo': '📮',
                    'aol': '📧',
                    'custom': '🔧'
                }.get(provider, '🔧')
                
                last_used = ""
                if account.get('last_used'):
                    try:
                        last_date = datetime.fromisoformat(account['last_used'])
                        last_used = f" (last used: {last_date.strftime('%Y-%m-%d')})"
                    except:
                        pass
                
                optimization_note = ""
                if provider == 'icloud':
                    optimization_note = " [Optimized]"
                
                print(f"{idx+1}. {provider_emoji} {account['email_address']} ({provider}){optimization_note}{last_used}")
            except Exception:
                continue
        
        print(f"{len(accounts)+1}. ➕ Add new account")
        print(f"{len(accounts)+2}. ❌ Cancel/Exit")
        print("-" * 60)
        
        # Import utils for choice handling
        from atlas_email.utils.general import get_user_choice
        
        # Create valid choices dynamically
        valid_choices = [str(i) for i in range(1, len(accounts) + 3)]
        
        choice = get_user_choice(f"Press a key (1-{len(accounts)+2}):", valid_choices)
        if choice is None:
            return "exit"
        
        idx = int(choice) - 1
        if idx == len(accounts):
            return None  # Add new account
        elif idx == len(accounts) + 1:
            return "exit"  # Cancel/Exit
        elif 0 <= idx < len(accounts):
            selected_account = accounts[idx]
            # Show provider-specific info
            provider = selected_account.get('provider', 'custom')
            if provider in ['icloud', 'gmail', 'outlook']:
                from atlas_email.utils.provider_utils import ProviderDetector
                notes = ProviderDetector.get_optimization_notes(provider)
                print(f"\n📋 {provider.upper()} ACCOUNT NOTES:")
                for note in notes:
                    print(f"   {note}")
                print()
            return selected_account
        else:
            return "exit"

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get specific account by ID"""
        try:
            row = db.execute_query("""
                SELECT id, email_address, provider, host, port, encrypted_password,
                       target_folders, folder_setup_complete, provider_optimizations,
                       created_at, last_used, is_active
                FROM accounts 
                WHERE id = ? AND is_active = TRUE
            """, (account_id,))
            
            if not row:
                return None
            
            row = row[0]
            
            # Decrypt password
            password = self._decrypt_password(row['encrypted_password'])
            
            # Parse JSON fields
            target_folders = json.loads(row['target_folders']) if row['target_folders'] else []
            provider_opts = json.loads(row['provider_optimizations']) if row['provider_optimizations'] else {}
            
            return {
                'id': row['id'],
                'email_address': row['email_address'],
                'provider': row['provider'],
                'host': row['host'],
                'port': row['port'],
                'password': password,
                'target_folders': target_folders,
                'folder_setup_complete': row['folder_setup_complete'],
                'provider_optimizations': provider_opts,
                'created_at': row['created_at'],
                'last_used': row['last_used']
            }
            
        except Exception as e:
            logger.error(e, f"get_account_by_id({account_id})")
            return None
    
    def update_folder_preferences(self, email_address: str, target_folders: List[str]) -> bool:
        """Update folder preferences for account"""
        try:
            target_folders_json = json.dumps(target_folders)
            
            rows_affected = db.execute_update("""
                UPDATE accounts SET 
                    target_folders = ?,
                    folder_setup_complete = TRUE
                WHERE email_address = ? AND is_active = TRUE
            """, (target_folders_json, email_address))
            
            if rows_affected > 0:
                logger.info(f"Updated folder preferences for {email_address}",
                           category=LogCategory.CONFIG,
                           metadata={"folders_count": len(target_folders)})
                return True
            else:
                logger.warn(f"No account found to update folder preferences: {email_address}",
                           category=LogCategory.CONFIG)
                return False
                
        except Exception as e:
            logger.error(e, f"update_folder_preferences({email_address})")
            return False
    
    def update_last_used(self, account_id: int):
        """Update last used timestamp for account"""
        try:
            db.execute_update("""
                UPDATE accounts SET last_used = CURRENT_TIMESTAMP WHERE id = ?
            """, (account_id,))
        except Exception as e:
            logger.error(e, f"update_last_used({account_id})")
    
    def delete_account(self, email_address: str) -> bool:
        """Soft delete account (mark as inactive)"""
        try:
            rows_affected = db.execute_update("""
                UPDATE accounts SET is_active = FALSE WHERE email_address = ?
            """, (email_address,))
            
            if rows_affected > 0:
                logger.info(f"Deleted account {email_address}",
                           category=LogCategory.AUTH,
                           metadata={"action": "account_deleted"})
                return True
            else:
                logger.warn(f"No account found to delete: {email_address}",
                           category=LogCategory.AUTH)
                return False
                
        except Exception as e:
            logger.error(e, f"delete_account({email_address})")
            return False
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """Get account statistics"""
        try:
            stats = {}
            
            # Total accounts
            result = db.execute_query("SELECT COUNT(*) as count FROM accounts WHERE is_active = TRUE")
            stats['total_accounts'] = result[0]['count']
            
            # Accounts by provider
            provider_stats = db.execute_query("""
                SELECT provider, COUNT(*) as count
                FROM accounts 
                WHERE is_active = TRUE
                GROUP BY provider
                ORDER BY count DESC
            """)
            stats['by_provider'] = {row['provider']: row['count'] for row in provider_stats}
            
            # Recently used accounts
            recent = db.execute_query("""
                SELECT COUNT(*) as count
                FROM accounts 
                WHERE is_active = TRUE AND last_used > datetime('now', '-7 days')
            """)
            stats['recently_used'] = recent[0]['count']
            
            # Accounts with folder setup
            setup_complete = db.execute_query("""
                SELECT COUNT(*) as count
                FROM accounts 
                WHERE is_active = TRUE AND folder_setup_complete = TRUE
            """)
            stats['setup_complete'] = setup_complete[0]['count']
            
            return stats
            
        except Exception as e:
            logger.error(e, "get_account_statistics")
            return {}
    
    def migrate_from_json(self, json_file_path: str) -> bool:
        """
        Migrate credentials from old JSON file to database
        
        Args:
            json_file_path: Path to existing credentials JSON file
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            if not os.path.exists(json_file_path):
                logger.info(f"No JSON file found at {json_file_path}, skipping migration",
                           category=LogCategory.AUTH)
                return True
            
            # Load JSON credentials
            with open(json_file_path, 'r') as f:
                json_accounts = json.load(f)
            
            migrated_count = 0
            failed_count = 0
            
            for account in json_accounts:
                if isinstance(account, dict) and 'email_address' in account:
                    try:
                        # Check if already exists in database
                        existing = db.execute_query("""
                            SELECT id FROM accounts WHERE email_address = ?
                        """, (account['email_address'],))
                        
                        if not existing:
                            # Migrate to database
                            if self.save_credentials(account):
                                migrated_count += 1
                                logger.debug(f"Migrated account: {account['email_address']}",
                                           category=LogCategory.AUTH)
                            else:
                                failed_count += 1
                        else:
                            logger.debug(f"Account already exists in database: {account['email_address']}",
                                        category=LogCategory.AUTH)
                    except Exception as e:
                        logger.warn(f"Failed to migrate account {account.get('email_address', 'unknown')}: {e}",
                                   category=LogCategory.AUTH)
                        failed_count += 1
            
            logger.info(f"Credential migration complete: {migrated_count} migrated, {failed_count} failed",
                       category=LogCategory.AUTH,
                       metadata={
                           "migrated_count": migrated_count,
                           "failed_count": failed_count,
                           "source_file": json_file_path
                       })
            
            return failed_count == 0
            
        except Exception as e:
            logger.error(e, f"migrate_from_json({json_file_path})")
            return False
    
    def export_to_json(self, output_file: str, include_passwords: bool = False) -> bool:
        """
        Export credentials to JSON file (for backup purposes)
        
        Args:
            output_file: Output file path
            include_passwords: Whether to include passwords (NOT recommended)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            accounts = self.load_credentials()
            
            # Remove sensitive data if not explicitly requested
            if not include_passwords:
                for account in accounts:
                    account.pop('password', None)
                    account.pop('id', None)  # Don't export internal DB IDs
            
            with open(output_file, 'w') as f:
                json.dump(accounts, f, indent=2, default=str)
            
            logger.info(f"Exported {len(accounts)} accounts to {output_file}",
                       category=LogCategory.AUTH,
                       metadata={
                           "exported_count": len(accounts),
                           "include_passwords": include_passwords,
                           "output_file": output_file
                       })
            
            return True
            
        except Exception as e:
            logger.error(e, f"export_to_json({output_file})")
            return False

# Global instance
db_credentials = DatabaseCredentialManager()

# Export main classes and functions
__all__ = [
    'DatabaseCredentialManager',
    'db_credentials'
]