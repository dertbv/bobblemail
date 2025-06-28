#!/usr/bin/env python3
"""
Vendor Relationship Detection Module
KISS Implementation: Use email history as ground truth for legitimate vendor relationships
"""

import re
from typing import Dict, Optional, Tuple
from database import DatabaseManager

class VendorRelationshipDetector:
    """
    KISS vendor relationship detection using email history as ground truth.
    
    Core Logic:
    1. Extract sender domain from email
    2. Query database for prior preserved (non-spam) emails from that domain
    3. If relationship exists + email looks like subscription/digest → "Transactional Email"
    4. If no relationship → Continue with normal spam classification
    
    Performance optimized: Only called after cheap filters have run.
    """
    
    def __init__(self):
        # Use the Atlas_Email database where the actual email data is stored
        import os
        atlas_db_path = os.path.join(os.path.dirname(__file__), "../Atlas_Email/data/mail_filter.db")
        atlas_db_path = os.path.abspath(atlas_db_path)
        
        self.db = DatabaseManager(atlas_db_path)
        self._domain_cache = {}  # Cache relationship results for performance
        print(f"🔍 VendorRelationshipDetector using database: {self.db.db_path}")
    
    def has_vendor_relationship(self, sender_email: str, sender_domain: str) -> Tuple[bool, Dict]:
        """
        Check if we have an existing vendor relationship with this domain.
        
        Returns:
            Tuple[bool, Dict]: (has_relationship, relationship_info)
        """
        # Check cache first
        if sender_domain in self._domain_cache:
            cached_result = self._domain_cache[sender_domain]
            return cached_result['has_relationship'], cached_result
        
        # Query database for preserved emails from this domain
        query = """
            SELECT 
                COUNT(*) as total_preserved,
                COUNT(CASE WHEN category = 'Transactional Email' THEN 1 END) as transactional_count,
                MIN(timestamp) as first_email_date,
                MAX(timestamp) as last_email_date,
                GROUP_CONCAT(DISTINCT reason) as example_reasons
            FROM processed_emails_bulletproof 
            WHERE sender_domain = ? 
            AND action = 'PRESERVED'
        """
        
        results = self.db.execute_query(query, (sender_domain,))
        
        if not results:
            # Cache negative result
            relationship_info = {
                'has_relationship': False,
                'total_preserved': 0,
                'confidence': 'none'
            }
            self._domain_cache[sender_domain] = relationship_info
            return False, relationship_info
        
        row = results[0]
        total_preserved = row['total_preserved']
        transactional_count = row['transactional_count']
        
        # Determine relationship strength
        has_relationship = total_preserved >= 3  # Need at least 3 preserved emails
        
        # Calculate confidence based on email history
        if total_preserved >= 10:
            confidence = 'high'
        elif total_preserved >= 5:
            confidence = 'medium'
        elif total_preserved >= 3:
            confidence = 'low'
        else:
            confidence = 'none'
            has_relationship = False
        
        relationship_info = {
            'has_relationship': has_relationship,
            'total_preserved': total_preserved,
            'transactional_count': transactional_count,
            'first_email_date': row['first_email_date'],
            'last_email_date': row['last_email_date'],
            'example_reasons': row['example_reasons'],
            'confidence': confidence
        }
        
        # Cache result for performance
        self._domain_cache[sender_domain] = relationship_info
        
        return has_relationship, relationship_info
    
    def classify_as_transactional(self, sender_email: str, subject: str, body: str) -> Optional[Dict]:
        """
        Check if email should be classified as transactional based on vendor relationship.
        
        Returns:
            None if not transactional, or classification dict if transactional
        """
        # Extract domain from sender email
        sender_domain = self._extract_domain(sender_email)
        if not sender_domain:
            return None
        
        # Check for existing vendor relationship
        has_relationship, relationship_info = self.has_vendor_relationship(sender_email, sender_domain)
        
        if not has_relationship:
            return None
        
        # Check if email looks like a digest/notification/subscription
        if self._is_digest_or_notification(subject, body):
            confidence = self._calculate_transactional_confidence(relationship_info, subject, body)
            
            return {
                'category': 'Transactional Email',
                'is_spam': False,
                'confidence': confidence,
                'confidence_level': self._get_confidence_level(confidence),
                'method': 'vendor_relationship',
                'reasoning': [
                    f"Existing vendor relationship with {sender_domain}",
                    f"Domain has {relationship_info['total_preserved']} preserved emails",
                    f"Email appears to be digest/notification",
                    f"Relationship confidence: {relationship_info['confidence']}"
                ],
                'relationship_info': relationship_info
            }
        
        return None
    
    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if '@' not in email:
            return None
        return email.split('@')[-1].lower()
    
    def _is_digest_or_notification(self, subject: str, body: str) -> bool:
        """
        Check if email looks like a digest, notification, or subscription.
        
        KISS patterns based on common transactional email characteristics.
        Enhanced to catch forum summaries and community digests.
        """
        subject_lower = subject.lower()
        body_lower = body.lower() if body else ""
        
        # Forum/Community digest patterns (high confidence)
        forum_patterns = [
            'forum', 'community forum', 'forum summary', 'community summary',
            'community digest', 'forum digest', 'discussion summary'
        ]
        
        # General digest patterns 
        digest_patterns = [
            'summary', 'digest', 'weekly', 'monthly', 'newsletter',
            'notification', 'alert', 'update', 'report', 'activity', 
            'news', 'bulletin', 'roundup'
        ]
        
        # Transactional patterns (orders, support, etc.)
        transactional_patterns = [
            'order', 'shipment', 'receipt', 'invoice', 'confirmation',
            'ticket', 'support', 'account', 'billing', 'payment',
            'subscription', 'renewal', 'expir'
        ]
        
        # Check subject for forum patterns first (high confidence)
        for pattern in forum_patterns:
            if pattern in subject_lower:
                return True
        
        # Check subject for other patterns
        for pattern in digest_patterns + transactional_patterns:
            if pattern in subject_lower:
                return True
        
        # Check for typical digest/notification body patterns
        notification_body_patterns = [
            'unsubscribe', 'notification settings', 'preferences',
            'here is your', 'here are your', 'recent activity',
            'weekly summary', 'monthly report', 'digest',
            'recent posts', 'new posts', 'community activity'
        ]
        
        for pattern in notification_body_patterns:
            if pattern in body_lower:
                return True
        
        # Special check for square bracket patterns [Something] which are common in forum digests
        if re.search(r'\[.*\].*summary', subject_lower) or re.search(r'\[.*forum.*\]', subject_lower):
            return True
        
        return False
    
    def _calculate_transactional_confidence(self, relationship_info: Dict, subject: str, body: str) -> float:
        """Calculate confidence score for transactional classification"""
        base_confidence = 60.0  # Base confidence for vendor relationship
        
        # Boost confidence based on relationship strength
        if relationship_info['confidence'] == 'high':
            base_confidence += 20.0
        elif relationship_info['confidence'] == 'medium':
            base_confidence += 10.0
        
        # Boost confidence for strong transactional patterns
        subject_lower = subject.lower()
        if any(pattern in subject_lower for pattern in ['order', 'shipment', 'receipt', 'invoice']):
            base_confidence += 15.0
        elif any(pattern in subject_lower for pattern in ['summary', 'digest', 'notification']):
            base_confidence += 10.0
        
        # Boost confidence if we have historical transactional emails from this domain
        if relationship_info['transactional_count'] > 0:
            base_confidence += 10.0
        
        return min(base_confidence, 95.0)  # Cap at 95%
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level"""
        if confidence >= 80:
            return 'HIGH'
        elif confidence >= 60:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def clear_cache(self):
        """Clear the domain relationship cache"""
        self._domain_cache.clear()
    
    def get_relationship_summary(self, sender_domain: str) -> Dict:
        """Get detailed relationship summary for a domain"""
        has_relationship, relationship_info = self.has_vendor_relationship("test@" + sender_domain, sender_domain)
        
        if has_relationship:
            # Get sample preserved emails from this domain
            sample_query = """
                SELECT sender_email, subject, category, reason, timestamp
                FROM processed_emails_bulletproof 
                WHERE sender_domain = ? 
                AND action = 'PRESERVED'
                ORDER BY timestamp DESC
                LIMIT 5
            """
            
            samples = self.db.execute_query(sample_query, (sender_domain,))
            relationship_info['sample_emails'] = [dict(row) for row in samples]
        
        return relationship_info


# Global instance for use in ensemble classifier
vendor_detector = VendorRelationshipDetector()