#!/usr/bin/env python3
"""
Regex Performance Test - Compare standard vs optimized regex performance
Measures performance improvement from pre-compiled patterns and caching
"""

import time
import re
from typing import List, Dict, Callable
from database import db

def test_keyword_matching_performance():
    """Compare standard keyword matching vs regex pattern matching"""
    
    # Get test keywords from database
    keywords = db.execute_query("""
        SELECT term FROM filter_terms 
        WHERE category = 'Investment Spam' AND is_active = 1
        LIMIT 50
    """)
    keyword_list = [kw['term'] for kw in keywords]
    
    # Create test text with some keywords
    test_text = """
    Looking for cryptocurrency investment opportunities? Our bitcoin trading platform 
    offers high returns and guaranteed profits. Join our forex trading community today!
    Get rich quick with our investment fund and portfolio management services.
    """
    
    print(f"🧪 Testing with {len(keyword_list)} keywords")
    print(f"📝 Test text length: {len(test_text)} characters")
    
    # Test 1: Standard keyword matching
    def standard_keyword_match(text: str, keywords: List[str]) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    # Test 2: Regex pattern matching
    escaped_keywords = [re.escape(keyword) for keyword in keyword_list]
    pattern_str = '(?:' + '|'.join(escaped_keywords) + ')'
    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
    
    def regex_pattern_match(text: str, pattern: re.Pattern) -> bool:
        return bool(pattern.search(text))
    
    # Test 3: Optimized regex with word boundaries
    wb_pattern_str = r'\b(?:' + '|'.join(escaped_keywords) + r')\b'
    wb_compiled_pattern = re.compile(wb_pattern_str, re.IGNORECASE)
    
    def regex_wb_match(text: str, pattern: re.Pattern) -> bool:
        return bool(pattern.search(text))
    
    # Performance testing
    iterations = 1000
    
    # Time standard approach
    start_time = time.time()
    for _ in range(iterations):
        result1 = standard_keyword_match(test_text, keyword_list)
    standard_time = time.time() - start_time
    
    # Time regex approach  
    start_time = time.time()
    for _ in range(iterations):
        result2 = regex_pattern_match(test_text, compiled_pattern)
    regex_time = time.time() - start_time
    
    # Time optimized regex with word boundaries
    start_time = time.time()
    for _ in range(iterations):
        result3 = regex_wb_match(test_text, wb_compiled_pattern)
    regex_wb_time = time.time() - start_time
    
    print(f"\n⏱️  Performance Results ({iterations} iterations):")
    print(f"   Standard keyword matching: {standard_time:.4f}s (result: {result1})")
    print(f"   Regex pattern matching:    {regex_time:.4f}s (result: {result2})")
    print(f"   Regex w/ word boundaries:  {regex_wb_time:.4f}s (result: {result3})")
    
    # Calculate improvements
    if standard_time > 0:
        regex_improvement = ((standard_time - regex_time) / standard_time) * 100
        regex_wb_improvement = ((standard_time - regex_wb_time) / standard_time) * 100
        
        print(f"\n📈 Performance Improvements:")
        print(f"   Regex pattern:     {regex_improvement:+.1f}% vs standard")
        print(f"   Regex w/ bounds:   {regex_wb_improvement:+.1f}% vs standard")
        
        if regex_time > 0:
            wb_vs_regex = ((regex_time - regex_wb_time) / regex_time) * 100
            print(f"   Word boundaries:   {wb_vs_regex:+.1f}% vs basic regex")

def test_domain_pattern_performance():
    """Test domain validation pattern performance"""
    
    test_domains = [
        "suspicious-domain123.com",
        "randomtext456789.net", 
        "mixedCASEDomain.org",
        "numbers123456789.info",
        "legitimate-company.com",
        "abcdefghijklmnop.tk",
        "short.co",
        "very-long-domain-name-here.click"
    ]
    
    # Standard regex patterns
    long_random_pattern = re.compile(r'^[a-z0-9]{12,}$')
    mixed_case_pattern = re.compile(r'[A-Z]{2,}[a-z]{2,}[A-Z]{2,}|[a-z]{2,}[A-Z]{2,}[a-z]{2,}')
    many_numbers_pattern = re.compile(r'[0-9]{4,}')
    
    # Test standard approach
    def standard_domain_check(domain: str) -> Dict[str, bool]:
        domain_clean = domain.lower().strip()
        return {
            'long_random': bool(long_random_pattern.match(domain_clean)),
            'mixed_case': bool(mixed_case_pattern.search(domain)),
            'many_numbers': bool(many_numbers_pattern.search(domain_clean))
        }
    
    # Test optimized approach
    try:
        from regex_optimizer import check_domain_fast
        def optimized_domain_check(domain: str) -> Dict[str, bool]:
            return check_domain_fast(domain)
        optimized_available = True
    except ImportError:
        optimized_available = False
    
    iterations = 1000
    
    # Time standard approach
    start_time = time.time()
    for _ in range(iterations):
        for domain in test_domains:
            result1 = standard_domain_check(domain)
    standard_time = time.time() - start_time
    
    if optimized_available:
        # Time optimized approach
        start_time = time.time()
        for _ in range(iterations):
            for domain in test_domains:
                result2 = optimized_domain_check(domain)
        optimized_time = time.time() - start_time
        
        print(f"\n🌐 Domain Pattern Performance ({iterations} iterations, {len(test_domains)} domains):")
        print(f"   Standard patterns:  {standard_time:.4f}s")
        print(f"   Optimized patterns: {optimized_time:.4f}s")
        
        if standard_time > 0:
            improvement = ((standard_time - optimized_time) / standard_time) * 100
            print(f"   Performance gain:   {improvement:+.1f}%")
    else:
        print(f"\n🌐 Domain Pattern Performance (optimized not available):")
        print(f"   Standard patterns:  {standard_time:.4f}s")

def test_pattern_compilation_overhead():
    """Test the overhead of pattern compilation vs pre-compilation"""
    
    keywords = ["investment", "cryptocurrency", "trading", "profit", "bitcoin"]
    test_text = "Looking for cryptocurrency investment opportunities with high profits"
    iterations = 100
    
    # Test 1: Compile pattern each time
    start_time = time.time()
    for _ in range(iterations):
        pattern_str = '(?:' + '|'.join(re.escape(k) for k in keywords) + ')'
        pattern = re.compile(pattern_str, re.IGNORECASE)
        result = bool(pattern.search(test_text))
    compile_each_time = time.time() - start_time
    
    # Test 2: Pre-compile pattern
    pattern_str = '(?:' + '|'.join(re.escape(k) for k in keywords) + ')'
    pre_compiled = re.compile(pattern_str, re.IGNORECASE)
    
    start_time = time.time()
    for _ in range(iterations):
        result = bool(pre_compiled.search(test_text))
    pre_compiled_time = time.time() - start_time
    
    print(f"\n⚡ Pattern Compilation Overhead ({iterations} iterations):")
    print(f"   Compile each time:  {compile_each_time:.4f}s")
    print(f"   Pre-compiled:       {pre_compiled_time:.4f}s")
    
    if compile_each_time > 0:
        improvement = ((compile_each_time - pre_compiled_time) / compile_each_time) * 100
        print(f"   Pre-compilation saves: {improvement:.1f}%")

def main():
    """Run all performance tests"""
    print("🚀 REGEX PERFORMANCE TESTING")
    print("=" * 50)
    
    try:
        test_keyword_matching_performance()
        test_domain_pattern_performance()
        test_pattern_compilation_overhead()
        
        print(f"\n✅ All performance tests completed!")
        print(f"\n💡 Key Insights:")
        print(f"   • Pre-compiled regex patterns provide significant performance gains")
        print(f"   • Word boundary patterns can improve accuracy without major performance cost")
        print(f"   • Pattern caching eliminates compilation overhead")
        print(f"   • Optimized patterns especially beneficial for high-frequency operations")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()