# 4-Category Classification Integration Guide

## Quick Start

The 4-category classification system has been deployed to your database. Follow these steps to integrate it into your Atlas Email application.

## 1. Database Migration ✅ COMPLETE

The following changes have been made to your database:
- Added `category_v2`, `subcategory`, `category_confidence_v2` columns
- Created mapping tables for category conversion
- Added A/B testing tracking tables
- Created performance indexes

**Backup location**: `/Users/Badman/mail_filter.db.backup_20250704_003544`

## 2. Update Email Processor

Replace the existing classifier import in your email processor:

```python
# In src/atlas_email/core/email_processor.py

# OLD:
from atlas_email.ml.category_classifier import MultiClassCategoryClassifier

# NEW:
from atlas_email.ml.ab_classifier_integration import ABClassifierIntegration

class EmailProcessor:
    def __init__(self):
        # Start with 10% rollout for safety
        self.classifier = ABClassifierIntegration(rollout_percentage=10.0)
    
    def classify_email(self, sender, subject, headers=""):
        # Use A/B testing classification
        result = self.classifier.classify_with_ab_testing(
            sender=sender,
            subject=subject,
            headers=headers
        )
        
        # The result includes both old and new classification
        # During rollout, it will use the selected classifier
        return result
```

## 3. Update Action Logic

Update your spam action logic to use the new categories:

```python
def determine_action(classification_result):
    category = classification_result.get('category') or classification_result.get('predicted_category')
    confidence = classification_result.get('confidence') or classification_result.get('category_confidence', 0)
    
    if category == 'Dangerous':
        return 'DELETE', 'Dangerous email detected'
    
    elif category == 'Commercial Spam':
        if confidence > 0.8:
            return 'DELETE', f'Commercial spam: {classification_result.get("subcategory", "")}'
        else:
            return 'FLAG_REVIEW', 'Possible commercial spam'
    
    elif category == 'Scams':
        return 'DELETE', f'Scam detected: {classification_result.get("subcategory", "")}'
    
    elif category == 'Legitimate Marketing':
        # Let user preferences decide
        return 'PRESERVE', 'Legitimate marketing email'
    
    else:
        return 'FLAG_REVIEW', 'Unknown classification'
```

## 4. Monitor A/B Testing

Add monitoring to track the new classifier's performance:

```python
# Daily monitoring script
from atlas_email.ml.ab_classifier_integration import ABClassifierIntegration

ab = ABClassifierIntegration()

# Get metrics
metrics = ab.get_ab_testing_metrics(days=7)
print(f"Agreement rate: {metrics['agreement_rate']:.1f}%")
print(f"Auto warranty fixes: {metrics['auto_warranty_fixes']}")

# Get recommendation
rec = ab.get_recommendation()
if rec['recommended_action'] == 'increase':
    print(f"Recommendation: Increase rollout to {rec['recommended_rollout']}%")
    ab.update_rollout_percentage(rec['recommended_rollout'])
```

## 5. Gradual Rollout Schedule

Week 1: 10% → Monitor for issues
Week 2: 30% → Check auto warranty classification
Week 3: 50% → Verify accuracy improvements  
Week 4: 100% → Full deployment

## 6. Key Improvements

### Auto Warranty Fix
- **Before**: Auto warranty → Adult & Dating Spam ❌
- **After**: Auto warranty → Commercial Spam / Auto warranty & insurance ✅

### Simplified Categories
- **Before**: 13+ overlapping categories
- **After**: 4 clear categories with subcategories

### Example Classifications

```python
# Auto warranty (FIXED!)
"Your vehicle warranty expires soon" 
→ Commercial Spam / Auto warranty & insurance

# Phishing
"Verify your PayPal account"
→ Dangerous / Phishing attempts

# Lottery scam  
"You won $1,000,000!"
→ Scams / Lottery & prize scams

# Newsletter
"Monthly product updates"
→ Legitimate Marketing / Newsletter subscriptions
```

## 7. Troubleshooting

### Classifier Not Found
Make sure to add the new classifier files to your Python path:
```bash
export PYTHONPATH=/path/to/atlas_email/src:$PYTHONPATH
```

### Training Required
If you see "Classifier not trained" errors:
```bash
cd src/atlas_email/ml
python3 four_category_classifier.py
```

### Check A/B Testing Results
```sql
SELECT * FROM ab_testing_results 
WHERE timestamp > datetime('now', '-1 day')
ORDER BY timestamp DESC;
```

## 8. Rollback Plan

If issues arise, you can rollback:
```bash
# Restore database backup
cp /Users/Badman/mail_filter.db.backup_20250704_003544 mail_filter.db

# Set rollout to 0%
ab.update_rollout_percentage(0.0)
```

## Support

The implementation includes:
- Comprehensive test suite: `tests/test_four_category_classifier.py`
- Full documentation: `docs/ml/four-category-classification.md`
- Migration tools: `src/atlas_email/ml/migrate_to_four_categories.py`

For questions, review the A/B testing metrics and check the misclassification patterns in the `ab_testing_results` table.