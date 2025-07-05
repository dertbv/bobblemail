#!/usr/bin/env python3
"""
Comprehensive Caching System for Atlas_Email
Provides multi-level caching with TTL, LRU eviction, and performance monitoring
"""

import time
import json
import hashlib
import threading
from typing import Any, Dict, Optional, Tuple, Callable
from collections import OrderedDict
from datetime import datetime, timedelta
from functools import wraps

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


class CacheEntry:
    """Represents a single cache entry with TTL and metadata"""
    
    def __init__(self, value: Any, ttl_seconds: int = 3600):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def access(self) -> Any:
        """Access the cache entry and update metadata"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    @performance_monitor("caching")
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            with monitor_operation("caching", "cache_get", {"key": key}):
                if key not in self.cache:
                    self.stats['misses'] += 1
                    return None
                
                entry = self.cache[key]
                
                # Check expiration
                if entry.is_expired():
                    del self.cache[key]
                    self.stats['expirations'] += 1
                    self.stats['misses'] += 1
                    return None
                
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                
                return entry.access()
    
    @performance_monitor("caching")
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        with self.lock:
            with monitor_operation("caching", "cache_set", {"key": key}):
                # Use provided TTL or default
                ttl_seconds = ttl if ttl is not None else self.default_ttl
                
                # Remove existing entry if present
                if key in self.cache:
                    del self.cache[key]
                
                # Add new entry
                self.cache[key] = CacheEntry(value, ttl_seconds)
                
                # Evict oldest if over capacity
                while len(self.cache) > self.max_size:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self.stats['evictions'] += 1
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expirations': 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self.stats['evictions'],
                'expirations': self.stats['expirations']
            }


class MultiLevelCache:
    """Multi-level cache system with different cache stores for different data types"""
    
    def __init__(self):
        # Different cache levels with different characteristics
        self.caches = {
            'classification': LRUCache(max_size=50000, default_ttl=7200),  # 2 hours
            'domain': LRUCache(max_size=20000, default_ttl=86400),  # 24 hours
            'geographic': LRUCache(max_size=10000, default_ttl=604800),  # 7 days
            'authentication': LRUCache(max_size=5000, default_ttl=3600),  # 1 hour
            'general': LRUCache(max_size=10000, default_ttl=3600)  # 1 hour
        }
        
        # Cache key generators for different types
        self.key_generators = {
            'classification': self._classification_key,
            'domain': self._domain_key,
            'geographic': self._geographic_key,
            'authentication': self._auth_key
        }
    
    def _classification_key(self, sender: str, subject: str, **kwargs) -> str:
        """Generate cache key for classification results"""
        content = f"{sender}:{subject}".lower()
        return hashlib.md5(content.encode()).hexdigest()
    
    def _domain_key(self, domain: str, **kwargs) -> str:
        """Generate cache key for domain validation"""
        return f"domain:{domain.lower()}"
    
    def _geographic_key(self, ip: str, **kwargs) -> str:
        """Generate cache key for geographic data"""
        return f"geo:{ip}"
    
    def _auth_key(self, sender: str, domain: str, **kwargs) -> str:
        """Generate cache key for authentication results"""
        return f"auth:{domain.lower()}:{sender.lower()}"
    
    @performance_monitor("caching")
    def get(self, cache_type: str, **key_params) -> Optional[Any]:
        """Get value from appropriate cache"""
        if cache_type not in self.caches:
            return None
        
        # Generate key
        if cache_type in self.key_generators:
            key = self.key_generators[cache_type](**key_params)
        else:
            key = key_params.get('key', '')
        
        return self.caches[cache_type].get(key)
    
    @performance_monitor("caching")
    def set(self, cache_type: str, value: Any, ttl: Optional[int] = None, **key_params):
        """Set value in appropriate cache"""
        if cache_type not in self.caches:
            return
        
        # Generate key
        if cache_type in self.key_generators:
            key = self.key_generators[cache_type](**key_params)
        else:
            key = key_params.get('key', '')
        
        self.caches[cache_type].set(key, value, ttl)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all cache levels"""
        return {
            cache_type: cache.get_stats()
            for cache_type, cache in self.caches.items()
        }
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear specific cache or all caches"""
        if cache_type:
            if cache_type in self.caches:
                self.caches[cache_type].clear()
        else:
            for cache in self.caches.values():
                cache.clear()


# Global cache instance
_cache_manager = MultiLevelCache()


# Decorator for automatic caching
def cached(cache_type: str, ttl: Optional[int] = None):
    """Decorator to automatically cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_value = _cache_manager.caches[cache_type].get(key)
            if cached_value is not None:
                return cached_value
            
            # Calculate and cache result
            with monitor_operation("caching", f"cache_miss_{cache_type}", {"function": func.__name__}):
                result = func(*args, **kwargs)
                _cache_manager.caches[cache_type].set(key, result, ttl)
                return result
        
        return wrapper
    return decorator


# Cache management functions
def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get global cache statistics"""
    return _cache_manager.get_all_stats()


def clear_cache(cache_type: Optional[str] = None):
    """Clear cache(s)"""
    _cache_manager.clear_cache(cache_type)


# Specific cache access functions
@performance_monitor("caching")
def get_classification_cache(sender: str, subject: str) -> Optional[Dict[str, Any]]:
    """Get cached classification result"""
    return _cache_manager.get('classification', sender=sender, subject=subject)


@performance_monitor("caching")
def set_classification_cache(sender: str, subject: str, result: Dict[str, Any], ttl: Optional[int] = None):
    """Cache classification result"""
    _cache_manager.set('classification', result, ttl, sender=sender, subject=subject)


@performance_monitor("caching")
def get_domain_cache(domain: str) -> Optional[Dict[str, Any]]:
    """Get cached domain validation result"""
    return _cache_manager.get('domain', domain=domain)


@performance_monitor("caching")
def set_domain_cache(domain: str, result: Dict[str, Any], ttl: Optional[int] = None):
    """Cache domain validation result"""
    _cache_manager.set('domain', result, ttl, domain=domain)


@performance_monitor("caching")
def get_geographic_cache(ip: str) -> Optional[Dict[str, Any]]:
    """Get cached geographic data"""
    return _cache_manager.get('geographic', ip=ip)


@performance_monitor("caching")
def set_geographic_cache(ip: str, result: Dict[str, Any], ttl: Optional[int] = None):
    """Cache geographic data"""
    _cache_manager.set('geographic', result, ttl, ip=ip)


@performance_monitor("caching")
def get_auth_cache(sender: str, domain: str) -> Optional[Dict[str, Any]]:
    """Get cached authentication result"""
    return _cache_manager.get('authentication', sender=sender, domain=domain)


@performance_monitor("caching")
def set_auth_cache(sender: str, domain: str, result: Dict[str, Any], ttl: Optional[int] = None):
    """Cache authentication result"""
    _cache_manager.set('authentication', result, ttl, sender=sender, domain=domain)


# Cache warming functions
@performance_monitor("caching")
def warm_domain_cache(domains: list):
    """Pre-populate domain cache with known domains"""
    for domain_info in domains:
        if isinstance(domain_info, dict) and 'domain' in domain_info:
            set_domain_cache(domain_info['domain'], domain_info, ttl=86400)  # 24 hours


@performance_monitor("caching")
def warm_geographic_cache(ip_data: list):
    """Pre-populate geographic cache with known IPs"""
    for geo_info in ip_data:
        if isinstance(geo_info, dict) and 'ip' in geo_info:
            set_geographic_cache(geo_info['ip'], geo_info, ttl=604800)  # 7 days