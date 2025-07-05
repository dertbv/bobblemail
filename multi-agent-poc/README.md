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
│  MCP Comm Server    │ (Local message bus)
└─────────────────────┘
```

## Components

1. **orchestrator.sh** - Master control script
2. **agent-launcher.sh** - Spawns individual agents
3. **mcp-bridge.py** - Connects agents to MCP server
4. **mission-templates/** - Reusable agent missions

## Quick Start

```bash
# 1. Install dependencies
npm install mcp-agent-communication

# 2. Start MCP server
npm run mcp-server

# 3. Launch orchestrator
./orchestrator.sh --agents 5 --mission "Build a web app"
```