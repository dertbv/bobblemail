#!/usr/bin/env python3
"""
Unified Keywords Manager
Consolidates CategoryKeywordManager and BuiltinKeywordsManager into a single interface
"""

from database import db
from utils import get_user_choice
from datetime import datetime

class UnifiedKeywordManager:
    """Unified manager for all keyword types (builtin, user, imported)"""
    
    def __init__(self):
        # Complete category list combining both managers
        self.spam_categories = [
            'Financial & Investment Spam',
            'Gambling Spam',
            'Pharmaceutical Spam',
            'Social/Dating Spam',
            'Business Opportunity Spam',
            'Brand Impersonation',
            'Marketing Spam',
            'Health & Medical Spam',  # Was 'Health Scam' in builtin
            'Payment Scam',
            'Phishing',
            'Adult Content Spam',
            'Education/Training Spam',
            'Real Estate Spam',
            'Legal Settlement Scam',
            'Promotional Email'  # New category
        ]
    
    def manage_keywords(self):
        """Main unified keyword management interface"""
        while True:
            self._show_main_menu()
            choice = get_user_choice("Press a key (1-6, 9, or Enter/Escape to exit):", 
                                   ['1', '2', '3', '4', '5', '6', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._view_all_keywords()
            elif choice == '2':
                self._manage_custom_keywords()
            elif choice == '3':
                self._manage_builtin_keywords()
            elif choice == '4':
                self._add_keyword_to_category()
            elif choice == '5':
                self._remove_keyword()
            elif choice == '6':
                self._import_export_menu()
    
    def _show_main_menu(self):
        """Display main unified keywords menu"""
        # Get keyword counts by type
        builtin_count = db.execute_query(
            "SELECT COUNT(*) as count FROM filter_terms WHERE created_by = 'builtin'"
        )[0]['count']
        
        user_count = db.execute_query(
            "SELECT COUNT(*) as count FROM filter_terms WHERE created_by IN ('user', 'import')"
        )[0]['count']
        
        total_count = builtin_count + user_count
        
        print("\n" + "=" * 60)
        print("🔑 UNIFIED KEYWORD MANAGEMENT")
        print("=" * 60)
        print(f"📊 Keyword Statistics:")
        print(f"   • Built-in Keywords: {builtin_count:,}")
        print(f"   • Custom Keywords: {user_count:,}")
        print(f"   • Total Keywords: {total_count:,}")
        print()
        print("📋 MENU OPTIONS:")
        print("1. 👁️  View All Keywords (by category)")
        print("2. 🛠️  Manage Custom Keywords")
        print("3. ⚙️  Manage Built-in Keywords")
        print("4. ➕ Add Keyword to Category")
        print("5. ➖ Remove Keyword")
        print("6. 📁 Import/Export Keywords")
        print()
        print("9. ⬅️  Back to Main Menu")
        print("-" * 60)
    
    def _view_all_keywords(self):
        """View all keywords organized by category and type"""
        print("\n" + "=" * 80)
        print("👁️ ALL KEYWORDS BY CATEGORY")
        print("=" * 80)
        
        for category in sorted(self.spam_categories):
            print(f"\n📂 {category.upper()}")
            print("-" * 60)
            
            # Get keywords for this category
            keywords = db.execute_query("""
                SELECT keyword, created_by, confidence_score, is_enabled 
                FROM filter_terms 
                WHERE category = ? 
                ORDER BY created_by, keyword
            """, (category,))
            
            if not keywords:
                print("   (No keywords defined)")
                continue
            
            # Group by type
            builtin_keywords = [k for k in keywords if k['created_by'] == 'builtin']
            custom_keywords = [k for k in keywords if k['created_by'] in ('user', 'import')]
            
            if builtin_keywords:
                print("   🏗️ Built-in Keywords:")
                for kw in builtin_keywords:
                    status = "✅" if kw['is_enabled'] else "❌"
                    print(f"      {status} {kw['keyword']} (confidence: {kw['confidence_score']:.2f})")
            
            if custom_keywords:
                print("   👤 Custom Keywords:")
                for kw in custom_keywords:
                    status = "✅" if kw['is_enabled'] else "❌"
                    source = "📁" if kw['created_by'] == 'import' else "✏️"
                    print(f"      {status} {source} {kw['keyword']} (confidence: {kw['confidence_score']:.2f})")
        
        input("\nPress Enter to continue...")
    
    def _manage_custom_keywords(self):
        """Manage custom (user-created and imported) keywords"""
        while True:
            print("\n" + "=" * 50)
            print("🛠️ CUSTOM KEYWORDS MANAGEMENT")
            print("=" * 50)
            print("1. 📝 Add Custom Keyword")
            print("2. ✏️  Edit Custom Keyword")
            print("3. ❌ Remove Custom Keyword")
            print("4. 🔄 Enable/Disable Custom Keyword")
            print("5. 📂 View Custom Keywords by Category")
            print("9. ⬅️  Back")
            
            choice = get_user_choice("Select option (1-5, 9):", ['1', '2', '3', '4', '5', '9'])
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._add_custom_keyword()
            elif choice == '2':
                self._edit_custom_keyword()
            elif choice == '3':
                self._remove_custom_keyword()
            elif choice == '4':
                self._toggle_custom_keyword()
            elif choice == '5':
                self._view_custom_keywords_by_category()
    
    def _manage_builtin_keywords(self):
        """Manage built-in keywords (enable/disable only)"""
        while True:
            print("\n" + "=" * 50)
            print("⚙️ BUILT-IN KEYWORDS MANAGEMENT")
            print("=" * 50)
            print("1. 📂 View Built-in Keywords by Category")
            print("2. 🔄 Enable/Disable Built-in Keyword")
            print("3. 🔧 Reset Category to Defaults")
            print("4. 📊 Built-in Keywords Statistics")
            print("9. ⬅️  Back")
            
            choice = get_user_choice("Select option (1-4, 9):", ['1', '2', '3', '4', '9'])
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._view_builtin_keywords_by_category()
            elif choice == '2':
                self._toggle_builtin_keyword()
            elif choice == '3':
                self._reset_category_to_defaults()
            elif choice == '4':
                self._show_builtin_statistics()
    
    def _add_keyword_to_category(self):
        """Add a new keyword to a category (simplified interface)"""
        print("\n" + "=" * 50)
        print("➕ ADD KEYWORD TO CATEGORY")
        print("=" * 50)
        
        # Show categories with numbers
        print("📂 Available Categories:")
        for i, category in enumerate(self.spam_categories, 1):
            print(f"{i:2d}. {category}")
        
        print("0. Cancel")
        
        try:
            choice = int(input("\nSelect category number: ").strip())
            if choice == 0:
                return
            if choice < 1 or choice > len(self.spam_categories):
                print("❌ Invalid category number")
                return
            
            selected_category = self.spam_categories[choice - 1]
            
            # Get keyword
            keyword = input("Enter keyword: ").strip().lower()
            if not keyword:
                print("❌ Keyword cannot be empty")
                return
            
            # Check if keyword already exists
            existing = db.execute_query(
                "SELECT id FROM filter_terms WHERE keyword = ? AND category = ?",
                (keyword, selected_category)
            )
            
            if existing:
                print(f"❌ Keyword '{keyword}' already exists in {selected_category}")
                return
            
            # Get confidence score
            try:
                confidence = float(input("Enter confidence score (0.0-1.0, default 0.5): ").strip() or "0.5")
                if confidence < 0 or confidence > 1:
                    print("❌ Confidence must be between 0.0 and 1.0")
                    return
            except ValueError:
                print("❌ Invalid confidence score")
                return
            
            # Insert keyword
            db.execute_query("""
                INSERT INTO filter_terms (keyword, category, confidence_score, created_by, date_created, is_enabled)
                VALUES (?, ?, ?, 'user', ?, 1)
            """, (keyword, selected_category, confidence, datetime.now().isoformat()))
            
            print(f"✅ Added '{keyword}' to {selected_category} with confidence {confidence}")
            
        except ValueError:
            print("❌ Invalid input")
    
    def _remove_keyword(self):
        """Remove a keyword (user keywords only)"""
        print("\n" + "=" * 50)
        print("➖ REMOVE KEYWORD")
        print("=" * 50)
        
        keyword = input("Enter keyword to remove: ").strip().lower()
        if not keyword:
            print("❌ Keyword cannot be empty")
            return
        
        # Find user keywords only
        keywords = db.execute_query("""
            SELECT id, category, created_by FROM filter_terms 
            WHERE keyword = ? AND created_by IN ('user', 'import')
        """, (keyword,))
        
        if not keywords:
            print(f"❌ User keyword '{keyword}' not found")
            return
        
        if len(keywords) == 1:
            keyword_record = keywords[0]
        else:
            # Multiple matches - let user choose
            print(f"Found {len(keywords)} matches:")
            for i, kw in enumerate(keywords, 1):
                print(f"{i}. {kw['category']} (created by: {kw['created_by']})")
            
            try:
                choice = int(input("Select keyword number: ").strip())
                if choice < 1 or choice > len(keywords):
                    print("❌ Invalid choice")
                    return
                keyword_record = keywords[choice - 1]
            except ValueError:
                print("❌ Invalid input")
                return
        
        # Confirm removal
        confirm = input(f"Remove '{keyword}' from {keyword_record['category']}? (y/N): ").strip().lower()
        if confirm == 'y':
            db.execute_query("DELETE FROM filter_terms WHERE id = ?", (keyword_record['id'],))
            print(f"✅ Removed '{keyword}' from {keyword_record['category']}")
        else:
            print("❌ Removal cancelled")
    
    def _import_export_menu(self):
        """Import/export keywords menu"""
        while True:
            print("\n" + "=" * 50)
            print("📁 IMPORT/EXPORT KEYWORDS")
            print("=" * 50)
            print("1. 📥 Import Keywords from JSON")
            print("2. 📤 Export Keywords to JSON")
            print("3. 📤 Export Built-in Keywords")
            print("4. 📤 Export Custom Keywords")
            print("9. ⬅️  Back")
            
            choice = get_user_choice("Select option (1-4, 9):", ['1', '2', '3', '4', '9'])
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._import_keywords()
            elif choice == '2':
                self._export_all_keywords()
            elif choice == '3':
                self._export_builtin_keywords()
            elif choice == '4':
                self._export_custom_keywords()
    
    # Helper methods for menu functionality
    def _add_custom_keyword(self):
        """Add a custom keyword with full interface"""
        self._add_keyword_to_category()
    
    def _remove_custom_keyword(self):
        """Remove a custom keyword"""
        self._remove_keyword()
    
    def _edit_custom_keyword(self):
        """Edit a custom keyword - placeholder for future implementation"""
        print("\n⚠️  Edit functionality not implemented. Use remove + add instead.")
    
    def _toggle_custom_keyword(self):
        """Enable/disable a custom keyword - placeholder for future implementation"""
        print("\n⚠️  Toggle functionality not implemented.")
    
    def _view_custom_keywords_by_category(self):
        """View custom keywords organized by category"""
        self._view_all_keywords()  # Use existing functionality
    
    def _view_builtin_keywords_by_category(self):
        """View built-in keywords organized by category"""
        self._view_all_keywords()  # Use existing functionality
    
    def _toggle_builtin_keyword(self):
        """Enable/disable a built-in keyword - placeholder for future implementation"""
        print("\n⚠️  Built-in keyword toggle not implemented.")
    
    def _reset_category_to_defaults(self):
        """Reset a category to default built-in keywords - placeholder for future implementation"""
        print("\n⚠️  Reset to defaults not implemented.")
    
    def _show_builtin_statistics(self):
        """Show built-in keywords statistics - placeholder for future implementation"""
        print("\n⚠️  Statistics not implemented.")
    
    def _import_keywords(self):
        """Import keywords from JSON file - placeholder for future implementation"""
        print("\n⚠️  Import functionality not implemented.")
    
    def _export_all_keywords(self):
        """Export all keywords to JSON - placeholder for future implementation"""
        print("\n⚠️  Export functionality not implemented.")
    
    def _export_builtin_keywords(self):
        """Export built-in keywords only - placeholder for future implementation"""
        print("\n⚠️  Export functionality not implemented.")
    
    def _export_custom_keywords(self):
        """Export custom keywords only - placeholder for future implementation"""
        print("\n⚠️  Export functionality not implemented.")

# Backwards compatibility aliases
CategoryKeywordManager = UnifiedKeywordManager
BuiltinKeywordsManager = UnifiedKeywordManager