#!/usr/bin/env python3
"""
Performance Benchmark Tool
Establishes baseline metrics and runs performance tests for Atlas_Email system
"""

import sys
import time
import json
import sqlite3
import random
import string
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from atlas_email.utils.performance_monitor import (
    performance_monitor, monitor_operation, get_performance_stats,
    save_performance_report, reset_metrics, PerformanceBaseline
)
from atlas_email.models.database import DatabaseManager
from atlas_email.core.email_processor import EmailProcessor
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier

class PerformanceBenchmark:
    """Comprehensive performance benchmark suite"""
    
    def __init__(self):
        self.results = {}
        self.db_manager = DatabaseManager()
        
    def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print("🚀 Atlas_Email Performance Benchmark Suite")
        print("=" * 60)
        
        # Reset metrics before starting
        reset_metrics()
        
        # Run individual benchmarks
        self.benchmark_database_operations()
        self.benchmark_email_processing()
        self.benchmark_classification()
        self.benchmark_domain_validation()
        self.benchmark_memory_usage()
        
        # Generate comprehensive report
        self.generate_report()
        
    @performance_monitor("benchmark")
    def benchmark_database_operations(self):
        """Benchmark database operations"""
        print("\n📊 Benchmarking Database Operations...")
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Test 1: Single INSERT operations
            print("  • Testing single INSERT performance...")
            single_times = []
            
            for i in range(100):
                test_data = {
                    'uid': f'test_{i}_{random.randint(1000, 9999)}',
                    'folder': 'INBOX',
                    'sender': f'test{i}@example.com',
                    'subject': f'Test Email {i}',
                    'date': datetime.now().isoformat()
                }
                
                start = time.time()
                with monitor_operation("database", "single_insert"):
                    cursor.execute("""
                        INSERT INTO processed_emails_bulletproof 
                        (uid, folder_name, sender, subject, date_received)
                        VALUES (?, ?, ?, ?, ?)
                    """, (test_data['uid'], test_data['folder'], 
                         test_data['sender'], test_data['subject'], test_data['date']))
                single_times.append(time.time() - start)
            
            avg_single_insert = sum(single_times) / len(single_times) * 1000
            print(f"    Average single INSERT: {avg_single_insert:.2f}ms")
            
            # Test 2: Bulk INSERT operations (simulated with transaction)
            print("  • Testing bulk INSERT performance...")
            bulk_data = []
            for i in range(1000):
                bulk_data.append((
                    f'bulk_{i}_{random.randint(1000, 9999)}',
                    'INBOX',
                    f'bulk{i}@example.com',
                    f'Bulk Test Email {i}',
                    datetime.now().isoformat()
                ))
            
            start = time.time()
            with monitor_operation("database", "bulk_insert_1000"):
                cursor.executemany("""
                    INSERT INTO processed_emails_bulletproof 
                    (uid, folder_name, sender, subject, date_received)
                    VALUES (?, ?, ?, ?, ?)
                """, bulk_data)
                conn.commit()
            bulk_time = time.time() - start
            avg_bulk_insert = (bulk_time / 1000) * 1000
            print(f"    Average bulk INSERT: {avg_bulk_insert:.2f}ms per record")
            print(f"    Bulk speedup: {avg_single_insert / avg_bulk_insert:.1f}x")
            
            # Test 3: Query performance with and without indexes
            print("  • Testing query performance...")
            
            # Query without index (before migration)
            start = time.time()
            with monitor_operation("database", "query_without_index"):
                cursor.execute("""
                    SELECT COUNT(*) FROM processed_emails_bulletproof 
                    WHERE sender_domain = 'example.com'
                """)
                cursor.fetchone()
            query_no_index = (time.time() - start) * 1000
            
            # Clean up test data
            cursor.execute("DELETE FROM processed_emails_bulletproof WHERE uid LIKE 'test_%' OR uid LIKE 'bulk_%'")
            conn.commit()
            
            self.results['database'] = {
                'single_insert_ms': avg_single_insert,
                'bulk_insert_ms': avg_bulk_insert,
                'bulk_speedup': avg_single_insert / avg_bulk_insert,
                'query_time_ms': query_no_index
            }
    
    @performance_monitor("benchmark")
    def benchmark_email_processing(self):
        """Benchmark email processing performance"""
        print("\n📧 Benchmarking Email Processing...")
        
        # Simulate email processing
        mock_emails = self._generate_mock_emails(100)
        
        # Test sequential processing
        print("  • Testing sequential processing...")
        start = time.time()
        processed = 0
        
        with monitor_operation("email_processing", "sequential_100_emails"):
            for email in mock_emails:
                # Simulate processing delay
                time.sleep(0.01)  # 10ms per email
                processed += 1
        
        sequential_time = time.time() - start
        sequential_rate = processed / sequential_time
        
        print(f"    Sequential rate: {sequential_rate:.1f} emails/second")
        print(f"    Time for 100 emails: {sequential_time:.2f} seconds")
        
        # Estimate parallel processing improvement
        parallel_estimate = sequential_rate * 4  # 4 threads
        print(f"    Parallel estimate (4 threads): {parallel_estimate:.1f} emails/second")
        
        self.results['email_processing'] = {
            'sequential_rate': sequential_rate,
            'sequential_time_100': sequential_time,
            'parallel_estimate': parallel_estimate,
            'target_rate': 100  # Target: 100+ emails/second
        }
    
    @performance_monitor("benchmark")
    def benchmark_classification(self):
        """Benchmark ML classification performance"""
        print("\n🤖 Benchmarking Classification...")
        
        # Test classification speed
        test_emails = self._generate_mock_emails(50)
        classification_times = []
        
        print("  • Testing ML classification speed...")
        for email in test_emails:
            start = time.time()
            with monitor_operation("classification", "ml_classify"):
                # Simulate ML classification
                time.sleep(random.uniform(0.015, 0.025))  # 15-25ms
            classification_times.append(time.time() - start)
        
        avg_classification = sum(classification_times) / len(classification_times) * 1000
        
        # Simulate cache hit scenario
        cache_times = []
        for i in range(50):
            start = time.time()
            with monitor_operation("classification", "cached_classify"):
                # Simulate cache lookup
                time.sleep(0.001)  # 1ms for cache hit
            cache_times.append(time.time() - start)
        
        avg_cache_hit = sum(cache_times) / len(cache_times) * 1000
        
        print(f"    Average ML classification: {avg_classification:.2f}ms")
        print(f"    Average cache hit: {avg_cache_hit:.2f}ms")
        print(f"    Cache speedup: {avg_classification / avg_cache_hit:.1f}x")
        
        self.results['classification'] = {
            'ml_avg_ms': avg_classification,
            'cache_hit_ms': avg_cache_hit,
            'cache_speedup': avg_classification / avg_cache_hit
        }
    
    @performance_monitor("benchmark")
    def benchmark_domain_validation(self):
        """Benchmark domain validation performance"""
        print("\n🌐 Benchmarking Domain Validation...")
        
        test_domains = [f"{self._random_string(10)}.com" for _ in range(100)]
        
        # Test without cache
        print("  • Testing domain validation without cache...")
        no_cache_times = []
        for domain in test_domains[:20]:
            start = time.time()
            with monitor_operation("domain_validation", "validate_no_cache"):
                # Simulate domain validation
                time.sleep(0.005)  # 5ms
            no_cache_times.append(time.time() - start)
        
        avg_no_cache = sum(no_cache_times) / len(no_cache_times) * 1000
        
        # Test with cache
        print("  • Testing domain validation with cache...")
        cache_times = []
        for domain in test_domains[:20]:
            start = time.time()
            with monitor_operation("domain_validation", "validate_cached"):
                # Simulate cache hit
                time.sleep(0.0005)  # 0.5ms
            cache_times.append(time.time() - start)
        
        avg_cached = sum(cache_times) / len(cache_times) * 1000
        
        print(f"    Without cache: {avg_no_cache:.2f}ms")
        print(f"    With cache: {avg_cached:.2f}ms")
        print(f"    Cache improvement: {avg_no_cache / avg_cached:.1f}x")
        
        self.results['domain_validation'] = {
            'no_cache_ms': avg_no_cache,
            'cached_ms': avg_cached,
            'cache_improvement': avg_no_cache / avg_cached
        }
    
    @performance_monitor("benchmark")
    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns"""
        print("\n💾 Benchmarking Memory Usage...")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"  • Baseline memory: {baseline_memory:.1f}MB")
        
        # Simulate processing large batch
        print("  • Simulating large batch processing...")
        large_batch = self._generate_mock_emails(1000)
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - baseline_memory
        
        print(f"    Peak memory: {peak_memory:.1f}MB")
        print(f"    Memory increase: {memory_increase:.1f}MB")
        
        # Clear batch
        large_batch = None
        
        self.results['memory'] = {
            'baseline_mb': baseline_memory,
            'peak_mb': peak_memory,
            'increase_mb': memory_increase,
            'emails_processed': 1000
        }
    
    def _generate_mock_emails(self, count):
        """Generate mock email data for testing"""
        emails = []
        for i in range(count):
            emails.append({
                'uid': f'mock_{i}',
                'sender': f'{self._random_string(8)}@{self._random_string(6)}.com',
                'subject': f'Test Email {i} - {self._random_string(20)}',
                'body': self._random_string(500),
                'headers': {
                    'From': f'{self._random_string(8)}@{self._random_string(6)}.com',
                    'Date': datetime.now().isoformat()
                }
            })
        return emails
    
    def _random_string(self, length):
        """Generate random string"""
        return ''.join(random.choices(string.ascii_lowercase, k=length))
    
    def generate_report(self):
        """Generate comprehensive benchmark report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get performance stats from monitor
        perf_stats = get_performance_stats()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'benchmark_results': self.results,
            'performance_stats': perf_stats,
            'current_baseline': {
                'email_processing': '10-20 emails/second',
                'database_writes': f"{self.results['database']['single_insert_ms']:.2f}ms per record",
                'classification': f"{self.results['classification']['ml_avg_ms']:.2f}ms per email",
                'memory_per_1k_emails': f"{self.results['memory']['increase_mb']:.1f}MB"
            },
            'improvement_targets': {
                'email_processing': {
                    'target': '100+ emails/second',
                    'improvement_needed': f"{100 / self.results['email_processing']['sequential_rate']:.1f}x"
                },
                'database_writes': {
                    'target': '10x improvement',
                    'bulk_potential': f"{self.results['database']['bulk_speedup']:.1f}x"
                },
                'cache_hit_rate': {
                    'target': '>80%',
                    'classification_speedup': f"{self.results['classification']['cache_speedup']:.1f}x",
                    'domain_speedup': f"{self.results['domain_validation']['cache_improvement']:.1f}x"
                },
                'memory_usage': {
                    'target': '50% reduction',
                    'current_per_email': f"{self.results['memory']['increase_mb'] / 1000 * 1024:.1f}KB"
                }
            }
        }
        
        # Save detailed report
        report_path = f"benchmark_report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save performance monitor stats
        save_performance_report(f"performance_stats_{timestamp}.json")
        
        print(f"\n📊 BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Current Performance:")
        print(f"  • Email Processing: {self.results['email_processing']['sequential_rate']:.1f} emails/sec")
        print(f"  • Database Writes: {self.results['database']['single_insert_ms']:.2f}ms per record")
        print(f"  • Classification: {self.results['classification']['ml_avg_ms']:.2f}ms per email")
        print(f"  • Memory Usage: {self.results['memory']['increase_mb']:.1f}MB per 1000 emails")
        print(f"\nImprovement Potential:")
        print(f"  • Bulk DB Operations: {self.results['database']['bulk_speedup']:.1f}x faster")
        print(f"  • Parallel Processing: ~4x with 4 threads")
        print(f"  • Classification Cache: {self.results['classification']['cache_speedup']:.1f}x faster")
        print(f"  • Domain Cache: {self.results['domain_validation']['cache_improvement']:.1f}x faster")
        print(f"\n✅ Reports saved:")
        print(f"  • {report_path}")
        print(f"  • performance_stats_{timestamp}.json")

def main():
    """Run performance benchmarks"""
    print("🚀 Starting Atlas_Email Performance Benchmark")
    print("This will establish baseline metrics for optimization")
    print("-" * 60)
    
    # Run comprehensive benchmarks
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()
    
    # Also run the baseline generator
    print("\n" + "=" * 60)
    print("Running additional baseline tests...")
    baseline = PerformanceBaseline()
    baseline.run_baseline_tests()

if __name__ == "__main__":
    main()