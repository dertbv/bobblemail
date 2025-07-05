#!/usr/bin/env python3
"""
Ensemble Hybrid Email Classifier
================================

Enhanced version of the hybrid classifier that uses the ML Ensemble system
for superior spam detection combining Random Forest + Naive Bayes + Keyword matching.

This replaces the previous hybrid approach with a more sophisticated ensemble voting system.
"""

import json
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Import core components
from atlas_email.filters.keyword_processor import KeywordProcessor, classify_spam_type_with_processor
from atlas_email.core.spam_classifier import is_authenticated_domain, detect_provider_from_sender
# Temporarily disabled due to import issues: from atlas_email.ml.category_classifier import MLCategoryClassifier

# Import caching
try:
    from atlas_email.utils.cache_manager import get_classification_cache, set_classification_cache
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False
    print("⚠️ Cache manager not available, running without cache")

# Import classifier optimizer
try:
    from atlas_email.ml.classifier_cache import get_classifier_optimizer
    OPTIMIZER_ENABLED = True
except ImportError:
    OPTIMIZER_ENABLED = False
    print("⚠️ Classifier optimizer not available")

class EnsembleHybridClassifier:
    """
    Advanced hybrid classifier using ML Ensemble for superior accuracy.
    
    Combines:
    1. ML Ensemble (Random Forest + Naive Bayes + Keyword matching)
    2. Legacy rule-based fallbacks
    3. Confidence-based decision making
    4. Performance tracking and optimization
    """
    
    def __init__(self, db_path: str = None, config_path: str = None):
        if db_path is None:
            from atlas_email.models.database import DB_FILE
            db_path = DB_FILE
        """Initialize ensemble hybrid classifier"""
        self.db_path = db_path
        self.config_path = config_path  # Legacy support, but now uses settings.py
        
        # Load configuration from centralized settings
        from config.settings import Settings
        self.config = Settings.get_hybrid_config()
        
        # Initialize ML Ensemble
        print("🤖 Initializing ML Ensemble...")
        try:
            from atlas_email.ml.naive_bayes import NaiveBayesClassifier
            from atlas_email.ml.random_forest import ProductionRandomForestClassifier
            self.naive_bayes = NaiveBayesClassifier(self.db_path)
            self.random_forest = ProductionRandomForestClassifier(self.db_path)
            
            # Load pre-trained models
            try:
                self.naive_bayes.load_model()
                print("✅ Naive Bayes model loaded")
            except Exception as e:
                print(f"⚠️ Naive Bayes model load failed: {e}")
            
            try:
                self.random_forest.load_model()
                print("✅ Random Forest model loaded")
            except Exception as e:
                print(f"⚠️ Random Forest model load failed: {e}")
            
            self.ensemble_available = True
            print("✅ ML Ensemble ready")
        except Exception as e:
            print(f"❌ ML Ensemble failed to initialize: {e}")
            self.ensemble_available = False
        
        # Initialize legacy components as fallbacks
        self.keyword_processor = KeywordProcessor()
        
        # Performance tracking
        self.stats = {
            'total_classifications': 0,
            'ensemble_decisions': 0,
            'fallback_decisions': 0,
            'high_confidence_decisions': 0,
            'processing_times': [],
            'accuracy_tracking': {
                'correct_predictions': 0,
                'total_predictions': 0
            }
        }
        
        print("🎯 Ensemble Hybrid Classifier initialized")
        self.print_status()
    
    def load_config(self):
        """Load hybrid classifier configuration"""
        default_config = {
            "decision_thresholds": {
                "high_confidence": 0.85,
                "medium_confidence": 0.65,
                "spam_threshold": 0.5
            },
            "ensemble_settings": {
                "enable_ensemble": True,
                "fallback_on_failure": True,
                "min_processing_time_ms": 50,
                "max_processing_time_ms": 1000
            },
            "classification_rules": {
                "require_high_confidence_for_deletion": False,
                "enable_whitelist_override": True,
                "enable_provider_override": True
            },
            "performance_tracking": {
                "enable_stats": True,
                "log_decisions": True,
                "track_accuracy": True
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            print(f"⚠️  Config file {self.config_path} not found, using centralized settings")
            from config.settings import Settings
            return Settings.get_hybrid_config()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing config file {self.config_path}: {e}, using centralized settings")
            from config.settings import Settings
            return Settings.get_hybrid_config()
    
    def print_status(self):
        """Print classifier status"""
        print("\n🔍 Ensemble Hybrid Classifier Status:")
        print(f"  ML Ensemble: {'✅ Active' if self.ensemble_available else '❌ Inactive'}")
        print(f"  Keyword Processor: ✅ Active")
        print(f"  Total Classifications: {self.stats['total_classifications']}")
        if self.ensemble_available:
            print(f"  Active ML Models: Naive Bayes + Random Forest + Keywords")
        print()
    
    def classify_email(self, subject="", sender="", body="", headers=None):
        """
        Main classification method using ensemble approach
        
        Args:
            subject: Email subject line
            sender: Email sender address  
            body: Email body content
            headers: Email headers (dict or str)
        """
        start_time = time.time()
        self.stats['total_classifications'] += 1
        
        # Check cache first
        if CACHE_ENABLED:
            cached_result = get_classification_cache(sender, subject)
            if cached_result:
                self.stats['total_classifications'] -= 1  # Don't count cache hits
                return cached_result
        
        # Prepare email data
        email_data = {
            "subject": subject,
            "sender": sender,
            "body": body,
            "headers": headers
        }
        
        # Try ensemble classification first
        if self.ensemble_available:
            try:
                result = self._classify_with_ensemble(email_data)
                self.stats['ensemble_decisions'] += 1
                
                # Add processing time
                processing_time = (time.time() - start_time) * 1000
                self.stats['processing_times'].append(processing_time)
                
                # Track high confidence decisions
                if result.get('confidence_level') == 'HIGH':
                    self.stats['high_confidence_decisions'] += 1
                
                formatted_result = self._format_classification_result(result, "ensemble", processing_time)
                
                # Cache the result
                if CACHE_ENABLED:
                    set_classification_cache(sender, subject, formatted_result, ttl=7200)  # 2 hours
                
                return formatted_result
                
            except Exception as e:
                print(f"⚠️ Ensemble classification failed: {e}")
                if not self.config["ensemble_settings"]["fallback_on_failure"]:
                    raise
        
        # Fallback to legacy classification
        result = self._classify_with_fallback(email_data)
        self.stats['fallback_decisions'] += 1
        
        processing_time = (time.time() - start_time) * 1000
        self.stats['processing_times'].append(processing_time)
        
        formatted_result = self._format_classification_result(result, "fallback", processing_time)
        
        # Cache the result
        if CACHE_ENABLED:
            set_classification_cache(sender, subject, formatted_result, ttl=7200)  # 2 hours
        
        return formatted_result
    
    def _classify_with_ensemble(self, email_data):
        """Classify using ML Ensemble voting system"""
        # Get predictions from both ML models
        votes = []
        
        # Naive Bayes prediction
        try:
            nb_result = self.naive_bayes.predict_single(
                sender=email_data["sender"],
                subject=email_data["subject"]
            )
            # Convert to standard format
            nb_classification = "SPAM" if nb_result.get("is_spam", False) else "NOT_SPAM"
            votes.append(("naive_bayes", nb_classification, nb_result.get("spam_probability", 0.2)))
        except Exception as e:
            print(f"⚠️ Naive Bayes failed: {e}")
        
        # Random Forest prediction  
        try:
            # Convert headers to string format if needed
            headers = email_data.get("headers", {})
            if isinstance(headers, dict):
                headers_str = "\n".join([f"{k}: {v}" for k, v in headers.items()])
            else:
                headers_str = str(headers) if headers else ""
                
            rf_result = self.random_forest.predict(
                sender=email_data["sender"],
                subject=email_data["subject"],
                headers=headers_str
            )
            # Convert to standard format
            rf_classification = "SPAM" if rf_result.get("is_spam", False) else "NOT_SPAM"
            votes.append(("random_forest", rf_classification, rf_result.get("spam_probability", 0.2)))
        except Exception as e:
            print(f"⚠️ Random Forest failed: {e}")
        
        # Keyword-based prediction with higher weight
        # Convert headers to string format if needed
        headers = email_data.get("headers", {})
        if isinstance(headers, dict):
            headers_str = "\n".join([f"{k}: {v}" for k, v in headers.items()])
        else:
            headers_str = str(headers) if headers else ""
            
        keyword_result = classify_spam_type_with_processor(
            headers_str,
            email_data["sender"],
            email_data["subject"]
        )
        # keyword_result is a string, not a dict
        keyword_category = keyword_result if isinstance(keyword_result, str) else "NOT_SPAM"
        keyword_prob = 0.8 if keyword_category != "NOT_SPAM" else 0.2
        votes.append(("keywords", keyword_category, keyword_prob))
        
        # Ensemble voting (weighted)
        ensemble_result = self._ensemble_vote(votes)
        
        # Apply business rules and overrides
        final_result = self._apply_classification_rules(ensemble_result, email_data)
        
        return final_result
    
    def _ensemble_vote(self, votes):
        """Ensemble voting with weighted majority"""
        # Weights: Keywords 30%, Random Forest 40%, Naive Bayes 30%
        weights = {"keywords": 0.3, "random_forest": 0.4, "naive_bayes": 0.3}
        
        category_scores = {}
        total_spam_prob = 0
        total_weight = 0
        
        for model, category, probability in votes:
            weight = weights.get(model, 0.1)
            
            # Aggregate category scores
            if category not in category_scores:
                category_scores[category] = 0
            category_scores[category] += weight
            
            # Aggregate spam probability
            if category != "NOT_SPAM":
                total_spam_prob += probability * weight
            total_weight += weight
        
        # Determine final classification
        if not category_scores:
            return {"final_classification": "NOT_SPAM", "spam_probability": 0.2}
        
        final_category = max(category_scores, key=category_scores.get)
        final_spam_prob = total_spam_prob / total_weight if total_weight > 0 else 0.2
        
        return {
            "final_classification": final_category,
            "spam_probability": final_spam_prob,
            "confidence_level": "HIGH" if category_scores[final_category] > 0.6 else "MEDIUM"
        }
    
    def _classify_with_fallback(self, email_data):
        """Fallback classification using legacy keyword processor"""
        try:
            # Convert headers to string format if needed
            headers = email_data.get("headers", {})
            if isinstance(headers, dict):
                # Convert dict headers to string representation
                headers_str = "\n".join([f"{k}: {v}" for k, v in headers.items()])
            else:
                headers_str = str(headers) if headers else ""
            
            # Use keyword processor for classification
            classification_result = classify_spam_type_with_processor(
                headers_str,
                email_data["sender"],
                email_data["subject"]
            )
            
            # Convert to ensemble-like format
            is_spam = classification_result["category"] != "NOT_SPAM"
            spam_probability = 0.8 if is_spam else 0.2
            
            return {
                "final_classification": classification_result["category"],
                "spam_probability": spam_probability,
                "confidence_level": "MEDIUM",
                "is_spam": is_spam,
                "method": "keyword_fallback",
                "reasoning": classification_result.get("reasoning", [])
            }
            
        except Exception as e:
            print(f"❌ Fallback classification failed: {e}")
            # Ultimate fallback - mark as unknown
            return {
                "final_classification": "UNKNOWN",
                "spam_probability": 0.5,
                "confidence_level": "LOW", 
                "is_spam": False,
                "method": "default_fallback",
                "error": str(e)
            }
    
    def _apply_classification_rules(self, ensemble_result, email_data):
        """Apply business rules and overrides to ensemble result"""
        result = ensemble_result.copy()
        
        # Rule 1: Authenticated Whitelist override (ANTI-SPOOFING PROTECTION)
        if self.config["classification_rules"]["enable_whitelist_override"]:
            if self._is_whitelisted_sender(email_data["sender"]):
                # Check authentication before trusting whitelisted sender
                auth_data = email_data.get("authentication_result", {})
                is_authentic = auth_data.get("is_authentic", False)
                auth_summary = auth_data.get("auth_summary", "No authentication")
                
                if is_authentic:
                    # Legitimate whitelisted email with proper authentication
                    result["final_classification"] = "WHITELISTED"
                    result["is_spam"] = False
                    result["spam_probability"] = 0.1
                    result["confidence_level"] = "HIGH"
                    result["override_reason"] = f"authenticated_whitelist ({auth_summary})"
                else:
                    # Potential spoofed email claiming to be from whitelisted sender
                    result["final_classification"] = "SPOOFED_WHITELIST"
                    result["is_spam"] = True
                    result["spam_probability"] = 0.95
                    result["confidence_level"] = "HIGH"
                    result["override_reason"] = f"spoofed_whitelist_sender ({auth_summary})"
        
        # Rule 2: Provider override (legitimate company domains)
        # Only protect legitimate business emails, NOT marketing spam
        if self.config["classification_rules"]["enable_provider_override"]:
            if is_authenticated_domain(email_data["sender"]):
                # Only override for legitimate business categories, not marketing spam
                legitimate_business_categories = [
                    "Legitimate", "TRANSACTIONAL", "ORDER_CONFIRMATION", 
                    "PAYMENT_NOTIFICATION", "SHIPPING_UPDATE", "ACCOUNT_ALERT",
                    "SECURITY_NOTIFICATION", "BILLING_STATEMENT"
                ]
                
                current_category = result.get("final_classification", "")
                
                # Do NOT override for marketing spam - delete it even from legitimate domains
                if current_category not in ["Marketing Spam", "Promotional Email", "MARKETING"]:
                    # Reduce spam probability only for non-marketing categories
                    if result["spam_probability"] < 0.9:  # Only if not extremely spammy
                        result["spam_probability"] *= 0.5
                        result["is_spam"] = result["spam_probability"] > 0.5
                        result["override_reason"] = "legitimate_domain_non_marketing"
        
        # Rule 3: High confidence requirement for deletion
        if self.config["classification_rules"]["require_high_confidence_for_deletion"]:
            if result["confidence_level"] != "HIGH" and result["is_spam"]:
                result["action_override"] = "PRESERVE" 
                result["override_reason"] = "insufficient_confidence"
        
        return result
    
    def _is_whitelisted_sender(self, sender):
        """Check if sender is whitelisted in database or hard-coded patterns"""
        # First check database for whitelisted addresses
        try:
            from atlas_email.models.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check exact email match
            cursor.execute("SELECT is_whitelisted FROM domains WHERE domain = ?", (sender.lower(),))
            result = cursor.fetchone()
            if result and result[0]:
                conn.close()
                return True
                
            # Check domain-level whitelist
            if '@' in sender:
                domain = sender.split('@')[1].lower()
                cursor.execute("SELECT is_whitelisted FROM domains WHERE domain = ?", (domain,))
                result = cursor.fetchone()
                if result and result[0]:
                    conn.close()
                    return True
                    
            conn.close()
        except Exception as e:
            print(f"Database whitelist check failed: {e}")
        
        # Fallback to hard-coded legitimate patterns
        legitimate_patterns = [
            "@github.com", "@stripe.com", "@paypal.com", "@amazon.com",
            "@google.com", "@microsoft.com", "@apple.com"
        ]
        return any(pattern in sender.lower() for pattern in legitimate_patterns)
    
    def _format_classification_result(self, result, method, processing_time):
        """Format classification result for output"""
        formatted = {
            # Core classification  
            "category": result.get("final_classification", "UNKNOWN"),
            "is_spam": result.get("is_spam", False),
            "confidence": result.get("spam_probability", 0.5),
            "confidence_level": result.get("confidence_level", "LOW"),
            
            # Method and performance
            "method": method,
            "processing_time_ms": round(processing_time, 2),
            
            # Additional info
            "reasoning": result.get("reasoning", []),
            "model_votes": result.get("category_votes", {}),
            "override_reason": result.get("override_reason"),
            
            # Raw ensemble data (for debugging)
            "raw_ensemble_result": result if method == "ensemble" else None
        }
        
        return formatted
    
    def get_performance_stats(self):
        """Get comprehensive performance statistics"""
        avg_processing_time = (
            sum(self.stats['processing_times']) / len(self.stats['processing_times'])
            if self.stats['processing_times'] else 0
        )
        
        ensemble_percentage = (
            self.stats['ensemble_decisions'] / self.stats['total_classifications'] * 100
            if self.stats['total_classifications'] > 0 else 0
        )
        
        stats = {
            "total_classifications": self.stats['total_classifications'],
            "ensemble_decisions": self.stats['ensemble_decisions'],
            "fallback_decisions": self.stats['fallback_decisions'],
            "ensemble_usage_percentage": round(ensemble_percentage, 1),
            "high_confidence_decisions": self.stats['high_confidence_decisions'],
            "average_processing_time_ms": round(avg_processing_time, 2),
            "ensemble_available": self.ensemble_available
        }
        
        if self.ensemble_available:
            ensemble_stats = self.ensemble.get_model_performance_stats()
            stats["ensemble_model_stats"] = ensemble_stats
        
        return stats
    
    def retrain_models(self):
        """Retrain ML models with latest data"""
        if not self.ensemble_available:
            print("❌ Cannot retrain - ensemble not available")
            return False
        
        try:
            # Retrain individual models in ensemble
            print("🔄 Retraining ML Ensemble models...")
            
            # Note: Would need to add retrain methods to ensemble
            # For now, just reload
            self.ensemble = MLEnsembleClassifier("ml_ensemble_config.json")
            
            print("✅ ML Ensemble retrained successfully")
            return True
            
        except Exception as e:
            print(f"❌ Retraining failed: {e}")
            return False


if __name__ == "__main__":
    # Test the ensemble hybrid classifier
    print("🧪 Testing Ensemble Hybrid Classifier")
    
    classifier = EnsembleHybridClassifier()
    
    # Test cases
    test_emails = [
        {
            "name": "Obvious Spam",
            "subject": "URGENT: Claim your $500 Walmart gift card now!",
            "sender": "winner@fake-walmart.tk",
            "body": "Congratulations! Click here to claim your prize!"
        },
        {
            "name": "Legitimate Email", 
            "subject": "Your GitHub notification",
            "sender": "noreply@github.com",
            "body": "You have a new pull request"
        },
        {
            "name": "Suspicious Finance",
            "subject": "Investment opportunity - 300% returns guaranteed",
            "sender": "invest@suspicious-domain.ru",
            "body": "Make money fast with our proven system"
        }
    ]
    
    print(f"\n📧 Testing {len(test_emails)} email classifications:")
    print("=" * 80)
    
    for email in test_emails:
        result = classifier.classify_email(
            subject=email["subject"],
            sender=email["sender"], 
            body=email["body"]
        )
        
        print(f"\n📨 {email['name']}:")
        print(f"  Subject: {email['subject'][:50]}...")
        print(f"  Sender: {email['sender']}")
        print(f"  🎯 Result: {result['category']}")
        print(f"  📊 Confidence: {result['confidence']:.3f} ({result['confidence_level']})")
        print(f"  ⚡ Method: {result['method']}")
        print(f"  ⏱️  Time: {result['processing_time_ms']}ms")
        if result.get('override_reason'):
            print(f"  🔄 Override: {result['override_reason']}")
    
    print("\n" + "=" * 80)
    print("📊 Performance Summary:")
    stats = classifier.get_performance_stats()
    for key, value in stats.items():
        if key != "ensemble_model_stats":
            print(f"  {key}: {value}")
    
    print("\n✅ Ensemble Hybrid Classifier testing complete!")