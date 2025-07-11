#!/usr/bin/env python3
"""
Database Management Module
Handles SQLite database operations, schema creation, and connection management
"""

import sqlite3
import os
from typing import List, Dict, Any, Tuple
from contextlib import contextmanager
import threading

# Performance monitoring
try:
    from atlas_email.utils.performance_monitor import performance_monitor, monitor_operation
except ImportError:
    # Fallback if performance monitoring not available
    def performance_monitor(category):
        def decorator(func):
            return func
        return decorator
    
    class monitor_operation:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

# Database configuration
import os
# Point to data directory from package root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DB_FILE = os.path.join(project_root, "data", "mail_filter.db")
DB_VERSION = 5  # Added processed_emails_bulletproof table to core schema

# SECURITY: Validate schema table name is safe SQL identifier
def _validate_table_name(table_name: str) -> str:
    """Validate table name contains only safe SQL identifier characters"""
    import re
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name

SCHEMA_VERSION_TABLE = _validate_table_name("schema_version")

class DatabaseManager:
    """Manages SQLite database operations with connection pooling and schema management"""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.local = threading.local()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file and schema exist"""
        if not os.path.exists(self.db_path):
            self._create_database()
        else:
            self._check_schema_version()
    
    def _create_database(self):
        """Create database with initial schema"""
        print(f"🔧 Creating database: {self.db_path}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create schema version table
            cursor.execute(f"""
                CREATE TABLE {SCHEMA_VERSION_TABLE} (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Core application tables
            self._create_core_tables(cursor)
            
            # Log and analytics tables
            self._create_log_tables(cursor)
            
            # Configuration tables
            self._create_config_tables(cursor)
            
            # Insert initial schema version
            cursor.execute(f"INSERT INTO {SCHEMA_VERSION_TABLE} (version) VALUES (?)", (DB_VERSION,))
            
            conn.commit()
            print("✅ Database created successfully")
    
    def _create_core_tables(self, cursor):
        """Create core application tables"""
        
        # Accounts table (replaces credentials JSON)
        cursor.execute("""
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address VARCHAR(255) UNIQUE NOT NULL,
                provider VARCHAR(50) NOT NULL,
                host VARCHAR(255) NOT NULL,
                port INTEGER NOT NULL,
                encrypted_password TEXT NOT NULL,
                target_folders TEXT,  -- JSON array of folder names
                folder_setup_complete BOOLEAN DEFAULT FALSE,
                provider_optimizations TEXT,  -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Processing sessions table
        cursor.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                folders_processed TEXT,  -- JSON array
                total_deleted INTEGER DEFAULT 0,
                total_preserved INTEGER DEFAULT 0,
                total_validated INTEGER DEFAULT 0,
                categories_summary TEXT,  -- JSON object
                session_type VARCHAR(20) DEFAULT 'manual',  -- manual, batch, preview
                is_preview BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        """)
        
        # Processed emails bulletproof table (main email tracking)
        cursor.execute("""
            CREATE TABLE processed_emails_bulletproof (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                session_id INTEGER,
                folder_name TEXT,
                uid TEXT,
                sender_email TEXT NOT NULL,
                sender_domain TEXT,
                subject TEXT NOT NULL,
                action TEXT NOT NULL CHECK (action IN ('DELETED', 'PRESERVED')),
                reason TEXT,
                category TEXT,
                confidence_score REAL,
                ml_validation_method TEXT,
                raw_data TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Domain analysis table
        cursor.execute("""
            CREATE TABLE domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain VARCHAR(255) UNIQUE NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_occurrences INTEGER DEFAULT 1,
                risk_score FLOAT DEFAULT 0.0,
                ml_confidence_scores TEXT,  -- JSON array
                validation_results TEXT,   -- JSON array
                associated_categories TEXT, -- JSON array
                action_taken VARCHAR(20),   -- DELETED, PRESERVED, UNKNOWN
                is_whitelisted BOOLEAN DEFAULT FALSE,
                notes TEXT
            )
        """)
        
        # Spam categories analysis
        cursor.execute("""
            CREATE TABLE spam_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(100) UNIQUE NOT NULL,
                total_count INTEGER DEFAULT 0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deletion_rate FLOAT DEFAULT 0.0,
                common_keywords TEXT,  -- JSON array
                associated_domains TEXT,  -- JSON array
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # User feedback table for ML training and system improvement
        cursor.execute("""
            CREATE TABLE user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_uid TEXT NOT NULL,
                session_id INTEGER,
                sender TEXT,
                subject TEXT,
                original_classification TEXT NOT NULL,
                user_classification TEXT,
                feedback_type TEXT NOT NULL,  -- 'correct', 'incorrect', 'false_positive'
                confidence_rating INTEGER,    -- 1-5 scale (optional)
                user_comments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_ip TEXT,
                account_email TEXT,
                processed BOOLEAN DEFAULT FALSE,  -- For ML pipeline processing
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_accounts_email ON accounts(email_address)")
        cursor.execute("CREATE INDEX idx_sessions_account ON sessions(account_id)")
        cursor.execute("CREATE INDEX idx_sessions_time ON sessions(start_time)")
        cursor.execute("CREATE INDEX idx_processed_emails_bulletproof_timestamp ON processed_emails_bulletproof(timestamp)")
        cursor.execute("CREATE INDEX idx_processed_emails_bulletproof_action ON processed_emails_bulletproof(action)")
        cursor.execute("CREATE INDEX idx_processed_emails_bulletproof_session ON processed_emails_bulletproof(session_id)")
        cursor.execute("CREATE INDEX idx_processed_emails_bulletproof_sender ON processed_emails_bulletproof(sender_email)")
        cursor.execute("CREATE INDEX idx_domains_domain ON domains(domain)")
        cursor.execute("CREATE INDEX idx_spam_categories_category ON spam_categories(category)")
        cursor.execute("CREATE INDEX idx_user_feedback_uid ON user_feedback(email_uid)")
        cursor.execute("CREATE INDEX idx_user_feedback_timestamp ON user_feedback(timestamp)")
        cursor.execute("CREATE INDEX idx_user_feedback_type ON user_feedback(feedback_type)")
    
    def _create_log_tables(self, cursor):
        """Create logging tables (replaces log file)"""
        
        # Main logs table (replaces mail_filter_imap_log.txt)
        cursor.execute("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level VARCHAR(10) NOT NULL,  -- DEBUG, INFO, WARN, ERROR
                category VARCHAR(50),        -- SESSION, EMAIL, DOMAIN, CONFIG, ERROR
                account_id INTEGER,
                session_id INTEGER,
                message TEXT NOT NULL,
                metadata TEXT,               -- JSON for additional structured data
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Performance tracking
        cursor.execute("""
            CREATE TABLE performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id INTEGER,
                operation_type VARCHAR(50),
                duration_seconds FLOAT,
                items_processed INTEGER,
                memory_usage_mb FLOAT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Error tracking
        cursor.execute("""
            CREATE TABLE error_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id INTEGER,
                error_type VARCHAR(100),
                error_message TEXT,
                stack_trace TEXT,
                context_data TEXT,  -- JSON
                resolved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # Create indexes for log queries
        cursor.execute("CREATE INDEX idx_logs_timestamp ON logs(timestamp)")
        cursor.execute("CREATE INDEX idx_logs_level ON logs(level)")
        cursor.execute("CREATE INDEX idx_logs_category ON logs(category)")
        cursor.execute("CREATE INDEX idx_logs_session ON logs(session_id)")
        cursor.execute("CREATE INDEX idx_performance_session ON performance_metrics(session_id)")
        cursor.execute("CREATE INDEX idx_errors_timestamp ON error_reports(timestamp)")
        cursor.execute("CREATE INDEX idx_errors_resolved ON error_reports(resolved)")
    
    def _create_config_tables(self, cursor):
        """Create configuration tables"""
        
        # Application configuration (replaces JSON files)
        cursor.execute("""
            CREATE TABLE configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,  -- NULL for global config
                config_type VARCHAR(50) NOT NULL,  -- FILTERS, ML_SETTINGS, PROVIDER, etc.
                config_key VARCHAR(100) NOT NULL,
                config_value TEXT,  -- JSON or plain text
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                UNIQUE(account_id, config_type, config_key)
            )
        """)
        
        # Filter terms (replaces my_keywords.txt)
        cursor.execute("""
            CREATE TABLE filter_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term VARCHAR(255) NOT NULL,
                category VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(50) DEFAULT 'user',
                confidence_threshold FLOAT DEFAULT 0.5
            )
        """)
        
        # ML settings (replaces ml_settings.json)
        cursor.execute("""
            CREATE TABLE ml_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,  -- JSON
                description TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_config_type ON configurations(config_type)")
        cursor.execute("CREATE INDEX idx_config_account ON configurations(account_id)")
        cursor.execute("CREATE INDEX idx_filter_terms_active ON filter_terms(is_active)")
        cursor.execute("CREATE INDEX idx_ml_settings_active ON ml_settings(is_active)")
    
    def _check_schema_version(self):
        """Check and upgrade schema if needed"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT MAX(version) FROM {SCHEMA_VERSION_TABLE}")
                current_version = cursor.fetchone()[0]
                
                if current_version < DB_VERSION:
                    print(f"🔄 Upgrading database schema from v{current_version} to v{DB_VERSION}")
                    self._upgrade_schema(cursor, current_version)
                    cursor.execute(f"INSERT INTO {SCHEMA_VERSION_TABLE} (version) VALUES (?)", (DB_VERSION,))
                    conn.commit()
        except sqlite3.Error:
            # Schema version table doesn't exist, recreate database
            print("⚠️  Schema version table missing, recreating database...")
            os.remove(self.db_path)
            self._create_database()
    
    def _upgrade_schema(self, cursor, current_version):
        """Upgrade database schema"""
        if current_version < 2:
            # Version 2: Add user_feedback table
            print("🔄 Adding user_feedback table...")
            cursor.execute("""
                CREATE TABLE user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_uid TEXT NOT NULL,
                    session_id INTEGER,
                    sender TEXT,
                    subject TEXT,
                    original_classification TEXT NOT NULL,
                    user_classification TEXT,
                    feedback_type TEXT NOT NULL,  -- 'correct', 'incorrect', 'false_positive'
                    confidence_rating INTEGER,    -- 1-5 scale (optional)
                    user_comments TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_ip TEXT,
                    account_email TEXT,
                    processed BOOLEAN DEFAULT FALSE,  -- For ML pipeline processing
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Add indexes for the new table
            cursor.execute("CREATE INDEX idx_user_feedback_uid ON user_feedback(email_uid)")
            cursor.execute("CREATE INDEX idx_user_feedback_timestamp ON user_feedback(timestamp)")
            cursor.execute("CREATE INDEX idx_user_feedback_type ON user_feedback(feedback_type)")
            print("✅ User feedback table created successfully")
        
        if current_version < 3:
            # Version 3: Add user analytics and immediate deletions tables
            print("🔄 Adding user analytics and immediate deletions tables...")
            
            # User analytics table for tracking contributions
            cursor.execute("""
                CREATE TABLE user_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_date DATE DEFAULT CURRENT_DATE,
                    emails_analyzed INTEGER DEFAULT 0,
                    feedback_given INTEGER DEFAULT 0,
                    emails_deleted INTEGER DEFAULT 0,
                    accuracy_contributions INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Immediate deletions tracking table
            cursor.execute("""
                CREATE TABLE immediate_deletions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT NOT NULL,
                    email_uid TEXT NOT NULL,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_feedback_id INTEGER,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    provider TEXT,
                    folder_name TEXT,
                    FOREIGN KEY (user_feedback_id) REFERENCES user_feedback(id)
                )
            """)
            
            # Add contributed_to_accuracy column to user_feedback table
            cursor.execute("""
                ALTER TABLE user_feedback 
                ADD COLUMN contributed_to_accuracy BOOLEAN DEFAULT FALSE
            """)
            
            # Create indexes for new tables
            cursor.execute("CREATE INDEX idx_user_analytics_date ON user_analytics(session_date)")
            cursor.execute("CREATE INDEX idx_immediate_deletions_account ON immediate_deletions(account_name)")
            cursor.execute("CREATE INDEX idx_immediate_deletions_timestamp ON immediate_deletions(deleted_at)")
            cursor.execute("CREATE INDEX idx_immediate_deletions_success ON immediate_deletions(success)")
            
            print("✅ User analytics and immediate deletions tables created successfully")
        
        if current_version < 4:
            # Version 4: Add email flagging system
            print("🔄 Adding email flagging table...")
            
            # Email flags table for protecting emails from deletion
            cursor.execute("""
                CREATE TABLE email_flags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_uid TEXT NOT NULL,
                    folder_name TEXT NOT NULL,
                    account_id INTEGER NOT NULL,
                    session_id INTEGER,
                    sender_email TEXT,
                    subject TEXT,
                    flag_type TEXT DEFAULT 'PROTECT',
                    flag_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Create indexes for efficient flagging queries
            cursor.execute("CREATE INDEX idx_email_flags_uid_folder_account ON email_flags(email_uid, folder_name, account_id)")
            cursor.execute("CREATE INDEX idx_email_flags_account ON email_flags(account_id)")
            cursor.execute("CREATE INDEX idx_email_flags_active ON email_flags(is_active)")
            cursor.execute("CREATE INDEX idx_email_flags_created ON email_flags(created_at)")
            
            # Create unique constraint to prevent duplicate flags
            cursor.execute("CREATE UNIQUE INDEX idx_email_flags_unique ON email_flags(email_uid, folder_name, account_id) WHERE is_active = TRUE")
            
            print("✅ Email flagging table created successfully")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        # Create fresh connection for each operation to prevent locks
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Enable foreign keys but disable WAL mode to reduce file handles
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = DELETE")
        
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            # Always close connection to prevent locks
            conn.close()
    
    def close_connection(self):
        """Close thread-local connection (deprecated - connections now auto-close)"""
        # With the new get_connection() implementation, connections are automatically closed
        # This method is kept for backward compatibility but is no longer needed
        pass
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """Execute INSERT query and return last row ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table row counts - SECURITY: validate all table names
            tables = ['accounts', 'sessions', 'processed_emails_bulletproof', 'domains', 
                     'spam_categories', 'logs', 'configurations', 'filter_terms']
            
            for table in tables:
                # SECURITY: Validate table name before SQL interpolation
                validated_table = _validate_table_name(table)
                cursor.execute(f"SELECT COUNT(*) FROM {validated_table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Database file size
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
            
            # Recent activity
            cursor.execute("SELECT COUNT(*) FROM logs WHERE timestamp > datetime('now', '-24 hours')")
            stats['logs_last_24h'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE start_time > datetime('now', '-7 days')")
            stats['sessions_last_7d'] = cursor.fetchone()[0]
        
        return stats
    
    def add_to_whitelist(self, email_or_domain: str, notes: str = "Manually whitelisted") -> bool:
        """Add email address or domain to whitelist"""
        try:
            self.execute_update('''
                INSERT OR REPLACE INTO domains (domain, is_whitelisted, first_seen, last_seen, total_occurrences, risk_score, notes)
                VALUES (?, ?, datetime('now'), datetime('now'), 1, 0.0, ?)
            ''', (email_or_domain.lower(), True, notes))
            return True
        except Exception as e:
            print(f"Failed to add {email_or_domain} to whitelist: {e}")
            return False
    
    def remove_from_whitelist(self, email_or_domain: str) -> bool:
        """Remove email address or domain from whitelist"""
        try:
            self.execute_update('''
                UPDATE domains SET is_whitelisted = FALSE, notes = notes || ' [Removed from whitelist]'
                WHERE domain = ?
            ''', (email_or_domain.lower(),))
            return True
        except Exception as e:
            print(f"Failed to remove {email_or_domain} from whitelist: {e}")
            return False
    
    def get_whitelisted_addresses(self) -> List[Dict[str, Any]]:
        """Get all whitelisted email addresses and domains"""
        try:
            result = self.execute_query('''
                SELECT domain, first_seen, last_seen, total_occurrences, notes
                FROM domains 
                WHERE is_whitelisted = TRUE
                ORDER BY domain
            ''')
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Failed to get whitelisted addresses: {e}")
            return []
    
    def store_user_feedback(self, email_uid: str, feedback_type: str, original_classification: str,
                          user_classification: str = None, session_id: int = None, 
                          sender: str = None, subject: str = None, user_ip: str = None,
                          account_email: str = None, confidence_rating: int = None,
                          user_comments: str = None) -> int:
        """
        Store user feedback for email classification.
        
        Args:
            email_uid: Unique identifier for the email
            feedback_type: Type of feedback ('correct', 'incorrect', 'false_positive')
            original_classification: Original spam classification
            user_classification: User's corrected classification (optional)
            session_id: Associated session ID (optional)
            sender: Email sender (optional)
            subject: Email subject (optional)  
            user_ip: User's IP address (optional)
            account_email: User's account email (optional)
            confidence_rating: User's confidence rating 1-5 (optional)
            user_comments: Additional user comments (optional)
            
        Returns:
            ID of the inserted feedback record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_feedback (
                    email_uid, feedback_type, original_classification, user_classification,
                    session_id, sender, subject, user_ip, account_email, 
                    confidence_rating, user_comments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_uid, feedback_type, original_classification, user_classification,
                session_id, sender, subject, user_ip, account_email,
                confidence_rating, user_comments
            ))
            
            feedback_id = cursor.lastrowid
            conn.commit()
            return feedback_id
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get user feedback statistics for analytics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total feedback count
            cursor.execute("SELECT COUNT(*) FROM user_feedback")
            stats['total_feedback'] = cursor.fetchone()[0]
            
            # Feedback by type
            cursor.execute("""
                SELECT feedback_type, COUNT(*) 
                FROM user_feedback 
                GROUP BY feedback_type
            """)
            stats['feedback_by_type'] = dict(cursor.fetchall())
            
            # Recent feedback (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM user_feedback 
                WHERE timestamp > datetime('now', '-7 days')
            """)
            stats['feedback_last_7d'] = cursor.fetchone()[0]
            
            # Accuracy rate (correct vs total)
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN feedback_type = 'correct' THEN 1 END) as correct_count,
                    COUNT(*) as total_count
                FROM user_feedback
            """)
            result = cursor.fetchone()
            if result[1] > 0:
                stats['accuracy_rate'] = result[0] / result[1]
            else:
                stats['accuracy_rate'] = 0.0
                
            # False positive rate
            cursor.execute("""
                SELECT COUNT(*) FROM user_feedback 
                WHERE feedback_type = 'false_positive'
            """)
            false_positives = cursor.fetchone()[0]
            stats['false_positive_count'] = false_positives
            
            return stats
    
    def get_feedback_for_training(self, limit: int = 1000, processed: bool = False) -> List[Dict[str, Any]]:
        """
        Get feedback data for ML training.
        
        Args:
            limit: Maximum number of records to return
            processed: Whether to get processed or unprocessed feedback
            
        Returns:
            List of feedback records for training
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id, email_uid, sender, subject, original_classification,
                    user_classification, feedback_type, confidence_rating,
                    timestamp, account_email
                FROM user_feedback 
                WHERE processed = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (processed, limit))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def mark_feedback_processed(self, feedback_ids: List[int]):
        """Mark feedback records as processed by ML pipeline."""
        if not feedback_ids:
            return
        
        # SECURITY: Validate all IDs are positive integers (SQL injection protection)
        validated_ids = []
        for fid in feedback_ids:
            if not isinstance(fid, int):
                raise ValueError(f"Invalid feedback ID type: {type(fid).__name__}. Expected int.")
            if fid <= 0:
                raise ValueError(f"Invalid feedback ID value: {fid}. Must be positive integer.")
            validated_ids.append(fid)
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # SECURITY: Use parameterized query with validated integer IDs only
            placeholders = ','.join(['?'] * len(validated_ids))
            query = f"UPDATE user_feedback SET processed = TRUE WHERE id IN ({placeholders})"
            cursor.execute(query, validated_ids)
            conn.commit()
    
    # Email Flagging System Methods
    
    def flag_email_for_protection(self, email_uid: str, folder_name: str, account_id: int,
                                 session_id: int = None, sender_email: str = None, 
                                 subject: str = None, flag_reason: str = None,
                                 created_by: str = 'user') -> bool:
        """
        Flag an email for protection from deletion.
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            session_id: Session ID when flag was created (optional)
            sender_email: Email sender (optional, for display)
            subject: Email subject (optional, for display)
            flag_reason: Reason for flagging (optional)
            created_by: Who created the flag (default: 'user')
            
        Returns:
            True if flag was created successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if email is already flagged
                cursor.execute("""
                    SELECT id FROM email_flags 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                if cursor.fetchone():
                    print(f"Email {email_uid} in {folder_name} is already flagged")
                    return True  # Already flagged, consider success
                
                # Insert new flag
                cursor.execute("""
                    INSERT INTO email_flags (
                        email_uid, folder_name, account_id, session_id, 
                        sender_email, subject, flag_reason, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (email_uid, folder_name, account_id, session_id, 
                     sender_email, subject, flag_reason, created_by))
                
                conn.commit()
                print(f"✅ Flagged email {email_uid} in {folder_name} for protection")
                return True
                
        except Exception as e:
            print(f"❌ Failed to flag email {email_uid}: {e}")
            return False
    
    def flag_email_for_deletion(self, email_uid: str, folder_name: str, account_id: int,
                               session_id: int = None, sender_email: str = None, 
                               subject: str = None, flag_reason: str = None,
                               created_by: str = 'user') -> bool:
        """
        Flag an email for deletion (override preservation decision).
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            session_id: Session ID when flag was created (optional)
            sender_email: Email sender (optional, for display)
            subject: Email subject (optional, for display)
            flag_reason: Reason for flagging (optional)
            created_by: Who created the flag (default: 'user')
            
        Returns:
            True if flag was created successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if email is already flagged (any type)
                cursor.execute("""
                    SELECT id, flag_type FROM email_flags 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                existing_flag = cursor.fetchone()
                if existing_flag:
                    if existing_flag[1] == 'DELETE':
                        print(f"Email {email_uid} in {folder_name} is already flagged for deletion")
                        return True  # Already flagged for deletion, consider success
                    else:
                        # Update existing flag to DELETE type
                        cursor.execute("""
                            UPDATE email_flags 
                            SET flag_type = 'DELETE', flag_reason = ?, created_by = ?, created_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (flag_reason or 'User requested deletion', created_by, existing_flag[0]))
                        conn.commit()
                        print(f"✅ Updated flag for email {email_uid} in {folder_name} to deletion")
                        return True
                
                # Insert new deletion flag
                cursor.execute("""
                    INSERT INTO email_flags (
                        email_uid, folder_name, account_id, session_id, 
                        sender_email, subject, flag_type, flag_reason, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, 'DELETE', ?, ?)
                """, (email_uid, folder_name, account_id, session_id, 
                     sender_email, subject, flag_reason, created_by))
                
                conn.commit()
                print(f"✅ Flagged email {email_uid} in {folder_name} for deletion")
                return True
                
        except Exception as e:
            print(f"❌ Failed to flag email {email_uid} for deletion: {e}")
            return False
    
    def flag_email_for_research(self, email_uid: str, folder_name: str, account_id: int,
                               session_id: int = None, sender_email: str = None, 
                               subject: str = None, flag_reason: str = None,
                               created_by: str = 'user') -> bool:
        """
        Flag an email for research investigation.
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            session_id: Session ID when flag was created (optional)
            sender_email: Email sender (optional, for display)
            subject: Email subject (optional, for display)
            flag_reason: Reason for flagging (optional)
            created_by: Who created the flag (default: 'user')
            
        Returns:
            True if flag was created successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if email is already flagged for research
                cursor.execute("""
                    SELECT id, flag_type FROM email_flags 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? 
                    AND flag_type = 'RESEARCH' AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                existing_research_flag = cursor.fetchone()
                if existing_research_flag:
                    print(f"Email {email_uid} in {folder_name} is already flagged for research")
                    return True  # Already flagged for research, consider success
                
                # Insert new research flag
                cursor.execute("""
                    INSERT INTO email_flags (
                        email_uid, folder_name, account_id, session_id, 
                        sender_email, subject, flag_type, flag_reason, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, 'RESEARCH', ?, ?)
                """, (email_uid, folder_name, account_id, session_id, 
                     sender_email, subject, flag_reason, created_by))
                
                conn.commit()
                print(f"✅ Flagged email {email_uid} in {folder_name} for research investigation")
                return True
                
        except Exception as e:
            print(f"❌ Failed to flag email {email_uid} for research: {e}")
            return False
    
    def unflag_email(self, email_uid: str, folder_name: str, account_id: int) -> bool:
        """
        Remove protection flag from an email.
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            
        Returns:
            True if flag was removed successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Deactivate the flag (soft delete)
                cursor.execute("""
                    UPDATE email_flags 
                    SET is_active = FALSE 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"✅ Removed flag from email {email_uid} in {folder_name}")
                    return True
                else:
                    print(f"No active flag found for email {email_uid} in {folder_name}")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to unflag email {email_uid}: {e}")
            return False
    
    def is_email_flagged(self, email_uid: str, folder_name: str, account_id: int) -> bool:
        """
        Check if an email is flagged for protection.
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            
        Returns:
            True if email is flagged for protection, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id FROM email_flags 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? 
                    AND flag_type IN ('PROTECT', 'RESEARCH') AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            print(f"❌ Failed to check flag status for email {email_uid}: {e}")
            return False
    
    def is_email_flagged_for_deletion(self, email_uid: str, folder_name: str, account_id: int) -> bool:
        """
        Check if an email is flagged for deletion.
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            
        Returns:
            True if email is flagged for deletion, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id FROM email_flags 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? 
                    AND flag_type = 'DELETE' AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            print(f"❌ Failed to check deletion flag status for email {email_uid}: {e}")
            return False
    
    def get_email_flag_type(self, email_uid: str, folder_name: str, account_id: int) -> str:
        """
        Get the flag type for an email.
        
        Args:
            email_uid: IMAP UID of the email
            folder_name: Folder containing the email
            account_id: Account ID the email belongs to
            
        Returns:
            Flag type ('PROTECT', 'DELETE') or None if not flagged
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT flag_type FROM email_flags 
                    WHERE email_uid = ? AND folder_name = ? AND account_id = ? AND is_active = TRUE
                """, (email_uid, folder_name, account_id))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            print(f"❌ Failed to get flag type for email {email_uid}: {e}")
            return None
    
    def get_flagged_emails(self, account_id: int = None, limit: int = 100, flag_type: str = None) -> List[Dict[str, Any]]:
        """
        Get list of flagged emails.
        
        Args:
            account_id: Filter by account (optional)
            limit: Maximum number of results
            flag_type: Filter by flag type ('PROTECT', 'DELETE') (optional)
            
        Returns:
            List of flagged email records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = ["f.is_active = TRUE"]
                params = []
                
                if account_id:
                    where_conditions.append("f.account_id = ?")
                    params.append(account_id)
                
                if flag_type:
                    where_conditions.append("f.flag_type = ?")
                    params.append(flag_type)
                
                params.append(limit)
                
                where_clause = " AND ".join(where_conditions)
                
                cursor.execute(f"""
                    SELECT 
                        f.id, f.email_uid, f.folder_name, f.account_id,
                        f.sender_email, f.subject, f.flag_type, f.flag_reason,
                        f.created_at, f.created_by,
                        a.email_address as account_email
                    FROM email_flags f
                    LEFT JOIN accounts a ON f.account_id = a.id
                    WHERE {where_clause}
                    ORDER BY f.created_at DESC
                    LIMIT ?
                """, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ Failed to get flagged emails: {e}")
            return []
    
    def get_flagged_count(self, account_id: int = None, flag_type: str = None) -> int:
        """
        Get count of flagged emails.
        
        Args:
            account_id: Filter by account (optional)
            flag_type: Filter by flag type ('PROTECT', 'DELETE') (optional)
            
        Returns:
            Number of flagged emails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = ["is_active = TRUE"]
                params = []
                
                if account_id:
                    where_conditions.append("account_id = ?")
                    params.append(account_id)
                
                if flag_type:
                    where_conditions.append("flag_type = ?")
                    params.append(flag_type)
                
                where_clause = " AND ".join(where_conditions)
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM email_flags 
                    WHERE {where_clause}
                """, params)
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            print(f"❌ Failed to get flagged email count: {e}")
            return 0
    
    def get_research_flagged_emails_for_investigation(self, limit: int = 50) -> list:
        """
        Get emails flagged for research investigation with full details for ATLAS analysis.
        
        Args:
            limit: Maximum number of emails to return (default: 50)
            
        Returns:
            List of dictionaries with email details for research
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.row_factory = sqlite3.Row
                
                # Get research-flagged emails with all relevant information
                cursor.execute("""
                    SELECT 
                        f.email_uid,
                        f.folder_name,
                        f.sender_email,
                        f.subject,
                        f.flag_reason,
                        f.created_at as research_flagged_at,
                        pe.sender_email as processed_sender,
                        pe.subject as processed_subject,
                        pe.category,
                        pe.confidence,
                        pe.action_taken as final_action,
                        pe.preservation_reason,
                        pe.spam_indicators,
                        pe.timestamp as processed_at,
                        a.email_address as account_email
                    FROM email_flags f
                    LEFT JOIN processed_emails_bulletproof pe ON (
                        f.email_uid = pe.uid AND 
                        f.folder_name = pe.folder_name AND 
                        f.account_id = pe.session_id
                    )
                    LEFT JOIN accounts a ON f.account_id = a.id
                    WHERE f.flag_type = 'RESEARCH' AND f.is_active = TRUE
                    ORDER BY f.created_at DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ Failed to get research flagged emails: {e}")
            return []
    
    def cleanup_duplicates(self) -> int:
        """
        Clean up duplicate emails from processed_emails_bulletproof table.
        Keeps the most recent entry (MAX(rowid)) for each unique email.
        
        Returns:
            Number of duplicate entries deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count duplicates before deletion
                cursor.execute("""
                    SELECT COUNT(*) FROM processed_emails_bulletproof
                    WHERE rowid NOT IN (
                        SELECT MAX(rowid)
                        FROM processed_emails_bulletproof
                        WHERE uid IS NOT NULL AND uid != ''
                        GROUP BY uid, folder_name
                    )
                    AND uid IS NOT NULL AND uid != ''
                """)
                duplicates_count = cursor.fetchone()[0]
                
                if duplicates_count == 0:
                    print("✅ No duplicates found")
                    return 0
                
                # Delete duplicates
                cursor.execute("""
                    DELETE FROM processed_emails_bulletproof
                    WHERE rowid NOT IN (
                        SELECT MAX(rowid)
                        FROM processed_emails_bulletproof
                        WHERE uid IS NOT NULL AND uid != ''
                        GROUP BY uid, folder_name
                    )
                    AND uid IS NOT NULL AND uid != ''
                """)
                
                conn.commit()
                print(f"✅ Cleaned up {duplicates_count} duplicate entries")
                return duplicates_count
                
        except Exception as e:
            print(f"❌ Failed to cleanup duplicates: {e}")
            return 0
    
    def get_session_email_actions(self, limit: int = 100, action_filter: str = None) -> list:
        """
        Get recent email actions from processed_emails_bulletproof table
        
        Args:
            limit: Maximum number of records to return
            action_filter: Filter by action type ('DELETED', 'PRESERVED') - optional
            
        Returns:
            List of real email action records from the bulletproof table
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build the WHERE clause for action filtering
                where_clause = ""
                params = []
                
                if action_filter:
                    where_clause = "WHERE action = ?"
                    params.append(action_filter)
                
                params.append(limit)
                
                # Query the actual processed_emails_bulletproof table for real data
                cursor.execute(f"""
                    SELECT 
                        id,
                        timestamp,
                        session_id,
                        folder_name,
                        uid,
                        sender_email,
                        sender_domain,
                        subject,
                        action,
                        reason,
                        category,
                        confidence_score,
                        ml_validation_method,
                        raw_data,
                        created_at
                    FROM processed_emails_bulletproof
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, params)
                
                rows = cursor.fetchall()
                email_actions = []
                
                for row in rows:
                    email_actions.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'session_id': row['session_id'],
                        'folder_name': row['folder_name'] or 'Unknown Folder',
                        'uid': row['uid'] or 'Unknown UID',
                        'sender_email': row['sender_email'],
                        'sender_domain': row['sender_domain'] or '',
                        'subject': row['subject'],
                        'action': row['action'],
                        'reason': row['reason'] or '',
                        'category': row['category'] or 'Unknown',
                        'confidence_score': row['confidence_score'] or 0.0,
                        'ml_validation_method': row['ml_validation_method'] or 'Unknown',
                        'raw_data': row['raw_data'] or '',
                        'created_at': row['created_at'],
                        # Legacy fields for compatibility
                        'reviewed': 0,
                        'user_validated': 0,
                        'validation_timestamp': None,
                        'user_protected': 0,
                        'protection_date': None,
                        'protection_reason': None
                    })
                
                return email_actions
                
        except Exception as e:
            print(f"❌ Error getting email actions from bulletproof table: {e}")
            import traceback
            traceback.print_exc()
            return []

# Global database instance
db = DatabaseManager()

# Export main classes and functions
__all__ = [
    'DatabaseManager',
    'db',
    'DB_FILE',
    'DB_VERSION'
]