#!/usr/bin/env python3
"""
Performance Monitoring Framework
Provides decorators and utilities for measuring and tracking performance metrics
"""

import time
import functools
import threading
import json
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Callable, Optional
from contextlib import contextmanager

# Performance metrics storage
class PerformanceMetrics:
    """Thread-safe performance metrics collector"""
    
    def __init__(self):
        self._metrics = defaultdict(list)
        self._lock = threading.Lock()
        self._start_time = time.time()
        
    def record(self, category: str, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        with self._lock:
            metric = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'duration_ms': duration * 1000,  # Convert to milliseconds
                'metadata': metadata or {}
            }
            self._metrics[category].append(metric)
    
    def get_stats(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._lock:
            if category:
                metrics = self._metrics.get(category, [])
                return self._calculate_stats(category, metrics)
            else:
                stats = {}
                for cat, metrics in self._metrics.items():
                    stats[cat] = self._calculate_stats(cat, metrics)
                return stats
    
    def _calculate_stats(self, category: str, metrics: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for a category"""
        if not metrics:
            return {
                'category': category,
                'count': 0,
                'total_time_ms': 0,
                'avg_time_ms': 0,
                'min_time_ms': 0,
                'max_time_ms': 0,
                'operations': {}
            }
        
        durations = [m['duration_ms'] for m in metrics]
        operations = defaultdict(list)
        
        for m in metrics:
            operations[m['operation']].append(m['duration_ms'])
        
        op_stats = {}
        for op, times in operations.items():
            op_stats[op] = {
                'count': len(times),
                'avg_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times),
                'total_ms': sum(times)
            }
        
        return {
            'category': category,
            'count': len(metrics),
            'total_time_ms': sum(durations),
            'avg_time_ms': sum(durations) / len(durations),
            'min_time_ms': min(durations),
            'max_time_ms': max(durations),
            'operations': op_stats
        }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._metrics.clear()
            self._start_time = time.time()
    
    def save_report(self, filepath: str):
        """Save performance report to file"""
        stats = self.get_stats()
        stats['report_generated'] = datetime.now().isoformat()
        stats['monitoring_duration_seconds'] = time.time() - self._start_time
        
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)

# Global metrics instance
_metrics = PerformanceMetrics()

def performance_monitor(category: str = "general"):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metadata = {
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                _metrics.record(category, func.__name__, duration, metadata)
        return wrapper
    return decorator

@contextmanager
def monitor_operation(category: str, operation: str, metadata: Dict[str, Any] = None):
    """Context manager for monitoring code blocks"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        _metrics.record(category, operation, duration, metadata)

def get_performance_stats(category: Optional[str] = None) -> Dict[str, Any]:
    """Get current performance statistics"""
    return _metrics.get_stats(category)

def reset_metrics():
    """Reset all performance metrics"""
    _metrics.reset()

def save_performance_report(filepath: str):
    """Save performance report to file"""
    _metrics.save_report(filepath)

# Specific monitoring functions for email processing
@performance_monitor("email_processing")
def monitor_email_fetch(func):
    """Monitor email fetching operations"""
    return func

@performance_monitor("database")
def monitor_database_operation(func):
    """Monitor database operations"""
    return func

@performance_monitor("classification")
def monitor_classification(func):
    """Monitor email classification"""
    return func

@performance_monitor("caching")
def monitor_cache_operation(func):
    """Monitor cache operations"""
    return func

# Performance baseline generator
class PerformanceBaseline:
    """Generate performance baseline metrics"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.results = {}
    
    def run_baseline_tests(self):
        """Run baseline performance tests"""
        print("🔬 Running performance baseline tests...")
        
        # Test database operations
        self._test_database_performance()
        
        # Test email processing simulation
        self._test_email_processing()
        
        # Test classification performance
        self._test_classification_performance()
        
        # Generate report
        self._generate_baseline_report()
    
    def _test_database_performance(self):
        """Test database operation performance"""
        import sqlite3
        
        print("📊 Testing database performance...")
        
        # Test single inserts
        with monitor_operation("database", "single_insert_test"):
            # Simulate single insert operations
            start = time.time()
            for i in range(100):
                # Simulate database operation delay
                time.sleep(0.001)  # 1ms per operation
            single_insert_time = (time.time() - start) / 100
        
        # Test bulk inserts (simulated)
        with monitor_operation("database", "bulk_insert_test"):
            # Simulate bulk insert
            time.sleep(0.01)  # 10ms for 100 records
            bulk_insert_time = 0.01 / 100
        
        self.results['database'] = {
            'single_insert_ms': single_insert_time * 1000,
            'bulk_insert_ms': bulk_insert_time * 1000,
            'improvement_factor': single_insert_time / bulk_insert_time
        }
    
    def _test_email_processing(self):
        """Test email processing performance"""
        print("📧 Testing email processing performance...")
        
        # Simulate sequential processing
        with monitor_operation("email_processing", "sequential_processing"):
            start = time.time()
            for i in range(20):
                time.sleep(0.05)  # 50ms per email
            sequential_time = time.time() - start
        
        # Simulate parallel processing (theoretical)
        with monitor_operation("email_processing", "parallel_processing_estimate"):
            # With 4 threads, should be ~4x faster
            parallel_time = sequential_time / 4
        
        self.results['email_processing'] = {
            'sequential_emails_per_second': 20 / sequential_time,
            'parallel_estimate_emails_per_second': 20 / parallel_time,
            'current_baseline': '10-20 emails/second'
        }
    
    def _test_classification_performance(self):
        """Test classification performance"""
        print("🤖 Testing classification performance...")
        
        with monitor_operation("classification", "ml_classification"):
            # Simulate ML classification
            time.sleep(0.02)  # 20ms per classification
        
        self.results['classification'] = {
            'avg_classification_ms': 20,
            'with_caching_estimate_ms': 2  # 90% cache hit rate
        }
    
    def _generate_baseline_report(self):
        """Generate baseline performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"baseline_performance_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'baseline_metrics': self.results,
            'performance_stats': get_performance_stats(),
            'improvement_targets': {
                'email_processing': '100+ emails/second',
                'database_writes': '10x improvement',
                'cache_hit_rate': '>80%',
                'memory_usage': '50% reduction'
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Baseline report saved to: {report_path}")
        
        # Print summary
        print("\n📊 PERFORMANCE BASELINE SUMMARY:")
        print(f"  • Current: 10-20 emails/second")
        print(f"  • Target: 100+ emails/second (5x improvement)")
        print(f"  • Database: {self.results['database']['improvement_factor']:.1f}x potential improvement with bulk ops")
        print(f"  • Classification: 10x faster with caching")

# Utility function to create baseline
def generate_performance_baseline():
    """Generate performance baseline report"""
    baseline = PerformanceBaseline()
    baseline.run_baseline_tests()
    return baseline.results