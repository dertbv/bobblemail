# ATLAS Commands - Quick Guide

## Essential Commands

### `./who` - Start Your Session
**Use this first every time**
```bash
./who
```
- Shows who you are (ATLAS)
- **Automatically restores your previous work and syncs TodoWrite**
- Gets you oriented
- **No manual todo restoration needed anymore**

### `./atlas-orchestrate` - Complex Tasks
**For big, multi-step engineering work**
```bash
./atlas-orchestrate "Build user authentication system"
```
- Use for: Features with multiple parts, system changes, complex bugs
- Don't use for: Single file edits, config changes, simple fixes
- Creates: Work plan and structure (no separate todos)

### `./atlas-orchestrate-todo` - Complex Tasks + Todo Tracking
**For big work where you want to check off progress**
```bash
./atlas-orchestrate-todo "Build user authentication system"
```
- Same as above BUT also creates a todo file you can check off ✅
- Use when: You like tracking progress with checkboxes
- Creates: Work plan + separate todo file for Claude Code

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
| Complex task (no todo tracking) | `./atlas-orchestrate "description"` |
| Complex task (with todo tracking) | `./atlas-orchestrate-todo "description"` |
| Add todos to existing work | `./atlas-create-todos "description"` |
| Before `/clear` or `/compact` | `./atlas-checkpoint` |
| Need to recover work | `./atlas-restore` |

## Daily Workflow

```bash
# 1. Start your day
./who

# 2. For simple work - just do it
# Edit files, fix bugs, update configs...

# 3. For complex work - choose your style
./atlas-orchestrate "Add email notifications to user system"        # Just structure
./atlas-orchestrate-todo "Add email notifications to user system"   # Structure + todos

# 4. Before breaks or risky operations
./atlas-checkpoint "before lunch"

# 5. If you need to /clear
./atlas-checkpoint
# Then /clear is safe

# 6. After /clear, get back to work
./who
```

## Enhanced Orchestration (Complex Tasks)

You now have **two options** for complex tasks:

### Option 1: `./atlas-orchestrate` (Structure Only)
When you run it, follow these phases:
1. **Plan**: Break the task into smaller pieces
2. **Execute**: Work through each piece systematically  
3. **Quality Check**: Make sure it meets standards
4. **Learn**: Document what you figured out

### Option 2: `./atlas-orchestrate-todo` (Structure + Checkboxes)
Same phases, but you also get a todo file with checkboxes:
- ✅ Can check off each step as you complete it
- ✅ Visual progress tracking in Claude Code
- ✅ Helpful for staying motivated on big tasks

## File Locations (Where Things Get Saved)

```
FRESH_COMPACT_MEMORY.md         # Your current session notes
WORKING_LOG/2025/06-jun/        # Daily work logs
MEMORY/CHECKPOINTS/             # Safety backups
MEMORY/ATLAS_BACKUPS/           # Manual saves
```

## Troubleshooting

**"No session found"** → Run `./who` (normal for new projects)

**Lost your work** → Run `./who` first (auto-restores), then try `./atlas-restore latest` if needed

**TodoRead() shows empty but you have work** → Run `./who` to sync session bridge

**Before risky changes** → Always `./atlas-checkpoint` first

## Key Points

✅ **Always start with** `./who` **(now auto-syncs todos)**  
✅ **Simple tasks** = work normally  
✅ **Complex tasks** = use `./atlas-orchestrate` or `./atlas-orchestrate-todo`  
✅ **Want checkboxes?** = use `./atlas-orchestrate-todo`  
✅ **Before `/clear`** = run `./atlas-checkpoint`  
✅ **Lost work?** = run `./who` first, then try `./atlas-restore`  

**Remember**: You're ATLAS - a senior engineer with FAANG + startup experience. The session bridge now handles todo synchronization automatically, making your workflow seamless.
