# 4-Category Classification System Design

## Overview
This document outlines the design for upgrading the Atlas Email spam classification system from the current multi-category approach to a streamlined 4-category system that better aligns with real-world spam patterns.

## Current Issues
- Auto warranty emails incorrectly classified as "Adult & Dating Spam" (48 found)
- Too many overlapping categories (13+ consolidated categories)
- High confidence in wrong classifications (80-95% for misclassified emails)
- Category boundaries not well-defined

## New 4-Category System

### 1. Dangerous (Priority: CRITICAL)
**Definition**: Emails that pose immediate security or financial risk
**Subcategories**:
- Phishing attempts
- Malware/virus distribution
- Account compromise attempts
- Fake security alerts
- Cryptocurrency scams
**Key Indicators**:
- Urgent security warnings
- Suspicious links to fake login pages
- Attachment-based threats
- Impersonation of financial institutions

### 2. Commercial Spam (Priority: HIGH)
**Definition**: Unsolicited bulk commercial emails
**Subcategories**:
- Auto warranty & insurance offers
- Health & medical products
- Adult & dating services
- Gambling promotions
- General product marketing
**Key Indicators**:
- Bulk sender patterns
- Marketing language ("save", "discount", "offer")
- Random domain patterns
- Heavy emoji usage

### 3. Scams (Priority: HIGH)
**Definition**: Deceptive emails seeking money or information
**Subcategories**:
- Nigerian prince / advance fee fraud
- Lottery & prize scams
- Work-from-home schemes
- Investment fraud
- Romance scams
**Key Indicators**:
- Too-good-to-be-true offers
- Requests for upfront payment
- Emotional manipulation
- Poor grammar/spelling

### 4. Legitimate Marketing (Priority: MEDIUM)
**Definition**: Marketing from legitimate businesses (may be unwanted)
**Subcategories**:
- Newsletter subscriptions
- Promotional emails from known companies
- Event invitations
- Product updates
- Sales notifications
**Key Indicators**:
- Verified sender domains
- Unsubscribe links
- Professional formatting
- Consistent branding

## Implementation Strategy

### Phase 1: Database Schema Updates
```sql
-- Add new columns to processed_emails_bulletproof
ALTER TABLE processed_emails_bulletproof 
ADD COLUMN category_v2 TEXT,
ADD COLUMN subcategory TEXT,
ADD COLUMN category_confidence_v2 REAL,
ADD COLUMN classification_version INTEGER DEFAULT 1;

-- Create new category mapping table
CREATE TABLE category_mappings (
    old_category TEXT PRIMARY KEY,
    new_category TEXT NOT NULL,
    subcategory TEXT,
    mapping_confidence REAL DEFAULT 1.0
);

-- Create subcategory tracking table
CREATE TABLE subcategory_patterns (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_value TEXT NOT NULL,
    effectiveness REAL DEFAULT 0.5,
    occurrence_count INTEGER DEFAULT 0
);
```

### Phase 2: Classifier Implementation
1. Create `FourCategoryClassifier` class extending the current classifier
2. Implement category-specific feature extraction
3. Add subcategory detection logic
4. Enable confidence scoring for each category

### Phase 3: Training Data Preparation
1. Map existing categories to new 4-category system
2. Review and correct misclassified auto warranty emails
3. Build balanced training set with equal representation
4. Implement cross-validation for accuracy testing

### Phase 4: Parallel Operation
1. Run both classifiers simultaneously
2. Log classification differences
3. Compare accuracy metrics
4. Gradual rollout based on confidence thresholds

## Category Mapping from Current System

| Current Category | New Category | Subcategory |
|-----------------|--------------|-------------|
| Phishing | Dangerous | Phishing attempts |
| Brand Impersonation | Dangerous | Account compromise |
| Payment Scam | Scams | Advance fee fraud |
| Financial & Investment Spam | Commercial Spam | Investment products |
| Adult & Dating Spam | Commercial Spam | Adult & dating services |
| Health & Medical Spam | Commercial Spam | Health & medical products |
| Gambling Spam | Commercial Spam | Gambling promotions |
| Legal & Compensation Scams | Scams | Legal scams |
| Real Estate Spam | Commercial Spam | Real estate offers |
| Promotional Email | Legitimate Marketing | Promotional emails |

## Success Metrics
1. Auto warranty emails correctly classified as Commercial Spam (not Adult)
2. Overall classification accuracy > 95%
3. Dangerous email detection rate > 99%
4. False positive rate < 1% for Legitimate Marketing
5. User feedback incorporation rate > 80%

## Migration Plan
1. Deploy schema changes
2. Run classification mapping script
3. Train new 4-category classifier
4. Enable A/B testing mode
5. Monitor performance for 7 days
6. Full rollout if metrics met
7. Deprecate old classifier

## Risk Mitigation
- Keep old classification data for rollback
- Implement gradual rollout
- Monitor user feedback closely
- Daily accuracy reports
- Automated alerts for accuracy drops

## Timeline
- Week 1: Schema updates and classifier implementation
- Week 2: Training data preparation and model training
- Week 3: A/B testing and monitoring
- Week 4: Full rollout and documentation