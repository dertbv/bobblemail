#!/usr/bin/env python3
"""
Smart Regex Selector - Intelligent selection between regex and keyword matching
Chooses optimal approach based on keyword count, text length, and pattern complexity
"""

import re
import time
from typing import List, Union, Pattern, Tuple
from ..models.database import db

class SmartRegexSelector:
    """Intelligently selects between regex and keyword matching for optimal performance"""
    
    def __init__(self):
        # Performance thresholds for different approaches
        self.REGEX_THRESHOLD_KEYWORDS = 10  # Use regex if more than 10 keywords
        self.REGEX_THRESHOLD_TEXT_LENGTH = 1000  # Use regex if text > 1000 chars
        self.COMPLEX_PATTERN_THRESHOLD = 5  # Use regex if 5+ special pattern keywords
        
        # Pattern cache for compiled regex
        self._pattern_cache = {}
        
        # Performance statistics
        self.stats = {
            'regex_used': 0,
            'keyword_used': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        print("🧠 Smart Regex Selector initialized")
    
    def should_use_regex(self, keywords: List[str], text_length: int) -> bool:
        """Decide whether to use regex or standard keyword matching"""
        
        # Factor 1: Number of keywords
        if len(keywords) >= self.REGEX_THRESHOLD_KEYWORDS:
            return True
            
        # Factor 2: Text length (regex better for longer texts)
        if text_length >= self.REGEX_THRESHOLD_TEXT_LENGTH:
            return True
            
        # Factor 3: Complex patterns (keywords with special characters)
        complex_keywords = sum(1 for kw in keywords 
                             if any(char in kw for char in ['(', ')', '[', ']', '.', '*', '+', '?']))
        if complex_keywords >= self.COMPLEX_PATTERN_THRESHOLD:
            return True
            
        # Factor 4: Keywords that benefit from word boundaries
        word_boundary_keywords = sum(1 for kw in keywords 
                                   if ' ' not in kw and len(kw) >= 4)
        if word_boundary_keywords >= len(keywords) * 0.7:  # 70% of keywords
            return True
            
        return False
    
    def get_optimized_pattern(self, keywords: List[str], use_word_boundaries: bool = True) -> Pattern:
        """Get optimized regex pattern with caching"""
        
        # Create cache key
        cache_key = f"{'wb_' if use_word_boundaries else ''}{hash(tuple(sorted(keywords)))}"
        
        if cache_key in self._pattern_cache:
            self.stats['cache_hits'] += 1
            return self._pattern_cache[cache_key]
        
        self.stats['cache_misses'] += 1
        
        # Escape keywords and create optimized pattern
        escaped_keywords = [re.escape(keyword) for keyword in keywords]
        
        # Group similar keywords for optimization
        short_keywords = [kw for kw in escaped_keywords if len(kw) <= 5]
        long_keywords = [kw for kw in escaped_keywords if len(kw) > 5]
        
        # Create optimized alternation
        if use_word_boundaries and any(' ' not in kw for kw in keywords):
            if short_keywords and long_keywords:
                # Optimize by putting longer keywords first (better for regex engine)
                pattern_str = r'\b(?:' + '|'.join(sorted(long_keywords + short_keywords, key=len, reverse=True)) + r')\b'
            else:
                pattern_str = r'\b(?:' + '|'.join(sorted(escaped_keywords, key=len, reverse=True)) + r')\b'
        else:
            pattern_str = '(?:' + '|'.join(sorted(escaped_keywords, key=len, reverse=True)) + ')'
        
        # Compile with optimizations
        compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
        
        # Cache the pattern
        self._pattern_cache[cache_key] = compiled_pattern
        
        return compiled_pattern
    
    def smart_keyword_match(self, text: str, keywords: List[str]) -> bool:
        """Smart keyword matching using optimal approach"""
        if not text or not keywords:
            return False
        
        text_length = len(text)
        use_regex = self.should_use_regex(keywords, text_length)
        
        if use_regex:
            self.stats['regex_used'] += 1
            pattern = self.get_optimized_pattern(keywords)
            return bool(pattern.search(text))
        else:
            self.stats['keyword_used'] += 1
            text_lower = text.lower()
            return any(keyword.lower() in text_lower for keyword in keywords)
    
    def smart_keyword_count(self, text: str, keywords: List[str]) -> int:
        """Smart keyword counting using optimal approach"""
        if not text or not keywords:
            return 0
        
        text_length = len(text)
        use_regex = self.should_use_regex(keywords, text_length)
        
        if use_regex:
            self.stats['regex_used'] += 1
            pattern = self.get_optimized_pattern(keywords, use_word_boundaries=False)
            return len(pattern.findall(text))
        else:
            self.stats['keyword_used'] += 1
            text_lower = text.lower()
            return sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    def smart_category_match(self, text: str, category: str) -> bool:
        """Smart category matching using database keywords"""
        try:
            keywords = db.execute_query("""
                SELECT term FROM filter_terms 
                WHERE category = ? AND is_active = 1
            """, (category,))
            keyword_list = [kw['term'] for kw in keywords]
            
            return self.smart_keyword_match(text, keyword_list)
            
        except Exception as e:
            print(f"Error in smart category match for {category}: {e}")
            return False
    
    def smart_category_count(self, text: str, category: str) -> int:
        """Smart category counting using database keywords"""
        try:
            keywords = db.execute_query("""
                SELECT term FROM filter_terms 
                WHERE category = ? AND is_active = 1
            """, (category,))
            keyword_list = [kw['term'] for kw in keywords]
            
            return self.smart_keyword_count(text, keyword_list)
            
        except Exception as e:
            print(f"Error in smart category count for {category}: {e}")
            return 0
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        total_operations = self.stats['regex_used'] + self.stats['keyword_used']
        total_cache_ops = self.stats['cache_hits'] + self.stats['cache_misses']
        
        return {
            'total_operations': total_operations,
            'regex_percentage': (self.stats['regex_used'] / total_operations * 100) if total_operations > 0 else 0,
            'keyword_percentage': (self.stats['keyword_used'] / total_operations * 100) if total_operations > 0 else 0,
            'cache_hit_rate': (self.stats['cache_hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0,
            'cached_patterns': len(self._pattern_cache),
            **self.stats
        }
    
    def optimize_thresholds(self, test_cases: List[Tuple[str, List[str]]]) -> dict:
        """Optimize performance thresholds based on test cases"""
        print("🔬 Optimizing performance thresholds...")
        
        results = {}
        thresholds_to_test = [5, 10, 15, 20, 25]
        
        for threshold in thresholds_to_test:
            old_threshold = self.REGEX_THRESHOLD_KEYWORDS
            self.REGEX_THRESHOLD_KEYWORDS = threshold
            
            # Test performance
            start_time = time.time()
            for text, keywords in test_cases:
                self.smart_keyword_match(text, keywords)
            elapsed = time.time() - start_time
            
            results[threshold] = elapsed
            self.REGEX_THRESHOLD_KEYWORDS = old_threshold
        
        # Find optimal threshold
        optimal_threshold = min(results, key=results.get)
        print(f"📊 Optimal keyword threshold: {optimal_threshold} (time: {results[optimal_threshold]:.4f}s)")
        
        return results
    
    def clear_cache(self):
        """Clear pattern cache"""
        self._pattern_cache.clear()
        self.stats['cache_hits'] = 0
        self.stats['cache_misses'] = 0
        print("🧹 Pattern cache cleared")

# Global instance
smart_selector = SmartRegexSelector()

# Convenience functions
def smart_match(text: str, keywords: List[str]) -> bool:
    """Smart keyword matching using optimal approach"""
    return smart_selector.smart_keyword_match(text, keywords)

def smart_count(text: str, keywords: List[str]) -> int:
    """Smart keyword counting using optimal approach"""
    return smart_selector.smart_keyword_count(text, keywords)

def smart_category_check(text: str, category: str) -> bool:
    """Smart category checking using database keywords"""
    return smart_selector.smart_category_match(text, category)

def smart_category_count(text: str, category: str) -> int:
    """Smart category counting using database keywords"""
    return smart_selector.smart_category_count(text, category)