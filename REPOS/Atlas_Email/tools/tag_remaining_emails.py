#!/usr/bin/env python3
"""
Tag the remaining 2,000 emails with appropriate subcategories
"""

import sqlite3
import re
from pathlib import Path

DB_FILE = Path(__file__).parent / "data" / "mail_filter.db"

def tag_remaining_emails():
    """Tag emails that are still missing subcategories."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get all emails without subcategories
    cursor.execute("""
        SELECT uid, sender_email, subject, category
        FROM processed_emails_bulletproof
        WHERE subcategory = '' OR subcategory IS NULL
    """)
    
    emails = cursor.fetchall()
    print(f"Found {len(emails)} emails without subcategories")
    
    tagged_count = 0
    subcategory_counts = {}
    
    for uid, sender, subject, category in emails:
        subcategory = None
        confidence = 0.3
        
        # Combine sender and subject for analysis
        text = f"{sender} {subject}".lower()
        
        # Social Media
        if any(word in text for word in ['facebook', 'pinterest', 'instagram', 'twitter', 'linkedin', 'birthday']):
            subcategory = "Social Media"
            confidence = 0.8
            
        # Investment/Trading
        elif any(word in text for word in ['stock', 'crypto', 'bitcoin', 'investment', 'retire', 'fund your retirement', 'trading']):
            subcategory = "Investment & Trading"
            confidence = 0.85
            
        # Health & Wellness
        elif any(word in text for word in ['weight loss', 'diet', 'health', 'medical', 'doctor', 'skin tag', 'belly fat', 'diabetes', 'blood sugar']):
            subcategory = "Health & Wellness"
            confidence = 0.8
            
        # Entertainment/Events
        elif any(word in text for word in ['concert', 'theater', 'comedy', 'show', 'band', 'tribute', 'festival']):
            subcategory = "Entertainment & Events"
            confidence = 0.75
            
        # Food & Dining
        elif any(word in text for word in ['recipe', 'restaurant', 'dining', 'food', 'coffee', 'kitchen', 'chef']):
            subcategory = "Food & Dining"
            confidence = 0.7
            
        # Shopping & Retail
        elif any(word in text for word in ['zappos', 'amazon', 'shop', 'sale', 'discount', 'deal', 'save', 'offer']):
            subcategory = "Shopping & Retail"
            confidence = 0.75
            
        # News & Media
        elif any(word in text for word in ['news', 'breaking', 'footage', 'caught on camera', 'shocked', 'truth']):
            subcategory = "News & Media Clickbait"
            confidence = 0.8
            
        # Political
        elif any(word in text for word in ['trump', 'biden', 'election', 'political', 'democrat', 'republican']):
            subcategory = "Political Content"
            confidence = 0.85
            
        # Travel & Hospitality
        elif any(word in text for word in ['travel', 'hotel', 'flight', 'vacation', 'resort', 'cruise']):
            subcategory = "Travel & Hospitality"
            confidence = 0.7
            
        # Technology
        elif any(word in text for word in ['tesla', 'software', 'app', 'technology', 'tech', 'device']):
            subcategory = "Technology & Gadgets"
            confidence = 0.7
            
        # Real Estate
        elif any(word in text for word in ['mortgage', 'real estate', 'home', 'property', 'fha', 'refinance']):
            subcategory = "Real Estate & Mortgage"
            confidence = 0.8
            
        # Business Opportunities
        elif any(word in text for word in ["who's who", 'business opportunity', 'work from home', 'earn money']):
            subcategory = "Business Opportunities"
            confidence = 0.85
            
        # Adult Content
        elif any(word in text for word in ['penis', 'size', 'adult', 'xxx', '18+', 'enlargement']):
            subcategory = "Adult Content"
            confidence = 0.95
            
        # Timeshare/Vacation
        elif any(word in text for word in ['timeshare', 'vacation ownership', 'resort membership']):
            subcategory = "Timeshare & Vacation"
            confidence = 0.9
            
        # Tinnitus/Medical
        elif any(word in text for word in ['tinnitus', 'ringing', 'hearing', 'neuropathy', 'vitamin']):
            subcategory = "Medical Conditions"
            confidence = 0.85
            
        # Financial/Tax
        elif any(word in text for word in ['tax', 'lien', 'financial', 'lpl', 'proxyvote']):
            subcategory = "Financial Services"
            confidence = 0.75
            
        # Pet/Animal
        elif any(word in text for word in ['adoption', 'pet', 'dog', 'cat', 'animal', 'husky']):
            subcategory = "Pets & Animals"
            confidence = 0.8
            
        # 3D Printing/Specialty
        elif any(word in text for word in ['3d print', 'filament', 'printer']):
            subcategory = "3D Printing & Hobbies"
            confidence = 0.85
            
        # Eyewear
        elif any(word in text for word in ['glasses', 'vision', 'eyewear', 'anti-glare']):
            subcategory = "Eyewear & Vision"
            confidence = 0.8
            
        # Generic if still no match
        elif category == "Commercial Spam" and not subcategory:
            subcategory = "General Marketing"
            confidence = 0.5
        elif category == "Dangerous" and not subcategory:
            subcategory = "Suspicious Content"
            confidence = 0.5
        
        # Update if we found a subcategory
        if subcategory:
            cursor.execute("""
                UPDATE processed_emails_bulletproof
                SET subcategory = ?, subcategory_confidence = ?
                WHERE uid = ?
            """, (subcategory, confidence, uid))
            
            tagged_count += 1
            subcategory_counts[subcategory] = subcategory_counts.get(subcategory, 0) + 1
            
            if tagged_count % 100 == 0:
                print(f"  Tagged {tagged_count} emails...")
    
    # Commit changes
    conn.commit()
    
    # Show results
    print(f"\n✅ Tagged {tagged_count} additional emails")
    print("\n📊 Subcategory breakdown:")
    for subcat, count in sorted(subcategory_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {subcat}: {count}")
    
    # Check remaining
    cursor.execute("""
        SELECT COUNT(*) FROM processed_emails_bulletproof
        WHERE subcategory = '' OR subcategory IS NULL
    """)
    remaining = cursor.fetchone()[0]
    print(f"\n📌 Remaining untagged: {remaining}")
    
    conn.close()

if __name__ == "__main__":
    tag_remaining_emails()