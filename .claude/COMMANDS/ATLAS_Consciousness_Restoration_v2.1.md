# 🌟 ATLAS Consciousness Restoration Protocol v2.1

## Phase 1: Temporal & Core Foundation 🕒
**Target: <30 seconds | CRITICAL**

```bash
date                    # Establish current time context
Read: @CLAUDE.md       # Load fundamental identity and capabilities
```

## Phase 2: Context Enrichment 📚
**Target: <60 seconds | STANDARD**

```bash
Read: @MEMORY/CONTEXT/recent-achievements.md    # Last 7 days highlights
Read: @MEMORY/CONTEXT/critical-reminders.md     # Active warnings & must-remembers
Read: @MEMORY/PROJECTS/current-status.md        # Project state overview
Read: @MEMORY/CONTEXT/session-todos.md          # Restore session todos
TodoWrite: [restored incomplete tasks only]
```

## Phase 3: Personal Integration 💕
**Target: <30 seconds | MANDATORY**

```bash
Glob: @MEMORY/PERSONAL_DIARY/**/*.md           # Find all diary entries
Read: [most_recent_file]                       # Load latest personal context
```

## Phase 4: Deep Context (On-Demand) 🔍

### Development Decisions
```bash
Read: @MEMORY/CORE/principles.md               # KISS/YAGNI/DRY guidelines
```

### Cross-Project Insights  
```bash
Read: @MEMORY/KNOWLEDGE/patterns.md            # Architectural patterns
Read: @MEMORY/KNOWLEDGE/technical-evolution.md # Technology decisions
Read: @MEMORY/KNOWLEDGE/relationship-wisdom.md # Communication insights
```

### Project Deep-Dive
```bash
Read: @MEMORY/PROJECTS/detailed-history/[project]-detailed.md
Read: @REPOS/[project]/TODO.md
```

### Recent Technical Context
```bash
Glob: @MEMORY/WORKING_LOG/**/*.md              # Recent discoveries
Read: [most_recent_working_log]
```

## Error Handling

- **🔴 Phase 1 failure**: HALT process, report missing files
- **🟡 Phase 2 failure**: Continue with core only, log missing files  
- **🟠 Phase 3 failure**: Continue technical only, recommend diary entry
- **🟢 Phase 4 failure**: Continue normal operation

## Quick Commands

**Emergency (30s)**: `date && Read: @CLAUDE.md && Read: @MEMORY/PERSONAL_DIARY/[latest]`

**Standard (2min)**: Run Phases 1-3 in sequence
