#!/bin/bash
# Deploy Six Agent System

# Set up variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH_NAME="agent-system-$TIMESTAMP"
WORKTREE_PATH="/Users/Badman/Desktop/email/Agents/$BRANCH_NAME"

# Create git worktree
echo "🌳 Creating git worktree: $BRANCH_NAME"
git worktree add -b $BRANCH_NAME $WORKTREE_PATH

# Start tmux session
echo "🖥️ Starting tmux session: $BRANCH_NAME"
tmux new-session -d -s $BRANCH_NAME -c $WORKTREE_PATH

# Start Claude with permissions flag
echo "🤖 Starting Claude agent system..."
tmux send-keys -t $BRANCH_NAME "claude --dangerously-skip-permissions" Enter

# Wait for Claude to start
sleep 3

# Send the mission
echo "📋 Deploying mission..."
tmux send-keys -t $BRANCH_NAME "You are the PLANNER agent in a six-agent system. Your mission will be provided next." Enter

# Provide connection instructions
echo "✅ Agent system deployed!"
echo ""
echo "To connect:"
echo "  tmux attach -t $BRANCH_NAME"
echo ""
echo "For iTerm2 native windows:"
echo "  tmux -CC attach -t $BRANCH_NAME"
echo ""
echo "To check progress:"
echo "  tmux capture-pane -t $BRANCH_NAME -S -10 -p"