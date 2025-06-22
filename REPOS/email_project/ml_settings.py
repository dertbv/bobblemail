#!/usr/bin/env python3
"""
ML Settings Management Module
Handles machine learning classification settings and tuning interface
"""

import os
from typing import Dict, Any, Optional
from constants import ML_DEFAULT_SETTINGS, ML_SETTINGS_FILE
from utils import (
    safe_json_load, safe_json_save, get_user_choice, get_confirmation,
    format_number, handle_unexpected_error, clear_screen, show_status_and_refresh
)


class MLSettingsManager:
    """Manages ML classification settings with clean separation of concerns"""
    
    def __init__(self, settings_file: str = ML_SETTINGS_FILE):
        self.settings_file = settings_file
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load ML settings from centralized settings or file fallback"""
        try:
            from settings import Settings
            # Load from centralized settings first
            settings = Settings.get_ml_settings()
            return settings
        except ImportError:
            # Fallback to JSON file if settings.py not available
            settings = safe_json_load(self.settings_file, ML_DEFAULT_SETTINGS.copy())
            
            # Merge with defaults to handle new settings
            for key, value in ML_DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
                    
            return settings
    
    def save_settings(self) -> bool:
        """Save current settings to centralized settings.py"""
        try:
            from settings import Settings
            
            # Update the whitelist in settings.py
            if 'custom_whitelist' in self.settings:
                # Update the Settings class whitelist
                Settings.WHITELIST['custom_whitelist'] = self.settings['custom_whitelist']
            
            if 'custom_keyword_whitelist' in self.settings:
                Settings.WHITELIST['custom_keyword_whitelist'] = self.settings['custom_keyword_whitelist']
            
            # Update ML settings if needed
            for key, value in self.settings.items():
                if key in Settings.ML_SETTINGS:
                    Settings.ML_SETTINGS[key] = value
            
            # Also save to JSON for backward compatibility
            safe_json_save(self.settings_file, self.settings)
            
            print("✅ Settings saved to centralized configuration!")
            return True
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
            # Fallback to JSON only
            if safe_json_save(self.settings_file, self.settings):
                print("✅ Settings saved to JSON file (fallback)")
                return True
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        print("\n🔄 RESET TO DEFAULTS")
        print("⚠️  This will reset ALL ML classification settings to defaults")
        
        if get_confirmation("Are you sure? (type 'RESET' to confirm): ", require_strict=True):
            # Remove existing file
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
            
            # Reload defaults
            self.settings = ML_DEFAULT_SETTINGS.copy()
            self.save_settings()
            
            print("✅ All settings reset to defaults!")
            return True
        else:
            print("❌ Reset cancelled")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a specific setting value"""
        self.settings[key] = value
    
    def display_current_settings(self) -> None:
        """Display current detection settings"""
        print("\n📊 ML CLASSIFICATION TUNING")
        print("=" * 60)
        print("🎯 Current Detection Settings:")
        print(f"   • Spam Confidence Threshold: {self.settings['confidence_threshold']}% (lower = more aggressive)")
        print(f"   • Domain Entropy Threshold: {self.settings['entropy_threshold']} (higher = more random detection)")
        print(f"   • Domain Age Threshold: {self.settings['domain_age_threshold']} days")
        print(f"   • Provider-Specific Mode: {'Enabled' if self.settings['provider_specific'] else 'Disabled'}")
        print()


class ThresholdAdjuster:
    """Handles threshold adjustment operations"""
    
    def __init__(self, settings_manager: MLSettingsManager):
        self.settings_manager = settings_manager
    
    def adjust_thresholds_menu(self) -> None:
        """Display threshold adjustment menu"""
        while True:
            self._display_threshold_menu()
            
            choice = get_user_choice("Press a key (1-6, or Enter/Escape to exit):", 
                                   ['1', '2', '3', '4', '5', '6'], allow_enter=True)
            if choice is None or choice == '6':
                break
            
            self._handle_threshold_choice(choice)
    
    def _display_threshold_menu(self) -> None:
        """Display the threshold adjustment menu"""
        settings = self.settings_manager.settings
        
        print("\n🎛️  DETECTION THRESHOLD ADJUSTMENT")
        print("=" * 50)
        print("📊 Current Settings:")
        print(f"   • Confidence Threshold: {settings['confidence_threshold']}%")
        print(f"   • Entropy Threshold: {settings['entropy_threshold']}")
        print(f"   • Domain Age: {settings['domain_age_threshold']} days")
        print()
        print("🎯 Adjustment Options:")
        print("1. 📈 Make More Aggressive (catch more, risk false positives)")
        print("2. 📉 Make More Conservative (fewer false positives, might miss some)")
        print("3. 🎛️  Custom Threshold Values")
        print("4. 📖 Help & Guidelines - Single Page explaining the three settings")
        print("5. 🧪 Test Settings - Working")
        print("6. ⬅️  Back")
    
    def _handle_threshold_choice(self, choice: str) -> None:
        """Handle threshold adjustment choice"""
        if choice == '1':
            self._make_more_aggressive()
        elif choice == '2':
            self._make_more_conservative()
        elif choice == '3':
            self._set_custom_thresholds()
        elif choice == '4':
            self._show_help_guidelines()
        elif choice == '5':
            self._test_settings()
    
    def _make_more_aggressive(self) -> None:
        """Make detection more aggressive"""
        settings = self.settings_manager.settings
        settings['confidence_threshold'] = max(30, settings['confidence_threshold'] - 10)
        settings['entropy_threshold'] = max(2.5, settings['entropy_threshold'] - 0.2)
        settings['domain_age_threshold'] = min(180, settings['domain_age_threshold'] + 30)
        print("🔥 Settings made MORE AGGRESSIVE")
        self.settings_manager.save_settings()
    
    def _make_more_conservative(self) -> None:
        """Make detection more conservative"""
        settings = self.settings_manager.settings
        settings['confidence_threshold'] = min(90, settings['confidence_threshold'] + 10)
        settings['entropy_threshold'] = min(4.0, settings['entropy_threshold'] + 0.2)
        settings['domain_age_threshold'] = max(30, settings['domain_age_threshold'] - 30)
        print("🛡️  Settings made MORE CONSERVATIVE")
        self.settings_manager.save_settings()
    
    def _set_custom_thresholds(self) -> None:
        """Set custom threshold values"""
        settings = self.settings_manager.settings
        
        try:
            new_confidence = int(input(f"Confidence threshold (30-90, current {settings['confidence_threshold']}): "))
            if 30 <= new_confidence <= 90:
                settings['confidence_threshold'] = new_confidence
            
            new_entropy = float(input(f"Entropy threshold (2.0-4.5, current {settings['entropy_threshold']}): "))
            if 2.0 <= new_entropy <= 4.5:
                settings['entropy_threshold'] = new_entropy
                
            new_age = int(input(f"Domain age threshold in days (14-365, current {settings['domain_age_threshold']}): "))
            if 14 <= new_age <= 365:
                settings['domain_age_threshold'] = new_age
                
            print("✅ Custom thresholds applied!")
            self.settings_manager.save_settings()
        except ValueError:
            print("❌ Invalid input. Settings unchanged.")
    
    def _show_current_impact(self) -> None:
        """Show impact analysis of current settings"""
        print("📊 Current settings would affect approximately X% of emails")
        print("💡 This feature will show impact analysis")
    
    def _reset_to_previous(self) -> None:
        """Reset to previous settings"""
        print("🔄 Reset to previous settings feature coming soon")
    
    def _show_help_guidelines(self) -> None:
        """Show comprehensive help and guidelines"""
        print("\n📖 THRESHOLD SETTINGS HELP & GUIDELINES")
        print("=" * 50)
        print("\n🎯 THREE MAIN SETTINGS EXPLAINED:")
        print("\n1. 📈 MAKE MORE AGGRESSIVE:")
        print("   • Catches MORE potential spam emails")
        print("   • Risk of FALSE POSITIVES (deleting legitimate emails)")
        print("   • Best for: Users with heavy spam volume")
        print("   • Confidence threshold: Lowered (catches more emails)")
        print("\n2. 📉 MAKE MORE CONSERVATIVE:")
        print("   • Preserves MORE legitimate emails")
        print("   • Risk of FALSE NEGATIVES (missing actual spam)")
        print("   • Best for: Users who can't afford to lose emails")
        print("   • Confidence threshold: Raised (preserves more emails)")
        print("\n3. 🎛️  CUSTOM THRESHOLD VALUES:")
        print("   • Manual fine-tuning of detection parameters")
        print("   • Confidence: 30-90% (70-80% recommended for most users)")
        print("   • Entropy: 2.0-4.5 (measures domain randomness)")
        print("   • Domain Age: 14-365 days (newer domains more suspicious)")
        print("\n💡 RECOMMENDATIONS:")
        print("   • Start with CONSERVATIVE settings")
        print("   • Monitor results for 1-2 weeks")
        print("   • Adjust based on false positives/negatives")
        print("   • Use TEST SETTINGS to preview changes")
        print("\n⚠️  WARNING: Always backup important emails before changes!")
        print("=" * 50)
        input("\nPress Enter to continue...")
    
    def _test_settings(self) -> None:
        """Test current threshold settings with working functionality"""
        test_manager = RealTimeTestManager(self.settings_manager)
        test_manager.run_testing_session()


class CategoryManager:
    """Manages spam category enable/disable settings"""
    
    def __init__(self, settings_manager: MLSettingsManager):
        self.settings_manager = settings_manager
    
    def category_controls_menu(self) -> None:
        """Display category controls menu"""
        while True:
            self._display_category_menu()
            
            # Limit to single digit choices (1-7)
            valid_choices = ['1', '2', '3', '4', '5', '6', '7']
            
            choice = get_user_choice("Press a key (1-7):", valid_choices)
            if choice is None or choice == '7':
                break
            
            self._handle_category_choice(choice)
    
    def _display_category_menu(self) -> None:
        """Display the category management menu"""
        settings = self.settings_manager.settings
        
        print("\n📂 CATEGORY-SPECIFIC CONTROLS")
        print("=" * 50)
        print("\n🎯 Spam Category Status:")
        
        # Show all categories with their status
        enabled_count = sum(1 for enabled in settings['enabled_categories'].values() if enabled)
        total_count = len(settings['enabled_categories'])
        print(f"📊 {enabled_count}/{total_count} categories enabled")
        print()
        
        for category, enabled in settings['enabled_categories'].items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            risk_level = self._get_category_risk_level(category)
            print(f"   {status} - {category} {risk_level}")
        
        print("\n📋 MANAGEMENT OPTIONS:")
        print("1. 🔄 Toggle All Categories")
        print("2. 🎯 Toggle High-Risk Categories")
        print("3. 🎯 Toggle Medium-Risk Categories")
        print("4. 🎯 Toggle Low-Risk Categories")
        print("5. 📊 Category Statistics")
        print("6. 🧪 Test Categories")
        print("7. ⬅️  Back")
    
    def _handle_category_choice(self, choice: str) -> None:
        """Handle category menu choice"""
        if choice == '1':
            self._toggle_all_categories()
        elif choice == '2':
            self._toggle_risk_categories('high')
        elif choice == '3':
            self._toggle_risk_categories('medium')
        elif choice == '4':
            self._toggle_risk_categories('low')
        elif choice == '5':
            self._show_category_statistics()
        elif choice == '6':
            self._test_categories()
    
    def _get_category_risk_level(self, category: str) -> str:
        """Get risk level indicator for spam categories"""
        from constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES, RISK_LEVELS
        
        if category in HIGH_RISK_CATEGORIES:
            return RISK_LEVELS['high']
        elif category in MEDIUM_RISK_CATEGORIES:
            return RISK_LEVELS['medium']
        else:
            return RISK_LEVELS['low']
    
    def _toggle_all_categories(self) -> None:
        """Toggle all categories"""
        settings = self.settings_manager.settings
        all_enabled = all(settings['enabled_categories'].values())
        
        for category in settings['enabled_categories']:
            settings['enabled_categories'][category] = not all_enabled
        
        status = "DISABLED" if all_enabled else "ENABLED"
        print(f"🔄 All categories {status}")
        self.settings_manager.save_settings()
    
    def _toggle_individual_category(self, letter: str) -> None:
        """Toggle an individual category by letter"""
        letters = 'ABCDEFGHIJKL'
        category_index = letters.index(letter)
        
        settings = self.settings_manager.settings
        categories = list(settings['enabled_categories'].keys())
        
        if category_index < len(categories):
            category_name = categories[category_index]
            current_status = settings['enabled_categories'][category_name]
            settings['enabled_categories'][category_name] = not current_status
            
            status = "ENABLED" if not current_status else "DISABLED"
            print(f"🔄 {category_name} is now {status}")
            self.settings_manager.save_settings()
        else:
            print("❌ Invalid category selection")
    
    def _toggle_risk_categories(self, risk_level: str) -> None:
        """Toggle categories by risk level"""
        from constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES
        
        settings = self.settings_manager.settings
        target_categories = []
        
        if risk_level == 'high':
            target_categories = HIGH_RISK_CATEGORIES
            display_name = "High-Risk"
        elif risk_level == 'medium':
            target_categories = MEDIUM_RISK_CATEGORIES
            display_name = "Medium-Risk"
        else:  # low risk
            all_categories = set(settings['enabled_categories'].keys())
            high_medium = set(HIGH_RISK_CATEGORIES + MEDIUM_RISK_CATEGORIES)
            target_categories = list(all_categories - high_medium)
            display_name = "Low-Risk"
        
        # Check if all target categories are currently enabled
        target_enabled = [settings['enabled_categories'].get(cat, True) for cat in target_categories if cat in settings['enabled_categories']]
        all_enabled = all(target_enabled) if target_enabled else False
        
        # Toggle the target categories
        count = 0
        for category in target_categories:
            if category in settings['enabled_categories']:
                settings['enabled_categories'][category] = not all_enabled
                count += 1
        
        status = "DISABLED" if all_enabled else "ENABLED"
        print(f"🎯 {count} {display_name} categories {status}")
        self.settings_manager.save_settings()
    
    def _show_category_statistics(self) -> None:
        """Show category statistics"""
        settings = self.settings_manager.settings
        from constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES
        
        print("\n📊 CATEGORY STATISTICS")
        print("=" * 40)
        
        total = len(settings['enabled_categories'])
        enabled = sum(1 for enabled in settings['enabled_categories'].values() if enabled)
        disabled = total - enabled
        
        print(f"📋 Total Categories: {total}")
        print(f"✅ Enabled: {enabled}")
        print(f"❌ Disabled: {disabled}")
        print()
        
        # Risk level breakdown
        high_enabled = sum(1 for cat in HIGH_RISK_CATEGORIES if settings['enabled_categories'].get(cat, True))
        medium_enabled = sum(1 for cat in MEDIUM_RISK_CATEGORIES if settings['enabled_categories'].get(cat, True))
        low_categories = set(settings['enabled_categories'].keys()) - set(HIGH_RISK_CATEGORIES + MEDIUM_RISK_CATEGORIES)
        low_enabled = sum(1 for cat in low_categories if settings['enabled_categories'].get(cat, True))
        
        print("⚠️  High Risk Categories:")
        for cat in HIGH_RISK_CATEGORIES:
            if cat in settings['enabled_categories']:
                status = "✅" if settings['enabled_categories'][cat] else "❌"
                print(f"   {status} {cat}")
        
        print("\n🔶 Medium Risk Categories:")
        for cat in MEDIUM_RISK_CATEGORIES:
            if cat in settings['enabled_categories']:
                status = "✅" if settings['enabled_categories'][cat] else "❌"
                print(f"   {status} {cat}")
        
        print("\n🟢 Low Risk Categories:")
        for cat in low_categories:
            if cat in settings['enabled_categories']:
                status = "✅" if settings['enabled_categories'][cat] else "❌"
                print(f"   {status} {cat}")
        
        print("=" * 40)
        input("\nPress Enter to continue...")
    
    def _reset_categories_to_defaults(self) -> None:
        """Reset categories to defaults"""
        print("🔄 Reset categories to defaults feature coming soon")
    
    def _show_category_help(self) -> None:
        """Show category help"""
        print("📖 Category help and descriptions feature coming soon")
    
    def _test_categories(self) -> None:
        """Test categories with working functionality"""
        test_manager = RealTimeTestManager(self.settings_manager)
        test_manager.run_testing_session()
    
    def _export_settings(self) -> None:
        """Export settings"""
        print("📈 Export settings feature coming soon")
    
    def _import_settings(self) -> None:
        """Import settings"""
        print("📥 Import settings feature coming soon")


class RealTimeTestManager:
    """Manages real-time email testing functionality"""
    
    def __init__(self, settings_manager: MLSettingsManager):
        self.settings_manager = settings_manager
    
    def run_testing_session(self) -> None:
        """Run real-time email testing session"""
        print("\n🧪 REAL-TIME EMAIL TESTING")
        print("=" * 50)
        print("Test how the current settings would classify emails")
        print()
        
        while True:
            print("📧 Enter email details to test (or 'q' to quit):")
            
            subject = input("Subject: ").strip()
            if subject.lower() == 'q':
                break
                
            sender = input("Sender: ").strip()
            if sender.lower() == 'q':
                break
            
            try:
                self._test_single_email(subject, sender)
            except Exception as e:
                handle_unexpected_error(e, "email testing")
    
    def _test_single_email(self, subject: str, sender: str) -> None:
        """Test classification of a single email"""
        # Import here to avoid circular dependencies
        from spam_classifier import classify_spam_type
        from domain_validator import DomainValidator
        
        # Create mock headers for testing
        mock_headers = f"Subject: {subject}\nFrom: {sender}\n"
        settings = self.settings_manager.settings
        
        try:
            # Test with spam classifier
            spam_category = classify_spam_type(mock_headers, sender, subject, "")
            
            # Test with domain validator if we have sender domain
            domain_suspicious = False
            domain_reason = ""
            was_validated = False
            
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                validator = DomainValidator()
                domain_suspicious, domain_reason, was_validated = validator.validate_domain_before_deletion(sender, subject)
                domain_suspicious = not domain_suspicious  # Invert logic
            
            print(f"\n📊 CLASSIFICATION RESULT:")
            print(f"   🎯 Spam Category: {spam_category}")
            
            # Determine if it would be deleted based on current settings
            would_delete = False
            reasons = []
            
            if spam_category not in ["Generic Spam", "Promotional Spam"]:
                if settings['enabled_categories'].get(spam_category, True):
                    would_delete = True
                    reasons.append(f"Spam Classifier: {spam_category}")
                else:
                    reasons.append(f"Spam Classifier: {spam_category} (DISABLED)")
            
            if domain_suspicious:
                reasons.append("Suspicious domain")
            elif '@' in sender and any(whitelist_domain in sender.lower() 
                                     for whitelist_domain in settings['custom_whitelist']):
                reasons.append("Custom domain whitelist protection")
                would_delete = False
            elif any(keyword in subject.lower() 
                    for keyword in settings.get('custom_keyword_whitelist', [])):
                reasons.append("Custom keyword whitelist protection")
                would_delete = False
            
            result_icon = "🗑️  WOULD DELETE" if would_delete else "✅ WOULD PRESERVE"
            print(f"   {result_icon}")
            
            if reasons:
                print(f"   📋 Reasons: {'; '.join(reasons)}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")


def ml_classification_tuning():
    """Streamlined single-screen ML configuration interface"""
    try:
        settings_manager = MLSettingsManager()
        
        # Clear screen initially
        clear_screen()
        
        while True:
            _display_unified_config_screen(settings_manager)
            
            # Use regular input to allow single-digit numbers
            try:
                choice_input = input("Choose option (1-8, or press Enter to exit): ").strip()
                if not choice_input:  # Empty input (Enter pressed)
                    break
                
                choice = int(choice_input)
                if not (1 <= choice <= 8):
                    show_status_and_refresh("❌ Please enter a number between 1 and 8")
                    continue
                    
            except ValueError:
                show_status_and_refresh("❌ Please enter a valid number")
                continue
            except KeyboardInterrupt:
                break
                
            # Handle choice and refresh screen
            result_message = _handle_unified_choice(choice, settings_manager)
            if result_message:
                show_status_and_refresh(result_message)
                
    except Exception as e:
        handle_unexpected_error(e, "ML classification tuning")


def _display_unified_config_screen(settings_manager: MLSettingsManager):
    """Display the streamlined configuration screen"""
    settings = settings_manager.settings
    
    print("\n" + "=" * 80)
    print("🎛️  SPAM FILTER CONFIGURATION - All Settings in One Place")
    print("=" * 80)
    
    # Current Settings Summary
    print("📊 CURRENT DETECTION SETTINGS:")
    print(f"   Confidence: {settings['confidence_threshold']}%  |  "
          f"Entropy: {settings['entropy_threshold']:.2f}  |  "
          f"Domain Age: {settings['domain_age_threshold']} days")
    
    # Quick Presets
    print("\n🚀 QUICK PRESETS:")
    print("1. 🛡️  CONSERVATIVE (preserve emails, miss some spam)")
    print("2. ⚖️  BALANCED (recommended for most users)")
    print("3. 🔥 AGGRESSIVE (catch more spam, risk false positives)")
    
    # Category Status Summary
    enabled_count = sum(1 for enabled in settings['enabled_categories'].values() if enabled)
    total_count = len(settings['enabled_categories'])
    print(f"\n📂 SPAM CATEGORIES: {enabled_count}/{total_count} enabled")
    print("   💡 Manage categories in Configuration → Category Manager")
    
    # Advanced Options
    print("\n⚙️  DETECTION SETTINGS:")
    print("4. 🎛️  Custom Threshold Values")
    print("5. ✏️  Edit Whitelist")
    print("6. 🧪 Test Settings")
    
    # Bottom Actions
    print("\n🔧 ACTIONS:")
    print("7. 🛡️  Quick Whitelist Add")
    print("8. 🔄 Reset All Settings")
    print("\n💡 Type a number (1-8) and press Enter, or just press Enter to exit")
    print("=" * 80)


def _get_risk_icon(category: str) -> str:
    """Get compact risk level icon"""
    from constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES
    
    if category in HIGH_RISK_CATEGORIES:
        return "⚠️"
    elif category in MEDIUM_RISK_CATEGORIES:
        return "🔶"
    else:
        return "🟢"


def _handle_unified_choice(choice: int, settings_manager: MLSettingsManager) -> str:
    """Handle all choices in the unified interface"""
    settings = settings_manager.settings
    choice_num = choice
    
    # Quick Presets (1-3)
    if choice_num == 1:  # Conservative
        settings['confidence_threshold'] = 85
        settings['entropy_threshold'] = 3.8
        settings['domain_age_threshold'] = 45
        settings_manager.save_settings()
        return "🛡️  Applied CONSERVATIVE preset - preserves more emails"
        
    elif choice_num == 2:  # Balanced
        settings['confidence_threshold'] = 70
        settings['entropy_threshold'] = 3.2
        settings['domain_age_threshold'] = 90
        settings_manager.save_settings()
        return "⚖️  Applied BALANCED preset - recommended settings"
        
    elif choice_num == 3:  # Aggressive
        settings['confidence_threshold'] = 55
        settings['entropy_threshold'] = 2.8
        settings['domain_age_threshold'] = 120
        settings_manager.save_settings()
        return "🔥 Applied AGGRESSIVE preset - catches more spam"
    
    # Detection Settings (4-6)
    elif choice_num == 4:  # Custom thresholds
        clear_screen()
        _custom_thresholds_inline(settings_manager)
        return "✅ Custom thresholds updated"
    elif choice_num == 5:  # Edit whitelist
        clear_screen()
        _edit_whitelist_inline(settings_manager)
        return "✅ Whitelist updated"
    elif choice_num == 6:  # Test settings
        clear_screen()
        test_manager = RealTimeTestManager(settings_manager)
        test_manager.run_testing_session()
        return "🧪 Testing session completed"
    
    # Actions (7-8)
    elif choice_num == 7:  # Quick whitelist add
        return _quick_whitelist_add(settings_manager)
    elif choice_num == 8:  # Reset
        if get_confirmation("Reset ALL settings to defaults? (type 'RESET'): ", require_strict=True):
            settings_manager.reset_to_defaults()
            return "🔄 All settings reset to defaults"
        else:
            return "❌ Reset cancelled"
    
    return ""


def _toggle_individual_category_unified(letter: str, settings_manager: MLSettingsManager):
    """Toggle individual category in unified interface"""
    letters = 'ABCDEFGHIJKL'
    category_index = letters.index(letter)
    
    settings = settings_manager.settings
    categories = list(settings['enabled_categories'].keys())
    
    if category_index < len(categories):
        category_name = categories[category_index]
        current_status = settings['enabled_categories'][category_name]
        settings['enabled_categories'][category_name] = not current_status
        
        status = "ENABLED" if not current_status else "DISABLED"
        print(f"🔄 {category_name} → {status}")
        settings_manager.save_settings()


def _toggle_risk_categories_unified(risk_level: str, settings_manager: MLSettingsManager) -> str:
    """Toggle categories by risk level in unified interface"""
    from constants import HIGH_RISK_CATEGORIES, MEDIUM_RISK_CATEGORIES
    
    settings = settings_manager.settings
    target_categories = []
    
    if risk_level == 'high':
        target_categories = HIGH_RISK_CATEGORIES
        display_name = "High-Risk"
    elif risk_level == 'medium':
        target_categories = MEDIUM_RISK_CATEGORIES
        display_name = "Medium-Risk"
    else:  # low risk
        all_categories = set(settings['enabled_categories'].keys())
        high_medium = set(HIGH_RISK_CATEGORIES + MEDIUM_RISK_CATEGORIES)
        target_categories = list(all_categories - high_medium)
        display_name = "Low-Risk"
    
    # Check if all target categories are currently enabled
    target_enabled = [settings['enabled_categories'].get(cat, True) for cat in target_categories if cat in settings['enabled_categories']]
    all_enabled = all(target_enabled) if target_enabled else False
    
    # Toggle the target categories
    count = 0
    for category in target_categories:
        if category in settings['enabled_categories']:
            settings['enabled_categories'][category] = not all_enabled
            count += 1
    
    status = "DISABLED" if all_enabled else "ENABLED"
    settings_manager.save_settings()
    return f"🎯 {count} {display_name} categories → {status}"


def _toggle_all_categories_unified(settings_manager: MLSettingsManager) -> str:
    """Toggle all categories in unified interface"""
    settings = settings_manager.settings
    all_enabled = all(settings['enabled_categories'].values())
    
    for category in settings['enabled_categories']:
        settings['enabled_categories'][category] = not all_enabled
    
    status = "DISABLED" if all_enabled else "ENABLED"
    settings_manager.save_settings()
    return f"🔄 All categories → {status}"


def _custom_thresholds_inline(settings_manager: MLSettingsManager):
    """Inline custom threshold editing"""
    settings = settings_manager.settings
    
    print(f"\n🎛️  CUSTOM THRESHOLDS (press Enter to keep current value)")
    
    try:
        # Confidence threshold
        current = settings['confidence_threshold']
        new_val = input(f"Confidence threshold (30-90, current {current}%): ").strip()
        if new_val and 30 <= int(new_val) <= 90:
            settings['confidence_threshold'] = int(new_val)
        
        # Entropy threshold
        current = settings['entropy_threshold']
        new_val = input(f"Entropy threshold (2.0-4.5, current {current:.2f}): ").strip()
        if new_val and 2.0 <= float(new_val) <= 4.5:
            settings['entropy_threshold'] = float(new_val)
            
        # Domain age threshold
        current = settings['domain_age_threshold']
        new_val = input(f"Domain age threshold (14-365 days, current {current}): ").strip()
        if new_val and 14 <= int(new_val) <= 365:
            settings['domain_age_threshold'] = int(new_val)
            
        print("✅ Custom thresholds applied!")
        settings_manager.save_settings()
        
    except ValueError:
        print("❌ Invalid input - settings unchanged")


def _edit_whitelist_inline(settings_manager: MLSettingsManager):
    """Inline whitelist editing"""
    settings = settings_manager.settings
    whitelist = settings.get('custom_whitelist', [])
    
    print(f"\n🛡️  WHITELIST MANAGEMENT ({len(whitelist)} domains)")
    if whitelist:
        print("Current domains:", ", ".join(whitelist[:5]))
        if len(whitelist) > 5:
            print(f"... and {len(whitelist) - 5} more")
    
    print("\nOptions: A=Add domain, R=Remove domain, V=View all, Enter=Done")
    
    while True:
        action = input("Action (A/R/V/Enter): ").strip().upper()
        
        if not action:  # Enter pressed
            break
        elif action == 'A':
            domain = input("Enter domain to add: ").strip().lower()
            if domain and domain not in whitelist:
                whitelist.append(domain)
                print(f"✅ Added {domain}")
            elif domain in whitelist:
                print(f"⚠️  {domain} already in whitelist")
        elif action == 'R':
            if whitelist:
                print("Domains:", ", ".join(f"{i+1}.{d}" for i, d in enumerate(whitelist)))
                try:
                    idx = int(input("Enter number to remove: ")) - 1
                    if 0 <= idx < len(whitelist):
                        removed = whitelist.pop(idx)
                        print(f"✅ Removed {removed}")
                except ValueError:
                    print("❌ Invalid number")
            else:
                print("No domains to remove")
        elif action == 'V':
            if whitelist:
                for i, domain in enumerate(whitelist, 1):
                    print(f"  {i}. {domain}")
            else:
                print("No domains in whitelist")
    
    settings['custom_whitelist'] = whitelist
    settings_manager.settings = settings
    settings_manager.save_settings()


def _quick_whitelist_add(settings_manager: MLSettingsManager) -> str:
    """Quick whitelist domain addition"""
    domain = input("🛡️  Enter domain to whitelist (e.g., example.com): ").strip().lower()
    
    if domain:
        settings = settings_manager.settings
        whitelist = settings.get('custom_whitelist', [])
        
        if domain not in whitelist:
            whitelist.append(domain)
            settings['custom_whitelist'] = whitelist
            settings_manager.settings = settings
            settings_manager.save_settings()
            return f"✅ Added {domain} to whitelist"
        else:
            return f"⚠️  {domain} already whitelisted"
    else:
        return "❌ No domain entered"


class WhitelistManager:
    """Manages domain and email whitelist for spam protection"""
    
    def __init__(self):
        self.settings_manager = MLSettingsManager()
    
    def manage_whitelist(self):
        """Main whitelist management interface"""
        while True:
            self._show_whitelist_menu()
            choice = get_user_choice("Press a key (1-7, 9, or Enter/Escape to exit):", ['1', '2', '3', '4', '5', '6', '7', '9'], allow_enter=True)
            
            if choice is None or choice == '9':
                break
            
            if choice == '1':
                self._view_whitelist()
            elif choice == '2':
                self._add_domain_direct()
            elif choice == '3':
                self._add_email_direct()
            elif choice == '4':
                self._add_keyword_direct()
            elif choice == '5':
                self._remove_from_whitelist()
            elif choice == '6':
                self._import_whitelist()
            elif choice == '7':
                self._export_whitelist()
    
    def _show_whitelist_menu(self):
        """Display whitelist management menu"""
        settings = self.settings_manager.load_settings()
        domains = settings.get('custom_whitelist', [])
        keywords = settings.get('custom_keyword_whitelist', [])
        
        print("\n🛡️  WHITELIST MANAGEMENT")
        print("=" * 50)
        print(f"📊 Protected Domains: {len(domains)}")
        print(f"🔤 Protected Keywords: {len(keywords)}")
        if domains:
            print(f"📋 Recent domains: {', '.join(domains[:3])}")
            if len(domains) > 3:
                print(f"    ... and {len(domains) - 3} more")
        if keywords:
            print(f"🔤 Recent keywords: {', '.join(keywords[:3])}")
            if len(keywords) > 3:
                print(f"    ... and {len(keywords) - 3} more")
        print()
        print("1. 📋 View All Whitelist")
        print("2. 🌐 Add Domain")
        print("3. 📧 Add Email Address")
        print("4. 🔤 Add Keyword")
        print("5. ➖ Remove from Whitelist")
        print("6. 📤 Import Whitelist from File")
        print("7. 📥 Export Whitelist to File")
        print("9. ⬅️  Back to ML Tuning")
        print("=" * 50)
    
    def _view_whitelist(self):
        """View all whitelisted domains and keywords"""
        settings = self.settings_manager.load_settings()
        domains = settings.get('custom_whitelist', [])
        keywords = settings.get('custom_keyword_whitelist', [])
        
        print("\n📋 CURRENT WHITELIST")
        print("=" * 40)
        
        print("🌐 PROTECTED DOMAINS:")
        if not domains:
            print("   📭 No domains currently whitelisted")
        else:
            for i, domain in enumerate(domains, 1):
                print(f"   {i:2d}. {domain}")
        
        print("\n🔤 PROTECTED KEYWORDS:")
        if not keywords:
            print("   📭 No keywords currently whitelisted")
        else:
            for i, keyword in enumerate(keywords, 1):
                print(f"   {i:2d}. {keyword}")
        
        print("=" * 40)
        input("\nPress Enter to continue...")
    
    def _add_to_whitelist(self):
        """Add a domain, email address, or keyword to the whitelist"""
        print("\n➕ ADD TO WHITELIST")
        print("-" * 25)
        print("Options:")
        print("  D) Domain (gmail.com)")
        print("  E) Email address (user@domain.com)")
        print("  K) Keyword (newsletter)")
        
        choice = input("What type? (D/E/K): ").strip().upper()
        
        if choice == 'K':
            self._add_keyword_to_whitelist()
            return
        elif choice not in ['D', 'E']:
            print("❌ Invalid choice")
            return
        
        entry = input("Enter domain or email address: ").strip().lower()
        
        if not entry:
            print("❌ No entry provided")
            return
        
        # Check if it's an email address or domain
        if '@' in entry:
            # It's an email address, extract domain
            if entry.count('@') != 1:
                print("❌ Invalid email address format")
                return
            domain = entry.split('@')[1]
            print(f"📧 Extracting domain '{domain}' from email address")
        else:
            # It's a domain
            domain = entry
        
        # Basic validation
        if not self._is_valid_domain(domain):
            print("❌ Invalid domain format")
            return
        
        settings = self.settings_manager.load_settings()
        whitelist = settings.get('custom_whitelist', [])
        
        if domain in whitelist:
            print(f"⚠️  Domain '{domain}' is already whitelisted")
        else:
            whitelist.append(domain)
            settings['custom_whitelist'] = whitelist
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            print(f"✅ Added '{domain}' to whitelist")
        
        input("\nPress Enter to continue...")
    
    def _add_domain_direct(self):
        """Add a domain directly to the whitelist without type selection"""
        print("\n🌐 ADD DOMAIN TO WHITELIST")
        print("-" * 30)
        
        entry = input("Enter domain (e.g., gmail.com): ").strip().lower()
        
        if not entry:
            print("❌ No domain provided")
            input("\nPress Enter to continue...")
            return
        
        # Basic validation
        if not self._is_valid_domain(entry):
            print("❌ Invalid domain format")
            input("\nPress Enter to continue...")
            return
        
        settings = self.settings_manager.load_settings()
        whitelist = settings.get('custom_whitelist', [])
        
        if entry in whitelist:
            print(f"⚠️  Domain '{entry}' is already whitelisted")
        else:
            whitelist.append(entry)
            settings['custom_whitelist'] = whitelist
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            print(f"✅ Added '{entry}' to whitelist")
        
        input("\nPress Enter to continue...")
    
    def _add_email_direct(self):
        """Add an email address directly to the whitelist (extracts domain)"""
        print("\n📧 ADD EMAIL ADDRESS TO WHITELIST")
        print("-" * 35)
        
        entry = input("Enter email address (e.g., user@domain.com): ").strip().lower()
        
        if not entry:
            print("❌ No email address provided")
            input("\nPress Enter to continue...")
            return
        
        # Check if it's an email address
        if '@' not in entry or entry.count('@') != 1:
            print("❌ Invalid email address format")
            input("\nPress Enter to continue...")
            return
        
        # Keep full email address for specific whitelisting
        email_address = entry.lower()
        print(f"📧 Adding specific email address '{email_address}' to whitelist")
        
        # Basic validation (email is already validated above)
        domain = email_address.split('@')[1]
        if not self._is_valid_domain(domain):
            print("❌ Invalid domain format")
            input("\nPress Enter to continue...")
            return
        
        settings = self.settings_manager.load_settings()
        whitelist = settings.get('custom_whitelist', [])
        
        if email_address in whitelist:
            print(f"⚠️  Email address '{email_address}' is already whitelisted")
        else:
            whitelist.append(email_address)
            settings['custom_whitelist'] = whitelist
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            print(f"✅ Added '{email_address}' to whitelist")
        
        input("\nPress Enter to continue...")
    
    def _add_keyword_direct(self):
        """Add a keyword directly to the whitelist"""
        print("\n🔤 ADD KEYWORD TO WHITELIST")
        print("-" * 30)
        
        keyword = input("Enter keyword to protect (e.g., newsletter, unsubscribe): ").strip().lower()
        
        if not keyword:
            print("❌ No keyword provided")
            input("\nPress Enter to continue...")
            return
        
        if len(keyword) < 2:
            print("❌ Keyword must be at least 2 characters")
            input("\nPress Enter to continue...")
            return
        
        settings = self.settings_manager.load_settings()
        keywords = settings.get('custom_keyword_whitelist', [])
        
        if keyword in keywords:
            print(f"⚠️  Keyword '{keyword}' is already whitelisted")
        else:
            keywords.append(keyword)
            settings['custom_keyword_whitelist'] = keywords
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            print(f"✅ Added keyword '{keyword}' to whitelist")
        
        input("\nPress Enter to continue...")
    
    def _remove_from_whitelist(self):
        """Remove a domain or keyword from the whitelist"""
        settings = self.settings_manager.load_settings()
        domains = settings.get('custom_whitelist', [])
        keywords = settings.get('custom_keyword_whitelist', [])
        
        if not domains and not keywords:
            print("\n📭 No domains or keywords currently whitelisted")
            input("Press Enter to continue...")
            return
        
        print("\n➖ REMOVE FROM WHITELIST")
        print("-" * 30)
        print("What type to remove?")
        print("D) Domain")
        print("K) Keyword")
        
        choice = input("Choose type (D/K): ").strip().upper()
        
        if choice == 'D':
            self._remove_domain(settings, domains)
        elif choice == 'K':
            self._remove_keyword(settings, keywords)
        else:
            print("❌ Invalid choice")
    
    def _remove_domain(self, settings, domains):
        """Remove a domain from whitelist"""
        if not domains:
            print("📭 No domains currently whitelisted")
            input("Press Enter to continue...")
            return
        
        print("\n🌐 DOMAINS:")
        for i, domain in enumerate(domains, 1):
            print(f"{i}. {domain}")
        
        try:
            choice = int(input(f"\nEnter number to remove (1-{len(domains)}, 0 to cancel): "))
            if choice == 0:
                print("❌ Cancelled")
            elif 1 <= choice <= len(domains):
                removed_domain = domains.pop(choice - 1)
                settings['custom_whitelist'] = domains
                self.settings_manager.settings = settings
                self.settings_manager.save_settings()
                print(f"✅ Removed '{removed_domain}' from whitelist")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        
        input("\nPress Enter to continue...")
    
    def _remove_keyword(self, settings, keywords):
        """Remove a keyword from whitelist"""
        if not keywords:
            print("📭 No keywords currently whitelisted")
            input("Press Enter to continue...")
            return
        
        print("\n🔤 KEYWORDS:")
        for i, keyword in enumerate(keywords, 1):
            print(f"{i}. {keyword}")
        
        try:
            choice = int(input(f"\nEnter number to remove (1-{len(keywords)}, 0 to cancel): "))
            if choice == 0:
                print("❌ Cancelled")
            elif 1 <= choice <= len(keywords):
                removed_keyword = keywords.pop(choice - 1)
                settings['custom_keyword_whitelist'] = keywords
                self.settings_manager.settings = settings
                self.settings_manager.save_settings()
                print(f"✅ Removed keyword '{removed_keyword}' from whitelist")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        
        input("\nPress Enter to continue...")
    
    def _import_whitelist(self):
        """Import whitelist from a text file"""
        print("\n📤 IMPORT WHITELIST FROM FILE")
        print("-" * 30)
        
        filename = input("Enter filename (or press Enter for 'whitelist.txt'): ").strip()
        if not filename:
            filename = "whitelist.txt"
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_domains = []
                for line in f:
                    domain = line.strip().lower()
                    if domain and self._is_valid_domain(domain):
                        imported_domains.append(domain)
            
            if not imported_domains:
                print("❌ No valid domains found in file")
                return
            
            settings = self.settings_manager.load_settings()
            whitelist = settings.get('custom_whitelist', [])
            
            new_domains = [d for d in imported_domains if d not in whitelist]
            whitelist.extend(new_domains)
            settings['custom_whitelist'] = whitelist
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            
            print(f"✅ Imported {len(new_domains)} new domains from {filename}")
            if len(imported_domains) > len(new_domains):
                print(f"⚠️  {len(imported_domains) - len(new_domains)} domains were already whitelisted")
        
        except FileNotFoundError:
            print(f"❌ File '{filename}' not found")
        except Exception as e:
            print(f"❌ Error importing file: {e}")
        
        input("\nPress Enter to continue...")
    
    def _export_whitelist(self):
        """Export whitelist to a text file"""
        settings = self.settings_manager.load_settings()
        whitelist = settings.get('custom_whitelist', [])
        
        if not whitelist:
            print("\n📭 No domains to export")
            input("Press Enter to continue...")
            return
        
        print("\n📥 EXPORT WHITELIST TO FILE")
        print("-" * 30)
        
        filename = input("Enter filename (or press Enter for 'whitelist_export.txt'): ").strip()
        if not filename:
            filename = "whitelist_export.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for domain in sorted(whitelist):
                    f.write(f"{domain}\n")
            
            print(f"✅ Exported {len(whitelist)} domains to {filename}")
        
        except Exception as e:
            print(f"❌ Error exporting file: {e}")
        
        input("\nPress Enter to continue...")
    
    def _add_keyword_to_whitelist(self):
        """Add a keyword to the whitelist"""
        print("\n🔤 ADD KEYWORD TO WHITELIST")
        print("-" * 30)
        
        keyword = input("Enter keyword to protect (e.g., 'newsletter', 'unsubscribe'): ").strip().lower()
        
        if not keyword:
            print("❌ No keyword provided")
            return
        
        if len(keyword) < 2:
            print("❌ Keyword must be at least 2 characters")
            return
        
        settings = self.settings_manager.load_settings()
        keyword_whitelist = settings.get('custom_keyword_whitelist', [])
        
        if keyword in keyword_whitelist:
            print(f"⚠️  Keyword '{keyword}' is already whitelisted")
        else:
            keyword_whitelist.append(keyword)
            settings['custom_keyword_whitelist'] = keyword_whitelist
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            print(f"✅ Added keyword '{keyword}' to whitelist")
        
        input("\nPress Enter to continue...")
    
    def _quick_add_keyword(self):
        """Quick keyword addition"""
        keyword = input("🔤 Enter keyword to protect: ").strip().lower()
        
        if not keyword:
            print("❌ No keyword provided")
            input("Press Enter to continue...")
            return
        
        if len(keyword) < 2:
            print("❌ Keyword must be at least 2 characters")
            input("Press Enter to continue...")
            return
        
        settings = self.settings_manager.load_settings()
        keyword_whitelist = settings.get('custom_keyword_whitelist', [])
        
        if keyword not in keyword_whitelist:
            keyword_whitelist.append(keyword)
            settings['custom_keyword_whitelist'] = keyword_whitelist
            self.settings_manager.settings = settings
            self.settings_manager.save_settings()
            print(f"✅ Added keyword '{keyword}' to whitelist")
        else:
            print(f"⚠️  Keyword '{keyword}' already whitelisted")
        
        input("Press Enter to continue...")
    
    def _is_valid_domain(self, domain):
        """Basic domain validation"""
        if not domain or len(domain) < 3:
            return False
        if '.' not in domain:
            return False
        if domain.startswith('.') or domain.endswith('.'):
            return False
        if '..' in domain:
            return False
        return True


# Export main classes and functions
__all__ = [
    'MLSettingsManager',
    'ThresholdAdjuster', 
    'CategoryManager',
    'RealTimeTestManager',
    'WhitelistManager',
    'ml_classification_tuning'
]