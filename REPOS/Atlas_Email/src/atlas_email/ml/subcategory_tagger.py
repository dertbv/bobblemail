"""
Subcategory Tagger for Email Classification
==========================================

This module provides detailed subcategory tagging for emails within the 4 main categories.
It uses pattern matching, keyword analysis, and ML techniques to identify specific
subcategories and track their effectiveness.
"""

import re
import json
import sqlite3
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np
from pathlib import Path


class SubcategoryTagger:
    """
    Advanced subcategory detection and tracking system.
    """
    
    def __init__(self, db_path: str = None):
        """Initialize the subcategory tagger."""
        if db_path is None:
            from atlas_email.models.database import DB_FILE
            db_path = DB_FILE
            
        self.db_path = db_path
        self.patterns = self._load_patterns()
        self.effectiveness_cache = {}
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure subcategory tracking tables exist."""
        conn = sqlite3.connect(self.db_path)
        
        # Create subcategory patterns table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subcategory_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                effectiveness REAL DEFAULT 0.5,
                occurrence_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, subcategory, pattern_type, pattern_value)
            )
        """)
        
        # Create subcategory tracking table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subcategory_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_uid TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                confidence REAL NOT NULL,
                matched_patterns TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_patterns(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Load comprehensive subcategory detection patterns."""
        patterns = {
            "Dangerous": {
                "Phishing attempts": [
                    {'type': 'subject', 'pattern': r'\b(verify|confirm|validate)\s+(your\s+)?(account|identity|password)', 'weight': 0.9},
                    {'type': 'subject', 'pattern': r'\bsuspicious\s+activity\b', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\baccount\s+(will\s+be\s+)?(suspended|locked|closed)', 'weight': 0.9},
                    {'type': 'sender', 'pattern': r'(security|support|admin)@.*(verify|confirm|validate)', 'weight': 0.8},
                    {'type': 'domain_spoof', 'pattern': r'(amaz0n|g00gle|micr0soft|app1e)', 'weight': 0.95},
                ],
                "Malware/virus distribution": [
                    {'type': 'subject', 'pattern': r'\b(download|install|update)\s+(now|immediately|urgent)', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\battachment\s+contains', 'weight': 0.7},
                    {'type': 'subject', 'pattern': r'\b(invoice|receipt|document)\s+attached', 'weight': 0.75},
                    {'type': 'attachment', 'pattern': r'\.(exe|bat|com|pif|scr|vbs|jar)$', 'weight': 0.95},
                ],
                "Account compromise attempts": [
                    {'type': 'subject', 'pattern': r'\bunauthorized\s+(access|login|attempt)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\bsecurity\s+code:\s*\d+', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\btwo.?factor|2fa\s+code', 'weight': 0.75},
                    {'type': 'body', 'pattern': r'click\s+here\s+to\s+secure', 'weight': 0.8},
                ],
                "Fake security alerts": [
                    {'type': 'subject', 'pattern': r'\b(virus|malware|threat)\s+detected', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\byour\s+computer\s+is\s+infected', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\bsecurity\s+alert\s*:', 'weight': 0.7},
                    {'type': 'sender', 'pattern': r'(windows|microsoft|apple)\s*security', 'weight': 0.8},
                ],
                "Cryptocurrency scams": [
                    {'type': 'subject', 'pattern': r'\b(bitcoin|crypto|ethereum|btc)\s+(investment|opportunity|profit)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\bcrypto\s+wallet\s+(compromised|hacked)', 'weight': 0.9},
                    {'type': 'subject', 'pattern': r'\b(double|triple)\s+your\s+(bitcoin|crypto)', 'weight': 0.95},
                    {'type': 'body', 'pattern': r'send\s+\d+\s*(btc|eth|bitcoin)', 'weight': 0.9},
                ],
            },
            
            "Commercial Spam": {
                "Auto warranty & insurance": [
                    {'type': 'subject', 'pattern': r'\b(auto|car|vehicle)\s+(warranty|protection|insurance)', 'weight': 0.9},
                    {'type': 'subject', 'pattern': r'\bendurance\s+auto', 'weight': 0.95},
                    {'type': 'subject', 'pattern': r'\bwarranty\s+(expir|coverage|discount)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\bfinal\s+notice.*warranty', 'weight': 0.9},
                    {'type': 'sender', 'pattern': r'warranty|autoprotect|carshield', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\$\d+\s+off.*auto\s+(repair|warranty)', 'weight': 0.85},
                ],
                "Health & medical products": [
                    {'type': 'subject', 'pattern': r'\b(weight\s+loss|diet\s+pills?|fat\s+burn)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\b(viagra|cialis|levitra|pharmacy)', 'weight': 0.95},
                    {'type': 'subject', 'pattern': r'\bFDA\s+approved', 'weight': 0.7},
                    {'type': 'subject', 'pattern': r'\b(miracle|revolutionary)\s+(cure|treatment|remedy)', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\blose\s+\d+\s+(pounds|lbs|kg)', 'weight': 0.75},
                ],
                "Adult & dating services": [
                    {'type': 'subject', 'pattern': r'\b(hot|sexy|naughty)\s+(singles?|girls?|women)', 'weight': 0.9},
                    {'type': 'subject', 'pattern': r'\b(dating|hookup|meet)\s+tonight', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\bin\s+your\s+area\b', 'weight': 0.7},
                    {'type': 'subject', 'pattern': r'\b(xxx|adult|porn)', 'weight': 0.95},
                    {'type': 'sender', 'pattern': r'(dating|singles|hookup|adult)', 'weight': 0.8},
                ],
                "Gambling promotions": [
                    {'type': 'subject', 'pattern': r'\b(casino|poker|slots|betting)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\b(win|won)\s+\$\d+', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\bfree\s+(spins?|chips?|credits?)', 'weight': 0.75},
                    {'type': 'subject', 'pattern': r'\b(jackpot|lottery|prize\s+pool)', 'weight': 0.8},
                    {'type': 'sender', 'pattern': r'(casino|gaming|lottery|betting)', 'weight': 0.85},
                ],
                "General product marketing": [
                    {'type': 'subject', 'pattern': r'\b(sale|discount|offer)\s+ends?\s+(today|soon|now)', 'weight': 0.7},
                    {'type': 'subject', 'pattern': r'\b\d+%\s+off', 'weight': 0.65},
                    {'type': 'subject', 'pattern': r'\b(limited\s+time|exclusive)\s+offer', 'weight': 0.7},
                    {'type': 'subject', 'pattern': r'\b(buy\s+now|shop\s+now|order\s+today)', 'weight': 0.75},
                ],
            },
            
            "Scams": {
                "Advance fee fraud": [
                    {'type': 'subject', 'pattern': r'\b(nigerian?\s+prince|royal\s+family|inheritance)', 'weight': 0.95},
                    {'type': 'subject', 'pattern': r'\bmillion(s)?\s+(dollar|usd|euro|pounds)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\b(beneficiary|next\s+of\s+kin|unclaimed\s+funds)', 'weight': 0.9},
                    {'type': 'body', 'pattern': r'transfer\s+fee|processing\s+fee|administrative\s+cost', 'weight': 0.85},
                ],
                "Lottery & prize scams": [
                    {'type': 'subject', 'pattern': r'\b(congratulations|winner|won)\s+.*(lottery|prize|sweepstake)', 'weight': 0.9},
                    {'type': 'subject', 'pattern': r'\bclaim\s+your\s+(prize|winnings|money)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\b(microsoft|google|facebook)\s+lottery', 'weight': 0.95},
                    {'type': 'subject', 'pattern': r'\blucky\s+(winner|draw|selection)', 'weight': 0.8},
                ],
                "Work-from-home schemes": [
                    {'type': 'subject', 'pattern': r'\b(work\s+from\s+home|home\s+based)\s+(job|opportunity)', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\bearn\s+\$\d+\s+(daily|weekly|per\s+hour)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\b(no\s+experience|start\s+immediately)', 'weight': 0.75},
                    {'type': 'subject', 'pattern': r'\b(data\s+entry|typing|survey)\s+job', 'weight': 0.7},
                ],
                "Investment fraud": [
                    {'type': 'subject', 'pattern': r'\b(guaranteed|risk.?free)\s+(returns?|profits?|income)', 'weight': 0.9},
                    {'type': 'subject', 'pattern': r'\b(penny\s+stocks?|forex|trading)\s+secrets?', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\bmake\s+\$\d+k?\s+in\s+\d+\s+(days?|weeks?)', 'weight': 0.85},
                    {'type': 'body', 'pattern': r'(insider\s+information|hot\s+tip|secret\s+strategy)', 'weight': 0.8},
                ],
                "Romance scams": [
                    {'type': 'subject', 'pattern': r'\b(lonely|looking\s+for\s+love|soul\s?mate)', 'weight': 0.75},
                    {'type': 'body', 'pattern': r'(send\s+money|wire\s+transfer|western\s+union)', 'weight': 0.9},
                    {'type': 'body', 'pattern': r'(stranded|emergency|urgent\s+help)', 'weight': 0.85},
                    {'type': 'sender', 'pattern': r'(love|romance|dating).*\d{4,}', 'weight': 0.7},
                ],
            },
            
            "Legitimate Marketing": {
                "Newsletter subscriptions": [
                    {'type': 'subject', 'pattern': r'\b(newsletter|weekly\s+digest|monthly\s+update)', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\bissue\s+#\d+', 'weight': 0.75},
                    {'type': 'body', 'pattern': r'unsubscribe|update\s+preferences|manage\s+subscription', 'weight': 0.85},
                    {'type': 'sender', 'pattern': r'newsletter@|updates@|digest@', 'weight': 0.7},
                ],
                "Promotional emails": [
                    {'type': 'subject', 'pattern': r'\b(sale|promotion|special\s+offer)\s+at\s+\w+', 'weight': 0.7},
                    {'type': 'domain_legitimate', 'pattern': r'(amazon|ebay|walmart|target|bestbuy)\.com$', 'weight': 0.9},
                    {'type': 'body', 'pattern': r'view\s+in\s+browser|add\s+to\s+cart', 'weight': 0.65},
                ],
                "Event invitations": [
                    {'type': 'subject', 'pattern': r'\b(webinar|conference|seminar|workshop)', 'weight': 0.75},
                    {'type': 'subject', 'pattern': r'\b(rsvp|register\s+now|save\s+the\s+date)', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\b(invited?|invitation)\s+to', 'weight': 0.7},
                ],
                "Product updates": [
                    {'type': 'subject', 'pattern': r'\b(new\s+features?|product\s+updates?|release\s+notes)', 'weight': 0.75},
                    {'type': 'subject', 'pattern': r'\bversion\s+\d+\.\d+', 'weight': 0.7},
                    {'type': 'subject', 'pattern': r'\b(changelog|what\'s\s+new)', 'weight': 0.75},
                ],
                "Sales notifications": [
                    {'type': 'subject', 'pattern': r'\b(order\s+confirmation|shipping\s+update|delivery)', 'weight': 0.85},
                    {'type': 'subject', 'pattern': r'\border\s+#\d+', 'weight': 0.8},
                    {'type': 'subject', 'pattern': r'\b(receipt|invoice|payment\s+received)', 'weight': 0.8},
                ],
            }
        }
        
        return patterns
    
    def tag_email(self, category: str, subject: str, sender: str = "", 
                  body: str = "", domain: str = "") -> Dict[str, Any]:
        """
        Tag an email with its most likely subcategory.
        
        Args:
            category: Main category (from 4-category classifier)
            subject: Email subject
            sender: Sender email address
            body: Email body (optional)
            domain: Sender domain (optional)
            
        Returns:
            Tagging result with subcategory and confidence
        """
        if category not in self.patterns:
            return {
                'subcategory': 'Unknown',
                'confidence': 0.0,
                'matched_patterns': []
            }
        
        # Extract domain if not provided
        if not domain and sender and '@' in sender:
            domain = sender.split('@')[1].lower()
        
        # Score each subcategory
        subcategory_scores = defaultdict(float)
        matched_patterns = defaultdict(list)
        
        for subcategory, patterns in self.patterns[category].items():
            for pattern_info in patterns:
                pattern_type = pattern_info['type']
                pattern = pattern_info['pattern']
                weight = pattern_info['weight']
                
                text_to_check = ""
                if pattern_type == 'subject':
                    text_to_check = subject.lower()
                elif pattern_type == 'sender':
                    text_to_check = sender.lower()
                elif pattern_type == 'body' and body:
                    text_to_check = body.lower()
                elif pattern_type == 'domain' and domain:
                    text_to_check = domain
                elif pattern_type == 'domain_spoof' and domain:
                    text_to_check = domain
                elif pattern_type == 'domain_legitimate' and domain:
                    text_to_check = domain
                
                if text_to_check and re.search(pattern, text_to_check, re.IGNORECASE):
                    subcategory_scores[subcategory] += weight
                    matched_patterns[subcategory].append({
                        'type': pattern_type,
                        'pattern': pattern,
                        'weight': weight
                    })
        
        # Find best subcategory
        if not subcategory_scores:
            return {
                'subcategory': f"General {category}",
                'confidence': 0.3,
                'matched_patterns': []
            }
        
        best_subcategory = max(subcategory_scores.items(), key=lambda x: x[1])
        subcategory_name = best_subcategory[0]
        raw_score = best_subcategory[1]
        
        # Normalize confidence (max score around 3-4 weights)
        confidence = min(raw_score / 3.0, 1.0)
        
        # Track the tagging
        self._track_tagging(category, subcategory_name, confidence, matched_patterns[subcategory_name])
        
        return {
            'subcategory': subcategory_name,
            'confidence': confidence,
            'matched_patterns': matched_patterns[subcategory_name],
            'raw_score': raw_score,
            'all_scores': dict(subcategory_scores)
        }
    
    def _track_tagging(self, category: str, subcategory: str, confidence: float, 
                      matched_patterns: List[Dict]):
        """Track subcategory tagging for effectiveness analysis."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Update pattern effectiveness
            for pattern in matched_patterns:
                conn.execute("""
                    INSERT INTO subcategory_patterns 
                    (category, subcategory, pattern_type, pattern_value, occurrence_count)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(category, subcategory, pattern_type, pattern_value)
                    DO UPDATE SET 
                        occurrence_count = occurrence_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """, (category, subcategory, pattern['type'], pattern['pattern']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Failed to track tagging: {e}")
    
    def get_subcategory_stats(self, category: str = None) -> Dict[str, Any]:
        """Get statistics about subcategory usage and effectiveness."""
        conn = sqlite3.connect(self.db_path)
        
        if category:
            query = """
                SELECT subcategory, SUM(occurrence_count) as total,
                       AVG(effectiveness) as avg_effectiveness
                FROM subcategory_patterns
                WHERE category = ?
                GROUP BY subcategory
                ORDER BY total DESC
            """
            cursor = conn.execute(query, (category,))
        else:
            query = """
                SELECT category, subcategory, SUM(occurrence_count) as total,
                       AVG(effectiveness) as avg_effectiveness
                FROM subcategory_patterns
                GROUP BY category, subcategory
                ORDER BY category, total DESC
            """
            cursor = conn.execute(query)
        
        results = []
        for row in cursor.fetchall():
            if category:
                results.append({
                    'subcategory': row[0],
                    'total_matches': row[1],
                    'effectiveness': row[2]
                })
            else:
                results.append({
                    'category': row[0],
                    'subcategory': row[1],
                    'total_matches': row[2],
                    'effectiveness': row[3]
                })
        
        conn.close()
        return {'stats': results}
    
    def update_pattern_effectiveness(self, category: str, subcategory: str, 
                                   pattern_value: str, effectiveness: float):
        """Update the effectiveness score of a pattern based on user feedback."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            UPDATE subcategory_patterns
            SET effectiveness = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE category = ? AND subcategory = ? AND pattern_value = ?
        """, (effectiveness, category, subcategory, pattern_value))
        
        conn.commit()
        conn.close()
    
    def export_patterns(self, output_file: str = None) -> str:
        """Export all patterns with their effectiveness scores."""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute("""
            SELECT category, subcategory, pattern_type, pattern_value,
                   effectiveness, occurrence_count
            FROM subcategory_patterns
            ORDER BY category, subcategory, effectiveness DESC
        """)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'patterns': defaultdict(lambda: defaultdict(list))
        }
        
        for row in cursor.fetchall():
            cat, subcat, ptype, pval, eff, count = row
            export_data['patterns'][cat][subcat].append({
                'type': ptype,
                'pattern': pval,
                'effectiveness': eff,
                'occurrences': count
            })
        
        conn.close()
        
        if output_file is None:
            output_file = f"subcategory_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_file


# Testing
if __name__ == "__main__":
    tagger = SubcategoryTagger()
    
    # Test cases
    test_emails = [
        {
            'category': 'Commercial Spam',
            'subject': "Final notice: Your auto warranty is about to expire!",
            'sender': "noreply@warranty-center.com"
        },
        {
            'category': 'Commercial Spam',
            'subject': "Hot singles in your area want to meet!",
            'sender': "matches@dating-site.net"
        },
        {
            'category': 'Dangerous',
            'subject': "Urgent: Verify your Amazon account",
            'sender': "security@amaz0n-verify.com"
        },
        {
            'category': 'Scams',
            'subject': "Congratulations! You've won the Microsoft Lottery!",
            'sender': "winner@lottery-notification.com"
        },
        {
            'category': 'Legitimate Marketing',
            'subject': "Your Amazon order #123-4567890 has shipped",
            'sender': "shipment-tracking@amazon.com"
        }
    ]
    
    print("🏷️  Testing Subcategory Tagger")
    print("=" * 80)
    
    for email in test_emails:
        print(f"\n📧 Testing email:")
        print(f"   Category: {email['category']}")
        print(f"   Subject: {email['subject']}")
        print(f"   Sender: {email['sender']}")
        
        result = tagger.tag_email(
            category=email['category'],
            subject=email['subject'],
            sender=email['sender']
        )
        
        print(f"   📌 Subcategory: {result['subcategory']} (confidence: {result['confidence']:.2f})")
        print(f"   🎯 Matched patterns: {len(result['matched_patterns'])}")
        
        if result['matched_patterns']:
            print("   📋 Pattern details:")
            for p in result['matched_patterns'][:2]:  # Show first 2
                print(f"      - Type: {p['type']}, Weight: {p['weight']}")
    
    # Get statistics
    print("\n📊 Subcategory Statistics:")
    stats = tagger.get_subcategory_stats()
    for stat in stats['stats'][:10]:  # Top 10
        print(f"   {stat['category']} / {stat['subcategory']}: {stat['total_matches']} matches")
    
    print("\n✅ Subcategory Tagger initialized successfully!")