#!/bin/bash

# Three Agent Communication Missions

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🎭 Deploying Three Agent Communication Missions${NC}\n"

# Agent A - The Coordinator/Leader
AGENT_A_MISSION='You are Agent A - The Coordinator

Your mission: Lead a team to build a simple calculator app.

Communication endpoint: http://localhost:3000

1. Announce yourself:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-a", "description": "Coordinator Agent A ready to lead", "content": {"role": "coordinator", "project": "calculator-app"}, "tags": ["announcement", "leader"]}'"'"'

2. Send tasks to other agents:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-a", "description": "Task assignments", "content": {"agent-b": "Build calculator logic", "agent-c": "Create UI design"}, "tags": ["task", "assignment"]}'"'"'

3. Check for status updates:
curl -X POST http://localhost:3000/check -H "Content-Type: application/json" -d '"'"'{"tags": ["status", "update"]}'"'"'

Start by announcing yourself and assigning tasks!'

# Agent B - The Developer
AGENT_B_MISSION='You are Agent B - The Developer

Your mission: Implement features as assigned by the coordinator.

Communication endpoint: http://localhost:3000

1. Announce yourself:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-b", "description": "Developer Agent B ready to code", "content": {"role": "developer", "skills": ["javascript", "python"]}, "tags": ["announcement", "developer"]}'"'"'

2. Check for task assignments:
curl -X POST http://localhost:3000/receive -H "Content-Type: application/json" -d '"'"'{"tags": ["task", "assignment"]}'"'"'

3. Send progress updates:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-b", "description": "Development progress", "content": {"status": "working on calculator logic", "progress": 50}, "tags": ["status", "update"]}'"'"'

4. Ask Agent C for design specs:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-b", "description": "Need UI specs", "content": {"request": "What colors and layout for calculator?"}, "tags": ["question", "design"]}'"'"'

Start by announcing yourself!'

# Agent C - The Designer
AGENT_C_MISSION='You are Agent C - The Designer

Your mission: Create UI designs and respond to design questions.

Communication endpoint: http://localhost:3000

1. Announce yourself:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-c", "description": "Designer Agent C ready to design", "content": {"role": "designer", "tools": ["figma", "css"]}, "tags": ["announcement", "designer"]}'"'"'

2. Check for design requests:
curl -X POST http://localhost:3000/check -H "Content-Type: application/json" -d '"'"'{"tags": ["question", "design"]}'"'"'

3. Send design specs:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-c", "description": "Calculator UI design", "content": {"colors": "blue and white", "layout": "grid", "buttons": "rounded"}, "tags": ["design", "specs"]}'"'"'

4. Update coordinator on progress:
curl -X POST http://localhost:3000/send -H "Content-Type: application/json" -d '"'"'{"agent_id": "agent-c", "description": "Design progress", "content": {"status": "mockup complete", "progress": 75}, "tags": ["status", "update"]}'"'"'

Start by announcing yourself!'

# Deploy missions
echo -e "${YELLOW}Sending mission to Agent A (Coordinator)...${NC}"
tmux send-keys -t claudesquad_a "$AGENT_A_MISSION" Enter

echo -e "${MAGENTA}Sending mission to Agent B (Developer)...${NC}"
tmux send-keys -t claudesquad_b "$AGENT_B_MISSION" Enter

echo -e "${GREEN}Sending mission to Agent C (Designer)...${NC}"
tmux send-keys -t claudesquad_c "$AGENT_C_MISSION" Enter

echo -e "\n${BLUE}✅ Missions deployed!${NC}"
echo -e "\nMonitor communication:"
echo "  Dashboard: open /Users/Badman/Desktop/email/multi-agent-poc/monitor-dashboard.html"
echo "  Status:    curl -s http://localhost:3000/status | jq"
echo ""
echo "View agents:"
echo "  tmux attach -t claudesquad_a"
echo "  tmux attach -t claudesquad_b"
echo "  tmux attach -t claudesquad_c"