#!/usr/bin/env python3
"""
Provider Utilities Module
Centralized provider detection and configuration management
"""

from typing import Dict, Any, List, Optional
from config.constants import PROVIDER_CONFIGS, DEFAULT_PROVIDER_CONFIG


class ProviderDetector:
    """Handles email provider detection and configuration"""
    
    @staticmethod
    def detect_provider_from_email(email_address: str) -> str:
        """
        Detect email provider from email address domain
        
        Args:
            email_address: Email address to analyze
            
        Returns:
            Provider name or 'custom' if unknown
        """
        if not email_address or '@' not in email_address:
            return 'custom'
        
        domain = email_address.split('@')[1].lower()
        
        for provider, config in PROVIDER_CONFIGS.items():
            if domain in config['domains']:
                return provider
        
        return 'custom'
    
    @staticmethod
    def detect_provider_from_sender(sender: str) -> str:
        """
        Detect provider from sender field (may include display name)
        
        Args:
            sender: Sender field from email header
            
        Returns:
            Provider name or 'unknown' if not detectable
        """
        if not sender:
            return 'unknown'
        
        # Extract email from sender field (handles "Name <email@domain.com>" format)
        email_part = sender
        if '<' in sender and '>' in sender:
            start = sender.find('<') + 1
            end = sender.find('>', start)
            if start > 0 and end > start:
                email_part = sender[start:end]
        
        provider = ProviderDetector.detect_provider_from_email(email_part)
        return provider if provider != 'custom' else 'unknown'
    
    @staticmethod
    def get_provider_config(provider_type: str) -> Dict[str, Any]:
        """
        Get provider-specific configuration
        
        Args:
            provider_type: Provider name
            
        Returns:
            Provider configuration dictionary
        """
        return PROVIDER_CONFIGS.get(provider_type, DEFAULT_PROVIDER_CONFIG.copy())
    
    @staticmethod
    def get_all_providers() -> List[str]:
        """Get list of all supported providers"""
        return list(PROVIDER_CONFIGS.keys())
    
    @staticmethod
    def is_major_provider(provider_type: str) -> bool:
        """Check if provider is a major email provider"""
        major_providers = ['gmail', 'outlook', 'icloud', 'yahoo']
        return provider_type in major_providers
    
    @staticmethod
    def get_provider_emoji(provider_type: str) -> str:
        """Get emoji icon for provider"""
        config = ProviderDetector.get_provider_config(provider_type)
        return config.get('emoji', '🔧')
    
    @staticmethod
    def requires_app_password(provider_type: str) -> bool:
        """Check if provider requires app-specific password"""
        config = ProviderDetector.get_provider_config(provider_type)
        return config.get('requires_app_password', False)
    
    @staticmethod
    def get_setup_instructions(provider_type: str) -> List[str]:
        """Get setup instructions for provider"""
        instructions = {
            'gmail': [
                "📝 GMAIL SETUP INSTRUCTIONS:",
                "For Gmail, you MUST use an app-specific password:",
                "1. Go to: https://myaccount.google.com/apppasswords",
                "2. Generate a new app password for 'Mail'",
                "3. Use that 16-character password (not your regular Gmail password)",
                "4. Enable 2-Factor Authentication if not already enabled"
            ],
            'icloud': [
                "📝 ICLOUD SETUP INSTRUCTIONS:",
                "For iCloud, you MUST use an app-specific password:",
                "1. Go to: https://appleid.apple.com/account/manage",
                "2. Sign in and go to 'Security' section",
                "3. Generate an app-specific password for 'Mail'",
                "4. Use that password (not your regular Apple ID password)"
            ],
            'yahoo': [
                "📝 YAHOO SETUP INSTRUCTIONS:",
                "For Yahoo, you may need an app password:",
                "1. Go to Yahoo Account Security",
                "2. Generate an app password if regular password fails",
                "3. Enable 'Less secure app access' if needed"
            ],
            'outlook': [
                "📝 OUTLOOK SETUP INSTRUCTIONS:",
                "For Outlook/Hotmail, use your regular password:",
                "1. Ensure account has IMAP enabled",
                "2. Use your regular Microsoft account password",
                "3. Enable two-factor authentication for better security"
            ],
            'aol': [
                "📝 AOL SETUP INSTRUCTIONS:",
                "For AOL, use your regular password:",
                "1. Ensure IMAP access is enabled",
                "2. Use your regular AOL password",
                "3. Check security settings if connection fails"
            ]
        }
        
        return instructions.get(provider_type, [
            "📝 CUSTOM PROVIDER SETUP:",
            "Configure your IMAP server settings manually:",
            "1. Get IMAP server address from your email provider",
            "2. Use standard port 993 for SSL/TLS",
            "3. Use your regular email password"
        ])
    
    @staticmethod
    def get_optimization_notes(provider_type: str) -> List[str]:
        """Get optimization notes for provider"""
        notes = {
            'icloud': [
                "🍎 iCloud uses optimized bulk deletion",
                "⚡ Individual UID operations are skipped (known to cause parse errors)",
                "🔧 Uses smaller batch sizes for stability"
            ],
            'gmail': [
                "📧 Gmail supports standard deletion methods",
                "🔑 Requires app-specific password (not regular Gmail password)",
                "⚡ Efficient batch processing supported"
            ],
            'outlook': [
                "🏢 Outlook supports standard deletion methods",
                "🔓 Uses regular email password",
                "⚡ Good batch processing performance"
            ],
            'yahoo': [
                "📮 Yahoo supports standard deletion methods",
                "🔑 May require app-specific password",
                "⚡ Moderate batch processing performance"
            ],
            'aol': [
                "📧 AOL supports standard deletion methods",
                "🔓 Uses regular email password",
                "⚡ Standard batch processing"
            ]
        }
        
        return notes.get(provider_type, [
            "🔧 Custom server configuration",
            "⚙️ Uses conservative deletion settings",
            "🛡️ Standard IMAP compatibility mode"
        ])


class ProviderOptimizer:
    """Handles provider-specific optimizations for email processing"""
    
    @staticmethod
    def get_deletion_strategy(provider_type: str) -> str:
        """Get optimal deletion strategy for provider"""
        config = ProviderDetector.get_provider_config(provider_type)
        return config.get('deletion_strategy', 'standard')
    
    @staticmethod
    def get_batch_size(provider_type: str) -> int:
        """Get optimal batch size for provider"""
        config = ProviderDetector.get_provider_config(provider_type)
        return config.get('batch_size', 25)
    
    @staticmethod
    def supports_individual_uid(provider_type: str) -> bool:
        """Check if provider supports individual UID operations"""
        config = ProviderDetector.get_provider_config(provider_type)
        return config.get('supports_individual_uid', True)
    
    @staticmethod
    def get_reselect_frequency(provider_type: str) -> int:
        """Get folder reselection frequency for provider"""
        config = ProviderDetector.get_provider_config(provider_type)
        return config.get('reselect_frequency', 5)
    
    @staticmethod
    def should_skip_individual_marking(provider_type: str) -> bool:
        """Check if provider should skip individual message marking"""
        # This is specifically for iCloud which has IMAP parse errors
        return provider_type == 'icloud'
    
    @staticmethod
    def should_use_bulk_operations(provider_type: str) -> bool:
        """Check if provider should use bulk operations"""
        strategy = ProviderOptimizer.get_deletion_strategy(provider_type)
        return strategy in ['bulk_only', 'bulk_preferred']
    
    @staticmethod
    def get_connection_delay(provider_type: str) -> float:
        """Get delay between connection attempts for provider"""
        delays = {
            'icloud': 0.2,
            'gmail': 0.1,
            'outlook': 0.1,
            'yahoo': 0.1,
            'aol': 0.1
        }
        return delays.get(provider_type, 0.1)
    
    @staticmethod
    def requires_folder_quotes(provider_type: str) -> bool:
        """Check if provider requires quoted folder names"""
        # Most providers handle both, but some are more reliable with quotes
        return provider_type in ['icloud', 'outlook']
    
    @staticmethod
    def get_flag_syntax(provider_type: str) -> str:
        """Get proper flag syntax for provider"""
        config = ProviderDetector.get_provider_config(provider_type)
        requires_parentheses = config.get('requires_parentheses', False)
        
        if requires_parentheses:
            return '+FLAGS (\\Deleted)'
        else:
            return '+FLAGS \\Deleted'


class ProviderValidator:
    """Validates provider configurations and settings"""
    
    @staticmethod
    def validate_email_for_provider(email: str, provider_type: str) -> bool:
        """
        Validate if email address matches expected provider
        
        Args:
            email: Email address to validate
            provider_type: Expected provider type
            
        Returns:
            True if email matches provider, False otherwise
        """
        detected_provider = ProviderDetector.detect_provider_from_email(email)
        return detected_provider == provider_type
    
    @staticmethod
    def validate_provider_config(provider_type: str) -> bool:
        """
        Validate provider configuration completeness
        
        Args:
            provider_type: Provider to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if provider_type not in PROVIDER_CONFIGS and provider_type != 'custom':
            return False
        
        config = ProviderDetector.get_provider_config(provider_type)
        required_fields = ['host', 'port', 'deletion_strategy', 'batch_size']
        
        return all(field in config for field in required_fields)
    
    @staticmethod
    def get_provider_troubleshooting(provider_type: str, error_message: str = "") -> List[str]:
        """
        Get troubleshooting tips for provider-specific issues
        
        Args:
            provider_type: Provider experiencing issues
            error_message: Error message if available
            
        Returns:
            List of troubleshooting tips
        """
        base_tips = [
            "🔍 TROUBLESHOOTING TIPS:",
            "• Check your internet connection",
            "• Verify email address is correct",
            "• Ensure IMAP is enabled in your email settings"
        ]
        
        provider_tips = {
            'gmail': [
                "• Use app-specific password, not regular Gmail password",
                "• Enable 2-Factor Authentication first",
                "• Generate password at: https://myaccount.google.com/apppasswords"
            ],
            'icloud': [
                "• Use app-specific password, not Apple ID password",
                "• Generate password in Apple ID security settings",
                "• Ensure iCloud Mail is enabled"
            ],
            'yahoo': [
                "• Try app-specific password if regular password fails",
                "• Enable 'Less secure app access' in account settings",
                "• Check Yahoo Account Security settings"
            ],
            'outlook': [
                "• Use regular Microsoft account password",
                "• Ensure IMAP is enabled in Outlook.com settings",
                "• Check if account requires 2FA verification"
            ]
        }
        
        tips = base_tips.copy()
        if provider_type in provider_tips:
            tips.extend(provider_tips[provider_type])
        
        # Add error-specific tips
        if error_message:
            error_lower = error_message.lower()
            if 'authentication failed' in error_lower:
                if provider_type in ['gmail', 'icloud', 'yahoo']:
                    tips.append("• Double-check you're using an APP-SPECIFIC password")
                else:
                    tips.append("• Verify your password is correct")
            elif 'connection' in error_lower or 'timeout' in error_lower:
                tips.extend([
                    "• Check firewall/antivirus settings",
                    "• Try different network connection",
                    "• Verify IMAP server address and port"
                ])
        
        return tips


# Export main classes and functions
__all__ = [
    'ProviderDetector',
    'ProviderOptimizer', 
    'ProviderValidator'
]