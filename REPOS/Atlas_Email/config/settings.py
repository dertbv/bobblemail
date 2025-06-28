"""
Centralized Configuration Settings - Consolidated from JSON files
Replaces: ml_settings.json, ml_ensemble_config.json, ensemble_hybrid_config.json
"""

import os
from typing import Dict, List, Any


class Settings:
    """Centralized application settings with environment variable support"""
    
    # ML Classification Settings (from ml_settings.json)
    ML_SETTINGS = {
        "confidence_threshold": int(os.getenv('ML_CONFIDENCE_THRESHOLD', 75)),
        "entropy_threshold": float(os.getenv('ML_ENTROPY_THRESHOLD', 3.2)),
        "domain_age_threshold": int(os.getenv('ML_DOMAIN_AGE_THRESHOLD', 90)),
        "provider_specific": os.getenv('ML_PROVIDER_SPECIFIC', 'true').lower() == 'true',
        
        "enabled_categories": {
            "Phishing": True,
            "Investment Spam": True,
            "Gambling Spam": True,
            "Financial Product Spam": True,
            "Health Scam": True,
            "Payment Scam": True,
            "Brand Impersonation": True,
            "Adult Content Spam": True,
            "Business Opportunity Spam": True,
            "Education/Training Spam": True,
            "Real Estate Spam": True,
            "Legal Settlement Scam": True,
            "Social/Dating Spam": True
        },
        
        "provider_thresholds": {
            "gmail": int(os.getenv('ML_GMAIL_THRESHOLD', 85)),
            "icloud": int(os.getenv('ML_ICLOUD_THRESHOLD', 80)),
            "outlook": int(os.getenv('ML_OUTLOOK_THRESHOLD', 75)),
            "yahoo": int(os.getenv('ML_YAHOO_THRESHOLD', 75)),
            "aol": int(os.getenv('ML_AOL_THRESHOLD', 75)),
            "unknown": int(os.getenv('ML_UNKNOWN_THRESHOLD', 65))
        },
        
        "category_thresholds": {
            "Phishing": int(os.getenv('ML_PHISHING_THRESHOLD', 90)),
            "Payment Scam": int(os.getenv('ML_PAYMENT_SCAM_THRESHOLD', 85)),
            "Health Scam": int(os.getenv('ML_HEALTH_SCAM_THRESHOLD', 80)),
            "Brand Impersonation": int(os.getenv('ML_BRAND_IMPERSONATION_THRESHOLD', 90)),
            "Marketing Spam": int(os.getenv('ML_MARKETING_SPAM_THRESHOLD', 70)),
            "Investment Spam": int(os.getenv('ML_INVESTMENT_SPAM_THRESHOLD', 80)),
            "Gambling Spam": int(os.getenv('ML_GAMBLING_SPAM_THRESHOLD', 75))
        }
    }
    
    # Ensemble Model Configuration (from ml_ensemble_config.json)
    ENSEMBLE_CONFIG = {
        "model_weights": {
            "random_forest": float(os.getenv('ENSEMBLE_RF_WEIGHT', 0.4)),
            "naive_bayes": float(os.getenv('ENSEMBLE_NB_WEIGHT', 0.3)),
            "keyword_matching": float(os.getenv('ENSEMBLE_KEYWORD_WEIGHT', 0.3))
        },
        
        "confidence_thresholds": {
            "high_confidence": float(os.getenv('ENSEMBLE_HIGH_CONFIDENCE', 0.85)),
            "medium_confidence": float(os.getenv('ENSEMBLE_MEDIUM_CONFIDENCE', 0.65)),
            "low_confidence": float(os.getenv('ENSEMBLE_LOW_CONFIDENCE', 0.45))
        },
        
        "consensus_settings": {
            "require_majority": os.getenv('ENSEMBLE_REQUIRE_MAJORITY', 'true').lower() == 'true',
            "category_agreement_threshold": float(os.getenv('ENSEMBLE_CATEGORY_AGREEMENT', 0.6)),
            "enable_confidence_boost": os.getenv('ENSEMBLE_CONFIDENCE_BOOST', 'true').lower() == 'true'
        },
        
        "model_paths": {
            "random_forest": os.getenv('ENSEMBLE_RF_MODEL_PATH', "random_forest_model.pkl"),
            "naive_bayes": os.getenv('ENSEMBLE_NB_MODEL_PATH', "naive_bayes_model.json")
        }
    }
    
    # Hybrid Classifier Configuration (from ensemble_hybrid_config.json)
    HYBRID_CONFIG = {
        "decision_thresholds": {
            "high_confidence": float(os.getenv('HYBRID_HIGH_CONFIDENCE', 0.85)),
            "medium_confidence": float(os.getenv('HYBRID_MEDIUM_CONFIDENCE', 0.65)),
            "spam_threshold": float(os.getenv('HYBRID_SPAM_THRESHOLD', 0.5))
        },
        
        "ensemble_settings": {
            "enable_ensemble": os.getenv('HYBRID_ENABLE_ENSEMBLE', 'true').lower() == 'true',
            "fallback_on_failure": os.getenv('HYBRID_FALLBACK_ON_FAILURE', 'true').lower() == 'true',
            "min_processing_time_ms": int(os.getenv('HYBRID_MIN_PROCESSING_TIME', 50)),
            "max_processing_time_ms": int(os.getenv('HYBRID_MAX_PROCESSING_TIME', 1000))
        },
        
        "classification_rules": {
            "require_high_confidence_for_deletion": os.getenv('HYBRID_REQUIRE_HIGH_CONFIDENCE', 'false').lower() == 'true',
            "enable_whitelist_override": os.getenv('HYBRID_ENABLE_WHITELIST_OVERRIDE', 'true').lower() == 'true',
            "enable_provider_override": os.getenv('HYBRID_ENABLE_PROVIDER_OVERRIDE', 'true').lower() == 'true'
        },
        
        "performance_tracking": {
            "enable_stats": os.getenv('HYBRID_ENABLE_STATS', 'true').lower() == 'true',
            "log_decisions": os.getenv('HYBRID_LOG_DECISIONS', 'true').lower() == 'true',
            "track_accuracy": os.getenv('HYBRID_TRACK_ACCURACY', 'true').lower() == 'true'
        }
    }
    
    # Whitelist Configuration - Personal domains for spam protection
    WHITELIST = {
        "custom_whitelist": [
            "unraid.net",
            "inova.org",
            "aetna.com",
            "dertbv@gmail.com",
            "genesismotorsamerica.comm",
            "statements.myaccountviewonline@lplfinancial.com",
            "anthropic.com"
        ],
        "custom_keyword_whitelist": []
    }
    
    @classmethod
    def get_ml_settings(cls) -> Dict[str, Any]:
        """Get ML classification settings including whitelist"""
        settings = cls.ML_SETTINGS.copy()
        # Include whitelist in ML settings for backward compatibility
        whitelist = cls.get_whitelist()
        settings.update(whitelist)
        return settings
    
    @classmethod
    def get_ensemble_config(cls) -> Dict[str, Any]:
        """Get ensemble model configuration"""
        return cls.ENSEMBLE_CONFIG.copy()
    
    @classmethod
    def get_hybrid_config(cls) -> Dict[str, Any]:
        """Get hybrid classifier configuration"""
        return cls.HYBRID_CONFIG.copy()
    
    @classmethod
    def get_whitelist(cls) -> Dict[str, List[str]]:
        """Get whitelist configuration"""
        return cls.WHITELIST.copy()
    
    @classmethod
    def get_confidence_threshold(cls, provider: str = None) -> int:
        """Get confidence threshold for specific provider or default"""
        if provider and provider.lower() in cls.ML_SETTINGS["provider_thresholds"]:
            return cls.ML_SETTINGS["provider_thresholds"][provider.lower()]
        return cls.ML_SETTINGS["confidence_threshold"]
    
    @classmethod
    def get_category_threshold(cls, category: str) -> int:
        """Get threshold for specific category or default"""
        return cls.ML_SETTINGS["category_thresholds"].get(category, cls.ML_SETTINGS["confidence_threshold"])
    
    @classmethod
    def is_category_enabled(cls, category: str) -> bool:
        """Check if a spam category is enabled"""
        return cls.ML_SETTINGS["enabled_categories"].get(category, False)
    
    @classmethod
    def get_model_weights(cls) -> Dict[str, float]:
        """Get ensemble model weights"""
        return cls.ENSEMBLE_CONFIG["model_weights"].copy()
    
    @classmethod
    def update_whitelist(cls, domain: str, add: bool = True) -> None:
        """Add or remove domain from whitelist"""
        if add and domain not in cls.WHITELIST["custom_whitelist"]:
            cls.WHITELIST["custom_whitelist"].append(domain)
        elif not add and domain in cls.WHITELIST["custom_whitelist"]:
            cls.WHITELIST["custom_whitelist"].remove(domain)
    
    @classmethod
    def update_category_status(cls, category: str, enabled: bool) -> None:
        """Enable or disable a spam category"""
        if category in cls.ML_SETTINGS["enabled_categories"]:
            cls.ML_SETTINGS["enabled_categories"][category] = enabled


# Legacy JSON compatibility functions for migration
class LegacyConfigMigration:
    """Helper functions for migrating from JSON config files"""
    
    @staticmethod
    def load_ml_settings_json() -> Dict[str, Any]:
        """Load ml_settings.json if it exists"""
        import json
        try:
            with open('ml_settings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def load_ensemble_config_json() -> Dict[str, Any]:
        """Load ml_ensemble_config.json if it exists"""
        import json
        try:
            with open('ml_ensemble_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def load_hybrid_config_json() -> Dict[str, Any]:
        """Load ensemble_hybrid_config.json if it exists"""
        import json
        try:
            with open('ensemble_hybrid_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def migrate_if_needed() -> bool:
        """Migrate settings from JSON files if they exist and differ from defaults"""
        import json
        import os
        
        migrated = False
        
        # Check if any JSON config files exist
        json_files = ['ml_settings.json', 'ml_ensemble_config.json', 'ensemble_hybrid_config.json']
        existing_files = [f for f in json_files if os.path.exists(f)]
        
        if existing_files:
            print(f"🔄 Found {len(existing_files)} JSON config files - migration may be needed")
            # Migration logic can be implemented here if needed
            # For now, we'll rely on the default values in Settings class
        
        return migrated


# Convenience imports for backward compatibility
def get_ml_settings():
    """Backward compatibility function"""
    return Settings.get_ml_settings()

def get_ensemble_config():
    """Backward compatibility function"""
    return Settings.get_ensemble_config()

def get_hybrid_config():
    """Backward compatibility function"""
    return Settings.get_hybrid_config()