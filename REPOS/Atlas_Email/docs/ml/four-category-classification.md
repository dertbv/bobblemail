# 4-Category Email Classification System

## Overview

The Atlas Email spam detection system has been upgraded to use a streamlined 4-category classification approach that better aligns with real-world spam patterns and fixes critical misclassification issues.

### Key Improvements

1. **Fixed Auto Warranty Misclassification**: Auto warranty emails are now correctly classified as "Commercial Spam" instead of "Adult & Dating Spam"
2. **Simplified Categories**: Reduced from 13+ overlapping categories to 4 clear, distinct categories
3. **Subcategory Tracking**: Detailed subcategory detection within each main category
4. **A/B Testing Support**: Parallel operation with gradual rollout capability

## The 4 Categories

### 1. Dangerous (Priority: CRITICAL)
Emails that pose immediate security or financial risk to users.

**Subcategories:**
- Phishing attempts
- Malware/virus distribution
- Account compromise attempts
- Fake security alerts
- Cryptocurrency scams

**Examples:**
- "Urgent: Verify your PayPal account or it will be suspended"
- "Security Alert: Suspicious activity on your account"
- "Your computer is infected - Click here to remove virus"

### 2. Commercial Spam (Priority: HIGH)
Unsolicited bulk commercial emails trying to sell products or services.

**Subcategories:**
- Auto warranty & insurance *(NEW - fixes misclassification)*
- Health & medical products
- Adult & dating services
- Gambling promotions
- General product marketing

**Examples:**
- "Your auto warranty is about to expire - Save now!"
- "Lose 30 pounds in 30 days with this miracle pill"
- "Hot singles in your area want to meet"

### 3. Scams (Priority: HIGH)
Deceptive emails attempting to steal money or personal information.

**Subcategories:**
- Advance fee fraud (Nigerian prince)
- Lottery & prize scams
- Work-from-home schemes
- Investment fraud
- Romance scams

**Examples:**
- "Congratulations! You've won the Microsoft Lottery"
- "Make $5000/week working from home"
- "Guaranteed returns on this investment opportunity"

### 4. Legitimate Marketing (Priority: MEDIUM)
Marketing emails from legitimate businesses (may still be unwanted).

**Subcategories:**
- Newsletter subscriptions
- Promotional emails from known companies
- Event invitations
- Product updates
- Sales notifications

**Examples:**
- "Your Amazon order has shipped"
- "Monthly newsletter from YourFavoriteStore"
- "Weekend sale - 20% off everything"

## Implementation Architecture

### Core Components

```
atlas_email/ml/
├── four_category_classifier.py    # Main 4-category classifier
├── subcategory_tagger.py         # Detailed subcategory detection
├── ab_classifier_integration.py   # A/B testing framework
└── migrate_to_four_categories.py  # Database migration script
```

### Classification Flow

1. **Email Received** → Extract features (sender, subject, domain)
2. **4-Category Classification** → Determine main category with confidence
3. **Subcategory Tagging** → Identify specific subcategory within main category
4. **A/B Testing** (optional) → Compare with old classifier for validation
5. **Action Decision** → Delete/Preserve based on category and confidence

## Usage

### Basic Classification

```python
from atlas_email.ml.four_category_classifier import FourCategoryClassifier

# Initialize and train classifier
classifier = FourCategoryClassifier()
classifier.train()

# Classify an email
result = classifier.classify(
    sender="warranty@auto-protect.com",
    subject="Your vehicle warranty expires soon!",
    domain="auto-protect.com"
)

print(f"Category: {result['category']}")           # Commercial Spam
print(f"Subcategory: {result['subcategory']}")    # Auto warranty & insurance
print(f"Confidence: {result['confidence']:.2f}")   # 0.92
print(f"Priority: {result['priority']}")          # HIGH
```

### Subcategory Detection

```python
from atlas_email.ml.subcategory_tagger import SubcategoryTagger

tagger = SubcategoryTagger()
result = tagger.tag_email(
    category="Commercial Spam",
    subject="Endurance Auto Warranty - Save thousands",
    sender="noreply@endurance.net"
)

print(f"Subcategory: {result['subcategory']}")              # Auto warranty & insurance
print(f"Confidence: {result['confidence']:.2f}")            # 0.95
print(f"Matched patterns: {len(result['matched_patterns'])}") # 3
```

### A/B Testing Integration

```python
from atlas_email.ml.ab_classifier_integration import ABClassifierIntegration

# Initialize with 20% rollout to new classifier
ab_classifier = ABClassifierIntegration(rollout_percentage=20.0)

# Classify with A/B testing
result = ab_classifier.classify_with_ab_testing(
    sender="test@example.com",
    subject="Test email"
)

# Check which classifier was used
print(f"Classifier used: {result['classifier_used']}")
print(f"Categories match: {result['ab_testing']['categories_match']}")

# Get A/B testing metrics
metrics = ab_classifier.get_ab_testing_metrics(days=7)
print(f"Agreement rate: {metrics['agreement_rate']:.1f}%")
```

## Database Schema

### New Columns in `processed_emails_bulletproof`

- `category_v2` (TEXT) - New 4-category classification
- `subcategory` (TEXT) - Detailed subcategory within main category
- `category_confidence_v2` (REAL) - Confidence score for new classification
- `classification_version` (INTEGER) - Version of classifier used (1=old, 2=new)

### New Tables

#### `category_mappings`
Maps old categories to new 4-category system
- `old_category` (TEXT PRIMARY KEY)
- `new_category` (TEXT)
- `subcategory` (TEXT)
- `mapping_confidence` (REAL)

#### `subcategory_patterns`
Tracks subcategory detection patterns and effectiveness
- `category` (TEXT)
- `subcategory` (TEXT)
- `pattern_type` (TEXT)
- `pattern_value` (TEXT)
- `effectiveness` (REAL)
- `occurrence_count` (INTEGER)

#### `ab_testing_results`
Tracks A/B testing comparisons
- `test_id` (TEXT)
- `old_category` (TEXT)
- `new_category` (TEXT)
- `categories_match` (BOOLEAN)
- `processing_time_old` (REAL)
- `processing_time_new` (REAL)

## Migration Guide

### Step 1: Backup Database
```bash
cp mail_filter.db mail_filter.db.backup
```

### Step 2: Run Migration Script
```bash
cd src/atlas_email/ml
python migrate_to_four_categories.py
```

The migration script will:
1. Create a timestamped backup
2. Add new database columns
3. Create mapping tables
4. Migrate existing classifications
5. Fix auto warranty misclassifications
6. Create performance indexes

### Step 3: Train New Classifier
```python
from atlas_email.ml.four_category_classifier import FourCategoryClassifier

classifier = FourCategoryClassifier()
stats = classifier.train()
classifier.save_model()

print(f"Training accuracy: {stats['test_score']:.3f}")
```

### Step 4: Enable A/B Testing
Start with low rollout percentage and gradually increase:

```python
# Week 1: 10% rollout
ab = ABClassifierIntegration(rollout_percentage=10.0)

# Week 2: Check metrics and increase if good
metrics = ab.get_ab_testing_metrics()
if metrics['agreement_rate'] > 85:
    ab.update_rollout_percentage(30.0)

# Week 3: Further increase
ab.update_rollout_percentage(50.0)

# Week 4: Full rollout
ab.update_rollout_percentage(100.0)
```

## Performance Metrics

### Expected Improvements

1. **Auto Warranty Classification**: 95%+ accuracy (was ~0% before)
2. **Overall Accuracy**: >95% on all categories
3. **Dangerous Email Detection**: >99% detection rate
4. **False Positive Rate**: <1% for Legitimate Marketing
5. **Processing Speed**: <50ms per email

### Monitoring

Use the A/B testing framework to monitor performance:

```python
# Generate comprehensive report
ab = ABClassifierIntegration()
report_file = ab.generate_ab_report()

# Get recommendation
recommendation = ab.get_recommendation()
print(f"Recommended action: {recommendation['recommended_action']}")
print(f"Confidence: {recommendation['confidence']:.2f}")
```

## Troubleshooting

### Classifier Not Trained Error
```python
# Check if classifier is trained
if not classifier.is_trained:
    classifier.train()
```

### Low Confidence Classifications
- Check if email subject/sender contains enough information
- Review subcategory patterns for effectiveness
- Consider retraining with more recent data

### A/B Testing Disagreements
- Review mismatched classifications in `ab_testing_results` table
- Identify patterns in disagreements
- Adjust subcategory patterns if needed

## API Integration

### Update Email Processing Pipeline

```python
# In email_processor.py
from atlas_email.ml.ab_classifier_integration import ABClassifierIntegration

class EmailProcessor:
    def __init__(self):
        # Use A/B testing integration during rollout
        self.classifier = ABClassifierIntegration(rollout_percentage=50.0)
    
    def process_email(self, email):
        # Classify email
        result = self.classifier.classify_with_ab_testing(
            sender=email.sender,
            subject=email.subject,
            domain=email.domain
        )
        
        # Take action based on category
        if result['category'] == 'Dangerous':
            action = 'DELETE'
            reason = f"Dangerous email: {result['subcategory']}"
        elif result['category'] in ['Commercial Spam', 'Scams']:
            if result['confidence'] > 0.8:
                action = 'DELETE'
                reason = f"{result['category']}: {result['subcategory']}"
            else:
                action = 'FLAG_REVIEW'
                reason = "Low confidence spam detection"
        else:  # Legitimate Marketing
            action = 'PRESERVE'
            reason = "Legitimate marketing email"
        
        return action, reason
```

## Future Enhancements

1. **User Feedback Integration**: Update pattern effectiveness based on user corrections
2. **Dynamic Subcategory Learning**: Automatically discover new subcategories
3. **Temporal Pattern Analysis**: Detect spam campaigns and trending patterns
4. **Multi-language Support**: Extend classification to non-English emails
5. **Attachment Analysis**: Include attachment types in classification decisions

## Support

For issues or questions:
1. Check A/B testing metrics for anomalies
2. Review classification logs in database
3. Generate diagnostic report with `ab.generate_ab_report()`
4. Consult subcategory pattern effectiveness scores