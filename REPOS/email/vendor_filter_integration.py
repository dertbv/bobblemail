#!/usr/bin/env python3
"""
Vendor Filter Integration

Integrates the selective vendor filter with the existing spam classification system.
This module provides a seamless interface that enhances the existing spam classifier
with intelligent vendor-specific filtering.
"""

import logging
from typing import Tuple, Optional, Dict, Any
from selective_vendor_filter import selective_vendor_filter, EmailIntent, VendorEmailClassification
from vendor_preferences_schema import log_vendor_classification

class VendorFilterIntegration:
    """
    Integration layer between selective vendor filter and spam classifier
    
    This class provides the interface for the existing spam classification system
    to leverage selective vendor filtering capabilities.
    """
    
    def __init__(self):
        """Initialize the vendor filter integration"""
        self.vendor_filter = selective_vendor_filter
        self.stats = {
            'total_processed': 0,
            'vendor_emails_processed': 0,
            'vendor_emails_preserved': 0,
            'vendor_emails_filtered': 0,
            'unknown_vendors': 0
        }
        
        logging.info("🎯 Vendor Filter Integration initialized")
    
    def should_preserve_vendor_email(self, sender_email: str, sender_domain: str,
                                   subject: str, content: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Determine if a vendor email should be preserved based on selective filtering
        
        Args:
            sender_email: Full sender email address
            sender_domain: Sender domain
            subject: Email subject line
            content: Email content (optional)
            
        Returns:
            Tuple of (should_preserve, reason, metadata)
        """
        
        self.stats['total_processed'] += 1
        
        try:
            # Process email through selective vendor filter
            classification = self.vendor_filter.process_vendor_email(
                sender_email, sender_domain, subject, content
            )
            
            # Update statistics
            if classification.vendor != "unknown":
                self.stats['vendor_emails_processed'] += 1
                
                if classification.should_preserve:
                    self.stats['vendor_emails_preserved'] += 1
                else:
                    self.stats['vendor_emails_filtered'] += 1
                    
                # Log classification for analysis
                self._log_classification(classification, sender_email, subject)
            else:
                self.stats['unknown_vendors'] += 1
            
            # Prepare detailed reasoning
            reason = self._format_vendor_reason(classification)
            
            # Prepare metadata for logging/debugging
            metadata = {
                'vendor': classification.vendor,
                'intent': classification.intent.value,
                'confidence': classification.confidence,
                'matched_patterns': classification.matched_patterns,
                'classification_method': 'selective_vendor_filter'
            }
            
            return classification.should_preserve, reason, metadata
            
        except Exception as e:
            logging.error(f"Error in vendor filter integration: {e}")
            
            # Conservative fallback - preserve email if there's an error
            return True, f"Vendor filter error: {str(e)}", {
                'error': str(e),
                'classification_method': 'error_fallback'
            }
    
    def _log_classification(self, classification: VendorEmailClassification, 
                           sender_email: str, subject: str):
        """Log vendor classification for analysis and learning"""
        
        try:
            log_vendor_classification(
                vendor_domain=classification.vendor,
                sender_email=sender_email,
                subject=subject,
                classified_intent=classification.intent.value,
                confidence_score=classification.confidence,
                should_preserve=classification.should_preserve,
                actual_action='PRESERVED' if classification.should_preserve else 'FILTERED',
                matched_patterns=classification.matched_patterns,
                reasoning=classification.reasoning
            )
        except Exception as e:
            logging.warning(f"Could not log vendor classification: {e}")
    
    def _format_vendor_reason(self, classification: VendorEmailClassification) -> str:
        """Format vendor classification into human-readable reason"""
        
        if classification.vendor == "unknown":
            return "Unknown vendor - preserved by default"
        
        action = "preserved" if classification.should_preserve else "filtered"
        intent_desc = {
            EmailIntent.TRANSACTIONAL: "transaction-related",
            EmailIntent.MARKETING: "marketing/promotional", 
            EmailIntent.SERVICE: "customer service",
            EmailIntent.SECURITY: "security/account alert",
            EmailIntent.PROMOTIONAL: "promotional/survey",
            EmailIntent.UNKNOWN: "unclassified"
        }
        
        intent_text = intent_desc.get(classification.intent, "unclassified")
        
        if classification.confidence >= 0.8:
            confidence_text = "high confidence"
        elif classification.confidence >= 0.6:
            confidence_text = "medium confidence"
        else:
            confidence_text = "low confidence"
        
        return f"Vendor: {classification.vendor} | Intent: {intent_text} | {action} ({confidence_text})"
    
    def is_vendor_email(self, sender_email: str, sender_domain: str) -> bool:
        """Check if email is from a recognized vendor"""
        
        vendor = self.vendor_filter.extract_vendor_from_email(sender_email, sender_domain)
        return vendor is not None and vendor != "unknown"
    
    def get_vendor_from_email(self, sender_email: str, sender_domain: str) -> Optional[str]:
        """Extract vendor identifier from email"""
        
        return self.vendor_filter.extract_vendor_from_email(sender_email, sender_domain)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vendor filtering statistics"""
        
        # Add percentage calculations
        total = self.stats['total_processed']
        vendor_total = self.stats['vendor_emails_processed']
        
        enhanced_stats = self.stats.copy()
        
        if total > 0:
            enhanced_stats['vendor_email_percentage'] = (vendor_total / total) * 100
            
        if vendor_total > 0:
            enhanced_stats['vendor_preservation_rate'] = (
                self.stats['vendor_emails_preserved'] / vendor_total
            ) * 100
            enhanced_stats['vendor_filtering_rate'] = (
                self.stats['vendor_emails_filtered'] / vendor_total  
            ) * 100
        
        # Get vendor filter statistics
        try:
            vendor_stats = self.vendor_filter.get_vendor_statistics()
            enhanced_stats.update(vendor_stats)
        except Exception:
            pass
        
        return enhanced_stats
    
    def reset_statistics(self):
        """Reset processing statistics"""
        
        self.stats = {
            'total_processed': 0,
            'vendor_emails_processed': 0,
            'vendor_emails_preserved': 0,
            'vendor_emails_filtered': 0,
            'unknown_vendors': 0
        }

# Global instance for use by spam classifier
vendor_filter_integration = VendorFilterIntegration()

def enhance_spam_classification_with_vendor_filter(sender_email: str, sender_domain: str,
                                                  subject: str, content: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Enhanced spam classification that includes selective vendor filtering
    
    This is the main integration point that should be called by the spam classifier
    to check if an email should be preserved based on vendor-specific rules.
    
    Returns:
        Tuple of (should_preserve, reason, metadata)
    """
    
    return vendor_filter_integration.should_preserve_vendor_email(
        sender_email, sender_domain, subject, content
    )

def is_recognized_vendor(sender_email: str, sender_domain: str) -> bool:
    """
    Check if email is from a recognized vendor
    
    This can be used by the spam classifier to decide whether to apply
    vendor-specific filtering or use standard spam detection.
    """
    
    return vendor_filter_integration.is_vendor_email(sender_email, sender_domain)

def get_vendor_filtering_stats() -> Dict[str, Any]:
    """Get vendor filtering statistics for reporting"""
    
    return vendor_filter_integration.get_statistics()

def test_vendor_integration():
    """Test the vendor filter integration with sample emails"""
    
    print("🧪 Testing Vendor Filter Integration...")
    
    test_cases = [
        # Chase transactional (should preserve)
        {
            'sender': 'alerts@chase.com',
            'domain': 'chase.com',
            'subject': 'Your Chase statement is ready',
            'content': 'Your monthly statement for account ending in 1234 is now available.',
            'expected_preserve': True
        },
        
        # Chase marketing (should filter)
        {
            'sender': 'offers@chase.com',
            'domain': 'chase.com', 
            'subject': 'You\'re pre-approved for Chase Sapphire',
            'content': 'Earn 60,000 bonus points with this limited time offer.',
            'expected_preserve': False
        },
        
        # Amazon order (should preserve)
        {
            'sender': 'auto-confirm@amazon.com',
            'domain': 'amazon.com',
            'subject': 'Your order has shipped',
            'content': 'Order #123-456-789 has shipped via UPS. Tracking: 1Z234567890',
            'expected_preserve': True
        },
        
        # Amazon recommendations (should filter)
        {
            'sender': 'store-news@amazon.com',
            'domain': 'amazon.com',
            'subject': 'Recommended for you',
            'content': 'Based on your recent purchases, here are some items you might like.',
            'expected_preserve': False
        },
        
        # Unknown vendor (should preserve)
        {
            'sender': 'info@unknowncompany.com',
            'domain': 'unknowncompany.com',
            'subject': 'Newsletter Update',
            'content': 'Here is our monthly newsletter.',
            'expected_preserve': True
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        should_preserve, reason, metadata = enhance_spam_classification_with_vendor_filter(
            test_case['sender'],
            test_case['domain'],
            test_case['subject'],
            test_case['content']
        )
        
        print(f"\n--- Test {i} ---")
        print(f"Email: {test_case['subject']}")
        print(f"Expected preserve: {test_case['expected_preserve']}")
        print(f"Actual preserve: {should_preserve}")
        print(f"Reason: {reason}")
        print(f"Metadata: {metadata}")
        
        if should_preserve == test_case['expected_preserve']:
            print("✅ Test PASSED")
            passed += 1
        else:
            print("❌ Test FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    # Show statistics
    print(f"\n📈 Integration Statistics:")
    stats = get_vendor_filtering_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        elif isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_vendor_integration()