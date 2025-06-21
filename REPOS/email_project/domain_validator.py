#!/usr/bin/env python3
"""
Domain Validator - Advanced domain analysis and validation system
Enhanced with provider-aware domain validation and optimization
Now with pre-compiled regex patterns for better performance
"""

import re
import math
import tldextract
from datetime import datetime
from email.header import decode_header

# Import regex optimizer for performance enhancement
try:
    from regex_optimizer import regex_optimizer, get_pattern, check_domain_fast
    REGEX_OPTIMIZER_AVAILABLE = True
    print("🚀 Domain Validator: Using optimized regex patterns")
except ImportError:
    REGEX_OPTIMIZER_AVAILABLE = False
    print("⚠️ Domain Validator: Using standard regex patterns")

# ============================================================================
# GIBBERISH DETECTION UTILITIES
# ============================================================================

def looks_like_gibberish(s):
    """
    Improved gibberish detection using advanced algorithms.
    Enhanced with entropy analysis, vowel patterns, and word recognition.
    """
    # Try to use improved detection if available
    try:
        from improved_gibberish_detector import improved_looks_like_gibberish
        return improved_looks_like_gibberish(s)
    except ImportError:
        # Fallback to enhanced regex-based detection
        if REGEX_OPTIMIZER_AVAILABLE:
            # Use pre-compiled pattern for better performance
            pattern = get_pattern('gibberish', 'no_vowels_long')
            if pattern and pattern.search(s):
                return True
        
        # Enhanced fallback detection
        if len(s) < 4:
            return False
        
        # Check for very long consonant sequences
        if re.search(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{8,}', s):
            return True
        
        # Check for high digit-to-letter ratio in non-numeric strings
        letters = sum(1 for c in s if c.isalpha())
        digits = sum(1 for c in s if c.isdigit())
        if letters > 0 and digits / max(letters, 1) > 0.6 and len(s) > 6:
            return True
        
        # Check for very random-looking patterns
        if len(s) > 10 and not re.search(r'[aeiou]', s.lower()):
            return True
        
        return False

def is_gibberish_email(email):
    """
    Determines if an email address (local part or main domain part)
    looks like gibberish using improved detection.
    """
    # Try to use improved detection if available
    try:
        from improved_gibberish_detector import improved_is_gibberish_email
        return improved_is_gibberish_email(email)
    except ImportError:
        # Fallback to enhanced detection
        try:
            local_part, domain_part = email.lower().split('@')
            # Clean domain part
            domain_part = domain_part.strip('<>').replace('>', '').replace('<', '')
            
            # Extract domain components
            ext = tldextract.extract(domain_part)
            main_domain_name = ext.domain
            
            # Check main domain (most important)
            if main_domain_name and looks_like_gibberish(main_domain_name):
                return True
            
            # Check subdomain if present and significant
            if ext.subdomain and len(ext.subdomain) > 4 and looks_like_gibberish(ext.subdomain):
                return True
            
            # Check local part if very long and suspicious
            if len(local_part) > 12 and looks_like_gibberish(local_part):
                return True
            
            return False
        except Exception:
            return True  # Invalid format or parsing error can indicate suspicion

# ============================================================================
# PROVIDER DETECTION UTILITIES
# ============================================================================

def detect_provider_from_sender(sender_email):
    """Detect email provider from sender email address"""
    if not sender_email or '@' not in sender_email:
        return 'unknown'

    domain = sender_email.split('@')[1].lower().replace('>', '').strip()

    # Major email providers
    if domain in ['icloud.com', 'me.com', 'mac.com']:
        return 'icloud'
    elif domain == 'gmail.com':
        return 'gmail'
    elif domain in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']:
        return 'outlook'
    elif domain in ['yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.fr', 'yahoo.de']:
        return 'yahoo'
    elif domain == 'aol.com':
        return 'aol'
    else:
        return 'unknown'

def is_major_email_provider(domain):
    """Check if domain belongs to a major email provider"""
    major_providers = {
        'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'live.com',
        'icloud.com', 'me.com', 'mac.com', 'aol.com', 'msn.com',
        'yahoo.co.uk', 'yahoo.ca', 'yahoo.fr', 'yahoo.de'
    }
    return domain.lower() in major_providers

def get_provider_reputation_score(domain):
    """Get reputation score for email provider domains"""
    if not domain:
        return 0

    domain_lower = domain.lower()

    # Tier 1: Most trusted providers
    tier1_providers = {
        'gmail.com': 95,
        'icloud.com': 95,
        'me.com': 95,
        'mac.com': 95,
        'outlook.com': 90,
        'hotmail.com': 85,
        'live.com': 85
    }

    # Tier 2: Established providers
    tier2_providers = {
        'yahoo.com': 80,
        'yahoo.co.uk': 80,
        'yahoo.ca': 80,
        'aol.com': 75,
        'msn.com': 75
    }

    # Tier 3: Business/Educational
    if any(domain_lower.endswith(suffix) for suffix in ['.edu', '.gov', '.org']):
        return 85

    # Check tiers
    if domain_lower in tier1_providers:
        return tier1_providers[domain_lower]
    elif domain_lower in tier2_providers:
        return tier2_providers[domain_lower]

    # Corporate domains (basic heuristic)
    if '.' in domain_lower and not domain_lower.endswith(('.tk', '.ml', '.ga', '.cf')):
        parts = domain_lower.split('.')
        if len(parts) == 2 and len(parts[0]) > 3:  # Reasonable company domain
            return 60

    return 30  # Unknown/suspicious domains

# ============================================================================
# MACHINE LEARNING DOMAIN ANALYSIS
# ============================================================================

def calculate_entropy(text):
    """Calculate Shannon entropy of a string - higher entropy = more random"""
    if not text:
        return 0
    char_counts = {}
    for char in text.lower():
        char_counts[char] = char_counts.get(char, 0) + 1
    entropy = 0
    length = len(text)
    for count in char_counts.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)
    return entropy

def count_real_words(text):
    """Count how many real English words are in the domain"""
    common_words = {
        'mail', 'email', 'contact', 'info', 'support', 'admin', 'web', 'www', 'news',
        'shop', 'store', 'buy', 'sell', 'get', 'new', 'best', 'top', 'free', 'win',
        'game', 'play', 'fun', 'cool', 'good', 'bad', 'big', 'small', 'fast', 'slow',
        'old', 'young', 'hot', 'cold', 'red', 'blue', 'green', 'black', 'white',
        'home', 'work', 'life', 'love', 'time', 'day', 'night', 'year', 'week',
        'health', 'money', 'bank', 'pay', 'card', 'deal', 'sale', 'offer', 'price',
        'service', 'help', 'team', 'group', 'club', 'world', 'global', 'local',
        'tech', 'data', 'cloud', 'digital', 'online', 'mobile', 'app', 'soft'
    }
    clean_text = re.sub(r'[0-9]', '', text.lower())
    potential_words = re.split(r'[.\-_]', clean_text)
    word_count = 0
    for word in potential_words:
        if len(word) >= 3 and word in common_words:
            word_count += 1
    return word_count

def has_natural_vowel_pattern(text):
    """Check if text has natural vowel/consonant patterns like real words"""
    if not text:
        return False
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    vowel_count = sum(1 for char in text.lower() if char in vowels)
    consonant_count = sum(1 for char in text.lower() if char in consonants)
    if vowel_count + consonant_count == 0:
        return False
    vowel_ratio = vowel_count / (vowel_count + consonant_count)
    return 0.25 <= vowel_ratio <= 0.55

def detect_keyboard_patterns(text):
    """Detect keyboard walks like 'qwerty', 'asdf', '123456'"""
    keyboard_rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm', '1234567890']
    text_lower = text.lower()
    for row in keyboard_rows:
        for i in range(len(row) - 2):
            pattern = row[i:i+3]
            if pattern in text_lower:
                return True
    return False

def analyze_character_distribution(text):
    """Analyze if character distribution looks natural"""
    if len(text) < 4:
        return False
    char_counts = {}
    for char in text.lower():
        if char.isalnum():
            char_counts[char] = char_counts.get(char, 0) + 1
    if not char_counts:
        return False
    max_char_freq = max(char_counts.values())
    return max_char_freq / len(text) > 0.4

def ml_domain_classification(domain, sender_email="", provider_context=None):
    """Enhanced ML domain classification with provider awareness"""
    if not domain:
        return False, 0, []

    # Provider-aware validation
    if provider_context:
        provider_reputation = get_provider_reputation_score(domain)
        if provider_reputation >= 85:
            return False, 0, [f"Major email provider ({provider_context})"]

    domain_clean = domain.lower().replace('.', '')
    domain_parts = domain.split('.')
    entropy_score = calculate_entropy(domain_clean)
    real_words = count_real_words(domain_clean)
    has_vowel_pattern = has_natural_vowel_pattern(domain_clean)
    has_keyboard_walk = detect_keyboard_patterns(domain_clean)
    has_char_repetition = analyze_character_distribution(domain_clean)

    username_suspicious = False
    username = ""
    if sender_email and '@' in sender_email:
        username = sender_email.split('@')[0]
        username_entropy = calculate_entropy(username)
        username_suspicious = (
            len(username) > 15 or
            username_entropy > 3.5 or
            not has_natural_vowel_pattern(username)
        )

    score = 0
    reasons = []

    # Check for gibberish using the dedicated function
    if sender_email and is_gibberish_email(sender_email):
        score += 30  # A very strong indicator, give it a high score
        reasons.append("Detected as gibberish email (long non-vowel sequences)")

    # Enhanced scoring algorithm with provider context
    base_entropy_threshold = 3.2
    if provider_context == 'icloud':
        # iCloud tends to have more random-looking domains, adjust threshold
        base_entropy_threshold = 3.5
    elif provider_context in ['gmail', 'outlook']:
        # These providers have stricter domain policies
        base_entropy_threshold = 3.0

    # Scoring algorithm
    if entropy_score > base_entropy_threshold + 0.6:
        score += 25
        reasons.append(f"Very high entropy ({entropy_score:.1f})")
    elif entropy_score > base_entropy_threshold:
        score += 15
        reasons.append(f"High entropy ({entropy_score:.1f})")

    if real_words == 0 and len(domain_clean) > 8:
        score += 20
        reasons.append("No recognizable words")
    elif real_words == 0 and len(domain_clean) > 12:
        score += 25
        reasons.append("No recognizable words in long domain")

    if not has_vowel_pattern and len(domain_clean) > 6:
        score += 15
        reasons.append("Unnatural vowel/consonant pattern")

    if has_keyboard_walk:
        score += 10
        reasons.append("Contains keyboard patterns")

    if has_char_repetition:
        score += 15
        reasons.append("Excessive character repetition")

    if len(domain_clean) > 20 and real_words == 0:
        score += 15
        reasons.append(f"Very long domain ({len(domain_clean)} chars) with no words")

    if username_suspicious:
        score += 10
        reasons.append("Suspicious email username")

    random_parts = sum(1 for part in domain_parts[:-1]
                      if len(part) > 6 and calculate_entropy(part) > 3.0)
    if random_parts >= 2:
        score += 10
        reasons.append(f"Multiple random domain parts ({random_parts})")

    # Check for long random alphanumeric domains using optimized patterns
    if REGEX_OPTIMIZER_AVAILABLE:
        pattern = get_pattern('domain', 'long_random')
        if pattern and pattern.match(domain_clean) and not has_vowel_pattern:
            score += 20
            reasons.append("Long alphanumeric string with no pattern")
    else:
        if re.search(r'^[a-z0-9]{12,}$', domain_clean) and not has_vowel_pattern:
            score += 20
            reasons.append("Long alphanumeric string with no pattern")

    # Provider-specific adjustments
    if provider_context == 'icloud':
        # iCloud forwarding domains can look suspicious but are legitimate
        if 'icloud' in domain or 'apple' in domain:
            score = max(0, score - 30)
            reasons.append("iCloud-related domain")
    elif provider_context == 'gmail':
        # Gmail has strict policies, so suspicious domains are more likely spam
        if score > 40:
            score += 10
            reasons.append("High suspicion on Gmail platform")

    # Final provider reputation check
    provider_rep = get_provider_reputation_score(domain)
    if provider_rep >= 85:
        score = max(0, score - 40)
        reasons = [f"Major provider (reputation: {provider_rep})"] + reasons

    is_suspicious = score >= 50
    confidence = min(score, 100)
    return is_suspicious, confidence, reasons

def lightweight_domain_validation(domain, provider_hint=None):
    """Enhanced domain age validation with provider awareness"""
    try:
        import whois
    except ImportError:
        return 'QUARANTINE'

    # Skip WHOIS for known major providers
    if is_major_email_provider(domain):
        return 'SAFE'

    try:
        domain_info = whois.whois(domain)
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            domain_age_days = (datetime.now() - creation_date).days

            # Provider-specific age thresholds
            if provider_hint == 'icloud':
                # iCloud users often use newer domains
                if domain_age_days < 14:
                    return 'SUSPICIOUS'
                elif domain_age_days < 60:
                    return 'QUARANTINE'
                else:
                    return 'SAFE'
            else:
                # Standard thresholds for other providers
                if domain_age_days < 30:
                    return 'SUSPICIOUS'
                elif domain_age_days < 90:
                    return 'QUARANTINE'
                else:
                    return 'SAFE'
        return 'QUARANTINE'
    except Exception:
        return 'QUARANTINE'

def is_suspicious_domain_pattern(domain):
    """Enhanced detection of suspicious domain patterns"""
    if not domain:
        return False

    parts = domain.split('.')
    suspicious_patterns = [
        len(parts[0]) > 10,
        len(parts) > 4,
        any(re.search(r'[A-Z]{2,}[a-z]{2,}[A-Z]{2,}|[a-z]{2,}[A-Z]{2,}[a-z]{2,}', part) for part in parts[:2]),
        any(re.search(r'^[a-z0-9]{8,}$', part) for part in parts[:2]),
        any(re.search(r'[0-9]{2,}[a-z]{2,}[0-9]{2,}|[a-z]{2,}[0-9]{2,}[a-z]{2,}', part) for part in parts[:2]),
        any(re.search(r'^[a-z]{15,}$', part) for part in parts[:2]),
        len(parts) > 3 and any(parts[-1].endswith(tld) for tld in [".tk", ".ml", ".ga", ".cf", ".us"]),
        re.search(r'[0-9]{4,}', domain),
    ]
    return any(suspicious_patterns)

# ============================================================================
# DOMAIN VALIDATOR CLASS
# ============================================================================

class DomainValidator:
    """Enhanced domain validation class with provider awareness"""

    def __init__(self, logger=None, account_provider=None):
        self.logger = logger
        self.account_provider = account_provider  # Provider of the account being processed
        self.known_legitimate = {
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
            "aol.com", "icloud.com", "live.com", "msn.com", "protonmail.com",
            "aliexpress.com", "alibaba.com", "amazon.com", "ebay.com",
            "discoveryplus.com", "netflix.com", "hulu.com", "disney.com",
            "apple.com", "microsoft.com", "google.com", "facebook.com",
            "paypal.com", "stripe.com", "shopify.com", "etsy.com",
            "cnn.com", "bbc.com", "reuters.com", "nytimes.com",
            "chase.com", "bankofamerica.com", "wellsfargo.com", "citi.com",
            "me.com", "mac.com"  # Added iCloud domains
        }

    def log(self, message, print_to_screen=False):
        """Log message if logger is available"""
        if self.logger:
            self.logger(message, print_to_screen)

    def validate_domain_before_deletion(self, sender_email, subject):
        """Enhanced domain validation with provider-specific optimization"""
        if not sender_email or '@' not in sender_email:
            return True, "Invalid sender format", False

        # Immediate check for gibberish email
        if is_gibberish_email(sender_email):
            self.log(f"DOMAIN VALIDATION: Detected as gibberish email (via direct check) - ALLOWING DELETION: {sender_email}", False)
            return True, "Detected as highly gibberish email", True

        domain = sender_email.split('@')[1].lower().replace('>', '').strip()
        domain = re.sub(r'[<>\s]', '', domain)
        ext = tldextract.extract(domain)
        registered_domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else domain

        # Detect sender's provider for context
        sender_provider = detect_provider_from_sender(sender_email)

        # Enhanced whitelist check with provider context
        if registered_domain in self.known_legitimate:
            provider_context = f" ({sender_provider})" if sender_provider != 'unknown' else ""
            return False, f"Major email provider{provider_context} - PRESERVED", False

        # Provider-aware ML Classification
        is_ml_suspicious, ml_confidence, ml_reasons = ml_domain_classification(
            domain, sender_email, provider_context=sender_provider
        )

        # Account provider specific adjustments
        confidence_threshold = 70
        if self.account_provider == 'icloud':
            # iCloud users may receive emails from more diverse domains
            confidence_threshold = 75
        elif self.account_provider == 'gmail':
            # Gmail has good spam filtering already, be more conservative
            confidence_threshold = 80

        # High confidence ML decision with provider awareness
        if is_ml_suspicious and ml_confidence >= confidence_threshold:
            reason_str = "; ".join(ml_reasons[:3])
            context_note = f" [Account: {self.account_provider}, Sender: {sender_provider}]" if self.account_provider else ""
            self.log(f"DOMAIN VALIDATION: ML Classification - HIGH CONFIDENCE SPAM ({ml_confidence}%) - ALLOWING DELETION: {domain}{context_note} - {reason_str}", False)
            return True, f"ML High Confidence Spam ({ml_confidence}%): {reason_str}", True

        # Traditional pattern detection with provider context
        domain_parts = domain.split('.')
        all_parts = domain_parts[:-1]

        definitely_suspicious = [
            any(len(part) > 15 for part in all_parts),
            any(re.search(r'^[a-z0-9]{12,}$', part) for part in all_parts),
            any(re.search(r'[A-Z]{2,}[a-z]{2,}[A-Z]{2,}|[a-z]{2,}[A-Z]{2,}[a-z]{2,}', part) for part in all_parts),
            len(domain_parts) > 4,
            len([part for part in all_parts if len(part) > 8]) >= 3,
            any(re.search(r'[0-9]{2,}[a-z]{2,}[0-9]{2,}|[a-z]{2,}[0-9]{2,}[a-z]{2,}', part) for part in all_parts),
            '@' in sender_email and len(sender_email.split('@')[0]) > 15,
            any(re.search(r'^[a-z0-9]{15,}$', part) for part in all_parts),
        ]

        if any(definitely_suspicious):
            context_note = f" [Provider context: {sender_provider}]" if sender_provider != 'unknown' else ""
            self.log(f"DOMAIN VALIDATION: Traditional Pattern - DEFINITELY SUSPICIOUS - ALLOWING DELETION: {domain}{context_note}", False)
            return True, f"Traditional pattern detection: {domain}", True

        # Medium confidence ML + WHOIS validation with provider hints
        if is_ml_suspicious and ml_confidence >= 50:
            return self._handle_medium_confidence_ml(domain, registered_domain, ml_confidence, ml_reasons, sender_provider)

        # Traditional suspicious patterns + WHOIS with provider context
        if is_suspicious_domain_pattern(domain):
            return self._handle_traditional_suspicious(domain, registered_domain, sender_provider)

        return False, "Normal domain pattern", False

    def _handle_medium_confidence_ml(self, domain, registered_domain, ml_confidence, ml_reasons, sender_provider):
        """Handle medium confidence ML results with provider-aware WHOIS validation"""
        try:
            import whois
            whois_available = True
        except ImportError:
            whois_available = False

        if not whois_available:
            # Provider-specific confidence adjustments when WHOIS unavailable
            adjusted_threshold = 60
            if sender_provider in ['icloud', 'gmail', 'outlook']:
                adjusted_threshold = 65  # Be more careful with major providers

            if ml_confidence >= adjusted_threshold:
                reason_str = "; ".join(ml_reasons[:2])
                provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
                self.log(f"DOMAIN VALIDATION: ML Medium-High Confidence ({ml_confidence}%) + No WHOIS - ALLOWING DELETION: {domain}{provider_note} - {reason_str}", False)
                return True, f"ML Medium-High Confidence ({ml_confidence}%): {reason_str}", True
            else:
                self.log(f"DOMAIN VALIDATION: ML Medium Confidence ({ml_confidence}%) but WHOIS unavailable - PRESERVING: {domain}", False)
                return False, f"ML suspicious ({ml_confidence}%) but WHOIS unavailable - preserved", True

        # Use cached domain validation for performance
        try:
            from domain_cache import cached_domain_validation
            validation_result, cache_reason, cache_is_suspicious = cached_domain_validation(
                registered_domain, provider_hint=sender_provider
            )
        except ImportError:
            # Fallback to direct validation if cache unavailable
            validation_result = lightweight_domain_validation(registered_domain, provider_hint=sender_provider)
        
        reason_str = "; ".join(ml_reasons[:2])

        if validation_result == 'SAFE':
            provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
            self.log(f"DOMAIN VALIDATION: ML suspicious ({ml_confidence}%) but established domain - NOT DELETING: {registered_domain}{provider_note}", False)
            return False, f"ML suspicious ({ml_confidence}%) but domain age > 90 days: {registered_domain}", True
        elif validation_result == 'QUARANTINE':
            self.log(f"DOMAIN VALIDATION: ML suspicious ({ml_confidence}%) and young domain - NOT DELETING for manual review: {registered_domain}", False)
            return False, f"ML suspicious ({ml_confidence}%) and young domain - manual review needed: {registered_domain}", True
        else:
            provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
            self.log(f"DOMAIN VALIDATION: ML suspicious ({ml_confidence}%) and very new domain - ALLOWING DELETION: {registered_domain}{provider_note} - {reason_str}", False)
            return True, f"ML suspicious ({ml_confidence}%) and very new domain: {reason_str}", True

    def _handle_traditional_suspicious(self, domain, registered_domain, sender_provider):
        """Handle traditional suspicious patterns with provider-aware WHOIS validation"""
        try:
            import whois
            whois_available = True
        except ImportError:
            whois_available = False

        if not whois_available:
            provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
            self.log(f"DOMAIN VALIDATION: Traditional suspicious pattern but WHOIS unavailable - PRESERVING: {domain}{provider_note}", False)
            return False, f"Traditional suspicious pattern but WHOIS unavailable - preserved: {domain}", True

        # Use cached domain validation for performance
        try:
            from domain_cache import cached_domain_validation
            validation_result, cache_reason, cache_is_suspicious = cached_domain_validation(
                registered_domain, provider_hint=sender_provider
            )
        except ImportError:
            # Fallback to direct validation if cache unavailable
            validation_result = lightweight_domain_validation(registered_domain, provider_hint=sender_provider)

        if validation_result == 'SAFE':
            provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
            self.log(f"DOMAIN VALIDATION: Traditional suspicious pattern but established domain - NOT DELETING: {registered_domain}{provider_note}", False)
            return False, f"Traditional suspicious pattern but domain age > 90 days: {registered_domain}", True
        elif validation_result == 'QUARANTINE':
            # Check if domain has obvious random character patterns that should be deleted regardless of age
            if self._is_obvious_spam_domain(registered_domain):
                provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
                self.log(f"DOMAIN VALIDATION: Traditional suspicious pattern with obvious random characters - ALLOWING DELETION: {registered_domain}{provider_note}", False)
                return True, f"Traditional suspicious pattern with obvious spam domain: {registered_domain}", True
            else:
                self.log(f"DOMAIN VALIDATION: Traditional suspicious pattern and young domain - NOT DELETING for manual review: {registered_domain}", False)
                return False, f"Traditional suspicious pattern and young domain - manual review needed: {registered_domain}", True
        else:
            provider_note = f" [Sender: {sender_provider}]" if sender_provider != 'unknown' else ""
            self.log(f"DOMAIN VALIDATION: Traditional suspicious pattern and very new domain - ALLOWING DELETION: {registered_domain}{provider_note}", False)
            return True, f"Traditional suspicious pattern and very new domain (< 30 days): {registered_domain}", True

    def _is_obvious_spam_domain(self, domain):
        """Detect domains with obvious random character patterns that should always be deleted"""
        if not domain:
            return False
        
        # Extract the main domain part (before first dot)
        main_part = domain.split('.')[0] if '.' in domain else domain
        
        # Patterns that indicate obvious spam domains
        obvious_spam_patterns = [
            # Long strings of mixed random characters (like 3smcu1z70u)
            re.search(r'^[a-z0-9]{10,}$', main_part) and len(set(main_part)) > 6,
            
            # Mixed case random patterns (like kImydULGAAGkZAlFAATJhVkUFL) 
            re.search(r'[A-Z]{2,}[a-z]{2,}[A-Z]{2,}', main_part) and len(main_part) > 15,
            
            # Domains that are mostly numbers mixed with letters
            len(re.findall(r'[0-9]', main_part)) > len(main_part) * 0.4 and len(main_part) > 8,
            
            # Very long random-looking strings
            len(main_part) > 20 and not re.search(r'[aeiou]{2,}', main_part.lower()),
            
            # Alternating character patterns that look generated
            re.search(r'[a-z][0-9][a-z][0-9][a-z][0-9]', main_part),
        ]
        
        return any(obvious_spam_patterns)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def decode_header_value(header_val):
    """
    Enhanced decode email header values ensuring ALWAYS decoded output
    Handles various encodings with bulletproof fallback mechanisms
    """
    if not header_val:
        return ""
    
    # If already a string, check if it needs additional decoding
    if isinstance(header_val, str):
        # Check if string contains encoded patterns that need decoding
        if '=?' in header_val and '?=' in header_val:
            # Try to decode encoded patterns within string
            try:
                # Re-process through decode_header in case it's encoded string
                decoded_parts = decode_header(header_val)
                decoded_string = ""
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        decoded_string += _decode_bytes_part(part, encoding)
                    else:
                        decoded_string += str(part)
                return decoded_string.strip()
            except Exception:
                # If re-processing fails, return original string
                pass
        return header_val.strip()

    # Handle non-string input (bytes, Header objects, etc.)
    try:
        decoded_parts = decode_header(header_val)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += _decode_bytes_part(part, encoding)
            else:
                decoded_string += str(part)
        return decoded_string.strip()
    except Exception as e:
        # Bulletproof fallback: convert to string and attempt manual decoding
        try:
            str_val = str(header_val)
            # Try manual decoding for common patterns
            if '=?UTF-8?Q?' in str_val:
                # Manual Q-encoding decode
                import re
                def decode_q_part(match):
                    encoded = match.group(1)
                    result = encoded.replace('_', ' ')
                    result = re.sub(r'=([0-9A-F]{2})', lambda m: chr(int(m.group(1), 16)), result)
                    return result
                str_val = re.sub(r'=\?UTF-8\?Q\?([^?]+)\?=', decode_q_part, str_val)
            elif '=?UTF-8?B?' in str_val:
                # Manual B-encoding (Base64) decode
                import base64, re
                def decode_b_part(match):
                    try:
                        return base64.b64decode(match.group(1)).decode('utf-8', errors='replace')
                    except:
                        return match.group(0)  # Return original if decode fails
                str_val = re.sub(r'=\?UTF-8\?B\?([^?]+)\?=', decode_b_part, str_val)
            return str_val.strip()
        except:
            # Ultimate fallback: return safe string representation
            return str(header_val)[:500]  # Limit length for safety

def _decode_bytes_part(part, encoding):
    """Helper function to decode bytes part with comprehensive fallback"""
    if encoding is None or encoding.lower() in ['unknown-8bit', 'unknown', '8bit']:
        # Try common encodings in order of likelihood
        for fallback_encoding in ['utf-8', 'iso-8859-1', 'ascii', 'cp1252', 'latin1']:
            try:
                return part.decode(fallback_encoding, errors="ignore")
            except (UnicodeDecodeError, LookupError, AttributeError):
                continue
        # If all standard encodings fail, use replacement characters
        return part.decode('utf-8', errors="replace")
    else:
        try:
            return part.decode(encoding, errors="ignore")
        except (UnicodeDecodeError, LookupError, AttributeError):
            # Fallback chain for problematic encodings
            for fallback_encoding in ['utf-8', 'iso-8859-1', 'cp1252']:
                try:
                    return part.decode(fallback_encoding, errors="ignore")
                except:
                    continue
            # Ultimate fallback with replacement characters
            return part.decode('utf-8', errors="replace")

def should_delete_email(headers, filters):
    """Check if email should be deleted based on filter criteria"""
    headers_lower = headers.lower()
    for term in filters:
        if term in headers_lower:
            return True, f"Matched: {term}"
    return False, ""

# Export main classes and functions
__all__ = [
    'DomainValidator',
    'ml_domain_classification',
    'decode_header_value',
    'should_delete_email',
    'calculate_entropy',
    'count_real_words',
    'has_natural_vowel_pattern',
    'detect_keyboard_patterns',
    'analyze_character_distribution',
    'lightweight_domain_validation',
    'is_suspicious_domain_pattern',
    'detect_provider_from_sender',
    'is_major_email_provider',
    'get_provider_reputation_score',
    'looks_like_gibberish',
    'is_gibberish_email'
]