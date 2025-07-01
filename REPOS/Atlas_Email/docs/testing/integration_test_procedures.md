# Atlas_Email Integration Testing Procedures

## Quick System Health Check

```bash
# Basic component test
python3 -c "
import sys
sys.path.insert(0, 'src')
from atlas_email.models.database import db
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
print('✅ Core systems operational')
"
```

## Template System Validation

```bash
# Check template extraction completeness
ls -la src/atlas_email/api/templates/pages/
# Expected: 7 template files

# Verify template inheritance
grep -r "{% extends" src/atlas_email/api/templates/pages/
```

## Security Testing

```bash
# XSS protection verification
grep -r "escapeHtml\|X-XSS-Protection\|X-Frame-Options" src/atlas_email/api/
```

## Performance Testing

```bash
# Check app.py size reduction
wc -l src/atlas_email/api/app.py
# Current: ~4,603 lines (33.8% reduction from template extraction)

# Asset organization check
find src/atlas_email/api/static -name "*.css" -o -name "*.js"
```

## Mobile Responsiveness Check

```bash
# Verify responsive CSS patterns
grep -r "@media\|viewport\|responsive" src/atlas_email/api/static/css/
```

## ML System Status

```bash
# Check ML classifier status
python3 -c "
import sys
sys.path.insert(0, 'src')
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
classifier = EnsembleHybridClassifier()
print(f'Keyword Processor: {\"Active\" if hasattr(classifier, \"keyword_processor\") else \"Inactive\"}')
print(f'Total Classifications: {classifier.total_classifications}')
"
```

## Web Server Testing

```bash
# Start development server
PYTHONPATH=src python3 -m uvicorn atlas_email.api.app:app --host 0.0.0.0 --port 8001 --reload

# Quick connectivity test
curl http://localhost:8001/health || echo "Health check endpoint needed"
```

## Database Connectivity

```bash
# Test database access
python3 -c "
import sys
sys.path.insert(0, 'src')
from atlas_email.models.database import db
result = db.execute('SELECT COUNT(*) FROM emails').fetchone()
print(f'Database operational: {result[0]} emails')
"
```

## Integration Test Suite Commands

```bash
# Full component test
python3 -c "
import sys, os
sys.path.insert(0, 'src')

print('🔬 INTEGRATION TEST SUITE')
print('=' * 40)

# Test all major components
components = [
    ('Database', 'atlas_email.models.database', 'db'),
    ('ML Classifier', 'atlas_email.ml.ensemble_classifier', 'EnsembleHybridClassifier'),
    ('Domain Validator', 'atlas_email.utils.domain_validator', 'DomainValidator')
]

for name, module, class_name in components:
    try:
        mod = __import__(module, fromlist=[class_name])
        cls = getattr(mod, class_name)
        if class_name == 'db':
            result = cls.execute('SELECT 1').fetchone()
            print(f'✅ {name}: Operational')
        else:
            instance = cls()
            print(f'✅ {name}: Initialized')
    except Exception as e:
        print(f'❌ {name}: {str(e)[:50]}...')

# Check template system
template_dir = 'src/atlas_email/api/templates/pages'
if os.path.exists(template_dir):
    templates = len(os.listdir(template_dir))
    print(f'✅ Templates: {templates} files')
else:
    print('❌ Templates: Directory not found')

print('=' * 40)
"
```

## Troubleshooting Common Issues

### Numpy Architecture Issues
```bash
# Check architecture
python3 -c "import platform; print(f'Architecture: {platform.machine()}')"

# Reinstall numpy for correct architecture
pip3 uninstall numpy -y && pip3 install numpy
```

### Port Conflicts
```bash
# Kill processes on port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
```

### Import Path Issues
```bash
# Set correct Python path
export PYTHONPATH=/Users/Badman/Desktop/email/REPOS/Atlas_Email/src:$PYTHONPATH
```

## Automated Testing Script

```bash
#!/bin/bash
# integration_test.sh

echo "🔬 Atlas_Email Integration Test Suite"
echo "====================================="

# Set Python path
export PYTHONPATH=src:$PYTHONPATH

# Test 1: Core Components
echo "Testing core components..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from atlas_email.models.database import db
    from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
    print('✅ Core imports successful')
except Exception as e:
    print(f'❌ Core imports failed: {e}')
"

# Test 2: Template System
echo "Testing template system..."
template_count=$(ls src/atlas_email/api/templates/pages/ 2>/dev/null | wc -l)
if [ $template_count -gt 5 ]; then
    echo "✅ Template system: $template_count templates found"
else
    echo "❌ Template system: Insufficient templates"
fi

# Test 3: Security Features
echo "Testing security features..."
if grep -q "escapeHtml" src/atlas_email/api/static/js/common.js 2>/dev/null; then
    echo "✅ XSS protection: escapeHtml function found"
else
    echo "❌ XSS protection: escapeHtml function missing"
fi

# Test 4: Mobile Responsiveness
echo "Testing mobile responsiveness..."
if grep -q "@media" src/atlas_email/api/static/css/common.css 2>/dev/null; then
    echo "✅ Mobile responsive: Media queries found"
else
    echo "❌ Mobile responsive: No media queries"
fi

echo "====================================="
echo "Integration test complete"
```

## Test Result Validation

Expected results for a healthy system:
- ✅ 7+ template files in pages directory
- ✅ XSS protection headers in base.html
- ✅ escapeHtml function in common.js
- ✅ 5+ CSS files in organized structure
- ✅ Database connectivity with email count
- ✅ ML classifier initialization (even with degraded ensemble)
- ✅ Mobile responsive patterns in CSS

Any deviation from these results indicates integration issues requiring investigation.