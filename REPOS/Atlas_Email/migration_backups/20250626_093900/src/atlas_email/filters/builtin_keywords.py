#!/usr/bin/env python3
"""
Built-in Keywords Manager
Manages the built-in spam detection keywords that were migrated from hardcoded arrays
"""

from atlas_email.models.database import db
from atlas_email.utils.general import get_user_choice
from datetime import datetime

class BuiltinKeywordsManager:
    """Manages built-in keywords that were migrated from spam_classifier.py"""
    
    def __init__(self):
        self.spam_categories = [
            'Financial & Investment Spam', 'Gambling Spam', 'Pharmaceutical Spam',
            'Social/Dating Spam', 'Business Opportunity Spam', 'Brand Impersonation',
            'Health Scam', 'Payment Scam', 'Adult Content Spam', 'Education/Training Spam',
            'Real Estate Spam', 'Legal Settlement Scam'
        ]
    
    def manage_builtin_keywords(self):
        """Main built-in keywords management interface"""
        while True:
            self._show_main_menu()
            choice = get_user_choice("Press a key (1-7, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '7', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._view_all_builtin_keywords()
            elif choice == '2':
                self._manage_category_builtins()
            elif choice == '3':
                self._edit_builtin_keyword()
            elif choice == '4':
                self._disable_enable_builtin()
            elif choice == '5':
                self._remove_builtin_keyword()
            elif choice == '6':
                self._export_builtin_keywords()
            elif choice == '7':
                self._reset_category_to_defaults()
    
    def _show_main_menu(self):
        """Display main built-in keywords menu"""
        total_builtin = db.execute_query(
            "SELECT COUNT(*) as count FROM filter_terms WHERE created_by = 'builtin'"
        )[0]['count']
        
        active_builtin = db.execute_query(
            "SELECT COUNT(*) as count FROM filter_terms WHERE created_by = 'builtin' AND is_active = 1"
        )[0]['count']
        
        disabled_builtin = total_builtin - active_builtin
        
        print("\n🔧 BUILT-IN KEYWORDS MANAGER")
        print("=" * 50)
        print(f"📊 Total built-in keywords: {total_builtin}")
        print(f"✅ Active: {active_builtin} | ❌ Disabled: {disabled_builtin}")
        print()
        print("⚠️  WARNING: These are the core spam detection keywords!")
        print("   Editing these affects all spam classification.")
        print()
        print("1. 📋 View All Built-in Keywords")
        print("2. 🎯 Manage Category Built-ins")
        print("3. ✏️  Edit Built-in Keyword")
        print("4. 🔄 Enable/Disable Built-in Keywords")
        print("5. 🗑️  Remove Built-in Keyword")
        print("6. 📥 Export Built-in Keywords")
        print("7. 🔄 Reset Category to Defaults")
        print("9. ⬅️  Back to Configuration")
        print("=" * 50)
    
    def _view_all_builtin_keywords(self):
        """View all built-in keywords by category"""
        print("\n📋 ALL BUILT-IN KEYWORDS")
        print("=" * 60)
        
        for category in self.spam_categories:
            keywords = db.execute_query("""
                SELECT term, confidence_threshold, is_active FROM filter_terms 
                WHERE category = ? AND created_by = 'builtin'
                ORDER BY term
            """, (category,))
            
            active_count = sum(1 for k in keywords if k['is_active'])
            disabled_count = len(keywords) - active_count
            
            print(f"\n🎯 {category}")
            print("-" * 50)
            print(f"📊 Total: {len(keywords)} | ✅ Active: {active_count} | ❌ Disabled: {disabled_count}")
            
            if keywords:
                # Show first 10 keywords as preview
                preview_keywords = keywords[:10]
                for kw in preview_keywords:
                    status = "✅" if kw['is_active'] else "❌"
                    confidence = kw['confidence_threshold'] or 0.7
                    print(f"  {status} {kw['term']} (conf: {confidence:.1f})")
                
                if len(keywords) > 10:
                    print(f"  ... and {len(keywords) - 10} more keywords")
            else:
                print("  📭 No built-in keywords found")
        
        print("\n" + "=" * 60)
        input("\nPress Enter to continue...")
    
    def _manage_category_builtins(self):
        """Manage built-in keywords for a specific category"""
        print("\n🎯 SELECT CATEGORY TO MANAGE")
        print("-" * 40)
        
        for i, category in enumerate(self.spam_categories, 1):
            # Get counts
            total = db.execute_query("""
                SELECT COUNT(*) as count FROM filter_terms 
                WHERE category = ? AND created_by = 'builtin'
            """, (category,))[0]['count']
            
            active = db.execute_query("""
                SELECT COUNT(*) as count FROM filter_terms 
                WHERE category = ? AND created_by = 'builtin' AND is_active = 1
            """, (category,))[0]['count']
            
            print(f"{i:2d}. {category} ({active}/{total} active)")
        
        try:
            choice = int(input(f"\nEnter category number (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                self._manage_single_category_builtins(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _manage_single_category_builtins(self, category):
        """Manage built-in keywords for a single category"""
        while True:
            keywords = db.execute_query("""
                SELECT term, confidence_threshold, is_active FROM filter_terms 
                WHERE category = ? AND created_by = 'builtin'
                ORDER BY is_active DESC, term
            """, (category,))
            
            active_count = sum(1 for k in keywords if k['is_active'])
            disabled_count = len(keywords) - active_count
            
            print(f"\n🎯 MANAGING BUILT-IN KEYWORDS: {category}")
            print("=" * 60)
            print(f"📊 Total: {len(keywords)} | ✅ Active: {active_count} | ❌ Disabled: {disabled_count}")
            
            if keywords:
                print(f"\n📋 Built-in keywords (showing first 20):")
                display_keywords = keywords[:20]
                for i, kw in enumerate(display_keywords, 1):
                    status = "✅" if kw['is_active'] else "❌"
                    confidence = kw['confidence_threshold'] or 0.7
                    print(f"{i:2d}. {status} {kw['term']} (conf: {confidence:.1f})")
                
                if len(keywords) > 20:
                    print(f"    ... and {len(keywords) - 20} more keywords")
            
            print("\nOptions:")
            print("1. 🔍 Search Keywords")
            print("2. ✏️  Edit Keyword")
            print("3. 🔄 Toggle Enable/Disable")
            print("4. 🗑️  Remove Keyword")
            print("5. 📊 View All Keywords")
            print("6. 🔄 Reset to Defaults")
            print("9. ⬅️  Back to Categories")
            
            choice = get_user_choice("Press a key (1-6, 9):", ['1', '2', '3', '4', '5', '6', '9'])
            
            if choice is None or choice == '9':
                break
            elif choice == '1':
                self._search_builtin_keywords(category)
            elif choice == '2':
                self._edit_category_builtin_keyword(category)
            elif choice == '3':
                self._toggle_category_builtin_keyword(category)
            elif choice == '4':
                self._remove_category_builtin_keyword(category)
            elif choice == '5':
                self._view_all_category_builtins(category)
            elif choice == '6':
                self._reset_single_category_to_defaults(category)
    
    def _search_builtin_keywords(self, category):
        """Search built-in keywords in a category"""
        print(f"\n🔍 SEARCH BUILT-IN KEYWORDS: {category}")
        print("-" * 45)
        
        search_term = input("Enter search term: ").strip().lower()
        if not search_term:
            print("❌ No search term entered")
            return
        
        keywords = db.execute_query("""
            SELECT term, confidence_threshold, is_active FROM filter_terms 
            WHERE category = ? AND created_by = 'builtin' AND term LIKE ?
            ORDER BY is_active DESC, term
        """, (category, f"%{search_term}%"))
        
        print(f"\n🔍 Search results for '{search_term}' in {category}:")
        print("-" * 50)
        
        if keywords:
            for i, kw in enumerate(keywords, 1):
                status = "✅" if kw['is_active'] else "❌"
                confidence = kw['confidence_threshold'] or 0.7
                print(f"{i:2d}. {status} {kw['term']} (conf: {confidence:.1f})")
            
            print(f"\nFound {len(keywords)} matching keywords")
        else:
            print(f"No keywords found matching '{search_term}'")
        
        input("\nPress Enter to continue...")
    
    def _edit_builtin_keyword(self):
        """Edit a built-in keyword's confidence threshold"""
        print("\n✏️  EDIT BUILT-IN KEYWORD")
        print("-" * 30)
        
        # Select category first
        for i, category in enumerate(self.spam_categories, 1):
            print(f"{i:2d}. {category}")
        
        try:
            cat_choice = int(input(f"\nSelect category (1-{len(self.spam_categories)}, 0 to cancel): "))
            if cat_choice == 0:
                return
            if 1 <= cat_choice <= len(self.spam_categories):
                selected_category = self.spam_categories[cat_choice - 1]
                self._edit_category_builtin_keyword(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _edit_category_builtin_keyword(self, category):
        """Edit a built-in keyword in a specific category"""
        search_term = input(f"\nEnter keyword to edit (or part of it): ").strip().lower()
        if not search_term:
            return
        
        keywords = db.execute_query("""
            SELECT term, confidence_threshold, is_active FROM filter_terms 
            WHERE category = ? AND created_by = 'builtin' AND term LIKE ?
            ORDER BY term
        """, (category, f"%{search_term}%"))
        
        if not keywords:
            print(f"❌ No keywords found matching '{search_term}'")
            return
        
        print(f"\n📋 Matching keywords in {category}:")
        for i, kw in enumerate(keywords, 1):
            status = "✅" if kw['is_active'] else "❌"
            confidence = kw['confidence_threshold'] or 0.7
            print(f"{i:2d}. {status} {kw['term']} (conf: {confidence:.1f})")
        
        try:
            choice = int(input(f"\nSelect keyword to edit (1-{len(keywords)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(keywords):
                selected_term = keywords[choice - 1]['term']
                current_confidence = keywords[choice - 1]['confidence_threshold'] or 0.7
                
                print(f"\nEditing: {selected_term}")
                print(f"Current confidence: {current_confidence:.1f}")
                
                try:
                    new_confidence = float(input("Enter new confidence (0.1-1.0): "))
                    if 0.1 <= new_confidence <= 1.0:
                        db.execute_update("""
                            UPDATE filter_terms SET confidence_threshold = ? 
                            WHERE term = ? AND category = ? AND created_by = 'builtin'
                        """, (new_confidence, selected_term, category))
                        print(f"✅ Updated confidence for '{selected_term}' to {new_confidence:.1f}")
                    else:
                        print("❌ Confidence must be between 0.1 and 1.0")
                except ValueError:
                    print("❌ Invalid confidence value")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        
        input("\nPress Enter to continue...")
    
    def _disable_enable_builtin(self):
        """Enable or disable built-in keywords"""
        print("\n🔄 ENABLE/DISABLE BUILT-IN KEYWORDS")
        print("-" * 40)
        
        for i, category in enumerate(self.spam_categories, 1):
            active = db.execute_query("""
                SELECT COUNT(*) as count FROM filter_terms 
                WHERE category = ? AND created_by = 'builtin' AND is_active = 1
            """, (category,))[0]['count']
            
            total = db.execute_query("""
                SELECT COUNT(*) as count FROM filter_terms 
                WHERE category = ? AND created_by = 'builtin'
            """, (category,))[0]['count']
            
            print(f"{i:2d}. {category} ({active}/{total} active)")
        
        try:
            choice = int(input(f"\nSelect category (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                self._toggle_category_builtin_keyword(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _toggle_category_builtin_keyword(self, category):
        """Toggle enable/disable for keywords in a category"""
        print(f"\n🔄 TOGGLE KEYWORDS: {category}")
        print("-" * 40)
        
        print("Options:")
        print("1. Enable all keywords in category")
        print("2. Disable all keywords in category")
        print("3. Toggle specific keyword")
        
        choice = get_user_choice("Press a key (1-3):", ['1', '2', '3'])
        
        if choice == '1':
            # Enable all
            count = db.execute_update("""
                UPDATE filter_terms SET is_active = 1 
                WHERE category = ? AND created_by = 'builtin'
            """, (category,))
            print(f"✅ Enabled all {count} keywords in {category}")
        
        elif choice == '2':
            # Disable all
            confirm = input(f"⚠️  Disable ALL keywords in {category}? This will affect spam detection! (yes/no): ").strip().lower()
            if confirm in ('yes', 'y'):
                count = db.execute_update("""
                    UPDATE filter_terms SET is_active = 0 
                    WHERE category = ? AND created_by = 'builtin'
                """, (category,))
                print(f"❌ Disabled all {count} keywords in {category}")
            else:
                print("❌ Cancelled")
        
        elif choice == '3':
            # Toggle specific keyword
            search_term = input("Enter keyword to toggle: ").strip().lower()
            if search_term:
                keywords = db.execute_query("""
                    SELECT term, is_active FROM filter_terms 
                    WHERE category = ? AND created_by = 'builtin' AND term LIKE ?
                """, (category, f"%{search_term}%"))
                
                for kw in keywords:
                    new_status = 0 if kw['is_active'] else 1
                    db.execute_update("""
                        UPDATE filter_terms SET is_active = ? 
                        WHERE term = ? AND category = ? AND created_by = 'builtin'
                    """, (new_status, kw['term'], category))
                    
                    status_text = "enabled" if new_status else "disabled"
                    print(f"🔄 {status_text.capitalize()} '{kw['term']}'")
        
        input("\nPress Enter to continue...")
    
    def _remove_builtin_keyword(self):
        """Remove a built-in keyword permanently"""
        print("\n🗑️  REMOVE BUILT-IN KEYWORD")
        print("-" * 35)
        print("⚠️  WARNING: This permanently removes the keyword!")
        print("   Consider disabling instead of removing.")
        
        confirm = input("\nContinue with removal? (yes/no): ").strip().lower()
        if confirm not in ('yes', 'y'):
            print("❌ Cancelled")
            return
        
        # Select category
        for i, category in enumerate(self.spam_categories, 1):
            print(f"{i:2d}. {category}")
        
        try:
            choice = int(input(f"\nSelect category (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                self._remove_category_builtin_keyword(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _remove_category_builtin_keyword(self, category):
        """Remove a built-in keyword from a specific category"""
        search_term = input(f"\nEnter keyword to remove: ").strip().lower()
        if not search_term:
            return
        
        keywords = db.execute_query("""
            SELECT term FROM filter_terms 
            WHERE category = ? AND created_by = 'builtin' AND term LIKE ?
        """, (category, f"%{search_term}%"))
        
        if not keywords:
            print(f"❌ No keywords found matching '{search_term}'")
            return
        
        for kw in keywords:
            confirm = input(f"Remove '{kw['term']}' from {category}? (yes/no): ").strip().lower()
            if confirm in ('yes', 'y'):
                db.execute_update("""
                    DELETE FROM filter_terms 
                    WHERE term = ? AND category = ? AND created_by = 'builtin'
                """, (kw['term'], category))
                print(f"🗑️  Removed '{kw['term']}'")
        
        input("\nPress Enter to continue...")
    
    def _export_builtin_keywords(self):
        """Export all built-in keywords to a file"""
        print("\n📥 EXPORT BUILT-IN KEYWORDS")
        print("-" * 35)
        
        filename = input("Enter filename (or press Enter for 'builtin_keywords_export.txt'): ").strip()
        if not filename:
            filename = "builtin_keywords_export.txt"
        
        try:
            keywords = db.execute_query("""
                SELECT category, term, confidence_threshold, is_active FROM filter_terms 
                WHERE created_by = 'builtin'
                ORDER BY category, term
            """)
            
            if not keywords:
                print("📭 No built-in keywords to export")
                return
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Built-in Keywords Export\n")
                f.write("# Format: category|keyword|confidence|active\n\n")
                
                for kw in keywords:
                    confidence = kw['confidence_threshold'] or 0.7
                    active = "1" if kw['is_active'] else "0"
                    f.write(f"{kw['category']}|{kw['term']}|{confidence:.1f}|{active}\n")
            
            print(f"✅ Exported {len(keywords)} built-in keywords to {filename}")
        
        except Exception as e:
            print(f"❌ Export error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _reset_category_to_defaults(self):
        """Reset a category's built-in keywords to defaults"""
        print("\n🔄 RESET CATEGORY TO DEFAULTS")
        print("-" * 40)
        print("⚠️  This will remove all current built-in keywords")
        print("   for the category and restore original defaults.")
        
        for i, category in enumerate(self.spam_categories, 1):
            print(f"{i:2d}. {category}")
        
        try:
            choice = int(input(f"\nSelect category to reset (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                self._reset_single_category_to_defaults(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _reset_single_category_to_defaults(self, category):
        """Reset a single category to default keywords"""
        confirm = input(f"⚠️  Reset {category} to default keywords? This cannot be undone! (yes/no): ").strip().lower()
        if confirm not in ('yes', 'y'):
            print("❌ Cancelled")
            return
        
        print(f"🔄 Resetting {category} to defaults...")
        print("   You'll need to run the migrator again to restore defaults.")
        print("   Use: python3 builtin_keywords_migrator.py")
        
        # Remove current built-in keywords for this category
        count = db.execute_update("""
            DELETE FROM filter_terms 
            WHERE category = ? AND created_by = 'builtin'
        """, (category,))
        
        print(f"✅ Removed {count} keywords from {category}")
        print("⚠️  Run the migrator to restore default keywords")
        
        input("\nPress Enter to continue...")
    
    def _view_all_category_builtins(self, category):
        """View all built-in keywords for a category"""
        keywords = db.execute_query("""
            SELECT term, confidence_threshold, is_active FROM filter_terms 
            WHERE category = ? AND created_by = 'builtin'
            ORDER BY is_active DESC, term
        """, (category,))
        
        print(f"\n📋 ALL BUILT-IN KEYWORDS: {category}")
        print("=" * 60)
        
        if keywords:
            active_count = sum(1 for k in keywords if k['is_active'])
            print(f"📊 Total: {len(keywords)} | ✅ Active: {active_count}")
            print()
            
            for i, kw in enumerate(keywords, 1):
                status = "✅" if kw['is_active'] else "❌"
                confidence = kw['confidence_threshold'] or 0.7
                print(f"{i:3d}. {status} {kw['term']} (conf: {confidence:.1f})")
        else:
            print("📭 No built-in keywords found")
        
        print("=" * 60)
        input("\nPress Enter to continue...")

def main():
    """Main function for standalone testing"""
    manager = BuiltinKeywordsManager()
    manager.manage_builtin_keywords()

if __name__ == "__main__":
    main()