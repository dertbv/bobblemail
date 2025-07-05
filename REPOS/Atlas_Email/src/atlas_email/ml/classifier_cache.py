#!/usr/bin/env python3
"""
Classifier Cache Module
Provides intelligent caching for ML classification results with early-exit patterns
"""

import hashlib
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from collections import defaultdict
import re

# Performance monitoring
try:
    from atlas_email.utils.performance_monitor import performance_monitor, monitor_operation
except ImportError:
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

# Import cache manager
try:
    from atlas_email.utils.cache_manager import (
        get_classification_cache, set_classification_cache,
        get_domain_cache, set_domain_cache
    )
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False


@dataclass
class EarlyExitPattern:
    """Pattern for early spam detection"""
    pattern: str
    category: str
    confidence: float
    description: str


class ClassifierOptimizer:
    """
    Optimizes classification through caching and early-exit patterns
    """
    
    # High-confidence spam patterns for early exit
    EARLY_EXIT_PATTERNS = [
        # Financial scams
        EarlyExitPattern(
            pattern=r'(?i)(nigerian?\s+prince|inheritance\s+fund|unclaimed\s+funds?|million\s+dollars?\s+transfer)',
            category='Financial Scam',
            confidence=0.95,
            description='Nigerian prince/inheritance scam'
        ),
        EarlyExitPattern(
            pattern=r'(?i)(crypto\s+investment|bitcoin\s+opportunity|guaranteed\s+returns?|forex\s+signals?)',
            category='Financial & Investment Spam',
            confidence=0.90,
            description='Cryptocurrency/investment scam'
        ),
        
        # Adult content
        EarlyExitPattern(
            pattern=r'(?i)(viagra|cialis|erectile\s+dysfunction|penis\s+enlarge|adult\s+dating|hot\s+singles?)',
            category='Adult & Dating Spam',
            confidence=0.95,
            description='Adult content/dating spam'
        ),
        
        # Health scams
        EarlyExitPattern(
            pattern=r'(?i)(weight\s+loss\s+pill|miracle\s+cure|cbd\s+oil|keto\s+diet|testosterone\s+boost)',
            category='Health & Medical Spam',
            confidence=0.90,
            description='Health/medical scam'
        ),
        
        # Obvious spam
        EarlyExitPattern(
            pattern=r'(?i)(congratulations?\s+you\s+won|claim\s+your\s+prize|limited\s+time\s+offer|act\s+now)',
            category='Prize/Lottery Scam',
            confidence=0.95,
            description='Prize/lottery scam'
        ),
        EarlyExitPattern(
            pattern=r'(?i)(unsubscribe|click\s+here\s+to\s+remove|opt\s+out|marketing\s+email)',
            category='Marketing Spam',
            confidence=0.85,
            description='Marketing/promotional email'
        ),
        
        # Phishing patterns
        EarlyExitPattern(
            pattern=r'(?i)(verify\s+your\s+account|suspended\s+account|confirm\s+identity|update\s+payment)',
            category='Phishing',
            confidence=0.90,
            description='Account phishing attempt'
        ),
        EarlyExitPattern(
            pattern=r'(?i)(paypal|amazon|apple|microsoft|google)\.com\-[a-z0-9]+\.',
            category='Phishing',
            confidence=0.95,
            description='Domain spoofing phishing'
        ),
        
        # Business opportunity
        EarlyExitPattern(
            pattern=r'(?i)(work\s+from\s+home|make\s+money\s+online|passive\s+income|financial\s+freedom)',
            category='Business Opportunity Spam',
            confidence=0.85,
            description='Work from home scam'
        ),
        
        # Auto warranty
        EarlyExitPattern(
            pattern=r'(?i)(auto\s+warrant|car\s+warrant|vehicle\s+protection|extended\s+warrant)',
            category='Scams',
            confidence=0.90,
            description='Auto warranty scam'
        )
    ]
    
    # Compiled patterns for performance
    COMPILED_PATTERNS = None
    
    def __init__(self):
        """Initialize classifier optimizer"""
        self._compile_patterns()
        self.stats = {
            'early_exits': 0,
            'cache_hits': 0,
            'full_classifications': 0,
            'total_time_saved': 0.0
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        if ClassifierOptimizer.COMPILED_PATTERNS is None:
            ClassifierOptimizer.COMPILED_PATTERNS = [
                EarlyExitPattern(
                    pattern=re.compile(ep.pattern),
                    category=ep.category,
                    confidence=ep.confidence,
                    description=ep.description
                )
                for ep in self.EARLY_EXIT_PATTERNS
            ]
    
    @performance_monitor("classification")
    def check_early_exit(self, sender: str, subject: str, body: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Check for early-exit spam patterns
        
        Returns classification result if pattern matches, None otherwise
        """
        with monitor_operation("classification", "early_exit_check"):
            # Combine text for checking
            text_to_check = f"{sender} {subject}"
            if body:
                # Only check first 500 chars of body for performance
                text_to_check += f" {body[:500]}"
            
            # Check each pattern
            for pattern in self.COMPILED_PATTERNS:
                if pattern.pattern.search(text_to_check):
                    self.stats['early_exits'] += 1
                    
                    return {
                        'is_spam': True,
                        'category': pattern.category,
                        'confidence': pattern.confidence,
                        'method': 'EARLY_EXIT',
                        'reason': pattern.description,
                        'processing_time_ms': 0.5  # Very fast
                    }
            
            return None
    
    @performance_monitor("classification")
    def optimize_classification(self, 
                              classifier_func,
                              sender: str,
                              subject: str,
                              body: Optional[str] = None,
                              headers: Optional[str] = None) -> Dict[str, Any]:
        """
        Optimize classification with caching and early exit
        
        Args:
            classifier_func: The actual classification function to call
            sender: Email sender
            subject: Email subject
            body: Email body (optional)
            headers: Email headers (optional)
            
        Returns:
            Classification result
        """
        start_time = time.time()
        
        # Step 1: Check early-exit patterns
        early_result = self.check_early_exit(sender, subject, body)
        if early_result:
            time_saved = 20 - (time.time() - start_time) * 1000  # Assume 20ms for full classification
            self.stats['total_time_saved'] += max(0, time_saved)
            return early_result
        
        # Step 2: Check cache
        if CACHE_ENABLED:
            cached_result = get_classification_cache(sender, subject)
            if cached_result:
                self.stats['cache_hits'] += 1
                # Add cache metadata
                cached_result['from_cache'] = True
                cached_result['cache_time_saved'] = 20  # ms
                self.stats['total_time_saved'] += 20
                return cached_result
        
        # Step 3: Full classification
        self.stats['full_classifications'] += 1
        result = classifier_func(sender=sender, subject=subject, body=body, headers=headers)
        
        # Cache the result
        if CACHE_ENABLED and result:
            set_classification_cache(sender, subject, result, ttl=7200)  # 2 hours
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        total_processed = (self.stats['early_exits'] + 
                          self.stats['cache_hits'] + 
                          self.stats['full_classifications'])
        
        if total_processed == 0:
            return self.stats
        
        return {
            **self.stats,
            'early_exit_rate': self.stats['early_exits'] / total_processed,
            'cache_hit_rate': self.stats['cache_hits'] / total_processed,
            'full_classification_rate': self.stats['full_classifications'] / total_processed,
            'avg_time_saved_ms': self.stats['total_time_saved'] / total_processed if total_processed > 0 else 0
        }


class ParallelClassificationOptimizer:
    """
    Optimizes classification for parallel processing
    """
    
    def __init__(self, num_classifiers: int = 2):
        """
        Initialize parallel classification optimizer
        
        Args:
            num_classifiers: Number of parallel classifiers to manage
        """
        self.num_classifiers = num_classifiers
        self.classifier_stats = defaultdict(lambda: {
            'processed': 0,
            'total_time': 0.0,
            'errors': 0
        })
        
    @performance_monitor("classification")
    def classify_parallel(self, 
                         classifiers: List[Any],
                         email_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Run multiple classifiers in parallel and combine results
        
        Args:
            classifiers: List of classifier instances
            email_data: Email data (sender, subject, body, headers)
            
        Returns:
            Combined classification result
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        with ThreadPoolExecutor(max_workers=len(classifiers)) as executor:
            # Submit classification tasks
            future_to_classifier = {}
            
            for i, classifier in enumerate(classifiers):
                future = executor.submit(
                    self._run_classifier,
                    classifier,
                    i,
                    email_data
                )
                future_to_classifier[future] = (i, classifier)
            
            # Collect results
            for future in as_completed(future_to_classifier):
                classifier_id, classifier = future_to_classifier[future]
                
                try:
                    result = future.result(timeout=1.0)  # 1 second timeout
                    results.append((classifier_id, result))
                except Exception as e:
                    self.classifier_stats[classifier_id]['errors'] += 1
                    print(f"Classifier {classifier_id} failed: {e}")
        
        # Combine results (majority voting or confidence-based)
        return self._combine_results(results)
    
    def _run_classifier(self, classifier, classifier_id: int, email_data: Dict[str, str]) -> Dict[str, Any]:
        """Run a single classifier"""
        start_time = time.time()
        
        try:
            result = classifier.classify_email(
                sender=email_data.get('sender', ''),
                subject=email_data.get('subject', ''),
                body=email_data.get('body', ''),
                headers=email_data.get('headers')
            )
            
            # Update stats
            elapsed = time.time() - start_time
            self.classifier_stats[classifier_id]['processed'] += 1
            self.classifier_stats[classifier_id]['total_time'] += elapsed
            
            return result
            
        except Exception as e:
            self.classifier_stats[classifier_id]['errors'] += 1
            raise
    
    def _combine_results(self, results: List[Tuple[int, Dict[str, Any]]]) -> Dict[str, Any]:
        """Combine results from multiple classifiers"""
        if not results:
            return {
                'is_spam': False,
                'category': 'Unknown',
                'confidence': 0.0,
                'method': 'NO_RESULTS'
            }
        
        # If only one result, return it
        if len(results) == 1:
            return results[0][1]
        
        # Multiple results - combine based on confidence
        spam_votes = 0
        total_confidence = 0.0
        categories = defaultdict(float)
        
        for classifier_id, result in results:
            if result.get('is_spam', False):
                spam_votes += 1
            
            confidence = result.get('confidence', 0.5)
            total_confidence += confidence
            
            category = result.get('category', 'Unknown')
            categories[category] += confidence
        
        # Determine final result
        is_spam = spam_votes > len(results) / 2
        avg_confidence = total_confidence / len(results)
        
        # Get highest confidence category
        final_category = max(categories.items(), key=lambda x: x[1])[0]
        
        return {
            'is_spam': is_spam,
            'category': final_category,
            'confidence': avg_confidence,
            'method': 'PARALLEL_CONSENSUS',
            'classifier_count': len(results),
            'spam_votes': spam_votes
        }


# Global optimizer instance
_classifier_optimizer = None

def get_classifier_optimizer() -> ClassifierOptimizer:
    """Get global classifier optimizer instance"""
    global _classifier_optimizer
    if _classifier_optimizer is None:
        _classifier_optimizer = ClassifierOptimizer()
    return _classifier_optimizer