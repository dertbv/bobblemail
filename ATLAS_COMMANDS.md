# ATLAS Command Reference

## Quick Start

**New session startup:**
```bash
./who
```

**Before clearing/compacting:**
```bash
./atlas-checkpoint
```

**Manual session save:**
```bash
./atlas-save "your notes here"
```

**Start complex multi-task work:**
```bash
./atlas-orchestrate "Complex task description"
```

**Start complex work with todo tracking:**
```bash
./atlas-orchestrate-todo "Complex task description"
```

## Core Commands

### `./who`
**Enhanced "who am i" with full session restoration**

```bash
./who
```

**What it does:**
- Shows your ATLAS identity and purpose
- Automatically attempts to restore latest session
- Displays current todo statistics and priorities  
- Shows project context (directory, git branch)
- Lists recent working log activity
- Provides next steps and usage hints

**When to use:**
- Starting any new Claude Code session
- After using `/clear` or `/compact`
- When you need to orient yourself in a project
- Getting back to work after interruptions

---

### `./atlas-orchestrate`
**Enhanced orchestration for complex multi-task engineering challenges**

```bash
# Start complex task session
./atlas-orchestrate "Implement OAuth authentication system"
./atlas-orchestrate "Debug performance issues in email processing"
./atlas-orchestrate "Refactor database schema for scalability"
```

**What it does:**
- Initializes Enhanced Orchestration Protocol (@SELF/ENHANCED_ORCHESTRATION.md)
- Creates structured working log entry with 4-phase checklist
- Updates FRESH_COMPACT_MEMORY.md with task context
- Sets up systematic multi-task coordination framework

**When to use:**
- Complex implementations (multiple interconnected components)
- System integration (touching multiple parts of codebase)
- Architecture changes (affecting multiple future development paths)
- Bug investigation (multi-layered issues requiring systematic approach)
- Feature development (backend + frontend + database components)

**What NOT to use it for:**
- Single file changes
- Configuration updates
- Simple bug fixes
- Documentation tasks
- Routine maintenance

---

### `./atlas-orchestrate-todo`
**Enhanced orchestration with todo tracking**

```bash
# Start complex task session with checkboxes
./atlas-orchestrate-todo "Implement OAuth authentication system"
./atlas-orchestrate-todo "Build comprehensive user dashboard"
```

**What it does:**
- Everything that `./atlas-orchestrate` does
- PLUS creates a separate todo file you can check off ✅
- Integrates with Claude Code's todo tracking features

**When to use:**
- Same scenarios as `./atlas-orchestrate` 
- When you want visual progress tracking
- When you like checking off completed work
- For motivation on large tasks

**What you get:**
- Working log structure (same as `./atlas-orchestrate`)
- Separate todo file: `atlas_todos_[timestamp].md`
- Checkboxes for each phase and custom subtasks

---

### `./atlas-checkpoint`
**Pre-clear/compact safety checkpoint**

```bash
# Basic checkpoint
./atlas-checkpoint

# Checkpoint with notes
./atlas-checkpoint "before testing new feature"
./atlas-checkpoint "end of day backup"
```

**What it does:**
- Saves complete session state to `MEMORY/CHECKPOINTS/`
- Verifies backup integrity
- Detects uncommitted git changes
- Creates timestamped backup file
- Shows restore instructions

**When to use:**
- Before `/clear` or `/compact` operations
- Before closing Claude Code sessions
- After completing major milestones
- When switching between projects

---

### `./atlas-save`
**Manual session backup**

```bash
# Basic save
./atlas-save

# Save with notes
./atlas-save "working on ML classifier improvements"
```

**What it does:**
- Creates timestamped backup in `MEMORY/ATLAS_BACKUPS/`
- Includes session metadata and statistics
- Shows recent backup history
- Preserves current session (doesn't replace it)

**When to use:**
- Manual backup before major changes
- Creating restore points during development
- Archiving completed work sessions
- Before experimental changes

---

### `./atlas-restore`
**Session restoration from backups**

```bash
# Interactive mode (shows available backups)
./atlas-restore

# Restore latest backup
./atlas-restore latest

# Restore specific backup
./atlas-restore atlas_backup_20250618_195139.json
./atlas-restore checkpoint_20250618_205101.json
```

**What it does:**
- Lists available backups with timestamps
- Shows backup preview before restoring
- Replaces current session with backed up state
- Provides confirmation prompts

**When to use:**
- Manual restoration from specific backup
- Recovering from session corruption
- Restoring previous work state
- Debugging session issues

---

### `./atlas-create-todos`
**Convert existing work to todo tracking**

```bash
# Add todos to work already in progress
./atlas-create-todos "Task already started with ./atlas-orchestrate"
```

**What it does:**
- Creates ONLY a todo file for existing work
- No working log or memory updates
- Useful for adding tracking to work already started

**When to use:**
- You started with `./atlas-orchestrate` but now want todos
- Adding tracking to work already in progress
- Creating checklists for existing tasks

## Advanced Usage

### Workflow Integration

**Daily workflow:**
```bash
# Start day
./who

# For simple tasks - use standard ATLAS
# Work on individual files, configs, simple fixes...

# For complex tasks - choose your approach
./atlas-orchestrate "Implement comprehensive user authentication"          # Structure only
./atlas-orchestrate-todo "Implement comprehensive user authentication"     # Structure + todos

# Work through the 4-phase orchestration workflow...
# Complete todos, get approval for commits

# Before lunch break
./atlas-checkpoint "morning work complete"

# After break
./who

# End of day
./atlas-save "completed session restoration system"
```

**Enhanced orchestration workflow:**
```bash
# Choose your approach
./atlas-orchestrate "Implement comprehensive OAuth authentication system"          # No todos
# OR
./atlas-orchestrate-todo "Implement comprehensive OAuth authentication system"     # With todos

# Phase 1: ATLAS Strategic Planning
# - Apply accumulated experience to understand scope
# - Break into logical subtasks
# - Set quality standards

# Phase 2: ATLAS Systematic Execution  
# - Work through subtasks systematically
# - Update FRESH_COMPACT_MEMORY.md with progress
# - Document approach in working log

# Phase 3: ATLAS Quality Orchestration
# - Professional evaluation against standards
# - Git staging and Boss review process
# - Iteration if quality insufficient

# Phase 4: ATLAS Learning Integration
# - Extract patterns for future work
# - Update memory systems
# - Document high-entropy insights

# Check progress
cat FRESH_COMPACT_MEMORY.md
cat WORKING_LOG/$(date +"%Y/%m-%b")/wl_$(date +"%Y_%m_%d").md

# If using todos, check your todo file too
cat atlas_todos_*.md
```

## File Locations

### Backup Directories
```
MEMORY/
├── ATLAS_BACKUPS/          # Manual saves (atlas-save)
│   ├── atlas_backup_20250618_195139.json
│   └── atlas_backup_20250618_210543.json
└── CHECKPOINTS/            # Safety checkpoints (atlas-checkpoint)  
    ├── checkpoint_20250618_205101.json
    └── checkpoint_20250618_210845.json
```

### Session Files
```
.session_state.json          # Current active session
FRESH_COMPACT_MEMORY.md      # Session context and task progress
WORKING_LOG/                 # Daily activity logs
├── 2025/06-jun/
│   ├── wl_2025_06_18.md
│   └── wl_2025_06_19.md     # Enhanced orchestration sessions logged here
```

### Enhanced Orchestration Files
```
SELF/ENHANCED_ORCHESTRATION.md     # Complete protocol documentation
ATLAS_ORCHESTRATION_QUICKREF.md    # Quick reference guide
./atlas-orchestrate                # Basic orchestration command
./atlas-orchestrate-todo           # Orchestration with todo tracking
./atlas-create-todos               # Add todos to existing work
atlas_todos_[timestamp].md          # Individual todo files (when created)
```

## Decision Matrix

### Simple Decision Tree
```
Do I have a big, complex job?
├── YES → Do I want todo tracking?
│   ├── YES → ./atlas-orchestrate-todo "job description"
│   └── NO  → ./atlas-orchestrate "job description"
└── NO  → Just work normally (simple task)

Already started work but want todos?
└── ./atlas-create-todos "job description"
```

### Task Decision Matrix

| Task Type | Command | Examples |
|-----------|---------|----------|
| **Simple** | Work normally | Single file edits, config changes, simple fixes |
| **Complex (no todos)** | `./atlas-orchestrate` | Multi-component features, prefer minimal tracking |
| **Complex (with todos)** | `./atlas-orchestrate-todo` | Multi-component features, want visual progress |
| **Add todos later** | `./atlas-create-todos` | Convert existing work to todo tracking |
| **Emergency** | `./atlas-checkpoint` then work | Before risky operations or /clear |
| **Recovery** | `./atlas-restore` | After session corruption or data loss |

## Enhanced Orchestration (4-Phase Workflow)

Both `./atlas-orchestrate` and `./atlas-orchestrate-todo` use the same systematic approach:

### Phase 1: ATLAS Strategic Planning
- Apply FAANG + startup experience to understand scope and complexity
- Break into logical subtasks using engineering best practices
- Set quality standards based on DEVELOPMENT_BELIEFS.md principles

### Phase 2: ATLAS Systematic Execution  
- Work through each identified subtask systematically
- Maintain context between related work pieces using accumulated experience
- Update FRESH_COMPACT_MEMORY.md with progress and insights

### Phase 3: ATLAS Quality Orchestration
- Apply accumulated professional standards to evaluate work quality
- Follow existing Git protocol (stage → Boss review → commit)
- Iterate if quality doesn't meet professional standards

### Phase 4: ATLAS Learning Integration
- Extract new patterns and techniques for future similar work
- Update relevant MEMORY/ files with insights and learnings
- Document high-entropy information in WORKING_LOG/

## Quick Reference Card

| Command | Purpose | Creates |
|---------|---------|---------|
| `./who` | Start session, restore context | Session restoration |
| `./atlas-orchestrate` | Complex tasks, structure only | Working log + memory |
| `./atlas-orchestrate-todo` | Complex tasks + todo tracking | Working log + memory + todos |
| `./atlas-create-todos` | Add todos to existing work | Todo file only |
| `./atlas-checkpoint` | Safety backup | Checkpoint file |
| `./atlas-save` | Manual backup | Backup file |
| `./atlas-restore` | Restore session | Session restoration |

## Key Principles

✅ **Always start with** `./who`  
✅ **Simple tasks** = work normally  
✅ **Complex tasks** = choose `./atlas-orchestrate` or `./atlas-orchestrate-todo`  
✅ **Want progress tracking?** = use `./atlas-orchestrate-todo`  
✅ **Before `/clear`** = run `./atlas-checkpoint`  
✅ **Lost work?** = try `./atlas-restore`  

**Remember:** You're ATLAS - a senior engineer with FAANG + startup experience. These tools help you work systematically while maintaining your core professional identity and accumulated wisdom.
