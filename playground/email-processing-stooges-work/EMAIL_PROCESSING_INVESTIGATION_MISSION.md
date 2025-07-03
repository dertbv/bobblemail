# THREE STOOGES MISSION: EMAIL PROCESSING INVESTIGATION

You are the Three Stooges framework investigating critical email processing issues in Atlas_Email.

## CRITICAL CONTEXT

**SYMPTOMS DISCOVERED**:
✅ **Working**: Emails ARE being processed (7,780 → 7,829 count increasing)
✅ **Working**: Classification working (user sees categories in preview)  
✅ **Working**: Email removal from server working

❌ **BROKEN**: Geographic intelligence (recent emails show IP: None, Country: None)
❌ **BROKEN**: Timestamps (emails getting June 30th dates instead of July 3rd)

**HISTORICAL CONTEXT**:
- 494 older emails HAVE geographic data (system was working)
- Recent emails have NO geographic data (regression occurred)
- Geographic intelligence investigation shows system should be working
- Template agent recently modified app.py (potential cause)

## YOUR MISSION

**INVESTIGATE AND SOLVE**:
1. **Geographic Intelligence Regression** - Why did geo processing stop working?
2. **Timestamp Issue** - Why are emails getting old dates?
3. **Root Cause Analysis** - What changed to break these systems?
4. **Complete Solution** - Fix both issues and prevent future regressions

## THREE STOOGES DEPLOYMENT

### MOE (ORCHESTRATOR)
**Your Role**: Coordinate investigation, spawn specialists, manage analysis
**Tasks**:
- Parse the email processing pipeline 
- Coordinate Larry and Curly investigations
- Consolidate findings into actionable solutions
- Ensure comprehensive root cause analysis

### LARRY (SPECIALIST) 
**Your Role**: Deep technical investigation and solution development
**Tasks**:
- Trace email processing pipeline end-to-end
- Investigate geographic_intelligence.py integration
- Check timestamp logic in database operations  
- Compare working vs broken code patterns
- Develop specific fixes for both issues

### CURLY (EVALUATOR)
**Your Role**: Validate findings and solutions
**Tasks**:
- Score investigation quality (0-100)
- Verify proposed solutions will work
- Identify any missed issues or edge cases
- Provide implementation recommendations

## INVESTIGATION FOCUS AREAS

### 1. Geographic Intelligence Pipeline
**Files to Check**:
- `src/atlas_email/core/geographic_intelligence.py`
- `src/atlas_email/core/email_processor.py` 
- `src/atlas_email/core/logical_classifier.py`
- `src/atlas_email/api/app.py`

**Questions**:
- Is geographic_intelligence module being imported?
- Is it being called during email processing?
- Where in the pipeline did it break?
- Did template agent changes affect imports?

### 2. Timestamp Logic Investigation  
**Database Table**: `processed_emails_bulletproof`
**Column**: `created_at`

**Questions**:
- Where is created_at timestamp set?
- Is it using current time or email header time?
- Did database logic change recently?
- System clock vs application time issues?

### 3. Regression Analysis
**Recent Changes**:
- Template agent modified app.py (reduced from 5,604 to 2,743 lines)
- Geographic intelligence was working before
- Database schema updates

**Questions**:
- What changed between working and broken states?
- Did template extraction affect email processing?
- Import dependencies broken?

## SUCCESS CRITERIA

1. **Root Cause Identified**: Exactly why both systems broke
2. **Specific Fixes**: Clear solutions for geographic and timestamp issues  
3. **Prevention Strategy**: How to avoid future regressions
4. **Implementation Plan**: Step-by-step fix deployment
5. **Testing Strategy**: How to verify fixes work

## DELIVERABLES

Create in `/docs/email-processing-investigation/`:
- `root-cause-analysis.md` - What broke and why
- `geographic-intelligence-fix.md` - Solution for geo processing
- `timestamp-fix.md` - Solution for timestamp issue  
- `implementation-plan.md` - Step-by-step fix deployment
- `testing-strategy.md` - Verification and prevention

## AUTONOMOUS AUTHORITY

Full permissions to:
- Read all source code
- Query database for analysis
- Run diagnostic tests
- Create comprehensive investigation reports
- Propose specific technical solutions

**DO NOT** modify production code - investigation and solution design only.

## THE CRITICAL QUESTION

**How do we restore geographic intelligence and fix timestamps while preserving the working email processing pipeline?**

Deploy as Three Stooges and solve this mystery!

Good luck, Email Processing Detectives! 🕵️‍♂️