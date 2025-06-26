#!/usr/bin/env python3
"""
Selective Vendor Filter - Universal Transactional vs Marketing Email Classification

This module provides intelligent filtering that preserves important emails (orders, bills, alerts)
while allowing users to block promotional content from the same vendors.

Key Features:
- Vendor-specific email pattern recognition
- Transactional vs Marketing classification
- User preference management
- ML-enhanced intent detection
- Seamless integration with existing spam classifier
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
from atlas_email.models.database import db

class EmailIntent(Enum):
    """Email intent classification"""
    TRANSACTIONAL = "transactional"    # Orders, bills, alerts, confirmations
    MARKETING = "marketing"            # Promotions, deals, recommendations  
    SERVICE = "service"                # Customer service, support
    SECURITY = "security"              # Fraud alerts, password resets
    PROMOTIONAL = "promotional"        # Surveys, reviews, newsletters
    UNKNOWN = "unknown"                # Cannot determine intent

@dataclass
class VendorEmailClassification:
    """Result of vendor email classification"""
    vendor: str
    intent: EmailIntent
    confidence: float
    reasoning: str
    should_preserve: bool
    matched_patterns: List[str]

class SelectiveVendorFilter:
    """
    Universal selective vendor filtering system
    
    Distinguishes between important emails (transactional) and promotional emails
    for major vendors based on content analysis and user preferences.
    """
    
    def __init__(self):
        """Initialize the selective vendor filter"""
        self.vendor_patterns = self._load_vendor_patterns()
        self.user_preferences = self._load_user_preferences()
        self.universal_patterns = self._load_universal_patterns()
        
        # Initialize ML components if available
        try:
            from atlas_email.ml.feature_extractor import MLFeatureExtractor
            self.ml_extractor = MLFeatureExtractor()
            self.ml_available = True
        except ImportError:
            self.ml_available = False
            
        logging.info("🎯 Selective Vendor Filter initialized")
    
    def _load_vendor_patterns(self) -> Dict[str, Dict]:
        """Load comprehensive vendor email patterns"""
        return {
            # FINANCIAL SERVICES
            'chase.com': {
                'transactional': {
                    'senders': [
                        'alerts@chase.com', 'statements@chase.com', 'fraud@chase.com',
                        'noreply@chase.com', 'customerservice@chase.com'
                    ],
                    'keywords': [
                        'statement ready', 'payment due', 'payment received', 'balance',
                        'fraud alert', 'security alert', 'account locked', 'password changed',
                        'payment confirmation', 'autopay', 'minimum payment', 'credit limit',
                        'dispute resolution', 'chargeback', 'transaction declined'
                    ],
                    'patterns': [
                        r'statement.*ready', r'payment.*due', r'fraud.*alert',
                        r'account.*ending.*\d{4}', r'\$\d+\.\d{2}.*due'
                    ]
                },
                'marketing': {
                    'senders': [
                        'offers@chase.com', 'marketing@chase.com', 'promotions@chase.com'
                    ],
                    'keywords': [
                        'pre-approved', 'special offer', 'cash back offer', 'bonus points',
                        'upgrade offer', 'new card', 'limited time', 'exclusive offer',
                        'earn rewards', 'rate your experience', 'survey', 'feedback'
                    ],
                    'patterns': [
                        r'\d+%.*cash back', r'pre-approved.*for', r'limited.*time.*offer',
                        r'bonus.*points', r'special.*rate'
                    ]
                }
            },
            
            'capitalone.com': {
                'transactional': {
                    'keywords': [
                        'payment reminder', 'statement ready', 'fraud alert', 'security notice',
                        'payment posted', 'account summary', 'credit score update',
                        'payment due', 'autopay', 'minimum payment'
                    ],
                    'senders': ['noreply@capitalone.com', 'alerts@capitalone.com']
                },
                'marketing': {
                    'keywords': [
                        'earn miles', 'cash back', 'limited time offer', 'new card offer',
                        'upgrade your card', 'bonus offer', 'special promotion'
                    ]
                }
            },
            
            'bankofamerica.com': {
                'transactional': {
                    'keywords': [
                        'eStatement', 'payment due', 'fraud alert', 'security alert',
                        'account alert', 'payment received', 'balance alert',
                        'overdraft notice', 'deposit confirmation'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'special offer', 'preferred rewards', 'credit card offer',
                        'mortgage rates', 'investment opportunity'
                    ]
                }
            },
            
            # E-COMMERCE PLATFORMS
            'amazon.com': {
                'transactional': {
                    'senders': [
                        'auto-confirm@amazon.com', 'shipment-tracking@amazon.com',
                        'payments-messages@amazon.com', 'account-update@amazon.com',
                        'returns@amazon.com', 'digital-no-reply@amazon.com'
                    ],
                    'keywords': [
                        'order confirmation', 'shipped', 'delivered', 'tracking number',
                        'invoice', 'receipt', 'refund', 'return', 'cancelled',
                        'payment declined', 'billing', 'subscription', 'renewal',
                        'security alert', 'password changed', 'sign-in detected'
                    ],
                    'patterns': [
                        r'order.*#\w+', r'tracking.*#\w+', r'delivered.*to',
                        r'refund.*processed', r'return.*initiated'
                    ]
                },
                'marketing': {
                    'senders': [
                        'store-news@amazon.com', 'deals@amazon.com',
                        'advertising@amazon.com', 'recommendations@amazon.com'
                    ],
                    'keywords': [
                        'recommended for you', 'customers who bought', 'lightning deal',
                        'daily deals', 'prime day', 'black friday', 'cyber monday',
                        'new arrivals', 'inspired by', 'browsing history',
                        'wish list', 'save for later'
                    ],
                    'patterns': [
                        r'recommended.*for.*you', r'customers.*who.*bought',
                        r'\d+%.*off', r'lightning.*deal'
                    ]
                }
            },
            
            'target.com': {
                'transactional': {
                    'keywords': [
                        'order confirmation', 'shipped', 'pickup ready', 'delivered',
                        'return processed', 'refund issued', 'order cancelled',
                        'payment received', 'gift card', 'registry'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'weekly ad', 'circle offers', 'new arrivals', 'sale alert',
                        'clearance', 'seasonal deals', 'back to school', 'holiday deals'
                    ]
                }
            },
            
            'walmart.com': {
                'transactional': {
                    'keywords': [
                        'order update', 'delivery', 'pickup', 'refund processed',
                        'order shipped', 'order ready', 'payment confirmation'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'rollback prices', 'clearance', 'seasonal deals', 'weekly savings',
                        'new arrivals', 'special buys'
                    ]
                }
            },
            
            'bestbuy.com': {
                'transactional': {
                    'keywords': [
                        'order shipped', 'ready for pickup', 'geek squad', 'warranty',
                        'repair status', 'service appointment', 'invoice', 'receipt'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'tech deals', 'member offers', 'new products', 'sale alert',
                        'deal of the day', 'weekly ad'
                    ]
                }
            },
            
            'ebay.com': {
                'transactional': {
                    'keywords': [
                        'purchase confirmation', 'payment received', 'item shipped',
                        'seller message', 'dispute resolution', 'refund processed',
                        'order confirmation', 'tracking information', 'delivery confirmation'
                    ],
                    'senders': [
                        'ebay@reply.ebay.com', 'noreply@ebay.com', 'payments@ebay.com'
                        # Removed 'ebay@emails.ebay.com' as it's used for both transactional AND marketing
                    ]
                },
                'marketing': {
                    'keywords': [
                        'daily deals', 'recommended items', 'similar items',
                        'new listings', 'price drop', 'auction ending',
                        'based on your recent activity', 'might like', 'viewing history',
                        # Product promotional terms
                        'essentials', 'skincare', 'anti-aging', 'beauty', 'cosmetic',
                        'featured', 'trending', 'must-have', 'bestseller', 'popular',
                        'new arrivals', 'special offer', 'limited time', 'exclusive',
                        # Financial promotional terms (critical for eBay/Klarna case)
                        '0% interest', 'no interest', 'financing available', 'pay later',
                        'monthly payments', 'installments', 'buy now pay later',
                        'klarna', 'paypal credit', 'affirm', 'sezzle',
                        # Health & beauty categories
                        'wellness', 'health', 'supplement', 'vitamin', 'nutrition',
                        'fashion', 'style', 'accessories', 'jewelry', 'clothing'
                    ],
                    'senders': [
                        'ebay-deals@ebay.com',  # Add specific marketing senders if known
                        'ebay@reply.ebay.com'   # Common promotional sender
                    ],
                    'patterns': [
                        r'recommended.*items', r'similar.*items', r'based.*on.*your.*recent',
                        r'might.*like', r'viewing.*history', r'essentials.*for',
                        r'anti-aging.*\w+', r'skincare.*\w+', r'beauty.*\w+'
                    ]
                }
            },
            
            # UTILITIES & TELECOM
            'verizon.com': {
                'transactional': {
                    'keywords': [
                        'bill ready', 'payment received', 'service alert', 'outage',
                        'payment due', 'autopay', 'usage alert', 'data usage',
                        'service appointment', 'technician visit', 'bill is ready'
                    ],
                    'senders': [
                        'verizonwireless@vtext.com', 'noreply@verizon.com',
                        'alerts@verizon.com', 'billing@verizon.com'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'upgrade offer', 'new plans', 'device deals', 'fios offers',
                        'unlimited plan', 'trade-in offer', 'special pricing'
                    ]
                }
            },
            
            'att.com': {
                'transactional': {
                    'keywords': [
                        'bill statement', 'payment confirmation', 'service notification',
                        'usage alert', 'account alert', 'appointment reminder'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'upgrade eligible', 'new device', 'special offers', 'plan upgrade',
                        'unlimited data', 'fiber internet'
                    ]
                }
            },
            
            'comcast.com': {
                'transactional': {
                    'keywords': [
                        'bill statement', 'service appointment', 'outage notification',
                        'payment received', 'equipment return', 'service call'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'speed upgrade', 'tv packages', 'bundle offers', 'new services',
                        'xfinity deals', 'internet upgrade'
                    ]
                }
            },
            
            # STREAMING SERVICES
            'netflix.com': {
                'transactional': {
                    'keywords': [
                        'payment received', 'billing', 'subscription', 'account',
                        'password changed', 'payment declined', 'plan change'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'new releases', 'recommended', 'trending now', 'coming soon',
                        'popular shows', 'because you watched'
                    ]
                }
            },
            
            'spotify.com': {
                'transactional': {
                    'keywords': [
                        'payment confirmation', 'subscription', 'billing', 'account',
                        'premium renewal', 'payment failed'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'your wrapped', 'discover weekly', 'new music', 'playlist',
                        'premium offer', 'family plan'
                    ]
                }
            },
            
            # AIRLINES & TRAVEL
            'delta.com': {
                'transactional': {
                    'keywords': [
                        'boarding pass', 'flight confirmation', 'check-in', 'gate change',
                        'flight delay', 'cancellation', 'itinerary', 'booking confirmation'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'skymiles offer', 'vacation packages', 'flight deals',
                        'destination deals', 'credit card offer'
                    ]
                }
            },
            
            'united.com': {
                'transactional': {
                    'keywords': [
                        'flight confirmation', 'mobile boarding', 'check-in reminder',
                        'flight status', 'gate assignment', 'baggage'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'mileageplus', 'flight deals', 'vacation packages',
                        'credit card', 'explorer card'
                    ]
                }
            },
            
            # INSURANCE & HEALTHCARE
            'geico.com': {
                'transactional': {
                    'keywords': [
                        'policy documents', 'bill due', 'payment received',
                        'claim update', 'policy renewal', 'id cards'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'save money', 'quote', 'switch and save', 'new customer',
                        'additional coverage', 'bundle discount'
                    ]
                }
            },
            
            'statefarm.com': {
                'transactional': {
                    'keywords': [
                        'policy statement', 'payment due', 'claim status',
                        'policy change', 'renewal notice', 'documents ready'
                    ]
                },
                'marketing': {
                    'keywords': [
                        'save with bundling', 'new coverage', 'rate quote',
                        'life insurance', 'additional protection'
                    ]
                }
            }
        }
    
    def _load_universal_patterns(self) -> Dict[str, List[str]]:
        """Load universal email patterns that apply across vendors"""
        return {
            'transactional_indicators': [
                # Financial patterns
                r'\$\d+\.\d{2}',                    # Dollar amounts
                r'due\s+date',                      # Payment due dates
                r'confirmation\s*#\s*\w+',          # Confirmation numbers
                r'tracking\s*#\s*\w+',              # Tracking numbers
                r'account\s+ending\s+in\s+\d{4}',   # Account references
                r'order\s*#\s*\w+',                 # Order numbers
                r'invoice\s*#\s*\w+',               # Invoice numbers
                r'reference\s*#\s*\w+',             # Reference numbers
                
                # Time-sensitive notifications
                r'fraud\s+alert',                   # Security alerts
                r'security\s+alert',                # Security notifications
                r'password\s+changed',              # Account changes
                r'login\s+detected',                # Security notifications
                r'payment\s+(received|processed)',  # Payment confirmations
                r'refund\s+(issued|processed)',     # Refund notifications
                
                # Delivery/shipping
                r'shipped.*to',                     # Shipping notifications
                r'delivered.*to',                   # Delivery confirmations
                r'out\s+for\s+delivery',           # Delivery status
                r'ready\s+for\s+pickup',           # Pickup notifications
            ],
            
            'marketing_indicators': [
                # Promotional language
                r'\d+%\s*off',                      # Percentage discounts
                r'limited\s+time',                  # Urgency tactics
                r'act\s+now',                       # Call to action
                r'expires\s+\w+',                   # Expiration dates
                r'special\s+offer',                 # Special offers
                r'exclusive\s+deal',                # Exclusive offers
                r'pre-approved',                    # Credit offers
                r'don\'t\s+miss',                   # FOMO tactics
                
                # Marketing terms
                r'recommended\s+for\s+you',         # Personalized recommendations
                r'customers\s+who\s+bought',        # Social proof
                r'because\s+you\s+bought',          # Purchase history
                r'new\s+arrivals',                  # Product announcements
                r'trending\s+now',                  # Popularity indicators
                r'bestsellers',                     # Popular products
                
                # Promotional events
                r'black\s+friday',                  # Sales events
                r'cyber\s+monday',                  # Sales events
                r'prime\s+day',                     # Amazon sales
                r'flash\s+sale',                    # Urgent sales
                r'clearance',                       # Inventory clearance
            ],
            
            'service_indicators': [
                r'customer\s+service',              # Customer service
                r'support\s+ticket',                # Support requests
                r'help\s+center',                   # Help documentation
                r'FAQ',                             # Frequently asked questions
                r'contact\s+us',                    # Contact information
            ]
        }
    
    def _load_user_preferences(self) -> Dict[str, Dict[str, bool]]:
        """Load user preferences for vendor email types"""
        try:
            # Try to load from database
            preferences = db.execute_query("""
                SELECT vendor_domain, email_type, allow_emails 
                FROM user_vendor_preferences 
                WHERE user_id = 'default'
            """)
            
            result = {}
            for pref in preferences:
                vendor = pref['vendor_domain']
                if vendor not in result:
                    result[vendor] = {}
                result[vendor][pref['email_type']] = bool(pref['allow_emails'])
            
            return result
            
        except Exception:
            # Return smart defaults if database not available
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Dict[str, bool]]:
        """Get smart default preferences for new users"""
        return {
            # Financial services - preserve important, block promotional
            'financial_default': {
                'transactional': True,   # Bills, statements, alerts
                'security': True,        # Fraud alerts, security notices
                'service': True,         # Customer service communications
                'marketing': False,      # Credit offers, promotions
                'promotional': False     # Surveys, rate requests
            },
            
            # E-commerce - preserve orders, block marketing
            'ecommerce_default': {
                'transactional': True,   # Orders, shipping, returns
                'security': True,        # Account security
                'service': True,         # Customer service
                'marketing': False,      # Product recommendations
                'promotional': False     # Reviews, surveys
            },
            
            # Utilities - preserve service, block upgrades
            'utilities_default': {
                'transactional': True,   # Bills, service alerts
                'security': True,        # Account security
                'service': True,         # Outage notifications
                'marketing': False,      # Upgrade offers
                'promotional': False     # Surveys, promotions
            },
            
            # Streaming - preserve billing, block content recommendations
            'streaming_default': {
                'transactional': True,   # Billing, subscriptions
                'security': True,        # Account security
                'service': True,         # Service notifications
                'marketing': True,       # Content recommendations (many users want these)
                'promotional': False     # Surveys, promotions
            }
        }
    
    def extract_vendor_from_email(self, sender_email: str, sender_domain: str = None) -> Optional[str]:
        """Extract vendor identifier from email sender"""
        if not sender_email:
            return None
            
        # Clean and normalize sender email
        sender_clean = sender_email.lower().strip()
        
        # Extract domain if not provided
        if not sender_domain:
            if '@' in sender_clean:
                sender_domain = sender_clean.split('@')[-1]
            else:
                return None
        
        # Direct vendor match
        if sender_domain in self.vendor_patterns:
            return sender_domain
            
        # Check for parent domain matches
        domain_parts = sender_domain.split('.')
        if len(domain_parts) >= 2:
            # Try parent domain (e.g., mail.amazon.com -> amazon.com)
            parent_domain = '.'.join(domain_parts[-2:])
            if parent_domain in self.vendor_patterns:
                return parent_domain
                
        # Check for known subdomains
        for vendor in self.vendor_patterns:
            if sender_domain.endswith(vendor):
                return vendor
        
        # Special handling for known vendor subdomains
        vendor_subdomain_mapping = {
            'vtext.com': 'verizon.com',
            'vzwpix.com': 'verizon.com',
            'reply.ebay.com': 'ebay.com',
            'emails.ebay.com': 'ebay.com'
        }
        
        if sender_domain in vendor_subdomain_mapping:
            return vendor_subdomain_mapping[sender_domain]
                
        return None
    
    def classify_email_intent(self, vendor: str, subject: str, content: str, 
                             sender_email: str) -> VendorEmailClassification:
        """Classify email intent for a specific vendor"""
        
        if vendor not in self.vendor_patterns:
            return VendorEmailClassification(
                vendor=vendor,
                intent=EmailIntent.UNKNOWN,
                confidence=0.0,
                reasoning="Vendor not in configuration",
                should_preserve=True,  # Conservative default
                matched_patterns=[]
            )
        
        vendor_config = self.vendor_patterns[vendor]
        combined_text = f"{subject} {content}".lower()
        matched_patterns = []
        intent_scores = {
            EmailIntent.TRANSACTIONAL: 0.0,
            EmailIntent.MARKETING: 0.0,
            EmailIntent.SERVICE: 0.0,
            EmailIntent.SECURITY: 0.0,
            EmailIntent.PROMOTIONAL: 0.0
        }
        
        # Check vendor-specific patterns
        self._check_vendor_patterns(vendor_config, combined_text, sender_email, 
                                   intent_scores, matched_patterns)
        
        # Check universal patterns
        self._check_universal_patterns(combined_text, intent_scores, matched_patterns)
        
        # Determine primary intent with enhanced logic for ambiguous cases
        max_intent = max(intent_scores.items(), key=lambda x: x[1])
        primary_intent = max_intent[0]
        confidence = max_intent[1]
        
        # Enhanced tie-breaking for mixed-use senders (same sender in both transactional and marketing)
        # Prioritize content over sender when there's ambiguity
        transactional_score = intent_scores[EmailIntent.TRANSACTIONAL]
        marketing_score = intent_scores[EmailIntent.MARKETING]
        
        # Check if this is a mixed-use sender scenario
        sender_in_both_lists = self._is_mixed_use_sender(vendor, sender_email)
        
        if sender_in_both_lists or abs(transactional_score - marketing_score) < 0.3:
            # For mixed-use senders, content should override sender patterns
            content_transactional = sum(1 for p in matched_patterns if 'transactional_keyword' in p or 'transactional_pattern' in p)
            content_marketing = sum(1 for p in matched_patterns if 'marketing_keyword' in p or 'marketing_pattern' in p)
            
            # If content strongly indicates marketing, override sender-based transactional classification
            if content_marketing > content_transactional and content_marketing >= 1:
                primary_intent = EmailIntent.MARKETING
                # Boost confidence when content clearly indicates marketing
                confidence = max(marketing_score + 0.2, 0.8)
                
            # If content strongly indicates transactional, override sender-based marketing classification  
            elif content_transactional > content_marketing and content_transactional >= 1:
                primary_intent = EmailIntent.TRANSACTIONAL
                confidence = max(transactional_score + 0.2, 0.8)
                
            # If still tied, check for universal marketing indicators
            elif content_marketing == content_transactional:
                universal_marketing_count = sum(1 for p in matched_patterns if 'universal_marketing' in p)
                if universal_marketing_count >= 1:
                    primary_intent = EmailIntent.MARKETING
                    confidence = max(marketing_score + 0.15, 0.75)
        
        # Apply ML enhancement if available
        if self.ml_available and confidence < 0.8:
            ml_boost = self._get_ml_intent_boost(subject, content, sender_email)
            confidence = min(1.0, confidence + ml_boost)
        
        # Determine if email should be preserved based on user preferences
        should_preserve = self._should_preserve_email(vendor, primary_intent)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(primary_intent, matched_patterns, confidence)
        
        return VendorEmailClassification(
            vendor=vendor,
            intent=primary_intent,
            confidence=confidence,
            reasoning=reasoning,
            should_preserve=should_preserve,
            matched_patterns=matched_patterns
        )
    
    def _is_mixed_use_sender(self, vendor: str, sender_email: str) -> bool:
        """Check if sender appears in both transactional and marketing sender lists"""
        if vendor not in self.vendor_patterns:
            return False
            
        vendor_config = self.vendor_patterns[vendor]
        sender_clean = sender_email.lower().strip()
        
        # Check if sender is in both transactional and marketing lists
        in_transactional = False
        in_marketing = False
        
        if 'transactional' in vendor_config and 'senders' in vendor_config['transactional']:
            in_transactional = any(sender_pattern.lower() in sender_clean 
                                 for sender_pattern in vendor_config['transactional']['senders'])
        
        if 'marketing' in vendor_config and 'senders' in vendor_config['marketing']:
            in_marketing = any(sender_pattern.lower() in sender_clean 
                             for sender_pattern in vendor_config['marketing']['senders'])
        
        return in_transactional and in_marketing
    
    def _check_vendor_patterns(self, vendor_config: Dict, text: str, sender: str,
                              intent_scores: Dict, matched_patterns: List):
        """Check vendor-specific patterns and update scores"""
        
        # Check transactional patterns
        if 'transactional' in vendor_config:
            trans_config = vendor_config['transactional']
            score = 0.0
            
            # Check sender patterns
            if 'senders' in trans_config:
                for sender_pattern in trans_config['senders']:
                    if sender_pattern.lower() in sender.lower():
                        score += 0.4
                        matched_patterns.append(f"transactional_sender:{sender_pattern}")
            
            # Check keyword patterns
            if 'keywords' in trans_config:
                for keyword in trans_config['keywords']:
                    if keyword.lower() in text:
                        score += 0.3
                        matched_patterns.append(f"transactional_keyword:{keyword}")
            
            # Check regex patterns
            if 'patterns' in trans_config:
                for pattern in trans_config['patterns']:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 0.5
                        matched_patterns.append(f"transactional_pattern:{pattern}")
            
            intent_scores[EmailIntent.TRANSACTIONAL] = min(1.0, score)
        
        # Check marketing patterns
        if 'marketing' in vendor_config:
            market_config = vendor_config['marketing']
            score = 0.0
            
            # Check sender patterns
            if 'senders' in market_config:
                for sender_pattern in market_config['senders']:
                    if sender_pattern.lower() in sender.lower():
                        score += 0.4
                        matched_patterns.append(f"marketing_sender:{sender_pattern}")
            
            # Check keyword patterns
            if 'keywords' in market_config:
                for keyword in market_config['keywords']:
                    if keyword.lower() in text:
                        score += 0.3
                        matched_patterns.append(f"marketing_keyword:{keyword}")
            
            # Check regex patterns
            if 'patterns' in market_config:
                for pattern in market_config['patterns']:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 0.5
                        matched_patterns.append(f"marketing_pattern:{pattern}")
            
            intent_scores[EmailIntent.MARKETING] = min(1.0, score)
    
    def _check_universal_patterns(self, text: str, intent_scores: Dict, 
                                 matched_patterns: List):
        """Check universal patterns that apply across all vendors"""
        
        # Check transactional indicators
        transactional_score = 0.0
        for pattern in self.universal_patterns['transactional_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                transactional_score += 0.2
                matched_patterns.append(f"universal_transactional:{pattern}")
        
        intent_scores[EmailIntent.TRANSACTIONAL] = max(
            intent_scores[EmailIntent.TRANSACTIONAL],
            min(1.0, transactional_score)
        )
        
        # Check marketing indicators
        marketing_score = 0.0
        for pattern in self.universal_patterns['marketing_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                marketing_score += 0.2
                matched_patterns.append(f"universal_marketing:{pattern}")
        
        intent_scores[EmailIntent.MARKETING] = max(
            intent_scores[EmailIntent.MARKETING],
            min(1.0, marketing_score)
        )
        
        # Check service indicators
        service_score = 0.0
        for pattern in self.universal_patterns['service_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                service_score += 0.3
                matched_patterns.append(f"universal_service:{pattern}")
        
        intent_scores[EmailIntent.SERVICE] = max(
            intent_scores[EmailIntent.SERVICE],
            min(1.0, service_score)
        )
    
    def _get_ml_intent_boost(self, subject: str, content: str, sender: str) -> float:
        """Get ML-based intent classification boost"""
        try:
            # Extract features using existing ML pipeline
            features = self.ml_extractor.extract_features(
                sender_email=sender,
                subject=subject,
                content=content
            )
            
            # Simple heuristic based on feature patterns
            # In production, this would use a trained intent classification model
            boost = 0.0
            
            # Financial indicators boost transactional score
            if features.get('has_financial_keywords', False):
                boost += 0.1
            
            # Promotional indicators boost marketing score
            if features.get('has_promotional_keywords', False):
                boost += 0.1
                
            return boost
            
        except Exception:
            return 0.0
    
    def _should_preserve_email(self, vendor: str, intent: EmailIntent) -> bool:
        """Determine if email should be preserved based on user preferences"""
        
        # Get vendor-specific preferences
        vendor_prefs = self.user_preferences.get(vendor, {})
        
        if not vendor_prefs:
            # Use category defaults
            defaults = self._get_category_defaults(vendor)
            vendor_prefs = defaults
        
        # Map intent to preference key
        intent_mapping = {
            EmailIntent.TRANSACTIONAL: 'transactional',
            EmailIntent.SECURITY: 'security', 
            EmailIntent.SERVICE: 'service',
            EmailIntent.MARKETING: 'marketing',
            EmailIntent.PROMOTIONAL: 'promotional'
        }
        
        pref_key = intent_mapping.get(intent, 'transactional')  # Default to transactional
        return vendor_prefs.get(pref_key, True)  # Conservative default
    
    def _get_category_defaults(self, vendor: str) -> Dict[str, bool]:
        """Get default preferences based on vendor category"""
        
        # Categorize vendor by domain
        financial_domains = ['chase.com', 'capitalone.com', 'bankofamerica.com', 'wellsfargo.com']
        ecommerce_domains = ['amazon.com', 'target.com', 'walmart.com', 'bestbuy.com']
        utilities_domains = ['verizon.com', 'att.com', 'comcast.com', 'spectrum.com']
        streaming_domains = ['netflix.com', 'spotify.com', 'hulu.com', 'disney.com']
        
        defaults = self._get_default_preferences()
        
        if vendor in financial_domains:
            return defaults['financial_default']
        elif vendor in ecommerce_domains:
            return defaults['ecommerce_default'] 
        elif vendor in utilities_domains:
            return defaults['utilities_default']
        elif vendor in streaming_domains:
            return defaults['streaming_default']
        else:
            # Conservative default for unknown vendors
            return {
                'transactional': True,
                'security': True,
                'service': True,
                'marketing': False,
                'promotional': False
            }
    
    def _generate_reasoning(self, intent: EmailIntent, matched_patterns: List[str], 
                           confidence: float) -> str:
        """Generate human-readable reasoning for classification"""
        
        reasoning_parts = [f"Classified as {intent.value}"]
        
        if confidence >= 0.8:
            reasoning_parts.append("(high confidence)")
        elif confidence >= 0.6:
            reasoning_parts.append("(medium confidence)")
        else:
            reasoning_parts.append("(low confidence)")
        
        if matched_patterns:
            pattern_types = {}
            for pattern in matched_patterns[:3]:  # Show top 3 patterns
                pattern_type = pattern.split(':')[0]
                if pattern_type not in pattern_types:
                    pattern_types[pattern_type] = []
                pattern_types[pattern_type].append(pattern.split(':', 1)[1])
            
            pattern_descriptions = []
            for ptype, patterns in pattern_types.items():
                pattern_descriptions.append(f"{ptype}: {', '.join(patterns[:2])}")
            
            reasoning_parts.append(f"based on {'; '.join(pattern_descriptions)}")
        
        return " ".join(reasoning_parts)
    
    def process_vendor_email(self, sender_email: str, sender_domain: str, 
                           subject: str, content: str = "") -> VendorEmailClassification:
        """
        Main entry point for processing vendor emails
        
        Returns classification result indicating whether email should be preserved
        """
        
        # Extract vendor from sender
        vendor = self.extract_vendor_from_email(sender_email, sender_domain)
        
        if not vendor:
            # Not a recognized vendor - return neutral result
            return VendorEmailClassification(
                vendor="unknown",
                intent=EmailIntent.UNKNOWN,
                confidence=0.0,
                reasoning="Vendor not recognized",
                should_preserve=True,  # Conservative - don't filter unknown vendors
                matched_patterns=[]
            )
        
        # Classify email intent
        return self.classify_email_intent(vendor, subject, content, sender_email)
    
    def get_vendor_statistics(self) -> Dict[str, Any]:
        """Get statistics about vendor email processing"""
        try:
            stats = db.execute_query("""
                SELECT 
                    sender_domain,
                    category,
                    action,
                    COUNT(*) as count
                FROM processed_emails_bulletproof 
                WHERE sender_domain IN ({placeholders})
                AND timestamp >= date('now', '-30 days')
                GROUP BY sender_domain, category, action
                ORDER BY count DESC
            """.format(placeholders=','.join(['?' for _ in self.vendor_patterns.keys()])),
            list(self.vendor_patterns.keys()))
            
            return {
                'vendor_patterns_loaded': len(self.vendor_patterns),
                'user_preferences_loaded': len(self.user_preferences),
                'recent_vendor_emails': stats
            }
            
        except Exception as e:
            return {
                'vendor_patterns_loaded': len(self.vendor_patterns),
                'user_preferences_loaded': len(self.user_preferences),
                'error': str(e)
            }

# Global instance for use by other modules
selective_vendor_filter = SelectiveVendorFilter()

def test_selective_vendor_filter():
    """Test the selective vendor filter with sample emails"""
    
    test_cases = [
        # Chase Credit Card Examples
        {
            'sender': 'alerts@chase.com',
            'domain': 'chase.com',
            'subject': 'Your Chase statement is ready',
            'content': 'Your monthly statement for account ending in 1234 is now available.',
            'expected_intent': EmailIntent.TRANSACTIONAL,
            'expected_preserve': True
        },
        {
            'sender': 'offers@chase.com', 
            'domain': 'chase.com',
            'subject': 'You\'re pre-approved for Chase Sapphire',
            'content': 'Earn 60,000 bonus points with this limited time offer.',
            'expected_intent': EmailIntent.MARKETING,
            'expected_preserve': False
        },
        
        # Amazon Examples
        {
            'sender': 'auto-confirm@amazon.com',
            'domain': 'amazon.com', 
            'subject': 'Your order has shipped',
            'content': 'Order #123-456-789 has shipped via UPS. Tracking: 1Z234567890',
            'expected_intent': EmailIntent.TRANSACTIONAL,
            'expected_preserve': True
        },
        {
            'sender': 'store-news@amazon.com',
            'domain': 'amazon.com',
            'subject': 'Recommended for you',
            'content': 'Based on your recent purchases, here are some items you might like.',
            'expected_intent': EmailIntent.MARKETING,
            'expected_preserve': False
        }
    ]
    
    print("🧪 Testing Selective Vendor Filter...")
    
    for i, test_case in enumerate(test_cases, 1):
        result = selective_vendor_filter.process_vendor_email(
            test_case['sender'],
            test_case['domain'],
            test_case['subject'],
            test_case['content']
        )
        
        print(f"\n--- Test {i} ---")
        print(f"Email: {test_case['subject']}")
        print(f"Expected: {test_case['expected_intent'].value}, preserve={test_case['expected_preserve']}")
        print(f"Actual: {result.intent.value}, preserve={result.should_preserve}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        
        # Check if test passed
        intent_match = result.intent == test_case['expected_intent']
        preserve_match = result.should_preserve == test_case['expected_preserve']
        
        if intent_match and preserve_match:
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
            if not intent_match:
                print(f"   Intent mismatch: expected {test_case['expected_intent']}, got {result.intent}")
            if not preserve_match:
                print(f"   Preserve mismatch: expected {test_case['expected_preserve']}, got {result.should_preserve}")

if __name__ == "__main__":
    test_selective_vendor_filter()