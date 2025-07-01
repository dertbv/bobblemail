#!/usr/bin/env python3
"""
Strategic Integration Test - Standalone Test for Tier 3 System
Tests the conditional Strategic Framework integration without complex dependencies
"""

import time
import logging
import sys
import os
from typing import Dict, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass

# Initialize availability flags
STRATEGIC_FRAMEWORK_AVAILABLE = False

try:
    # Path to Strategic Framework
    framework_path = os.path.join(os.path.dirname(__file__), 'ADAPTIVE_SPAM_LOGIC_FRAMEWORK.py')
    if os.path.exists(framework_path):
        sys.path.insert(0, os.path.dirname(framework_path))
        from ADAPTIVE_SPAM_LOGIC_FRAMEWORK import AdaptiveSpamLogicFramework, ValidationResult, ThreatLevel
        STRATEGIC_FRAMEWORK_AVAILABLE = True
    else:
        print(f"Strategic Framework not found at: {framework_path}")
        
except ImportError as e:
    print(f"Import error for Strategic Framework: {e}")

# Fallback classes if Strategic Framework unavailable
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

class SimpleFastClassifier:
    """Simplified fast classifier for testing tier integration"""
    
    def __init__(self):
        self.suspicious_tlds = {'.cn', '.ru', '.tk', '.ml', '.ga', '.cf'}
        self.high_risk_patterns = ['fuck', 'xxx', 'porn', 'nude', 'horny']
        self.brand_names = ['walmart', 'amazon', 'apple', 'google', 'microsoft', 'chase']
        
    def classify_email(self, sender, subject, headers=""):
        """Simplified classification for testing"""
        full_text = f"{sender} {subject}".lower()
        
        # Tier 1: Instant obvious spam
        domain = self._extract_domain(sender)
        
        # Adult content - highest confidence
        if any(pattern in full_text for pattern in self.high_risk_patterns):
            return "Adult & Dating Spam", 0.98, "Explicit content detected"
        
        # Suspicious TLD
        if any(domain.endswith(tld) for tld in self.suspicious_tlds):
            return "Domain Spam", 0.95, f"Suspicious TLD: {domain}"
        
        # Tier 2: Geographic analysis (simulated)
        if headers and self._has_suspicious_ip(headers):
            return "Geographic Spam", 0.90, "Suspicious IP detected"
        
        # Brand impersonation detection (uncertain cases)
        for brand in self.brand_names:
            if brand in full_text and not domain.endswith(f"{brand}.com"):
                # This is uncertain - needs Strategic analysis
                return "Possible Brand Impersonation", 0.65, f"Potential {brand} impersonation"
        
        # Generic spam (moderate confidence)
        spam_indicators = ['winner', 'prize', 'lottery', 'urgent', 'verify', 'claim']
        if any(indicator in full_text for indicator in spam_indicators):
            return "Marketing Spam", 0.75, "Spam indicators detected"
        
        # Uncertain case
        return "Unknown Classification", 0.50, "Requires further analysis"
    
    def _extract_domain(self, sender):
        """Extract domain from sender"""
        if '@' not in sender:
            return ""
        try:
            return sender.split('@')[1].strip().replace('>', '').lower()
        except:
            return ""
    
    def _has_suspicious_ip(self, headers):
        """Check for suspicious IP patterns"""
        suspicious_ranges = ['103.45.', '45.67.', '185.220.']
        return any(ip_range in headers for ip_range in suspicious_ranges)

class StrategicIntegrationTester:
    """Test the Strategic Integration architecture"""
    
    def __init__(self, confidence_threshold=0.7):
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # Initialize fast classifier
        self.fast_classifier = SimpleFastClassifier()
        
        # Initialize Strategic Framework
        self.strategic_framework = None
        if STRATEGIC_FRAMEWORK_AVAILABLE:
            try:
                self.strategic_framework = AdaptiveSpamLogicFramework(logger=self.logger)
                print("✅ Strategic Framework loaded successfully")
            except Exception as e:
                print(f"❌ Strategic Framework initialization failed: {e}")
        else:
            print("❌ Strategic Framework not available (using fallback)")
        
        # Performance tracking
        self.tier_stats = {tier: 0 for tier in TierUsage}
        self.total_processed = 0
    
    def classify_email(self, sender, subject, headers="", sender_name=""):
        """Test the 3-tier classification system"""
        start_time = time.time()
        self.total_processed += 1
        
        # Tier 1 & 2: Fast classification
        category, confidence, reason = self.fast_classifier.classify_email(sender, subject, headers)
        
        # Determine tier used
        tier_used = self._determine_tier(category, confidence, headers)
        
        # Conditional Tier 3 escalation
        strategic_analysis = None
        
        if (confidence < self.confidence_threshold and
            not self._is_obvious_spam(category, confidence) and
            self.strategic_framework):
            
            print(f"🔍 Escalating to Tier 3 Strategic analysis: {sender} (confidence: {confidence:.2f})")
            
            # Run Strategic Framework
            strategic_analysis = self._run_strategic_analysis(sender, subject, sender_name)
            
            if strategic_analysis:
                category, confidence, reason = self._integrate_strategic_results(
                    category, confidence, reason, strategic_analysis
                )
                tier_used = TierUsage.TIER_3_STRATEGIC
        
        self.tier_stats[tier_used] += 1
        processing_time = (time.time() - start_time) * 1000
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            reason=reason,
            tier_used=tier_used,
            processing_time_ms=processing_time,
            strategic_analysis=strategic_analysis
        )
    
    def _determine_tier(self, category, confidence, headers):
        """Determine which tier was used"""
        if category in ["Adult & Dating Spam", "Domain Spam"] or confidence >= 0.95:
            return TierUsage.TIER_1_INSTANT
        elif category == "Geographic Spam" or headers:
            return TierUsage.TIER_2_GEOGRAPHIC
        else:
            return TierUsage.TIER_1_INSTANT
    
    def _is_obvious_spam(self, category, confidence):
        """Check if this needs Strategic analysis"""
        obvious_categories = ["Adult & Dating Spam", "Domain Spam", "Geographic Spam"]
        return category in obvious_categories or confidence >= 0.95
    
    def _run_strategic_analysis(self, sender, subject, sender_name):
        """Run Strategic Framework analysis"""
        try:
            domain = self.fast_classifier._extract_domain(sender)
            if not domain:
                return None
            
            result = self.strategic_framework.validate_email(
                sender_email=sender,
                sender_domain=domain,
                sender_name=sender_name,
                subject=subject
            )
            return result
        except Exception as e:
            print(f"❌ Strategic analysis failed: {e}")
            return None
    
    def _integrate_strategic_results(self, fast_category, fast_confidence, fast_reason, strategic_result):
        """Integrate Strategic Framework results"""
        threat_mapping = {
            ThreatLevel.LEGITIMATE: ("Legitimate Email", 0.90),
            ThreatLevel.SUSPICIOUS: ("Suspicious Email", 0.60),
            ThreatLevel.HIGH_RISK: ("High Risk Spam", 0.80),
            ThreatLevel.PHISHING: ("Phishing", 0.95)
        }
        
        if strategic_result.threat_level in threat_mapping:
            strategic_category, _ = threat_mapping[strategic_result.threat_level]
            strategic_confidence = min(strategic_result.confidence, 0.95)
            strategic_reason = f"Strategic: {strategic_result.threat_level.value} " \
                             f"(Auth: {strategic_result.authentication_score}%, " \
                             f"Business: {strategic_result.business_score}%)"
            
            if strategic_confidence >= 0.8:
                return strategic_category, strategic_confidence, strategic_reason
            else:
                combined_confidence = (fast_confidence + strategic_confidence) / 2
                combined_reason = f"{fast_reason} | {strategic_reason}"
                return strategic_category, combined_confidence, combined_reason
        
        return fast_category, fast_confidence, fast_reason
    
    def get_stats(self):
        """Get performance statistics"""
        if self.total_processed == 0:
            return {"message": "No emails processed"}
        
        percentages = {
            tier.value: (count / self.total_processed) * 100 
            for tier, count in self.tier_stats.items()
        }
        
        strategic_usage = percentages.get("TIER_3_STRATEGIC", 0)
        
        return {
            "total_processed": self.total_processed,
            "tier_1_instant": f"{percentages['TIER_1_INSTANT']:.1f}%",
            "tier_2_geographic": f"{percentages['TIER_2_GEOGRAPHIC']:.1f}%", 
            "tier_3_strategic": f"{strategic_usage:.1f}%",
            "strategic_target": "< 1%",
            "within_target": strategic_usage < 1.0,
            "framework_available": STRATEGIC_FRAMEWORK_AVAILABLE
        }

def test_strategic_integration():
    """Test the Strategic Integration system"""
    
    print("🎯 Strategic Integration Test - 3-Tier Architecture")
    print("=" * 60)
    print(f"Strategic Framework Available: {STRATEGIC_FRAMEWORK_AVAILABLE}")
    print()
    
    tester = StrategicIntegrationTester(confidence_threshold=0.7)
    
    # Test cases designed to trigger different tiers
    test_cases = [
        # Tier 1: Obvious spam (instant detection)
        {
            "sender": "fuck@example.cn",
            "subject": "XXX Adult Content",
            "headers": "",
            "sender_name": "",
            "expected_tier": "TIER_1_INSTANT",
            "description": "Adult content + suspicious TLD"
        },
        
        # Tier 2: Geographic analysis
        {
            "sender": "business@normalsite.com",
            "subject": "Investment opportunity",
            "headers": "Received: from [103.45.123.45] by mail.example.com",
            "sender_name": "",
            "expected_tier": "TIER_2_GEOGRAPHIC", 
            "description": "Suspicious IP range"
        },
        
        # Tier 3: Uncertain brand impersonation (Strategic analysis needed)
        {
            "sender": "support@suspicious-bank.com",
            "subject": "Chase account verification required",
            "headers": "",
            "sender_name": "Chase Bank Support",
            "expected_tier": "TIER_3_STRATEGIC",
            "description": "Brand impersonation (uncertain)"
        },
        
        # Tier 3: Borderline legitimate case 
        {
            "sender": "reply@ss.email.nextdoor.com",
            "subject": "Hello.",
            "headers": "",
            "sender_name": "Sugarland Run Trending Posts",
            "expected_tier": "TIER_3_STRATEGIC",
            "description": "Nextdoor misclassification case"
        },
        
        # High confidence marketing (Tier 1)
        {
            "sender": "winner@lottery.tk",
            "subject": "You won the lottery! Claim now!",
            "headers": "",
            "sender_name": "",
            "expected_tier": "TIER_1_INSTANT",
            "description": "Obvious lottery spam"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"🧪 Test Case {i}: {test['description']}")
        print(f"📧 From: {test['sender']}")
        print(f"📝 Subject: {test['subject']}")
        
        result = tester.classify_email(
            sender=test['sender'],
            subject=test['subject'],
            headers=test['headers'],
            sender_name=test['sender_name']
        )
        
        print(f"🎯 Classification: {result.category}")
        print(f"📊 Confidence: {result.confidence:.2f}")
        print(f"⚡ Tier Used: {result.tier_used.value}")
        print(f"⏱️  Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"💭 Reason: {result.reason}")
        
        if result.strategic_analysis:
            print(f"🧠 Strategic Analysis: {result.strategic_analysis.threat_level.value}")
            print(f"   🔐 Auth Score: {result.strategic_analysis.authentication_score}%")
            print(f"   🏢 Business Score: {result.strategic_analysis.business_score}%")
        
        # Check if tier matches expectation
        tier_match = "✅" if result.tier_used.value == test['expected_tier'] else "❌"
        print(f"{tier_match} Expected: {test['expected_tier']}, Got: {result.tier_used.value}")
        print("-" * 50)
    
    # Performance Statistics
    print("\n📊 Performance Statistics")
    print("=" * 40)
    stats = tester.get_stats()
    
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🎯 Mission Status:")
    print(f"Strategic Framework Available: {'✅' if stats['framework_available'] else '❌'}")
    print(f"Strategic Usage Target (<1%): {'✅' if stats['within_target'] else '❌'}")
    
    strategic_percent = float(stats['tier_3_strategic'].replace('%', ''))
    performance_preserved = (100 - strategic_percent) >= 99
    print(f"Performance Preserved (≥99%): {'✅' if performance_preserved else '❌'}")

if __name__ == "__main__":
    test_strategic_integration()