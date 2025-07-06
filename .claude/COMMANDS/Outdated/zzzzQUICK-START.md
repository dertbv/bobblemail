# 🚀 Six Agent System - Quick Start Guide

## Usage

The unified deployment script combines mission generation and agent deployment into a single command:

```bash
./agent.sh "your task description"
```

## Examples

```bash
# Feature Implementation
./agent.sh "implement user authentication system"
./agent.sh "add real-time notifications"
./agent.sh "create dashboard analytics"

# Bug Fixes
./agent.sh "fix memory leak in data parser"
./agent.sh "resolve login session timeout issues"

# Refactoring
./agent.sh "refactor email processing pipeline"
./agent.sh "optimize database query performance"

# Analysis
./agent.sh "analyze security vulnerabilities"
./agent.sh "investigate performance bottlenecks"
```

## What It Does

1. **Analyzes your request** and determines task type (feature/bug/refactor/analysis)
2. **Generates a comprehensive mission file** with requirements, constraints, and deliverables
3. **Creates a git worktree** with timestamped branch for isolated work
4. **Launches tmux session** with Claude agent system
5. **Deploys the mission** to the six-agent system
6. **Provides connection instructions** for monitoring progress

## Connection Options

After deployment, you can connect using:

**Standard tmux:**
```bash
tmux attach -t [session-name]
```

**iTerm2 native windows:**
```bash
tmux -CC attach -t [session-name]
```

**Quick progress check:**
```bash
tmux capture-pane -t [session-name] -S -20 -p
```

## Six Agent Workflow

The system coordinates these agents automatically:

1. **PLANNER** - Analyzes mission, creates WORK.md with implementation plan
2. **EXECUTER** - Implements the solution according to the plan
3. **TESTER** - Creates comprehensive test suite (>90% coverage)
4. **DOCUMENTER** - Generates technical and user documentation
5. **VERIFIER** - Validates all requirements are met and quality standards passed
6. **REPORTER** - Creates final summary and deployment instructions

## Monitoring Progress

- Check `WORK.md` for the main coordination file
- Look for generated files in the worktree directory
- Use tmux to watch real-time agent coordination
- Quality gates ensure 90% completion before proceeding to next phase

## File Locations

- **Worktree**: `/Users/Badman/Desktop/email/Agents/agent-[task]-[timestamp]/`
- **Mission File**: `AGENT_MISSION.md` (in worktree)
- **Coordination**: `WORK.md` (created by PLANNER)
- **Deliverables**: Various files created by each agent

## Error Recovery

If agents get stuck:
1. Check the last output in tmux
2. Provide clarification through the tmux session
3. Agents will auto-iterate if VERIFIER rejects work
4. Monitor WORK.md for coordination status

---

**Tip**: The system is designed for autonomous operation. Let the agents coordinate and check progress periodically rather than micromanaging individual steps.
