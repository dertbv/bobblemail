#!/usr/bin/env python3
"""
Spam Classifier - Comprehensive spam detection and classification logic
Provider-aware spam categorization with advanced pattern detection
Enhanced with encoded spam content analysis

Refactored to use classification_utils to break circular dependencies.
"""

import re
import email.header
from atlas_email.utils.domain_validator import detect_provider_from_sender
from atlas_email.models.database import db
from atlas_email.core.classification_utils import (
    is_legitimate_company_domain, is_community_email, is_transactional_email,
    is_account_notification, is_subscription_management, classify_encoded_spam_content,
    get_all_keywords_for_category, check_all_keywords, check_keywords_simple
)

# Import smart regex selector for optimal performance
try:
    from atlas_email.utils.smart_regex import smart_category_check, smart_category_count
    SMART_REGEX_AVAILABLE = True
    print("🧠 Spam Classifier: Using smart regex selection")
except ImportError:
    # Fallback to regex optimizer
    try:
        from atlas_email.utils.regex_optimizer import regex_optimizer, create_keyword_regex, analyze_spam_indicators
        REGEX_OPTIMIZER_AVAILABLE = True
        SMART_REGEX_AVAILABLE = False
        print("🚀 Spam Classifier: Using optimized regex patterns")
    except ImportError:
        REGEX_OPTIMIZER_AVAILABLE = False
        SMART_REGEX_AVAILABLE = False
        print("⚠️ Spam Classifier: Using standard keyword matching")

# ============================================================================
# DOMAIN ANALYSIS FUNCTIONS
# ============================================================================

def analyze_sender_domain_for_scam(sender):
    """Analyze sender domain for obvious scam patterns"""
    if not sender or '@' not in sender:
        return None
    
    try:
        domain = sender.split('@')[1].strip().replace('>', '').lower()
        
        # Check for obviously fake domains - ENHANCED
        fake_domain_patterns = [
            # Random character domains
            lambda d: len(re.findall(r'[a-z0-9]{8,}', d.split('.')[0])) > 0 and len(d.split('.')[0]) > 8,  # Lowered from 10 to 8
            # Suspicious TLDs with random subdomains  
            lambda d: d.endswith(('.us', '.tk', '.ml', '.ga', '.cf', '.info', '.biz')) and len(d.split('.')[0]) > 6,  # Lowered from 8 to 6
            # Mixed numbers and letters in weird patterns
            lambda d: bool(re.search(r'[0-9]{2,}[a-z]{2,}[0-9]{2,}', d)) or bool(re.search(r'[a-z]{2,}[0-9]{3,}[a-z]', d)),
            # Too many random characters
            lambda d: len(d.split('.')[0]) > 12 and not any(brand in d for brand in ['amazon', 'ebay', 'paypal', 'google', 'microsoft']),  # Lowered from 15 to 12
            # Shortened weird domains
            lambda d: len(d.split('.')[0]) < 4 and d.endswith(('.us', '.tk', '.ml', '.ga', '.cf')),  # Very short + suspicious TLD
            # Mix of consonants without vowels (common in spam)
            lambda d: len(re.findall(r'[bcdfghjklmnpqrstvwxyz]{4,}', d.split('.')[0])) > 0
        ]
        
        if any(pattern(domain) for pattern in fake_domain_patterns):
            return "Suspicious Domain"
            
    except:
        pass
    
    return None

def is_news_content(subject, sender, headers=""):
    """Detect legitimate news content to prevent false positives"""
    combined_text = f"{subject} {sender} {headers}".lower()
    
    # News content indicators
    news_patterns = [
        # News language patterns
        r'\b(breaking|urgent|live coverage|caught on camera|exclusive|footage|reveals?|exposed?)\b',
        r'\b(airstrike|bombing|attack|conflict|war|military|defense|security)\b',
        r'\b(president|prime minister|government|congress|senate|official|diplomat)\b',
        r'\b(israel|palestine|ukraine|russia|china|biden|trump|musk|congress)\b',
        # News organization patterns
        r'\b(news|report|media|journalist|correspondent|investigation)\b',
        # Legitimate news domains/sources
        r'@(news|media|report|times|post|herald|tribune|journal|press)\.com',
        r'@.*\.(news|media)$'
    ]
    
    # Exclude if multiple news indicators present
    news_score = sum(1 for pattern in news_patterns if re.search(pattern, combined_text))
    
    if news_score >= 2:  # Require at least 2 news indicators
        return True
    
    return False

def is_legitimate_billing_delivery(subject, sender, headers=""):
    """Detect legitimate billing and delivery emails that should be preserved"""
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    combined_text = f"{subject} {sender} {headers}".lower()
    
    # Legitimate billing/delivery domains (high confidence)
    trusted_billing_domains = [
        # Order/shipping specific domains
        'oes.macys.com',           # Macy's order/shipping
        'customerservice@oes.macys.com', 
        'orders.amazon.com',       # Amazon orders
        'shipping.amazon.com',     # Amazon shipping
        'digital-no-reply@amazon.com', # Amazon digital orders
        'auto-confirm@amazon.com', # Amazon confirmations
        'receipts@emails.macys.com', # Macy's receipts
        
        # Customer service domains
        'customerservice.target.com',
        'orders.kohls.com',
        'billing.petco.com',
        'orders.petco.com',
        
        # Legitimate service patterns
        'customerservice@',
        'billing@',
        'orders@',
        'shipping@'
    ]
    
    # Broader legitimate retail domains (medium confidence for transactional content)
    legitimate_retail_domains = [
        'emails.macys.com',
        'e.petco.com', 
        'e.kohls.com',
        'amazon.com',
        'apple.com',
        'insideapple.apple.com',
        'target.com',
        'email.target.com'
    ]
    
    # Known scam domain patterns to exclude
    scam_domain_patterns = [
        '.be', '.tk', '.ml', '.ga', '.cf',  # Suspicious TLDs
        'thebusinessengineer.net',         # Known scam pattern
        'thebusinessanalytica',            # Known scam pattern
        'brutele.be',                      # Suspicious domain
        'billing team',                    # Generic billing team (suspicious)
        'service desk',                    # Generic service desk (suspicious)
    ]
    
    # Billing/delivery keywords that indicate transactional content
    billing_keywords = [
        # Order management
        'order confirmation', 'order shipped', 'order status', 'order #', 'order number',
        'tracking number', 'tracking info', 'shipment', 'shipped', 'delivery confirmation',
        'out for delivery', 'delivered', 'package delivered',
        
        # Payment/billing  
        'payment confirmation', 'payment received', 'receipt', 'invoice #',
        'billing statement', 'account statement', 'subscription renewal',
        'membership renewal', 'auto-renewal',
        
        # Legitimate transactional phrases
        'thank you for your order', 'your recent purchase', 'order complete',
        'shipping confirmation', 'delivery update'
    ]
    
    # Check for scam domain patterns first (exclusion)
    has_scam_domain = any(pattern in sender_lower for pattern in scam_domain_patterns)
    if has_scam_domain:
        return False  # Immediately reject emails from known scam domains
    
    # Check for high-confidence trusted domains
    has_trusted_domain = any(domain in sender_lower for domain in trusted_billing_domains)
    
    # Check for legitimate retail domains
    has_retail_domain = any(domain in sender_lower for domain in legitimate_retail_domains)
    
    # Check for billing/delivery keywords
    has_billing_keywords = any(keyword in combined_text for keyword in billing_keywords)
    
    # Check for order/invoice number patterns
    has_order_numbers = bool(re.search(r'(order|invoice|tracking|receipt)[\s#:]*[a-zA-Z0-9]{6,}', combined_text))
    
    # Additional security check - exclude promotional language that indicates marketing
    has_promotional_language = any(promo in combined_text for promo in [
        'get $', 'save $', '% off', 'deal', 'sale', 'discount', 'offer expires', 'limited time'
    ])
    
    # Scoring system
    confidence_score = 0
    
    if has_trusted_domain:
        confidence_score += 0.8  # High confidence for dedicated order/billing domains
    elif has_retail_domain:
        confidence_score += 0.3  # Lower confidence for general retail domains (need more evidence)
    
    if has_billing_keywords:
        confidence_score += 0.4
        
    if has_order_numbers:
        confidence_score += 0.4  # Increased weight for order numbers
    
    # Additional checks for specific patterns
    if 'part of your order has shipped' in combined_text:
        confidence_score += 0.6  # Very specific transactional language
    
    if 'order confirmation' in combined_text and (has_trusted_domain or has_retail_domain):
        confidence_score += 0.5
        
    if 'receipt' in combined_text and (has_trusted_domain or has_retail_domain):
        confidence_score += 0.4
    
    # Penalize promotional language (reduces confidence for marketing emails)
    if has_promotional_language and not has_trusted_domain:
        confidence_score -= 0.3
    
    # Return True if confidence score indicates legitimate billing/delivery
    return confidence_score >= 0.7

# ============================================================================
# CUSTOM KEYWORDS FROM DATABASE
# ============================================================================

def get_custom_keywords_for_category(category):
    """Get custom keywords for a specific category from database, excluding auto_detected"""
    try:
        keywords = db.execute_query("""
            SELECT term, confidence_threshold FROM filter_terms 
            WHERE category = ? AND is_active = 1 AND category != 'auto_detected'
        """, (category,))
        return [(kw['term'], kw['confidence_threshold'] or 0.7) for kw in keywords]
    except:
        return []

def check_custom_keywords(text, category):
    """Check if text matches any custom keywords for the given category, return highest confidence"""
    if not text:
        return False, 0.0
    
    text_lower = text.lower()
    custom_keywords = get_custom_keywords_for_category(category)
    
    highest_confidence = 0.0
    found_match = False
    
    for term, confidence in custom_keywords:
        if term in text_lower:
            found_match = True
            if confidence > highest_confidence:
                highest_confidence = confidence
    
    return found_match, highest_confidence

# ============================================================================
# OPTIMIZED DATABASE KEYWORD FUNCTIONS
# ============================================================================

# Cache for keyword lookups to improve performance
_keyword_cache = {}

def count_keywords(text, category):
    """Count how many keywords from category match in text
    Enhanced with smart regex selection for optimal performance"""
    if not text:
        return 0
    
    # Use smart regex selector for optimal performance
    if SMART_REGEX_AVAILABLE:
        return smart_category_count(text, category)
    
    # Fallback to regex optimizer
    elif hasattr(globals(), 'REGEX_OPTIMIZER_AVAILABLE') and REGEX_OPTIMIZER_AVAILABLE:
        pattern = regex_optimizer.create_category_pattern(category)
        if pattern:
            return len(pattern.findall(text))
    
    # Fallback to standard keyword counting
    text_lower = text.lower()
    keywords = get_keywords_simple(category)
    return sum(1 for keyword in keywords if keyword in text_lower)

def check_domain_keywords(domain, category_suffix="_domains"):
    """Check domain against category-specific domain keywords"""
    if not domain:
        return False
    
    domain_lower = domain.lower()
    domain_category = f"{category_suffix}"
    keywords = get_keywords_simple(domain_category)
    return any(keyword in domain_lower for keyword in keywords)

# ============================================================================
# SPAM CLASSIFICATION
# ============================================================================

def classify_spam_type_legacy(headers, sender, subject, matched_term):
    """Legacy monolithic spam classification function - now replaced by KeywordProcessor"""
    headers_str = str(headers) if headers else ""
    headers_lower = headers_str.lower()
    subject_lower = str(subject).lower() if subject else ""
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

    # Check if this is a legitimate company domain for special handling
    is_legitimate_domain = is_legitimate_company_domain(domain)

    # Enhanced suspicious domain detection with legitimate company protection
    suspicious_domain = False
    
    # First check if it's a legitimate company domain - if so, not suspicious
    if not is_legitimate_domain:
        suspicious_domain = any([
            len(domain.split(".")[0]) > 15,
            domain.count(".") > 3,  # Allow more subdomains for legitimate companies
            any(char.isdigit() for char in domain.replace(".", "")) and len(domain.split(".")[0]) > 10,  # More lenient for numbered subdomains
            domain.endswith((".us", ".tk", ".ml", ".ga", ".cf")) and sender_provider == 'unknown',
        ])

        # Provider-specific adjustments for classification
        if sender_provider in ['icloud', 'gmail', 'outlook']:
            # Major providers have better spam filtering, so suspicious emails are more likely false positives
            # Adjust classification to be more conservative
            suspicious_domain = suspicious_domain and len(domain.split(".")[0]) > 20

    # Check both subject and headers for content analysis
    all_text = f"{subject_lower} {headers_lower}"

    # ENCODED SPAM CHECK - Enhanced with content analysis
    is_encoded = ("=?UTF-8?" in str(subject) or "����" in str(sender) or len(str(subject)) > 200)
    
    if is_encoded:
        # NEW: Attempt to decode and classify the content
        try:
            decoded_classification = classify_encoded_spam_content(headers, sender, subject)
            print(f"🔍 Encoded spam decoded as: {decoded_classification}")
            return decoded_classification
        except Exception as e:
            print(f"⚠️ Decoding failed: {e}, falling back to generic Encoded Spam")
            return "Encoded Spam"

    # DATABASE KEYWORDS CHECK - Check all categories for both custom and built-in keywords
    # Skip keyword matching for legitimate company domains to prevent false positives
    spam_categories = [
        'Financial & Investment Spam', 'Gambling Spam', 'Pharmaceutical Spam',
        'Social/Dating Spam', 'Business Opportunity Spam', 'Brand Impersonation',
        'Marketing Spam', 'Health Scam', 'Payment Scam', 'Adult Content Spam', 
        'Education/Training Spam', 'Real Estate Spam', 'Legal Settlement Scam'
    ]
    
    # Check all keywords (custom + built-in) from database first, excluding auto_detected category
    # Use confidence scoring to pick the best category match
    best_category = None
    best_confidence = 0.0
    category_matches = []
    
    # Only do keyword matching for non-legitimate domains or use higher confidence threshold for legitimate domains
    confidence_threshold = 0.9 if is_legitimate_domain else 0.5
    
    for category in spam_categories:
        found_keyword, confidence = check_all_keywords(all_text, category)
        if found_keyword and confidence >= confidence_threshold:  # Use higher threshold for legitimate domains
            category_matches.append((category, confidence))
            if confidence > best_confidence:
                best_confidence = confidence
                best_category = category
    
    # If we have category matches, handle ties by specificity
    if category_matches:
        # Find all categories with the highest confidence
        max_confidence = max(confidence for _, confidence in category_matches)
        top_categories = [category for category, confidence in category_matches if confidence == max_confidence]
        
        # If only one category has max confidence, return it
        if len(top_categories) == 1:
            return top_categories[0]
        
        # Tiebreaker: prefer more specific categories over generic ones
        specificity_order = [
            'Legal Settlement Scam', 'Brand Impersonation', 'Payment Scam', 
            'Pharmaceutical Spam', 'Health Scam', 'Adult Content Spam',
            'Gambling Spam', 'Education/Training Spam', 'Real Estate Spam',
            'Social/Dating Spam', 'Business Opportunity Spam', 
            'Financial & Investment Spam', 'Marketing Spam'
        ]
        
        # Return the most specific category among tied categories
        for specific_category in specificity_order:
            if specific_category in top_categories:
                return specific_category
        
        # Fallback: return first category if none found in specificity order
        return top_categories[0]
    
    # Special handling for legitimate domains - prevent aggressive categories but allow genuine spam detection
    if is_legitimate_domain:
        # Only check for extremely obvious spam patterns for legitimate domains
        if "=?UTF-8?" in str(subject) or "����" in str(sender) or len(str(subject)) > 200:
            return "Encoded Spam"
        
        # Skip most hardcoded classification for legitimate domains
        # Only return "Promotional Email" for legitimate company domains that don't match database keywords
        return "Promotional Email"
    
    # For non-legitimate domains, proceed with full keyword-based classification
    
    # Financial & Investment Spam Detection using database keywords
    if check_keywords_simple(all_text, "Financial & Investment Spam"):
        return "Financial & Investment Spam"

    # Check for investment domain patterns with provider context (using database keywords)
    investment_domains = [
        "invest", "trading", "forex", "crypto", "bitcoin", "finance", "wealth", "profit",
        "money", "rich", "capital", "fund", "market", "stock", "bond", "gold", "silver",
        "currency", "dollar", "euro", "yen", "pound", "economy", "financial"
    ]
    if any(investment_term in domain for investment_term in investment_domains) and sender_provider == 'unknown':
        return "Financial & Investment Spam"

    # Gambling Spam Detection using database keywords
    if check_keywords_simple(all_text, "Gambling Spam"):
        return "Gambling Spam"

    # Check for gambling domain patterns (only for unknown providers)
    gambling_domains = ["casino", "bet", "poker", "slots", "gambling", "lottery", "jackpot", "spin",
                        "win", "lucky", "fortune", "mega", "bonus", "odds", "game", "play"]
    if any(gambling_term in domain for gambling_term in gambling_domains) and sender_provider == 'unknown':
        return "Gambling Spam"

    # Legal Settlement Scam Detection using database keywords
    if check_keywords_simple(all_text, "Legal Settlement Scam"):
        return "Legal Settlement Scam"

    # Business Opportunity Spam Detection using database keywords
    if check_keywords_simple(all_text, "Business Opportunity Spam"):
        return "Business Opportunity Spam"

    # Education/Training Spam Detection using database keywords
    if check_keywords_simple(all_text, "Education/Training Spam"):
        return "Education/Training Spam"

    # Real Estate Spam Detection using database keywords
    if check_keywords_simple(all_text, "Real Estate Spam"):
        return "Real Estate Spam"

    # Adult Content Spam Detection using database keywords (count-based)
    adult_count = count_keywords(all_text, "Adult Content Spam")
    if adult_count >= 2 or any(explicit in all_text for explicit in ["xxx", "porn", "nude", "naked"]):
        return "Adult Content Spam"

    # Pharmaceutical Spam Detection using database keywords (count-based)
    pharma_count = count_keywords(all_text, "Pharmaceutical Spam")
    if pharma_count >= 2:
        return "Pharmaceutical Spam"

    # Payment Scam Detection using database keywords
    if check_keywords_simple(all_text, "Payment Scam"):
        # Check for scam indicators vs legitimate payment terms (using database keywords)
        payment_scam_triggers = [
            "act fast", "urgent payment", "immediate payment", "payment required", "overdue payment",
            "final notice", "last chance", "avoid legal action", "collection notice", "past due",
            "suspended account", "account closure", "payment failure", "declined payment",
            "verify payment", "confirm payment", "update payment", "payment issue", "billing error"
        ]
        if any(scam in all_text for scam in payment_scam_triggers):
            return "Payment Scam"
        return "Financial & Investment Spam"

    # Winner/Prize Detection - check subject for winner keywords
    winner_keywords = ["winner", "won", "prize", "reward", "congratulations", "selected", "claim"]
    if any(keyword in subject_lower for keyword in winner_keywords):
        # Double-check if it's gambling-related or investment-related winner spam
        if any(gambling_term in all_text for gambling_term in ["casino", "lottery", "jackpot", "slots", "bet"]):
            return "Gambling Spam"
        if any(investment_term in all_text for investment_term in ["investment", "trading", "crypto", "bitcoin", "stocks"]):
            return "Financial & Investment Spam"
        return "Fake Winner Scam"

    # Social/Dating Spam Detection using database keywords
    if check_keywords_simple(all_text, "Social/Dating Spam"):
        return "Social/Dating Spam"

    # Marketing Spam Detection using database keywords (count-based, requires 2+ indicators)
    marketing_spam_count = count_keywords(all_text, "Marketing Spam")
    if marketing_spam_count >= 2 and not is_legitimate_domain:
        return "Marketing Spam"

    # Provider-aware suspicious domain classification
    if suspicious_domain and sender_provider == 'unknown':
        return "Suspicious Domain"
    elif suspicious_domain and sender_provider in ['icloud', 'gmail', 'outlook']:
        # Be more lenient with major providers, only flag extremely suspicious domains
        if len(domain.split(".")[0]) > 25 or domain.count(".") > 4:
            return "Suspicious Domain"

    # Promotional Spam Detection using database keywords (should use Marketing Spam category)
    if check_keywords_simple(all_text, "Marketing Spam"):
        return "Promotional Spam"

    # For legitimate company domains, return a more neutral classification
    if is_legitimate_domain:
        return "Promotional Email"  # Less aggressive classification for legitimate companies
    
    return "Generic Spam"


def classify_spam_type(headers, sender, subject, matched_term=None):
    """
    Enhanced spam classification with provider awareness.
    
    This function has been refactored to use the new KeywordProcessor module
    for better maintainability and testability.
    
    Args:
        headers: Email headers
        sender: Email sender
        subject: Email subject  
        matched_term: Previously matched term (legacy parameter)
        
    Returns:
        Classified spam type string
    """
    # Import here to avoid circular imports
    from atlas_email.filters.keyword_processor import keyword_processor
    
    # Use the new modular keyword processor
    return keyword_processor.process_keywords(headers, sender, subject, matched_term)


# Export main function
__all__ = ['classify_spam_type', 'classify_spam_type_legacy']