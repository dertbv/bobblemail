#!/usr/bin/env python3
"""
Keyword Usage Analyzer
Analyzes which keywords from filter_terms actually appear in processed emails
to identify high-impact vs. low-impact keywords for optimization.
"""

import sqlite3
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json
import os
import sys

# Add parent directory to path for database imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import DB_FILE

def analyze_keyword_usage():
    """Analyze which keywords actually appear in processed emails."""
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🔍 KEYWORD USAGE ANALYSIS")
    print("=" * 50)
    
    # Get all active keywords by category
    cursor.execute("""
        SELECT category, term, confidence_threshold 
        FROM filter_terms 
        WHERE is_active = 1 
        ORDER BY category, term
    """)
    
    keywords_by_category = defaultdict(list)
    all_keywords = {}
    
    for category, term, confidence in cursor.fetchall():
        keywords_by_category[category].append((term, confidence))
        all_keywords[term.lower()] = category
    
    print(f"📊 Total Keywords: {sum(len(keywords) for keywords in keywords_by_category.values())}")
    print(f"📊 Total Categories: {len(keywords_by_category)}")
    print()
    
    # Get all processed emails with their content
    cursor.execute("""
        SELECT sender_email, subject, category, action, reason
        FROM processed_emails_bulletproof 
        WHERE action = 'DELETED'
        ORDER BY timestamp DESC
    """)
    
    emails = cursor.fetchall()
    print(f"📧 Analyzing {len(emails)} deleted emails")
    print()
    
    # Track keyword usage
    keyword_usage = defaultdict(int)
    category_keyword_hits = defaultdict(lambda: defaultdict(int))
    email_keyword_matches = defaultdict(list)
    
    # Analyze each email for keyword matches
    for sender, subject, category, action, reason in emails:
        email_text = f"{sender} {subject}".lower()
        
        # Check each keyword
        for keyword, keyword_category in all_keywords.items():
            if keyword in email_text:
                keyword_usage[keyword] += 1
                category_keyword_hits[keyword_category][keyword] += 1
                email_keyword_matches[f"{sender}|{subject}"].append(keyword)
    
    # Generate comprehensive analysis
    print("🎯 KEYWORD EFFECTIVENESS ANALYSIS")
    print("=" * 50)
    
    total_keywords = sum(len(keywords) for keywords in keywords_by_category.values())
    used_keywords = len(keyword_usage)
    unused_keywords_count = total_keywords - used_keywords
    
    print(f"✅ Keywords that matched emails: {used_keywords} ({used_keywords/total_keywords*100:.1f}%)")
    print(f"❌ Keywords that never matched: {unused_keywords_count} ({unused_keywords_count/total_keywords*100:.1f}%)")
    print()
    
    # Category-by-category analysis
    print("📋 CATEGORY-BY-CATEGORY ANALYSIS")
    print("=" * 50)
    
    optimization_results = {}
    
    for category in sorted(keywords_by_category.keys()):
        keywords = keywords_by_category[category]
        category_hits = category_keyword_hits[category]
        
        print(f"\n🏷️  {category}")
        print(f"   Total Keywords: {len(keywords)}")
        print(f"   Used Keywords: {len(category_hits)}")
        print(f"   Unused Keywords: {len(keywords) - len(category_hits)}")
        print(f"   Usage Rate: {len(category_hits)/len(keywords)*100:.1f}%")
        
        # Top performing keywords
        if category_hits:
            top_keywords = sorted(category_hits.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"   🔥 Top 10 Used Keywords:")
            for keyword, count in top_keywords:
                print(f"      • {keyword}: {count} emails")
        
        # Store optimization data
        optimization_results[category] = {
            'total_keywords': len(keywords),
            'used_keywords': len(category_hits),
            'usage_rate': len(category_hits)/len(keywords)*100 if keywords else 0,
            'top_keywords': dict(sorted(category_hits.items(), key=lambda x: x[1], reverse=True)[:20]),
            'all_keywords': [kw[0] for kw in keywords],
            'unused_keywords': [kw[0] for kw in keywords if kw[0].lower() not in category_hits]
        }
    
    # Find most effective keywords across all categories
    print("\n🏆 MOST EFFECTIVE KEYWORDS (ALL CATEGORIES)")
    print("=" * 50)
    
    top_overall = sorted(keyword_usage.items(), key=lambda x: x[1], reverse=True)[:20]
    for keyword, count in top_overall:
        category = all_keywords[keyword]
        print(f"   • {keyword} ({category}): {count} emails")
    
    # Find keywords that never matched
    print("\n🗑️  KEYWORDS THAT NEVER MATCHED EMAILS")
    print("=" * 50)
    
    all_keyword_terms = set(all_keywords.keys())
    used_keyword_terms = set(keyword_usage.keys())
    unused_keywords = all_keyword_terms - used_keyword_terms
    
    unused_by_category = defaultdict(list)
    for unused_kw in unused_keywords:
        category = all_keywords[unused_kw]
        unused_by_category[category].append(unused_kw)
    
    total_unused = 0
    for category in sorted(unused_by_category.keys()):
        unused_list = unused_by_category[category]
        total_unused += len(unused_list)
        print(f"\n   {category}: {len(unused_list)} unused keywords")
        if len(unused_list) <= 10:
            for kw in sorted(unused_list):
                print(f"      • {kw}")
        else:
            for kw in sorted(unused_list)[:5]:
                print(f"      • {kw}")
            print(f"      ... and {len(unused_list)-5} more")
    
    print(f"\n📊 TOTAL UNUSED KEYWORDS: {total_unused}")
    
    # Generate optimization recommendations
    print("\n💡 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 50)
    
    for category, data in optimization_results.items():
        total = data['total_keywords']
        used = data['used_keywords']
        usage_rate = data['usage_rate']
        
        if total > 50:  # Categories with too many keywords
            recommended_reduction = total - 30  # Target 30 keywords max
            print(f"\n🎯 {category}:")
            print(f"   Current: {total} keywords")
            print(f"   Used: {used} keywords ({usage_rate:.1f}%)")
            print(f"   📉 RECOMMEND: Reduce by {recommended_reduction} keywords (-{recommended_reduction/total*100:.1f}%)")
            print(f"   🎯 Target: 20-30 high-impact keywords")
            
            if data['top_keywords']:
                print(f"   🔥 Keep these top performers:")
                for kw, count in list(data['top_keywords'].items())[:5]:
                    print(f"      • {kw} ({count} hits)")
    
    # Export optimization data
    with open('keyword_optimization_data.json', 'w') as f:
        json.dump(optimization_results, f, indent=2)
    
    print(f"\n💾 Detailed optimization data saved to: keyword_optimization_data.json")
    
    # Summary statistics
    print("\n📈 SUMMARY STATISTICS")
    print("=" * 50)
    print(f"Total Keywords in Database: {total_keywords}")
    print(f"Keywords Actually Used: {used_keywords} ({used_keywords/total_keywords*100:.1f}%)")
    print(f"Keywords Never Used: {len(unused_keywords)} ({len(unused_keywords)/total_keywords*100:.1f}%)")
    print(f"Potential Reduction: {len(unused_keywords)} keywords")
    print(f"Estimated Storage Savings: {len(unused_keywords)/total_keywords*100:.1f}%")
    
    conn.close()

def find_cross_category_duplicates():
    """Find keywords that appear in multiple categories."""
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("\n🔄 CROSS-CATEGORY DUPLICATE ANALYSIS")
    print("=" * 50)
    
    cursor.execute("""
        SELECT term, GROUP_CONCAT(category) as categories, COUNT(*) as category_count 
        FROM filter_terms 
        WHERE is_active = 1 
        GROUP BY LOWER(term) 
        HAVING COUNT(*) > 1 
        ORDER BY category_count DESC, term
    """)
    
    duplicates = cursor.fetchall()
    
    print(f"📊 Found {len(duplicates)} keywords appearing in multiple categories")
    print()
    
    total_duplicate_instances = 0
    
    for term, categories, count in duplicates:
        total_duplicate_instances += count - 1  # Subtract 1 to keep one instance
        print(f"   • '{term}' appears in {count} categories: {categories}")
    
    print(f"\n📉 Potential reduction from duplicate removal: {total_duplicate_instances} keywords")
    
    conn.close()
    return total_duplicate_instances

if __name__ == "__main__":
    analyze_keyword_usage()
    duplicate_reduction = find_cross_category_duplicates()
    
    print("\n🎯 FINAL OPTIMIZATION SUMMARY")
    print("=" * 50)
    print("1. Remove unused keywords (never match emails)")
    print("2. Remove cross-category duplicates")
    print("3. Focus each category on 20-30 high-impact keywords")
    print("4. Create separate 'Generic Spam' category for universal terms")
    print("5. Expected total reduction: 60-70% of current keywords")