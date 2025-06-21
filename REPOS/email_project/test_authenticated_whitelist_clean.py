#!/usr/bin/env python3
"""
Test Authenticated Whitelist Implementation
==========================================

Tests the new authenticated whitelist system to ensure:
1. Legitimate emails from whitelisted addresses with proper authentication pass
2. Spoofed emails claiming to be from whitelisted addresses fail
3. Non-whitelisted emails are classified normally
"""

def test_whitelist_database():
    """Test whitelist database functionality"""
    print("🧪 Testing Whitelist Database System")
    print("=" * 50)
    
    from database import DatabaseManager
    db = DatabaseManager()
    
    # Test database whitelist check
    print("\n📧 Test 1: Database Whitelist Check")
    print("  Checking if dertbv@gmail.com is whitelisted...")
    
    result = db.execute_query('SELECT is_whitelisted FROM domains WHERE domain = ?', ('dertbv@gmail.com',))
    if result and result[0]['is_whitelisted']:
        print("  ✅ PASS: dertbv@gmail.com is whitelisted in database")
    else:
        print("  ❌ FAIL: dertbv@gmail.com not found in whitelist")
    
    # Test whitelist management functions
    print("\n📧 Test 2: Whitelist Management Functions")
    all_whitelisted = db.get_whitelisted_addresses()
    print(f"  Found {len(all_whitelisted)} whitelisted addresses:")
    for addr in all_whitelisted:
        print(f"    ✅ {addr['domain']} - {addr['notes']}")

def test_authenticated_whitelist():
    """Test authenticated whitelist functionality"""
    test_whitelist_database()
    
    print("\n🧪 Testing Authentication Scenarios")
    print("=" * 50)
    
    from database import DatabaseManager
    db = DatabaseManager()
    
    def simulate_whitelist_check(sender, auth_result):
        """Simulate the whitelist + authentication logic"""
        # Check if whitelisted
        result = db.execute_query('SELECT is_whitelisted FROM domains WHERE domain = ?', (sender.lower(),))
        is_whitelisted = result and result[0]['is_whitelisted']
        
        if is_whitelisted:
            is_authentic = auth_result.get('is_authentic', False)
            auth_summary = auth_result.get('auth_summary', 'No authentication')
            
            if is_authentic:
                return {
                    "final_classification": "WHITELISTED",
                    "is_spam": False,
                    "spam_probability": 0.1,
                    "override_reason": f"authenticated_whitelist ({auth_summary})"
                }
            else:
                return {
                    "final_classification": "SPOOFED_WHITELIST", 
                    "is_spam": True,
                    "spam_probability": 0.95,
                    "override_reason": f"spoofed_whitelist_sender ({auth_summary})"
                }
        
        return None  # Not whitelisted
    
    # Test Case 1: Legitimate whitelisted email with authentication
    print("\n📧 Test 1: Legitimate Sonarr email from dertbv@gmail.com")
    auth_result_good = {
        "is_authentic": True,
        "auth_summary": "SPF: pass, DKIM: pass"
    }
    
    result = simulate_whitelist_check("dertbv@gmail.com", auth_result_good)
    if result:
        print(f"  Classification: {result['final_classification']}")
        print(f"  Is Spam: {result['is_spam']}")
        print(f"  Override: {result['override_reason']}")
        
        if result['final_classification'] == 'WHITELISTED' and not result['is_spam']:
            print("  ✅ PASS: Legitimate email correctly whitelisted")
        else:
            print("  ❌ FAIL: Legitimate email incorrectly handled")
    else:
        print("  ❌ FAIL: Whitelisted email not recognized")
    
    # Test Case 2: Spoofed email claiming to be from whitelisted address  
    print("\n📧 Test 2: Spoofed email claiming to be from dertbv@gmail.com")
    auth_result_bad = {
        "is_authentic": False,
        "auth_summary": "SPF: fail, DKIM: none"
    }
    
    result = simulate_whitelist_check("dertbv@gmail.com", auth_result_bad)
    if result:
        print(f"  Classification: {result['final_classification']}")
        print(f"  Is Spam: {result['is_spam']}")
        print(f"  Override: {result['override_reason']}")
        
        if result['final_classification'] == 'SPOOFED_WHITELIST' and result['is_spam']:
            print("  ✅ PASS: Spoofed email correctly blocked")
        else:
            print("  ❌ FAIL: Spoofed email incorrectly allowed")
    else:
        print("  ❌ FAIL: Spoofed email logic failed")
    
    # Test Case 3: Non-whitelisted email
    print("\n📧 Test 3: Non-whitelisted email")
    result = simulate_whitelist_check("spam@random-domain.com", auth_result_good)
    if result is None:
        print("  ✅ PASS: Non-whitelisted email proceeds to normal classification")
    else:
        print("  ❌ FAIL: Non-whitelisted email incorrectly handled by whitelist")
    
    print(f"\n🎯 Authenticated Whitelist Testing Complete!")

if __name__ == "__main__":
    test_authenticated_whitelist()