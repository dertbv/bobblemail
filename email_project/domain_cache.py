#!/usr/bin/env python3
"""
Domain Validation Cache
High-performance caching system for domain validation results
Eliminates 40.6% performance bottleneck from WHOIS lookups
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
from database import db

class DomainValidationCache:
    """
    Caches domain validation results to eliminate repeated WHOIS lookups
    """
    
    def __init__(self, cache_duration_hours: int = 24):
        """Initialize domain cache with configurable duration"""
        self.cache_duration_hours = cache_duration_hours
        self.db = db
        self._ensure_cache_table()
        
    def _ensure_cache_table(self):
        """Create domain cache table if it doesn't exist"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domain_validation_cache (
                    domain TEXT PRIMARY KEY,
                    validation_result TEXT NOT NULL,
                    validation_reason TEXT,
                    is_suspicious BOOLEAN,
                    provider_hint TEXT,
                    cached_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    whois_age_days INTEGER,
                    whois_creation_date TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_domain_cache_timestamp 
                ON domain_validation_cache(cached_timestamp)
            """)
            
            # Create index for access patterns
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_domain_cache_access 
                ON domain_validation_cache(last_accessed, access_count)
            """)
            
            conn.commit()
    
    def get_cached_validation(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached domain validation result if available and fresh
        
        Args:
            domain: Domain to check
            
        Returns:
            Cached validation result or None if not cached/expired
        """
        cutoff_time = datetime.now() - timedelta(hours=self.cache_duration_hours)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT validation_result, validation_reason, is_suspicious, 
                       provider_hint, whois_age_days, whois_creation_date,
                       cached_timestamp, access_count
                FROM domain_validation_cache 
                WHERE domain = ? AND cached_timestamp > ?
            """, (domain.lower(), cutoff_time.isoformat()))
            
            result = cursor.fetchone()
            
            if result:
                # Update access statistics
                cursor.execute("""
                    UPDATE domain_validation_cache 
                    SET access_count = access_count + 1, 
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE domain = ?
                """, (domain.lower(),))
                conn.commit()
                
                return {
                    'validation_result': result['validation_result'],
                    'validation_reason': result['validation_reason'],
                    'is_suspicious': bool(result['is_suspicious']),
                    'provider_hint': result['provider_hint'],
                    'whois_age_days': result['whois_age_days'],
                    'whois_creation_date': result['whois_creation_date'],
                    'cached_timestamp': result['cached_timestamp'],
                    'access_count': result['access_count'],
                    'cache_hit': True
                }
        
        return None
    
    def cache_validation_result(self, domain: str, validation_result: str, 
                              validation_reason: str, is_suspicious: bool,
                              provider_hint: str = None, whois_age_days: int = None,
                              whois_creation_date: datetime = None):
        """
        Cache domain validation result for future use
        
        Args:
            domain: Domain that was validated
            validation_result: Validation result ('SAFE', 'SUSPICIOUS', 'QUARANTINE')
            validation_reason: Human-readable reason for the result
            is_suspicious: Boolean indicating if domain is suspicious
            provider_hint: Provider context for the validation
            whois_age_days: Age of domain in days from WHOIS
            whois_creation_date: Domain creation date from WHOIS
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Use REPLACE to handle both insert and update cases
            cursor.execute("""
                REPLACE INTO domain_validation_cache 
                (domain, validation_result, validation_reason, is_suspicious, 
                 provider_hint, whois_age_days, whois_creation_date, 
                 cached_timestamp, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1, CURRENT_TIMESTAMP)
            """, (
                domain.lower(),
                validation_result,
                validation_reason,
                is_suspicious,
                provider_hint,
                whois_age_days,
                whois_creation_date.isoformat() if whois_creation_date else None
            ))
            
            conn.commit()
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries
        
        Returns:
            Number of entries removed
        """
        cutoff_time = datetime.now() - timedelta(hours=self.cache_duration_hours)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM domain_validation_cache 
                WHERE cached_timestamp < ?
            """, (cutoff_time.isoformat(),))
            
            removed_count = cursor.rowcount
            conn.commit()
            
        return removed_count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) as total FROM domain_validation_cache")
            total_entries = cursor.fetchone()['total']
            
            # Entries by validation result
            cursor.execute("""
                SELECT validation_result, COUNT(*) as count 
                FROM domain_validation_cache 
                GROUP BY validation_result
            """)
            by_result = {row['validation_result']: row['count'] for row in cursor.fetchall()}
            
            # Access statistics
            cursor.execute("""
                SELECT 
                    AVG(access_count) as avg_access,
                    MAX(access_count) as max_access,
                    SUM(access_count) as total_accesses
                FROM domain_validation_cache
            """)
            access_stats = cursor.fetchone()
            
            # Recent cache activity
            cutoff_recent = datetime.now() - timedelta(hours=1)
            cursor.execute("""
                SELECT COUNT(*) as recent_hits
                FROM domain_validation_cache 
                WHERE last_accessed > ?
            """, (cutoff_recent.isoformat(),))
            recent_hits = cursor.fetchone()['recent_hits']
            
            return {
                'total_entries': total_entries,
                'by_validation_result': by_result,
                'average_access_count': round(access_stats['avg_access'] or 0, 2),
                'max_access_count': access_stats['max_access'] or 0,
                'total_cache_hits': access_stats['total_accesses'] or 0,
                'recent_hits_1h': recent_hits,
                'cache_duration_hours': self.cache_duration_hours
            }
    
    def get_most_accessed_domains(self, limit: int = 10) -> list:
        """Get most frequently accessed cached domains"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT domain, validation_result, access_count, last_accessed
                FROM domain_validation_cache 
                ORDER BY access_count DESC, last_accessed DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_cache(self) -> int:
        """Clear all cache entries"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM domain_validation_cache")
            removed_count = cursor.rowcount
            conn.commit()
            
        return removed_count

# Global cache instance
domain_cache = DomainValidationCache()

# Note: cached_domain_validation moved to domain_validator.py to break circular dependency

def print_cache_statistics():
    """Print cache performance statistics"""
    stats = domain_cache.get_cache_statistics()
    
    print("🚀 DOMAIN VALIDATION CACHE STATISTICS")
    print("=" * 50)
    print(f"📊 Total Cached Domains: {stats['total_entries']:,}")
    print(f"⏱️  Cache Duration: {stats['cache_duration_hours']} hours")
    print(f"🎯 Total Cache Hits: {stats['total_cache_hits']:,}")
    print(f"📈 Recent Activity (1h): {stats['recent_hits_1h']} hits")
    print(f"📊 Average Access per Domain: {stats['average_access_count']}")
    print(f"🔥 Most Accessed Domain: {stats['max_access_count']} hits")
    
    print(f"\n📋 Cache Distribution:")
    for result, count in stats['by_validation_result'].items():
        percentage = (count / stats['total_entries'] * 100) if stats['total_entries'] > 0 else 0
        print(f"   • {result}: {count:,} ({percentage:.1f}%)")

if __name__ == "__main__":
    # Test and demonstrate cache functionality
    print("🧪 Testing Domain Validation Cache")
    
    # Test domains
    test_domains = [
        "gmail.com",
        "icloud.com", 
        "suspicious-domain-123.com",
        "test.example.com"
    ]
    
    print("\n🔍 Testing cache functionality...")
    for domain in test_domains:
        print(f"\n📧 Testing: {domain}")
        
        # First call (cache miss)
        import time
        start_time = time.perf_counter()
        result1 = cached_domain_validation(domain)
        first_time = time.perf_counter() - start_time
        print(f"   First call: {result1} ({first_time:.3f}s)")
        
        # Second call (cache hit)
        start_time = time.perf_counter() 
        result2 = cached_domain_validation(domain)
        second_time = time.perf_counter() - start_time
        print(f"   Second call: {result2} ({second_time:.3f}s)")
        
        speedup = first_time / second_time if second_time > 0 else float('inf')
        print(f"   ⚡ Speedup: {speedup:.1f}x faster")
    
    print("\n📊 Final Cache Statistics:")
    print_cache_statistics()