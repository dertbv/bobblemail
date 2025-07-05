
# Strategic Integration Production Configuration
# Auto-generated from threshold optimization

STRATEGIC_INTEGRATION_CONFIG = {
    # Conditional trigger threshold for Tier 3 Strategic analysis
    'confidence_threshold': 0.50,
    
    # Performance targets
    'target_strategic_usage_percent': 1.0,  # <1% of emails
    'target_fast_processing_percent': 99.0,  # ≥99% fast processing
    
    # Tier definitions
    'tier_1_instant': [
        'Adult & Dating Spam',
        'Domain Spam', 
        'Geographic Spam'
    ],
    
    'tier_2_geographic': [
        'IP-based detection',
        'Suspicious ranges',
        'Country risk analysis'
    ],
    
    'tier_3_strategic': [
        'Brand impersonation edge cases',
        'Nextdoor misclassifications',
        'Uncertain authentication cases'
    ],
    
    # Fallback behavior
    'graceful_degradation': True,
    'fallback_to_fast_on_error': True,
    'max_strategic_processing_time_ms': 5000,
    
    # Monitoring
    'track_tier_usage': True,
    'performance_alerts': True,
    'alert_threshold_strategic_percent': 2.0
}

# Usage example:
# classifier = StrategicEmailClassifier(
#     confidence_threshold=STRATEGIC_INTEGRATION_CONFIG['confidence_threshold']
# )
