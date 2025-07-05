#!/bin/bash

# Inject communication missions into Claude Squad agents

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎯 Injecting Communication Missions${NC}\n"

# Agent 1 mission
AGENT1_MISSION=$(cat << 'EOF'
You are Agent 1 (Coordinator) in a multi-agent system. 

Your role: Coordinate the team to build a simple web application.

You can communicate with other agents using curl commands to http://localhost:3000

First, announce yourself:
curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "coordinator",
    "description": "Coordinator online and ready",
    "content": {"role": "coordinator", "ready": true},
    "tags": ["announcement", "status"]
  }'

Then check who else is online:
curl -X POST http://localhost:3000/check \
  -H "Content-Type: application/json" \
  -d '{"tags": ["announcement"]}'

Start coordinating by sending tasks to other agents.
EOF
)

# Agent 2 mission
AGENT2_MISSION=$(cat << 'EOF'
You are Agent 2 (Developer) in a multi-agent system.

Your role: Implement code based on coordinator instructions.

You can communicate with other agents using curl commands to http://localhost:3000

First, announce yourself:
curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "developer",
    "description": "Developer online and ready",
    "content": {"role": "developer", "skills": ["python", "javascript"]},
    "tags": ["announcement", "status"]
  }'

Then check for work:
curl -X POST http://localhost:3000/receive \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "developer", "tags": ["task", "work"]}'

Listen for coordinator instructions and implement requested features.
EOF
)

# Send to first agent
echo -e "${YELLOW}Injecting mission to claudesquad_test...${NC}"
tmux send-keys -t claudesquad_test "$AGENT1_MISSION" Enter

# Send to second agent
echo -e "${YELLOW}Injecting mission to claudesquad_test2...${NC}"
tmux send-keys -t claudesquad_test2 "$AGENT2_MISSION" Enter

echo -e "\n${GREEN}✅ Missions injected!${NC}"
echo -e "\nMonitor communication:"
echo "  curl -s http://localhost:3000/status | jq"
echo ""
echo "View agent sessions:"
echo "  tmux attach -t claudesquad_test"
echo "  tmux attach -t claudesquad_test2"