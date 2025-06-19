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
- Prepares ATLAS for complex engineering challenges

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

**4-Phase Enhanced Workflow:**
1. **ATLAS Strategic Planning**: Apply FAANG + startup experience to scope and decompose
2. **ATLAS Systematic Execution**: Implement subtasks with context management
3. **ATLAS Quality Orchestration**: Professional evaluation and iteration
4. **ATLAS Learning Integration**: Extract patterns and update memory systems

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

## Advanced Usage

### Workflow Integration

**Daily workflow:**
```bash
# Start day
./who

# For simple tasks - use standard ATLAS
# Work on individual files, configs, simple fixes...

# For complex tasks - use enhanced orchestration
./atlas-orchestrate "Implement comprehensive user authentication"

# Work through the 4-phase orchestration workflow...
# Complete todos, get approval for commits

# Before lunch break
./atlas-checkpoint "morning work complete"

# After break
./who

# End of day
./atlas-save "completed session restoration system"
```

**Git integration:**
```bash
# Before major git operations
./atlas-checkpoint "before rebasing feature branch"

# After git operations, restore context
./who
```

**Enhanced orchestration workflow:**
```bash
# Start complex task
./atlas-orchestrate "Implement comprehensive OAuth authentication system"

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
```

**Testing workflow:**
```bash
# Before risky changes
./atlas-checkpoint "before experimental changes"

# If things go wrong, restore
./atlas-restore latest

# If successful, continue normally
./who
```

### Batch Operations

**Checkpoint and continue:**
```bash
./atlas-checkpoint "batch checkpoint" && echo "Safe to /clear now"
```

**Save and show status:**
```bash
./atlas-save "milestone backup" && ./who
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
./atlas-orchestrate                # Command script
```

## Troubleshooting

### Common Issues

**"No session state found"**
```bash
# Solution: Create todos first in Claude Code
# Then use commands
./who  # Will show "starting fresh"
```

**"No previous session found"**
```bash
# Normal for new projects - create some todos first
# Or restore from specific backup
./atlas-restore atlas_backup_filename.json
```

**"Checkpoint verification failed"**
```bash
# Try again - usually transient issue
./atlas-checkpoint

# If persistent, check disk space and permissions
```

**Git changes detected**
```bash
# Checkpoint warns about uncommitted changes
# Either commit first, or proceed anyway
git add . && git commit -m "work in progress"
./atlas-checkpoint
```

### Recovery Options

**Lost session data:**
1. Try `./who` (auto-restores latest)
2. Try `./atlas-restore latest`
3. List and restore specific backup:
   ```bash
   ls MEMORY/ATLAS_BACKUPS/
   ./atlas-restore filename.json
   ```

**Corrupted session file:**
```bash
# Remove corrupted file and restore
rm .session_state.json
./atlas-restore latest
```

## Tips and Best Practices

### Naming Conventions
```bash
# Good checkpoint notes
./atlas-checkpoint "completed milestone 3"
./atlas-checkpoint "before major refactor"
./atlas-checkpoint "working classifier implementation"

# Good save notes  
./atlas-save "end of sprint 2"
./atlas-save "stable ML pipeline version"
```

### Timing
- **Checkpoint**: Before risky operations (`/clear`, `/compact`, major changes)
- **Save**: After completing meaningful work units
- **Who**: Start of every session, after clearing/compacting

### Integration
- Use with git workflow - checkpoint before major git operations
- Combine with todo management - save after completing milestones
- Use with Claude Code features - checkpoint before `/compact`

## Quick Reference Card

| Command | Usage | Purpose |
|---------|--------|---------|
| `./who` | Session start | Identity + restore + context |
| `./atlas-orchestrate` | Complex tasks | Enhanced multi-task coordination |
| `./atlas-checkpoint` | Before /clear | Safety backup |
| `./atlas-save` | Manual backup | Work preservation |
| `./atlas-restore` | Recovery | Session restoration |

### Task Decision Matrix

| Task Type | Command | Examples |
|-----------|---------|----------|
| **Simple** | Standard ATLAS | Single file edits, config changes, simple fixes |
| **Complex** | `./atlas-orchestrate` | Multi-component features, system integration |
| **Emergency** | `./atlas-checkpoint` then work | Before risky operations or /clear |
| **Recovery** | `./atlas-restore` | After session corruption or data loss |

**Remember:** 
- Always `./atlas-checkpoint` before `/clear` or `/compact`!
- Use `./atlas-orchestrate` for complex multi-step engineering challenges
- Check `ATLAS_ORCHESTRATION_QUICKREF.md` for detailed enhanced workflow guide