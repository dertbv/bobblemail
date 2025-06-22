# Tools Folder

This folder contains diagnostic and performance testing tools for the email filtering system.

## Tool Files

### ML System Diagnostics
- **`verify_ml_enabled.py`** - ML System Enablement Verification
  - Comprehensive verification that ML is enabled and working properly
  - Tests hybrid classifier integration (Random Forest + Naive Bayes + Keywords)
  - Validates ML model loading and prediction functionality
  - Checks ensemble system component availability and connectivity
  - Usage: `python tools/verify_ml_enabled.py`

### Performance Analysis Tools
- **`regex_performance_test.py`** - Regex Performance Testing Framework
  - Performance testing framework for regex pattern optimization
  - Benchmarks keyword matching speed and efficiency
  - Identifies bottlenecks in pattern matching algorithms
  - Provides optimization recommendations for filter performance
  - Usage: `python tools/regex_performance_test.py`

- **`keyword_usage_analyzer.py`** - Keyword Usage Analysis
  - Analyzes which keywords from filter_terms actually appear in processed emails
  - Identifies high-impact vs. low-impact keywords for optimization
  - Generates usage statistics and frequency analysis
  - Helps optimize keyword database by removing unused patterns
  - Connects to `mail_filter.db` for historical email analysis
  - Usage: `python tools/keyword_usage_analyzer.py`

## Usage Guidelines

### System Health Checks
```bash
# Verify ML system is properly configured
python tools/verify_ml_enabled.py

# Analyze keyword effectiveness
python tools/keyword_usage_analyzer.py

# Test regex performance
python tools/regex_performance_test.py
```

### Development Workflow
1. **After ML Changes**: Run `verify_ml_enabled.py` to ensure ensemble still works
2. **Performance Issues**: Use `regex_performance_test.py` to identify bottlenecks
3. **Keyword Optimization**: Use `keyword_usage_analyzer.py` to prune unused keywords

### Prerequisites
- **Database Access**: Tools require connection to `mail_filter.db`
- **ML Models**: Verify trained model files exist (*.pkl, *.json)
- **Dependencies**: Ensure scikit-learn, pandas, numpy are installed
- **System Path**: Run from project root directory for proper imports

## Expected Outputs

### ML Verification
- ✅ **Hybrid Classifier Loaded** - Confirms ensemble system initialization
- ✅ **Model Files Present** - Validates Random Forest and Naive Bayes models
- ✅ **Prediction Test Passed** - Verifies end-to-end classification pipeline
- ⚠️ **Component Warnings** - Identifies any missing or degraded components

### Performance Analysis
- **Regex Timing Results** - Benchmark results for pattern matching speed
- **Keyword Hit Rates** - Frequency analysis of keyword matches in actual emails
- **Optimization Recommendations** - Specific suggestions for performance improvements

### Keyword Analysis
- **Usage Statistics** - Which keywords actually match emails in database
- **Effectiveness Metrics** - Keywords with highest classification impact
- **Pruning Candidates** - Keywords that can be removed without impact loss

**Note**: Tools are designed for development support and system diagnostics. Some tools may require specific system configurations or email data to provide meaningful results.