# Orchestrator Coordination Plan

## Context Analysis
- **Problem Scope**: Atlas_Email regression affecting geographic intelligence and timestamps
- **Evidence**: 494 older emails have geo data, recent emails don't (clear regression point)
- **Change Vector**: Template agent reduced app.py from 5,604 to 2,743 lines
- **Working Components**: Email processing, classification, server removal
- **Broken Components**: IP/Country detection, timestamp accuracy

## Specialist Task Assignment
Larry (Specialist) will conduct comprehensive technical analysis focusing on:

### Primary Investigation Areas
1. **Geographic Intelligence Pipeline Analysis**
   - Locate IP extraction and geolocation logic in codebase
   - Identify where app.py modifications may have broken the pipeline
   - Compare working vs broken email records for pattern analysis

2. **Timestamp Processing Examination** 
   - Trace timestamp handling from email ingestion to database storage
   - Identify why dates are defaulting to June 30th instead of current dates
   - Check timezone handling and date parsing logic

3. **Template Agent Impact Assessment**
   - Review specific changes made during app.py reduction (5,604→2,743 lines)
   - Identify removed code sections that may have contained geo/timestamp logic
   - Map removed functionality to current broken features

4. **Root Cause Determination**
   - Pinpoint exact code changes causing each regression
   - Provide specific file paths and line numbers where issues occur
   - Document evidence supporting each root cause finding

## Success Criteria for Larry
- Deliver complete technical analysis with specific code locations
- Provide actionable technical solutions for both issues
- Include prevention strategy recommendations
- Tag complex reasoning with **ultrathink** for Curly's evaluation

## Next Phase
Curly (Evaluator) will assess Larry's analysis against 90+ score threshold before final consolidation.