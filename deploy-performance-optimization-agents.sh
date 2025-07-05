#!/bin/bash

# Atlas_Email Performance Optimization - 6-Agent Deployment Script

MISSION_NAME="atlas-performance-optimization"

echo "🚀 Deploying 6-agent system for Atlas_Email Performance Optimization"

# Step 1: Create worktree
echo "📁 Creating agent worktree..."
git worktree add -b agent-system-$MISSION_NAME /Users/Badman/Desktop/email/Agents/agent-system-$MISSION_NAME

# Step 2: Copy agent files
echo "📋 Copying agent framework files..."
cp Agents/*AGENT*.md /Users/Badman/Desktop/email/Agents/agent-system-$MISSION_NAME/

# Step 3: Copy mission file
echo "📜 Copying mission file..."
cp ATLAS_EMAIL_PERFORMANCE_OPTIMIZATION_MISSION.md /Users/Badman/Desktop/email/Agents/agent-system-$MISSION_NAME/MISSION.md

# Step 4: Copy performance plan
echo "📊 Copying performance plan..."
cp -r plans /Users/Badman/Desktop/email/Agents/agent-system-$MISSION_NAME/

# Step 5: Create tmux session
echo "🖥️ Creating tmux session..."
tmux new-session -d -s agent-system-$MISSION_NAME -c /Users/Badman/Desktop/email/Agents/agent-system-$MISSION_NAME

# Step 6: Start Claude
echo "🤖 Starting Claude..."
tmux send-keys -t agent-system-$MISSION_NAME "claude --dangerously-skip-permissions" Enter

# Step 7: Send agent initialization
echo "📨 Sending agent initialization..."
sleep 3 && tmux send-keys -t agent-system-$MISSION_NAME "Read the *AGENT*.md files in this directory to understand the six-agent system (PLANNER, INVESTIGATOR, EXECUTER, DOCUMENTER, TESTER, VERIFIER). You are starting as the PLANNER agent. Implement this system to accomplish the performance optimization mission in MISSION.md. The detailed implementation plan is in plans/atlas-email-performance-optimization.md. You have full autonomous authority to implement all optimizations. Focus on delivering measurable performance improvements while maintaining system stability." Enter

echo "✅ Deployment complete!"
echo ""
echo "📱 Connect with iTerm2:"
echo "tmux -CC attach -t agent-system-$MISSION_NAME"
echo ""
echo "📺 Standard terminal:"
echo "tmux attach -t agent-system-$MISSION_NAME"
echo ""
echo "👀 Quick progress check:"
echo "tmux capture-pane -t agent-system-$MISSION_NAME -S -10 -p"
echo ""
echo "⚠️ Remember: You must manually approve Claude startup in the tmux session"