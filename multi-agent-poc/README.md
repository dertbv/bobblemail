# Multi-Agent Orchestration POC

## Architecture

```
┌─────────────────────┐
│   Orchestrator      │ (You + Master Script)
└──────────┬──────────┘
           │
┌──────────┴──────────┐
│  Claude Squad TUI   │ (Manages tmux sessions)
└──────────┬──────────┘
           │
┌──────────┴──────────────────────────┐
│  Agent 1  │  Agent 2  │ ... │ Agent 10 │ (Parallel Claude instances)
└──────────┬──────────────────────────┘
           │
┌──────────┴──────────┐
│  Git Coordination   │ (Shared file-based communication)
└─────────────────────┘
```

## Components

1. **orchestrator.sh** - Master control script
2. **claude-agent-mission.md** - Agent mission template
3. **coordination/** - Git-tracked directory for agent communication
4. **missions/** - Generated agent-specific missions

## Quick Start

```bash
# 1. Launch orchestrator with desired number of agents
./orchestrator.sh 5 "Build a web app"

# 2. Inject missions into each agent
./inject-mission.sh [agent-session] missions/agent-[n].md

# 3. Monitor coordination
cd coordination && watch -n 2 'git log --oneline -10'
```

## How It Works

1. **Orchestrator** creates a git-tracked coordination directory
2. **Agents** write status updates to individual files (agent-N-status.md)
3. **Git commits** provide atomic updates and history tracking
4. **Agents poll** other agents' files to coordinate work

## Agent Communication Protocol

Agents coordinate by:
- Writing status to: `coordination/agent-[ID]-status.md`
- Reading others' status files
- Using git commits as synchronization points
- Following mission-defined coordination patterns