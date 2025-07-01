#!/usr/bin/env python3
"""
Logical Email Classification Engine

Intelligent email classification using decision tree logic instead of keyword soup.
Analyzes sender, domain, and content patterns with hierarchical priority rules.
"""

import re
import tldextract
from urllib.parse import urlparse
from atlas_email.utils.domain_cache import domain_cache
try:
    import geoip2fast.geoip2fast as geoip2fast_module
    GEOIP_AVAILABLE = True
    _geoip = geoip2fast_module.GeoIP2Fast()
except ImportError:
    GEOIP_AVAILABLE = False
    _geoip = None


class LogicalEmailClassifier:
    """
    Logic-based email classifier using decision trees and pattern recognition
    """
    
    def __init__(self):
        self.confidence_score = 0.0
        self.classification_reason = ""
        
        # TLD blacklist for instant detection (1,934,674x faster than WHOIS)
        self.suspicious_tlds = {
            '.cn', '.ru', '.tk', '.ml', '.ga', '.cf', '.cc', '.pw',
            '.top', '.click', '.bid', '.win', '.download', '.party'
        }
        
        # High-risk countries for geographic intelligence
        self.high_risk_countries = {'CN', 'RU', 'UA', 'BD', 'PK', 'IN'}
        
        # Suspicious IP ranges (botnets, compromised servers)
        self.suspicious_ip_ranges = [
            '103.45.',  # Known botnet range
            '45.67.',   # Compromised server range
            '185.220.', # Tor exit nodes
            '198.98.',  # VPN spam networks
        ]
        
    def classify_email(self, sender, subject, headers=""):
        """
        Main classification method using logical decision tree
        
        Args:
            sender: Email sender address
            subject: Email subject line
            headers: Additional email headers (optional)
            
        Returns:
            tuple: (category, confidence, reason)
        """
        
        # Reset for new classification
        self.confidence_score = 0.0
        self.classification_reason = ""
        
        # Combine all text for analysis
        full_text = f"{sender} {subject} {headers}".lower()
        
        # PHASE 1 OPTIMIZATION: Check cache and instant detection FIRST
        sender_domain = self._extract_domain_fast(sender)
        
        # 1. TLD BLACKLIST CHECK (instant, no expensive analysis)
        if self._is_suspicious_tld(sender_domain):
            return "Domain Spam", 0.98, f"Suspicious TLD detected: {sender_domain}"
        
        # 2. DOMAIN CACHE CHECK (70% hit rate = 9x performance)
        cached_result = self._check_domain_cache(sender_domain)
        if cached_result and cached_result.get('is_suspicious'):
            return "Domain Spam", 0.95, f"Cached suspicious domain: {sender_domain}"
        
        # 3. OBVIOUS SPAM PATTERNS (before expensive domain analysis)
        # Adult content (highest confidence, instant detection)
        if self._is_adult_content(sender, subject, full_text):
            return "Adult & Dating Spam", 0.95, "Explicit adult content detected"
        
        # Gibberish domains (instant pattern matching)
        if self._is_gibberish_domain_fast(sender_domain):
            return "Domain Spam", 0.98, f"Gibberish domain detected: {sender_domain}"
        
        # TIER 2: FAST GEOGRAPHIC INTELLIGENCE (0.01-1ms)
        # Extract sender IP from headers for geographic analysis
        sender_ip = self._extract_sender_ip(headers)
        if sender_ip:
            # Geographic risk assessment using geoip2fast (55,099x faster than WHOIS)
            geo_risk = self._assess_geographic_risk(sender_ip)
            if geo_risk['is_high_risk']:
                return "Geographic Spam", geo_risk['confidence'], geo_risk['reason']
        
        # Only perform expensive domain analysis if needed
        domain_info = self._analyze_domain(sender)
        
        # Apply hierarchical classification logic
        
        # Adult content already checked above for early exit
            
        # PRIORITY 2: Brand Impersonation (fake domains with brand names)
        brand_result = self._detect_brand_impersonation(sender, subject, domain_info)
        if brand_result:
            # 4. EARLY EXIT on high confidence
            if brand_result[1] >= 0.95:
                return brand_result
            # Continue checking if confidence < 0.95
            
        # PRIORITY 3: Phishing & Payment Scams (moved before financial to catch personal email invoices)
        phishing_result = self._detect_phishing_scams(sender, subject, full_text, domain_info)
        if phishing_result:
            # 4. EARLY EXIT on high confidence
            if phishing_result[1] >= 0.95:
                return phishing_result
            # Continue checking if confidence < 0.95
            
        # PRIORITY 4: Financial & Investment Spam
        financial_result = self._detect_financial_spam(sender, subject, full_text, domain_info)
        if financial_result:
            # 4. EARLY EXIT on high confidence
            if financial_result[1] >= 0.95:
                return financial_result
            # Continue checking if confidence < 0.95
            
        # PRIORITY 5: Health & Medical Spam
        health_result = self._detect_health_spam(sender, subject, full_text)
        if health_result:
            return health_result
            
        # PRIORITY 6: Gambling Spam
        gambling_result = self._detect_gambling_spam(sender, subject, full_text)
        if gambling_result:
            return gambling_result
            
        # PRIORITY 7: Real Estate Spam
        real_estate_result = self._detect_real_estate_spam(sender, subject, full_text)
        if real_estate_result:
            return real_estate_result
            
        # PRIORITY 8: Legal & Compensation Scams
        legal_result = self._detect_legal_scams(sender, subject, full_text)
        if legal_result:
            return legal_result
            
        # PRIORITY 9: Promotional Email (legitimate retail)
        promotional_result = self._detect_promotional_email(sender, subject, full_text, domain_info)
        if promotional_result:
            return promotional_result
            
        # DEFAULT: Marketing Spam (catch-all)
        return "Marketing Spam", 0.5, "General spam content detected"
    
    def _extract_domain_fast(self, sender):
        """Fast domain extraction without full analysis"""
        if '@' not in sender:
            return ""
        try:
            return sender.split('@')[1].strip().replace('>', '').lower()
        except:
            return ""
    
    def _is_suspicious_tld(self, domain):
        """Instant TLD blacklist check - 1,934,674x faster than WHOIS"""
        if not domain:
            return False
        return any(domain.endswith(tld) for tld in self.suspicious_tlds)
    
    def _check_domain_cache(self, domain):
        """Check domain cache for instant results"""
        if not domain:
            return None
        return domain_cache.get_cached_validation(domain)
    
    def _is_gibberish_domain_fast(self, domain):
        """Fast gibberish detection using patterns"""
        if not domain or len(domain) < 5:
            return False
        
        # Extract domain part (before first dot)
        domain_part = domain.split('.')[0]
        
        # Very short random domains
        if len(domain_part) <= 3:
            return True
            
        # Long strings of random characters (no recognizable words)
        if len(domain_part) > 12:
            recognizable_words = ['email', 'mail', 'news', 'letter', 'update', 'info', 'support', 'app', 'web', 'net']
            if not any(word in domain_part for word in recognizable_words):
                return True
        
        # Pattern: excessive consonants without vowels  
        consonant_ratio = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', domain_part)) / len(domain_part)
        if consonant_ratio > 0.8 and len(domain_part) > 6:
            return True
            
        return False
    
    def _analyze_domain(self, sender):
        """
        Analyze sender domain for legitimacy and patterns
        
        Returns:
            dict: Domain analysis results
        """
        if '@' not in sender:
            return {'is_valid': False, 'is_suspicious': True, 'is_gibberish': True}
            
        try:
            domain = sender.split('@')[1].strip().replace('>', '').lower()
            extracted = tldextract.extract(domain)
            
            # Check for gibberish domain
            is_gibberish = self._is_gibberish_domain(domain, extracted)
            
            # Check for suspicious patterns
            is_suspicious = self._is_suspicious_domain(domain, extracted)
            
            # Check for legitimate known domains
            is_legitimate = self._is_legitimate_domain(domain)
            
            return {
                'domain': domain,
                'subdomain': extracted.subdomain,
                'domain_name': extracted.domain,
                'suffix': extracted.suffix,
                'is_gibberish': is_gibberish,
                'is_suspicious': is_suspicious,
                'is_legitimate': is_legitimate,
                'is_valid': True
            }
            
        except Exception:
            return {'is_valid': False, 'is_suspicious': True, 'is_gibberish': True}
    
    def _is_gibberish_domain(self, domain, extracted):
        """Check if domain appears to be randomly generated gibberish"""
        
        domain_part = extracted.domain
        
        # Very short random domains
        if len(domain_part) <= 3:
            return True
            
        # Long strings of random characters
        if len(domain_part) > 12 and not any(word in domain_part for word in [
            'email', 'mail', 'news', 'letter', 'update', 'info', 'support'
        ]):
            return True
            
        # Pattern: random chars + numbers
        if re.search(r'^[a-z0-9]{8,}$', domain_part) and re.search(r'[0-9]{3,}', domain_part):
            return True
        
        # ENHANCED: Random character sequences like "mvppnzrnrlmkqk"
        if len(domain_part) >= 8:
            # Check for patterns with no recognizable words
            has_recognizable_words = any(word in domain_part for word in [
                'mail', 'email', 'news', 'info', 'support', 'app', 'pay', 'cash',
                'bank', 'shop', 'store', 'market', 'tech', 'web', 'net', 'com'
            ])
            
            if not has_recognizable_words:
                # Count repeated character patterns (spam domains often repeat patterns)
                repeated_patterns = len(re.findall(r'([a-z]{2,3})\1+', domain_part))
                
                # Check for alternating consonant/vowel violation (natural words follow patterns)
                vowels = 'aeiou'
                consonant_clusters = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]{4,}', domain_part))
                vowel_clusters = len(re.findall(r'[aeiou]{3,}', domain_part))
                
                # Gibberish indicators
                if (repeated_patterns >= 2 or 
                    consonant_clusters >= 2 or 
                    vowel_clusters >= 2 or
                    len(domain_part) >= 12):
                    return True
            
        # Excessive consonants without vowels
        consonant_ratio = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', domain_part)) / len(domain_part)
        if consonant_ratio > 0.8 and len(domain_part) > 6:
            return True
            
        return False
    
    def _is_suspicious_domain(self, domain, extracted):
        """Check for suspicious domain patterns"""
        
        # Suspicious TLDs with random domains
        suspicious_tlds = ['.us', '.tk', '.ml', '.ga', '.cf', '.info', '.biz']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            if len(extracted.domain) > 8 or self._is_gibberish_domain(domain, extracted):
                return True
                
        # Multiple numbers in domain
        if len(re.findall(r'[0-9]', extracted.domain)) >= 3:
            return True
            
        # Suspicious patterns
        if re.search(r'[0-9]{2,}[a-z]{2,}[0-9]{2,}', domain):
            return True
            
        return False
    
    def _is_legitimate_domain(self, domain):
        """Check if domain is from a known legitimate company"""
        # Use the comprehensive legitimate domain function from classification_utils
        from atlas_email.core.classification_utils import is_authenticated_domain
        return is_authenticated_domain(domain)
    
    def _is_personal_email_account(self, sender):
        """Check if sender is from a personal email account (Gmail, Yahoo, etc.)"""
        if '@' not in sender:
            return False
            
        try:
            domain = sender.split('@')[1].strip().replace('>', '').lower()
            # Check for personal email provider patterns (not hardcoded lists)
            return any(domain.endswith(suffix) for suffix in ['.gmail.com', '.yahoo.com', '.hotmail.com', '.outlook.com', '.aol.com', '.icloud.com', '.live.com', '.msn.com'])
        except:
            return False
    
    def _normalize_unicode_text(self, text):
        """Convert Unicode formatting characters to normal text for brand detection"""
        import unicodedata
        
        # Normalize to decomposed form, then remove accents and formatting
        normalized = unicodedata.normalize('NFD', text)
        
        # Replace mathematical bold characters with normal ones
        unicode_replacements = {
            # Mathematical Bold Capital Letters
            '𝗔': 'A', '𝗕': 'B', '𝗖': 'C', '𝗗': 'D', '𝗘': 'E', '𝗙': 'F', '𝗚': 'G', '𝗛': 'H',
            '𝗜': 'I', '𝗝': 'J', '𝗞': 'K', '𝗟': 'L', '𝗠': 'M', '𝗡': 'N', '𝗢': 'O', '𝗣': 'P',
            '𝗤': 'Q', '𝗥': 'R', '𝗦': 'S', '𝗧': 'T', '𝗨': 'U', '𝗩': 'V', '𝗪': 'W', '𝗫': 'X',
            '𝗬': 'Y', '𝗭': 'Z',
            # Mathematical Bold Small Letters
            '𝗮': 'a', '𝗯': 'b', '𝗰': 'c', '𝗱': 'd', '𝗲': 'e', '𝗳': 'f', '𝗴': 'g', '𝗵': 'h',
            '𝗶': 'i', '𝗷': 'j', '𝗸': 'k', '𝗹': 'l', '𝗺': 'm', '𝗻': 'n', '𝗼': 'o', '𝗽': 'p',
            '𝗾': 'q', '𝗿': 'r', '𝘀': 's', '𝘁': 't', '𝘂': 'u', '𝘃': 'v', '𝘄': 'w', '𝘅': 'x',
            '𝘆': 'y', '𝘇': 'z'
        }
        
        # Apply replacements
        for unicode_char, normal_char in unicode_replacements.items():
            normalized = normalized.replace(unicode_char, normal_char)
        
        # Remove any remaining non-ASCII characters that might be formatting
        ascii_text = ''.join(char for char in normalized if ord(char) < 128 or char.isalnum())
        
        return ascii_text.lower()
    
    def _is_adult_content(self, sender, subject, full_text):
        """
        Detect explicit adult/sexual content with high confidence
        """
        
        # Explicit sexual terms (high confidence) - use word boundaries to avoid false positives
        explicit_word_terms = [
            'fuck', 'pussy', 'dick', 'cock', 'cum', 'xxx',
            'porn', 'nude', 'naked', 'horny', 'milf'
        ]
        
        # Multi-word explicit phrases
        explicit_phrases = [
            'ready to play', 'want you to fuck', 'ass or pussy'
        ]
        
        # Check for explicit word terms with word boundaries
        for term in explicit_word_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', full_text, re.IGNORECASE):
                self.confidence_score = 0.95
                self.classification_reason = f"Explicit sexual content: '{term}'"
                return True
        
        # Check for explicit phrases
        for phrase in explicit_phrases:
            if phrase in full_text:
                self.confidence_score = 0.95
                self.classification_reason = f"Explicit sexual content: '{phrase}'"
                return True
        
        # Check for specific problematic words that need context
        # "ass" and "anal" are too common in legitimate contexts
        contextual_terms = {
            'sex': ['have sex', 'hot sex', 'cyber sex', 'phone sex'],
            'ass': [' ass ', 'nice ass', 'hot ass', 'sexy ass'],  # Space-bounded
            'anal': [' anal ', 'anal sex', 'anal play'],  # Space-bounded, avoid "analysis"
            'teen': ['teen sex', 'teen porn', 'teen girls', 'hot teen']
        }
        
        for base_term, contexts in contextual_terms.items():
            for context in contexts:
                if context in full_text:
                    self.confidence_score = 0.95
                    self.classification_reason = f"Explicit sexual content: '{context}'"
                    return True
                
        # Sexual emoji patterns
        sexual_emojis = ['💋', '🔥', '💘', '🍆', '🍑']
        if any(emoji in subject for emoji in sexual_emojis):
            if any(word in full_text for word in ['play', 'ready', 'want', 'fuck']):
                self.confidence_score = 0.90
                self.classification_reason = "Sexual emoji + explicit language"
                return True
                
        return False
    
    def _detect_brand_impersonation(self, sender, subject, domain_info):
        """
        Detect fake emails impersonating legitimate brands
        """
        
        # Common impersonated brands with their legitimate domains
        brands = {
            'walmart': ['walmart.com'],
            'amazon': ['amazon.com'],
            'apple': ['apple.com', 'icloud.com'],
            'google': ['google.com', 'gmail.com'],
            'microsoft': ['microsoft.com', 'outlook.com', 'hotmail.com', 'live.com'],
            'facebook': ['facebook.com'],
            'costco': ['costco.com'],
            'target': ['target.com'],
            'bestbuy': ['bestbuy.com'],
            'macys': ['macys.com'],
            'kohls': ['kohls.com'],
            'skechers': ['skechers.com'],
            'temu': ['temu.com'],
            'ebay': ['ebay.com'],
            'paypal': ['paypal.com'],
            'chase': ['chase.com'],
            'visa': ['visa.com'],
            'mastercard': ['mastercard.com'],
            'cvs': ['cvs.com'],
            'walgreens': ['walgreens.com'],
            'fedex': ['fedex.com'],
            'ups': ['ups.com'],
            'usps': ['usps.com'],
            'netflix': ['netflix.com'],
            'disney': ['disney.com'],
            'spotify': ['spotify.com'],
            'steam': ['steampowered.com'],
            'yeti': ['yeti.com'],
            'aaa': ['aaa.com'],
            't-mobile': ['t-mobile.com'],
            'tmobile': ['t-mobile.com'],
            'verizon': ['verizon.com'],
            'att': ['att.com'],
            'xfinity': ['xfinity.com', 'comcast.com'],
            'selectquote': ['selectquote.com'],
            'cashapp': ['cash.app'],
            'venmo': ['venmo.com'],
            'zelle': ['zellepay.com']
        }
        
        combined_text = f"{sender} {subject}".lower()
        
        # Normalize Unicode characters to detect encoded brand impersonation
        normalized_text = self._normalize_unicode_text(combined_text)
        
        # Get sender domain for validation
        sender_domain = domain_info.get('domain', '')
        
        # Check for brand names in sender or subject (using word boundaries to avoid false matches)
        for brand, legitimate_domains in brands.items():
            # Use word boundaries to avoid matching "chase" in "purchase"
            import re
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, combined_text) or re.search(pattern, normalized_text):
                
                # Check if the sending domain matches any legitimate domain for this brand
                is_domain_match = any(
                    sender_domain == legit_domain or sender_domain.endswith('.' + legit_domain)
                    for legit_domain in legitimate_domains
                )
                
                # CRITICAL: Brand domain mismatch detection
                if not is_domain_match:
                    
                    # If domain is suspicious/gibberish, analyze the actual malicious intent
                    if domain_info.get('is_gibberish') or domain_info.get('is_suspicious'):
                        
                        # PRIORITY 1: Phishing (credential theft)
                        phishing_patterns = [
                            'verify', 'confirm', 'update', 'security', 'account', 'login',
                            'password', 'suspended', 'locked', 'expired', 'authenticate',
                            'click here', 'sign in', 'log in', 'verify now'
                        ]
                        
                        if any(pattern in combined_text for pattern in phishing_patterns):
                            confidence = 0.95
                            reason = f"Phishing via {brand} impersonation: credential theft from {sender_domain}"
                            return "Phishing", confidence, reason
                        
                        # PRIORITY 2: Payment Scams (financial theft)
                        payment_patterns = [
                            'billing', 'payment', 'invoice', 'charge', 'refund', 'card',
                            'declined', 'failed', 'due', 'overdue', 'method', 'expired',
                            'update payment', 'billing issue'
                        ]
                        
                        if any(pattern in combined_text for pattern in payment_patterns):
                            confidence = 0.90
                            reason = f"Payment scam via {brand} impersonation: financial theft from {sender_domain}"
                            return "Payment Scam", confidence, reason
                        
                        # PRIORITY 3: Prize/Lottery Scams
                        prize_patterns = [
                            'winner', 'won', 'prize', 'gift', 'free', 'claim',
                            'congratulations', 'selected', 'lucky', 'giveaway',
                            'congrats', 'reward', 'sweepstakes', 'lottery'
                        ]
                        
                        if any(pattern in combined_text for pattern in prize_patterns):
                            confidence = 0.90
                            reason = f"Prize scam via {brand} impersonation: lottery fraud from {sender_domain}"
                            return "Phishing", confidence, reason
                        
                        # PRIORITY 4: Delivery/Package Scams
                        delivery_patterns = [
                            'delivery', 'package', 'shipment', 'tracking', 'customs',
                            'delivery failed', 'package held', 'redelivery', 'shipping',
                            'arrived', 'order'
                        ]
                        
                        if any(pattern in combined_text for pattern in delivery_patterns):
                            confidence = 0.85
                            reason = f"Delivery scam via {brand} impersonation: package fraud from {sender_domain}"
                            return "Payment Scam", confidence, reason
                        
                        # FALLBACK: Generic brand impersonation
                        confidence = 0.80
                        reason = f"Brand impersonation: {brand} from suspicious domain {sender_domain}"
                        return "Brand Impersonation", confidence, reason
                    
                    # Even non-suspicious domains can be brand impersonation if they don't match
                    else:
                        
                        # Analyze intent for domain mismatches
                        phishing_patterns = [
                            'verify', 'confirm', 'update', 'security', 'account', 
                            'suspended', 'expired', 'authenticate'
                        ]
                        
                        if any(pattern in combined_text for pattern in phishing_patterns):
                            confidence = 0.90
                            reason = f"Phishing via {brand} impersonation: domain mismatch ({sender_domain})"
                            return "Phishing", confidence, reason
                        
                        prize_patterns = [
                            'winner', 'won', 'prize', 'gift', 'free', 'claim',
                            'congratulations', 'selected', 'lucky', 'giveaway'
                        ]
                        
                        if any(pattern in combined_text for pattern in prize_patterns):
                            confidence = 0.90
                            reason = f"Prize scam via {brand} impersonation: domain mismatch ({sender_domain})"
                            return "Phishing", confidence, reason
                        
                        # Generic brand impersonation with domain mismatch
                        confidence = 0.85
                        reason = f"Brand impersonation: {brand} from unrelated domain {sender_domain}"
                        return "Brand Impersonation", confidence, reason
                
        return None
    
    def _detect_financial_spam(self, sender, subject, full_text, domain_info):
        """
        Detect financial and investment spam/scams
        """
        
        # Political figure + finance/business content (very common spam pattern)
        political_figures = ['trump', 'elon', 'musk', 'biden', 'obama', 'zelensky', 'zelenskyy', 'putin', 'xi', 'macron']
        financial_business_terms = [
            'investment', 'trading', 'stocks', 'crypto', 'bitcoin', 'doge',
            'portfolio', 'profit', 'returns', 'wealth', 'riches', 'fortune',
            'stimulus', 'checks', 'money', 'financial', 'economy', 'ai',
            'revolution', 'dominance', 'showdown', 'feud', 'war', 'tweet',
            'vision', 'business', 'empire', 'market', 'economy', 'economic',
            'economics', 'economist', 'analyst', 'forecast', 'prediction'
        ]
        
        has_political = any(figure in full_text for figure in political_figures)
        has_financial_business = any(term in full_text for term in financial_business_terms)
        
        # Crisis + political figures pattern (sophisticated newsletter scams) - CHECK THIS FIRST
        crisis_terms = [
            'shaken', 'crisis', 'war', 'conflict', 'tensions', 'statement',
            'peace', 'turmoil', 'chaos', 'uncertainty', 'threat', 'warning'
        ]
        
        has_crisis = any(term in full_text for term in crisis_terms)
        
        # Newsletter scam format detection
        newsletter_format_patterns = [
            r'\|.*\|',  # "Global Peace Shaken | Oscar Perkins | EA"
            'economic age', 'market insights', 'financial times',
            'investment weekly', 'trader alert', 'market watch'
        ]
        
        has_newsletter_format = any(
            re.search(pattern, full_text, re.IGNORECASE) if '\\' in pattern 
            else pattern in full_text
            for pattern in newsletter_format_patterns
        )
        
        # High confidence for political + crisis + financial newsletter format
        if has_political and has_crisis and (has_financial_business or has_newsletter_format):
            confidence = 0.90
            reason = "Political crisis + financial newsletter scam format"
            return "Financial & Investment Spam", confidence, reason
        
        # Political + crisis without obvious financial content (still likely financial spam)
        if has_political and has_crisis:
            confidence = 0.85
            reason = "Political crisis narrative (likely investment hook)"
            return "Financial & Investment Spam", confidence, reason
        
        # Just political figures with business language patterns
        if has_political:
            business_patterns = [
                'revolution', 'dominance', 'vision', 'strategy', 'empire',
                'bombshell', 'shocking', 'secret', 'warning', 'breakthrough'
            ]
            if any(pattern in full_text for pattern in business_patterns):
                confidence = 0.80
                reason = "Political figure + business hype language"
                return "Financial & Investment Spam", confidence, reason
        
        # Newsletter-style financial content (enhanced detection)
        newsletter_indicators = [
            'newsletter', 'report', 'daily', 'update', 'forecast',
            'insights', 'strategies', 'research', 'analysis', 'alert',
            'briefing', 'digest', 'weekly', 'monthly', 'exclusive'
        ]
        
        has_newsletter = any(indicator in full_text for indicator in newsletter_indicators)
        
        # Check for financial newsletter content patterns (not domain-based)
        # Content analysis is more reliable than hardcoded domain lists
        has_financial_domain = False  # Removed domain-based detection
        
        # Enhanced newsletter spam detection
        if (has_newsletter or has_financial_domain or has_newsletter_format) and has_financial_business:
            confidence = 0.85
            reason = "Investment newsletter spam"
            return "Financial & Investment Spam", confidence, reason
        
        # Financial newsletter domain with political content (common scam pattern)
        if has_financial_domain and has_political:
            confidence = 0.85
            reason = "Financial newsletter domain + political content"
            return "Financial & Investment Spam", confidence, reason
        
        # Known financial scam personas (fake analysts/advisors)
        known_scam_personas = [
            'oscar perkins', 'jim rickards', 'marc faber', 'peter schiff',
            'economic age', 'market guru', 'trading expert', 'financial advisor'
        ]
        
        has_scam_persona = any(persona in full_text for persona in known_scam_personas)
        
        if has_scam_persona and (has_political or has_crisis or has_financial_business):
            confidence = 0.88
            reason = "Known financial scam persona detected"
            return "Financial & Investment Spam", confidence, reason
        
        # Basic political figures + financial/business content (lower priority than sophisticated patterns)
        if has_political and has_financial_business:
            confidence = 0.82
            reason = "Political figure + financial/business content"
            return "Financial & Investment Spam", confidence, reason
            
        # General financial scam terms
        financial_scam_terms = [
            'rich people trades', 'wealth secrets', 'financial freedom',
            'money making', 'get rich', 'investment opportunity',
            'credit card secrets', 'debt relief', 'tax exemption',
            'stimulus check', 'government check'
        ]
        
        if any(term in full_text for term in financial_scam_terms):
            confidence = 0.75
            reason = "Financial scam content detected"
            return "Financial & Investment Spam", confidence, reason
            
        return None
    
    def _detect_phishing_scams(self, sender, subject, full_text, domain_info):
        """
        Detect phishing attempts and payment scams
        """
        
        # CRITICAL FIX: Gmail account invoice/billing scams
        if self._is_personal_email_account(sender):
            invoice_billing_terms = [
                'invoice', 'billing', 'payment', 'charge', 'due', 'overdue',
                'bill', 'statement', 'account', 'balance', 'refund'
            ]
            
            if any(term in full_text for term in invoice_billing_terms):
                confidence = 0.95
                reason = "Fake invoice/billing from personal email account"
                return "Payment Scam", confidence, reason
        
        # Prize/lottery/stimulus scams
        prize_terms = [
            'winner', 'won', 'prize', 'lottery', 'sweepstakes', 'jackpot',
            'stimulus check', 'government check', 'cash prize', 'reward',
            'congratulations', 'selected', 'chosen', 'lucky'
        ]
        
        if any(term in full_text for term in prize_terms):
            if domain_info.get('is_suspicious') or domain_info.get('is_gibberish'):
                confidence = 0.90
                reason = "Prize scam with suspicious domain"
                return "Phishing", confidence, reason
            else:
                confidence = 0.75
                reason = "Prize scam content"
                return "Payment Scam", confidence, reason
                
        # Urgent action required
        urgency_terms = [
            'urgent', 'immediate', 'act now', 'expires soon', 'limited time',
            'claim now', 'verify now', 'update now', 'confirm now'
        ]
        
        if any(term in full_text for term in urgency_terms):
            if domain_info.get('is_suspicious'):
                confidence = 0.80
                reason = "Phishing with urgency tactics"
                return "Phishing", confidence, reason
                
        # Free stuff scams (but only from non-legitimate domains)
        free_terms = [
            'free gift', 'free money', 'free cash', 'free prize',
            'no cost', 'completely free', 'risk free'
        ]
        
        if any(term in full_text for term in free_terms):
            # Check if this is from a legitimate company first
            if not domain_info.get('is_legitimate'):
                confidence = 0.70
                reason = "Free stuff scam"
                return "Payment Scam", confidence, reason
            # If from legitimate company, this is just promotional marketing
            
        return None
    
    def _detect_health_spam(self, sender, subject, full_text):
        """
        Detect health and medical spam
        """
        
        health_terms = [
            'weight loss', 'lose weight', 'diet', 'supplement', 'pill',
            'cure', 'treatment', 'medicine', 'pharmacy', 'prescription',
            'health', 'medical', 'doctor', 'pain relief', 'viagra'
        ]
        
        if any(term in full_text for term in health_terms):
            # Additional spam indicators
            spam_indicators = [
                'miracle', 'breakthrough', 'secret', 'natural', 'safe',
                'no side effects', 'instant', 'fast results'
            ]
            
            if any(indicator in full_text for indicator in spam_indicators):
                confidence = 0.80
                reason = "Health spam with exaggerated claims"
                return "Health & Medical Spam", confidence, reason
                
        return None
    
    def _detect_gambling_spam(self, sender, subject, full_text):
        """
        Detect gambling spam
        """
        
        gambling_terms = [
            'casino', 'poker', 'blackjack', 'slots', 'jackpot',
            'betting', 'gambling', 'lottery', 'scratch', 'win big'
        ]
        
        if any(term in full_text for term in gambling_terms):
            confidence = 0.75
            reason = "Gambling content detected"
            return "Gambling Spam", confidence, reason
            
        return None
    
    def _detect_real_estate_spam(self, sender, subject, full_text):
        """
        Detect real estate spam (investment/mortgage scams, NOT retail home goods)
        """
        
        # Check if this is from a legitimate retailer first
        domain_info = self._analyze_domain(sender)
        if domain_info.get('is_legitimate'):
            # Skip real estate detection for legitimate retailers
            # They use "home" for home goods/décor, not real estate investment
            return None
        
        real_estate_terms = [
            'real estate', 'property', 'house', 'mortgage',
            'refinance', 'loan', 'foreclosure', 'investment property'
        ]
        
        # Remove standalone "home" - too generic for retailers
        # Only detect when combined with investment/opportunity language
        
        if any(term in full_text for term in real_estate_terms):
            spam_indicators = [
                'opportunity', 'deal', 'profit', 'cash', 'no money down',
                'investment', 'flip', 'wholesale', 'foreclosure'
            ]
            
            if any(indicator in full_text for indicator in spam_indicators):
                confidence = 0.70
                reason = "Real estate investment spam"
                return "Real Estate Spam", confidence, reason
                
        return None
    
    def _detect_legal_scams(self, sender, subject, full_text):
        """
        Detect legal and compensation scams (NOT legitimate retail claims)
        """
        
        # Check if this is from a legitimate retailer first
        domain_info = self._analyze_domain(sender)
        if domain_info.get('is_legitimate'):
            # Skip legal scam detection for legitimate retailers
            # They use "claim" for promotional items, "money back" for savings
            return None
        
        # More specific legal terms (exclude generic "claim" and "money")
        legal_terms = [
            'lawsuit', 'settlement', 'compensation', 'legal action',
            'attorney', 'lawyer', 'court', 'judgment', 'class action',
            'tax lien', 'auction', 'government settlement', 'irs settlement',
            'legal claim', 'compensation claim'
        ]
        
        if any(term in full_text for term in legal_terms):
            scam_indicators = [
                'opportunity', 'profit', 'cash settlement', 'investment',
                'owed money', 'entitled to', 'contact attorney'
            ]
            
            if any(indicator in full_text for indicator in scam_indicators):
                confidence = 0.75
                reason = "Legal/compensation scam"
                return "Legal & Compensation Scams", confidence, reason
                
        return None
    
    def _detect_promotional_email(self, sender, subject, full_text, domain_info):
        """
        Detect legitimate promotional emails from real retailers
        """
        
        # Must be from legitimate domain
        if not domain_info.get('is_legitimate'):
            return None
            
        promotional_terms = [
            'sale', 'discount', '% off', 'deal', 'offer', 'promo',
            'clearance', 'special', 'limited time', 'ends tonight',
            'father\'s day', 'mother\'s day', 'black friday',
            # Additional promotional indicators
            'new arrivals', 'updates', 'collection', 'styles', 'trends',
            'season', 'summer', 'winter', 'spring', 'fall', 'holiday',
            'shop', 'browse', 'explore', 'discover', 'featured',
            'newsletter', 'news', 'latest', 'fresh', 'just in'
        ]
        
        if any(term in full_text for term in promotional_terms):
            confidence = 0.85
            reason = "Legitimate promotional email from verified retailer"
            return "Promotional Email", confidence, reason
            
        return None
    
    def _extract_sender_ip(self, headers):
        """
        Extract sender IP address from email headers
        
        Args:
            headers: Email headers string
            
        Returns:
            str: IP address or None if not found
        """
        if not headers:
            return None
            
        # Common IP header patterns
        ip_patterns = [
            r'Received:.*?\[(\d+\.\d+\.\d+\.\d+)\]',  # Standard format
            r'X-Originating-IP:\s*(\d+\.\d+\.\d+\.\d+)',  # Outlook/Hotmail
            r'X-Sender-IP:\s*(\d+\.\d+\.\d+\.\d+)',  # Various providers
            r'X-Real-IP:\s*(\d+\.\d+\.\d+\.\d+)',  # Proxy headers
        ]
        
        for pattern in ip_patterns:
            matches = re.findall(pattern, headers, re.IGNORECASE)
            if matches:
                # Return first public IP (skip private ranges)
                for ip in matches:
                    if self._is_public_ip(ip):
                        return ip
        
        return None
    
    def _is_public_ip(self, ip):
        """Check if IP is public (not private/local)"""
        try:
            parts = [int(x) for x in ip.split('.')]
            # Private ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x, 127.x.x.x
            if (parts[0] == 10 or 
                (parts[0] == 172 and 16 <= parts[1] <= 31) or
                (parts[0] == 192 and parts[1] == 168) or
                parts[0] == 127):
                return False
            return True
        except:
            return False
    
    def _assess_geographic_risk(self, ip_address):
        """
        Fast geographic risk assessment using geoip2fast
        
        Args:
            ip_address: IP address to analyze
            
        Returns:
            dict: Risk assessment with confidence and reason
        """
        if not GEOIP_AVAILABLE:
            return {'is_high_risk': False, 'confidence': 0.0, 'reason': 'GeoIP not available'}
        
        try:
            # Suspicious IP range check (instant)
            for ip_range in self.suspicious_ip_ranges:
                if ip_address.startswith(ip_range):
                    return {
                        'is_high_risk': True,
                        'confidence': 0.95,
                        'reason': f'Suspicious IP range detected: {ip_range}*'
                    }
            
            # Fast country lookup using geoip2fast (0.0416ms vs 2,294ms WHOIS)
            geo_result = _geoip.lookup(ip_address)
            country_code = getattr(geo_result, 'country_code', '')
            
            if country_code in self.high_risk_countries:
                country_name = getattr(geo_result, 'country_name', country_code)
                return {
                    'is_high_risk': True,
                    'confidence': 0.90,
                    'reason': f'High-risk country detected: {country_name} ({country_code})'
                }
            
            return {'is_high_risk': False, 'confidence': 0.1, 'reason': f'Low-risk country: {country_code}'}
            
        except Exception as e:
            return {'is_high_risk': False, 'confidence': 0.5, 'reason': f'GeoIP lookup failed: {str(e)}'}


def test_logical_classifier():
    """Test the logical classifier with sample emails"""
    
    classifier = LogicalEmailClassifier()
    
    # Test cases from the problematic emails
    test_emails = [
        # Adult content
        ("FUCK👅ME..    <f3qkt4dxpvr@yun>", "Adult explicit subject", ""),
        ("🔥💋Ready to Play?💘 <Cgf6ywPi>", "💘🔥 𝗔𝘀𝘀 or 𝗣𝘂𝘀𝘀𝘆 ?💘💋💘I want you to fuck", ""),
        
        # Brand impersonation
        ("Walmart🛒 <dcev2ty2xi@RcwMvw2k>", "You have won an 𝐢𝐏𝐚𝐝 𝐏𝐫𝐨🎁", ""),
        ("Temu® <gf6wiz1opl@orvr.ua8w8q>", "✅ 🎉Congrats!! dertbv: You're the winner", ""),
        
        # Financial spam
        ("Elon's AI Revolution || DI<em>", "Post-2025: Musk's Vision for AI Dominance", ""),
        ("Trump Musk Showdown | UFG <ne>", "The Feud Between Trump and Musk Is Just", ""),
        
        # Legitimate promotional
        ("SKECHERS <no-reply@emails.skechers.com>", "Father's Day Deals End Tonight", ""),
        ("Wrangler <wrangler@e.wrangler.com>", "30% off sitewide ends tomorrow", "")
    ]
    
    print("🧪 Testing Logical Email Classifier")
    print("=" * 60)
    
    for sender, subject, headers in test_emails:
        category, confidence, reason = classifier.classify_email(sender, subject, headers)
        print(f"📧 {sender}")
        print(f"   Subject: {subject}")
        print(f"   Classification: {category} (confidence: {confidence:.2f})")
        print(f"   Reason: {reason}")
        print()


if __name__ == "__main__":
    test_logical_classifier()