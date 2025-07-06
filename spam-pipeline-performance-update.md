# Spam Pipeline Performance Update - KISS

## Current Problem
- Processing 164 emails takes 32.8 seconds
- Every spam email gets expensive domain validation (200ms each)
- Validating obvious spam domains like `3em5zstrd8.us`

## Simple Fix
Change the order of checks to fail fast:

```python
# OLD (slow):
1. Check all emails with domain validation first

# NEW (fast):
1. ML says 95%+ spam? → Delete (5ms)
2. Domain is gibberish? → Delete (1ms)  
3. Failed auth? → Delete (10ms)
4. Only uncertain? → Domain validate (200ms)
```

## Code Changes Needed

### 1. Move gibberish check earlier
```python
# In email_processor.py, line ~1050
if ml_spam_confidence > 0.90:
    # Check gibberish BEFORE domain validation
    if is_gibberish_domain(sender_domain):
        return delete_spam("gibberish domain")
```

### 2. Skip domain validation for obvious spam
```python
# In email_processor.py, line ~1068
if ml_spam_confidence > 0.90:
    # Skip expensive domain validation
    return delete_spam("high ML confidence")
    
# Only validate uncertain emails
if 0.40 < ml_spam_confidence < 0.70:
    domain_result = validate_domain(sender)
```

### 3. Add simple metrics
```python
# Track what's happening
self.skip_counts = {
    'ml_skip': 0,
    'gibberish_skip': 0,
    'domain_checked': 0
}
```

## Expected Results
- 150 emails: Skip domain check (ML/gibberish catches them)
- 14 emails: Need domain check (uncertain cases)
- **Time: 32.8s → 4.3s (87% faster)**

## Test It
```bash
# Before changes
python3 atlas_cli.py preview 200

# After changes  
python3 atlas_cli.py preview 200
# Should be MUCH faster
```

## Rollback
If something breaks, just revert email_processor.py:
```bash
git checkout -- src/atlas_email/core/email_processor.py
```

That's it. Simple reordering, huge performance gain.