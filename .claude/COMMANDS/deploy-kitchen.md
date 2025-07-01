# 🍳 MULTI-AGENT KITCHEN QUICK DEPLOY

## Setup Commands (Run in sequence):

```bash
# Check existing worktrees
git worktree list

# Create Template Chef Station
git worktree add -b template-extraction ../email-template-work
tmux new-session -d -s template-chef
tmux send-keys -t template-chef "cd /Users/Badman/Desktop/email-template-work" Enter

# Create Moe Orchestrator Station  
git worktree add -b moe-coordination ../email-moe-work
tmux new-session -d -s moe-orchestrator
tmux send-keys -t moe-orchestrator "cd /Users/Badman/Desktop/email-moe-work" Enter

# Create Larry Specialist Station
git worktree add -b larry-specialist ../email-larry-work  
tmux new-session -d -s larry-specialist
tmux send-keys -t larry-specialist "cd /Users/Badman/Desktop/email-larry-work" Enter

# Create Curly Evaluator Station
git worktree add -b curly-evaluator ../email-curly-work
tmux new-session -d -s curly-evaluator  
tmux send-keys -t curly-evaluator "cd /Users/Badman/Desktop/email-curly-work" Enter

# List all stations
tmux list-sessions
```

## Coordination Commands:

```bash
# Send task to agent
tmux send-keys -t [agent-name] "[task description]" Enter

# Check agent progress  
tmux capture-pane -t [agent-name] -p

# Monitor agent (last 10 lines)
tmux capture-pane -t [agent-name] -p | tail -10
```

## Kitchen Roles:
- **Head Chef**: You (orchestrate all agents)
- **Sous Chef**: Main Claude Code (coordinate & monitor)  
- **Template Chef**: Specialized template extraction
- **Moe**: Orchestrator for complex tasks
- **Larry**: Specialist for heavy computational work
- **Curly**: Evaluator with 0-100 scoring

## Next Steps:
1. Run setup commands
2. Attach to each tmux session: `tmux attach -t [agent-name]`
3. Start `claude` in each session
4. Begin coordinated AI development!