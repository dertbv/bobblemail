#!/usr/bin/env python3
"""
Database Keyword Inspector
Comprehensive tool to inspect and manage keywords stored in the database
that may be causing "User Keyword" classifications
"""

import sqlite3
from database import db
from collections import defaultdict

class DatabaseKeywordInspector:
    """Tool to inspect and manage database keywords"""
    
    def __init__(self):
        self.db = db
    
    def show_keyword_summary(self):
        """Show summary of all keywords in database"""
        print("="*60)
        print("📊 DATABASE KEYWORD SUMMARY")
        print("="*60)
        
        # Get total counts by created_by
        summary = self.db.execute_query("""
            SELECT created_by, COUNT(*) as count, 
                   COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_count
            FROM filter_terms 
            GROUP BY created_by 
            ORDER BY count DESC
        """)
        
        total_keywords = 0
        total_active = 0
        
        print(f"{'Source':<20} {'Total':<8} {'Active':<8} {'Inactive':<8}")
        print("-"*50)
        for row in summary:
            inactive = row['count'] - row['active_count']
            print(f"{row['created_by']:<20} {row['count']:<8} {row['active_count']:<8} {inactive:<8}")
            total_keywords += row['count']
            total_active += row['active_count']
        
        print("-"*50)
        print(f"{'TOTAL':<20} {total_keywords:<8} {total_active:<8} {total_keywords-total_active:<8}")
        print()
    
    def show_user_keywords(self):
        """Show all user-created keywords"""
        print("="*60)
        print("👤 USER KEYWORDS (created_by = 'user')")
        print("="*60)
        
        user_keywords = self.db.execute_query("""
            SELECT term, category, confidence_threshold, is_active, created_at 
            FROM filter_terms 
            WHERE created_by = 'user' 
            ORDER BY category, term
        """)
        
        if not user_keywords:
            print("✅ No user keywords found in database")
            return
        
        print(f"Found {len(user_keywords)} user keywords:")
        print()
        
        by_category = defaultdict(list)
        for kw in user_keywords:
            by_category[kw['category'] or 'No Category'].append(kw)
        
        for category, keywords in by_category.items():
            print(f"📂 {category} ({len(keywords)} keywords)")
            print("-" * 40)
            for kw in keywords:
                status = "✅ Active" if kw['is_active'] else "❌ Inactive"
                confidence = kw['confidence_threshold'] or 'Default'
                print(f"  • {kw['term']} | {confidence} | {status}")
            print()
    
    def show_auto_detected_keywords(self):
        """Show auto-detected keywords that might be causing issues"""
        print("="*60)
        print("🤖 AUTO-DETECTED KEYWORDS")
        print("="*60)
        
        auto_keywords = self.db.execute_query("""
            SELECT term, category, confidence_threshold, is_active, created_at 
            FROM filter_terms 
            WHERE category = 'auto_detected' AND is_active = 1
            ORDER BY term
        """)
        
        if not auto_keywords:
            print("✅ No auto-detected keywords found")
            return
        
        print(f"Found {len(auto_keywords)} auto-detected keywords:")
        print("(These are likely causing 'User Keyword' classifications)")
        print()
        
        for kw in auto_keywords:
            confidence = kw['confidence_threshold'] or 'Default'
            print(f"  • '{kw['term']}' | Confidence: {confidence}")
        print()
    
    def show_keywords_without_category(self):
        """Show keywords without specific categories"""
        print("="*60)
        print("❓ KEYWORDS WITHOUT CATEGORIES")
        print("="*60)
        
        no_category = self.db.execute_query("""
            SELECT term, created_by, confidence_threshold, is_active, created_at 
            FROM filter_terms 
            WHERE (category IS NULL OR category = '' OR category = 'auto_detected') 
              AND is_active = 1
            ORDER BY created_by, term
        """)
        
        if not no_category:
            print("✅ All keywords have proper categories")
            return
        
        print(f"Found {len(no_category)} keywords without proper categories:")
        print("(These may be contributing to 'User Keyword' classifications)")
        print()
        
        by_source = defaultdict(list)
        for kw in no_category:
            by_source[kw['created_by']].append(kw)
        
        for source, keywords in by_source.items():
            print(f"📂 {source} ({len(keywords)} keywords)")
            print("-" * 30)
            for kw in keywords:
                confidence = kw['confidence_threshold'] or 'Default'
                print(f"  • '{kw['term']}' | {confidence}")
            print()
    
    def search_keyword(self, search_term):
        """Search for a specific keyword in the database"""
        print("="*60)
        print(f"🔍 SEARCHING FOR: '{search_term}'")
        print("="*60)
        
        results = self.db.execute_query("""
            SELECT term, category, created_by, confidence_threshold, is_active, created_at 
            FROM filter_terms 
            WHERE term LIKE ? 
            ORDER BY term, created_by
        """, (f"%{search_term}%",))
        
        if not results:
            print(f"❌ No keywords found containing '{search_term}'")
            return
        
        print(f"Found {len(results)} matching keywords:")
        print()
        
        for result in results:
            status = "✅ Active" if result['is_active'] else "❌ Inactive"
            category = result['category'] or 'No Category'
            confidence = result['confidence_threshold'] or 'Default'
            print(f"  • '{result['term']}' | {category} | {result['created_by']} | {confidence} | {status}")
        print()
    
    def remove_auto_detected_keywords(self):
        """Remove auto-detected keywords that are too generic"""
        print("="*60)
        print("🧹 REMOVING AUTO-DETECTED KEYWORDS")
        print("="*60)
        
        # First, show what will be removed
        auto_keywords = self.db.execute_query("""
            SELECT COUNT(*) as count FROM filter_terms 
            WHERE category = 'auto_detected' AND is_active = 1
        """)[0]['count']
        
        if auto_keywords == 0:
            print("✅ No auto-detected keywords to remove")
            return
        
        print(f"Found {auto_keywords} auto-detected keywords to remove")
        
        # Show some examples
        examples = self.db.execute_query("""
            SELECT term FROM filter_terms 
            WHERE category = 'auto_detected' AND is_active = 1
            ORDER BY term LIMIT 10
        """)
        
        print("\nExamples of keywords to be removed:")
        for example in examples:
            print(f"  • '{example['term']}'")
        
        if auto_keywords > 10:
            print(f"  ... and {auto_keywords - 10} more")
        
        # Confirm before removal
        confirm = input(f"\nRemove all {auto_keywords} auto-detected keywords? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            # Deactivate instead of delete for safety
            affected = self.db.execute_update("""
                UPDATE filter_terms 
                SET is_active = 0 
                WHERE category = 'auto_detected' AND is_active = 1
            """)
            
            print(f"✅ Deactivated {affected} auto-detected keywords")
            print("These keywords will no longer trigger 'User Keyword' classifications")
        else:
            print("❌ Operation cancelled")
    
    def clean_generic_user_keywords(self):
        """Remove overly generic user keywords"""
        print("="*60)
        print("🧹 CLEANING GENERIC USER KEYWORDS")
        print("="*60)
        
        # Define generic terms that shouldn't be user keywords
        generic_terms = [
            'free', 'this', 'every', 'home', 'with', 'have', 'save', 'today',
            'that', 'these', 'your', 'from', 'will', 'more', 'time', 'new',
            'best', 'now', 'get', 'all', 'can', 'our', 'you', 'for', 'the',
            'and', 'are', 'not', 'but', 'has', 'was', 'his', 'her', 'its'
        ]
        
        # Find generic user keywords
        placeholders = ','.join(['?'] * len(generic_terms))
        generic_user_keywords = self.db.execute_query(f"""
            SELECT term, category, created_by FROM filter_terms 
            WHERE created_by = 'user' AND term IN ({placeholders}) AND is_active = 1
        """, generic_terms)
        
        if not generic_user_keywords:
            print("✅ No generic user keywords found")
            return
        
        print(f"Found {len(generic_user_keywords)} generic user keywords:")
        for kw in generic_user_keywords:
            print(f"  • '{kw['term']}' ({kw['category'] or 'No Category'})")
        
        confirm = input(f"\nRemove these {len(generic_user_keywords)} generic keywords? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            affected = self.db.execute_update(f"""
                UPDATE filter_terms 
                SET is_active = 0 
                WHERE created_by = 'user' AND term IN ({placeholders}) AND is_active = 1
            """, generic_terms)
            
            print(f"✅ Deactivated {affected} generic user keywords")
        else:
            print("❌ Operation cancelled")
    
    def show_menu(self):
        """Show the main menu"""
        while True:
            print("\n" + "="*60)
            print("🔍 DATABASE KEYWORD INSPECTOR")
            print("="*60)
            print("1. 📊 Show Keyword Summary")
            print("2. 👤 Show User Keywords")
            print("3. 🤖 Show Auto-Detected Keywords")
            print("4. ❓ Show Keywords Without Categories")
            print("5. 🔍 Search for Specific Keyword")
            print("6. 🧹 Remove Auto-Detected Keywords")
            print("7. 🧹 Clean Generic User Keywords")
            print("8. 📤 Export Problem Keywords")
            print("9. ❌ Exit")
            
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                self.show_keyword_summary()
            elif choice == '2':
                self.show_user_keywords()
            elif choice == '3':
                self.show_auto_detected_keywords()
            elif choice == '4':
                self.show_keywords_without_category()
            elif choice == '5':
                search_term = input("Enter keyword to search for: ").strip()
                if search_term:
                    self.search_keyword(search_term)
            elif choice == '6':
                self.remove_auto_detected_keywords()
            elif choice == '7':
                self.clean_generic_user_keywords()
            elif choice == '8':
                self.export_problem_keywords()
            elif choice == '9':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-9.")
    
    def export_problem_keywords(self):
        """Export problematic keywords to a file for analysis"""
        print("="*60)
        print("📤 EXPORTING PROBLEM KEYWORDS")
        print("="*60)
        
        # Get all potentially problematic keywords
        problem_keywords = self.db.execute_query("""
            SELECT term, category, created_by, confidence_threshold, is_active, created_at 
            FROM filter_terms 
            WHERE (created_by = 'user' OR category = 'auto_detected' OR category IS NULL)
              AND is_active = 1
            ORDER BY created_by, category, term
        """)
        
        if not problem_keywords:
            print("✅ No problematic keywords found")
            return
        
        filename = "problem_keywords_analysis.txt"
        
        with open(filename, 'w') as f:
            f.write("Database Keyword Analysis Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {self.db.execute_query('SELECT datetime()')[0][0]}\n")
            f.write(f"Total problematic keywords: {len(problem_keywords)}\n\n")
            
            # Group by source
            by_source = defaultdict(list)
            for kw in problem_keywords:
                source = f"{kw['created_by']} / {kw['category'] or 'No Category'}"
                by_source[source].append(kw)
            
            for source, keywords in by_source.items():
                f.write(f"\n{source} ({len(keywords)} keywords)\n")
                f.write("-" * 40 + "\n")
                for kw in keywords:
                    confidence = kw['confidence_threshold'] or 'Default'
                    f.write(f"  {kw['term']} | {confidence}\n")
        
        print(f"✅ Exported {len(problem_keywords)} keywords to {filename}")

def main():
    """Main function"""
    inspector = DatabaseKeywordInspector()
    inspector.show_menu()

if __name__ == "__main__":
    main()