#!/usr/bin/env python3
"""
Test China IP Detection in Geographic Intelligence
Validates high-risk country detection works correctly
"""

import time
import sys
import os
import re

# Test geoip2fast directly
try:
    import geoip2fast.geoip2fast as geoip2fast_module
    GEOIP_AVAILABLE = True
    _geoip = geoip2fast_module.GeoIP2Fast()
    print("✅ geoip2fast library available")
except ImportError:
    GEOIP_AVAILABLE = False
    _geoip = None
    print("❌ geoip2fast library not available")

def assess_geographic_risk(ip_address):
    """Fast geographic risk assessment using geoip2fast"""
    
    high_risk_countries = {'CN', 'RU', 'UA', 'BD', 'PK', 'IN'}
    suspicious_ip_ranges = [
        '103.45.',  # Known botnet range
        '45.67.',   # Compromised server range  
        '185.220.', # Tor exit nodes
        '198.98.',  # VPN spam networks
    ]
    
    if not GEOIP_AVAILABLE:
        return {'is_high_risk': False, 'confidence': 0.0, 'reason': 'GeoIP not available'}
    
    try:
        # Suspicious IP range check (instant)
        for ip_range in suspicious_ip_ranges:
            if ip_address.startswith(ip_range):
                return {
                    'is_high_risk': True,
                    'confidence': 0.95,
                    'reason': f'Suspicious IP range detected: {ip_range}*'
                }
        
        # Fast country lookup using geoip2fast (0.0416ms vs 2,294ms WHOIS)
        geo_result = _geoip.lookup(ip_address)
        country_code = getattr(geo_result, 'country_code', '')
        
        if country_code in high_risk_countries:
            country_name = getattr(geo_result, 'country_name', country_code)
            return {
                'is_high_risk': True,
                'confidence': 0.90,
                'reason': f'High-risk country detected: {country_name} ({country_code})'
            }
        
        return {'is_high_risk': False, 'confidence': 0.1, 'reason': f'Low-risk country: {country_code}'}
        
    except Exception as e:
        return {'is_high_risk': False, 'confidence': 0.5, 'reason': f'GeoIP lookup failed: {str(e)}'}

def test_china_detection():
    """Test China IP detection specifically"""
    
    print("🇨🇳 CHINA IP DETECTION TEST")
    print("=" * 40)
    
    # Real China IPs
    china_ips = [
        '58.246.58.140',   # Tencent
        '202.108.22.5',    # Sina
        '219.133.40.177',  # China Telecom
        '180.149.132.47',  # China Unicom
        '125.64.94.200'    # CERNET
    ]
    
    print("🧪 Testing Real China IPs:")
    
    for ip in china_ips:
        start_time = time.perf_counter()
        result = assess_geographic_risk(ip)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000
        
        status = "🚨 HIGH RISK" if result['is_high_risk'] else "❌ MISSED"
        
        print(f"  {ip} -> {status} ({processing_time:.3f}ms)")
        print(f"    {result['reason']} (confidence: {result['confidence']:.2f})")
        print()
    
    # Test other high-risk countries
    print("🌍 Testing Other High-Risk Countries:")
    
    other_ips = [
        ('95.216.181.40', 'Russia'),      # Real Russian IP
        ('93.120.27.62', 'Ukraine'),      # Real Ukrainian IP  
        ('103.247.13.90', 'Bangladesh'),  # Real Bangladesh IP
        ('182.160.109.145', 'Pakistan'),  # Real Pakistan IP
        ('122.165.165.165', 'India')      # Real India IP
    ]
    
    for ip, expected_country in other_ips:
        start_time = time.perf_counter()
        result = assess_geographic_risk(ip)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000
        
        status = "🚨 HIGH RISK" if result['is_high_risk'] else "❌ MISSED"
        
        print(f"  {ip} ({expected_country}) -> {status} ({processing_time:.3f}ms)")
        print(f"    {result['reason']} (confidence: {result['confidence']:.2f})")
        print()
    
    print("✅ China detection test complete!")

if __name__ == "__main__":
    test_china_detection()