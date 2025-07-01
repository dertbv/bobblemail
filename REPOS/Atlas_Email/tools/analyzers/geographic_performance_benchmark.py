#!/usr/bin/env python3
"""
Geographic Performance Analysis Benchmark
Performance testing for different geographic intelligence approaches
"""

import time
import random
import string
from typing import List, Dict, Tuple

# Simulate different geographic approaches
class GeographicIntelligenceComparison:
    """Benchmark different geographic spam detection approaches"""
    
    def __init__(self):
        # Suspicious domain suffixes (instant lookup)
        self.suspicious_tlds = {
            '.tk', '.ml', '.ga', '.cf', '.us', '.info', '.biz',
            '.cn', '.ru', '.ua', '.by', '.kz', '.kg', '.uz'
        }
        
        # Country-based patterns (instant lookup)
        self.high_risk_country_codes = {
            'cn', 'ru', 'ua', 'by', 'kz', 'kg', 'uz', 'bd', 'pk', 'in'
        }
        
        # Pre-built suspicious IP ranges (instant lookup)
        self.suspicious_ip_ranges = [
            ('1.2.3.', '1.2.4.'),     # Simulated ranges
            ('45.67.', '45.68.'),
            ('103.45.', '103.46.'),
            ('185.220.', '185.221.'),
        ]

    def benchmark_instant_tld_detection(self, domains: List[str]) -> Tuple[float, int]:
        """Benchmark instant TLD-based geographic detection"""
        start_time = time.perf_counter()
        
        detections = 0
        for domain in domains:
            for tld in self.suspicious_tlds:
                if domain.endswith(tld):
                    detections += 1
                    break
        
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000, detections  # Return milliseconds

    def benchmark_simulated_geoip_fast(self, ips: List[str]) -> Tuple[float, int]:
        """Benchmark GeoIP2Fast alternative (0.03ms per lookup)"""
        start_time = time.perf_counter()
        
        detections = 0
        for ip in ips:
            # Simulate GeoIP2Fast lookup (0.03ms)
            time.sleep(0.00003)  # 0.03 milliseconds
            
            # Simulate country detection
            if any(ip.startswith(range_start) for range_start, _ in self.suspicious_ip_ranges):
                detections += 1
        
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000, detections

    def benchmark_simulated_geoip_standard(self, ips: List[str]) -> Tuple[float, int]:
        """Benchmark Standard GeoIP2 Python (0.25-0.5ms per lookup)"""
        start_time = time.perf_counter()
        
        detections = 0
        for ip in ips:
            # Simulate standard GeoIP2 lookup (0.375ms average)
            time.sleep(0.000375)  # 0.375 milliseconds
            
            # Simulate country detection
            if any(ip.startswith(range_start) for range_start, _ in self.suspicious_ip_ranges):
                detections += 1
        
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000, detections

    def benchmark_simulated_whois_lookup(self, domains: List[str]) -> Tuple[float, int]:
        """Benchmark expensive WHOIS lookups (current bottleneck)"""
        start_time = time.perf_counter()
        
        detections = 0
        for domain in domains:
            # Simulate WHOIS lookup (1000-3000ms)
            time.sleep(random.uniform(1.0, 3.0))  # 1-3 seconds!
            
            # Simulate geographic detection from WHOIS
            if any(cc in domain for cc in ['cn', 'ru', 'ua']):
                detections += 1
        
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000, detections

    def benchmark_cached_whois(self, domains: List[str], cache_hit_rate: float = 0.7) -> Tuple[float, int]:
        """Benchmark cached WHOIS with smart refresh logic"""
        start_time = time.perf_counter()
        
        detections = 0
        for domain in domains:
            if random.random() < cache_hit_rate:
                # Cache hit - instant lookup
                time.sleep(0.0001)  # 0.1ms cache lookup
            else:
                # Cache miss - full WHOIS lookup
                time.sleep(random.uniform(1.0, 3.0))
            
            # Simulate geographic detection
            if any(cc in domain for cc in ['cn', 'ru', 'ua']):
                detections += 1
        
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000, detections

def generate_test_domains(count: int) -> List[str]:
    """Generate test domains with mix of suspicious and normal patterns"""
    domains = []
    
    # 30% suspicious TLD domains
    suspicious_count = int(count * 0.3)
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.cn', '.ru', '.ua']
    
    for _ in range(suspicious_count):
        random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        random_tld = random.choice(suspicious_tlds)
        domains.append(f"{random_name}{random_tld}")
    
    # 70% normal domains
    normal_count = count - suspicious_count
    normal_tlds = ['.com', '.org', '.net', '.edu', '.gov']
    
    for _ in range(normal_count):
        random_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        random_tld = random.choice(normal_tlds)
        domains.append(f"{random_name}{random_tld}")
    
    return domains

def generate_test_ips(count: int) -> List[str]:
    """Generate test IP addresses"""
    ips = []
    for _ in range(count):
        ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        ips.append(ip)
    return ips

def run_comprehensive_benchmark():
    """Run comprehensive geographic intelligence benchmark"""
    print("🌍 GEOGRAPHIC PERFORMANCE ANALYSIS BENCHMARK")
    print("=" * 60)
    
    benchmark = GeographicIntelligenceComparison()
    
    # Test datasets
    test_domains = generate_test_domains(100)  # 100 domains for reasonable test
    test_ips = generate_test_ips(100)         # 100 IPs for comparison
    
    print(f"Testing with {len(test_domains)} domains and {len(test_ips)} IP addresses")
    print()
    
    # Benchmark results
    results = {}
    
    print("🚀 TIER 1: INSTANT DETECTION (0-1ms per lookup)")
    print("-" * 50)
    
    # 1. Instant TLD Detection
    duration, detections = benchmark.benchmark_instant_tld_detection(test_domains)
    results['instant_tld'] = duration
    print(f"Instant TLD Detection: {duration:.2f}ms total, {duration/len(test_domains):.4f}ms per domain")
    print(f"  → Detected {detections} suspicious TLDs")
    print()
    
    print("⚡ TIER 2: FAST PATTERN MATCHING (0.01-1ms per lookup)")
    print("-" * 50)
    
    # 2. GeoIP2Fast Alternative
    duration, detections = benchmark.benchmark_simulated_geoip_fast(test_ips[:10])  # Smaller set for simulation
    results['geoip_fast'] = duration
    print(f"GeoIP2Fast Alternative: {duration:.2f}ms total, {duration/10:.4f}ms per IP")
    print(f"  → Detected {detections} suspicious IPs")
    print()
    
    # 3. Standard GeoIP2
    duration, detections = benchmark.benchmark_simulated_geoip_standard(test_ips[:10])
    results['geoip_standard'] = duration
    print(f"Standard GeoIP2 Python: {duration:.2f}ms total, {duration/10:.4f}ms per IP")
    print(f"  → Detected {detections} suspicious IPs")
    print()
    
    # 4. Cached WHOIS (70% hit rate)
    duration, detections = benchmark.benchmark_cached_whois(test_domains[:10], 0.7)
    results['cached_whois'] = duration
    print(f"Cached WHOIS (70% hit rate): {duration:.2f}ms total, {duration/10:.4f}ms per domain")
    print(f"  → Detected {detections} suspicious domains")
    print()
    
    print("🐌 TIER 3: EXPENSIVE ANALYSIS (1000-3000ms per lookup)")
    print("-" * 50)
    
    # 5. Full WHOIS Lookup (CURRENT BOTTLENECK)
    print("⚠️  Full WHOIS Lookup Test (WARNING: This will take 5-15 seconds)")
    duration, detections = benchmark.benchmark_simulated_whois_lookup(test_domains[:5])  # Only 5 for demo
    results['full_whois'] = duration
    print(f"Full WHOIS Lookup: {duration:.2f}ms total, {duration/5:.0f}ms per domain")
    print(f"  → Detected {detections} suspicious domains")
    print()
    
    # Performance Comparison
    print("📊 PERFORMANCE COMPARISON SUMMARY")
    print("=" * 60)
    
    per_item_times = {
        'Instant TLD Detection': results['instant_tld'] / len(test_domains),
        'GeoIP2Fast Alternative': results['geoip_fast'] / 10,
        'Standard GeoIP2': results['geoip_standard'] / 10,
        'Cached WHOIS (70% hit)': results['cached_whois'] / 10,
        'Full WHOIS Lookup': results['full_whois'] / 5
    }
    
    # Sort by performance (fastest first)
    sorted_methods = sorted(per_item_times.items(), key=lambda x: x[1])
    
    fastest_time = sorted_methods[0][1]
    
    for method, time_ms in sorted_methods:
        speed_improvement = (per_item_times['Full WHOIS Lookup'] / time_ms)
        print(f"{method:<25}: {time_ms:>8.4f}ms per lookup ({speed_improvement:>6.0f}x faster than WHOIS)")
    
    print()
    print("🎯 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)
    
    print("1. IMMEDIATE WINS:")
    print("   • Move TLD detection to BEFORE domain analysis")
    print("   • 99%+ emails can skip expensive WHOIS lookups")
    print("   • Instant detection vs 1-3 second delays")
    print()
    
    print("2. MEDIUM-TERM IMPROVEMENTS:")
    print("   • Implement GeoIP2Fast for IP-based geographic detection")
    print("   • Cache WHOIS results with smart refresh logic")
    print("   • Use geographic patterns for fast pre-filtering")
    print()
    
    print("3. ARCHITECTURE CHANGES:")
    print("   • Tier 1: Instant patterns (TLD, gibberish domains)")
    print("   • Tier 2: Fast geographic (GeoIP, cached WHOIS)")
    print("   • Tier 3: Deep analysis (fresh WHOIS) for uncertain cases only")
    print()

if __name__ == "__main__":
    run_comprehensive_benchmark()