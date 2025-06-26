#!/usr/bin/env python3
"""
Category Keywords Manager
Manages custom keywords for specific spam categories
"""

from atlas_email.models.database import db
from atlas_email.utils.general import get_user_choice
from datetime import datetime

class CategoryKeywordManager:
    """Manages custom keywords for spam categories"""
    
    def __init__(self):
        self.spam_categories = [
            'Financial & Investment Spam',
            'Gambling Spam',
            'Pharmaceutical Spam',
            'Social/Dating Spam',
            'Business Opportunity Spam',
            'Brand Impersonation',
            'Marketing Spam',
            'Health Scam',
            'Payment Scam',
            'Phishing',
            'Adult Content Spam',
            'Education/Training Spam',
            'Real Estate Spam',
            'Legal Settlement Scam'
        ]
    
    def manage_category_keywords(self):
        """Main category keyword management interface"""
        while True:
            self._show_main_menu()
            choice = get_user_choice("Press a key (1-6, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._view_all_categories()
            elif choice == '2':
                self._manage_category_keywords_menu()
            elif choice == '3':
                self._add_keyword_to_category()
            elif choice == '4':
                self._remove_keyword_from_category()
            elif choice == '5':
                self._import_category_keywords()
            elif choice == '6':
                self._export_category_keywords()
    
    def _show_main_menu(self):
        """Display main category keywords menu"""
        from atlas_email.utils.general import display_application_header
        total_custom_keywords = db.execute_query(
            "SELECT COUNT(*) as count FROM filter_terms WHERE category IS NOT NULL"
        )[0]['count']
        
        active_categories = db.execute_query("""
            SELECT DISTINCT category FROM filter_terms 
            WHERE category IS NOT NULL AND is_active = 1
        """)
        
        display_application_header("CATEGORY KEYWORDS MANAGER")
        print(f"📋 Custom keywords: {total_custom_keywords}")
        print(f"📂 Categories with custom terms: {len(active_categories)}")
        print()
        print("1. 📋 View All Categories & Keywords")
        print("2. 🎯 Manage Specific Category")
        print("3. ➕ Add Keyword to Category")
        print("4. ➖ Remove Keyword from Category")
        print("5. 📤 Import Category Keywords")
        print("6. 📥 Export Category Keywords")
        print("9. ⬅️  Back to Configuration")
    
    def _view_all_categories(self):
        """View all categories and their custom keywords"""
        print("\n📋 ALL SPAM CATEGORIES & CUSTOM KEYWORDS")
        print("=" * 60)
        
        for category in self.spam_categories:
            # Get custom keywords for this category
            keywords = db.execute_query("""
                SELECT term, confidence_threshold, created_at FROM filter_terms 
                WHERE category = ? AND is_active = 1
                ORDER BY term
            """, (category,))
            
            print(f"\n🎯 {category}")
            print("-" * 40)
            
            if keywords:
                for kw in keywords:
                    confidence = kw['confidence_threshold'] or 0.5
                    print(f"  • {kw['term']} (confidence: {confidence:.1f})")
                print(f"  Total custom keywords: {len(keywords)}")
            else:
                print("  📭 No custom keywords (uses built-in terms only)")
        
        print("\n" + "=" * 60)
        input("\nPress Enter to continue...")
    
    def _manage_category_keywords_menu(self):
        """Menu to manage keywords for a specific category"""
        print("\n🎯 SELECT CATEGORY TO MANAGE")
        print("-" * 40)
        
        for i, category in enumerate(self.spam_categories, 1):
            # Get count of custom keywords
            count = db.execute_query("""
                SELECT COUNT(*) as count FROM filter_terms 
                WHERE category = ? AND is_active = 1
            """, (category,))[0]['count']
            
            print(f"{i:2d}. {category} ({count} custom)")
        
        try:
            choice = int(input(f"\nEnter category number (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                self._manage_single_category(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _manage_single_category(self, category):
        """Manage keywords for a single category"""
        while True:
            keywords = db.execute_query("""
                SELECT term, confidence_threshold, created_at FROM filter_terms 
                WHERE category = ? AND is_active = 1
                ORDER BY term
            """, (category,))
            
            print(f"\n🎯 MANAGING: {category}")
            print("=" * 50)
            print(f"📊 Custom keywords: {len(keywords)}")
            
            if keywords:
                print("\n📋 Current custom keywords:")
                for i, kw in enumerate(keywords, 1):
                    confidence = kw['confidence_threshold'] or 0.5
                    print(f"{i:2d}. {kw['term']} (confidence: {confidence:.1f})")
            else:
                print("\n📭 No custom keywords for this category")
                print("💡 This category uses built-in terms only")
            
            print("\nOptions:")
            print("1. ➕ Add Keyword")
            print("2. ➖ Remove Keyword") 
            print("3. 🔧 Edit Keyword Confidence")
            print("9. ⬅️  Back to Categories")
            
            choice = get_user_choice("Press a key (1-3, 9):", ['1', '2', '3', '9'])
            
            if choice is None or choice == '9':
                break
            elif choice == '1':
                self._add_keyword_to_specific_category(category)
            elif choice == '2':
                if keywords:
                    self._remove_keyword_from_specific_category(category, keywords)
                else:
                    print("📭 No keywords to remove")
                    input("Press Enter to continue...")
            elif choice == '3':
                if keywords:
                    self._edit_keyword_confidence(category, keywords)
                else:
                    print("📭 No keywords to edit")
                    input("Press Enter to continue...")
    
    def _add_keyword_to_category(self):
        """Add a keyword to a category (select category first)"""
        print("\n➕ ADD KEYWORD TO CATEGORY")
        print("-" * 30)
        
        # Select category
        for i, category in enumerate(self.spam_categories, 1):
            print(f"{i:2d}. {category}")
        
        try:
            choice = int(input(f"\nSelect category (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                self._add_keyword_to_specific_category(selected_category)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _add_keyword_to_specific_category(self, category):
        """Add a keyword to a specific category"""
        print(f"\n➕ ADD KEYWORD TO: {category}")
        print("-" * 40)
        
        term = input("Enter keyword/phrase: ").strip().lower()
        if not term:
            print("❌ No keyword entered")
            return
        
        # Check if keyword already exists for this category
        existing = db.execute_query("""
            SELECT id FROM filter_terms 
            WHERE term = ? AND category = ? AND is_active = 1
        """, (term, category))
        
        if existing:
            print(f"⚠️  Keyword '{term}' already exists for {category}")
            return
        
        # Get confidence threshold
        try:
            confidence = float(input("Enter confidence threshold (0.1-1.0, default 0.7): ") or "0.7")
            if not 0.1 <= confidence <= 1.0:
                confidence = 0.7
        except ValueError:
            confidence = 0.7
        
        # Add to database
        db.execute_insert("""
            INSERT INTO filter_terms (term, category, confidence_threshold, is_active, created_by)
            VALUES (?, ?, ?, 1, 'user')
        """, (term, category, confidence))
        
        print(f"✅ Added '{term}' to {category} (confidence: {confidence})")
        input("\nPress Enter to continue...")
    
    def _remove_keyword_from_category(self):
        """Remove a keyword from a category (select category first)"""
        print("\n➖ REMOVE KEYWORD FROM CATEGORY")
        print("-" * 35)
        
        # Select category
        for i, category in enumerate(self.spam_categories, 1):
            count = db.execute_query("""
                SELECT COUNT(*) as count FROM filter_terms 
                WHERE category = ? AND is_active = 1
            """, (category,))[0]['count']
            print(f"{i:2d}. {category} ({count} keywords)")
        
        try:
            choice = int(input(f"\nSelect category (1-{len(self.spam_categories)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(self.spam_categories):
                selected_category = self.spam_categories[choice - 1]
                keywords = db.execute_query("""
                    SELECT term, confidence_threshold FROM filter_terms 
                    WHERE category = ? AND is_active = 1
                    ORDER BY term
                """, (selected_category,))
                
                if keywords:
                    self._remove_keyword_from_specific_category(selected_category, keywords)
                else:
                    print(f"📭 No keywords found for {selected_category}")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def _remove_keyword_from_specific_category(self, category, keywords):
        """Remove a keyword from a specific category"""
        print(f"\n➖ REMOVE KEYWORD FROM: {category}")
        print("-" * 40)
        
        for i, kw in enumerate(keywords, 1):
            confidence = kw['confidence_threshold'] or 0.5
            print(f"{i:2d}. {kw['term']} (confidence: {confidence:.1f})")
        
        try:
            choice = int(input(f"\nSelect keyword to remove (1-{len(keywords)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(keywords):
                term_to_remove = keywords[choice - 1]['term']
                
                # Confirm deletion
                confirm = input(f"Remove '{term_to_remove}' from {category}? (yes/no): ").strip().lower()
                if confirm in ('yes', 'y'):
                    db.execute_update("""
                        UPDATE filter_terms SET is_active = 0 
                        WHERE term = ? AND category = ?
                    """, (term_to_remove, category))
                    print(f"✅ Removed '{term_to_remove}' from {category}")
                else:
                    print("❌ Cancelled")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        
        input("\nPress Enter to continue...")
    
    def _edit_keyword_confidence(self, category, keywords):
        """Edit confidence threshold for a keyword"""
        print(f"\n🔧 EDIT KEYWORD CONFIDENCE: {category}")
        print("-" * 45)
        
        for i, kw in enumerate(keywords, 1):
            confidence = kw['confidence_threshold'] or 0.5
            print(f"{i:2d}. {kw['term']} (confidence: {confidence:.1f})")
        
        try:
            choice = int(input(f"\nSelect keyword to edit (1-{len(keywords)}, 0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(keywords):
                selected_term = keywords[choice - 1]['term']
                current_confidence = keywords[choice - 1]['confidence_threshold'] or 0.5
                
                print(f"\nEditing: {selected_term}")
                print(f"Current confidence: {current_confidence:.1f}")
                
                try:
                    new_confidence = float(input("Enter new confidence (0.1-1.0): "))
                    if 0.1 <= new_confidence <= 1.0:
                        db.execute_update("""
                            UPDATE filter_terms SET confidence_threshold = ? 
                            WHERE term = ? AND category = ?
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
    
    def _import_category_keywords(self):
        """Import category keywords from a file with preview and confirmation"""
        print("\n📤 IMPORT CATEGORY KEYWORDS")
        print("-" * 35)
        print("File format: category|keyword|confidence")
        print("Example: Investment Spam|crypto scam|0.8")
        print()
        print("Import behavior:")
        print("• Updates existing keywords with new confidence values")
        print("• Adds new keywords that don't exist")
        print("• Preserves keywords not in the import file")
        
        filename = input("\nEnter filename (or press Enter for 'category_keywords.txt'): ").strip()
        if not filename:
            filename = "category_keywords.txt"
        
        try:
            # First pass: Parse and analyze the file
            print(f"\n🔍 Analyzing file: {filename}")
            print("-" * 40)
            
            planned_additions = []
            planned_updates = []
            errors = []
            
            with open(filename, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('|')
                    if len(parts) < 2:
                        errors.append(f"Line {line_num}: Invalid format - {line}")
                        continue
                    
                    category = parts[0].strip()
                    term = parts[1].strip().lower()
                    
                    try:
                        confidence = float(parts[2].strip()) if len(parts) > 2 else 0.7
                    except (ValueError, IndexError):
                        errors.append(f"Line {line_num}: Invalid confidence value - {line}")
                        continue
                    
                    # Validate confidence range
                    if not (0.1 <= confidence <= 1.0):
                        errors.append(f"Line {line_num}: Confidence {confidence} out of range (0.1-1.0)")
                        continue
                    
                    # Handle legacy category names
                    if category in ['Investment Spam', 'Financial Spam']:
                        category = 'Financial & Investment Spam'
                    
                    if category not in self.spam_categories:
                        errors.append(f"Line {line_num}: Unknown category '{category}'")
                        continue
                    
                    # Check if already exists
                    existing = db.execute_query("""
                        SELECT id, confidence_threshold FROM filter_terms 
                        WHERE term = ? AND category = ? AND is_active = 1
                    """, (term, category))
                    
                    if not existing:
                        # Plan to add new keyword
                        planned_additions.append({
                            'category': category,
                            'term': term,
                            'confidence': confidence,
                            'line': line_num
                        })
                    else:
                        # Plan to update existing keyword
                        existing_confidence = existing[0]['confidence_threshold'] or 0.7
                        if abs(existing_confidence - confidence) > 0.05:  # Only update if significant difference
                            planned_updates.append({
                                'category': category,
                                'term': term,
                                'old_confidence': existing_confidence,
                                'new_confidence': confidence,
                                'line': line_num
                            })
            
            # Display preview report
            print(f"\n📊 IMPORT PREVIEW REPORT")
            print("=" * 50)
            
            if planned_additions:
                print(f"\n➕ NEW KEYWORDS TO ADD ({len(planned_additions)}):")
                print("-" * 30)
                for item in planned_additions[:10]:  # Show first 10
                    print(f"   {item['category']} | {item['term']} | {item['confidence']:.1f}")
                if len(planned_additions) > 10:
                    print(f"   ... and {len(planned_additions) - 10} more")
            
            if planned_updates:
                print(f"\n🔄 KEYWORDS TO UPDATE ({len(planned_updates)}):")
                print("-" * 30)
                for item in planned_updates[:10]:  # Show first 10
                    print(f"   {item['category']} | {item['term']} | {item['old_confidence']:.1f} → {item['new_confidence']:.1f}")
                if len(planned_updates) > 10:
                    print(f"   ... and {len(planned_updates) - 10} more")
            
            if errors:
                print(f"\n⚠️  ERRORS FOUND ({len(errors)}):")
                print("-" * 20)
                for error in errors[:5]:  # Show first 5 errors
                    print(f"   {error}")
                if len(errors) > 5:
                    print(f"   ... and {len(errors) - 5} more errors")
            
            # Summary
            total_changes = len(planned_additions) + len(planned_updates)
            print(f"\n📈 SUMMARY:")
            print(f"   ➕ New keywords: {len(planned_additions)}")
            print(f"   🔄 Updates: {len(planned_updates)}")
            print(f"   ⚠️  Errors: {len(errors)}")
            print(f"   💡 Total changes: {total_changes}")
            
            if total_changes == 0:
                print("\n💡 No changes needed - all keywords are already up to date!")
                input("\nPress Enter to continue...")
                return
            
            # Ask for confirmation
            print(f"\n❓ CONFIRMATION")
            print("-" * 15)
            confirm = input(f"Proceed with importing {total_changes} changes? (yes/no): ").strip().lower()
            
            if confirm not in ('yes', 'y'):
                print("❌ Import cancelled")
                input("\nPress Enter to continue...")
                return
            
            # Second pass: Actually perform the import
            print(f"\n🚀 PERFORMING IMPORT...")
            print("-" * 25)
            
            added_count = 0
            updated_count = 0
            
            # Process additions
            for item in planned_additions:
                db.execute_insert("""
                    INSERT INTO filter_terms (term, category, confidence_threshold, is_active, created_by)
                    VALUES (?, ?, ?, 1, 'import')
                """, (item['term'], item['category'], item['confidence']))
                print(f"➕ Added: {item['category']} | {item['term']} | {item['confidence']:.1f}")
                added_count += 1
            
            # Process updates
            for item in planned_updates:
                db.execute_update("""
                    UPDATE filter_terms 
                    SET confidence_threshold = ?, created_by = 'import_update'
                    WHERE term = ? AND category = ? AND is_active = 1
                """, (item['new_confidence'], item['term'], item['category']))
                print(f"🔄 Updated: {item['category']} | {item['term']} | {item['old_confidence']:.1f} → {item['new_confidence']:.1f}")
                updated_count += 1
            
            print(f"\n✅ Import complete:")
            print(f"   ➕ Added: {added_count} new keywords")
            print(f"   🔄 Updated: {updated_count} existing keywords")
            print(f"   ⚠️  Errors: {len(errors)} lines skipped")
            
            if added_count > 0 or updated_count > 0:
                print(f"\n💡 Successfully imported {added_count + updated_count} keywords!")
        
        except FileNotFoundError:
            print(f"❌ File '{filename}' not found")
            print("💡 Make sure the file is in the same directory as the application")
        except Exception as e:
            print(f"❌ Import error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _export_category_keywords(self):
        """Export category keywords to a file with debugging"""
        print("\n📥 EXPORT CATEGORY KEYWORDS")
        print("-" * 35)
        
        filename = input("Enter filename (or press Enter for 'category_keywords_export.txt'): ").strip()
        if not filename:
            filename = "category_keywords_export.txt"
        
        try:
            # Debug: Show what we're querying
            print("\n🔍 Querying database for category keywords...")
            keywords = db.execute_query("""
                SELECT category, term, confidence_threshold, created_by, created_at FROM filter_terms 
                WHERE category IS NOT NULL AND is_active = 1
                ORDER BY category, term
            """)
            
            print(f"📊 Found {len(keywords)} keywords in database")
            
            # Debug: Show sample of what we found
            if keywords:
                print("\n📋 Sample keywords found:")
                print("-" * 40)
                for i, kw in enumerate(keywords[:5]):  # Show first 5
                    confidence = kw['confidence_threshold'] or 0.7
                    created_by = kw.get('created_by', 'unknown')
                    print(f"   {kw['category']} | {kw['term']} | {confidence:.1f} | {created_by}")
                if len(keywords) > 5:
                    print(f"   ... and {len(keywords) - 5} more keywords")
                
                # Show breakdown by created_by
                import_count = len([k for k in keywords if k.get('created_by') in ['import', 'import_update']])
                user_count = len([k for k in keywords if k.get('created_by') == 'user'])
                builtin_count = len([k for k in keywords if k.get('created_by') not in ['import', 'import_update', 'user']])
                
                print(f"\n📈 Breakdown by source:")
                print(f"   📤 Imported: {import_count}")
                print(f"   👤 User added: {user_count}")
                print(f"   🔧 Built-in: {builtin_count}")
            
            if not keywords:
                print("📭 No category keywords to export")
                return
            
            # Ask if user wants to proceed
            proceed = input(f"\nProceed with exporting {len(keywords)} keywords? (yes/no): ").strip().lower()
            if proceed not in ('yes', 'y'):
                print("❌ Export cancelled")
                return
            
            # Perform the export
            print(f"\n💾 Writing to file: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Category Keywords Export\n")
                f.write(f"# Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total keywords: {len(keywords)}\n")
                f.write("# Format: category|keyword|confidence\n\n")
                
                category_counts = {}
                for kw in keywords:
                    confidence = kw['confidence_threshold'] or 0.7
                    category = kw['category']
                    
                    # Track category counts
                    category_counts[category] = category_counts.get(category, 0) + 1
                    
                    f.write(f"{category}|{kw['term']}|{confidence:.1f}\n")
            
            print(f"✅ Exported {len(keywords)} keywords to {filename}")
            
            # Show category breakdown
            if category_counts:
                print(f"\n📊 Keywords by category:")
                for category, count in sorted(category_counts.items()):
                    print(f"   {category}: {count}")
        
        except Exception as e:
            print(f"❌ Export error: {e}")
            import traceback
            print(f"📋 Error details: {traceback.format_exc()}")
        
        input("\nPress Enter to continue...")
    
    def get_category_stats(self):
        """Get statistics about category keywords"""
        try:
            # Query database for keyword stats
            keywords = db.get_all_category_keywords()
            
            total_keywords = len(keywords)
            categories_with_terms = len(set(kw['category'] for kw in keywords))
            
            return {
                'total_keywords': total_keywords,
                'categories_with_terms': categories_with_terms
            }
        except Exception as e:
            return {
                'total_keywords': 0,
                'categories_with_terms': 0
            }

def main():
    """Main function for standalone testing"""
    manager = CategoryKeywordManager()
    manager.manage_category_keywords()

if __name__ == "__main__":
    main()