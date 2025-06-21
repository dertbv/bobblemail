#!/usr/bin/env python3
"""
Complete Vendor Integration Test

Tests the full integration of selective vendor filtering with the spam classification system.
"""

import sys
sys.path.append('.')

from keyword_processor import KeywordProcessor

def test_complete_vendor_integration():
    """Test the complete vendor filtering integration"""
    
    print("🧪 Testing Complete Vendor Integration...")
    print("=" * 60)
    
    # Initialize keyword processor
    keyword_processor = KeywordProcessor()
    
    # Test cases covering various scenarios
    test_cases = [
        # Chase Credit Card - Transactional (should preserve)
        {
            'sender': 'alerts@chase.com',
            'subject': 'Your Chase statement is ready',
            'headers': 'From: alerts@chase.com\nSubject: Your Chase statement is ready\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'Chase statement notification (transactional)'
        },
        
        # Chase Credit Card - Marketing (should filter as spam)
        {
            'sender': 'offers@chase.com',
            'subject': 'You\'re pre-approved for Chase Sapphire - Earn 60,000 bonus points!',
            'headers': 'From: offers@chase.com\nSubject: You\'re pre-approved for Chase Sapphire\nTo: user@example.com',
            'expected_action': 'filter',
            'expected_category_type': 'spam',
            'description': 'Chase marketing offer (promotional)'
        },
        
        # Amazon - Order confirmation (should preserve)
        {
            'sender': 'auto-confirm@amazon.com',
            'subject': 'Your order #123-456-789 has shipped',
            'headers': 'From: auto-confirm@amazon.com\nSubject: Your order has shipped\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'Amazon order confirmation (transactional)'
        },
        
        # Amazon - Product recommendations (should filter as marketing)
        {
            'sender': 'store-news@amazon.com',
            'subject': 'Recommended for you based on your browsing history',
            'headers': 'From: store-news@amazon.com\nSubject: Recommended for you\nTo: user@example.com',
            'expected_action': 'filter',
            'expected_category_type': 'spam',
            'description': 'Amazon product recommendations (marketing)'
        },
        
        # Target - Order status (should preserve)
        {
            'sender': 'orders@target.com',
            'subject': 'Your Target order is ready for pickup',
            'headers': 'From: orders@target.com\nSubject: Your order is ready for pickup\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'Target pickup notification (transactional)'
        },
        
        # Verizon - Bill notification (should preserve)
        {
            'sender': 'verizonwireless@vtext.com',
            'subject': 'Your Verizon bill is ready',
            'headers': 'From: verizonwireless@vtext.com\nSubject: Your bill is ready\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'Verizon bill notification (transactional)'
        },
        
        # Netflix - Billing (should preserve)
        {
            'sender': 'info@netflix.com',
            'subject': 'Your Netflix payment was successful',
            'headers': 'From: info@netflix.com\nSubject: Payment confirmation\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'Netflix payment confirmation (transactional)'
        },
        
        # Netflix - Content recommendations (should preserve - streaming default)
        {
            'sender': 'info@netflix.com',
            'subject': 'New shows you might like based on your viewing',
            'headers': 'From: info@netflix.com\nSubject: New shows recommended\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'Netflix content recommendations (marketing - but allowed for streaming)'
        },
        
        # Unknown vendor - Regular spam (should filter normally)
        {
            'sender': 'noreply@scamsite.com',
            'subject': 'URGENT: You won $1,000,000! Claim now!',
            'headers': 'From: noreply@scamsite.com\nSubject: You won money!\nTo: user@example.com',
            'expected_action': 'filter',
            'expected_category_type': 'spam',
            'description': 'Regular spam from unknown vendor'
        },
        
        # eBay - Transaction (should preserve)
        {
            'sender': 'ebay@reply.ebay.com',
            'subject': 'Your eBay purchase confirmation',
            'headers': 'From: ebay@reply.ebay.com\nSubject: Purchase confirmation\nTo: user@example.com',
            'expected_action': 'preserve',
            'expected_category_type': 'Trusted Domain',
            'description': 'eBay purchase confirmation (transactional)'
        }
    ]
    
    # Run tests
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['description']} ---")
        print(f"Sender: {test_case['sender']}")
        print(f"Subject: {test_case['subject']}")
        
        # Process email through keyword processor (with vendor integration)
        result = keyword_processor.process_keywords(
            test_case['headers'],
            test_case['sender'],
            test_case['subject']
        )
        
        print(f"Classification Result: {result}")
        
        # Determine actual action and category type
        if result.startswith("Trusted Domain"):
            actual_action = "preserve"
            actual_category_type = "Trusted Domain"
        elif result in ["Promotional Email"]:
            actual_action = "preserve"
            actual_category_type = "Promotional Email"
        else:
            actual_action = "filter"
            actual_category_type = "spam"
        
        print(f"Expected: {test_case['expected_action']} ({test_case['expected_category_type']})")
        print(f"Actual: {actual_action} ({actual_category_type})")
        
        # Check if test passed
        action_match = actual_action == test_case['expected_action']
        
        # For category type, be flexible about specific spam categories
        if test_case['expected_category_type'] == 'Trusted Domain':
            category_match = actual_category_type == 'Trusted Domain'
        elif test_case['expected_category_type'] == 'spam':
            category_match = actual_category_type not in ['Trusted Domain', 'Promotional Email']
        else:
            category_match = True  # Flexible for other categories
        
        if action_match and category_match:
            print("✅ Test PASSED")
            passed += 1
        else:
            print("❌ Test FAILED")
            if not action_match:
                print(f"   Action mismatch: expected {test_case['expected_action']}, got {actual_action}")
            if not category_match:
                print(f"   Category mismatch: expected {test_case['expected_category_type']}, got {actual_category_type}")
    
    print(f"\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Selective vendor filtering is working perfectly!")
    else:
        print(f"⚠️  {total - passed} tests failed. Review the integration.")
    
    # Show vendor filtering statistics
    try:
        from vendor_filter_integration import get_vendor_filtering_stats
        print(f"\n📈 Vendor Filtering Statistics:")
        stats = get_vendor_filtering_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            elif isinstance(value, list):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"📈 Could not retrieve statistics: {e}")

def test_edge_cases():
    """Test edge cases and error handling"""
    
    print(f"\n🔬 Testing Edge Cases...")
    print("=" * 40)
    
    keyword_processor = KeywordProcessor()
    
    edge_cases = [
        # Empty/None inputs
        {
            'sender': '',
            'subject': '',
            'headers': '',
            'description': 'Empty inputs'
        },
        
        # Malformed email addresses
        {
            'sender': 'invalid-email',
            'subject': 'Test subject',
            'headers': 'From: invalid-email\nSubject: Test',
            'description': 'Invalid email format'
        },
        
        # Very long inputs
        {
            'sender': 'test@' + 'a' * 100 + '.com',
            'subject': 'A' * 200,
            'headers': 'From: test@example.com\nSubject: ' + 'A' * 200,
            'description': 'Very long inputs'
        }
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\nEdge Case {i}: {test_case['description']}")
        try:
            result = keyword_processor.process_keywords(
                test_case['headers'],
                test_case['sender'],
                test_case['subject']
            )
            print(f"  Result: {result}")
            print("  ✅ Handled gracefully")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Complete Vendor Integration Test...")
    
    test_complete_vendor_integration()
    test_edge_cases()
    
    print(f"\n✅ Testing complete!")