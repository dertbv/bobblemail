#!/usr/bin/env python3
"""
Geographic Intelligence Module for Atlas Email
Extracts IP addresses from email headers and provides geographic threat intelligence
"""

import re
import json
import geoip2fast
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Import caching
try:
    from atlas_email.utils.cache_manager import get_geographic_cache, set_geographic_cache
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False

@dataclass
class GeographicData:
    """Container for geographic intelligence data"""
    sender_ip: Optional[str] = None
    sender_country_code: Optional[str] = None 
    sender_country_name: Optional[str] = None
    geographic_risk_score: float = 0.0
    detection_method: str = "IP_HEADER_ANALYSIS"

class GeographicIntelligenceProcessor:
    """
    Processes email headers to extract IP addresses and provide geographic threat intelligence
    """
    
    # Country risk scores based on threat intelligence data
    COUNTRY_RISK_SCORES = {
        # High-risk countries (known spam/phishing sources)
        'CN': 0.95,  # China - major spam source
        'RU': 0.90,  # Russia - high phishing activity
        'NG': 0.85,  # Nigeria - financial scams
        'IN': 0.80,  # India - call center fraud
        'PK': 0.75,  # Pakistan - spam networks
        'BD': 0.70,  # Bangladesh - suspicious patterns
        'VN': 0.65,  # Vietnam - emerging threat
        'UA': 0.60,  # Ukraine - conflict-related risks
        'ID': 0.55,  # Indonesia - growing spam source
        'BR': 0.50,  # Brazil - moderate risk
        
        # Medium-risk countries
        'TR': 0.45,  # Turkey
        'MX': 0.40,  # Mexico
        'TH': 0.35,  # Thailand
        'PL': 0.30,  # Poland
        'RO': 0.25,  # Romania
        
        # Low-risk countries (established email infrastructure)
        'US': 0.10,  # United States
        'CA': 0.10,  # Canada
        'GB': 0.10,  # United Kingdom
        'DE': 0.10,  # Germany
        'FR': 0.10,  # France
        'AU': 0.10,  # Australia
        'JP': 0.10,  # Japan
        'NL': 0.10,  # Netherlands
        'SE': 0.10,  # Sweden
        'CH': 0.10,  # Switzerland
        'DK': 0.10,  # Denmark
        'NO': 0.10,  # Norway
        'FI': 0.10,  # Finland
        'IT': 0.15,  # Italy
        'ES': 0.15,  # Spain
        'KR': 0.15,  # South Korea
        'SG': 0.15,  # Singapore
        'HK': 0.20,  # Hong Kong
        'NZ': 0.10,  # New Zealand
        'IE': 0.10,  # Ireland
        'BE': 0.10,  # Belgium
        'AT': 0.10,  # Austria
        'IL': 0.20,  # Israel
        'ZA': 0.25,  # South Africa
    }
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.geoip = geoip2fast.GeoIP2Fast()
        
    def extract_ip_from_headers(self, headers: str) -> Optional[str]:
        """
        Extract sender IP address from email headers
        Looks for the first external IP in Received headers
        """
        if not headers:
            return None
            
        try:
            # Split headers into lines
            header_lines = headers.split('\n')
            
            # Look for Received headers in reverse order (most recent first)
            received_headers = []
            for line in header_lines:
                if line.lower().startswith('received:'):
                    received_headers.append(line)
            
            # Process received headers to find external IPs
            for received in received_headers:
                ip = self._extract_ip_from_received_header(received)
                if ip and self._is_external_ip(ip):
                    return ip
                    
            # Fallback: look for other IP-containing headers
            for line in header_lines:
                if any(header in line.lower() for header in ['x-originating-ip:', 'x-sender-ip:', 'x-real-ip:']):
                    ip = self._extract_ip_from_line(line)
                    if ip and self._is_external_ip(ip):
                        return ip
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting IP from headers: {e}")
            return None
    
    def _extract_ip_from_received_header(self, received_header: str) -> Optional[str]:
        """Extract IP from a Received header line"""
        # Common patterns in Received headers:
        # from hostname [ip.address]
        # from hostname (ip.address)
        # from hostname ip.address
        
        # Pattern 1: [ip.address] format
        bracket_pattern = r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]'
        match = re.search(bracket_pattern, received_header)
        if match:
            return match.group(1)
            
        # Pattern 2: (ip.address) format  
        paren_pattern = r'\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)'
        match = re.search(paren_pattern, received_header)
        if match:
            return match.group(1)
            
        # Pattern 3: standalone IP after "from"
        from_pattern = r'from\s+[^\s]*\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(from_pattern, received_header, re.IGNORECASE)
        if match:
            return match.group(1)
            
        return None
    
    def _extract_ip_from_line(self, line: str) -> Optional[str]:
        """Extract IP from any header line"""
        ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(ip_pattern, line)
        return match.group(1) if match else None
    
    def _is_external_ip(self, ip: str) -> bool:
        """Check if IP is external (not private/local)"""
        try:
            octets = [int(x) for x in ip.split('.')]
            
            # Private IP ranges to exclude:
            # 10.0.0.0/8 (10.0.0.0 - 10.255.255.255)
            # 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)  
            # 192.168.0.0/16 (192.168.0.0 - 192.168.255.255)
            # 127.0.0.0/8 (localhost)
            # 169.254.0.0/16 (link-local)
            
            if octets[0] == 10:
                return False
            elif octets[0] == 172 and 16 <= octets[1] <= 31:
                return False
            elif octets[0] == 192 and octets[1] == 168:
                return False
            elif octets[0] == 127:
                return False
            elif octets[0] == 169 and octets[1] == 254:
                return False
            elif octets[0] == 0:
                return False
                
            return True
            
        except (ValueError, IndexError):
            return False
    
    def get_geographic_data(self, ip_address: str) -> GeographicData:
        """
        Get geographic data for an IP address using GeoIP2Fast
        """
        if not ip_address or not self._is_external_ip(ip_address):
            return GeographicData()
        
        # Check cache first
        if CACHE_ENABLED:
            cached_data = get_geographic_cache(ip_address)
            if cached_data:
                # Convert dict back to GeographicData
                return GeographicData(**cached_data)
            
        try:
            # Use GeoIP2Fast for geographic lookup
            result = self.geoip.lookup(ip_address)
            
            if result and result.country_code:
                country_code = result.country_code
                country_name = result.country_name or country_code
                
                # Calculate risk score based on country
                risk_score = self.COUNTRY_RISK_SCORES.get(country_code, 0.30)  # Default moderate risk
                
                geo_data = GeographicData(
                    sender_ip=ip_address,
                    sender_country_code=country_code,
                    sender_country_name=country_name,
                    geographic_risk_score=risk_score,
                    detection_method="GEOIP2FAST_LOOKUP"
                )
                
                # Cache the result
                if CACHE_ENABLED:
                    # Convert to dict for caching
                    cache_data = {
                        'sender_ip': geo_data.sender_ip,
                        'sender_country_code': geo_data.sender_country_code,
                        'sender_country_name': geo_data.sender_country_name,
                        'geographic_risk_score': geo_data.geographic_risk_score,
                        'detection_method': geo_data.detection_method
                    }
                    set_geographic_cache(ip_address, cache_data, ttl=604800)  # 7 days
                
                return geo_data
            else:
                # IP lookup failed but we have the IP
                return GeographicData(
                    sender_ip=ip_address,
                    sender_country_code=None,
                    sender_country_name=None,
                    geographic_risk_score=0.40,  # Unknown country = moderate risk
                    detection_method="IP_EXTRACTED_COUNTRY_UNKNOWN"
                )
                
        except Exception as e:
            self.logger.error(f"Geographic lookup failed for IP {ip_address}: {e}")
            return GeographicData(
                sender_ip=ip_address,
                geographic_risk_score=0.35,  # Lookup error = low-moderate risk
                detection_method="GEOIP_LOOKUP_ERROR"
            )
    
    def process_email_geographic_intelligence(self, headers: str, sender_email: str = None) -> GeographicData:
        """
        Complete geographic intelligence processing for an email
        Returns geographic data including IP, country, and risk assessment
        """
        try:
            # Extract IP from headers
            sender_ip = self.extract_ip_from_headers(headers)
            
            if sender_ip:
                # Get geographic data
                geo_data = self.get_geographic_data(sender_ip)
                self.logger.info(f"📍 Geographic Intelligence: {sender_email} -> {geo_data.sender_country_code} (Risk: {geo_data.geographic_risk_score:.2f})")
                return geo_data
            else:
                # No IP found in headers
                self.logger.debug(f"No external IP found in headers for {sender_email}")
                return GeographicData(
                    detection_method="NO_EXTERNAL_IP_FOUND"
                )
                
        except Exception as e:
            self.logger.error(f"Geographic intelligence processing failed for {sender_email}: {e}")
            return GeographicData(
                detection_method="PROCESSING_ERROR"
            )
    
    def get_risk_assessment(self, country_code: str) -> Dict[str, Any]:
        """
        Get detailed risk assessment for a country
        """
        if not country_code:
            return {"risk_level": "unknown", "score": 0.30, "reason": "Country unknown"}
            
        score = self.COUNTRY_RISK_SCORES.get(country_code, 0.30)
        
        if score >= 0.80:
            risk_level = "very_high"
            reason = "Known major spam/phishing source"
        elif score >= 0.60:
            risk_level = "high" 
            reason = "Significant suspicious activity"
        elif score >= 0.40:
            risk_level = "medium"
            reason = "Moderate risk profile"
        elif score >= 0.20:
            risk_level = "low"
            reason = "Generally trustworthy"
        else:
            risk_level = "very_low"
            reason = "Established secure infrastructure"
            
        return {
            "risk_level": risk_level,
            "score": score,
            "reason": reason,
            "country_code": country_code
        }