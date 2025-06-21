#!/usr/bin/env python3
"""
Spam Classifier - Comprehensive spam detection and classification logic
Provider-aware spam categorization with advanced pattern detection
Enhanced with encoded spam content analysis
"""

import re
import email.header
from domain_validator import detect_provider_from_sender
from database import db

# Import smart regex selector for optimal performance
try:
    from smart_regex_selector import smart_category_check, smart_category_count
    SMART_REGEX_AVAILABLE = True
    print("🧠 Spam Classifier: Using smart regex selection")
except ImportError:
    # Fallback to regex optimizer
    try:
        from regex_optimizer import regex_optimizer, create_keyword_regex, analyze_spam_indicators
        REGEX_OPTIMIZER_AVAILABLE = True
        SMART_REGEX_AVAILABLE = False
        print("🚀 Spam Classifier: Using optimized regex patterns")
    except ImportError:
        REGEX_OPTIMIZER_AVAILABLE = False
        SMART_REGEX_AVAILABLE = False
        print("⚠️ Spam Classifier: Using standard keyword matching")

# ============================================================================
# ENCODED SPAM DECODING FUNCTIONS
# ============================================================================

def decode_utf8_headers(text):
    """Attempt to decode UTF-8 encoded headers and email content"""
    if not text:
        return ""
    
    decoded_parts = []
    text_str = str(text)
    
    try:
        # Handle email header encoding like =?UTF-8?B?...?= or =?UTF-8?Q?...?=
        if "=?UTF-8?" in text_str:
            decoded_header = email.header.decode_header(text_str)
            for part, encoding in decoded_header:
                if isinstance(part, bytes):
                    try:
                        decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                    except:
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    decoded_parts.append(str(part))
        else:
            decoded_parts.append(text_str)
            
    except Exception as e:
        # Fallback: just use the original text
        decoded_parts.append(text_str)
    
    return " ".join(decoded_parts).lower()

def extract_readable_fragments(subject, headers, sender):
    """Extract readable text fragments from potentially encoded content"""
    fragments = []
    
    # Combine all text sources
    all_sources = [str(subject), str(headers), str(sender)]
    
    for source in all_sources:
        if not source:
            continue
            
        # Extract words that are likely readable (basic Latin characters)
        readable_words = re.findall(r'[a-zA-Z]{3,}', source)
        fragments.extend(readable_words)
        
        # Extract potential URLs or domains
        urls = re.findall(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', source)
        fragments.extend(urls)
        
        # Extract numbers that might be significant (prices, percentages)
        numbers = re.findall(r'\$\d+|\d+%|\d+\.\d+', source)
        fragments.extend(numbers)
    
    return " ".join(fragments).lower()

def analyze_encoded_content_patterns(decoded_text, readable_fragments):
    """Analyze decoded content using the full 1,590 keyword database"""
    combined_text = f"{decoded_text} {readable_fragments}".lower()
    
    # Use the full database keywords with PROPER PRIORITY ORDER
    spam_categories = [
        'Phishing',  # HIGHEST PRIORITY - prize scams, credential theft, info harvesting
        'Payment Scam', 'Adult & Dating Spam', 'Health & Medical Spam',
        'Legal & Compensation Scams', 'Financial & Investment Spam', 'Gambling Spam',
        'Education/Training Spam', 'Real Estate Spam', 'Business Opportunity Spam',
        'Brand Impersonation', 'Marketing Spam'  # LOWEST PRIORITIES
    ]
    
    # UPDATED: Use priority order instead of highest score to ensure Phishing precedence
    for category in spam_categories:
        found_keyword, confidence = check_all_keywords(combined_text, category)
        if found_keyword and confidence >= 0.05:  # Very low threshold for encoded content
            return category
    
    return None

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

def is_community_email(subject, sender, headers=""):
    """Detect legitimate community/neighborhood emails (Nextdoor, local groups)"""
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    combined_text = f"{subject} {sender} {headers}".lower()
    
    # Community platform domains
    community_domains = [
        'nextdoor.com', 'email.nextdoor.com', 'ss.email.nextdoor.com',
        'rs.email.nextdoor.com', 'is.email.nextdoor.com', 'ms.email.nextdoor.com'
    ]
    
    # Check if from recognized community platform
    is_community_domain = any(domain in sender_lower for domain in community_domains)
    
    if is_community_domain:
        return True
    
    # REMOVED: Keyword-based detection to prevent spam exploitation
    # Only preserve emails from verified community domains
    return is_community_domain

def is_transactional_email(subject, sender, headers=""):
    """
    Detect legitimate transactional emails (receipts, confirmations, statements, shipping).
    These are essential business communications that should be preserved.
    """
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    combined_text = f"{subject} {sender} {headers}".lower()
    
    # High-confidence transactional keywords
    transactional_keywords = [
        # Receipt and billing - enhanced
        'your receipt', 'receipt from', 'invoice', 'billing statement', 'account statement',
        'financial statement', 'bank statement', 'monthly statement', 'quarterly statement',
        'payment confirmation', 'payment received', 'charge summary', 'transaction summary',
        
        # Order management
        'order confirmation', 'order shipped', 'order delivered', 'shipment notification',
        'tracking information', 'tracking number', 'delivery confirmation', 'package delivered',
        'shipping confirmation', 'your order has', 'order status', 'order #',
        
        # Legitimate business communications
        'thank you for your purchase', 'welcome to', 'account created', 'registration confirmation'
    ]
    
    # Check for transactional keywords
    has_transactional_keywords = any(keyword in combined_text for keyword in transactional_keywords)
    
    # Check for legitimate business email prefixes
    business_prefixes = [
        'receipts@', 'billing@', 'orders@', 'shipping@', 'notifications@',
        'security@', 'account@', 'noreply@', 'no-reply@', 'no_reply@', 'auto-confirm@',
        'customerservice@', 'support@', 'service@', 'info@'
    ]
    
    has_business_prefix = any(prefix in sender_lower for prefix in business_prefixes)
    
    # Check for order/invoice number patterns
    has_order_numbers = bool(re.search(r'(order|invoice|tracking|receipt)[\s#:]*[a-zA-Z0-9]{6,}', combined_text))
    
    # Exclude promotional language and spam patterns that indicate marketing rather than transactional
    promotional_exclusions = [
        'sale', 'discount', '% off', 'save $', 'deal', 'offer expires',
        'limited time', 'flash sale', 'clearance', 'special offer',
        'up to', 'starting at', 'as low as', 'free shipping on orders'
    ]
    
    # Exclude political/financial newsletter patterns that use transactional words out of context
    newsletter_spam_exclusions = [
        'trump', 'biden', 'zelensky', 'zelenskyy', 'putin', 'elon', 'musk',
        'shocking statement', 'find out what happened', 'global peace', 'crisis',
        'war', 'economic age', 'market insights', 'investment', 'trading',
        'financial newsletter', 'newsletter', 'daily report', 'economic report'
    ]
    
    has_promotional_language = any(promo in combined_text for promo in promotional_exclusions)
    has_newsletter_spam_patterns = any(pattern in combined_text for pattern in newsletter_spam_exclusions)
    
    # CRITICAL FIX: Block political/financial newsletters from being classified as transactional
    if has_newsletter_spam_patterns:
        return False  # Immediately reject as transactional - these are spam newsletters
    
    # Scoring system for transactional confidence
    confidence_score = 0
    
    if has_transactional_keywords:
        confidence_score += 0.6  # Strong indicator
    
    if has_business_prefix:
        confidence_score += 0.3  # Professional sender
    
    if has_order_numbers:
        confidence_score += 0.4  # Specific transaction reference
    
    # Check for legitimate domains (Apple, banks, major retailers for receipts/statements)
    # Extract domain from sender email
    domain = None
    if '@' in sender_lower:
        domain = sender_lower.split('@')[1].replace('>', '').strip()
    
    if domain and is_legitimate_company_domain(domain):
        confidence_score += 0.2
    
    # Penalize promotional language (reduces transactional confidence)
    if has_promotional_language:
        confidence_score -= 0.4
    
    # Return True if confidence indicates this is transactional
    return confidence_score >= 0.65  # Lowered threshold for strong keyword matches

def is_account_notification(subject, sender, headers=""):
    """
    Detect legitimate account notifications (security alerts, password resets, account updates).
    These are important account-related communications that should be preserved.
    """
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    combined_text = f"{subject} {sender} {headers}".lower()
    
    # Account security keywords
    security_keywords = [
        'password reset', 'password changed', 'security alert', 'suspicious activity',
        'login attempt', 'new device', 'unknown device', 'new sign-in', 'sign-in', 'login',
        'account access', 'unauthorized access', 'unusual activity',
        'verify your account', 'account verification', 'confirm your email',
        'two-factor authentication', '2fa', 'security code', 'verification code'
    ]
    
    # Account management keywords  
    account_keywords = [
        'account updated', 'profile changed', 'email changed', 'phone number updated',
        'address updated', 'payment method', 'credit card updated', 'account settings',
        'privacy settings', 'notification preferences', 'account suspended',
        'account locked', 'account disabled', 'reactivate account'
    ]
    
    # Service/subscription management
    service_keywords = [
        'subscription expired', 'membership ending', 'auto-renewal',
        'payment failed', 'update payment', 'billing issue', 'subscription cancelled',
        'service termination', 'account closure', 'final notice'
    ]
    
    all_keywords = security_keywords + account_keywords + service_keywords
    
    # Check for account notification keywords
    has_account_keywords = any(keyword in combined_text for keyword in all_keywords)
    
    # Check for legitimate account-related prefixes
    account_prefixes = [
        'security@', 'account@', 'notifications@', 'alerts@', 'noreply@',
        'no-reply@', 'support@', 'help@', 'admin@'
    ]
    
    has_account_prefix = any(prefix in sender_lower for prefix in account_prefixes)
    
    # Must be from legitimate domain for account notifications
    # Extract domain from sender email
    domain = None
    if '@' in sender_lower:
        domain = sender_lower.split('@')[1].replace('>', '').strip()
    
    is_legitimate_domain = domain and is_legitimate_company_domain(domain)
    
    # Confidence scoring
    confidence_score = 0
    
    if has_account_keywords:
        confidence_score += 0.7
    
    if has_account_prefix:
        confidence_score += 0.2
    
    if is_legitimate_domain:
        confidence_score += 0.3
    else:
        confidence_score -= 0.5  # Penalize unknown domains for account notifications
    
    return confidence_score >= 0.8  # Higher threshold for account notifications

def is_subscription_management(subject, sender, headers=""):
    """
    Detect legitimate subscription/service management emails (terms changes, service updates).
    These are important service communications that should be preserved.
    """
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    combined_text = f"{subject} {sender} {headers}".lower()
    
    # Service management keywords
    service_keywords = [
        'terms of service', 'privacy policy', 'user agreement', 'terms and conditions',
        'policy update', 'terms changing', 'terms are changing', 'service update', 'platform update',
        'new features', 'service improvement', 'maintenance notice', 'downtime',
        'data processing', 'gdpr', 'california privacy'
    ]
    
    # Subscription keywords
    subscription_keywords = [
        'subscription', 'membership', 'plan change', 'tier update', 'billing cycle',
        'auto-renewal', 'renewal notice', 'cancellation', 'unsubscribe instructions'
    ]
    
    all_keywords = service_keywords + subscription_keywords
    
    # Check for service management keywords
    has_service_keywords = any(keyword in combined_text for keyword in all_keywords)
    
    # Must be from legitimate COMPANY domain for service notifications
    # Extract domain from sender email
    domain = None
    if '@' in sender_lower:
        domain = sender_lower.split('@')[1].replace('>', '').strip()
    
    is_legitimate_domain = domain and is_legitimate_company_domain(domain)
    
    # CRITICAL SECURITY FIX: Block consumer email services for subscription management
    # Legitimate subscriptions come from company domains, not Gmail/Yahoo/Hotmail
    consumer_email_services = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com',
        'aol.com', 'icloud.com', 'protonmail.com', 'mail.com'
    ]
    
    is_consumer_email = domain and any(domain == service for service in consumer_email_services)
    
    # If it's from a consumer email service and claims to be subscription management, it's likely spam
    if is_consumer_email and has_service_keywords:
        # High suspicion of fake subscription scam
        return False
    
    # Confidence scoring for legitimate company domains only
    confidence_score = 0
    
    if has_service_keywords:
        confidence_score += 0.6
    
    if is_legitimate_domain and not is_consumer_email:
        confidence_score += 0.4
    else:
        confidence_score -= 0.6  # Penalize unknown/consumer domains heavily
    
    return confidence_score >= 0.8  # Higher threshold for service notifications

def classify_encoded_spam_content(headers, sender, subject):
    """Attempt to decode and classify encoded spam content"""
    
    # FIRST: Check for community emails (preserve neighborhood communications)
    if is_community_email(subject, sender, headers):
        return "Community Email"  # Preserve legitimate community communications
    
    # SECOND: Check for transactional emails (receipts, confirmations, statements)
    if is_transactional_email(subject, sender, headers):
        return "Transactional Email"  # Preserve legitimate business transactions
    
    # THIRD: Check for account notifications (security alerts, password resets)
    if is_account_notification(subject, sender, headers):
        return "Account Notification"  # Preserve important account communications
    
    # FOURTH: Check for subscription management (terms changes, service updates)
    if is_subscription_management(subject, sender, headers):
        return "Subscription Management"  # Preserve legitimate service notifications
    
    # FIFTH: Check for legitimate billing/delivery content (backward compatibility)
    if is_legitimate_billing_delivery(subject, sender, headers):
        return "Legitimate Billing/Delivery"  # Preserve legacy detection
    
    # SIXTH: Check for legitimate news content (prevent false positives)
    if is_news_content(subject, sender, headers):
        return None  # Skip spam classification for news content
    
    # SEVENTH: Check for user-protected patterns (highest priority)
    try:
        from keyword_processor import keyword_processor
        protected_result = keyword_processor.check_protected_patterns(sender, subject)
        if protected_result:
            return protected_result
    except Exception as e:
        print(f"Warning: Protection pattern check failed: {e}")
    
    # Strategy 0: Check domain first
    domain_suspicion = analyze_sender_domain_for_scam(sender)
    
    # Strategy 1: Decode UTF-8 headers
    decoded_subject = decode_utf8_headers(subject)
    decoded_headers = decode_utf8_headers(headers)
    decoded_sender = decode_utf8_headers(sender)
    
    # Strategy 2: Extract readable fragments
    readable_fragments = extract_readable_fragments(subject, headers, sender)
    
    # Strategy 3: Analyze patterns in decoded content
    decoded_text = f"{decoded_subject} {decoded_headers} {decoded_sender}"
    suspected_category = analyze_encoded_content_patterns(decoded_text, readable_fragments)
    
    # Strategy 4: Check for explicit patterns first
    explicit_patterns = ['fuck', 'sex', 'porn', 'xxx', 'adult', 'naked', 'erotic']
    if any(pattern in decoded_text.lower() or pattern in readable_fragments.lower() for pattern in explicit_patterns):
        return "Adult & Dating Spam"
    
    # Strategy 5: Check against existing keyword database
    if suspected_category:
        # Verify against our keyword database
        combined_content = f"{decoded_text} {readable_fragments}"
        found_keyword, confidence = check_all_keywords(combined_content, suspected_category)
        if found_keyword and confidence >= 0.2:  # Lower threshold for encoded content
            return suspected_category
    
    # Strategy 5: Check all categories with decoded content - PROPER PRIORITY ORDER
    spam_categories = [
        'Phishing',  # HIGHEST PRIORITY - prize scams, credential theft, info harvesting
        'Payment Scam', 'Adult & Dating Spam', 'Health & Medical Spam',
        'Legal & Compensation Scams', 'Financial & Investment Spam', 'Gambling Spam',
        'Education/Training Spam', 'Real Estate Spam', 'Business Opportunity Spam',
        'Brand Impersonation', 'Marketing Spam'  # LOWEST PRIORITIES
    ]
    
    combined_content = f"{decoded_text} {readable_fragments}"
    
    # UPDATED: Use category priority order instead of highest confidence
    # This ensures Phishing takes precedence over other categories
    for category in spam_categories:
        found_keyword, confidence = check_all_keywords(combined_content, category)
        if found_keyword and confidence >= 0.1:  # Even lower threshold for encoded content
            return category
    
    # No matches found - fallback to generic
    
    # Fallback: return generic spam (no "Encoded" prefix)
    return "Marketing Spam"

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

def get_all_keywords_for_category(category):
    """Get both custom and built-in keywords for a specific category from database, excluding auto_detected"""
    try:
        keywords = db.execute_query("""
            SELECT term, confidence_threshold FROM filter_terms 
            WHERE category = ? AND is_active = 1 AND category != 'auto_detected'
            ORDER BY 
                CASE WHEN created_by = 'user' THEN 1 ELSE 2 END,
                confidence_threshold DESC
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

def check_all_keywords(text, category):
    """
    ENHANCED: Context-aware keyword matching with intelligent thresholds
    
    Improvements:
    - Minimum word count requirements for single-word matches
    - Context weighting (multiple related keywords boost confidence)
    - Text length consideration
    - Keyword specificity scoring
    """
    if not text:
        return False, 0.0
    
    text_lower = text.lower()
    text_words = text_lower.split()
    all_keywords = get_all_keywords_for_category(category)
    
    matched_keywords = []
    total_confidence = 0.0
    
    # Find all matching keywords with their details (remove duplicates)
    seen_terms = set()
    for term, confidence in all_keywords:
        if term in text_lower and term not in seen_terms:
            seen_terms.add(term)
            keyword_length = len(term.split())
            keyword_specificity = len(term)  # Longer terms are more specific
            
            # ENHANCEMENT: Context exclusions for problematic keywords
            if category == "Financial & Investment Spam" and term == "stock":
                # Exclude "stock" when it's clearly about product inventory
                legitimate_commerce_patterns = [
                    "back in stock", "in stock", "out of stock", "low stock",
                    "stock up", "restock", "restocked", "stock alert"
                ]
                if any(pattern in text_lower for pattern in legitimate_commerce_patterns):
                    continue  # Skip this keyword - it's legitimate commerce
            
            # ENHANCEMENT: Penalize very short keywords that might be partial matches
            is_partial_match = False
            if len(term) <= 3 and keyword_length == 1:
                # Check if this short term appears as part of a larger word
                import re
                pattern = r'\b' + re.escape(term) + r'\b'
                if not re.search(pattern, text_lower):
                    # This is a partial match (e.g., "cam" in "scams")
                    is_partial_match = True
                    confidence = max(0.2, confidence * 0.3)  # Heavily penalize
            
            matched_keywords.append({
                'term': term,
                'confidence': confidence,
                'length': keyword_length,
                'specificity': keyword_specificity,
                'is_partial': is_partial_match
            })
    
    if not matched_keywords:
        return False, 0.0
    
    # ENHANCEMENT 1: Penalize single-word matches in short text
    if len(matched_keywords) == 1 and len(text_words) <= 3:
        single_match = matched_keywords[0]
        # If it's a very short/broad term, require more context
        if len(single_match['term']) <= 3 and single_match['length'] == 1:
            # Reduce confidence for short single-word matches like "cam", "win", etc.
            adjusted_confidence = max(0.3, single_match['confidence'] * 0.5)
            return True, adjusted_confidence
    
    # ENHANCEMENT 2: Multi-keyword context scoring
    if len(matched_keywords) > 1:
        # Multiple keywords = higher confidence through context
        base_confidence = max(k['confidence'] for k in matched_keywords)
        
        # Bonus for multiple matches (up to +0.3)
        multi_match_bonus = min(0.3, (len(matched_keywords) - 1) * 0.1)
        
        # Bonus for keyword specificity (longer terms)
        specificity_bonus = min(0.2, sum(k['specificity'] for k in matched_keywords) / 100)
        
        total_confidence = min(1.0, base_confidence + multi_match_bonus + specificity_bonus)
        return True, total_confidence
    
    # ENHANCEMENT 3: Single keyword with context consideration
    single_match = matched_keywords[0]
    base_confidence = single_match['confidence']
    
    # Boost confidence for longer, more specific terms
    if single_match['specificity'] >= 10:  # Multi-word or long terms
        context_bonus = min(0.2, single_match['specificity'] / 50)
        total_confidence = min(1.0, base_confidence + context_bonus)
    else:
        # For short terms, consider surrounding context
        total_confidence = base_confidence
    
    # ENHANCEMENT 4: Minimum confidence threshold
    # Don't flag content with very low confidence matches
    # More aggressive threshold for single-word matches
    min_threshold = 0.6 if len(text_words) <= 2 else 0.4
    if total_confidence < min_threshold:
        return False, 0.0
    
    return True, total_confidence

# ============================================================================
# OPTIMIZED DATABASE KEYWORD FUNCTIONS
# ============================================================================

# Cache for keyword lookups to improve performance
_keyword_cache = {}

def get_keywords_simple(category):
    """Get simple keyword list for a category (optimized for performance)"""
    if category in _keyword_cache:
        return _keyword_cache[category]
    
    try:
        keywords = db.execute_query("""
            SELECT term FROM filter_terms 
            WHERE category = ? AND is_active = 1
        """, (category,))
        keyword_list = [kw['term'] for kw in keywords]
        _keyword_cache[category] = keyword_list
        return keyword_list
    except:
        return []

def check_keywords_simple(text, category):
    """Simple keyword check - returns True if any keyword matches
    Enhanced with smart regex selection for optimal performance"""
    if not text:
        return False
    
    # Use smart regex selector for optimal performance
    if SMART_REGEX_AVAILABLE:
        return smart_category_check(text, category)
    
    # Fallback to regex optimizer
    elif hasattr(globals(), 'REGEX_OPTIMIZER_AVAILABLE') and REGEX_OPTIMIZER_AVAILABLE:
        pattern = regex_optimizer.create_category_pattern(category)
        if pattern:
            return bool(pattern.search(text))
    
    # Fallback to standard keyword matching
    text_lower = text.lower()
    keywords = get_keywords_simple(category)
    return any(keyword in text_lower for keyword in keywords)

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
# LEGITIMATE DOMAIN WHITELIST
# ============================================================================

def is_legitimate_company_domain(domain):
    """Check if domain belongs to a legitimate company"""
    if not domain:
        return False
        
    domain = domain.lower().strip()
    
    # Debug logging for domain checking
    
    # Major legitimate company domains and their subdomains
    legitimate_domains = {
        # E-commerce & Retail
        'amazon.com', 'amazon.co.uk', 'amazon.ca', 'amazon.de', 'amazon.fr',
        'walmart.com', 'target.com', 'costco.com', 'bestbuy.com', 'homedepot.com', 'homedepotcustomersupport.com', 'lowes.com',
        'etsy.com', 'shopify.com', 'wayfair.com',
        'chargriller.com', 'char-griller.com', 'ecobee.com',
        'skechers.com', 'emails.skechers.com', 'tacticaltraps.com',
        'internetbrandsauto.com', 'clublexus.com',
        
        # Financial Services
        'experian.com', 'equifax.com', 'transunion.com', 'creditkarma.com',
        'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'citi.com',
        'penfed.org', 'usaa.com', 'capitalone.com', 'discover.com',
        'americanexpress.com', 'visa.com', 'mastercard.com', 'robinhood.com',
        
        # Technology
        'apple.com', 'microsoft.com', 'google.com', 'facebook.com', 'meta.com',
        'twitter.com', 'linkedin.com', 'adobe.com', 'salesforce.com',
        'oracle.com', 'ibm.com', 'intel.com', 'nvidia.com', 'tesla.com',
        'samsung.com', 'bambulab.com', 'lectron.com', 'ev-lectron.com',
        'gazelle.com', 'schmidtbrothers.com', 'unraid.com', 'unraid.net',
        
        # Social & Community Platforms
        'nextdoor.com', 'email.nextdoor.com', 'ss.email.nextdoor.com', 
        'rs.email.nextdoor.com', 'is.email.nextdoor.com', 'ms.email.nextdoor.com',
        'facebookmail.com', 'pinterest.com',
        
        # Telecom & Utilities
        'verizon.com', 'att.com', 't-mobile.com', 'sprint.com', 'comcast.com',
        'xfinity.com', 'spectrum.com', 'directv.com', 'dish.com',
        'siriusxm.com', 'e.siriusxm.com',
        
        # Streaming & Entertainment
        'netflix.com', 'disney.com', 'hulu.com', 'hbo.com', 'paramount.com',
        'spotify.com', 'youtube.com', 'twitch.com', 'steam.com',
        
        # Government & Official
        'irs.gov', 'usps.com', 'fedex.com', 'ups.com', 'dhl.com',
        'socialsecurity.gov', 'medicare.gov',
        
        # Airlines & Travel
        'delta.com', 'united.com', 'american.com', 'southwest.com',
        'booking.com', 'expedia.com', 'hotels.com', 'airbnb.com',
        
        # Food & Services  
        'mcdonalds.com', 'starbucks.com', 'subway.com', 'doordash.com',
        'grubhub.com', 'ubereats.com', 'instacart.com',
        'firebirdswoodfiredgrill.com', 'firebirds.fbmta.com', 'firebirds.com',
        'seatgeek.com', 'zenni.com', 'zennioptical.com',
        
        # Home & Kitchen Products
        'hexclad.com', 'hexcladcookware.com', 'traegergrills.com',
        'yeti.com', 'oxo.com', 'cuisinart.com', 'kitchenaid.com', 'vitamix.com',
        
        # Home Improvement & Windows
        'andersenwindows.com', 'renewalbyandersen.com', 'pella.com',
        'milgard.com', 'marvin.com', 'jeldwen.com',
        
        # Safety & Emergency Equipment
        'lifevac.net', 'lifevac.com', 'first-aid-product.com', 'zoll.com',
        
        # Healthcare & Insurance
        'aetna.com', 'anthem.com', 'bluecross.com', 'humana.com',
        'unitedhealth.com', 'kaiserpermanente.org', 'inova.org',
        
        # Auto Services & Home Security
        'carshield.com', 'vivint.com', 'vivintinc.com',
        
        # Education & Non-profit
        'khanacademy.org', 'wikipedia.org', 'redcross.org', 'salvation.org',
        
        # Sports & Entertainment Companies
        'dcunited.com', 'indigo.ca', 'pledgebox.com', 'spiritedvirginia.com',
        
        # Additional E-commerce & Retail Domains
        'oldnavy.com', 'gap.com', 'bananarepublic.com', 'athleta.com',
        'nordstrom.com', 'nordstromrack.com', 'macys.com', 'bloomingdales.com',
        'kohls.com', 'jcpenney.com', 'dillards.com', 'saksfifthavenue.com',
        'loft.com',
        'rh.com', 'restorationhardware.com', 'williams-sonoma.com', 'potterybarn.com',
        
        # Clothing & Fashion Brands
        'nike.com', 'adidas.com', 'underarmour.com', 'puma.com', 'reebok.com',
        'lululemon.com', 'patagonia.com', 'northface.com', 'columbia.com',
        'rei.com', 'dickssportinggoods.com', 'footlocker.com', 'finishline.com',
        
        # Additional Tech & Services
        'dropbox.com', 'slack.com', 'zoom.us', 'github.com', 'atlassian.com',
        'mailchimp.com', 'constantcontact.com', 'surveymonkey.com',
        'squarespace.com', 'wix.com', 'godaddy.com', 'bluehost.com',
        'energysage.com',
        
        # Email Marketing Services
        'mailgun.com', 'sendgrid.com', 'mandrill.com', 'campaignmonitor.com',
        'aweber.com', 'getresponse.com', 'convertkit.com', 'activecampaign.com',
        
        # Apple Services & Pharmacy/Healthcare (added for security email fix)
        'icloud.com', 'me.com', 'mac.com',  # Apple email services
        'cvs.com', 'walgreens.com', 'riteaid.com', 'pharmacydirect.com',  # Pharmacy services
        
        # Major Email Providers (for account notifications)
        'gmail.com', 'googlemail.com', 'google.com',  # Google email services
        'outlook.com', 'hotmail.com', 'live.com', 'msn.com',  # Microsoft email services
        'yahoo.com', 'yahoomail.com', 'ymail.com',  # Yahoo email services
        'protonmail.com', 'aol.com', 'mail.com',  # Other major providers
        
        # Pet & Animal Care
        'petco.com', 'petsmart.com', 'chewy.com', 'petflow.com',
        
        # Media & News
        'consumerreports.org', 'nytimes.com', 'washingtonpost.com', 'wsj.com',
        'cnn.com', 'bbc.com', 'reuters.com', 'ap.org',
        
        # Retail Department Stores & Brands
        'bedbathandbeyond.com', 'jcrew.com', 'anntaylor.com', 'loft.com',
        'bananarepublic.com', 'gap.com', 'oldnavy.com', 'athleta.com',
        'alamodeintimates.com',  # A la mode intimates
        
        # Social Networks & Communication
        'facebookmail.com', 'facebookemail.com', 'instagrammail.com',
        'nextdoor.com', 'linkedin.com', 'twittermail.com',
        
        # Third-Party Email Marketing Services
        'qualtrics-survey.com', 'qualtrics.com', 'surveymonkey.com',
        'typeform.com', 'mailchimp.com', 'constantcontact.com',
        'campaignmonitor.com', 'aweber.com', 'getresponse.com',
        'convertkit.com', 'activecampaign.com', 'klaviyo.com',
        'omnisend.com', 'drip.com', 'sendinblue.com', 'mailerlite.com',
        
        # Email Infrastructure Services
        'sendgrid.com', 'mailgun.com', 'mandrill.com', 'postmarkapp.com',
        'sparkpost.com', 'ses.amazonaws.com', 'amazonses.com',
        
        # Survey & Feedback Services
        'locationrater.com', 'trustpilot.com', 'yelp.com', 'google.com',
        'surveyedapp.com', 'podium.com', 'birdeye.com',
        
        # Newsletter & Content Platforms
        'substack.com', 'medium.com', 'wordpress.com', 'blogger.com',
        'tumblr.com', 'ghost.org',
        
        # Additional Legitimate Business Domains
        'salesforce.com', 'hubspot.com', 'zendesk.com', 'freshworks.com',
        'intercom.com', 'drift.com', 'olark.com', 'livechat.com'
    }
    
    # Direct domain match
    if domain in legitimate_domains:
        return True
    
    # Check if it's a subdomain of a legitimate domain
    for legit_domain in legitimate_domains:
        if domain.endswith('.' + legit_domain):
            return True
    
    # Check for educational and government domains
    if domain.endswith(('.edu', '.gov', '.org')) and len(domain.split('.')) <= 3:
        return True
    
    # ENHANCEMENT: Intelligent business domain detection
    # Check for professional business domain patterns
    if _is_professional_business_domain(domain):
        return True
    
    return False

def _is_gibberish_domain_name(domain_name):
    """
    Detect if a domain name looks like gibberish (random characters).
    
    Enhanced detection for obvious random strings that should not be trusted as legitimate domains.
    """
    if not domain_name or len(domain_name) < 5:
        return False
    
    # Convert to lowercase for analysis
    name = domain_name.lower()
    
    # Pattern 1: Mixed case random patterns in original string
    mixed_case_random = bool(re.search(r'[A-Za-z]*[A-Z][a-z][A-Z]', domain_name))
    
    # Pattern 2: High digit-to-letter ratio with long strings
    letters = sum(1 for c in name if c.isalpha())
    digits = sum(1 for c in name if c.isdigit())
    if letters > 0:
        digit_ratio = digits / letters
        high_digit_ratio = digit_ratio > 0.15 and len(name) > 10
    else:
        high_digit_ratio = True  # All digits is suspicious
    
    # Pattern 3: Low vowel density (less than 20% vowels)
    vowels = sum(1 for c in name if c in 'aeiou')
    vowel_ratio = vowels / len(name) if len(name) > 0 else 0
    low_vowel_density = vowel_ratio < 0.2 and len(name) > 8
    
    # Pattern 4: Long consonant sequences (6+ consonants in a row)
    long_consonant_seq = bool(re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', name))
    
    # Pattern 5: Alternating number/letter patterns
    alternating_pattern = bool(re.search(r'[0-9][a-z][0-9][a-z]|[a-z][0-9][a-z][0-9]', name))
    
    # Pattern 6: Very long strings with no recognizable word parts
    if len(name) > 12:
        # Check for any common word fragments
        common_fragments = ['com', 'net', 'org', 'web', 'mail', 'shop', 'store', 'tech', 'soft', 'data', 'info', 'news']
        has_word_fragment = any(frag in name for frag in common_fragments)
        no_word_patterns = not has_word_fragment
    else:
        no_word_patterns = False
    
    # Pattern 7: Excessive character repetition
    char_counts = {}
    for char in name:
        if char.isalnum():
            char_counts[char] = char_counts.get(char, 0) + 1
    if char_counts:
        max_char_freq = max(char_counts.values())
        excessive_repetition = max_char_freq > len(name) * 0.3 and len(name) > 6
    else:
        excessive_repetition = False
    
    # Combine patterns - any 2+ indicators suggest gibberish
    indicators = [
        mixed_case_random,
        high_digit_ratio, 
        low_vowel_density,
        long_consonant_seq,
        alternating_pattern,
        no_word_patterns,
        excessive_repetition
    ]
    
    gibberish_score = sum(indicators)
    
    # Special case: extremely suspicious single indicators
    if mixed_case_random and len(domain_name) > 15:
        return True  # Long mixed-case strings are highly suspicious
    if long_consonant_seq and len(name) > 10:
        return True  # Long consonant sequences in long strings
    if alternating_pattern and len(name) > 10:
        return True  # Alternating patterns in long strings
    
    return gibberish_score >= 2  # 2 or more indicators = gibberish

def _is_professional_business_domain(domain):
    """
    INTELLIGENT DOMAIN TRUST DETECTION
    
    Detects legitimate business domains based on patterns rather than hardcoded lists.
    Uses professional naming conventions and structural analysis.
    """
    if not domain or len(domain) < 5:
        return False
    
    domain_lower = domain.lower()
    domain_parts = domain_lower.split('.')
    
    # Must be standard .com business domain
    if not domain_lower.endswith('.com') or len(domain_parts) < 2:
        return False
    
    # Extract main domain (remove subdomains like 'email.', 'newsletter.', etc.)
    if len(domain_parts) > 2 and domain_parts[0] in ['email', 'newsletter', 'news', 'marketing', 'promo', 'offers']:
        main_domain = '.'.join(domain_parts[1:])  # email.longhorn.com -> longhorn.com
    else:
        main_domain = domain_lower
    
    main_parts = main_domain.replace('.com', '').split('.')
    if not main_parts:
        return False
    
    company_name = main_parts[-1]  # Get the main company part
    
    # GIBBERISH DETECTION: Check for obvious random strings before trust scoring
    if _is_gibberish_domain_name(company_name):
        return False
    
    # PATTERN 1: Established business naming patterns
    business_patterns = [
        # Restaurant chains
        'steakhouse', 'restaurant', 'grill', 'kitchen', 'cafe', 'diner', 'pizza', 'burgers',
        # Retail chains  
        'store', 'shop', 'outlet', 'market', 'supply', 'depot', 'warehouse', 'center',
        # Service companies
        'insurance', 'financial', 'bank', 'credit', 'services', 'solutions', 'systems',
        # Hospitality
        'hotel', 'resort', 'inn', 'lodge', 'suites',
        # Healthcare
        'health', 'medical', 'dental', 'pharmacy', 'clinic',
        # Automotive
        'auto', 'motors', 'dealership', 'toyota', 'ford', 'honda', 'bmw'
    ]
    
    # Check if domain contains established business terms
    domain_text = main_domain.replace('.com', '')
    has_business_pattern = any(pattern in domain_text for pattern in business_patterns)
    
    # PATTERN 2: Professional domain structure
    # - Reasonable length (5-25 characters for company part)
    # - Not random/suspicious patterns
    # - Contains vowels (real words vs random strings)
    company_reasonable_length = 5 <= len(company_name) <= 25
    has_vowels = any(vowel in company_name for vowel in 'aeiou')
    not_suspicious = not any(suspicious in domain_lower for suspicious in [
        'temp', 'tmp', 'test', 'spam', 'fake', 'scam', 'phish', 'malware',
        '123', '456', '789', 'xxx', 'random', 'unknown', 'suspicious', 
        'domain', 'email', 'alert', 'notification', 'security'
    ])
    
    # PATTERN 3: Known legitimate company characteristics
    # Check for well-known company name patterns
    known_company_indicators = [
        # Major brands (partial matches to avoid hardcoding full list)
        'amazon', 'google', 'microsoft', 'apple', 'facebook', 'netflix', 'uber',
        'walmart', 'target', 'costco', 'homedepot', 'lowes', 'macys', 'nordstrom',
        'chase', 'wells', 'bofa', 'citi', 'discover', 'capital', 'amex',
        'verizon', 'tmobile', 'sprint', 'comcast', 'att',
        # Restaurant chains
        'mcdonalds', 'subway', 'starbucks', 'chipotle', 'dominos', 'pizzahut',
        'tacobell', 'kfc', 'burgerking', 'wendys', 'arbys', 'sonic',
        'olivegarden', 'applebees', 'chilis', 'outback', 'redlobster',
        'longhorn', 'texasroadhouse', 'cracker', 'dennys', 'ihop'
    ]
    
    has_known_brand = any(brand in company_name for brand in known_company_indicators)
    
    # FINAL DECISION: Multiple factors increase trust
    trust_score = 0
    
    if has_business_pattern:
        trust_score += 2  # Strong indicator
    if company_reasonable_length and has_vowels and not_suspicious:
        trust_score += 2  # Professional structure
    if has_known_brand:
        trust_score += 3  # Very strong indicator
    if len(domain_parts) <= 3:  # Not too many subdomains
        trust_score += 1
    
    # Require minimum trust score for legitimacy
    return trust_score >= 3

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
        
        # Debug logging for domain extraction

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
            # Remove the broad exclusion check that was too aggressive
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
    # Gambling domains moved to database
    gambling_domains = ["casino", "bet", "poker", "slots", "gambling", "lottery", "jackpot", "spin",
                        "win", "lucky", "fortune", "mega", "bonus", "odds", "game", "play"]
    if any(gambling_term in domain for gambling_term in gambling_domains) and sender_provider == 'unknown':
        return "Gambling Spam"

    # Legal Settlement Scam Detection (High Priority)

    # Legal Settlement Scam Detection using database keywords
    if check_keywords_simple(all_text, "Legal Settlement Scam"):
        return "Legal Settlement Scam"

    # Business Opportunity/MLM Detection

    # Business Opportunity Spam Detection using database keywords
    if check_keywords_simple(all_text, "Business Opportunity Spam"):
        return "Business Opportunity Spam"

    # Education/Training/Certification Detection

    # Education/Training Spam Detection using database keywords
    if check_keywords_simple(all_text, "Education/Training Spam"):
        return "Education/Training Spam"

    # Real Estate Detection

    # Real Estate Spam Detection using database keywords
    if check_keywords_simple(all_text, "Real Estate Spam"):
        return "Real Estate Spam"

    # Enhanced Adult Content Detection

    # Adult Content Spam Detection using database keywords (count-based)
    adult_count = count_keywords(all_text, "Adult Content Spam")
    if adult_count >= 2 or any(explicit in all_text for explicit in ["xxx", "porn", "nude", "naked"]):
        return "Adult Content Spam"

    # Enhanced Pharmaceutical/Health Detection

    # Pharmaceutical Spam Detection using database keywords (count-based)
    pharma_count = count_keywords(all_text, "Pharmaceutical Spam")
    if pharma_count >= 2:
        return "Pharmaceutical Spam"

    # Enhanced Payment Scam Detection

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

    # Winner/Prize Detection - check subject for winner keywords (using database keywords)
    # Winner keywords moved to database
    winner_keywords = ["winner", "won", "prize", "reward", "congratulations", "selected", "claim"]  # TODO: Move to database
    if any(keyword in subject_lower for keyword in winner_keywords):
        # Double-check if it's gambling-related or investment-related winner spam
        if any(gambling_term in all_text for gambling_term in ["casino", "lottery", "jackpot", "slots", "bet"]):
            return "Gambling Spam"
        if any(investment_term in all_text for investment_term in ["investment", "trading", "crypto", "bitcoin", "stocks"]):
            return "Financial & Investment Spam"
        return "Fake Winner Scam"

    # Enhanced Social/Dating Detection
    # Social/Dating Spam Detection using database keywords
    if check_keywords_simple(all_text, "Social/Dating Spam"):
        return "Social/Dating Spam"

    # Check for domain patterns for new categories (only for unknown providers)
    if sender_provider == 'unknown':
        # Business domains moved to database
        business_domains = [
            "opportunity", "income", "wealth", "profit", "earn", "money", "business",
            "mlm", "affiliate", "network", "marketing", "franchise", "work", "job"
        ]
        if any(business_term in domain for business_term in business_domains):
            return "Business Opportunity Spam"

        # Education domains moved to database
        education_domains = [
            "education", "learning", "course", "training", "certification", "degree",
            "university", "college", "school", "academy", "institute", "study"
        ]
        if any(education_term in domain for education_term in education_domains):
            return "Education/Training Spam"

        # Real estate domains moved to database
        real_estate_domains = [
            "realestate", "property", "homes", "house", "mortgage", "loan", "refinance",
            "foreclosure", "investment", "rental", "landlord", "realtor", "mls"
        ]
        if any(real_estate_term in domain for real_estate_term in real_estate_domains):
            return "Real Estate Spam"

        # Dating domains moved to database
        dating_domains = [
            "dating", "singles", "match", "meet", "chat", "love", "romance", "flirt",
            "hookup", "affair", "social", "friend", "connect", "relationship"
        ]
        if any(dating_term in domain for dating_term in dating_domains):
            return "Social/Dating Spam"

    # Enhanced Health Scam Detection
    # Health Scam Detection using database keywords
    if check_keywords_simple(all_text, "Health Scam"):
        return "Health Scam"

    # Marketing Spam Detection - Aggressive marketing from unknown sources
    
    # Marketing Spam Detection using database keywords (count-based, requires 2+ indicators)
    marketing_spam_count = count_keywords(all_text, "Marketing Spam")
    if marketing_spam_count >= 2 and not is_legitimate_domain:
        return "Marketing Spam"
    
    # Check for domain patterns that indicate marketing operations (only for unknown providers)
    if sender_provider == 'unknown':
        # Marketing domains moved to database
        marketing_domains = [
            "marketing", "promo", "offers", "deals", "sales", "campaign", "newsletter",
            "email", "mail", "blast", "direct", "bulk", "mass", "auto", "lead", "list"
        ]
        if any(marketing_term in domain for marketing_term in marketing_domains):
            return "Marketing Spam"

    # Marketing Email Detection - Legitimate promotional content from known brands
    if is_legitimate_domain:
        # Check for legitimate marketing email patterns from known companies
        # Marketing indicators moved to database
        marketing_indicators = [
            "unsubscribe", "newsletter", "promotional", "special offer", "sale",
            "discount", "new arrivals", "exclusive offer", "limited time",
            "free shipping", "customer", "member", "subscriber", "deals",
            "save", "% off", "clearance", "shop now", "browse", "collection",
            "seasonal", "holiday", "black friday", "cyber monday", "summer sale",
            "winter sale", "flash sale", "early bird", "pre-order", "launch",
            "announcement", "update", "news", "event", "webinar", "product",
            "catalog", "lookbook", "style guide", "rewards", "points",
            "loyalty program", "vip", "premium", "membership", "account"
        ]
        
        # Enhanced marketing detection - check both subject and content
        marketing_score = 0
        for indicator in marketing_indicators:
            if indicator in all_text:
                marketing_score += 1
        
        # If multiple marketing indicators present from legitimate domain, classify as marketing
        if marketing_score >= 2:
            return "Marketing Email"

    # Enhanced Brand Impersonation Detection with legitimate domain protection
    
    # Use the already-computed legitimate domain check
    if is_legitimate_domain:
        # This is a legitimate company domain, don't flag as brand impersonation
        pass  # Continue with other checks but skip brand impersonation
    else:
        # Only check for brand impersonation if domain is not legitimate
        # Using database keywords for brand impersonation detection

        # More targeted brand impersonation detection - only check sender domain, not content
        # Focus on actual impersonation attempts in sender addresses
        sender_domain_only = domain if domain else ""
        
        # Check for obvious brand impersonation patterns in sender addresses (not content)
        if sender_provider == 'unknown' and suspicious_domain:
            # Brand impersonation patterns moved to database
            brand_impersonation_patterns = [
                "noreply-", "no-reply", "notification-", "alert-", "security-", "account-",
                "support-", "service-", "billing-", "invoice-", "payment-", "verify-",
                "update-", "confirm-", "suspend-", "warning-", "urgent-"
            ]
            
            # Only flag if sender has impersonation patterns AND mentions a major brand in sender address
            if any(pattern in sender_lower for pattern in brand_impersonation_patterns):
                # Check only top 10 most commonly impersonated brands in sender address - using database keywords
                # Top impersonated brands moved to database
                top_impersonated_brands = [
                    "amazon", "apple", "microsoft", "google", "facebook", "paypal", 
                    "netflix", "bank", "chase", "wells fargo"
                ]
                if any(brand in sender_lower for brand in top_impersonated_brands):
                    return "Brand Impersonation"
            
            # Check for obvious fake domain impersonation (brand name in domain with suspicious TLD)
            for brand in top_impersonated_brands:
                if brand in sender_domain_only and any(ext in sender_domain_only for ext in [".tk", ".ml", ".ga", ".cf", ".us"]):
                    return "Brand Impersonation"

    # Emoji Spam Detection (Cash App, reward scams with excessive emojis)
    # Common scam emojis and patterns
    # Scam emojis moved to database
    scam_emojis = [
        "💲", "💰", "💵", "💴", "💶", "💷", "🤑", "💳", "💎", "🎁", "🎉", "🎊",
        "🔥", "⚡", "✨", "🌟", "⭐", "🏆", "🎯", "🚀", "📈", "📊", "👑", "💯",
        "🎪", "🎭", "🎨", "🎬", "🎮", "🕹️", "🎲", "🃏", "🎰", "🎱", "🏅", "🥇"
    ]

    # Count emojis in subject and all text
    emoji_count = 0
    scam_emoji_count = 0

    # Use regex to find all emojis (Unicode emoji ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002600-\U000027BF"  # misc symbols
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "]+",
        flags=re.UNICODE
    )

    emojis_found = emoji_pattern.findall(all_text)
    emoji_count = len(emojis_found)

    # Count specific scam emojis
    for emoji in scam_emojis:
        scam_emoji_count += all_text.count(emoji)

    # Scam phrases commonly used with emojis
    # Emoji scam phrases moved to database
    emoji_scam_phrases = [
        "cash app", "cashapp", "claim your", "claim now", "free money", "easy money",
        "instant cash", "quick cash", "reward now", "get paid", "earn money",
        "$1000", "$500", "$100", "thousand", "hundred", "dollars", "cash reward",
        "gift card", "amazon gift", "walmart gift", "target gift", "itunes gift",
        "google play", "steam card", "paypal money", "venmo money", "zelle money",
        "act now", "limited time", "expires today", "hurry up", "don't wait",
        "congratulations", "you've won", "winner", "selected", "chosen",
        "click here", "tap here", "swipe up", "link in bio", "dm for details"
    ]

    # Check for emoji spam patterns
    if emoji_count >= 3 and any(phrase in all_text for phrase in emoji_scam_phrases):
        return "Emoji Scam Spam"
    elif scam_emoji_count >= 2:
        return "Emoji Scam Spam"
    elif emoji_count >= 5 and any(keyword in all_text for keyword in ["money", "cash", "reward", "free", "win", "claim"]):
        return "Emoji Scam Spam"

    # Provider-aware suspicious domain classification
    if suspicious_domain and sender_provider == 'unknown':
        return "Suspicious Domain"
    elif suspicious_domain and sender_provider in ['icloud', 'gmail', 'outlook']:
        # Be more lenient with major providers, only flag extremely suspicious domains
        if len(domain.split(".")[0]) > 25 or domain.count(".") > 4:
            return "Suspicious Domain"

    # Enhanced Promotional Detection
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
    from keyword_processor import keyword_processor
    
    # Use the new modular keyword processor
    return keyword_processor.process_keywords(headers, sender, subject, matched_term)


# Export main function
__all__ = ['classify_spam_type', 'classify_spam_type_legacy']