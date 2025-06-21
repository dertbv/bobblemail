# Tests Folder

This folder contains development and integration test scripts for the email filtering system.

## Test Files

### ML Classification Tests
- **`test_ml_category_system.py`** - Comprehensive ML ensemble classification testing
  - Tests multi-class category classifier functionality
  - Validates ensemble hybrid classifier performance
  - Uses reliable action data (DELETED/PRESERVED) as ground truth
  - Covers Random Forest + Naive Bayes + Keyword ensemble integration

- **`test_random_forest_integration.py`** - Random Forest classifier integration testing
  - Validates Random Forest model performance in ensemble
  - Tests feature extraction and classification accuracy
  - Verifies integration with keyword and Naive Bayes components

### System Integration Tests
- **`test_complete_vendor_integration.py`** - Comprehensive vendor filtering integration
  - Tests selective vendor filtering with spam classification system
  - Validates keyword processor integration with vendor patterns
  - Covers full email processing pipeline with vendor-specific rules

- **`test_domain_validation.py`** - Domain validation system testing
  - Tests two-factor email validation (business prefix + domain legitimacy)
  - Validates WHOIS-based domain analysis and risk scoring
  - Covers domain caching and performance optimization

- **`test_user_keyword_priority.py`** - User keyword priority functionality
  - Tests custom keyword management and priority handling
  - Validates user-defined vs built-in keyword precedence
  - Covers keyword conflict resolution and category assignment

## Usage

### Running Tests
```bash
# Run individual tests
python tests/test_ml_category_system.py
python tests/test_domain_validation.py

# Run from project root
python -m tests.test_complete_vendor_integration
```

### Test Requirements
- Tests require active database connection to `mail_filter.db`
- Some tests use actual email data for realistic validation
- ML tests require trained model files (*.pkl, *.json)
- Domain validation tests may require internet connectivity for WHOIS lookups

### Test Philosophy
- **Integration over Unit**: Focus on end-to-end email processing validation
- **Real Data Testing**: Use actual email samples for classification accuracy
- **Regression Detection**: Monitor classification performance across system changes
- **Component Interaction**: Validate proper integration between ML, keyword, and domain systems

## Expected Outcomes
- **95.6%+ Classification Accuracy** - ML ensemble system performance baseline
- **Zero False Positives** - No legitimate business emails misclassified as spam
- **Proper Ensemble Weighting** - Random Forest 40%, Naive Bayes 30%, Keywords 30%
- **Alternative Ranking Validation** - 5-8 ranked alternatives generated for failed classifications

**Note**: Test scripts are designed for development validation and may require specific database states or email samples to run properly.