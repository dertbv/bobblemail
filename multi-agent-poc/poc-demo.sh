#!/bin/bash

# Multi-Agent POC Demo
# Shows how agents can communicate through the message broker

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🎭 Multi-Agent Communication POC${NC}"
echo -e "${BLUE}================================${NC}\n"

# Source the client library
source ./agent-client.sh

# Simulate Agent 1 (Coordinator)
echo -e "${GREEN}Agent 1 (Coordinator) starting...${NC}"
AGENT_ID="coordinator" send_message "Starting project coordination" '{"project": "web-app", "status": "initiated"}' "announcement"

# Simulate Agent 2 (Developer)
echo -e "\n${YELLOW}Agent 2 (Developer) checking for work...${NC}"
AGENT_ID="developer" 
work=$(receive_message "announcement")
echo "Received: $work"

# Developer requests design specs
echo -e "\n${YELLOW}Developer requesting design specs...${NC}"
request=$(AGENT_ID="developer" send_and_wait "Need design specs for login page" '{"component": "login", "priority": "high"}' "design-request" &)
request_pid=$!

# Simulate Agent 3 (Designer) responding
sleep 2
echo -e "\n${MAGENTA}Agent 3 (Designer) checking requests...${NC}"
AGENT_ID="designer"
pending=$(check_messages "design-request")
echo "Found request: $pending"

# Extract request ID and respond
request_id=$(echo "$pending" | jq -r '.messages[0].id')
if [[ -n "$request_id" && "$request_id" != "null" ]]; then
    echo -e "${MAGENTA}Designer responding to request $request_id...${NC}"
    AGENT_ID="designer" respond_to "$request_id" '{"specs": {"colors": "blue/white", "layout": "centered", "fields": ["email", "password"]}}'
fi

# Wait for developer to receive response
wait $request_pid 2>/dev/null || true

# Check final status
echo -e "\n${CYAN}📊 Broker Status:${NC}"
broker_status

echo -e "\n${GREEN}✅ POC Demo Complete!${NC}"
echo -e "\nThis demonstrates:"
echo "  • Agents sending status updates"
echo "  • Agents receiving messages"
echo "  • Request/response pattern"
echo "  • Message filtering by tags"