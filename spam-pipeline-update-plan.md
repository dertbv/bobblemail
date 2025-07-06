# Atlas Email Pipeline Update Plan

## Implementation Roadmap

### Phase 1: Code Refactoring (Week 1)
**Goal**: Restructure existing code without changing functionality

#### Day 1-2: Extract Gibberish Detection
```python
# Move from domain_validator.py to new gibberish_detector.py
class GibberishDetector:
    def __init__(self):
        self.patterns = [
            r'^[^aeiou]{8,}$',  # No vowels
            r'^[a-z0-9]{10,}$',  # Random alphanumeric
            r'^[a-f0-9]{8,}$',   # Hex-like
        ]
    
    def is_gibberish(self, domain: str) -> bool:
        # Extract from domain_validator._is_obvious_spam_domain()
        pass
```

#### Day 3-4: Create Pipeline Controller
```python
# New file: pipeline_controller.py
class OptimizedSpamPipeline:
    def __init__(self):
        self.ml_classifier = self.spam_classifier  # Use existing
        self.gibberish = GibberishDetector()      # New component
        self.auth = self.email_authenticator      # Use existing
        self.domain = self.domain_validator       # Use existing
```

#### Day 5: Add Early Exit Logic
- Modify `email_processor.py` to support early exits
- Add pipeline stage tracking
- Implement cost tracking per stage

### Phase 2: Monitoring Setup (Week 2)
**Goal**: Add metrics before changing behavior

#### Day 1-2: Implement Metrics Collection
```python
# Add to email_processor.py
self.metrics = {
    'ml_exits': 0,
    'gibberish_exits': 0,
    'auth_exits': 0,
    'domain_validations': 0,
    'total_processed': 0,
    'total_cost': 0.0
}
```

#### Day 3-4: Create Dashboard Endpoints
```python
# Add to app.py
@app.route('/api/pipeline-metrics')
def pipeline_metrics():
    return jsonify({
        'stage_distribution': processor.metrics,
        'cost_per_email': processor.metrics['total_cost'] / processor.metrics['total_processed'],
        'domain_validation_rate': processor.metrics['domain_validations'] / processor.metrics['total_processed']
    })
```

#### Day 5: Deploy Monitoring Dashboard
- Add real-time metrics display
- Set up alerting thresholds
- Create baseline measurements

### Phase 3: A/B Testing Implementation (Week 3)
**Goal**: Safely test optimized pipeline

#### Day 1-2: Implement Feature Flag
```python
# Add to email_processor.py
def should_use_optimized_pipeline(self, email):
    # Start with 5% of traffic
    return hash(email.uid) % 100 < 5
```

#### Day 2-3: Parallel Pipeline Execution
```python
if self.should_use_optimized_pipeline(email):
    result = self.process_email_optimized(email)
    result['pipeline'] = 'optimized'
else:
    result = self.process_email_legacy(email)
    result['pipeline'] = 'legacy'
```

#### Day 4-5: Result Comparison
- Log both pipeline results
- Compare accuracy metrics
- Monitor performance differences

### Phase 4: Gradual Rollout (Week 4)
**Goal**: Increase traffic to optimized pipeline

#### Rollout Schedule
- **Monday**: Increase to 10% (if metrics good)
- **Tuesday**: Increase to 25%
- **Wednesday**: Increase to 50%
- **Thursday**: Increase to 75%
- **Friday**: Full deployment to 100%

#### Rollback Triggers
```python
# Automatic rollback if:
if (error_rate > 0.02 or 
    false_positive_rate > 0.005 or
    avg_processing_time > 200):
    self.feature_flag = 0  # Disable optimized pipeline
    self.alert_team("Pipeline rollback triggered")
```

## File Changes Required

### 1. New Files to Create
- `src/atlas_email/core/gibberish_detector.py`
- `src/atlas_email/core/pipeline_metrics.py`
- `src/atlas_email/core/optimized_pipeline.py`
- `tests/test_optimized_pipeline.py`

### 2. Files to Modify
- `src/atlas_email/core/email_processor.py` - Add pipeline selection
- `src/atlas_email/utils/domain_validator.py` - Remove gibberish logic
- `src/atlas_email/api/app.py` - Add metrics endpoints
- `config/settings.py` - Add feature flags

### 3. Configuration Updates
```python
# config/settings.py
PIPELINE_OPTIMIZATION = {
    'enabled': False,  # Start disabled
    'percentage': 0,   # Start with 0%
    'ml_threshold': 0.95,
    'gibberish_patterns': [...],
    'cost_tracking': True
}
```

## Testing Strategy

### Unit Tests
```python
# tests/test_gibberish_detector.py
def test_gibberish_detection():
    detector = GibberishDetector()
    assert detector.is_gibberish("3em5zstrd8.us") == True
    assert detector.is_gibberish("gmail.com") == False
```

### Integration Tests
```python
# tests/test_pipeline_integration.py
def test_early_exit_ml_high_confidence():
    email = create_spam_email()
    result = pipeline.process_email(email)
    assert result.stage == "ml_classification"
    assert result.cost_usd == 0.001  # Only ML cost
```

### Load Tests
```bash
# Run load test with both pipelines
python tools/benchmark_performance.py --pipeline=both --emails=10000
```

## Success Criteria

### Week 1 Success
- [ ] All code refactored with no behavior changes
- [ ] All existing tests still pass
- [ ] Metrics collection working

### Week 2 Success
- [ ] Dashboard showing real-time metrics
- [ ] Baseline performance documented
- [ ] A/B test framework ready

### Week 3 Success
- [ ] 5% traffic on optimized pipeline
- [ ] No increase in error rates
- [ ] Cost reduction visible in metrics

### Week 4 Success
- [ ] 100% traffic on optimized pipeline
- [ ] 75% cost reduction achieved
- [ ] 99.2% accuracy maintained

## Rollback Plan

If issues arise:
1. Set feature flag to 0% immediately
2. Review metrics to identify issue
3. Fix and test in staging
4. Resume rollout at 5%

## Communication Plan

### Stakeholder Updates
- **Daily**: Slack update with metrics
- **Weekly**: Email report with progress
- **Issues**: Immediate notification

### Team Coordination
- **Morning**: Review overnight metrics
- **Afternoon**: Decide on traffic percentage
- **Evening**: Deploy configuration changes

---

This plan provides a safe, measured approach to implementing the optimized pipeline with clear success metrics and rollback procedures.