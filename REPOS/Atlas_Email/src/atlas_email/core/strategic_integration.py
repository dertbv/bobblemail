#!/usr/bin/env python3
"""
Strategic Intelligence Framework Integration - Tier 3 System
Optimal placement for uncertain cases only (confidence < 0.7)

Mission: Add Strategic Framework intelligence for <1% uncertain cases 
without impacting 99%+ fast processing performance.
"""

import time
import logging
from typing import Dict, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
# Will be imported dynamically below

# Initialize availability flags
STRATEGIC_FRAMEWORK_AVAILABLE = False
LOGICAL_CLASSIFIER_AVAILABLE = False

try:
    import sys
    import os
    
    # Add paths for both the Strategic Framework and logical classifier
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to Strategic Framework (in project root)
    framework_path = os.path.join(current_dir, '..', '..', '..', '..', 'ADAPTIVE_SPAM_LOGIC_FRAMEWORK.py')
    if os.path.exists(framework_path):
        sys.path.insert(0, os.path.dirname(framework_path))
        from ADAPTIVE_SPAM_LOGIC_FRAMEWORK import AdaptiveSpamLogicFramework, ValidationResult, ThreatLevel
        STRATEGIC_FRAMEWORK_AVAILABLE = True
    
    # Path to logical classifier (same directory) 
    logical_classifier_path = os.path.join(current_dir, 'logical_classifier.py')
    if os.path.exists(logical_classifier_path):
        sys.path.insert(0, current_dir)
        from logical_classifier import LogicalEmailClassifier
        LOGICAL_CLASSIFIER_AVAILABLE = True
        
except ImportError as e:
    print(f"Import error: {e}")
    pass

# Fallback classes if imports fail
if not STRATEGIC_FRAMEWORK_AVAILABLE:
    class ThreatLevel(Enum):
            LEGITIMATE = "LEGITIMATE"
            SUSPICIOUS = "SUSPICIOUS"
            HIGH_RISK = "HIGH_RISK"
            PHISHING = "PHISHING"
    
    @dataclass
    class ValidationResult:
        threat_level: ThreatLevel
        confidence: float
        reasons: list
        authentication_score: int = 0
        business_score: int = 0
        content_score: int = 0
        geographic_score: int = 0
        network_score: int = 0
    
    class AdaptiveSpamLogicFramework:
        def validate_email(self, sender_email, sender_domain, sender_name, subject):
            return ValidationResult(ThreatLevel.SUSPICIOUS, 0.5, ["Strategic Framework unavailable"])

# Fallback LogicalEmailClassifier if not available
if not LOGICAL_CLASSIFIER_AVAILABLE:
    class LogicalEmailClassifier:
        def __init__(self):
            pass
        
        def classify_email(self, sender, subject, headers=""):
            return "General Spam", 0.5, "Logical classifier unavailable"
        
        def _extract_sender_ip(self, headers):
            return None
        
        def _is_suspicious_tld(self, domain):
            return domain.endswith(('.cn', '.ru', '.tk', '.ml'))

class TierUsage(Enum):
    TIER_1_INSTANT = "TIER_1_INSTANT"
    TIER_2_GEOGRAPHIC = "TIER_2_GEOGRAPHIC" 
    TIER_3_STRATEGIC = "TIER_3_STRATEGIC"

@dataclass
class ClassificationResult:
    """Enhanced classification result with tier tracking"""
    category: str
    confidence: float
    reason: str
    tier_used: TierUsage
    processing_time_ms: float
    strategic_analysis: Optional[ValidationResult] = None

class StrategicEmailClassifier:
    """
    3-Tier Email Classification System with Strategic Framework Integration
    
    Tier 1: Instant detection (obvious spam, TLD blacklist, domain cache)
    Tier 2: Fast geographic intelligence (IP analysis, suspicious ranges)
    Tier 3: Strategic deep analysis (uncertain cases only, confidence < 0.7)
    """
    
    def __init__(self, confidence_threshold: float = 0.7, logger=None):
        self.confidence_threshold = confidence_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize Tier 1 & 2 (fast pipeline)
        self.logical_classifier = LogicalEmailClassifier()
        
        # Initialize Tier 3 (strategic framework) 
        self.strategic_framework = None
        if STRATEGIC_FRAMEWORK_AVAILABLE:
            try:
                self.strategic_framework = AdaptiveSpamLogicFramework(logger=self.logger)
                self.logger.info("🎯 Strategic Framework loaded successfully")
            except Exception as e:
                self.logger.warning(f"Strategic Framework initialization failed: {e}")
                STRATEGIC_FRAMEWORK_AVAILABLE = False
        
        # Performance monitoring
        self.tier_usage_stats = {
            TierUsage.TIER_1_INSTANT: 0,
            TierUsage.TIER_2_GEOGRAPHIC: 0,
            TierUsage.TIER_3_STRATEGIC: 0
        }
        self.total_emails_processed = 0
        
    def classify_email(self, sender: str, subject: str, headers: str = "", sender_name: str = "") -> ClassificationResult:
        """
        Main classification method with 3-tier architecture
        
        Args:
            sender: Email sender address
            subject: Email subject line  
            headers: Email headers (for IP extraction)
            sender_name: Sender display name
            
        Returns:
            ClassificationResult: Classification with tier tracking and performance metrics
        """
        start_time = time.time()
        self.total_emails_processed += 1
        
        # TIER 1 & 2: Fast Classification Pipeline
        category, confidence, reason = self.logical_classifier.classify_email(sender, subject, headers)
        
        # Determine which tier was used based on classification path
        tier_used = self._determine_tier_used(category, confidence, sender, headers)
        
        # CONDITIONAL TIER 3 ESCALATION
        # Only use expensive Strategic Framework for uncertain cases
        strategic_analysis = None
        
        if (confidence < self.confidence_threshold and 
            not self._is_obvious_spam(category, confidence) and
            STRATEGIC_FRAMEWORK_AVAILABLE and 
            self.strategic_framework):
            
            # TIER 3: Strategic Deep Analysis for uncertain cases
            strategic_analysis = self._run_strategic_analysis(sender, subject, sender_name)
            
            if strategic_analysis:
                # Use Strategic Framework results for final classification
                category, confidence, reason = self._integrate_strategic_results(
                    category, confidence, reason, strategic_analysis
                )
                tier_used = TierUsage.TIER_3_STRATEGIC
        
        # Update tier usage statistics
        self.tier_usage_stats[tier_used] += 1
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            reason=reason,
            tier_used=tier_used,
            processing_time_ms=processing_time_ms,
            strategic_analysis=strategic_analysis
        )
    
    def _determine_tier_used(self, category: str, confidence: float, sender: str, headers: str) -> TierUsage:
        """Determine which tier was used for classification"""
        
        # Tier 1 indicators: Instant detection patterns
        sender_domain = self._extract_domain_fast(sender)
        
        # TLD blacklist, domain cache, obvious spam = Tier 1
        if (self.logical_classifier._is_suspicious_tld(sender_domain) or
            category in ["Domain Spam", "Adult & Dating Spam"] or
            confidence >= 0.95):
            return TierUsage.TIER_1_INSTANT
        
        # Geographic analysis = Tier 2
        if category == "Geographic Spam" or self._has_ip_analysis(headers):
            return TierUsage.TIER_2_GEOGRAPHIC
        
        # Default to Tier 1 for other fast classifications
        return TierUsage.TIER_1_INSTANT
    
    def _extract_domain_fast(self, sender: str) -> str:
        """Fast domain extraction"""
        if '@' not in sender:
            return ""
        try:
            return sender.split('@')[1].strip().replace('>', '').lower()
        except:
            return ""
    
    def _has_ip_analysis(self, headers: str) -> bool:
        """Check if geographic IP analysis was performed"""
        return bool(headers and self.logical_classifier._extract_sender_ip(headers))
    
    def _is_obvious_spam(self, category: str, confidence: float) -> bool:
        """Check if this is obvious spam that doesn't need Strategic analysis"""
        obvious_spam_categories = [
            "Adult & Dating Spam",
            "Domain Spam", 
            "Geographic Spam"
        ]
        return category in obvious_spam_categories or confidence >= 0.95
    
    def _run_strategic_analysis(self, sender: str, subject: str, sender_name: str) -> Optional[ValidationResult]:
        """Run Strategic Framework analysis for uncertain cases"""
        try:
            sender_domain = self._extract_domain_fast(sender)
            
            if not sender_domain:
                return None
            
            self.logger.debug(f"🔍 Running Strategic analysis for uncertain case: {sender}")
            
            # Run comprehensive Strategic Framework validation
            result = self.strategic_framework.validate_email(
                sender_email=sender,
                sender_domain=sender_domain,
                sender_name=sender_name,
                subject=subject
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Strategic Framework analysis failed for {sender}: {e}")
            return None
    
    def _integrate_strategic_results(self, fast_category: str, fast_confidence: float, 
                                   fast_reason: str, strategic_result: ValidationResult) -> Tuple[str, float, str]:
        """Integrate Strategic Framework results with fast classification"""
        
        # Map Strategic Framework threat levels to classification categories
        threat_mapping = {
            ThreatLevel.LEGITIMATE: ("Legitimate Email", 0.9),
            ThreatLevel.SUSPICIOUS: ("Suspicious Email", 0.6),
            ThreatLevel.HIGH_RISK: ("High Risk Spam", 0.8),
            ThreatLevel.PHISHING: ("Phishing", 0.95)
        }
        
        if strategic_result.threat_level in threat_mapping:
            strategic_category, base_confidence = threat_mapping[strategic_result.threat_level]
            
            # Use Strategic Framework confidence score
            strategic_confidence = min(strategic_result.confidence, 0.95)
            
            # Create combined reason
            strategic_reason = f"Strategic analysis: {strategic_result.threat_level.value} " \
                             f"(Auth: {strategic_result.authentication_score}%, " \
                             f"Business: {strategic_result.business_score}%)"
            
            # If Strategic Framework has high confidence, use its results
            if strategic_confidence >= 0.8:
                return strategic_category, strategic_confidence, strategic_reason
            
            # If Strategic Framework is uncertain, combine with fast results
            else:
                combined_confidence = (fast_confidence + strategic_confidence) / 2
                combined_reason = f"{fast_reason} | {strategic_reason}"
                
                # Use the more specific category
                category = strategic_category if strategic_confidence > fast_confidence else fast_category
                
                return category, combined_confidence, combined_reason
        
        # Fallback to fast classification if Strategic results are unclear
        return fast_category, fast_confidence, fast_reason
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance and tier usage statistics"""
        
        if self.total_emails_processed == 0:
            return {"status": "No emails processed yet"}
        
        tier_percentages = {
            tier.value: (count / self.total_emails_processed) * 100 
            for tier, count in self.tier_usage_stats.items()
        }
        
        strategic_usage_percent = tier_percentages.get("TIER_3_STRATEGIC", 0)
        
        return {
            "total_emails_processed": self.total_emails_processed,
            "tier_usage": {
                "tier_1_instant": {
                    "count": self.tier_usage_stats[TierUsage.TIER_1_INSTANT],
                    "percentage": tier_percentages["TIER_1_INSTANT"]
                },
                "tier_2_geographic": {
                    "count": self.tier_usage_stats[TierUsage.TIER_2_GEOGRAPHIC], 
                    "percentage": tier_percentages["TIER_2_GEOGRAPHIC"]
                },
                "tier_3_strategic": {
                    "count": self.tier_usage_stats[TierUsage.TIER_3_STRATEGIC],
                    "percentage": strategic_usage_percent
                }
            },
            "strategic_framework": {
                "available": STRATEGIC_FRAMEWORK_AVAILABLE,
                "usage_target": "< 1% of emails",
                "actual_usage": f"{strategic_usage_percent:.2f}%",
                "within_target": strategic_usage_percent < 1.0
            },
            "confidence_threshold": self.confidence_threshold,
            "performance_preserved": tier_percentages["TIER_1_INSTANT"] + tier_percentages["TIER_2_GEOGRAPHIC"] > 99.0
        }
    
    def update_confidence_threshold(self, new_threshold: float):
        """Update the confidence threshold for Strategic Framework escalation"""
        old_threshold = self.confidence_threshold
        self.confidence_threshold = max(0.1, min(0.9, new_threshold))
        
        self.logger.info(f"Confidence threshold updated: {old_threshold:.2f} → {self.confidence_threshold:.2f}")
    
    def reset_statistics(self):
        """Reset performance monitoring statistics"""
        self.tier_usage_stats = {tier: 0 for tier in TierUsage}
        self.total_emails_processed = 0
        self.logger.info("Performance statistics reset")


def test_strategic_integration():
    """Test the 3-tier Strategic Integration system"""
    
    print("🎯 Testing Strategic Integration - 3-Tier Architecture")
    print("=" * 60)
    
    classifier = StrategicEmailClassifier(confidence_threshold=0.7)
    
    # Test cases designed to trigger different tiers
    test_cases = [
        # Tier 1: Obvious spam (should be instant)
        {
            "sender": "fuck@example.cn",
            "subject": "XXX Adult Content", 
            "headers": "",
            "sender_name": "",
            "expected_tier": "TIER_1_INSTANT"
        },
        
        # Tier 2: Geographic analysis
        {
            "sender": "test@suspicious-domain.com",
            "subject": "Business opportunity",
            "headers": "Received: from [103.45.123.45] by mail.example.com",
            "sender_name": "",
            "expected_tier": "TIER_2_GEOGRAPHIC"
        },
        
        # Tier 3: Uncertain case (borderline legitimate)
        {
            "sender": "reply@ss.email.nextdoor.com",
            "subject": "Hello.",
            "headers": "",
            "sender_name": "Sugarland Run Trending Posts",
            "expected_tier": "TIER_3_STRATEGIC"
        },
        
        # Tier 3: Brand impersonation edge case
        {
            "sender": "support@suspicious-bank.com",
            "subject": "Account verification required",
            "headers": "",
            "sender_name": "Chase Bank Support",
            "expected_tier": "TIER_3_STRATEGIC"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test['expected_tier']}")
        print(f"📧 From: {test['sender']}")
        print(f"📝 Subject: {test['subject']}")
        
        result = classifier.classify_email(
            sender=test['sender'],
            subject=test['subject'], 
            headers=test['headers'],
            sender_name=test['sender_name']
        )
        
        print(f"🎯 Classification: {result.category} (confidence: {result.confidence:.2f})")
        print(f"⚡ Tier Used: {result.tier_used.value}")
        print(f"⏱️  Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"💭 Reason: {result.reason}")
        
        if result.strategic_analysis:
            print(f"🧠 Strategic Analysis: {result.strategic_analysis.threat_level.value}")
            print(f"   Auth: {result.strategic_analysis.authentication_score}%, "
                  f"Business: {result.strategic_analysis.business_score}%")
    
    # Performance Statistics
    print(f"\n📊 Performance Statistics")
    print("=" * 40)
    stats = classifier.get_performance_stats()
    
    print(f"Total Emails: {stats['total_emails_processed']}")
    print(f"Tier 1 (Instant): {stats['tier_usage']['tier_1_instant']['percentage']:.1f}%")
    print(f"Tier 2 (Geographic): {stats['tier_usage']['tier_2_geographic']['percentage']:.1f}%") 
    print(f"Tier 3 (Strategic): {stats['tier_usage']['tier_3_strategic']['percentage']:.1f}%")
    print(f"Strategic Framework Available: {stats['strategic_framework']['available']}")
    print(f"Performance Target Met: {stats['performance_preserved']}")


if __name__ == "__main__":
    test_strategic_integration()