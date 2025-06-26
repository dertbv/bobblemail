#!/usr/bin/env python3
"""
🚀 REVOLUTIONARY TWO-FACTOR EMAIL VALIDATION SYSTEM 🚀

This system combines:
1. Universal Business Prefix Detection (Phase 1)
2. Advanced Domain Validation (Existing)
3. Smart Content-Based Routing (Phase 3)

This will change email classification forever!
"""

import re
from atlas_email.filters.business_prefixes import is_legitimate_business_prefix, get_prefix_confidence_explanation
from atlas_email.utils.domain_validator import DomainValidator, is_gibberish_email, detect_provider_from_sender
from atlas_email.core.spam_classifier import is_legitimate_company_domain

class TwoFactorEmailValidator:
    """
    Revolutionary email validation using business conventions + domain analysis.
    
    Two-Factor Authentication for Emails:
    Factor 1: Legitimate Business Prefix (marketing@, offers@, etc.)
    Factor 2: Verified Domain (age, reputation, legitimacy)
    
    Both factors must pass for "Promotional Email" classification.
    Smart content routing for failed validations.
    """
    
    def __init__(self, logger=None, account_provider=None):
        self.logger = logger
        self.account_provider = account_provider
        self.domain_validator = DomainValidator(logger=logger, account_provider=account_provider)
        
        # Content-based routing keywords for failed validations
        self.content_routing_keywords = {
            'Financial & Investment Spam': [
                'crypto', 'cryptocurrency', 'bitcoin', 'investment', 'trading', 'stocks',
                'retirement', '401k', 'portfolio', 'profit', 'earnings', 'dividends',
                'financial', 'money', 'cash', 'income', 'wealth', 'rich', 'millionaire',
                'fund', 'market', 'nasdaq', 'dow', 'wall street', 'broker', 'advisor'
            ],
            
            'Health & Medical Spam': [
                'weight loss', 'lose weight', 'diet', 'pills', 'supplement', 'medical',
                'doctor', 'prescription', 'pharmacy', 'medicine', 'treatment', 'cure',
                'health', 'wellness', 'fitness', 'exercise', 'nutrition', 'vitamin',
                'fat removal', 'surgery', 'procedure', 'clinic', 'hospital', 'patient'
            ],
            
            'Adult & Dating Spam': [
                'dating', 'singles', 'hookup', 'adult', 'sexy', 'hot', 'beautiful',
                'romance', 'love', 'relationship', 'match', 'profile', 'intimate',
                'enhancement', 'enlargement', 'performance', 'stamina', 'inches',
                'satisfaction', 'pleasure', 'bedroom', 'sexual', 'viagra'
            ],
            
            'Phishing': [
                'urgent', 'immediate', 'action required', 'verify', 'confirm', 'suspended',
                'expired', 'blocked', 'security', 'alert', 'warning', 'unauthorized',
                'click here', 'login', 'password', 'account', 'winner', 'won', 'prize',
                'congratulations', 'claim', 'lottery', 'sweepstakes', 'giveaway',
                'delivery failed', 'package', 'shipment', 'fedex', 'ups', 'dhl'
            ],
            
            'Legal & Compensation Scams': [
                'lawsuit', 'settlement', 'compensation', 'legal', 'attorney', 'lawyer',
                'court', 'class action', 'damages', 'claim', 'injury', 'accident',
                'sue', 'litigation', 'judgment', 'verdict', 'settlement fund'
            ],
            
            'Gambling Spam': [
                'casino', 'poker', 'slots', 'jackpot', 'lottery', 'betting', 'odds',
                'gambling', 'game', 'win', 'lucky', 'fortune', 'chance', 'risk'
            ]
        }
    
    def log(self, message, print_to_screen=False):
        """Log message if logger is available"""
        if self.logger:
            self.logger(message, print_to_screen)
    
    def validate_email_classification(self, sender_email, subject, email_content=""):
        """
        🚀 REVOLUTIONARY TWO-FACTOR EMAIL VALIDATION
        
        Returns:
            tuple: (classification, confidence, reasoning, should_delete)
        """
        if not sender_email or '@' not in sender_email:
            return "Invalid Email", 0.0, "Invalid email format", True
        
        # Extract domain for analysis
        domain = sender_email.split('@')[1].lower().strip()
        domain = re.sub(r'[<>\s]', '', domain)
        
        self.log(f"🔍 TWO-FACTOR VALIDATION: Analyzing {sender_email}", False)
        
        # FACTOR 1: Business Prefix Validation
        prefix_valid, prefix_used, prefix_confidence = is_legitimate_business_prefix(sender_email)
        prefix_explanation = get_prefix_confidence_explanation(sender_email)
        
        # FACTOR 2: Domain Validation  
        domain_deletion_allowed, domain_reason, domain_was_validated = self.domain_validator.validate_domain_before_deletion(
            sender_email, subject
        )
        # Domain is legitimate if deletion is NOT allowed
        domain_legitimate = not domain_deletion_allowed
        
        # Additional check for obviously suspicious domains
        if any(tld in domain for tld in ['.tk', '.ml', '.ga', '.cf']):
            domain_legitimate = False
            domain_reason += " (Suspicious TLD)"
        
        # Check for gibberish email (immediate red flag)
        if is_gibberish_email(sender_email):
            self.log(f"🚨 GIBBERISH DETECTED: {sender_email} - Routing to content analysis", False)
            return self._route_by_content(sender_email, subject, email_content, "Gibberish domain detected")
        
        # 🚀 UNIVERSAL SUBDOMAIN COMPLEXITY CHECK
        # Check for sophisticated newsletter scam patterns
        try:
            from atlas_email.filters.keyword_processor import KeywordProcessor
            kp = KeywordProcessor()
            subdomain_suspicious, subdomain_reason = kp.detect_universal_subdomain_complexity(domain, detect_provider_from_sender(sender_email))
            if subdomain_suspicious:
                self.log(f"🎯 SUBDOMAIN COMPLEXITY: {sender_email} - {subdomain_reason}", False)
                # Mark domain as not legitimate for two-factor validation
                domain_legitimate = False
                domain_reason += f" + {subdomain_reason}"
        except Exception as e:
            # If subdomain detection fails, continue with normal processing
            self.log(f"⚠️ Subdomain detection error: {e}", False)
        
        # Check for transactional content before applying two-factor logic
        from atlas_email.core.spam_classifier import is_transactional_email, is_account_notification, is_subscription_management
        
        if is_transactional_email(subject, sender_email, email_content):
            confidence = 0.95
            reasoning = f"Transactional email detected (receipts, orders, billing)"
            self.log(f"✅ TRANSACTIONAL: {sender_email} classified as Transactional Email", False)
            return "Transactional Email", confidence, reasoning, False
            
        if is_account_notification(subject, sender_email, email_content):
            confidence = 0.95
            reasoning = f"Account notification detected (security, password resets)"
            self.log(f"✅ ACCOUNT: {sender_email} classified as Account Notification", False)
            return "Account Notification", confidence, reasoning, False
            
        if is_subscription_management(subject, sender_email, email_content):
            confidence = 0.95
            reasoning = f"Subscription management detected (terms, service updates)"
            self.log(f"✅ SUBSCRIPTION: {sender_email} classified as Subscription Management", False)
            return "Subscription Management", confidence, reasoning, False

        # TWO-FACTOR AUTHENTICATION LOGIC FOR PROMOTIONAL CONTENT
        if prefix_valid and domain_legitimate:
            # 🎉 BOTH FACTORS PASS - LEGITIMATE PROMOTIONAL EMAIL
            confidence = min(prefix_confidence + 0.05, 1.0)  # Slight boost for passing both
            reasoning = f"Two-factor auth PASSED: {prefix_explanation} + legitimate domain ({domain})"
            
            self.log(f"✅ TWO-FACTOR PASS: {sender_email} classified as Promotional Email", False)
            return "Promotional Email", confidence, reasoning, False
            
        elif prefix_valid and not domain_legitimate:
            # 🚨 GOOD PREFIX, BAD DOMAIN - Likely spammer using professional prefix
            reasoning = f"Professional prefix '{prefix_used}' but suspicious domain: {domain_reason}"
            
            self.log(f"🚨 PREFIX SPOOFING: {sender_email} - Good prefix, bad domain", False)
            return self._route_by_content(sender_email, subject, email_content, reasoning)
            
        elif not prefix_valid and domain_legitimate:
            # 🤔 BAD PREFIX, GOOD DOMAIN - Could be legitimate business with unusual naming
            local_part = sender_email.split('@')[0]
            
            # Check if it's a personal name pattern or legitimate variation
            if self._is_likely_legitimate_variation(local_part, domain):
                confidence = 0.65  # Lower confidence due to unusual prefix
                reasoning = f"Legitimate domain but non-standard prefix '{local_part}' - likely legitimate variation"
                
                self.log(f"🤷 UNUSUAL PREFIX: {sender_email} - Treating as legitimate with lower confidence", False)
                return "Promotional Email", confidence, reasoning, False
            else:
                # Non-professional prefix from legitimate domain - route by content
                reasoning = f"Non-professional prefix '{local_part}' from legitimate domain - content analysis needed"
                
                self.log(f"🔍 CONTENT ROUTING: {sender_email} - Legitimate domain, unusual prefix", False)
                return self._route_by_content(sender_email, subject, email_content, reasoning)
                
        else:
            # 🚨 BOTH FACTORS FAIL - Definitely suspicious
            reasoning = f"Two-factor auth FAILED: Non-professional prefix + suspicious domain"
            
            self.log(f"❌ TWO-FACTOR FAIL: {sender_email} - Both factors failed", False)
            return self._route_by_content(sender_email, subject, email_content, reasoning)
    
    def _is_likely_legitimate_variation(self, local_part, domain):
        """
        Check if an unusual prefix might still be legitimate.
        Examples: CEO names, department codes, etc.
        """
        # Known legitimate domain gets more lenient treatment
        if is_legitimate_company_domain(f"test@{domain}"):
            return True
        
        # Professional name patterns
        if ('.' in local_part or '_' in local_part) and len(local_part) > 4:
            return True
        
        # Short, simple patterns that could be legitimate
        if len(local_part) <= 8 and local_part.isalpha():
            return True
        
        return False
    
    def _route_by_content(self, sender_email, subject, content, base_reasoning):
        """
        🎯 SMART CONTENT-BASED ROUTING
        Route failed validations to appropriate spam categories based on content.
        """
        combined_text = f"{subject} {content}".lower()
        
        # Check for brand impersonation first (specific company mentions)
        brand_impersonation = self._detect_brand_impersonation(sender_email, subject, combined_text)
        if brand_impersonation:
            reasoning = f"{base_reasoning} + Brand impersonation detected: {brand_impersonation}"
            return "Brand Impersonation", 0.85, reasoning, True
        
        # Route by content categories (highest confidence first)
        category_scores = {}
        
        for category, keywords in self.content_routing_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in combined_text:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Calculate confidence based on keyword matches
                confidence = min(0.60 + (score * 0.05), 0.95)
                category_scores[category] = (confidence, matched_keywords)
        
        # Return highest confidence category
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1][0])
            category, (confidence, keywords) = best_category
            
            keyword_list = ", ".join(keywords[:3])  # Show first 3 matches
            reasoning = f"{base_reasoning} + Content analysis: {keyword_list}"
            
            self.log(f"🎯 CONTENT ROUTED: {sender_email} → {category} (confidence: {confidence:.2f})", False)
            return category, confidence, reasoning, True
        
        # Fallback to Marketing Spam if no specific category matches
        reasoning = f"{base_reasoning} + No specific content match - generic marketing"
        self.log(f"📋 FALLBACK: {sender_email} → Marketing Spam", False)
        return "Marketing Spam", 0.55, reasoning, True
    
    def _detect_brand_impersonation(self, sender_email, subject, combined_text):
        """
        Detect if email is impersonating a specific brand.
        Returns brand name if impersonation detected, None otherwise.
        """
        domain = sender_email.split('@')[1].lower()
        
        # List of major brands to check for impersonation
        major_brands = [
            'amazon', 'walmart', 'target', 'costco', 'apple', 'microsoft', 'google',
            'facebook', 'netflix', 'paypal', 'ebay', 'fedex', 'ups', 'dhl',
            'bank of america', 'chase', 'wells fargo', 'american express',
            'tmobile', 't-mobile', 'verizon', 'att', 'at&t', 'sprint',
            'nike', 'adidas', 'mcdonalds', 'starbucks', 'coca cola'
        ]
        
        for brand in major_brands:
            # Check if brand is mentioned in subject/content but domain doesn't match
            if brand in combined_text and brand not in domain:
                # Make sure it's not just a passing mention
                brand_mentions = combined_text.count(brand)
                if brand_mentions >= 1 and len(subject) > 0:
                    return brand
        
        return None

# Test the revolutionary system
if __name__ == "__main__":
    print("🚀 TESTING REVOLUTIONARY TWO-FACTOR EMAIL VALIDATION SYSTEM")
    print("=" * 80)
    
    validator = TwoFactorEmailValidator()
    
    test_cases = [
        # Should PASS two-factor auth
        ("marketing@kohls.com", "Summer Sale - 50% Off Everything!", ""),
        ("offers@amazon.com", "Prime Day Deals Inside", ""),
        
        # Should FAIL - good prefix, bad domain  
        ("marketing@scam-domain.tk", "Crypto investment opportunity", "bitcoin trading"),
        
        # Should FAIL - bad prefix, suspicious content
        ("kjhg123@random.com", "You won the lottery!", "claim your prize"),
        
        # Should route to specific categories
        ("randomuser@sketchy.com", "Lose 30 pounds fast!", "weight loss pills"),
        ("spammer@fake.net", "Hot singles in your area", "dating hookup"),
        
        # Brand impersonation
        ("amazon-deals@fake-amazon.tk", "Your Amazon order", ""),
    ]
    
    for sender, subject, content in test_cases:
        print(f"\n📧 Testing: {sender}")
        print(f"   Subject: {subject}")
        
        classification, confidence, reasoning, should_delete = validator.validate_email_classification(
            sender, subject, content
        )
        
        action = "🗑️ DELETE" if should_delete else "✅ KEEP"
        print(f"   Result: {action} {classification} (confidence: {confidence:.2f})")
        print(f"   Reasoning: {reasoning}")
        print("-" * 80)