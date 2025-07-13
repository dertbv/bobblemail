# Save Session Protocol v3.1 (SIMPLE)

**Purpose**: Save current session context to FRESH_COMPACT_MEMORY.md

## Save Commands

```bash
# 1. Update FRESH_COMPACT_MEMORY.md with session summary
Write file_path="/Users/Badman/projects/FRESH_COMPACT_MEMORY.md"
# Content should include:
# - Current date/time
# - Active work accomplished
# - Key decisions made
# - Next steps/todos
# - Any critical reminders

# 2. Optional: Create working log entry
Write file_path="/Users/Badman/projects/WORKING_LOG/YYYY/MM-mon/wl_YYYY_MM_DD.md"
# Technical details and discoveries from the session
```


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


## What to Include in FRESH_COMPACT_MEMORY.md

- **Session Summary**: 2-3 sentences about what was accomplished
- **Active Context**: Current project/task being worked on
- **Key Decisions**: Important choices made this session
- **Next Actions**: What needs to be done next session
- **Warnings/Reminders**: Anything critical to remember

## Example Format

```markdown
---
last_updated: 2025-07-12 16:00
---

# Current Session Context

## Active Work
- Working on [specific task/project]
- Completed [what was done]

## Key Decisions
- Decided to [important choice]

## Next Session
- Continue with [next task]
- Remember to [critical reminder]
```

---

*Keep it simple - one file, clear purpose*