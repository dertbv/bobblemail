#!/usr/bin/env python3
"""
Whitelist Domains Extractor
Extracts all whitelisted domains from the email filtering system
"""

import re

def extract_domains_from_file(filename):
    """Extract domains from a Python file"""
    domains = set()
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Find all quoted strings that look like domains
        domain_pattern = r"['\"]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})['\"]"
        matches = re.findall(domain_pattern, content)
        
        for match in matches:
            # Filter out obviously non-domain strings
            if ('.' in match and 
                not match.startswith('http') and 
                not match.startswith('www.') and
                len(match.split('.')) >= 2 and
                not match.endswith('.py') and
                not match.endswith('.json') and
                not match.endswith('.txt') and
                not match.endswith('.log')):
                domains.add(match.lower())
    
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    
    return domains

def categorize_domain(domain):
    """Categorize domains for better organization"""
    domain_lower = domain.lower()
    
    if domain_lower.endswith(('.gov', '.edu')):
        return 'Government & Education'
    elif any(x in domain_lower for x in ['amazon', 'walmart', 'target', 'costco', 'bestbuy', 'homedepot', 'lowes']):
        return 'Major Retailers'
    elif any(x in domain_lower for x in ['apple', 'google', 'microsoft', 'facebook', 'meta', 'twitter', 'linkedin']):
        return 'Technology Giants'
    elif any(x in domain_lower for x in ['chase', 'bank', 'wells', 'capital', 'citi', 'usaa', 'discover']):
        return 'Financial Services'
    elif any(x in domain_lower for x in ['netflix', 'spotify', 'disney', 'hulu', 'hbo', 'youtube']):
        return 'Entertainment & Streaming'
    elif any(x in domain_lower for x in ['nextdoor', 'facebook', 'instagram', 'pinterest', 'linkedin']):
        return 'Social & Community'
    elif any(x in domain_lower for x in ['verizon', 'att', 't-mobile', 'comcast', 'xfinity', 'spectrum']):
        return 'Telecom & Utilities'
    elif any(x in domain_lower for x in ['fedex', 'ups', 'usps', 'dhl']):
        return 'Shipping & Logistics'
    elif any(x in domain_lower for x in ['gmail', 'outlook', 'yahoo', 'icloud', 'hotmail']):
        return 'Email Providers'
    elif any(x in domain_lower for x in ['sendgrid', 'mailgun', 'mailchimp', 'constantcontact']):
        return 'Email Marketing Services'
    else:
        return 'Other Business Domains'

def main():
    print("🔍 EMAIL FILTERING SYSTEM - COMPREHENSIVE WHITELIST DOMAINS")
    print("=" * 80)
    
    # Files to check for domains
    files_to_check = [
        'spam_classifier.py',
        'domain_validator.py', 
        'keyword_processor.py',
        'two_factor_email_validator.py'
    ]
    
    all_domains = set()
    
    # Extract domains from each file
    for filename in files_to_check:
        print(f"📄 Extracting domains from {filename}...")
        file_domains = extract_domains_from_file(filename)
        all_domains.update(file_domains)
        print(f"   Found {len(file_domains)} domains")
    
    print(f"\n📊 TOTAL UNIQUE DOMAINS FOUND: {len(all_domains)}")
    print("=" * 80)
    
    # Categorize and display domains
    categorized = {}
    for domain in all_domains:
        category = categorize_domain(domain)
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(domain)
    
    # Sort categories and domains
    for category in sorted(categorized.keys()):
        domains = sorted(categorized[category])
        print(f"\n## {category} ({len(domains)} domains):")
        print("-" * 50)
        for domain in domains:
            print(f"  • {domain}")
    
    print(f"\n📋 SUMMARY:")
    print(f"Total Whitelisted Domains: {len(all_domains)}")
    for category in sorted(categorized.keys()):
        print(f"  • {category}: {len(categorized[category])} domains")

if __name__ == "__main__":
    main()
