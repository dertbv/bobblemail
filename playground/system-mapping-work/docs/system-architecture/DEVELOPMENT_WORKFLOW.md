# ATLAS EMAIL DEVELOPMENT WORKFLOW

## EXECUTIVE SUMMARY

This guide provides comprehensive development workflows for extending Atlas_Email functionality, including feature development, testing procedures, deployment processes, and code quality standards. Designed for both core contributors and external developers.

**DEVELOPMENT CHARACTERISTICS**:
- **Test-Driven Development**: Comprehensive testing at unit, integration, and system levels
- **Modular Architecture**: Clean separation enabling independent feature development
- **Git Workflow**: Feature branches with code review and CI/CD integration
- **Documentation-First**: All changes require corresponding documentation updates
- **Performance-Aware**: Performance impact assessment for all changes

## DEVELOPMENT ENVIRONMENT SETUP

### Prerequisites and Dependencies
```bash
# System requirements
Python 3.8+
Git 2.20+
SQLite 3.30+

# Development tools
pip install pytest black flake8 mypy
pip install pre-commit commitizen

# Optional but recommended
pip install jupyter notebook  # For data analysis
pip install memory-profiler   # For performance analysis
```

### Environment Configuration
```bash
# 1. Clone repository
git clone https://github.com/your-org/atlas_email.git
cd atlas_email

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Setup development database
cp data/mail_filter.db data/mail_filter_dev.db
export ATLAS_DB_PATH="data/mail_filter_dev.db"

# 5. Initialize development configuration
cp config/settings.py.example config/settings.py
cp config/credentials.py.example config/credentials.py

# 6. Setup pre-commit hooks
pre-commit install
```

### IDE Configuration
```python
# .vscode/settings.json (Visual Studio Code)
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}

# .vscode/launch.json (Debugging configuration)
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Atlas Email API",
            "type": "python",
            "request": "launch",
            "program": "src/atlas_email/api/app.py",
            "console": "integratedTerminal",
            "env": {
                "ATLAS_DEBUG": "true",
                "ATLAS_DB_PATH": "data/mail_filter_dev.db"
            }
        }
    ]
}
```

## FEATURE DEVELOPMENT WORKFLOW

### 1. Planning and Design Phase

#### Feature Request Analysis
```markdown
# Feature Request Template
## Feature Description
Brief description of the requested feature

## Business Justification
Why this feature is needed and expected impact

## Technical Requirements
- Functional requirements
- Non-functional requirements (performance, security, etc.)
- Integration requirements

## Implementation Approach
High-level technical approach and architecture changes

## Testing Strategy
Unit tests, integration tests, and validation procedures

## Documentation Updates
Required documentation changes and user guides
```

#### Architecture Impact Assessment
```python
# Impact assessment checklist
impact_areas = {
    "database_schema": False,     # New tables or columns?
    "api_endpoints": False,       # New or modified endpoints?
    "ml_pipeline": False,         # Changes to classification logic?
    "geographic_intel": False,    # Geographic processing changes?
    "web_interface": False,       # UI/UX modifications?
    "configuration": False,       # New configuration options?
    "dependencies": False,        # New external libraries?
    "performance": "neutral"      # positive/negative/neutral impact
}
```

### 2. Development Phase

#### Branch Strategy
```bash
# Feature branch workflow
git checkout main
git pull origin main
git checkout -b feature/new-spam-category-detection

# Work on feature with frequent commits
git add -A
git commit -m "feat: add new spam category detection logic"

# Push feature branch
git push -u origin feature/new-spam-category-detection
```

#### Code Development Standards
```python
# File structure for new features
src/atlas_email/
├── core/
│   └── new_feature.py          # Core business logic
├── api/
│   └── new_feature_routes.py   # API endpoints (if needed)
├── ml/
│   └── new_feature_ml.py       # ML components (if needed)
├── tests/
│   ├── unit/
│   │   └── test_new_feature.py # Unit tests
│   └── integration/
│       └── test_new_feature_integration.py
└── docs/
    └── features/
        └── new_feature.md      # Feature documentation
```

#### Code Quality Standards
```python
# Example: Adding new spam detection feature
"""
New Feature: Advanced Phishing Detection
========================================

PURPOSE: Detect sophisticated phishing attempts using behavioral analysis
INPUT: Email metadata and headers
OUTPUT: Phishing probability score (0.0-1.0)
DEPENDENCIES: existing ML pipeline, geographic intelligence
SIDE_EFFECTS: Updates phishing_patterns table
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from atlas_email.core.spam_classifier import BaseClassifier
from atlas_email.models.database import db

@dataclass
class PhishingAnalysisResult:
    """Container for phishing analysis results"""
    phishing_probability: float
    confidence: float
    detection_indicators: List[str]
    risk_level: str

class AdvancedPhishingDetector(BaseClassifier):
    """
    Advanced phishing detection using behavioral analysis.
    
    Analyzes email patterns, sender behavior, and content sophistication
    to identify phishing attempts beyond traditional keyword matching.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize phishing detector with configuration."""
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
    def analyze_email(self, email_data: Dict) -> PhishingAnalysisResult:
        """
        Analyze email for phishing indicators.
        
        Args:
            email_data: Dictionary containing sender, subject, headers
            
        Returns:
            PhishingAnalysisResult with probability and indicators
            
        Raises:
            ValueError: If email_data is invalid
        """
        if not self._validate_email_data(email_data):
            raise ValueError("Invalid email data provided")
            
        try:
            # Behavioral analysis
            behavioral_score = self._analyze_sender_behavior(email_data)
            
            # Content sophistication analysis
            content_score = self._analyze_content_sophistication(email_data)
            
            # URL and link analysis
            link_score = self._analyze_links(email_data)
            
            # Aggregate scores
            final_probability = self._calculate_final_score(
                behavioral_score, content_score, link_score
            )
            
            return PhishingAnalysisResult(
                phishing_probability=final_probability,
                confidence=self._calculate_confidence(final_probability),
                detection_indicators=self._get_detection_indicators(),
                risk_level=self._determine_risk_level(final_probability)
            )
            
        except Exception as e:
            self.logger.error(f"Phishing analysis failed: {e}")
            return self._get_fallback_result()
```

### 3. Testing Workflow

#### Unit Testing
```python
# tests/unit/test_advanced_phishing_detector.py
import pytest
from unittest.mock import Mock, patch

from atlas_email.core.advanced_phishing_detector import AdvancedPhishingDetector

class TestAdvancedPhishingDetector:
    """Test suite for AdvancedPhishingDetector"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = AdvancedPhishingDetector()
        self.sample_email = {
            'sender': 'test@example.com',
            'subject': 'Test Email',
            'headers': 'Received: from test.com [192.0.2.1]'
        }
    
    def test_analyze_email_valid_input(self):
        """Test analysis with valid email data"""
        result = self.detector.analyze_email(self.sample_email)
        
        assert isinstance(result.phishing_probability, float)
        assert 0.0 <= result.phishing_probability <= 1.0
        assert isinstance(result.detection_indicators, list)
    
    def test_analyze_email_invalid_input(self):
        """Test analysis with invalid email data"""
        with pytest.raises(ValueError):
            self.detector.analyze_email({})
    
    @patch('atlas_email.core.advanced_phishing_detector.db')
    def test_database_interaction(self, mock_db):
        """Test database queries during analysis"""
        mock_db.execute_query.return_value = [{'count': 5}]
        
        result = self.detector.analyze_email(self.sample_email)
        
        mock_db.execute_query.assert_called()
        assert result is not None
```

#### Integration Testing
```python
# tests/integration/test_phishing_detector_integration.py
import pytest
from atlas_email.core.advanced_phishing_detector import AdvancedPhishingDetector
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier
from atlas_email.models.database import db

class TestPhishingDetectorIntegration:
    """Integration tests for phishing detector with ML pipeline"""
    
    def setup_method(self):
        """Setup integration test environment"""
        # Use test database
        db.switch_to_test_database()
        self.detector = AdvancedPhishingDetector()
        self.ensemble = EnsembleHybridClassifier()
    
    def test_integration_with_ensemble_classifier(self):
        """Test phishing detector integration with ensemble classifier"""
        email_data = {
            'sender': 'phishing@suspicious.com',
            'subject': 'Urgent: Verify your account now!',
            'headers': 'Received: from suspicious.com [203.0.113.1]'
        }
        
        # Test phishing detection
        phishing_result = self.detector.analyze_email(email_data)
        
        # Test ensemble classification
        ensemble_result = self.ensemble.classify_email(
            sender=email_data['sender'],
            subject=email_data['subject'],
            headers=email_data['headers']
        )
        
        # Verify integration
        assert phishing_result.phishing_probability > 0.5
        assert ensemble_result['category'] == 'Phishing'
        assert ensemble_result['confidence'] > 0.7
```

#### Performance Testing
```python
# tests/performance/test_phishing_detector_performance.py
import time
import pytest
from memory_profiler import profile

from atlas_email.core.advanced_phishing_detector import AdvancedPhishingDetector

class TestPhishingDetectorPerformance:
    """Performance tests for phishing detector"""
    
    def test_analysis_speed(self):
        """Test that analysis completes within acceptable time"""
        detector = AdvancedPhishingDetector()
        email_data = self._generate_test_email()
        
        start_time = time.time()
        result = detector.analyze_email(email_data)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        assert analysis_time < 0.1  # Should complete in under 100ms
    
    @profile
    def test_memory_usage(self):
        """Test memory usage during analysis"""
        detector = AdvancedPhishingDetector()
        
        # Process multiple emails to test memory accumulation
        for i in range(100):
            email_data = self._generate_test_email(i)
            result = detector.analyze_email(email_data)
        
        # Memory profiler will show memory usage patterns
```

### 4. Database Migration Workflow

#### Schema Changes
```python
# migrations/add_phishing_patterns_table.py
"""
Migration: Add phishing_patterns table
Version: 6
Date: 2025-07-03
"""

def upgrade():
    """Apply migration"""
    return """
    CREATE TABLE phishing_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_type VARCHAR(50) NOT NULL,
        pattern_value TEXT NOT NULL,
        detection_count INTEGER DEFAULT 0,
        success_rate FLOAT DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    CREATE INDEX idx_phishing_patterns_type ON phishing_patterns(pattern_type);
    CREATE INDEX idx_phishing_patterns_active ON phishing_patterns(is_active);
    
    INSERT INTO schema_version (version) VALUES (6);
    """

def downgrade():
    """Rollback migration"""
    return """
    DROP TABLE IF EXISTS phishing_patterns;
    DELETE FROM schema_version WHERE version = 6;
    """
```

#### Migration Execution
```bash
# Run migration
python3 migrations/migrate.py --upgrade

# Rollback if needed
python3 migrations/migrate.py --downgrade --version 5

# Check current schema version
python3 -c "from atlas_email.models.database import db; print('Schema version:', db.get_schema_version())"
```

### 5. API Development Workflow

#### New Endpoint Development
```python
# src/atlas_email/api/phishing_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from atlas_email.core.advanced_phishing_detector import AdvancedPhishingDetector

router = APIRouter(prefix="/api/phishing", tags=["phishing"])

class PhishingAnalysisRequest(BaseModel):
    sender: str
    subject: str
    headers: Optional[str] = ""

class PhishingAnalysisResponse(BaseModel):
    phishing_probability: float
    confidence: float
    risk_level: str
    detection_indicators: list

@router.post("/analyze", response_model=PhishingAnalysisResponse)
async def analyze_phishing(request: PhishingAnalysisRequest):
    """Analyze email for phishing indicators"""
    try:
        detector = AdvancedPhishingDetector()
        
        result = detector.analyze_email({
            'sender': request.sender,
            'subject': request.subject,
            'headers': request.headers
        })
        
        return PhishingAnalysisResponse(
            phishing_probability=result.phishing_probability,
            confidence=result.confidence,
            risk_level=result.risk_level,
            detection_indicators=result.detection_indicators
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### API Testing
```python
# tests/api/test_phishing_api.py
from fastapi.testclient import TestClient
from atlas_email.api.app import app

client = TestClient(app)

def test_phishing_analysis_endpoint():
    """Test phishing analysis API endpoint"""
    response = client.post("/api/phishing/analyze", json={
        "sender": "test@suspicious.com",
        "subject": "Urgent: Click here now!",
        "headers": "Received: from suspicious.com"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "phishing_probability" in data
    assert 0.0 <= data["phishing_probability"] <= 1.0
```

## CODE QUALITY AND REVIEW PROCESS

### Pre-commit Checks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
  
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/unit/
        language: system
        types: [python]
        pass_filenames: false
```

### Code Review Checklist
```markdown
## Code Review Checklist

### Functionality
- [ ] Feature works as specified
- [ ] Edge cases handled appropriately
- [ ] Error handling is comprehensive
- [ ] Performance impact is acceptable

### Code Quality
- [ ] Code follows project style guidelines
- [ ] Functions and classes are well-documented
- [ ] Variable and function names are descriptive
- [ ] Code is DRY (Don't Repeat Yourself)

### Testing
- [ ] Unit tests cover new functionality
- [ ] Integration tests pass
- [ ] Performance tests (if applicable)
- [ ] Test coverage is adequate (>80%)

### Security
- [ ] No sensitive data in code
- [ ] Input validation is present
- [ ] SQL injection prevention
- [ ] No hardcoded credentials

### Documentation
- [ ] Code documentation updated
- [ ] API documentation updated (if applicable)
- [ ] User documentation updated (if applicable)
- [ ] README updated (if applicable)

### Database
- [ ] Schema changes include migrations
- [ ] Backward compatibility considered
- [ ] Index performance impact assessed
- [ ] Data migration tested
```

## DEPLOYMENT WORKFLOW

### Development Deployment
```bash
# Local development server
cd src/atlas_email/api
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Development with debugging
ATLAS_DEBUG=true ATLAS_LOG_LEVEL=DEBUG uvicorn app:app --reload
```

### Staging Deployment
```bash
# Staging environment setup
export ATLAS_ENVIRONMENT="staging"
export ATLAS_DB_PATH="data/staging_mail_filter.db"
export ATLAS_LOG_LEVEL="INFO"

# Database migration
python3 migrations/migrate.py --upgrade

# Run comprehensive tests
pytest tests/ --cov=atlas_email --cov-report=html

# Deploy to staging
docker build -t atlas_email:staging .
docker run -p 8000:8000 atlas_email:staging
```

### Production Deployment
```bash
# Production checklist
# 1. All tests pass
pytest tests/

# 2. Security scan
bandit -r src/atlas_email/

# 3. Performance benchmark
python3 tests/performance/benchmark.py

# 4. Database backup
cp data/mail_filter.db data/backup/mail_filter_$(date +%Y%m%d).db

# 5. Deploy with zero downtime
./scripts/deploy_production.sh
```

## CONTINUOUS INTEGRATION

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=atlas_email --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Security check
      run: bandit -r src/atlas_email/
    
    - name: Type checking
      run: mypy src/atlas_email/
```

## PERFORMANCE MONITORING

### Performance Benchmarking
```python
# scripts/performance_benchmark.py
import time
import statistics
from atlas_email.ml.ensemble_classifier import EnsembleHybridClassifier

def benchmark_classification():
    """Benchmark email classification performance"""
    classifier = EnsembleHybridClassifier()
    
    # Test data
    test_emails = [
        {
            'sender': 'spam@example.com',
            'subject': 'Buy now! Limited time offer!',
            'headers': 'Received: from spam.com'
        }
        # ... more test emails
    ]
    
    times = []
    for email in test_emails:
        start_time = time.time()
        result = classifier.classify_email(**email)
        end_time = time.time()
        times.append(end_time - start_time)
    
    print(f"Average classification time: {statistics.mean(times):.3f}s")
    print(f"95th percentile: {statistics.quantiles(times, n=20)[18]:.3f}s")
    print(f"Max classification time: {max(times):.3f}s")

if __name__ == "__main__":
    benchmark_classification()
```

This development workflow ensures consistent, high-quality code delivery with comprehensive testing, security validation, and performance monitoring.

---
*Development Workflow Guide - Version 1.0*  
*Generated: 2025-07-03*  
*Status: Production Ready*