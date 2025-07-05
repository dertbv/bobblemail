#!/usr/bin/env python3
"""
Strategic Integration Threshold Optimization
Find optimal confidence threshold for <1% Strategic Framework usage
"""

import time
from strategic_integration_test import StrategicIntegrationTester

def test_threshold_optimization():
    """Test different confidence thresholds to find optimal setting"""
    
    print("🎯 Strategic Integration Threshold Optimization")
    print("=" * 60)
    print("Finding optimal threshold for <1% Strategic Framework usage\n")
    
    # Test cases representing realistic email distribution
    realistic_test_cases = [
        # 80% should be obvious spam (Tier 1)
        ("fuck@spam.cn", "XXX Adult Content", "", ""),
        ("winner@lottery.tk", "You won! Claim prize now!", "", ""),
        ("pills@pharma.ru", "Viagra discount 90% off", "", ""),
        ("casino@gambling.ml", "Win big at our casino!", "", ""),
        ("scam@gibberish123.com", "Make money fast!", "", ""),
        ("phishing@bank-fake.com", "Account suspended! Verify now!", "", ""),
        ("dating@hookup.info", "Hot singles in your area", "", ""),
        ("investment@get-rich.biz", "Secret trading strategy", "", ""),
        
        # 15% should be fast geographic/pattern detection (Tier 2)
        ("business@normalsite.com", "Investment opportunity", "Received: from [103.45.123.45]", ""),
        ("sender@example.org", "Business proposal", "Received: from [45.67.89.10]", ""),
        ("info@company.net", "Partnership opportunity", "Received: from [185.220.101.42]", ""),
        
        # 5% uncertain cases that might need Strategic analysis
        ("support@questionable-bank.com", "Account verification", "", "Chase Support"),
        ("reply@ss.email.nextdoor.com", "Hello neighbor", "", "Nextdoor"),
        ("noreply@brand-like.org", "Important update", "", "Microsoft Team"),
        ("service@auth-portal.net", "Security alert", "", "Apple Support"),
        ("notifications@social-updates.com", "New message", "", "Facebook"),
        
        # Add more obvious spam to get realistic distribution
        ("adult@xxx.tk", "Live webcam shows", "", ""),
        ("lottery@win.ml", "Mega jackpot winner", "", ""),
        ("crypto@pump.ru", "Bitcoin millionaire secrets", "", ""),
        ("pills@meds.cn", "Weight loss miracle", "", ""),
    ]
    
    # Test different confidence thresholds
    thresholds_to_test = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]
    
    results = []
    
    for threshold in thresholds_to_test:
        print(f"Testing threshold: {threshold:.2f}")
        
        tester = StrategicIntegrationTester(confidence_threshold=threshold)
        
        strategic_count = 0
        total_time = 0
        
        for sender, subject, headers, sender_name in realistic_test_cases:
            result = tester.classify_email(sender, subject, headers, sender_name)
            if result.tier_used.value == "TIER_3_STRATEGIC":
                strategic_count += 1
            total_time += result.processing_time_ms
        
        stats = tester.get_stats()
        strategic_percent = float(stats['tier_3_strategic'].replace('%', ''))
        
        results.append({
            'threshold': threshold,
            'strategic_percent': strategic_percent,
            'strategic_count': strategic_count,
            'total_cases': len(realistic_test_cases),
            'avg_time_ms': total_time / len(realistic_test_cases),
            'within_target': strategic_percent < 1.0
        })
        
        status = "✅" if strategic_percent < 1.0 else "❌"
        print(f"  Strategic usage: {strategic_percent:.1f}% ({strategic_count}/{len(realistic_test_cases)}) {status}")
        print(f"  Avg processing time: {total_time / len(realistic_test_cases):.2f}ms\n")
    
    # Find optimal threshold
    print("📊 Threshold Optimization Results")
    print("=" * 50)
    print(f"{'Threshold':<10} {'Strategic%':<12} {'Count':<8} {'Target':<8} {'Avg Time':<10}")
    print("-" * 50)
    
    optimal_threshold = None
    
    for result in results:
        status = "✅" if result['within_target'] else "❌"
        print(f"{result['threshold']:<10.2f} {result['strategic_percent']:<12.1f} "
              f"{result['strategic_count']:<8} {status:<8} {result['avg_time_ms']:<10.2f}ms")
        
        # Find the lowest threshold that meets the target
        if result['within_target'] and optimal_threshold is None:
            optimal_threshold = result['threshold']
    
    print("\n🎯 Optimization Summary")
    print("=" * 30)
    
    if optimal_threshold:
        print(f"✅ Optimal threshold found: {optimal_threshold:.2f}")
        print(f"✅ Achieves <1% Strategic Framework usage")
        print(f"✅ Preserves fast processing for 99%+ of emails")
        
        # Test the optimal threshold with edge cases
        print(f"\n🧪 Testing optimal threshold ({optimal_threshold:.2f}) with edge cases:")
        
        edge_cases = [
            ("reply@ss.email.nextdoor.com", "Hello.", "", "Sugarland Run"),
            ("support@chase-security.org", "Account verification", "", "Chase Bank"),
            ("noreply@apple-id.net", "Security alert", "", "Apple Support")
        ]
        
        optimal_tester = StrategicIntegrationTester(confidence_threshold=optimal_threshold)
        
        for sender, subject, headers, sender_name in edge_cases:
            result = optimal_tester.classify_email(sender, subject, headers, sender_name)
            tier_status = "🔍 Strategic" if result.tier_used.value == "TIER_3_STRATEGIC" else "⚡ Fast"
            print(f"  {sender}: {tier_status} ({result.confidence:.2f})")
    
    else:
        print("❌ No threshold achieves <1% target with current test cases")
        print("💡 Recommendation: Improve fast classification rules")
        print("💡 Alternative: Use threshold 0.80+ for production")
    
    return optimal_threshold

def generate_production_config(optimal_threshold):
    """Generate production configuration"""
    
    config = f"""
# Strategic Integration Production Configuration
# Auto-generated from threshold optimization

STRATEGIC_INTEGRATION_CONFIG = {{
    # Conditional trigger threshold for Tier 3 Strategic analysis
    'confidence_threshold': {optimal_threshold:.2f},
    
    # Performance targets
    'target_strategic_usage_percent': 1.0,  # <1% of emails
    'target_fast_processing_percent': 99.0,  # ≥99% fast processing
    
    # Tier definitions
    'tier_1_instant': [
        'Adult & Dating Spam',
        'Domain Spam', 
        'Geographic Spam'
    ],
    
    'tier_2_geographic': [
        'IP-based detection',
        'Suspicious ranges',
        'Country risk analysis'
    ],
    
    'tier_3_strategic': [
        'Brand impersonation edge cases',
        'Nextdoor misclassifications',
        'Uncertain authentication cases'
    ],
    
    # Fallback behavior
    'graceful_degradation': True,
    'fallback_to_fast_on_error': True,
    'max_strategic_processing_time_ms': 5000,
    
    # Monitoring
    'track_tier_usage': True,
    'performance_alerts': True,
    'alert_threshold_strategic_percent': 2.0
}}

# Usage example:
# classifier = StrategicEmailClassifier(
#     confidence_threshold=STRATEGIC_INTEGRATION_CONFIG['confidence_threshold']
# )
"""
    
    with open('/Users/Badman/Desktop/email/REPOS/Atlas_Email/strategic_config.py', 'w') as f:
        f.write(config)
    
    print(f"\n💾 Production configuration saved to strategic_config.py")
    print(f"🎯 Recommended threshold: {optimal_threshold:.2f}")

if __name__ == "__main__":
    optimal_threshold = test_threshold_optimization()
    
    if optimal_threshold:
        generate_production_config(optimal_threshold)
        print(f"\n🚀 Strategic Integration optimization complete!")
        print(f"✅ Threshold: {optimal_threshold:.2f}")
        print(f"✅ Target: <1% Strategic Framework usage achieved")
        print(f"✅ Performance: 99%+ fast processing preserved")
    else:
        print(f"\n⚠️  Further optimization needed")
        print(f"💡 Consider improving fast classification rules")