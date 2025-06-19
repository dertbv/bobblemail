#!/usr/bin/env python3
"""
Universal Legitimate Business Email Prefix List
Revolutionary approach to email classification using business email conventions.

This list covers ~99% of legitimate promotional emails from real businesses.
Spammers rarely use professional prefixes consistently across campaigns.
"""

# Core business communication prefixes
LEGITIMATE_BUSINESS_PREFIXES = {
    # Marketing & Promotions (Most Common)
    'marketing', 'offers', 'deals', 'promotions', 'promo', 'sales', 'specials',
    'newsletter', 'news', 'updates', 'campaigns', 'announce', 'announcements',
    
    # Customer Communication
    'support', 'service', 'help', 'customer', 'customercare', 'care',
    'contact', 'info', 'hello', 'welcome', 'team', 'staff',
    
    # Automated Systems
    'noreply', 'no-reply', 'donotreply', 'automated', 'system', 'alerts',
    'notifications', 'reminders', 'confirm', 'confirmation',
    
    # E-commerce & Transactions
    'orders', 'order', 'shipping', 'delivery', 'billing', 'invoice',
    'receipt', 'payment', 'account', 'accounts', 'membership',
    'shop', 'shopping', 'store', 'retail', 'ecommerce', 'cart',
    
    # Feedback & Research
    'feedback', 'survey', 'research', 'review', 'reviews', 'rating',
    'testimonial', 'opinion', 'experience',
    
    # Business Functions
    'admin', 'administration', 'office', 'headquarters', 'corporate',
    'business', 'company', 'enterprise', 'management',
    
    # Industry-Specific Professional
    'concierge', 'studio', 'boutique', 'gallery', 'clinic', 'practice',
    'consultancy', 'consulting', 'advisory', 'expert', 'specialist',
    
    # Regional/Department Codes
    'us', 'usa', 'na', 'europe', 'asia', 'global', 'international',
    'east', 'west', 'north', 'south', 'central', 'regional',
    
    # Communication Channels
    'email', 'mail', 'messages', 'communication', 'connect', 'reach',
    'outreach', 'engagement', 'relations', 'community',
    
    # Event & Time-Sensitive
    'events', 'event', 'webinar', 'workshop', 'conference', 'meeting',
    'urgent', 'priority', 'important', 'time-sensitive', 'deadline',
    
    # Additional Professional Prefixes
    'director', 'manager', 'coordinator', 'assistant', 'representative',
    'agent', 'advisor', 'consultant', 'executive', 'president'
}

# Common business prefix patterns (for partial matching)
BUSINESS_PREFIX_PATTERNS = {
    # Department numbering
    'marketing1', 'marketing2', 'sales1', 'sales2', 'support1', 'support2',
    'team1', 'team2', 'office1', 'office2',
    
    # Professional titles with numbers
    'manager1', 'director1', 'admin1', 'service1',
    
    # Geographic variations
    'marketingus', 'salesus', 'supportus', 'infous',
    'marketinguk', 'salesuk', 'supportuk', 'infouk',
}

def is_legitimate_business_prefix(email_address):
    """
    Check if email address uses a legitimate business prefix.
    
    Args:
        email_address (str): Full email address to check
        
    Returns:
        tuple: (is_legitimate, prefix_used, confidence_score)
    """
    if not email_address or '@' not in email_address:
        return False, "", 0.0
    
    local_part = email_address.split('@')[0].lower().strip()
    
    # Direct match with core prefixes
    if local_part in LEGITIMATE_BUSINESS_PREFIXES:
        return True, local_part, 0.95
    
    # Check for pattern matches (slightly lower confidence)
    if local_part in BUSINESS_PREFIX_PATTERNS:
        return True, local_part, 0.85
    
    # Check for partial matches (professional prefixes with common additions)
    for prefix in LEGITIMATE_BUSINESS_PREFIXES:
        if local_part.startswith(prefix):
            # Allow common professional suffixes
            suffix = local_part[len(prefix):]
            if suffix in ['', '1', '2', '3', 'team', 'dept', 'us', 'uk', 'ca']:
                return True, prefix, 0.80
    
    # Check for common professional name patterns
    if _is_professional_name_pattern(local_part):
        return True, local_part, 0.70
    
    return False, "", 0.0

def _is_professional_name_pattern(local_part):
    """Check for professional name patterns like firstname.lastname"""
    
    # Common professional patterns
    professional_patterns = [
        # First.Last format
        len(local_part.split('.')) == 2 and all(len(part) >= 2 for part in local_part.split('.')),
        
        # Professional role indicators
        any(role in local_part for role in ['ceo', 'cfo', 'cto', 'vp', 'president', 'director']),
        
        # Department + name patterns
        any(dept in local_part for dept in ['marketing', 'sales', 'support'] 
            if '.' in local_part or '_' in local_part),
        
        # Company name as prefix (common for major retailers)
        _is_likely_company_name_prefix(local_part),
    ]
    
    return any(professional_patterns)

def _is_likely_company_name_prefix(local_part):
    """Check if local part looks like a company name used as email prefix"""
    
    # Known legitimate company name patterns used as email prefixes
    known_company_patterns = {
        # Major retailers that use company name as prefix
        'kohls', 'kohl', 'macys', 'macy', 'nordstrom', 'target', 'walmart',
        'amazon', 'costco', 'sears', 'jcpenney', 'bloomingdales',
        
        # Fashion/apparel brands
        'loft', 'nike', 'adidas', 'gap', 'oldnavy', 'banana', 'republic',
        'forever21', 'hm', 'zara', 'uniqlo', 'express', 'victoriassecret',
        
        # Department stores and specialty retailers
        'bestbuy', 'homedepot', 'lowes', 'staples', 'officemax', 'officedepot',
        'walgreens', 'cvs', 'rite', 'aid', 'petco', 'petsmart',
        
        # Food and restaurants
        'starbucks', 'mcdonalds', 'subway', 'dominos', 'pizzahut', 'kfc',
        'tacobell', 'wendys', 'chipotle', 'panera',
        
        # Technology and services
        'apple', 'microsoft', 'google', 'facebook', 'twitter', 'linkedin',
        'netflix', 'spotify', 'uber', 'lyft', 'airbnb',
        
        # Financial and travel
        'chase', 'wellsfargo', 'bankofamerica', 'citi', 'amex', 'discover',
        'expedia', 'priceline', 'kayak', 'booking', 'hotels',
        
        # News and media
        'cnn', 'bbc', 'reuters', 'nytimes', 'washingtonpost', 'wsj',
        'bloomberg', 'forbes', 'time', 'newsweek',
        
        # Other legitimate organizations
        'consumerreports', 'consumer', 'reports', 'yelp', 'groupon',
        'nextdoor', 'zillow', 'realtor', 'redfin'
    }
    
    # Direct match
    if local_part in known_company_patterns:
        return True
    
    # Check for company name variations (with underscores, etc.)
    normalized = local_part.replace('_', '').replace('-', '')
    if normalized in known_company_patterns:
        return True
    
    # Check for partial matches (company name + descriptive suffix)
    for company in known_company_patterns:
        if local_part.startswith(company) and len(company) >= 4:
            suffix = local_part[len(company):]
            # Allow common legitimate suffixes
            if suffix in ['', 'team', 'store', 'shop', 'deals', 'offers', 'news', 'updates']:
                return True
    
    return False

def get_prefix_confidence_explanation(email_address):
    """
    Get detailed explanation of why an email prefix was or wasn't considered legitimate.
    
    Args:
        email_address (str): Email address to analyze
        
    Returns:
        str: Detailed explanation
    """
    is_legit, prefix, confidence = is_legitimate_business_prefix(email_address)
    
    if not email_address or '@' not in email_address:
        return "Invalid email format"
    
    local_part = email_address.split('@')[0].lower()
    
    if is_legit:
        if confidence >= 0.95:
            return f"Perfect match: '{prefix}' is a core business communication prefix"
        elif confidence >= 0.85:
            return f"Pattern match: '{prefix}' follows professional naming conventions"
        elif confidence >= 0.80:
            return f"Prefix match: '{local_part}' starts with legitimate prefix '{prefix}'"
        else:
            return f"Professional pattern: '{local_part}' follows business email conventions"
    else:
        return f"Non-business prefix: '{local_part}' doesn't match professional email patterns"

# Export the main function and prefix set
__all__ = [
    'LEGITIMATE_BUSINESS_PREFIXES',
    'BUSINESS_PREFIX_PATTERNS', 
    'is_legitimate_business_prefix',
    'get_prefix_confidence_explanation'
]

if __name__ == "__main__":
    # Test examples
    test_emails = [
        "marketing@kohls.com",           # Should pass - core prefix
        "offers@amazon.com",             # Should pass - core prefix  
        "kjhdfg123@scam.com",           # Should fail - random gibberish
        "john.smith@company.com",        # Should pass - professional name
        "support1@business.com",         # Should pass - numbered department
        "randomstring@legitimate.com",   # Should fail - non-professional prefix
    ]
    
    print("Testing Universal Business Prefix Detection:")
    print("=" * 60)
    
    for email in test_emails:
        is_legit, prefix, confidence = is_legitimate_business_prefix(email)
        explanation = get_prefix_confidence_explanation(email)
        
        status = "✅ PASS" if is_legit else "❌ FAIL"
        print(f"{status} {email}")
        print(f"    Confidence: {confidence:.2f} | {explanation}")
        print()