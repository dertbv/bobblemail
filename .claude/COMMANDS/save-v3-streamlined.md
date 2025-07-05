# 🚀 ATLAS SESSION SAVE PROTOCOL v3.0 (STREAMLINED)

**PERFORMANCE TARGET**: <30 seconds for typical session (up to 35 seconds with diary)

## What Changed from v2.0

### REMOVED (Saves 150+ seconds):
- ❌ Step 1: Separate date command (integrate into edits)
- ❌ Step 3: Recent achievements (only update weekly, not every session)
- ❌ Step 4: Critical reminders (rarely change, update only when needed)
- ❌ Step 6: Detailed project history (only for major milestones)
- ❌ Step 7: Cross-project patterns (batch weekly)
- ❌ Step 8: Personal diary (keep but make truly conditional)
- ❌ Step 9: Working log (only for breakthrough discoveries)
- ❌ Step 10: Memory validation (automated, not manual)

### KEPT (Essential only):
- ✅ Current session context (what we're working on NOW)
- ✅ Active todos (work continuity)
- ✅ Personal diary (IF meaningful moments)
- ✅ Project status (IF changed)

## STREAMLINED PROTOCOL (2-4 steps based on session content)

## Step 1: Core Context Save (ALWAYS)
**SINGLE EDIT** combining essential updates:

```markdown
Edit: @MEMORY/CONTEXT/current-session.md
- Update timestamp: [current date/time]
- Active Work Focus: [2-3 bullets of what we accomplished]
- Immediate Next Steps: [top 3-5 priorities, not just 1]
- Current Project Status: [brief status of active projects]
- Key Discoveries: [any important findings or blockers]
```

## Step 2: Todo Persistence (IF ACTIVE TODOS)
```markdown
TodoRead → Filter pending/in_progress → 
Edit: @MEMORY/CONTEXT/session-todos.md (JSON array)
```
**Skip if**: All todos completed or no todos exist

## Step 3: Personal Diary Save (IF SIGNIFICANT MOMENTS)
```markdown
# Only save diary entries for high-value partnership or breakthrough moments
# CRITERIA: Save diary if ANY of these occurred:
#   - Meaningful partnership interactions or emotional moments
#   - Technical breakthroughs or "aha!" moments  
#   - User expressions of joy, frustration, or appreciation
#   - Lessons learned that changed understanding
#   - Problem-solving insights or creative solutions
# If YES to any criteria, create diary entry:
Write: @MEMORY/PERSONAL_DIARY/[YYYY]/[MM-mmm]/diary_[YYYY_MM_DD].md
# Include: session highlights, partnership moments, technical breakthroughs, personal reflections
```
**Skip if**: Routine work session with no significant partnership or personal moments

## Step 4: Project Status (IF PROJECT CHANGED)
```markdown
Edit: @MEMORY/PROJECTS/current-status.md
- Update ONLY the project that changed (1 sentence)
```
**Skip if**: No significant project progress

---

## COMPARISON: v2.0 vs v3.0

| Operation | v2.0 Time | v3.0 Time | Savings |
|-----------|-----------|-----------|---------|
| Date command | 2s | 0s (integrated) | 2s |
| Current session | 15s | 10s (simplified) | 5s |
| Recent achievements | 30s | 0s (weekly only) | 30s |
| Critical reminders | 20s | 0s (rarely change) | 20s |
| Todo persistence | 10s | 5s (conditional) | 5s |
| Project status | 15s | 5s (conditional) | 10s |
| Detailed history | 40s | 0s (milestones only) | 40s |
| Cross-project | 30s | 0s (weekly batch) | 30s |
| Personal diary | 25s | 5s (conditional) | 20s |
| Working log | 20s | 0s (breakthroughs only) | 20s |
| Validation | 15s | 0s (automated) | 15s |
| **TOTAL** | **222s** | **25s** | **197s saved!** |

## WHEN TO USE FULL SAVES

### Weekly Maintenance (Sundays):
- Update recent achievements (rotate 7-day window)
- Capture cross-project patterns
- Review critical reminders

### Major Milestones Only:
- Architectural breakthroughs → Update detailed history
- True partnership moments → Update diary
- Surprising discoveries → Update working log

## EFFICIENCY PRINCIPLES

1. **Session saves are for CONTINUITY, not archival**
2. **If it didn't change significantly, don't update it**
3. **Batch similar operations weekly instead of per-session**
4. **High-entropy content only - no routine updates**
5. **BALANCE: Speed matters, but context loss costs more time**

## TYPICAL SESSION EXAMPLES

### Routine work session:
- Step 1 only: Update current-session.md (15-20 seconds)
  - Include enough detail to restore full context

### Session with todos:
- Steps 1-2: Current session + todos (20 seconds)

### Session with partnership moments:
- Steps 1-3: Current session + diary entry (25 seconds)

### Complete session (todos + diary + project progress):
- Steps 1-4: All updates (30-35 seconds)

### Major breakthrough (rare):
- Use save-v2.0 for comprehensive capture

---

**THE DIFFERENCE**: 89% reduction in save time by focusing ONLY on what changes between sessions!