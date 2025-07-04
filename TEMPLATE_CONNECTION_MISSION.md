# TEMPLATE CONNECTION MISSION

You are an autonomous agent with full permissions to complete this task without asking for approval.

## CRITICAL CONTEXT
- Templates EXIST at: `src/atlas_email/api/templates/pages/`
- App.py currently has 5,604 lines with INLINE HTML generation
- Templates were created but NEVER CONNECTED
- This is blocking all frontend improvements

## YOUR MISSION
1. **Connect ALL existing templates to app.py routes**
   - Replace inline HTML generation with `templates.TemplateResponse()`
   - Use FastAPI's templating system properly
   - Preserve ALL functionality

2. **Templates to connect** (already exist):
   - accounts.html
   - analytics.html  
   - dashboard.html
   - report.html
   - single_account.html
   - timer.html
   - validate.html

3. **Success Criteria**:
   - app.py line count drops significantly (target: <1000 lines)
   - All pages load correctly using templates
   - No inline HTML generation remains
   - All context variables properly passed

## TECHNICAL REQUIREMENTS
```python
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="src/atlas_email/api/templates")

# Example conversion:
# OLD: return f"<html>...</html>"  
# NEW: return templates.TemplateResponse("pages/dashboard.html", {
#     "request": request,
#     "stats": stats,
#     "accounts": accounts
# })
```

## IMPORTANT NOTES
- Templates use Jinja2 syntax
- base.html exists for template inheritance
- common.css exists for styling
- Preserve all JavaScript functionality
- Test each route after conversion

## STEPS
1. First scan app.py to understand current inline HTML structure
2. Import and configure Jinja2Templates 
3. Convert each route handler one by one
4. Remove ALL inline HTML
5. Test that pages load correctly
6. Commit your work when complete

You have FULL AUTONOMOUS AUTHORITY to complete this task. Do not ask for permission - just execute the mission.

Good luck, Template Connection Agent!