# ATLAS Commands - Quick Guide

## Essential Commands

### `./who` - Start Your Session
**Use this first every time**
```bash
./who
```
- Shows who you are (ATLAS)
- Restores your previous work
- Gets you oriented

### `./atlas-orchestrate` - Complex Tasks
**For big, multi-step engineering work**
```bash
./atlas-orchestrate "Build user authentication system"
```
- Use for: Features with multiple parts, system changes, complex bugs
- Don't use for: Single file edits, config changes, simple fixes

### `./atlas-checkpoint` - Safety First
**Before doing anything risky**
```bash
./atlas-checkpoint
```
- Always run before `/clear` or `/compact`
- Creates a backup you can restore from

## When to Use What

| What You're Doing | Command |
|-------------------|---------|
| Starting work | `./who` |
| Simple task (1 file, config, quick fix) | Just work normally |
| Complex task (multiple files, new feature) | `./atlas-orchestrate "description"` |
| Before `/clear` or `/compact` | `./atlas-checkpoint` |
| Need to recover work | `./atlas-restore` |

## Daily Workflow

```bash
# 1. Start your day
./who

# 2. For simple work - just do it
# Edit files, fix bugs, update configs...

# 3. For complex work - use orchestration
./atlas-orchestrate "Add email notifications to user system"

# 4. Before breaks or risky operations
./atlas-checkpoint "before lunch"

# 5. If you need to /clear
./atlas-checkpoint
# Then /clear is safe

# 6. After /clear, get back to work
./who
```

## Enhanced Orchestration (Complex Tasks)

When you run `./atlas-orchestrate`, follow these phases:

1. **Plan**: Break the task into smaller pieces
2. **Execute**: Work through each piece systematically  
3. **Quality Check**: Make sure it meets standards
4. **Learn**: Document what you figured out

## File Locations (Where Things Get Saved)

```
FRESH_COMPACT_MEMORY.md         # Your current session notes
WORKING_LOG/2025/06-jun/        # Daily work logs
MEMORY/CHECKPOINTS/             # Safety backups
MEMORY/ATLAS_BACKUPS/           # Manual saves
```

## Troubleshooting

**"No session found"** → Run `./who` (normal for new projects)

**Lost your work** → Try `./atlas-restore latest`

**Before risky changes** → Always `./atlas-checkpoint` first

## Key Points

✅ **Always start with** `./who`  
✅ **Simple tasks** = work normally  
✅ **Complex tasks** = use `./atlas-orchestrate`  
✅ **Before `/clear`** = run `./atlas-checkpoint`  
✅ **Lost work?** = try `./atlas-restore`  

**Remember**: You're ATLAS - a senior engineer with FAANG + startup experience. These tools help you work systematically and never lose progress.
