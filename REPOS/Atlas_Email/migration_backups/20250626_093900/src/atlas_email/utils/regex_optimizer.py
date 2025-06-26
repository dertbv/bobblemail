#!/usr/bin/env python3
"""
Regex Optimizer - Pre-compiled regex patterns for email filtering system
Provides optimized, cached regex patterns for better performance
"""

import re
from typing import Dict, Pattern, List, Optional
from atlas_email.models.database import db

class RegexOptimizer:
    """Centralized regex pattern management with pre-compilation and caching"""
    
    def __init__(self):
        # Pre-compiled domain validation patterns
        self.domain_patterns = self._compile_domain_patterns()
        
        # Pre-compiled spam detection patterns  
        self.spam_patterns = self._compile_spam_patterns()
        
        # Pre-compiled gibberish detection patterns
        self.gibberish_patterns = self._compile_gibberish_patterns()
        
        # Dynamic keyword patterns cache
        self._keyword_pattern_cache: Dict[str, Pattern] = {}
        
        # Email address patterns
        self.email_patterns = self._compile_email_patterns()
        
        print("🚀 RegexOptimizer initialized with pre-compiled patterns")
    
    def _compile_domain_patterns(self) -> Dict[str, Pattern]:
        """Pre-compile domain validation regex patterns"""
        return {
            'vowel_pattern': re.compile(r'[aeiouAEIOU]'),
            'long_random': re.compile(r'^[a-z0-9]{12,}$'),
            'mixed_case': re.compile(r'[A-Z]{2,}[a-z]{2,}[A-Z]{2,}|[a-z]{2,}[A-Z]{2,}[a-z]{2,}'),
            'alphanumeric': re.compile(r'^[a-z0-9]{8,}$'),
            'number_letter_mix': re.compile(r'[0-9]{2,}[a-z]{2,}[0-9]{2,}|[a-z]{2,}[0-9]{2,}[a-z]{2,}'),
            'very_long': re.compile(r'^[a-z]{15,}$'),
            'many_numbers': re.compile(r'[0-9]{4,}'),
            'domain_cleanup': re.compile(r'[<>\s]'),
            'gibberish_consonants': re.compile(r'\b[^aeiouAEIOU\s\d\W]{7,}\b'),
            'word_split': re.compile(r'[.\-_]'),
            'digit_removal': re.compile(r'[0-9]')
        }
    
    def _compile_spam_patterns(self) -> Dict[str, Pattern]:
        """Pre-compile spam detection regex patterns"""
        return {
            # Email header patterns
            'suspicious_sender': re.compile(r'(noreply|no-reply|donotreply|auto|system|info)@', re.IGNORECASE),
            'suspicious_subject': re.compile(r'(urgent|act now|limited time|free|winner|congratulations)', re.IGNORECASE),
            
            # Content patterns
            'phone_numbers': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'urls': re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            
            # Scam indicators
            'money_amounts': re.compile(r'\$[\d,]+|\b\d+\s*dollars?\b', re.IGNORECASE),
            'urgent_action': re.compile(r'\b(urgent|emergency|immediate|asap|deadline)\b', re.IGNORECASE),
            'clickbait': re.compile(r'\b(click here|click now|tap here|download now)\b', re.IGNORECASE),
            
            # Emoji patterns
            'money_emojis': re.compile(r'[💰💎💸💵💴💶💷🤑]'),
            'warning_emojis': re.compile(r'[⚠️🚨⛔❗❌]'),
            'celebration_emojis': re.compile(r'[🎉🎊🥳🎁🏆]')
        }
    
    def _compile_gibberish_patterns(self) -> Dict[str, Pattern]:
        """Pre-compile gibberish detection patterns"""
        return {
            'consonant_sequence': re.compile(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{4,}'),
            'vowel_sequence': re.compile(r'[aeiouAEIOU]{3,}'),
            'repeating_chars': re.compile(r'(.)\1{3,}'),  # 4+ repeated characters
            'keyboard_walk': re.compile(r'(qwert|asdf|zxcv|1234|abcd)', re.IGNORECASE),
            'random_mix': re.compile(r'^[a-z0-9]{8,}$', re.IGNORECASE),
            'no_vowels_long': re.compile(r'^[^aeiouAEIOU\s\d]{6,}$', re.IGNORECASE)
        }
    
    def _compile_email_patterns(self) -> Dict[str, Pattern]:
        """Pre-compile email validation patterns"""
        return {
            'valid_email': re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
            'suspicious_tld': re.compile(r'\.(tk|ml|ga|cf|pw|top|click|download)$', re.IGNORECASE),
            'subdomain_count': re.compile(r'\.'),
            'local_part': re.compile(r'^([^@]+)@'),
            'domain_part': re.compile(r'@(.+)$')
        }
    
    def get_compiled_pattern(self, category: str, pattern_name: str) -> Optional[Pattern]:
        """Get a pre-compiled regex pattern"""
        pattern_dict = {
            'domain': self.domain_patterns,
            'spam': self.spam_patterns, 
            'gibberish': self.gibberish_patterns,
            'email': self.email_patterns
        }.get(category)
        
        return pattern_dict.get(pattern_name) if pattern_dict else None
    
    def create_keyword_pattern(self, keywords: List[str], word_boundaries: bool = True) -> Pattern:
        """Create optimized regex pattern from keyword list with caching"""
        # Create cache key
        cache_key = f"{'wb_' if word_boundaries else ''}{hash(tuple(sorted(keywords)))}"
        
        if cache_key in self._keyword_pattern_cache:
            return self._keyword_pattern_cache[cache_key]
        
        # Escape special regex characters in keywords
        escaped_keywords = [re.escape(keyword) for keyword in keywords]
        
        # Create optimized alternation pattern
        if word_boundaries:
            pattern_str = r'\b(?:' + '|'.join(escaped_keywords) + r')\b'
        else:
            pattern_str = '(?:' + '|'.join(escaped_keywords) + ')'
        
        # Compile with case-insensitive flag
        compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
        
        # Cache the pattern
        self._keyword_pattern_cache[cache_key] = compiled_pattern
        
        return compiled_pattern
    
    def create_category_pattern(self, category: str) -> Optional[Pattern]:
        """Create regex pattern for all keywords in a spam category"""
        try:
            keywords = db.execute_query("""
                SELECT term FROM filter_terms 
                WHERE category = ? AND is_active = 1
            """, (category,))
            
            keyword_list = [kw['term'] for kw in keywords]
            
            if not keyword_list:
                return None
                
            return self.create_keyword_pattern(keyword_list, word_boundaries=False)
            
        except Exception as e:
            print(f"Error creating pattern for category {category}: {e}")
            return None
    
    def check_domain_suspicious(self, domain: str) -> Dict[str, bool]:
        """Fast domain suspicion check using pre-compiled patterns"""
        if not domain:
            return {}
        
        domain_clean = domain.lower().strip()
        results = {}
        
        # Use pre-compiled patterns for fast checking
        results['has_vowels'] = bool(self.domain_patterns['vowel_pattern'].search(domain_clean))
        results['long_random'] = bool(self.domain_patterns['long_random'].match(domain_clean))
        results['mixed_case'] = bool(self.domain_patterns['mixed_case'].search(domain))
        results['many_numbers'] = bool(self.domain_patterns['many_numbers'].search(domain_clean))
        
        return results
    
    def extract_spam_indicators(self, text: str) -> Dict[str, List[str]]:
        """Extract spam indicators using pre-compiled patterns"""
        indicators = {}
        
        # Find phone numbers
        phones = self.spam_patterns['phone_numbers'].findall(text)
        if phones:
            indicators['phone_numbers'] = phones
        
        # Find URLs
        urls = self.spam_patterns['urls'].findall(text)
        if urls:
            indicators['urls'] = urls
        
        # Find money amounts
        money = self.spam_patterns['money_amounts'].findall(text)
        if money:
            indicators['money_amounts'] = money
        
        # Check for urgent action words
        urgent = self.spam_patterns['urgent_action'].findall(text)
        if urgent:
            indicators['urgent_actions'] = urgent
            
        return indicators
    
    def analyze_gibberish_fast(self, text: str) -> Dict[str, int]:
        """Fast gibberish analysis using pre-compiled patterns"""
        scores = {}
        
        scores['consonant_sequences'] = len(self.gibberish_patterns['consonant_sequence'].findall(text))
        scores['vowel_sequences'] = len(self.gibberish_patterns['vowel_sequence'].findall(text))  
        scores['repeating_chars'] = len(self.gibberish_patterns['repeating_chars'].findall(text))
        scores['keyboard_walks'] = len(self.gibberish_patterns['keyboard_walk'].findall(text))
        
        return scores
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get regex cache statistics"""
        return {
            'domain_patterns': len(self.domain_patterns),
            'spam_patterns': len(self.spam_patterns),
            'gibberish_patterns': len(self.gibberish_patterns),
            'email_patterns': len(self.email_patterns),
            'cached_keyword_patterns': len(self._keyword_pattern_cache)
        }
    
    def clear_keyword_cache(self):
        """Clear the keyword pattern cache"""
        self._keyword_pattern_cache.clear()
        print("🧹 Keyword pattern cache cleared")

# Global instance for reuse across the application
regex_optimizer = RegexOptimizer()

# Convenience functions for easy access
def get_pattern(category: str, name: str) -> Optional[Pattern]:
    """Get a pre-compiled regex pattern"""
    return regex_optimizer.get_compiled_pattern(category, name)

def create_keyword_regex(keywords: List[str]) -> Pattern:
    """Create optimized keyword regex pattern"""
    return regex_optimizer.create_keyword_pattern(keywords)

def check_domain_fast(domain: str) -> Dict[str, bool]:
    """Fast domain checking with pre-compiled patterns"""
    return regex_optimizer.check_domain_suspicious(domain)

def analyze_spam_indicators(text: str) -> Dict[str, List[str]]:
    """Extract spam indicators with pre-compiled patterns"""
    return regex_optimizer.extract_spam_indicators(text)