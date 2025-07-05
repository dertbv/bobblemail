# AUTONOMOUS AGENT DEPLOYMENT PROTOCOL

## CRITICAL: Full Autonomous Operation - ONLY ONE METHOD WORKS

### THE ONLY SOLUTION: Command Line Flag
Start Claude with the dangerous permissions flag:
```bash
claude --dangerously-skip-permissions
```
This bypasses ALL permission prompts from the start!

### ⚠️ SHIFT+TAB DOES NOT WORK
- Shift+Tab auto-accept mode does NOT work for agents
- Only the --dangerously-skip-permissions flag enables true autonomy
- There is NO other method that works

### 2. Enhanced Mission Template
```bash
tmux send-keys -t [agent-name] '
AUTONOMOUS AGENT MISSION - [AGENT-NAME]

STEP 1: Your Authority
You have FULL AUTONOMOUS AUTHORITY for ALL operations including:
- Creating, editing, deleting ANY files (auto-accepted)
- Running ANY commands or tests (auto-accepted)
- Making ANY code changes (auto-accepted)
- All tool uses automatically approved with auto-accept on

STEP 2: Your Mission
[INSERT SPECIFIC MISSION HERE]

Remember: With auto-accept mode on (Shift+Tab), you work completely autonomously!'
```

### 3. Updated Deployment Sequence with --dangerously-skip-permissions
```bash
# Create worktree
git worktree add -b [branch-name] ../playground/[work-dir]

# Start tmux session
tmux new-session -d -s [agent-name]

# Navigate to worktree
tmux send-keys -t [agent-name] 'cd /path/to/worktree' Enter

# Start Claude with NO PERMISSIONS FLAG
tmux send-keys -t [agent-name] 'claude --dangerously-skip-permissions' Enter

# Wait for startup
sleep 5

# Deploy mission - NO PERMISSION INSTRUCTIONS NEEDED!
tmux send-keys -t [agent-name] '[MISSION]' Enter
```

### 4. Original Deployment Checklist (if not using flag)
- [ ] Create git worktree
- [ ] Start tmux session
- [ ] Navigate to worktree
- [ ] Start claude (with or without --dangerously-skip-permissions)
- [ ] Send single Enter for initial auth (if not using flag)
- [ ] Deploy mission with Shift+Tab instructions (if not using flag)
- [ ] Verify agent working autonomously

### 4. Monitoring Without Interrupting
```bash
# Check progress without interfering
tmux capture-pane -t [agent-name] -S -20 -p

# Look for this indicator of auto-accept mode:
# "⏵⏵ auto-accept edits on"
```

### 5. Why This Works
- Shift+Tab toggles Claude Code's built-in auto-accept feature
- With auto-accept on, ALL tool uses are automatically approved
- No more "Select an option" prompts
- Agent can work completely autonomously
- This is an official Claude Code feature designed for trusted autonomous work

### 6. Example Successful Deployment
```bash
# Agent output showing auto-accept mode active:
⏺ Write(geographic_migration_script.py)
  ⎿  Wrote 145 lines to geographic_migration_script.py  # Auto-accepted!

⏺ Bash(python geographic_migration_script.py)
  ⎿  Running...  # Auto-accepted!

# Bottom of screen shows:
⏵⏵ auto-accept edits on (shift+tab to cycle)
```

## REMEMBER: The key is Shift+Tab for TRUE autonomous operation!