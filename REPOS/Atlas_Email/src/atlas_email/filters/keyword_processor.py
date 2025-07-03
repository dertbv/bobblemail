"""
🚀 REVOLUTIONARY KEYWORD PROCESSOR WITH TWO-FACTOR VALIDATION 🚀

This module provides breakthrough email classification combining:
- Traditional keyword-based detection
- Revolutionary two-factor validation (business prefix + domain)
- Smart content-based routing
- Enhanced brand impersonation detection

This system will change email filtering forever!
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Union
from atlas_email.core.classification_utils import (
    check_all_keywords, check_keywords_simple, is_authenticated_domain,
    get_all_keywords_for_category, is_community_email, is_transactional_email,
    is_account_notification, is_subscription_management, classify_encoded_spam_content
)
from atlas_email.utils.domain_validator import detect_provider_from_sender

# Import revolutionary two-factor validation system
try:
    from atlas_email.core.two_factor_validator import TwoFactorEmailValidator
    TWO_FACTOR_AVAILABLE = True
    print("🚀 Revolutionary Two-Factor Email Validation System LOADED in KeywordProcessor!")
except ImportError:
    TWO_FACTOR_AVAILABLE = False
    print("⚠️ Two-Factor validation not available in KeywordProcessor - using fallback classification")

class KeywordProcessor:
    """
    Handles keyword-based spam classification with provider awareness and confidence scoring.
    
    Extracted from the monolithic classify_spam_type function to improve maintainability,
    testability, and enable better separation of concerns.
    """
    
    # Spam categories in PRIORITY order (highest priority first) - FIXED TO MATCH SPECIFICITY_ORDER
    SPAM_CATEGORIES = [
        'Phishing',             # HIGHEST PRIORITY - credential theft, prize scams, information gathering
        'Payment Scam',         # HIGH PRIORITY - fake invoices/bills
        'Adult & Dating Spam',   # Explicit content and dating scams
        'Health & Medical Spam',  # Health/medical products and treatments
        'Legal & Compensation Scams', # Legal settlements and compensation claims
        'Financial & Investment Spam',  # All money-related scams (loans, investments, trading)
        'Gambling Spam',        # Casino/lottery
        'Education/Training Spam', 'Real Estate Spam', 'Business Opportunity Spam',
        'Brand Impersonation',  # LOWER PRIORITY - only when content doesn't match more specific categories
        'Marketing Spam'        # LOWEST PRIORITY - general marketing/promotional content
    ]
    
    # Category specificity order for tie-breaking - MATCHES SPAM_CATEGORIES ORDER
    SPECIFICITY_ORDER = [
        'Phishing',             # HIGHEST PRIORITY - credential theft, prize scams, information gathering
        'Payment Scam',         # HIGH PRIORITY - fake invoices/bills
        'Adult & Dating Spam',   # Explicit content and dating scams
        'Health & Medical Spam',  # Health/medical products and treatments
        'Legal & Compensation Scams', # Legal settlements and compensation claims
        'Financial & Investment Spam',  # All money-related scams (loans, investments, trading)
        'Gambling Spam',        # Casino/lottery
        'Education/Training Spam', 'Real Estate Spam', 'Business Opportunity Spam',
        'Brand Impersonation',  # LOWER PRIORITY - only when content doesn't match more specific categories
        'Marketing Spam'        # LOWEST PRIORITY - general marketing/promotional content
    ]
    
    # Domain keywords now sourced from unified database (filter_terms table)
    # This ensures consistency between domain hints and content analysis
    # No more hard-coded domain lists - all keywords stored in database
    
    # Brand impersonation patterns
    BRAND_IMPERSONATION_PATTERNS = [
        "noreply-", "no-reply", "notification-", "alert-", "security-", "account-",
        "support-", "service-", "billing-", "invoice-", "payment-", "verify-",
        "update-", "confirm-", "suspend-", "warning-", "urgent-"
    ]
    
    # Top impersonated brands
    TOP_IMPERSONATED_BRANDS = [
        "amazon", "apple", "microsoft", "google", "facebook", "paypal", 
        "netflix", "bank", "chase", "wells fargo"
    ]
    
    # Suspicious TLDs for brand impersonation
    SUSPICIOUS_TLDS = [".tk", ".ml", ".ga", ".cf", ".us"]
    
    # Scam emojis for emoji spam detection
    SCAM_EMOJIS = [
        "💲", "💰", "💵", "💴", "💶", "💷", "🤑", "💳", "💎", "🎁", "🎉", "🎊",
        "🔥", "⚡", "✨", "🌟", "⭐", "🏆", "🎯", "🚀", "📈", "📊", "👑", "💯",
        "🎪", "🎭", "🎨", "🎬", "🎮", "🕹️", "🎲", "🃏", "🎰", "🎱", "🏅", "🥇"
    ]
    
    def __init__(self):
        """Initialize the keyword processor with emoji detection pattern, ML settings, and revolutionary two-factor validation."""
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002600-\U000027BF"  # misc symbols
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            "]+", flags=re.UNICODE
        )
        
        # Load category-specific thresholds
        self.category_thresholds = self._load_category_thresholds()
        
        # Store last classification confidence for reporting
        self.last_classification_confidence = 0.0
        
        # 🚀 REVOLUTIONARY FEATURE: Initialize two-factor email validator
        if TWO_FACTOR_AVAILABLE:
            self.two_factor_validator = TwoFactorEmailValidator()
            print("🎉 KeywordProcessor: Two-factor validation system initialized!")
        else:
            self.two_factor_validator = None
            print("⚠️ KeywordProcessor: Using fallback classification without two-factor validation")
    
    def _load_category_thresholds(self) -> Dict[str, float]:
        """Load category-specific confidence thresholds from centralized settings."""
        try:
            from config.settings import Settings
            return Settings.get_ml_settings().get('category_thresholds', {})
        except ImportError:
            # Fallback to JSON if settings.py not available
            try:
                import json
                with open('ml_settings.json', 'r') as f:
                    settings = json.load(f)
                return settings.get('category_thresholds', {})
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
    
    def get_category_threshold(self, category: str, default: float = 0.7) -> float:
        """Get confidence threshold for a specific category."""
        threshold = self.category_thresholds.get(category, default)
        # Handle both integer (75) and float (0.75) formats from config
        if isinstance(threshold, (int, float)) and threshold > 1.0:
            return threshold / 100.0  # Convert percentage to decimal
        return threshold
    
    def extract_domain_info(self, sender: str) -> Tuple[str, str]:
        """
        Extract domain and provider information from sender email.
        
        Args:
            sender: Email sender string
            
        Returns:
            Tuple of (domain, sender_provider)
        """
        sender_lower = str(sender).lower() if sender else ""
        domain = ""
        sender_provider = 'unknown'
        
        if "@" in sender_lower:
            domain = sender_lower.split("@")[-1].replace(">", "").strip()
            sender_provider = detect_provider_from_sender(sender_lower)
        elif "<" in sender_lower and ">" in sender_lower:
            # Handle format like: "Name <domain.com>" (without @)
            domain_part = sender_lower.split("<")[-1].replace(">", "").strip()
            if "." in domain_part:  # Basic domain validation
                domain = domain_part
                sender_provider = detect_provider_from_sender(sender_lower)
        
        return domain, sender_provider
    
    def is_suspicious_domain(self, domain: str, sender_provider: str) -> bool:
        """
        Check if domain appears suspicious based on various patterns.
        
        Args:
            domain: Domain to check
            sender_provider: Email provider type
            
        Returns:
            True if domain appears suspicious
        """
        if is_authenticated_domain(domain):
            return False
            
        suspicious = any([
            len(domain.split(".")[0]) > 15,
            domain.count(".") > 3,
            any(char.isdigit() for char in domain.replace(".", "")) and len(domain.split(".")[0]) > 10,
            domain.endswith(tuple(self.SUSPICIOUS_TLDS)) and sender_provider == 'unknown',
        ])
        
        # Provider-specific adjustments for classification
        if sender_provider in ['icloud', 'gmail', 'outlook']:
            # Major providers have better spam filtering, so suspicious emails are more likely false positives
            suspicious = suspicious and len(domain.split(".")[0]) > 20
            
        return suspicious
    
    def detect_universal_subdomain_complexity(self, domain: str, sender_provider: str) -> Tuple[bool, str]:
        """
        🚀 UNIVERSAL SUBDOMAIN COMPLEXITY DETECTION
        
        Detects sophisticated scam patterns using complex subdomains across ALL spam categories.
        This catches scammers using authority-claiming subdomains like:
        - insights.domain.com (newsletter scams)
        - strategies.domain.com (investment scams) 
        - portfolio.domain.com (financial scams)
        - daily.domain.com (news scams)
        - reports.domain.com (professional scams)
        
        Args:
            domain: Domain to analyze
            sender_provider: Email provider type
            
        Returns:
            Tuple of (is_complex_suspicious, reason)
        """
        if not domain or '.' not in domain:
            return False, "Invalid domain"
        
        domain_parts = domain.lower().split('.')
        
        # Need at least 3 parts for subdomain complexity (subdomain.domain.tld)
        if len(domain_parts) < 3:
            return False, "No subdomains detected"
        
        # Extract the subdomain (first part)
        subdomain = domain_parts[0]
        
        # Check for legitimate domains first - they can use complex subdomains
        # is_authenticated_domain already imported from classification_utils
        if is_authenticated_domain(domain):
            # Exception: Even legitimate domains with obvious scam patterns should be flagged
            main_domain = domain_parts[1] if len(domain_parts) >= 2 else ""
            
            # Check for obvious scam words in domain
            if any(scam_word in main_domain for scam_word in ['scam', 'fake', 'fraud', 'phish', 'spam']):
                # Continue with subdomain analysis even for "legitimate" domains with scam words
                pass
            # 🎯 ENHANCED: Check for newsletter scam domain patterns that use professional-sounding names
            elif any(scam_pattern in domain.lower() for scam_pattern in [
                'hints.com', 'strategies.com', 'research.com', 'rulebook.com',
                'mastery', 'insights', 'secrets', 'solutions', 'advisory',
                'capital', 'futures', 'economic', 'financial', 'investment'
            ]) and subdomain in ['daily', 'insights', 'strategies', 'portfolio', 'newsletter']:
                # These are likely newsletter scam domains using professional language to appear legitimate
                return True, f"Newsletter scam pattern: '{subdomain}' + professional-sounding domain"
            else:
                return False, "Legitimate company domain"
        
        # 🎯 SUSPICIOUS NEWSLETTER/AUTHORITY SUBDOMAIN PATTERNS
        suspicious_newsletter_patterns = [
            # Newsletter/Content patterns
            'insights', 'strategies', 'portfolio', 'daily', 'weekly', 'monthly',
            'reports', 'analysis', 'research', 'data', 'intelligence', 'updates',
            'newsletter', 'bulletins', 'digest', 'briefing', 'summary',
            
            # Authority/Professional patterns  
            'expert', 'professional', 'premium', 'exclusive', 'insider',
            'official', 'verified', 'certified', 'authorized', 'trusted',
            'secure', 'private', 'confidential', 'members', 'vip',
            
            # Financial/Investment patterns
            'trading', 'invest', 'wealth', 'money', 'profit', 'earnings',
            'finance', 'market', 'stocks', 'crypto', 'forex', 'funds',
            
            # Health/Medical patterns
            'health', 'medical', 'wellness', 'fitness', 'nutrition', 'diet',
            'treatment', 'cure', 'therapy', 'supplements', 'pharmacy',
            
            # Technology/Service patterns
            'tech', 'digital', 'online', 'platform', 'service', 'solutions',
            'systems', 'software', 'apps', 'tools', 'resources'
        ]
        
        # Check if subdomain matches suspicious patterns
        for pattern in suspicious_newsletter_patterns:
            if pattern in subdomain:
                # Additional validation - check domain structure
                main_domain = domain_parts[1] if len(domain_parts) >= 2 else ""
                
                # More suspicious if main domain is also generic/random
                if len(main_domain) > 8 and any(char.isdigit() for char in main_domain):
                    return True, f"Suspicious newsletter subdomain '{subdomain}' + random main domain"
                
                # More suspicious if using suspicious TLDs
                tld = domain_parts[-1]
                if tld in ['tk', 'ml', 'ga', 'cf', 'us', 'info', 'biz']:
                    return True, f"Suspicious newsletter subdomain '{subdomain}' + suspicious TLD"
                
                # More suspicious if combined with unknown email provider
                if sender_provider == 'unknown':
                    return True, f"Suspicious newsletter subdomain '{subdomain}' from unknown provider"
                
                # Flag as moderately suspicious for professional review
                return True, f"Newsletter subdomain pattern '{subdomain}' detected"
        
        # 🔍 COMPLEX SUBDOMAIN STRUCTURE ANALYSIS
        # Multiple subdomains with random patterns
        if len(domain_parts) > 3:
            # Check for chains like: mail.newsletter.random123.com
            complex_chain = True
            for part in domain_parts[:-2]:  # Exclude main domain and TLD
                if len(part) > 8 or any(char.isdigit() for char in part):
                    return True, f"Complex subdomain chain with random elements: {'.'.join(domain_parts[:-1])}"
        
        # Long subdomain names (often random/generated)
        if len(subdomain) > 12:
            return True, f"Unusually long subdomain '{subdomain}' may indicate generated domain"
        
        # Mixed alphanumeric patterns in subdomain
        if re.search(r'[0-9]+[a-z]+[0-9]+|[a-z]+[0-9]{3,}', subdomain):
            return True, f"Random alphanumeric pattern in subdomain '{subdomain}'"
        
        return False, "No suspicious subdomain patterns detected"
    
    def analyze_display_name_complexity(self, sender: str) -> Tuple[bool, str, float]:
        """
        🚨 SOPHISTICATED DISPLAY NAME ANALYSIS
        
        Detects spam patterns in sender display names including:
        - Overly complex multi-word display names (5+ words suspicious, 7+ high risk)
        - News hook patterns ("Breaking", "Just Hit", "URGENT")
        - Authority claiming patterns ("Expert", "from [ORG]", titles)
        - Multi-component structures (news + person + organization)
        - Emoji abuse and suspicious character patterns
        
        Args:
            sender: Full sender string including display name
            
        Returns:
            Tuple of (is_suspicious, reason, suspicion_score)
        """
        if not sender:
            return False, "No sender provided", 0.0
        
        # Extract display name from sender
        display_name = ""
        if '"' in sender and '<' in sender:
            # Format: "Display Name" <email@domain.com>
            try:
                display_name = sender.split('"')[1].strip()
            except IndexError:
                display_name = ""
        elif '<' in sender and '>' in sender:
            # Format: Display Name <email@domain.com>
            try:
                display_name = sender.split('<')[0].strip()
            except IndexError:
                display_name = ""
        else:
            # Just email address, no display name
            return False, "No display name found", 0.0
        
        if not display_name or len(display_name.strip()) == 0:
            return False, "Empty display name", 0.0
        
        suspicion_score = 0.0
        suspicious_patterns = []
        
        # 🎯 WORD COUNT ANALYSIS
        words = display_name.split()
        word_count = len(words)
        
        if word_count >= 7:
            suspicion_score += 0.8  # Very high suspicion for 7+ words
            suspicious_patterns.append(f"{word_count} words (overly complex)")
        elif word_count >= 5:
            suspicion_score += 0.5  # Moderate suspicion for 5-6 words
            suspicious_patterns.append(f"{word_count} words (complex)")
        elif word_count >= 8:
            suspicion_score += 1.0  # Maximum suspicion for 8+ words
            suspicious_patterns.append(f"{word_count} words (extremely complex)")
        
        # 🚨 NEWS HOOK PATTERNS
        news_hooks = [
            'breaking', 'urgent', 'alert', 'just hit', 'just in', 'live',
            'exclusive', 'leaked', 'exposed', 'caught', 'shocking',
            'stunning', 'horrifying', 'devastating', 'massive', 'huge',
            'bombshell', 'developing', 'update', 'latest', 'new'
        ]
        
        display_lower = display_name.lower()
        for hook in news_hooks:
            if hook in display_lower:
                suspicion_score += 0.3
                suspicious_patterns.append(f"news hook: '{hook}'")
        
        # 👨‍💼 AUTHORITY CLAIMING PATTERNS
        authority_patterns = [
            'expert', 'specialist', 'advisor', 'consultant', 'analyst',
            'director', 'manager', 'ceo', 'president', 'founder',
            'dr.', 'doctor', 'professor', 'phd', 'md',
            'from', 'at', 'with', '|', '||', '•', 'team',
            'official', 'verified', 'certified', 'licensed'
        ]
        
        for pattern in authority_patterns:
            if pattern in display_lower:
                suspicion_score += 0.2
                suspicious_patterns.append(f"authority claim: '{pattern}'")
        
        # 🏢 MULTI-COMPONENT STRUCTURE ANALYSIS
        # Check for multiple distinct components (person + org + news)
        has_person_name = any(word.istitle() and len(word) > 2 for word in words)
        has_organization = any(word.isupper() and len(word) >= 2 for word in words)
        has_news_content = any(hook in display_lower for hook in news_hooks)
        
        component_count = sum([has_person_name, has_organization, has_news_content])
        if component_count >= 3:
            suspicion_score += 0.6
            suspicious_patterns.append("multi-component (news+person+org)")
        elif component_count == 2:
            suspicion_score += 0.3
            suspicious_patterns.append("dual-component structure")
        
        # 😀 EMOJI ABUSE DETECTION
        emoji_count = len(self.emoji_pattern.findall(display_name))
        if emoji_count >= 3:
            suspicion_score += 0.4
            suspicious_patterns.append(f"{emoji_count} emojis (abuse)")
        elif emoji_count >= 1:
            suspicion_score += 0.1
            suspicious_patterns.append(f"{emoji_count} emoji(s)")
        
        # 🔢 SUSPICIOUS CHARACTER PATTERNS
        special_chars = ['|', '||', '•', '★', '►', '▶', '→', '⇒', '>>']
        special_count = sum(display_name.count(char) for char in special_chars)
        if special_count >= 2:
            suspicion_score += 0.3
            suspicious_patterns.append("multiple special separators")
        
        # 📏 LENGTH ANALYSIS
        if len(display_name) > 50:
            suspicion_score += 0.2
            suspicious_patterns.append("excessive length")
        
        # 🔠 CASE PATTERN ANALYSIS
        all_caps_words = [word for word in words if word.isupper() and len(word) > 1]
        if len(all_caps_words) >= 2:
            suspicion_score += 0.2
            suspicious_patterns.append("multiple ALL CAPS words")
        
        # 🎯 FINANCIAL NEWSLETTER PATTERNS (specific to this spam type)
        financial_newsletter_patterns = [
            'trader', 'investment', 'profit', 'wealth', 'money', 'cash',
            'market', 'stock', 'crypto', 'finance', 'trading', 'fund',
            'intelligence', 'insights', 'reports', 'alerts', 'analysis'
        ]
        
        financial_matches = [pattern for pattern in financial_newsletter_patterns if pattern in display_lower]
        if financial_matches:
            suspicion_score += 0.3 * len(financial_matches)
            suspicious_patterns.append(f"financial terms: {financial_matches}")
        
        # 🏛️ LEGITIMATE ORGANIZATION EXCEPTIONS
        # Check for known legitimate patterns that might trigger false positives
        legitimate_exceptions = [
            # Financial institutions using "alerts" - legitimate
            (lambda: 'alert' in display_lower and word_count <= 3 and 
             any(bank in sender.lower() for bank in ['chase', 'bank', 'wells', 'citi', 'amex', 'discover'])),
            
            # News organizations with "breaking" or "news" - legitimate if from known domains
            (lambda: any(news_word in display_lower for news_word in ['breaking', 'news']) and word_count <= 4 and
             any(news_domain in sender.lower() for news_domain in ['cnn', 'bbc', 'reuters', 'ap.org', 'nytimes', 'wsj', 'bloomberg'])),
            
            # Professional titles with 2 words or less - legitimate
            (lambda: any(title in display_lower for title in ['dr.', 'doctor', 'professor']) and word_count <= 2),
        ]
        
        # Check if this matches any legitimate exception
        is_legitimate_exception = any(exception() for exception in legitimate_exceptions if callable(exception))
        
        if is_legitimate_exception:
            # Reduce suspicion significantly for legitimate exceptions
            suspicion_score *= 0.3  # Reduce to 30% of original score
            suspicious_patterns.append("(reduced - legitimate exception)")
        
        # 🚩 FINAL ASSESSMENT
        is_suspicious = suspicion_score >= 0.5  # Threshold for suspicion
        
        if suspicious_patterns:
            reason = f"Suspicious display name: {', '.join(suspicious_patterns)}"
        else:
            reason = "Display name appears normal"
        
        # Cap suspicion score at 1.0
        suspicion_score = min(suspicion_score, 1.0)
        
        return is_suspicious, reason, suspicion_score
    
    def analyze_display_name_categories(self, sender: str) -> Dict[str, float]:
        """
        🎯 DISPLAY NAME CATEGORY ANALYSIS
        
        Runs category keyword detection on the display name itself to identify
        what type of spam might be indicated by the sender's chosen display name.
        
        Args:
            sender: Full sender string including display name
            
        Returns:
            Dictionary of {category: confidence} for matching categories
        """
        if not sender:
            return {}
        
        # Extract display name from sender (same logic as complexity analysis)
        display_name = ""
        if '"' in sender and '<' in sender:
            # Format: "Display Name" <email@domain.com>
            try:
                display_name = sender.split('"')[1].strip()
            except IndexError:
                display_name = ""
        elif '<' in sender and '>' in sender:
            # Format: Display Name <email@domain.com>
            try:
                display_name = sender.split('<')[0].strip()
            except IndexError:
                display_name = ""
        else:
            # Just email address, no display name
            return {}
        
        if not display_name or len(display_name.strip()) == 0:
            return {}
        
        # Run category keyword detection on display name
        display_text = display_name.lower()
        category_matches = {}
        
        for category in self.SPAM_CATEGORIES:
            found_keyword, confidence = check_all_keywords(display_text, category)
            if found_keyword and confidence > 0.1:  # Lower threshold for display names
                category_matches[category] = confidence
        
        return category_matches
    
    def check_encoded_spam(self, subject: str, sender: str) -> bool:
        """
        Check for encoded spam patterns.
        
        Args:
            subject: Email subject
            sender: Email sender
            
        Returns:
            True if encoded spam detected
        """
        return any([
            "=?UTF-8?" in str(subject),
            "����" in str(sender),
            len(str(subject)) > 200
        ])
    
    def find_best_category_match(self, all_text: str, confidence_threshold: float = 0.5, display_categories: Dict[str, float] = None) -> Optional[str]:
        """
        ENHANCED: Find the best matching spam category with improved precedence logic.
        
        Key improvements:
        - Universal Spam Indicators integration for generic promotional terms
        - Specificity-based keyword weighting (longer keywords = more specific)
        - Enhanced category precedence with separate generic spam detection
        
        Args:
            all_text: Combined text from subject and headers
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Best matching category name or None
        """
        category_matches = []
        
        # ENHANCEMENT 1: Check Universal Spam Indicators for basic spam detection
        universal_match, universal_confidence = check_all_keywords(all_text, "Universal Spam Indicators")
        
        # ENHANCEMENT 2: Check all specific categories with enhanced scoring
        for category in self.SPAM_CATEGORIES:
            found_keyword, confidence = check_all_keywords(all_text, category)
            
            # 🎯 ENHANCEMENT: Boost confidence if display name also matches this category
            if display_categories and category in display_categories:
                display_confidence = display_categories[category]
                # Combine content and display name confidence (weighted average)
                combined_confidence = (confidence * 0.7) + (display_confidence * 0.3)
                print(f"   🎯 CATEGORY BOOST: {category} content:{confidence:.3f} + display:{display_confidence:.3f} = {combined_confidence:.3f}")
                confidence = combined_confidence
            
            # Use category-specific threshold if available
            category_threshold = self.get_category_threshold(category, confidence_threshold)
            if found_keyword and confidence >= category_threshold:
                # ENHANCEMENT 3: Calculate specificity score for better precedence
                specificity_score = self._calculate_specificity_score(all_text, category, confidence)
                category_matches.append((category, confidence, specificity_score))
        
        # ENHANCEMENT 4: Handle Universal Spam Indicators fallback
        if not category_matches and universal_match and universal_confidence >= 0.3:
            # Generic promotional content detected but no specific category - classify as Marketing Spam
            return "Marketing Spam"
        
        if not category_matches:
            return None
            
        # PRIORITY FIX: Use strict category priority order instead of complex specificity scoring
        # This ensures that Phishing always beats Brand Impersonation, etc.
        
        # Create a dictionary of category matches for quick lookup
        matched_categories = {match[0]: (match[1], match[2]) for match in category_matches}
        
        # Return the first matching category in priority order (SPECIFICITY_ORDER)
        for priority_category in self.SPECIFICITY_ORDER:
            if priority_category in matched_categories:
                return priority_category
        
        # Fallback: return highest confidence category if none found in priority order
        category_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)  # Sort by confidence, then specificity
        return category_matches[0][0]
    
    def get_ranked_classifications(self, all_text: str, sender: str = "", confidence_threshold: float = 0.3, limit: int = 5) -> List[Tuple[str, float, float]]:
        """
        ALTERNATIVE RANKING SYSTEM: Get ranked alternative classifications for an email.
        
        This method provides a list of possible classifications ranked by likelihood,
        enabling the thumbs down feedback system to cycle through logical alternatives.
        
        Args:
            all_text: Combined text from subject and headers
            sender: Email sender for additional context
            confidence_threshold: Minimum confidence threshold for alternatives
            limit: Maximum number of alternatives to return
            
        Returns:
            List of (category, confidence, specificity_score) tuples, sorted by likelihood
        """
        category_matches = []
        
        # Check Universal Spam Indicators
        universal_match, universal_confidence = check_all_keywords(all_text, "Universal Spam Indicators")
        
        # Check all specific categories
        for category in self.SPAM_CATEGORIES:
            found_keyword, confidence = check_all_keywords(all_text, category)
            # Use category-specific threshold if available, but lower for alternatives
            category_threshold = max(self.get_category_threshold(category, confidence_threshold) * 0.7, 0.2)
            
            if found_keyword and confidence >= category_threshold:
                # Calculate specificity score for ranking
                specificity_score = self._calculate_specificity_score(all_text, category, confidence)
                category_matches.append((category, confidence, specificity_score))
        
        # Add Universal Spam fallback if applicable
        if universal_match and universal_confidence >= 0.2:
            # Calculate a basic specificity score for Marketing Spam
            marketing_specificity = universal_confidence + 0.1  # Base score for generic marketing
            category_matches.append(("Marketing Spam", universal_confidence, marketing_specificity))
        
        # Add domain and sender context-based alternatives
        if sender:
            domain, sender_provider = self.extract_domain_info(sender)
            
            # Check for domain-specific patterns
            domain_category = self.check_domain_patterns(domain, sender_provider)
            if domain_category:
                # Add domain-based classification as an alternative
                domain_confidence = 0.6  # Moderate confidence for domain-based detection
                domain_specificity = self._calculate_specificity_score(all_text, domain_category, domain_confidence)
                category_matches.append((domain_category, domain_confidence, domain_specificity))
            
            # Check for brand impersonation
            suspicious_domain = self.is_suspicious_domain(domain, sender_provider)
            brand_impersonation = self.check_brand_impersonation(sender, domain, sender_provider, suspicious_domain)
            if brand_impersonation:
                brand_confidence = 0.7  # Higher confidence for brand impersonation detection
                brand_specificity = self._calculate_specificity_score(all_text, brand_impersonation, brand_confidence)
                category_matches.append((brand_impersonation, brand_confidence, brand_specificity))
        
        # Remove duplicates while preserving the highest scores
        unique_matches = {}
        for category, confidence, specificity in category_matches:
            if category not in unique_matches or specificity > unique_matches[category][2]:
                unique_matches[category] = (category, confidence, specificity)
        
        # Convert back to list and sort by combined score
        final_matches = list(unique_matches.values())
        final_matches.sort(key=lambda x: (x[2], x[1]), reverse=True)
        
        # Add logical fallback categories if we don't have enough alternatives
        if len(final_matches) < limit:
            fallback_categories = [
                ("Marketing Spam", 0.4, 1.0),
                ("Promotional Email", 0.3, 0.8),
                ("Not Spam", 0.2, 0.5)
            ]
            
            for fallback_category, fallback_conf, fallback_spec in fallback_categories:
                if fallback_category not in unique_matches and len(final_matches) < limit:
                    final_matches.append((fallback_category, fallback_conf, fallback_spec))
        
        return final_matches[:limit]
    
    def _calculate_specificity_score(self, text: str, category: str, base_confidence: float) -> float:
        """
        Calculate specificity score for enhanced keyword precedence.
        
        Factors considered:
        - Keyword length (longer = more specific)
        - Category specificity weight
        - Number of category-specific matches
        - Base confidence score
        
        Args:
            text: Text being analyzed
            category: Category being scored
            base_confidence: Base confidence from keyword match
            
        Returns:
            Enhanced specificity score (0.0-10.0)
        """
        try:
            # get_all_keywords_for_category already imported from classification_utils
            
            # Get all keywords for this category
            all_keywords = get_all_keywords_for_category(category)
            text_lower = text.lower()
            
            # Calculate keyword-specific metrics
            matched_keywords = []
            total_keyword_length = 0
            max_keyword_length = 0
            
            for term, confidence in all_keywords:
                if term in text_lower:
                    matched_keywords.append((term, confidence))
                    keyword_length = len(term)
                    total_keyword_length += keyword_length
                    max_keyword_length = max(max_keyword_length, keyword_length)
            
            if not matched_keywords:
                return 0.0
            
            # FACTOR 1: Keyword length weight (longer keywords are more specific)
            avg_keyword_length = total_keyword_length / len(matched_keywords)
            length_weight = min(avg_keyword_length / 20.0, 2.0)  # Cap at 2.0
            
            # FACTOR 2: Category specificity weight (from SPECIFICITY_ORDER)
            try:
                category_position = self.SPECIFICITY_ORDER.index(category)
                category_weight = (len(self.SPECIFICITY_ORDER) - category_position) / len(self.SPECIFICITY_ORDER)
            except ValueError:
                category_weight = 0.5  # Default for categories not in specificity order
            
            # FACTOR 3: Number of matches weight (more matches = higher confidence)
            match_count_weight = min(len(matched_keywords) / 5.0, 1.5)  # Cap at 1.5
            
            # FACTOR 4: Maximum keyword length bonus (very specific terms get extra weight)
            max_length_bonus = min(max_keyword_length / 15.0, 1.0)  # Cap at 1.0
            
            # Calculate final specificity score
            specificity_score = (
                base_confidence +           # Base confidence (0.0-1.0)
                length_weight +            # Keyword length weight (0.0-2.0)
                category_weight +          # Category specificity weight (0.0-1.0)
                match_count_weight +       # Match count weight (0.0-1.5)
                max_length_bonus           # Max length bonus (0.0-1.0)
            )
            
            return min(specificity_score, 10.0)  # Cap total score at 10.0
            
        except Exception as e:
            # Fallback to base confidence if calculation fails
            return base_confidence
    
    def check_domain_patterns(self, domain: str, sender_provider: str) -> Optional[str]:
        """
        Check for spam patterns in domain names using unified database keywords.
        
        Args:
            domain: Domain to check
            sender_provider: Email provider type
            
        Returns:
            Spam category if pattern matches, None otherwise
        """
        if sender_provider != 'unknown':
            return None
            
        # Use unified database keywords for domain checking
        from atlas_email.models.database import db
        
        # Check all categories for domain keyword matches
        categories_to_check = [
            'Financial & Investment Spam',
            'Gambling Spam', 
            'Health & Medical Spam',
            'Adult & Dating Spam',
            'Real Estate Spam'
        ]
        
        domain_lower = domain.lower()
        
        for category in categories_to_check:
            # Get keywords for this category from database
            try:
                keywords = db.execute_query(
                    "SELECT term FROM filter_terms WHERE category = ?", 
                    (category,)
                )
                
                # Check if any keyword appears in domain
                for keyword_row in keywords:
                    keyword = keyword_row['term'].lower()
                    if keyword in domain_lower and len(keyword) >= 3:  # Avoid false matches on short terms
                        # Domain keyword match found - remove debug output for production
                        return category
                        
            except Exception as e:
                print(f"⚠️ Database lookup failed for {category}: {e}")
                continue
            
        return None
    
    def check_brand_impersonation(self, sender: str, domain: str, sender_provider: str, suspicious_domain: bool) -> Optional[str]:
        """
        PATTERN-BASED: Check for brand impersonation using pattern detection instead of brand lists.
        
        This approach detects when an email claims to be from a company but the domain doesn't match,
        without maintaining any hardcoded lists of company names.
        
        Args:
            sender: Email sender
            domain: Sender domain
            sender_provider: Email provider type
            suspicious_domain: Whether domain is suspicious
            
        Returns:
            "Brand Impersonation" if detected, None otherwise
        """
        sender_lower = str(sender).lower()
        
        # Step 1: Extract what companies this email claims to represent
        claimed_companies = self._extract_company_claims(sender)
        
        if not claimed_companies:
            return None  # No corporate claims = not impersonation
        
        # Step 2: Check each claimed company against the actual domain
        mismatched_companies = []
        for claimed_company in claimed_companies:
            if not self._domain_matches_company(domain, claimed_company):
                mismatched_companies.append(claimed_company)
        
        # If no companies were mismatched, this is legitimate
        if not mismatched_companies:
            return None
        
        # Check suspicion scores only for mismatched companies
        for claimed_company in mismatched_companies:
            suspicion_score = self._calculate_impersonation_suspicion_score(
                domain, sender, claimed_company, sender_provider
            )
            
            if suspicion_score >= 3:  # Threshold for impersonation detection (raised back to 3 to reduce false positives)
                return "Brand Impersonation"
        
        # Fallback: Check for generic corporate impersonation patterns
        return self._check_generic_corporate_impersonation(sender, domain, sender_provider, suspicious_domain)
    
    def _extract_company_claims(self, sender: str) -> List[str]:
        """
        Extract what companies this email claims to represent from the sender field.
        
        Args:
            sender: Email sender string
            
        Returns:
            List of claimed company names
        """
        if not sender:
            return []
        
        # Clean up sender string and handle unicode spoofing
        sender_clean = self._normalize_unicode_spoofing(sender)
        
        claimed_companies = []
        
        # Pattern 1: Direct company names in sender (use normalized text for patterns)
        # Look for capitalized words that could be company names
        company_patterns = [
            r'\b([A-Z][a-z]{2,}(?:[A-Z][a-z]{2,})+)\b',  # CamelCase companies (UnitedHealthCare)
            r'\b([A-Z][a-z]{4,})\b',                      # Single capitalized words (Amazon, PayPal)
            r'\b([A-Z][A-Z]+)\b',                         # Acronyms like UPS, IBM
            r'([a-z]{3,})\s*(?:team|support|billing|security|customer|service)',  # "amazon team"
            r'(?:from|by)\s+([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)',  # "From Amazon"
            r'\b([A-Z][a-z]{3,})\s+([A-Z][a-z]{3,})\b',  # Two-word companies like "Ralph Lauren"
        ]
        
        # Apply patterns to the normalized (spoofing-free) text
        for pattern in company_patterns:
            matches = re.findall(pattern, sender_clean, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle tuple matches from two-word company pattern
                    if len(match) == 2 and match[0] and match[1]:
                        # Two-word company like "Ralph Lauren"
                        full_company = f"{match[0]} {match[1]}".lower()
                        if self._looks_like_company_name(match[0]) and self._looks_like_company_name(match[1]):
                            claimed_companies.append(full_company)
                            # Also add individual parts for partial matching
                            claimed_companies.append(match[0].lower())
                            claimed_companies.append(match[1].lower())
                    else:
                        match = match[0] if match[0] else match[1]
                        if self._looks_like_company_name(match):
                            claimed_companies.append(match.lower())
                else:
                    # Filter out common words that aren't companies
                    if self._looks_like_company_name(match):
                        claimed_companies.append(match.lower())
        
        return list(set(claimed_companies))  # Remove duplicates
    
    def _normalize_unicode_spoofing(self, text: str) -> str:
        """
        Normalize unicode characters that might be used for spoofing.
        
        Args:
            text: Text that might contain unicode spoofing
            
        Returns:
            Normalized text with common spoofing characters replaced
        """
        # Common unicode spoofing characters
        spoofing_map = {
            '𝐀': 'A', '𝐁': 'B', '𝐂': 'C', '𝐃': 'D', '𝐄': 'E', '𝐅': 'F', '𝐆': 'G',
            '𝐇': 'H', '𝐈': 'I', '𝐉': 'J', '𝐊': 'K', '𝐋': 'L', '𝐌': 'M', '𝐍': 'N',
            '𝐎': 'O', '𝐏': 'P', '𝐐': 'Q', '𝐑': 'R', '𝐒': 'S', '𝐓': 'T', '𝐔': 'U',
            '𝐕': 'V', '𝐖': 'W', '𝐗': 'X', '𝐘': 'Y', '𝐙': 'Z',
            '𝐚': 'a', '𝐛': 'b', '𝐜': 'c', '𝐝': 'd', '𝐞': 'e', '𝐟': 'f', '𝐠': 'g',
            '𝐡': 'h', '𝐢': 'i', '𝐣': 'j', '𝐤': 'k', '𝐥': 'l', '𝐦': 'm', '𝐧': 'n',
            '𝐨': 'o', '𝐩': 'p', '𝐪': 'q', '𝐫': 'r', '𝐬': 's', '𝐭': 't', '𝐮': 'u',
            '𝐯': 'v', '𝐰': 'w', '𝐱': 'x', '𝐲': 'y', '𝐳': 'z'
        }
        
        normalized = text
        for spoofed, normal in spoofing_map.items():
            normalized = normalized.replace(spoofed, normal)
        
        return normalized
    
    def _looks_like_company_name(self, name: str) -> bool:
        """
        Check if a name looks like a legitimate company name.
        
        Args:
            name: Potential company name
            
        Returns:
            True if it looks like a company name
        """
        if not name or len(name) < 3:
            return False
        
        # Filter out common words that aren't companies
        common_words = {
            'email', 'mail', 'message', 'notification', 'alert', 'update',
            'team', 'support', 'customer', 'service', 'security', 'billing',
            'account', 'system', 'admin', 'info', 'help', 'contact', 'reply',
            'from', 'sender', 'user', 'member', 'client', 'guest',
            # Add TLDs that get incorrectly extracted as company names
            'com', 'net', 'org', 'edu', 'gov', 'co', 'io', 'ca', 'uk',
            # Add political/public figures that aren't companies
            'trump', 'biden', 'elon', 'musk', 'bezos', 'gates',
            # Add financial/investment terms that aren't companies
            'crypto', 'blockchain', 'finance', 'investment', 'trading', 'stock',
            'market', 'portfolio', 'retirement', 'forex', 'bitcoin', 'ethereum',
            # Add common promotional/marketing terms
            'promotion', 'marketing', 'newsletter', 'offers', 'deals', 'sales',
            'discount', 'special', 'limited', 'exclusive', 'flash', 'clearance',
            # Add social media terms
            'facebook', 'instagram', 'twitter', 'linkedin', 'social', 'posts',
            'updates', 'recommendations', 'alerts', 'notifications',
            # Add survey/feedback terms
            'survey', 'feedback', 'review', 'rating', 'opinion', 'experience',
            'satisfaction', 'questionnaire',
            # Add general business terms
            'business', 'company', 'corporation', 'enterprise', 'organization',
            'department', 'division', 'branch', 'office', 'center'
        }
        
        if name.lower() in common_words:
            return False
        
        # Check if it has characteristics of a company name
        # Companies usually have vowels and reasonable length
        has_vowels = any(vowel in name.lower() for vowel in 'aeiou')
        reasonable_length = 3 <= len(name) <= 25
        not_all_caps = not name.isupper() or len(name) <= 5  # Allow short acronyms
        
        return has_vowels and reasonable_length and not_all_caps
    
    def _domain_matches_company(self, domain: str, company_name: str) -> bool:
        """
        Check if a domain legitimately belongs to the claimed company.
        
        Args:
            domain: Actual domain
            company_name: Claimed company name
            
        Returns:
            True if domain likely belongs to company
        """
        if not domain or not company_name:
            return False
        
        domain_lower = domain.lower()
        company_lower = company_name.lower()
        
        # First check if it's already a known legitimate domain
        # For legitimate domains, be more lenient with company name matching
        # is_authenticated_domain already imported from classification_utils
        if is_authenticated_domain(domain):
            # For legitimate domains, we trust them more - check for reasonable company connections
            domain_parts = domain.lower().split('.')
            
            # Handle subdomains (e.g., email.consumerreports.org)
            if len(domain_parts) >= 3:
                # Check if company name appears anywhere in the full domain
                full_domain_text = '.'.join(domain_parts[:-1])  # Remove TLD
                if company_lower in full_domain_text or any(part in company_lower for part in domain_parts if len(part) > 3):
                    return True
            
            # For main domains, check if company name appears in the main domain
            main_domain = domain_parts[-2] if len(domain_parts) >= 2 else domain_parts[0]
            if company_lower in main_domain or main_domain in company_lower:
                return True
            
            # ENHANCEMENT: Special handling for third-party email services
            third_party_services = [
                'qualtrics-survey.com', 'qualtrics.com', 'locationrater.com',
                'facebookmail.com', 'email.nextdoor.com', 'rs.email.nextdoor.com',
                'ss.email.nextdoor.com', 'promotion.bedbathandbeyond.com',
                'email.consumerreports.org', 'annualsurveyteam@email.consumerreports.org',
                # Automotive enthusiast and community platforms
                'internetbrandsauto.com', 'internetbrands.com', 'automotiveforums.com',
                'clubmazdausa.com', 'bmwcca.org', 'audiclub.org'
            ]
            
            # If it's a known third-party service, don't require exact name matching
            if any(service in domain for service in third_party_services):
                return True
            
            # For other legitimate domains, continue with stricter pattern matching
        
        # Expected legitimate patterns for company domains
        legitimate_patterns = [
            f"{company_lower}.com",                    # amazon.com
            f"{company_lower}.org",                    # redcross.org
            f"www.{company_lower}.com",                # www.amazon.com
            f"mail.{company_lower}.com",               # mail.amazon.com
            f"email.{company_lower}.com",              # email.amazon.com
            f"newsletter.{company_lower}.com",         # newsletter.amazon.com
            f"no-reply.{company_lower}.com",           # no-reply.amazon.com
            f"noreply.{company_lower}.com",            # noreply.amazon.com
            f"alerts.{company_lower}.com",             # alerts.amazon.com
            f"notifications.{company_lower}.com",      # notifications.amazon.com
            f"promotion.{company_lower}.com",          # promotion.bedbathandbeyond.com
            f"promo.{company_lower}.com",              # promo.company.com
            f"marketing.{company_lower}.com",          # marketing.company.com
            f"offers.{company_lower}.com",             # offers.company.com
            f"deals.{company_lower}.com",              # deals.company.com
            f"news.{company_lower}.com",               # news.company.com
            f"updates.{company_lower}.com",            # updates.company.com
            f"info.{company_lower}.com",               # info.alamodeintimates.com
        ]
        
        # Check if domain matches any legitimate pattern
        for pattern in legitimate_patterns:
            if domain_lower == pattern or domain_lower.endswith('.' + pattern):
                return True
        
        # Check for reasonable domain variations (abbreviations, etc.)
        # Allow some flexibility for legitimate companies
        if company_lower in domain_lower and len(company_lower) >= 4:
            # Company name is in domain - check if it's reasonable
            domain_parts = domain_lower.split('.')
            if len(domain_parts) >= 2:
                main_domain = domain_parts[-2]  # Get the main part before .com
                
                # If company name takes up most of the domain, probably legitimate
                if len(company_lower) / len(main_domain) >= 0.6:
                    return True
        
        # ENHANCEMENT: Handle multi-word company names (e.g., "mode intimates" -> "alamodeintimates.com")
        # Check if all words from company name appear in the domain (concatenated)
        company_words = company_lower.split()
        if len(company_words) > 1:
            domain_parts = domain_lower.split('.')
            main_domain = domain_parts[-2] if len(domain_parts) >= 2 else domain_parts[0]
            
            # Check if concatenating company words creates a match
            concatenated_company = ''.join(company_words)
            if concatenated_company in main_domain:
                return True
            
            # Check if all words appear in the domain (allow partial matches)
            words_found = sum(1 for word in company_words if word in main_domain and len(word) >= 3)
            if words_found >= len(company_words) * 0.7:  # At least 70% of words must be found
                return True
        
        return False
    
    def _calculate_impersonation_suspicion_score(self, domain: str, sender: str, 
                                               claimed_company: str, sender_provider: str) -> int:
        """
        Calculate suspicion score for potential brand impersonation.
        
        Args:
            domain: Actual domain
            sender: Full sender string
            claimed_company: Company name claimed in sender
            sender_provider: Email provider type
            
        Returns:
            Suspicion score (0-10, higher = more suspicious)
        """
        score = 0
        domain_lower = domain.lower()
        sender_lower = sender.lower()
        domain_main = domain.split('.')[0]  # Get main domain part
        
        # Factor 1: Domain characteristics (0-4 points) - ENHANCED
        if len(domain_main) > 25:  # Extremely long domains are highly suspicious
            score += 3
        elif len(domain_main) > 15:  # Very long domains
            score += 2
        elif len(domain_main) > 10:  # Long domains
            score += 1
        
        if any(char.isdigit() for char in domain_lower) and len(domain_lower) > 6:
            score += 1  # Numbers in domain names are suspicious for companies
        
        if any(tld in domain_lower for tld in self.SUSPICIOUS_TLDS):
            score += 2  # Suspicious TLDs
        
        # Factor 2: Company name impersonation patterns (0-4 points) - ENHANCED
        company_lower = claimed_company.lower()
        
        # ENHANCED: Check for obvious impersonation where claimed company is major brand
        # but domain is completely unrelated
        major_brands = {'apple', 'amazon', 'microsoft', 'google', 'paypal', 'facebook', 'netflix', 'ebay'}
        if company_lower in major_brands and company_lower not in domain_lower:
            # Major brand claimed but not in domain at all - VERY suspicious
            score += 3
        
        if company_lower in domain_lower:
            # Company name in domain but doesn't match legitimate patterns - HIGHLY suspicious
            company_in_domain_score = 2
            
            # Extra suspicious if company name is mixed with other words
            domain_without_company = domain_lower.replace(company_lower, '')
            if len(domain_without_company) > 5:  # Lots of extra text around company name
                company_in_domain_score += 1
            
            score += company_in_domain_score
        elif len(company_lower) >= 4:
            # Check for partial company name matches and common abbreviations
            found_partial = False
            
            # Check common company abbreviations
            common_abbreviations = {
                'facebook': ['fb', 'face'],
                'microsoft': ['ms', 'msft', 'micro'],
                'amazon': ['amzn', 'amz'],
                'google': ['goog', 'googl'],
                'paypal': ['pp', 'pypl'],
                'apple': ['aapl'],
                'netflix': ['nflx'],
                'costco': ['cost']
            }
            
            if company_lower in common_abbreviations:
                for abbrev in common_abbreviations[company_lower]:
                    if abbrev in domain_lower:
                        found_partial = True
                        break
            
            # Also check substrings of 3+ characters
            if not found_partial:
                for i in range(3, len(company_lower) + 1):
                    for j in range(len(company_lower) - i + 1):
                        substring = company_lower[j:j+i]
                        if len(substring) >= 3 and substring in domain_lower:
                            found_partial = True
                            break
                    if found_partial:
                        break
            
            if found_partial:
                score += 1  # Partial match is somewhat suspicious
        
        # Factor 3: Unicode spoofing (0-2 points)
        if self._has_unicode_spoofing(sender):
            score += 2
        
        # Factor 4: Provider context (0-1 point)
        if sender_provider == 'unknown':
            score += 1  # Unknown providers more suspicious
        
        # Factor 5: Obvious impersonation patterns (0-2 points) - NEW
        suspicious_patterns = [
            'verification', 'secure', 'update', 'suspended', 'alert',
            'notification', 'billing', 'account', 'support'
        ]
        if any(pattern in domain_lower for pattern in suspicious_patterns):
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    def _has_unicode_spoofing(self, text: str) -> bool:
        """Check if text contains unicode spoofing characters."""
        # Check for mathematical alphanumeric symbols (common in spoofing)
        unicode_spoofing_ranges = [
            (0x1D400, 0x1D7FF),  # Mathematical Alphanumeric Symbols
            (0xFF00, 0xFFEF),    # Halfwidth and Fullwidth Forms
        ]
        
        for char in text:
            char_code = ord(char)
            for start, end in unicode_spoofing_ranges:
                if start <= char_code <= end:
                    return True
        return False
    
    def _check_generic_corporate_impersonation(self, sender: str, domain: str, 
                                             sender_provider: str, suspicious_domain: bool) -> Optional[str]:
        """
        Check for generic corporate impersonation patterns when no specific company is claimed.
        
        This catches cases where scammers use corporate-sounding language without claiming
        to be a specific company.
        """
        if sender_provider != 'unknown' or not suspicious_domain:
            return None
        
        sender_lower = sender.lower()
        
        # Check for corporate-sounding patterns in sender
        corporate_patterns = [
            'customer.service', 'billing.department', 'security.team',
            'account.verification', 'payment.processing', 'no.reply',
            'noreply', 'support', 'notification', 'alert'
        ]
        
        has_corporate_pattern = any(pattern in sender_lower for pattern in corporate_patterns)
        
        if has_corporate_pattern and suspicious_domain:
            # Generic corporate impersonation
            return "Brand Impersonation"
        
        return None
    
    def count_emojis(self, text: str) -> Tuple[int, int]:
        """
        Count total emojis and scam-specific emojis in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (total_emoji_count, scam_emoji_count)
        """
        emoji_matches = self.emoji_pattern.findall(text)
        emoji_count = len(emoji_matches)
        
        scam_emoji_count = 0
        for emoji in emoji_matches:
            if emoji in self.SCAM_EMOJIS:
                scam_emoji_count += 1
                
        return emoji_count, scam_emoji_count
    
    def check_emoji_spam(self, subject: str, all_text: str) -> Optional[str]:
        """
        Check for emoji spam patterns.
        
        Args:
            subject: Email subject
            all_text: Combined text from subject and headers
            
        Returns:
            "Emoji Spam" if detected, None otherwise
        """
        subject_emoji_count, subject_scam_count = self.count_emojis(str(subject))
        total_emoji_count, total_scam_count = self.count_emojis(all_text)
        
        # Emoji spam criteria
        if (subject_emoji_count >= 3 and subject_scam_count >= 2) or total_scam_count >= 4:
            return "Emoji Spam"
            
        return None
    
    def check_protected_patterns(self, sender: str, subject: str) -> Optional[str]:
        """
        Check if email matches any user-protected patterns.
        If matched, return 'Not Spam' to prevent deletion.
        
        Args:
            sender: Email sender address
            subject: Email subject line
            
        Returns:
            'Not Spam' if protected, None otherwise
        """
        try:
            from atlas_email.models.database import db
            
            # Extract domain from sender
            domain = None
            if sender and '@' in sender:
                domain = sender.split('@')[1].lower()
            
            # Check exact sender match
            if sender:
                sender_matches = db.execute_query("""
                    SELECT confidence_score FROM protected_patterns 
                    WHERE pattern_type = 'sender' AND pattern_value = ?
                """, (sender.lower(),))
                
                if sender_matches:
                    print(f"🛡️ Email protected by exact sender match: {sender}")
                    return "Not Spam"
                
                # Check if sender contains any protected pattern as domain
                # This handles cases where pattern "metal" should protect "test@metal.com"
                if domain:
                    domain_base = domain.split('.')[0]  # Get "metal" from "metal.com"
                    base_matches = db.execute_query("""
                        SELECT confidence_score FROM protected_patterns 
                        WHERE pattern_type = 'sender' AND pattern_value = ?
                    """, (domain_base,))
                    
                    if base_matches:
                        print(f"🛡️ Email protected by domain base match: {domain_base}")
                        return "Not Spam"
            
            # Check domain match
            if domain:
                domain_matches = db.execute_query("""
                    SELECT confidence_score FROM protected_patterns 
                    WHERE pattern_type = 'domain' AND pattern_value = ?
                """, (domain,))
                
                if domain_matches:
                    print(f"🛡️ Email protected by domain match: {domain}")
                    return "Not Spam"
            
            # Check subject keyword patterns
            if subject:
                subject_lower = subject.lower()
                
                # Check for newsletter pattern
                newsletter_matches = db.execute_query("""
                    SELECT confidence_score FROM protected_patterns 
                    WHERE pattern_type = 'subject_keyword' AND pattern_value = 'newsletter_pattern'
                """)
                
                if newsletter_matches and any(keyword in subject_lower for keyword in ['newsletter', 'update', 'notification', 'alert', 'digest']):
                    print(f"🛡️ Email protected by newsletter pattern: {subject[:50]}")
                    return "Not Spam"
                
                # Check for promotional pattern
                promo_matches = db.execute_query("""
                    SELECT confidence_score FROM protected_patterns 
                    WHERE pattern_type = 'subject_keyword' AND pattern_value = 'promotional_pattern'
                """)
                
                if promo_matches and any(keyword in subject_lower for keyword in ['sale', 'offer', 'deal', 'discount', 'promo']):
                    print(f"🛡️ Email protected by promotional pattern: {subject[:50]}")
                    return "Not Spam"
            
            # No protection patterns matched
            return None
            
        except Exception as e:
            print(f"⚠️ Error checking protected patterns: {e}")
            # On error, don't protect (allow normal classification)
            return None
    
    def process_keywords(self, headers: str, sender: str, subject: str, matched_term: str = None) -> str:
        """
        🚀 REVOLUTIONARY EMAIL CLASSIFICATION with Two-Factor Validation
        
        Args:
            headers: Email headers
            sender: Email sender
            subject: Email subject
            matched_term: Previously matched term (legacy parameter)
            
        Returns:
            Classified spam type
        """
        # FIRST: Check for user-protected patterns (highest priority)
        protected_result = self.check_protected_patterns(sender, subject)
        if protected_result:
            return protected_result
        
        # SECOND: Check for community emails (preserve neighborhood communications)
        # is_community_email already imported from classification_utils
        if is_community_email(subject, sender, headers):
            return "Community Email"
        
        # THIRD: Check for transactional emails (receipts, confirmations, statements) - HIGH PRIORITY
        # is_transactional_email already imported from classification_utils
        if is_transactional_email(subject, sender, headers):
            return "Transactional Email"
        
        # FOURTH: Check for account notifications (security alerts, password resets) - HIGH PRIORITY
        # is_account_notification already imported from classification_utils
        if is_account_notification(subject, sender, headers):
            return "Account Notification"
        
        # FIFTH: Check for subscription management (terms changes, service updates) - HIGH PRIORITY
        # is_subscription_management already imported from classification_utils
        if is_subscription_management(subject, sender, headers):
            return "Subscription Management"
        
        # 🧠 LOGICAL CLASSIFIER: Use intelligent decision tree for spam classification
        try:
            from atlas_email.core.logical_classifier import LogicalEmailClassifier
            logical_classifier = LogicalEmailClassifier()
            logical_category, logical_confidence, logical_reason = logical_classifier.classify_email(sender, subject, headers)
            
            # Use logical classifier result with high confidence
            if logical_confidence >= 0.7:
                print(f"🧠 LOGICAL CLASSIFIER: {sender} → {logical_category} (confidence: {logical_confidence:.2f}) - {logical_reason}")
                self.last_classification_confidence = logical_confidence
                return logical_category
            else:
                print(f"🔄 LOGICAL CLASSIFIER BACKUP: {sender} → {logical_category} (confidence: {logical_confidence:.2f}) - Continuing with fallback")
        except Exception as e:
            print(f"⚠️ Logical classifier error for {sender}: {e}")
            # Continue with traditional processing
        
        # 🚀 REVOLUTIONARY: Try two-factor validation first for promotional emails
        if self.two_factor_validator and TWO_FACTOR_AVAILABLE:
            try:
                # Combine headers and subject for content analysis
                email_content = f"{headers} {subject}" if headers else subject
                
                classification, confidence, reasoning, should_delete = self.two_factor_validator.validate_email_classification(
                    sender, subject, email_content
                )
                
                # If two-factor validation gives a definitive result, use it
                if confidence >= 0.8 or classification in ['Promotional Email', 'Phishing', 'Financial & Investment Spam', 'Health & Medical Spam']:
                    print(f"🚀 TWO-FACTOR RESULT: {sender} → {classification} (confidence: {confidence:.2f})")
                    return classification
                    
                # For lower confidence results, continue with traditional processing as backup
                print(f"🔄 TWO-FACTOR BACKUP: {sender} → {classification} (confidence: {confidence:.2f}) - Continuing with traditional processing")
                
            except Exception as e:
                print(f"⚠️ Two-factor validation error for {sender}: {e}")
                # Continue with traditional processing
        
        # Continue with traditional keyword processing as fallback or primary method
        
        # Prepare text for analysis - INCLUDE SENDER for domain-based keyword matching
        headers_str = str(headers) if headers else ""
        headers_lower = headers_str.lower()
        subject_lower = str(subject).lower() if subject else ""
        sender_lower = str(sender).lower() if sender else ""
        all_text = f"{subject_lower} {headers_lower} {sender_lower}"
        
        # Extract domain and provider information
        domain, sender_provider = self.extract_domain_info(sender)
        
        # Check for legitimate company domain (default)
        is_legitimate_domain = is_authenticated_domain(domain)
        
        # Check for suspicious domain patterns (needed for brand impersonation detection)
        suspicious_domain = self.is_suspicious_domain(domain, sender_provider)
        
        # 🚀 UNIVERSAL SUBDOMAIN COMPLEXITY DETECTION
        # Check for sophisticated scam patterns using complex subdomains across ALL categories
        subdomain_suspicious, subdomain_reason = self.detect_universal_subdomain_complexity(domain, sender_provider)
        if subdomain_suspicious:
            print(f"🎯 SUBDOMAIN COMPLEXITY DETECTED: {sender} - {subdomain_reason}")
            # Route to content-based classification to determine specific spam type
            # Don't immediately classify as brand impersonation - let content analysis decide the category
            suspicious_domain = True  # Mark as suspicious for downstream processing
        
        # 🚨 SOPHISTICATED DISPLAY NAME ANALYSIS
        # Check for overly complex display names and spam patterns
        display_suspicious, display_reason, display_score = self.analyze_display_name_complexity(sender)
        display_categories = self.analyze_display_name_categories(sender)
        
        if display_suspicious:
            print(f"🚨 DISPLAY NAME COMPLEXITY DETECTED: {sender}")
            print(f"   Reason: {display_reason}")
            print(f"   Suspicion Score: {display_score:.2f}")
            # High display name suspicion should lower classification thresholds
            suspicious_domain = True  # Mark as suspicious for downstream processing
        
        if display_categories:
            print(f"🎯 DISPLAY NAME CATEGORIES DETECTED: {sender}")
            for category, confidence in display_categories.items():
                print(f"   {category}: {confidence:.3f}")
            # Mark as suspicious if display name contains spam category keywords
            suspicious_domain = True
        
        # EARLY CHECK: If this is promotional content from a trusted domain, return immediately
        # REMOVED: This was causing over-classification as Promotional Email
        # Instead, let proper content analysis determine the specific category first
        
        # EARLY SPAM DETECTION - Check for obvious spam patterns BEFORE vendor filtering
        # This prevents spoofed emails from bypassing detection due to "trusted" email providers
        
        # Check for unicode spoofing first (highest priority for security)
        if self._has_unicode_spoofing(sender) or self._has_unicode_spoofing(subject):
            # Unicode spoofing detected - check if this is brand impersonation or phishing
            brand_impersonation = self.check_brand_impersonation(sender, domain, sender_provider, suspicious_domain)
            if brand_impersonation:
                return brand_impersonation
            # If not brand impersonation, continue checking for other spam types with lower threshold
            confidence_threshold = 0.3  # Lower threshold for unicode spoofing emails
        
        # Vendor filtering removed - using pure logic over static lists
        
        # Check for encoded spam first - Enhanced with content analysis
        if self.check_encoded_spam(subject, sender):
            # NEW: Attempt to decode and classify the content
            try:
                # classify_encoded_spam_content already imported from classification_utils
                decoded_classification = classify_encoded_spam_content(headers, sender, subject)
                print(f"🔍 KeywordProcessor: Encoded spam decoded as: {decoded_classification}")
                return decoded_classification
            except Exception as e:
                print(f"⚠️ KeywordProcessor: Decoding failed: {e}, falling back to generic Encoded Spam")
                return "Encoded Spam"
        
        # Suspicious domain already calculated above
        
        # Set confidence threshold based on domain legitimacy and updated ML settings
        # Factor in display name suspicion for threshold adjustment
        if is_legitimate_domain and not subdomain_suspicious and not display_suspicious:
            # Only be very conservative for truly legitimate domains without any suspicion indicators
            confidence_threshold = 0.8  # Lowered from 0.95 to catch sophisticated newsletter scams
        elif suspicious_domain or subdomain_suspicious or display_suspicious:
            # Lower threshold for any form of suspicion to catch more spam
            base_threshold = 0.4  # Base threshold for suspicious indicators
            
            # Further lower threshold based on display name suspicion score
            if display_suspicious and display_score >= 0.8:
                confidence_threshold = 0.3  # Very suspicious display names get lowest threshold
            else:
                confidence_threshold = base_threshold
        else:
            # Use moderate threshold for unknown domains
            confidence_threshold = 0.6  # Lowered from 0.7 to catch more spam
        
        # PRIORITY FIX: Check database keywords FIRST to ensure specific categories take precedence
        # Pass display name categories for enhanced confidence scoring
        best_category = self.find_best_category_match(all_text, confidence_threshold, display_categories)
        if best_category:
            # 🎯 ENHANCED: Content-first classification - specific spam categories override domain reputation
            high_priority_spam_categories = [
                "Phishing", "Payment Scam", "Legal & Compensation Scams", 
                "Financial & Investment Spam", "Health & Medical Spam",
                "Adult & Dating Spam", "Gambling Spam"
            ]
            
            # If we have a high-confidence match for specific spam, trust the content over domain reputation
            if best_category in high_priority_spam_categories:
                found_keyword, spam_confidence = check_all_keywords(all_text, best_category)
                if spam_confidence >= 0.6:  # High confidence threshold for overriding domain reputation
                    print(f"🎯 CONTENT OVERRIDE: {best_category} (confidence: {spam_confidence:.2f}) overrides domain reputation")
                    return best_category
            
            # For legitimate domains with lower confidence spam matches, be more conservative
            if is_legitimate_domain:
                if best_category not in high_priority_spam_categories:
                    return "Promotional Email"
                else:
                    # For spam categories, require higher confidence for legitimate domains
                    found_keyword, spam_confidence = check_all_keywords(all_text, best_category)
                    if spam_confidence >= 0.7:  # Higher threshold for legitimate domains
                        return best_category
                    else:
                        return "Promotional Email"
            
            return best_category
        
        # Check brand impersonation ONLY if no specific database category matches
        brand_impersonation = self.check_brand_impersonation(sender, domain, sender_provider, suspicious_domain)
        if brand_impersonation:
            # ENHANCED: Check if this brand impersonation is actually phishing
            phishing_indicators = [
                'winner', 'won', 'claim', 'verify', 'urgent', 'final', 'expires',
                'reward', 'prize', 'gift card', 'reimbursement', 'last call',
                'account suspended', 'account blocked', 'service has been suspended',
                'verification required', 'click to verify', 'confirm your', 
                'time is running out', 'subscription expired', 'subscription has expired',
                'reactivate now', 'renew your', 'data will be deleted',
                'photos will be removed', 'videos will be removed'
            ]
            
            all_text_lower = all_text.lower()
            has_phishing_indicators = any(indicator in all_text_lower for indicator in phishing_indicators)
            
            if has_phishing_indicators:
                # This is phishing disguised as brand impersonation - prioritize phishing
                return "Phishing"
            else:
                return brand_impersonation
        
        # Special handling for legitimate domains
        if is_legitimate_domain:
            return "Promotional Email"
        
        # Check individual categories with database keywords
        if check_keywords_simple(all_text, "Financial & Investment Spam"):
            return "Financial & Investment Spam"
            
        if check_keywords_simple(all_text, "Gambling Spam"):
            return "Gambling Spam"
            
        if check_keywords_simple(all_text, "Legal Settlement Scam"):
            return "Legal Settlement Scam"
        
        # Check domain patterns
        domain_category = self.check_domain_patterns(domain, sender_provider)
        if domain_category:
            return domain_category
        
        # Check brand impersonation
        brand_impersonation = self.check_brand_impersonation(sender, domain, sender_provider, suspicious_domain)
        if brand_impersonation:
            return brand_impersonation
        
        # Check emoji spam
        emoji_spam = self.check_emoji_spam(subject, all_text)
        if emoji_spam:
            return emoji_spam
        
        # Check promotional/marketing content
        if check_keywords_simple(all_text, "Marketing Spam"):
            if is_legitimate_domain:  # TRUSTED domain
                return "Promotional Email"  
            else:  # UNTRUSTED domain  
                return "Marketing Spam"
        
        # Final fallback
        if is_legitimate_domain:
            return "Promotional Email"
            
        return "Marketing Spam"


# Create global instance for backward compatibility
keyword_processor = KeywordProcessor()

def classify_spam_type_with_processor(headers, sender, subject, matched_term=None):
    """
    Backward-compatible wrapper function that uses the new KeywordProcessor.
    
    This allows existing code to continue working while using the new modular approach.
    """
    return keyword_processor.process_keywords(headers, sender, subject, matched_term)

# Export classes and functions
__all__ = ['KeywordProcessor', 'classify_spam_type_with_processor', 'keyword_processor']