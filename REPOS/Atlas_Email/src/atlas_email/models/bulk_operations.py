#!/usr/bin/env python3
"""
Bulk Database Operations Module
Provides high-performance bulk insert/update operations with transaction batching
"""

import sqlite3
import time
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import json
import threading
from contextlib import contextmanager

# Performance monitoring
try:
    from atlas_email.utils.performance_monitor import performance_monitor, monitor_operation
except ImportError:
    # Fallback decorators
    def performance_monitor(category):
        def decorator(func):
            return func
        return decorator
    
    def monitor_operation(*args, **kwargs):
        from contextlib import contextmanager
        @contextmanager
        def noop():
            yield
        return noop()

from atlas_email.models.database import DatabaseManager


class BulkOperationManager:
    """Manages bulk database operations with automatic batching and error handling"""
    
    def __init__(self, db_manager: DatabaseManager, batch_size: int = 500):
        self.db_manager = db_manager
        self.batch_size = batch_size
        self._operation_queue = defaultdict(list)
        self._lock = threading.Lock()
        self._operation_count = 0
        
    @performance_monitor("database")
    def add_email_record(self, email_data: Dict[str, Any]):
        """Add email record to bulk insert queue"""
        with self._lock:
            self._operation_queue['processed_emails'].append(email_data)
            self._operation_count += 1
            
            # Auto-flush if batch size reached
            if len(self._operation_queue['processed_emails']) >= self.batch_size:
                self.flush_emails()
    
    @performance_monitor("database")
    def add_domain_record(self, domain_data: Dict[str, Any]):
        """Add domain record to bulk insert/update queue"""
        with self._lock:
            self._operation_queue['domains'].append(domain_data)
            
            # Auto-flush if batch size reached
            if len(self._operation_queue['domains']) >= self.batch_size:
                self.flush_domains()
    
    @performance_monitor("database")
    def add_flag_record(self, flag_data: Dict[str, Any]):
        """Add flag record to bulk insert queue"""
        with self._lock:
            self._operation_queue['flags'].append(flag_data)
            
            # Auto-flush if batch size reached
            if len(self._operation_queue['flags']) >= self.batch_size:
                self.flush_flags()
    
    @performance_monitor("database")
    def flush_all(self):
        """Flush all pending operations"""
        with monitor_operation("database", "bulk_flush_all"):
            self.flush_emails()
            self.flush_domains()
            self.flush_flags()
            self.flush_analytics()
    
    @performance_monitor("database")
    def flush_emails(self):
        """Bulk insert pending email records"""
        with self._lock:
            emails = self._operation_queue['processed_emails']
            if not emails:
                return
            
            # Clear queue
            self._operation_queue['processed_emails'] = []
        
        with monitor_operation("database", "bulk_insert_emails", {"count": len(emails)}):
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Prepare bulk insert data
                    insert_data = []
                    for email in emails:
                        insert_data.append((
                            email.get('uid'),
                            email.get('folder_name'),
                            email.get('sender'),
                            email.get('sender_domain'),
                            email.get('subject'),
                            email.get('date_received'),
                            email.get('processing_timestamp', datetime.now().isoformat()),
                            email.get('ml_enabled', True),
                            email.get('result'),
                            email.get('confidence', 0.0),
                            email.get('method', 'UNKNOWN'),
                            email.get('account_id'),
                            email.get('preview_shown', False),
                            email.get('ab_variant'),
                            email.get('predicted_category'),
                            email.get('category_confidence', 0.0),
                            email.get('result_4category'),
                            email.get('confidence_4category', 0.0),
                            email.get('subcategory_4category')
                        ))
                    
                    # Bulk insert
                    cursor.executemany("""
                        INSERT OR REPLACE INTO processed_emails_bulletproof (
                            uid, folder_name, sender, sender_domain, subject,
                            date_received, processing_timestamp, ml_enabled,
                            result, confidence, method, account_id,
                            preview_shown, ab_variant, predicted_category,
                            category_confidence, result_4category,
                            confidence_4category, subcategory_4category
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, insert_data)
                    
                    conn.commit()
                    
                    # Log performance
                    from atlas_email.models.db_logger import write_log
                    write_log(f"Bulk inserted {len(emails)} email records", False)
                    
                except Exception as e:
                    conn.rollback()
                    write_log(f"Bulk email insert failed: {e}", True)
                    # Re-queue failed operations
                    with self._lock:
                        self._operation_queue['processed_emails'].extend(emails)
                    raise
    
    @performance_monitor("database")
    def flush_domains(self):
        """Bulk insert/update pending domain records"""
        with self._lock:
            domains = self._operation_queue['domains']
            if not domains:
                return
            
            # Clear queue
            self._operation_queue['domains'] = []
        
        with monitor_operation("database", "bulk_upsert_domains", {"count": len(domains)}):
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Group by operation type
                    inserts = []
                    updates = []
                    
                    for domain in domains:
                        # Check if domain exists
                        cursor.execute("SELECT id FROM domains WHERE domain = ?", (domain['domain'],))
                        exists = cursor.fetchone()
                        
                        if exists:
                            updates.append(domain)
                        else:
                            inserts.append(domain)
                    
                    # Bulk insert new domains
                    if inserts:
                        insert_data = [(
                            d['domain'],
                            d.get('first_seen', datetime.now().isoformat()),
                            d.get('last_seen', datetime.now().isoformat()),
                            d.get('occurrences', 1),
                            d.get('is_valid', None),
                            d.get('validation_timestamp'),
                            d.get('domain_type'),
                            d.get('registrar'),
                            d.get('creation_date'),
                            d.get('expiry_date'),
                            d.get('dns_records', '{}'),
                            d.get('whois_data', '{}'),
                            d.get('geo_country_code'),
                            d.get('geo_country_name'),
                            d.get('geo_risk_score', 0.0),
                            d.get('geo_registrar'),
                            d.get('geo_analysis_timestamp')
                        ) for d in inserts]
                        
                        cursor.executemany("""
                            INSERT INTO domains (
                                domain, first_seen, last_seen, occurrences,
                                is_valid, validation_timestamp, domain_type,
                                registrar, creation_date, expiry_date,
                                dns_records, whois_data, geo_country_code,
                                geo_country_name, geo_risk_score, geo_registrar,
                                geo_analysis_timestamp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, insert_data)
                    
                    # Bulk update existing domains
                    if updates:
                        for domain in updates:
                            cursor.execute("""
                                UPDATE domains SET
                                    last_seen = ?,
                                    occurrences = occurrences + 1,
                                    is_valid = COALESCE(?, is_valid),
                                    validation_timestamp = COALESCE(?, validation_timestamp),
                                    domain_type = COALESCE(?, domain_type),
                                    geo_country_code = COALESCE(?, geo_country_code),
                                    geo_country_name = COALESCE(?, geo_country_name),
                                    geo_risk_score = COALESCE(?, geo_risk_score)
                                WHERE domain = ?
                            """, (
                                datetime.now().isoformat(),
                                domain.get('is_valid'),
                                domain.get('validation_timestamp'),
                                domain.get('domain_type'),
                                domain.get('geo_country_code'),
                                domain.get('geo_country_name'),
                                domain.get('geo_risk_score'),
                                domain['domain']
                            ))
                    
                    conn.commit()
                    
                    from atlas_email.models.db_logger import write_log
                    write_log(f"Bulk processed {len(domains)} domain records ({len(inserts)} new, {len(updates)} updated)", False)
                    
                except Exception as e:
                    conn.rollback()
                    write_log(f"Bulk domain operation failed: {e}", True)
                    # Re-queue failed operations
                    with self._lock:
                        self._operation_queue['domains'].extend(domains)
                    raise
    
    @performance_monitor("database")
    def flush_flags(self):
        """Bulk insert pending flag records"""
        with self._lock:
            flags = self._operation_queue['flags']
            if not flags:
                return
            
            # Clear queue
            self._operation_queue['flags'] = []
        
        with monitor_operation("database", "bulk_insert_flags", {"count": len(flags)}):
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    insert_data = [(
                        f['uid'],
                        f['folder_name'],
                        f['account_id'],
                        f.get('flag_type', 'preview'),
                        f.get('flagged_at', datetime.now().isoformat()),
                        f.get('review_status', 'pending'),
                        f.get('reviewed_at'),
                        f.get('action_taken'),
                        f.get('notes')
                    ) for f in flags]
                    
                    cursor.executemany("""
                        INSERT OR REPLACE INTO flags (
                            uid, folder_name, account_id, flag_type,
                            flagged_at, review_status, reviewed_at,
                            action_taken, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, insert_data)
                    
                    conn.commit()
                    
                    from atlas_email.models.db_logger import write_log
                    write_log(f"Bulk inserted {len(flags)} flag records", False)
                    
                except Exception as e:
                    conn.rollback()
                    write_log(f"Bulk flag insert failed: {e}", True)
                    # Re-queue failed operations
                    with self._lock:
                        self._operation_queue['flags'].extend(flags)
                    raise
    
    @performance_monitor("database")
    def flush_analytics(self):
        """Bulk insert/update analytics records"""
        with self._lock:
            analytics = self._operation_queue['analytics']
            if not analytics:
                return
            
            # Clear queue
            self._operation_queue['analytics'] = []
        
        with monitor_operation("database", "bulk_upsert_analytics", {"count": len(analytics)}):
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Group analytics by date/category/type for aggregation
                    aggregated = defaultdict(lambda: {"value": 0, "metadata": {}})
                    
                    for record in analytics:
                        key = (
                            record.get('date', datetime.now().date().isoformat()),
                            record['category'],
                            record.get('type', 'count')
                        )
                        aggregated[key]['value'] += record.get('value', 1)
                        
                        # Merge metadata
                        if 'metadata' in record:
                            aggregated[key]['metadata'].update(record['metadata'])
                    
                    # Bulk upsert
                    for (date, category, type_), data in aggregated.items():
                        cursor.execute("""
                            INSERT INTO analytics (date, category, type, value, metadata)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(date, category, type) DO UPDATE SET
                                value = value + excluded.value,
                                metadata = json_patch(metadata, excluded.metadata)
                        """, (date, category, type_, data['value'], json.dumps(data['metadata'])))
                    
                    conn.commit()
                    
                    from atlas_email.models.db_logger import write_log
                    write_log(f"Bulk processed {len(aggregated)} analytics records", False)
                    
                except Exception as e:
                    conn.rollback()
                    write_log(f"Bulk analytics operation failed: {e}", True)
                    # Re-queue failed operations
                    with self._lock:
                        self._operation_queue['analytics'].extend(analytics)
                    raise
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get current queue statistics"""
        with self._lock:
            return {
                'processed_emails': len(self._operation_queue['processed_emails']),
                'domains': len(self._operation_queue['domains']),
                'flags': len(self._operation_queue['flags']),
                'analytics': len(self._operation_queue['analytics']),
                'total_operations': self._operation_count
            }
    
    @contextmanager
    def batch_context(self):
        """Context manager for batch operations"""
        try:
            yield self
        finally:
            # Flush all pending operations on exit
            self.flush_all()


# Global bulk operation instance (singleton pattern)
_bulk_manager = None

def get_bulk_manager(db_manager: Optional[DatabaseManager] = None, batch_size: int = 500) -> BulkOperationManager:
    """Get or create the global bulk operation manager"""
    global _bulk_manager
    
    if _bulk_manager is None:
        if db_manager is None:
            db_manager = DatabaseManager()
        _bulk_manager = BulkOperationManager(db_manager, batch_size)
    
    return _bulk_manager


# Convenience functions for direct usage
@performance_monitor("database")
def bulk_insert_emails(emails: List[Dict[str, Any]], batch_size: int = 500):
    """Bulk insert email records"""
    manager = get_bulk_manager(batch_size=batch_size)
    
    with manager.batch_context():
        for email in emails:
            manager.add_email_record(email)


@performance_monitor("database")
def bulk_upsert_domains(domains: List[Dict[str, Any]], batch_size: int = 500):
    """Bulk insert/update domain records"""
    manager = get_bulk_manager(batch_size=batch_size)
    
    with manager.batch_context():
        for domain in domains:
            manager.add_domain_record(domain)


@performance_monitor("database")
def bulk_insert_flags(flags: List[Dict[str, Any]], batch_size: int = 500):
    """Bulk insert flag records"""
    manager = get_bulk_manager(batch_size=batch_size)
    
    with manager.batch_context():
        for flag in flags:
            manager.add_flag_record(flag)