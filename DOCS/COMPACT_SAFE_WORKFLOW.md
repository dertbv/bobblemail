# ATLAS Compact-Safe Workflow

## Overview

The compact-safe workflow protects your todos, session state, and work context when using Claude Code's `/compact` or `/clear` commands. This prevents loss of active work during conversation operations.

## Quick Reference

**Before `/compact` or `/clear`:**
```bash
./atlas-checkpoint "before compact"
```

**After `/compact` or `/clear`:**
```bash
./who
```

That's it! Your full session context is restored.

## Detailed Workflow

### Step 1: Pre-Compact Checkpoint

Before using `/compact` or `/clear`, create a checkpoint:

```bash
# Create checkpoint with optional notes
./atlas-checkpoint "working on session restoration system"

# Or simple checkpoint
./atlas-checkpoint
```

**What this does:**
- Saves current todos and session state
- Detects uncommitted git changes
- Creates timestamped backup in `MEMORY/CHECKPOINTS/`
- Verifies backup integrity
- Shows restore instructions

### Step 2: Safe to Compact/Clear

After successful checkpoint, you can safely:
- Use `/compact` to compress conversation history
- Use `/clear` to clear conversation display
- Exit and restart Claude Code sessions

Your work is protected in the checkpoint.

### Step 3: Post-Compact Restoration

After compact/clear operation, restore your context:

```bash
# Enhanced "who am i" with auto-restore
./who
```

**What this restores:**
- Your ATLAS identity and purpose
- Latest session todos and priorities  
- Current project context
- Git branch information
- Recent working log activity

## Checkpoint Files

Checkpoints are stored in `MEMORY/CHECKPOINTS/` with format:
```
checkpoint_YYYYMMDD_HHMMSS.json
```

Each checkpoint contains:
- Complete session state
- Todo list snapshot  
- Session statistics
- Timestamp and notes
- Verification metadata

## Manual Restoration

If automatic restoration doesn't work, manually restore from specific checkpoint:

```bash
# List available checkpoints
ls MEMORY/CHECKPOINTS/

# Restore specific checkpoint
./atlas-restore checkpoint_20250618_205101.json
```

## Git Integration

The checkpoint system detects uncommitted git changes:

- ✅ **Clean git status**: Safe to compact
- ⚠️ **Uncommitted changes**: Consider committing first

You can still checkpoint with uncommitted changes, but you may want to commit first to avoid losing code changes.

## Best Practices

### When to Checkpoint
- Before any `/compact` or `/clear` operation
- Before closing Claude Code sessions
- After completing significant work milestones
- When switching between different projects

### Checkpoint Notes
Include meaningful notes to identify checkpoints:
```bash
./atlas-checkpoint "completed milestone 3 - checkpoint system"
./atlas-checkpoint "before testing new feature"
./atlas-checkpoint "end of day backup"
```

### Recovery Strategy
1. **Immediate recovery**: `./who` (auto-restores latest)
2. **Specific recovery**: `./atlas-restore filename.json`
3. **Manual recovery**: Edit `.session_state.json` directly

## Troubleshooting

### No Session to Checkpoint
```
⚠️  No active session to checkpoint
💡 Create todos with TodoWrite first, then checkpoint
```
**Solution**: Create todos in Claude Code first, then checkpoint.

### Checkpoint Verification Failed
```
❌ Checkpoint verification failed: Todo count mismatch
```
**Solution**: Try checkpointing again. If persistent, check disk space and file permissions.

### Restoration Not Working
1. Check if checkpoint file exists in `MEMORY/CHECKPOINTS/`
2. Try manual restore: `./atlas-restore filename.json`
3. Check session file: `cat .session_state.json`

## Advanced Usage

### Batch Operations
```bash
# Checkpoint, compact, and restore in sequence
./atlas-checkpoint "batch operation" && echo "Use /compact now" && ./who
```

### Custom Checkpoint Location
Checkpoints are automatically stored in `MEMORY/CHECKPOINTS/`. To backup to different location:
```bash
# After checkpoint, copy to backup location
cp MEMORY/CHECKPOINTS/checkpoint_*.json /path/to/backup/
```

### Integration with Git Workflow
```bash
# Checkpoint, commit, then compact
./atlas-checkpoint "before git commit"
git add . && git commit -m "milestone complete"
# Use /compact in Claude Code
./who  # Restore after compact
```

## File Structure

```
project/
├── atlas-checkpoint           # Checkpoint creation script
├── atlas-restore             # Restore script  
├── who                       # Enhanced identity + restore
├── MEMORY/
│   └── CHECKPOINTS/          # Checkpoint storage
│       ├── checkpoint_20250618_205101.json
│       └── checkpoint_20250618_210543.json
└── .session_state.json       # Active session state
```

## Safety Guarantees

The compact-safe workflow provides:
- ✅ **No todo loss**: All todos preserved across operations
- ✅ **Session continuity**: Current focus and context maintained  
- ✅ **File integrity**: Verification ensures backup completeness
- ✅ **Multiple restore options**: Auto and manual restoration methods
- ✅ **Git awareness**: Detects uncommitted changes
- ✅ **Timestamped backups**: Multiple recovery points available

Your work is safe with the ATLAS compact-safe workflow.