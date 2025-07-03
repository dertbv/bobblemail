# ATLAS EMAIL SYSTEM ARCHITECTURE MAPPING MISSION

You are an autonomous System Architecture Analyst with full permissions to investigate and document the complete Atlas_Email system.

## CRITICAL CONTEXT
**THE MYSTERY**: Geographic intelligence is working (analytics page shows country data with risk scores) but we cannot find where it's implemented in the pipeline!

Your mission is to create a complete architectural map of how Atlas_Email works.

## YOUR COMPREHENSIVE MISSION

### 1. DATABASE ARCHITECTURE MAPPING
```python
# Create: SYSTEM_ARCHITECTURE_REPORT.md
# Document ALL database tables, schemas, relationships
```

**Tasks**:
- Map all 30+ database tables and their purposes
- Document table schemas (columns, types, relationships)
- Find where geographic data might be stored
- Identify data flow between tables
- Document any hidden or non-obvious data storage

### 2. CLASSIFICATION PIPELINE ANALYSIS
```python
# Create: CLASSIFICATION_PIPELINE_MAP.md
# Trace email processing from input to output
```

**Tasks**:
- Map the complete email classification flow
- Find every function that processes emails
- Identify where geographic analysis happens
- Document the ML pipeline components
- Trace how emails flow through the system

### 3. API ENDPOINT INVENTORY
```python
# Create: API_ENDPOINTS_REFERENCE.md
# Document all web routes and API endpoints
```

**Tasks**:
- List all Flask/FastAPI routes
- Document what each endpoint does
- Find the analytics endpoint that serves geographic data
- Map API data sources and responses
- Identify any hidden or undocumented endpoints

### 4. GEOGRAPHIC INTELLIGENCE INVESTIGATION
```python
# Create: GEOGRAPHIC_INTELLIGENCE_INVESTIGATION.md
# SOLVE THE MYSTERY of how geo data works
```

**CRITICAL TASKS**:
- Find where `geographic_intelligence.py` is imported
- Trace how country detection happens
- Locate where risk scores are calculated
- Find the data source for the analytics page
- Document the complete geo intelligence workflow

### 5. DATA FLOW MAPPING
```python
# Create: DATA_FLOW_DIAGRAM.md
# Show how data moves through the entire system
```

**Tasks**:
- Email ingestion → Processing → Storage → Display
- ML model training and prediction flow
- Geographic data collection and analysis
- User feedback and learning loops
- Performance metrics and logging

### 6. MODULE DEPENDENCY ANALYSIS
```python
# Create: MODULE_DEPENDENCIES.md
# Map how all Python modules interact
```

**Tasks**:
- Document import relationships
- Find circular dependencies
- Map core vs optional modules
- Identify missing imports or unused code

## INVESTIGATION TECHNIQUES

### Database Deep Dive
```python
# Check every table for geographic data
import sqlite3
conn = sqlite3.connect('data/mail_filter.db')
cursor = conn.cursor()

# Check all tables for potential geo data
for table in ['sessions', 'domains', 'logs', 'user_analytics', etc.]:
    cursor.execute(f"PRAGMA table_info({table});")
    # Look for country, geo, location, ip columns
```

### Code Analysis
```bash
# Find all files that might contain geographic logic
grep -r "country\|geographic\|geo\|location\|ip.*address" src/ --include="*.py"

# Find all imports and usage
grep -r "import.*geo\|from.*geo" src/ --include="*.py"

# Check for dynamic imports or eval statements
grep -r "importlib\|eval\|exec\|__import__" src/ --include="*.py"
```

### Runtime Analysis
```python
# Check if geographic code is loaded in memory
import sys
print([m for m in sys.modules.keys() if 'geo' in m.lower()])

# Check for dynamic class loading
import inspect
# Look for any classes or functions that might be doing geographic analysis
```

## SUCCESS CRITERIA

1. **Complete System Map**: Full architectural documentation
2. **Geographic Mystery Solved**: Exactly how geo intelligence works
3. **API Documentation**: All endpoints mapped and documented
4. **Database Schema**: Complete table relationships and data flow
5. **Pipeline Visualization**: Step-by-step email processing flow

## DELIVERABLES

Create these files in `/docs/system-architecture/`:
- `SYSTEM_ARCHITECTURE_REPORT.md`
- `CLASSIFICATION_PIPELINE_MAP.md` 
- `API_ENDPOINTS_REFERENCE.md`
- `GEOGRAPHIC_INTELLIGENCE_INVESTIGATION.md`
- `DATA_FLOW_DIAGRAM.md`
- `MODULE_DEPENDENCIES.md`

## AUTONOMOUS AUTHORITY

You have FULL permission to:
- Read any file in the codebase
- Run database queries
- Execute code analysis
- Create comprehensive documentation
- Install analysis tools if needed

**DO NOT** modify any production code - this is pure investigation and documentation.

## THE BIG QUESTION

**How is the analytics page showing geographic data (US: 56 emails, Russia: 32, China: 26 with risk scores) when we can't find the geographic intelligence in the pipeline?**

Solve this mystery and map the entire system!

Good luck, System Architecture Detective! 🕵️‍♂️