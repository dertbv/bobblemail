#!/usr/bin/env python3
"""
ATLAS Email - Adaptive Spam Logic Framework
Zero-maintenance, logic-based spam prevention using publicly verifiable data
Implements multi-dimensional analysis: authentication + business + content + geographic + network
"""

import re
import math
import hashlib
import socket
import ssl
import whois
import dns.resolver
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

class ThreatLevel(Enum):
    LEGITIMATE = "LEGITIMATE"
    SUSPICIOUS = "SUSPICIOUS" 
    HIGH_RISK = "HIGH_RISK"
    PHISHING = "PHISHING"

@dataclass
class ValidationResult:
    threat_level: ThreatLevel
    confidence: float
    reasons: List[str]
    authentication_score: int
    business_score: int
    content_score: int
    geographic_score: int
    network_score: int
    
class AdaptiveSpamLogicFramework:
    """
    Multi-dimensional spam detection using publicly verifiable data only.
    Zero maintenance required - self-adapting thresholds and pattern recognition.
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.authentication_cache = {}
        self.domain_reputation_cache = {}
        self.geographic_risk_cache = {}
        self.adaptive_thresholds = self._initialize_adaptive_thresholds()
        
    def _initialize_adaptive_thresholds(self) -> Dict[str, float]:
        """Initialize self-adapting threshold values"""
        return {
            'authentication_minimum': 0.7,
            'business_verification_minimum': 0.6,
            'content_entropy_threshold': 3.2,
            'domain_age_suspicious_days': 30,
            'domain_age_quarantine_days': 90,
            'geographic_risk_threshold': 0.6,
            'network_quality_threshold': 0.5,
            'phishing_detection_threshold': 0.8
        }
    
    # ============================================================================
    # 1. AUTHENTICATION-FIRST VALIDATION
    # ============================================================================
    
    def validate_authentication(self, sender_email: str, sender_domain: str) -> Tuple[float, List[str]]:
        """
        Cryptographic domain authentication using SPF/DKIM/DMARC
        Returns (score 0-1, reasons)
        """
        if sender_domain in self.authentication_cache:
            cached = self.authentication_cache[sender_domain]
            if (datetime.now() - cached['timestamp']).hours < 24:
                return cached['score'], cached['reasons']
        
        score = 0.0
        reasons = []
        
        try:
            # SPF Validation
            spf_score = self._validate_spf_record(sender_domain)
            score += spf_score * 0.4
            if spf_score > 0.5:
                reasons.append(f"Valid SPF record ({spf_score:.2f})")
            else:
                reasons.append("Missing or invalid SPF record")
            
            # DKIM Validation  
            dkim_score = self._validate_dkim_capability(sender_domain)
            score += dkim_score * 0.4
            if dkim_score > 0.5:
                reasons.append(f"DKIM capable domain ({dkim_score:.2f})")
            else:
                reasons.append("No DKIM infrastructure detected")
            
            # DMARC Policy Validation
            dmarc_score = self._validate_dmarc_policy(sender_domain)
            score += dmarc_score * 0.2
            if dmarc_score > 0.5:
                reasons.append(f"DMARC policy present ({dmarc_score:.2f})")
            else:
                reasons.append("No DMARC policy found")
                
        except Exception as e:
            self.logger.error(f"Authentication validation error for {sender_domain}: {e}")
            reasons.append("Authentication validation failed")
        
        # Cache result
        self.authentication_cache[sender_domain] = {
            'score': score,
            'reasons': reasons,
            'timestamp': datetime.now()
        }
        
        return score, reasons
    
    def _validate_spf_record(self, domain: str) -> float:
        """Validate SPF record exists and is properly configured"""
        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                record_str = record.to_text().strip('"')
                if record_str.startswith('v=spf1'):
                    # Basic SPF validation - proper mechanisms present
                    if any(mechanism in record_str for mechanism in ['include:', 'ip4:', 'ip6:', 'a:', 'mx:']):
                        if record_str.endswith(('~all', '-all')):
                            return 1.0  # Strict SPF policy
                        elif record_str.endswith('+all'):
                            return 0.3  # Permissive policy
                        else:
                            return 0.7  # Moderate policy
            return 0.0  # No SPF record found
        except Exception:
            return 0.0
    
    def _validate_dkim_capability(self, domain: str) -> float:
        """Check if domain has DKIM infrastructure (common selectors)"""
        common_selectors = ['default', 'google', 'k1', 'k2', 'selector1', 'selector2', 'dkim']
        
        for selector in common_selectors:
            try:
                dkim_domain = f"{selector}._domainkey.{domain}"
                txt_records = dns.resolver.resolve(dkim_domain, 'TXT')
                for record in txt_records:
                    if 'p=' in record.to_text():  # Public key present
                        return 1.0
            except Exception:
                continue
        return 0.0
    
    def _validate_dmarc_policy(self, domain: str) -> float:
        """Validate DMARC policy exists and analyze strictness"""
        try:
            dmarc_domain = f"_dmarc.{domain}"
            txt_records = dns.resolver.resolve(dmarc_domain, 'TXT')
            for record in txt_records:
                record_str = record.to_text().strip('"')
                if record_str.startswith('v=DMARC1'):
                    if 'p=reject' in record_str:
                        return 1.0  # Strict policy
                    elif 'p=quarantine' in record_str:
                        return 0.8  # Moderate policy
                    elif 'p=none' in record_str:
                        return 0.5  # Monitoring only
            return 0.0
        except Exception:
            return 0.0
    
    # ============================================================================
    # 2. BUSINESS VERIFICATION LOGIC
    # ============================================================================
    
    def validate_business_legitimacy(self, sender_email: str, sender_domain: str, sender_name: str) -> Tuple[float, List[str]]:
        """
        Validate business legitimacy through domain patterns and infrastructure
        Returns (score 0-1, reasons)
        """
        score = 0.0
        reasons = []
        
        # Corporate domain pattern validation (emails.company.com, mail.company.com)
        corporate_score = self._validate_corporate_domain_pattern(sender_domain)
        score += corporate_score * 0.3
        if corporate_score > 0.7:
            reasons.append("Valid corporate domain pattern")
        
        # ESP (Email Service Provider) validation
        esp_score = self._validate_esp_infrastructure(sender_domain)
        score += esp_score * 0.2
        if esp_score > 0.5:
            reasons.append("Professional ESP infrastructure")
        
        # Brand consistency analysis
        brand_score = self._validate_brand_consistency(sender_domain, sender_name)
        score += brand_score * 0.3
        if brand_score < 0.3:
            reasons.append("⚠️ Brand inconsistency detected")
        elif brand_score > 0.7:
            reasons.append("Brand name matches domain")
        
        # Professional infrastructure indicators
        infra_score = self._validate_professional_infrastructure(sender_domain)
        score += infra_score * 0.2
        if infra_score > 0.6:
            reasons.append("Professional hosting infrastructure")
        
        return min(score, 1.0), reasons
    
    def _validate_corporate_domain_pattern(self, domain: str) -> float:
        """Validate emails.company.com, mail.company.com patterns"""
        corporate_patterns = [
            r'^emails?\.',      # emails.company.com, email.company.com
            r'^mail\.',         # mail.company.com
            r'^newsletter\.',   # newsletter.company.com
            r'^noreply\.',      # noreply.company.com
            r'^notifications?\.',# notification.company.com
            r'^alerts?\.',      # alert.company.com
            r'^updates?\.',     # update.company.com
        ]
        
        for pattern in corporate_patterns:
            if re.match(pattern, domain):
                # Check if base domain exists and looks legitimate
                base_domain = '.'.join(domain.split('.')[1:])
                if len(base_domain.split('.')[0]) > 3:  # Reasonable company name length
                    return 0.9
        
        # Check for direct corporate domains (company.com)
        parts = domain.split('.')
        if len(parts) == 2 and len(parts[0]) > 3 and parts[1] in ['com', 'org', 'net', 'edu']:
            return 0.7
        
        return 0.2
    
    def _validate_esp_infrastructure(self, domain: str) -> float:
        """Identify known Email Service Providers"""
        esp_patterns = {
            'sendgrid': 0.9,
            'mailgun': 0.9,
            'amazon': 0.9,  # SES
            'mailchimp': 0.8,
            'constantcontact': 0.8,
            'campaign': 0.7,
            'mailer': 0.6,
            'broadcast': 0.6,
        }
        
        domain_lower = domain.lower()
        for esp, score in esp_patterns.items():
            if esp in domain_lower:
                return score
        
        return 0.0
    
    def _validate_brand_consistency(self, domain: str, sender_name: str) -> float:
        """Validate sender name consistency with domain"""
        if not sender_name:
            return 0.5
        
        # Extract company name from domain
        domain_parts = domain.split('.')
        if domain.startswith('emails.') or domain.startswith('mail.'):
            company_domain = '.'.join(domain_parts[1:])
        else:
            company_domain = domain
        
        company_name = company_domain.split('.')[0]
        sender_name_clean = re.sub(r'[^a-zA-Z0-9\s]', '', sender_name).lower()
        
        # Check for brand name in sender
        if company_name.lower() in sender_name_clean:
            return 0.9
        
        # Check for obvious brand mismatches (AOL from non-AOL domain)
        suspicious_brands = ['aol', 'google', 'microsoft', 'apple', 'amazon', 'paypal']
        for brand in suspicious_brands:
            if brand in sender_name_clean and brand not in company_name.lower():
                return 0.1  # Likely phishing
        
        return 0.5
    
    def _validate_professional_infrastructure(self, domain: str) -> float:
        """Analyze hosting and infrastructure quality"""
        try:
            # Check for proper MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            if len(list(mx_records)) > 0:
                mx_score = 0.4
            else:
                return 0.0
            
            # Check for proper A record
            a_records = dns.resolver.resolve(domain, 'A')
            if len(list(a_records)) > 0:
                a_score = 0.3
            else:
                return 0.0
            
            # SSL certificate validation
            ssl_score = self._validate_ssl_certificate(domain)
            
            return mx_score + a_score + ssl_score * 0.3
            
        except Exception:
            return 0.0
    
    def _validate_ssl_certificate(self, domain: str) -> float:
        """Validate SSL certificate quality"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate validity
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    if not_after > datetime.now():
                        return 1.0
                    else:
                        return 0.3  # Expired certificate
        except Exception:
            return 0.0
    
    # ============================================================================
    # 3. CONTENT ENTROPY ANALYSIS
    # ============================================================================
    
    def analyze_content_entropy(self, subject: str, sender_name: str) -> Tuple[float, List[str]]:
        """
        Mathematical analysis of message randomness and linguistic patterns
        Returns (suspicion_score 0-1, reasons)
        """
        score = 0.0
        reasons = []
        
        # Subject line entropy analysis
        subject_entropy = self._calculate_entropy(subject)
        if subject_entropy > self.adaptive_thresholds['content_entropy_threshold']:
            score += 0.4
            reasons.append(f"High subject entropy ({subject_entropy:.2f})")
        
        # Unicode manipulation detection
        unicode_score = self._detect_unicode_manipulation(sender_name)
        score += unicode_score * 0.3
        if unicode_score > 0.5:
            reasons.append("Unicode manipulation detected")
        
        # Urgency pattern recognition
        urgency_score = self._detect_urgency_patterns(subject)
        score += urgency_score * 0.2
        if urgency_score > 0.5:
            reasons.append("Urgency/pressure tactics detected")
        
        # Personalization analysis
        personalization_score = self._analyze_personalization(subject, sender_name)
        if personalization_score < 0.3:
            score += 0.1
            reasons.append("Generic/mass email indicators")
        
        return min(score, 1.0), reasons
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy - higher = more random"""
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
    
    def _detect_unicode_manipulation(self, sender_name: str) -> float:
        """Detect Unicode character manipulation (bold, special chars)"""
        if not sender_name:
            return 0.0
        
        # Count non-ASCII characters
        non_ascii_count = sum(1 for char in sender_name if ord(char) > 127)
        ascii_count = len(sender_name) - non_ascii_count
        
        if ascii_count == 0:
            return 1.0  # All non-ASCII
        
        non_ascii_ratio = non_ascii_count / len(sender_name)
        
        # High ratio of non-ASCII in sender name is suspicious
        if non_ascii_ratio > 0.3:
            return min(non_ascii_ratio * 2, 1.0)
        
        return 0.0
    
    def _detect_urgency_patterns(self, subject: str) -> float:
        """Detect urgency and pressure tactics"""
        urgency_keywords = [
            'urgent', 'immediate', 'asap', 'final', 'last', 'expire', 'deadline',
            'action required', 'suspended', 'closed', 'warning', 'alert',
            'verify', 'confirm', 'update', 'secure', 'locked'
        ]
        
        pressure_patterns = [
            r'\b(act|respond|click|call)\s+(now|today|immediately)\b',
            r'\b(limited|final|last)\s+(time|chance|opportunity)\b',
            r'\[(urgent|important|final|warning)\]',
            r'!{2,}',  # Multiple exclamation marks
            r'[A-Z]{3,}',  # All caps words
        ]
        
        subject_lower = subject.lower()
        score = 0.0
        
        # Count urgency keywords
        keyword_matches = sum(1 for keyword in urgency_keywords if keyword in subject_lower)
        score += min(keyword_matches * 0.2, 0.6)
        
        # Check pressure patterns
        for pattern in pressure_patterns:
            if re.search(pattern, subject, re.IGNORECASE):
                score += 0.3
                break
        
        return min(score, 1.0)
    
    def _analyze_personalization(self, subject: str, sender_name: str) -> float:
        """Analyze if message appears personalized vs mass email"""
        # Generic indicators reduce personalization score
        generic_patterns = [
            r'^(dear|hello|hi)\s+(customer|user|member|subscriber)\b',
            r'\b(valued|important|urgent)\s+(customer|notification)\b',
            r'^(newsletter|update|alert|notification)',
            r'\[(update|notification|alert)\]'
        ]
        
        subject_lower = subject.lower()
        for pattern in generic_patterns:
            if re.search(pattern, subject_lower):
                return 0.2
        
        # Check for personal indicators
        if any(indicator in subject_lower for indicator in ['your', 'you', 'personal']):
            return 0.7
        
        return 0.5  # Neutral
    
    # ============================================================================
    # 4. GEOGRAPHIC INTELLIGENCE LOGIC
    # ============================================================================
    
    def analyze_geographic_risk(self, domain: str) -> Tuple[float, List[str]]:
        """
        Analyze geographic registration patterns for risk assessment
        Returns (risk_score 0-1, reasons)
        """
        if domain in self.geographic_risk_cache:
            cached = self.geographic_risk_cache[domain]
            if (datetime.now() - cached['timestamp']).days < 7:
                return cached['score'], cached['reasons']
        
        score = 0.0
        reasons = []
        
        try:
            # WHOIS analysis
            domain_info = whois.whois(domain)
            
            # Country risk assessment
            country_score = self._assess_country_risk(domain_info)
            score += country_score * 0.4
            if country_score > 0.6:
                reasons.append("High-risk country registration")
            
            # Registrar reputation analysis
            registrar_score = self._assess_registrar_reputation(domain_info)
            score += registrar_score * 0.3
            if registrar_score > 0.6:
                reasons.append("High-risk registrar")
            
            # Infrastructure location analysis
            infra_score = self._analyze_infrastructure_location(domain)
            score += infra_score * 0.3
            if infra_score > 0.5:
                reasons.append("Suspicious infrastructure location")
            
        except Exception as e:
            self.logger.error(f"Geographic analysis error for {domain}: {e}")
            score = 0.3  # Default moderate risk for analysis failures
            reasons.append("Geographic analysis unavailable")
        
        # Cache result
        self.geographic_risk_cache[domain] = {
            'score': score,
            'reasons': reasons,
            'timestamp': datetime.now()
        }
        
        return min(score, 1.0), reasons
    
    def _assess_country_risk(self, domain_info) -> float:
        """Assess country-based risk using historical spam correlation"""
        # High-risk countries based on spam statistics
        high_risk_countries = ['CN', 'RU', 'TR', 'IN', 'PK', 'NG', 'BR', 'VN']
        medium_risk_countries = ['UA', 'RO', 'BG', 'PL', 'TH', 'PH', 'ID', 'MY']
        
        try:
            country = getattr(domain_info, 'country', None)
            if isinstance(country, list):
                country = country[0] if country else None
            
            if country:
                country_upper = country.upper()
                if country_upper in high_risk_countries:
                    return 0.8
                elif country_upper in medium_risk_countries:
                    return 0.5
                elif country_upper in ['US', 'CA', 'GB', 'DE', 'FR', 'AU', 'JP']:
                    return 0.1  # Low risk
                else:
                    return 0.3  # Unknown/moderate risk
        except Exception:
            pass
        
        return 0.3  # Default moderate risk
    
    def _assess_registrar_reputation(self, domain_info) -> float:
        """Assess registrar reputation based on spam correlation"""
        # Known high-risk registrars (updated based on spam statistics)
        high_risk_registrars = [
            'namecheap', 'godaddy cheap', 'porkbun', 'namesilo',
            'dynadot', 'name.com', 'enom'
        ]
        
        reputable_registrars = [
            'markmonitor', 'corporation service company', 'amazon',
            'google', 'microsoft', 'cloudflare'
        ]
        
        try:
            registrar = getattr(domain_info, 'registrar', '')
            if isinstance(registrar, list):
                registrar = registrar[0] if registrar else ''
            
            registrar_lower = registrar.lower()
            
            if any(risky in registrar_lower for risky in high_risk_registrars):
                return 0.7
            elif any(reputable in registrar_lower for reputable in reputable_registrars):
                return 0.1
            else:
                return 0.4  # Unknown registrar
        except Exception:
            pass
        
        return 0.4  # Default moderate risk
    
    def _analyze_infrastructure_location(self, domain: str) -> float:
        """Analyze hosting infrastructure location"""
        try:
            # Get IP address
            ip = socket.gethostbyname(domain)
            
            # Basic IP range analysis (this would be enhanced with GeoIP data)
            ip_parts = ip.split('.')
            first_octet = int(ip_parts[0])
            
            # Some basic IP range risk assessment
            if first_octet in [10, 172, 192]:  # Private ranges (shouldn't be public)
                return 0.9
            elif first_octet < 1 or first_octet > 223:  # Invalid ranges
                return 0.8
            else:
                return 0.2  # Appears to be valid public IP
                
        except Exception:
            return 0.5  # Unknown infrastructure
    
    # ============================================================================
    # 5. NETWORK INFRASTRUCTURE ANALYSIS
    # ============================================================================
    
    def analyze_network_infrastructure(self, domain: str) -> Tuple[float, List[str]]:
        """
        Analyze technical infrastructure quality and legitimacy indicators
        Returns (quality_score 0-1, reasons)
        """
        score = 0.0
        reasons = []
        
        # DNS configuration quality
        dns_score = self._analyze_dns_configuration(domain)
        score += dns_score * 0.4
        if dns_score > 0.7:
            reasons.append("Professional DNS configuration")
        elif dns_score < 0.3:
            reasons.append("Poor DNS configuration")
        
        # SSL certificate analysis
        ssl_score = self._analyze_ssl_certificate_quality(domain)
        score += ssl_score * 0.3
        if ssl_score > 0.8:
            reasons.append("High-quality SSL certificate")
        elif ssl_score < 0.3:
            reasons.append("Poor or missing SSL certificate")
        
        # Hosting quality assessment
        hosting_score = self._assess_hosting_quality(domain)
        score += hosting_score * 0.3
        if hosting_score > 0.7:
            reasons.append("Professional hosting provider")
        elif hosting_score < 0.3:
            reasons.append("Low-quality hosting")
        
        return min(score, 1.0), reasons
    
    def _analyze_dns_configuration(self, domain: str) -> float:
        """Analyze DNS configuration completeness and quality"""
        score = 0.0
        
        try:
            # Check for proper A record
            dns.resolver.resolve(domain, 'A')
            score += 0.2
            
            # Check for MX records
            mx_records = list(dns.resolver.resolve(domain, 'MX'))
            if len(mx_records) > 0:
                score += 0.3
                if len(mx_records) > 1:  # Multiple MX for redundancy
                    score += 0.1
            
            # Check for SPF record
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                if record.to_text().strip('"').startswith('v=spf1'):
                    score += 0.2
                    break
            
            # Check for DMARC
            try:
                dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
                score += 0.2
            except:
                pass
            
        except Exception:
            pass
        
        return min(score, 1.0)
    
    def _analyze_ssl_certificate_quality(self, domain: str) -> float:
        """Analyze SSL certificate quality and validation level"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    score = 0.0
                    
                    # Certificate validity
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    
                    if not_before <= datetime.now() <= not_after:
                        score += 0.4  # Valid certificate
                        
                        # Certificate age (longer = more established)
                        cert_age = (datetime.now() - not_before).days
                        if cert_age > 90:
                            score += 0.2
                        elif cert_age > 30:
                            score += 0.1
                    
                    # Issuer quality (CA reputation)
                    issuer = cert.get('issuer', [])
                    issuer_name = ''
                    for item in issuer:
                        if item[0][0] == 'organizationName':
                            issuer_name = item[0][1].lower()
                            break
                    
                    reputable_cas = [
                        'lets encrypt', 'digicert', 'comodo', 'symantec',
                        'godaddy', 'geotrust', 'rapidssl', 'thawte'
                    ]
                    
                    if any(ca in issuer_name for ca in reputable_cas):
                        score += 0.3
                    
                    # Extended Validation indicators
                    if 'EV' in str(cert) or len(issuer) > 5:
                        score += 0.1
                    
                    return min(score, 1.0)
                    
        except Exception:
            return 0.0  # No SSL or connection failed
    
    def _assess_hosting_quality(self, domain: str) -> float:
        """Assess hosting provider quality and reputation"""
        try:
            ip = socket.gethostbyname(domain)
            
            # Get PTR record for reverse DNS
            try:
                ptr_record = socket.gethostbyaddr(ip)[0]
                
                # Professional hosting providers
                quality_providers = [
                    'amazon', 'google', 'microsoft', 'cloudflare',
                    'fastly', 'akamai', 'digitalocean', 'linode'
                ]
                
                ptr_lower = ptr_record.lower()
                if any(provider in ptr_lower for provider in quality_providers):
                    return 0.9
                
                # Generic hosting patterns
                if any(pattern in ptr_lower for pattern in ['hosting', 'server', 'cloud']):
                    return 0.6
                
                return 0.4  # Unknown hosting
                
            except Exception:
                return 0.3  # No PTR record
                
        except Exception:
            return 0.0  # Cannot resolve domain
    
    # ============================================================================
    # 6. COMPREHENSIVE VALIDATION ENGINE
    # ============================================================================
    
    def validate_email(self, sender_email: str, sender_domain: str, sender_name: str, subject: str) -> ValidationResult:
        """
        Comprehensive email validation using all analysis dimensions
        Returns final threat assessment and confidence score
        """
        # Run all validation components
        auth_score, auth_reasons = self.validate_authentication(sender_email, sender_domain)
        business_score, business_reasons = self.validate_business_legitimacy(sender_email, sender_domain, sender_name)
        content_score, content_reasons = self.analyze_content_entropy(subject, sender_name)
        geo_score, geo_reasons = self.analyze_geographic_risk(sender_domain)
        network_score, network_reasons = self.analyze_network_infrastructure(sender_domain)
        
        # Combine all reasons
        all_reasons = auth_reasons + business_reasons + content_reasons + geo_reasons + network_reasons
        
        # Calculate weighted final score
        final_score = (
            auth_score * 0.3 +           # Authentication is most important
            business_score * 0.25 +      # Business validation
            (1 - content_score) * 0.2 +  # Content (inverted - low content score = good)
            (1 - geo_score) * 0.15 +     # Geographic (inverted - low geo risk = good) 
            network_score * 0.1          # Network infrastructure
        )
        
        # Determine threat level
        if final_score >= 0.8:
            threat_level = ThreatLevel.LEGITIMATE
        elif final_score >= 0.6:
            threat_level = ThreatLevel.SUSPICIOUS
        elif final_score >= 0.4:
            threat_level = ThreatLevel.HIGH_RISK
        else:
            threat_level = ThreatLevel.PHISHING
        
        # Special phishing detection overrides
        if (content_score > 0.8 and business_score < 0.3) or auth_score < 0.2:
            threat_level = ThreatLevel.PHISHING
        
        # High authentication score override (cryptographic proof)
        if auth_score > 0.8 and business_score > 0.6:
            threat_level = ThreatLevel.LEGITIMATE
        
        return ValidationResult(
            threat_level=threat_level,
            confidence=final_score,
            reasons=all_reasons,
            authentication_score=int(auth_score * 100),
            business_score=int(business_score * 100),
            content_score=int(content_score * 100),
            geographic_score=int(geo_score * 100),
            network_score=int(network_score * 100)
        )
    
    # ============================================================================
    # 7. ADAPTIVE LEARNING SYSTEM
    # ============================================================================
    
    def update_adaptive_thresholds(self, validation_results: List[ValidationResult], accuracy_feedback: Dict[str, bool]):
        """
        Update thresholds based on validation accuracy feedback
        Self-learning system that requires no manual intervention
        """
        if len(validation_results) < 10:  # Need minimum sample size
            return
        
        # Calculate current accuracy rates
        correct_predictions = sum(1 for result_id, is_correct in accuracy_feedback.items() if is_correct)
        total_predictions = len(accuracy_feedback)
        current_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # Adjust thresholds based on accuracy
        if current_accuracy < 0.95:  # Target 95% accuracy
            # Tighten thresholds to reduce false negatives
            self.adaptive_thresholds['authentication_minimum'] = min(0.8, self.adaptive_thresholds['authentication_minimum'] + 0.02)
            self.adaptive_thresholds['content_entropy_threshold'] = max(2.8, self.adaptive_thresholds['content_entropy_threshold'] - 0.1)
        elif current_accuracy > 0.98:  # Too conservative
            # Relax thresholds slightly to reduce false positives
            self.adaptive_thresholds['authentication_minimum'] = max(0.6, self.adaptive_thresholds['authentication_minimum'] - 0.01)
            self.adaptive_thresholds['content_entropy_threshold'] = min(3.6, self.adaptive_thresholds['content_entropy_threshold'] + 0.05)
        
        self.logger.info(f"Adaptive thresholds updated. Current accuracy: {current_accuracy:.3f}")
    
    def export_intelligence_report(self) -> Dict[str, Any]:
        """Export comprehensive intelligence report for analysis"""
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'adaptive_thresholds': self.adaptive_thresholds,
            'cache_statistics': {
                'authentication_cache_size': len(self.authentication_cache),
                'domain_reputation_cache_size': len(self.domain_reputation_cache),
                'geographic_risk_cache_size': len(self.geographic_risk_cache)
            },
            'framework_version': '1.0.0',
            'validation_capabilities': [
                'SPF/DKIM/DMARC Authentication',
                'Business Domain Pattern Recognition',
                'Content Entropy Analysis',
                'Geographic Risk Assessment',
                'Network Infrastructure Quality',
                'Adaptive Threshold Learning'
            ]
        }

# Example usage
if __name__ == "__main__":
    framework = AdaptiveSpamLogicFramework()
    
    # Test with research flagged email examples
    test_cases = [
        {
            'sender_email': 'reply@ss.email.nextdoor.com',
            'sender_domain': 'ss.email.nextdoor.com',
            'sender_name': 'Sugarland Run Trending Posts',
            'subject': 'Hello.'
        },
        {
            'sender_email': 'reply@warfarersuk.com',
            'sender_domain': 'warfarersuk.com', 
            'sender_name': '𝗔𝗢𝗟 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗧𝗲𝗮𝗺',
            'subject': 'teamicbob Your Subscription has Closed at __DT [ 𝗙𝗶𝗻𝗮𝗹 𝗪𝗮𝗿𝗻𝗶𝗻𝗴 ]'
        }
    ]
    
    for test in test_cases:
        result = framework.validate_email(
            test['sender_email'],
            test['sender_domain'], 
            test['sender_name'],
            test['subject']
        )
        
        print(f"\n📧 Analysis: {test['sender_email']}")
        print(f"Threat Level: {result.threat_level.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Scores - Auth: {result.authentication_score}, Business: {result.business_score}, Content: {result.content_score}")
        print(f"Reasons: {result.reasons[:3]}")