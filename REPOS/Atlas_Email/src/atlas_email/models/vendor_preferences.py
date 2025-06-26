#!/usr/bin/env python3
"""
Vendor Preferences Database Schema

Creates database tables for storing user preferences for selective vendor filtering.
"""

import json
from atlas_email.models.database import db

def create_vendor_preferences_tables():
    """Create database tables for vendor preferences"""
    
    print("🗄️ Creating vendor preferences database schema...")
    
    # User vendor preferences table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS user_vendor_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            vendor_domain TEXT NOT NULL,
            email_type TEXT NOT NULL CHECK (email_type IN 
                ('transactional', 'marketing', 'service', 'security', 'promotional')),
            allow_emails BOOLEAN NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            UNIQUE(user_id, vendor_domain, email_type)
        )
    """)
    
    # Vendor email patterns table (for dynamic pattern management)
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS vendor_email_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_domain TEXT NOT NULL,
            pattern_type TEXT NOT NULL CHECK (pattern_type IN 
                ('transactional', 'marketing', 'service', 'security', 'promotional')),
            pattern_category TEXT NOT NULL CHECK (pattern_category IN 
                ('sender', 'keyword', 'regex', 'subject')),
            pattern_value TEXT NOT NULL,
            confidence_weight REAL NOT NULL DEFAULT 0.3,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL DEFAULT 'system',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    
    # Vendor classification history (for learning and optimization)
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS vendor_classification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_domain TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            classified_intent TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            user_feedback TEXT,  -- 'correct', 'wrong_intent', 'wrong_action'
            should_preserve BOOLEAN NOT NULL,
            actual_action TEXT,  -- 'PRESERVED', 'DELETED'
            matched_patterns TEXT,  -- JSON array of matched patterns
            reasoning TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    
    # Create indexes for performance
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_user_vendor_preferences_lookup 
        ON user_vendor_preferences(user_id, vendor_domain, email_type)
    """)
    
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_vendor_patterns_lookup 
        ON vendor_email_patterns(vendor_domain, pattern_type, is_active)
    """)
    
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_classification_history_vendor 
        ON vendor_classification_history(vendor_domain, timestamp)
    """)
    
    print("✅ Vendor preferences database schema created")

def insert_default_preferences():
    """Insert smart default preferences for major vendors"""
    
    print("📋 Inserting default vendor preferences...")
    
    # Default preferences for major vendor categories
    default_preferences = [
        # Financial Services - Conservative approach
        ('chase.com', 'transactional', True),
        ('chase.com', 'security', True),
        ('chase.com', 'service', True),
        ('chase.com', 'marketing', False),
        ('chase.com', 'promotional', False),
        
        ('capitalone.com', 'transactional', True),
        ('capitalone.com', 'security', True),
        ('capitalone.com', 'service', True),
        ('capitalone.com', 'marketing', False),
        ('capitalone.com', 'promotional', False),
        
        ('bankofamerica.com', 'transactional', True),
        ('bankofamerica.com', 'security', True),
        ('bankofamerica.com', 'service', True),
        ('bankofamerica.com', 'marketing', False),
        ('bankofamerica.com', 'promotional', False),
        
        # E-commerce - Allow orders, block marketing
        ('amazon.com', 'transactional', True),
        ('amazon.com', 'security', True),
        ('amazon.com', 'service', True),
        ('amazon.com', 'marketing', False),
        ('amazon.com', 'promotional', False),
        
        ('target.com', 'transactional', True),
        ('target.com', 'security', True),
        ('target.com', 'service', True),
        ('target.com', 'marketing', False),
        ('target.com', 'promotional', False),
        
        ('walmart.com', 'transactional', True),
        ('walmart.com', 'security', True),
        ('walmart.com', 'service', True),
        ('walmart.com', 'marketing', False),
        ('walmart.com', 'promotional', False),
        
        ('bestbuy.com', 'transactional', True),
        ('bestbuy.com', 'security', True),
        ('bestbuy.com', 'service', True),
        ('bestbuy.com', 'marketing', False),
        ('bestbuy.com', 'promotional', False),
        
        # Utilities - Allow service info, block upgrades
        ('verizon.com', 'transactional', True),
        ('verizon.com', 'security', True),
        ('verizon.com', 'service', True),
        ('verizon.com', 'marketing', False),
        ('verizon.com', 'promotional', False),
        
        ('att.com', 'transactional', True),
        ('att.com', 'security', True),
        ('att.com', 'service', True),
        ('att.com', 'marketing', False),
        ('att.com', 'promotional', False),
        
        ('comcast.com', 'transactional', True),
        ('comcast.com', 'security', True),
        ('comcast.com', 'service', True),
        ('comcast.com', 'marketing', False),
        ('comcast.com', 'promotional', False),
        
        # Streaming - Many users want content recommendations
        ('netflix.com', 'transactional', True),
        ('netflix.com', 'security', True),
        ('netflix.com', 'service', True),
        ('netflix.com', 'marketing', True),   # Content recommendations
        ('netflix.com', 'promotional', False),
        
        ('spotify.com', 'transactional', True),
        ('spotify.com', 'security', True),
        ('spotify.com', 'service', True),
        ('spotify.com', 'marketing', True),   # Music recommendations
        ('spotify.com', 'promotional', False),
        
        # Airlines - Allow important travel info, block deals
        ('delta.com', 'transactional', True),
        ('delta.com', 'security', True),
        ('delta.com', 'service', True),
        ('delta.com', 'marketing', False),
        ('delta.com', 'promotional', False),
        
        ('united.com', 'transactional', True),
        ('united.com', 'security', True),
        ('united.com', 'service', True),
        ('united.com', 'marketing', False),
        ('united.com', 'promotional', False),
        
        # Insurance - Allow policy info, block sales
        ('geico.com', 'transactional', True),
        ('geico.com', 'security', True),
        ('geico.com', 'service', True),
        ('geico.com', 'marketing', False),
        ('geico.com', 'promotional', False),
        
        ('statefarm.com', 'transactional', True),
        ('statefarm.com', 'security', True),
        ('statefarm.com', 'service', True),
        ('statefarm.com', 'marketing', False),
        ('statefarm.com', 'promotional', False),
    ]
    
    # Insert preferences (ignore duplicates)
    for vendor, email_type, allow in default_preferences:
        try:
            db.execute_query("""
                INSERT OR IGNORE INTO user_vendor_preferences 
                (user_id, vendor_domain, email_type, allow_emails)
                VALUES ('default', ?, ?, ?)
            """, (vendor, email_type, allow))
        except Exception as e:
            print(f"Warning: Could not insert preference for {vendor}.{email_type}: {e}")
    
    print(f"✅ Inserted {len(default_preferences)} default vendor preferences")

def get_user_vendor_preferences(user_id='default'):
    """Get all vendor preferences for a user"""
    
    preferences = db.execute_query("""
        SELECT vendor_domain, email_type, allow_emails
        FROM user_vendor_preferences 
        WHERE user_id = ?
        ORDER BY vendor_domain, email_type
    """, (user_id,))
    
    # Group by vendor
    result = {}
    for pref in preferences:
        vendor = pref['vendor_domain']
        if vendor not in result:
            result[vendor] = {}
        result[vendor][pref['email_type']] = bool(pref['allow_emails'])
    
    return result

def update_vendor_preference(vendor_domain, email_type, allow_emails, user_id='default'):
    """Update a specific vendor preference"""
    
    db.execute_query("""
        INSERT OR REPLACE INTO user_vendor_preferences 
        (user_id, vendor_domain, email_type, allow_emails, updated_at)
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
    """, (user_id, vendor_domain, email_type, allow_emails))
    
    print(f"✅ Updated preference: {vendor_domain}.{email_type} = {allow_emails}")

def log_vendor_classification(vendor_domain, sender_email, subject, 
                             classified_intent, confidence_score, should_preserve,
                             actual_action, matched_patterns, reasoning):
    """Log vendor email classification for analysis and learning"""
    
    patterns_json = json.dumps(matched_patterns) if matched_patterns else None
    
    db.execute_query("""
        INSERT INTO vendor_classification_history 
        (vendor_domain, sender_email, subject, classified_intent, confidence_score,
         should_preserve, actual_action, matched_patterns, reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (vendor_domain, sender_email, subject, classified_intent, confidence_score,
          should_preserve, actual_action, patterns_json, reasoning))

def get_vendor_statistics(days=30):
    """Get vendor classification statistics"""
    
    stats = db.execute_query("""
        SELECT 
            vendor_domain,
            classified_intent,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence,
            SUM(CASE WHEN should_preserve = 1 THEN 1 ELSE 0 END) as preserved,
            SUM(CASE WHEN should_preserve = 0 THEN 1 ELSE 0 END) as filtered
        FROM vendor_classification_history
        WHERE timestamp >= date('now', '-{days} days')
        GROUP BY vendor_domain, classified_intent
        ORDER BY vendor_domain, count DESC
    """)
    
    return stats

if __name__ == "__main__":
    print("🚀 Setting up vendor preferences database...")
    
    create_vendor_preferences_tables()
    insert_default_preferences()
    
    # Test the system
    print("\n📊 Testing vendor preferences...")
    preferences = get_user_vendor_preferences()
    print(f"Loaded preferences for {len(preferences)} vendors")
    
    # Show a few examples
    for vendor in list(preferences.keys())[:3]:
        print(f"  {vendor}: {preferences[vendor]}")
    
    print("\n✅ Vendor preferences system ready!")