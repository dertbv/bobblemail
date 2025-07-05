#!/bin/bash

# Multi-Agent Orchestrator POC
# Controls multiple Claude agents via Claude Squad + MCP

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
MCP_PORT=${MCP_PORT:-3000}
AGENT_COUNT=${1:-3}
MISSION=${2:-"Test mission"}
SQUAD_BINARY="$HOME/.local/bin/cs"

echo -e "${BLUE}🎭 Multi-Agent Orchestrator POC${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    if [[ ! -f "$SQUAD_BINARY" ]]; then
        echo -e "${RED}❌ Claude Squad not found at $SQUAD_BINARY${NC}"
        exit 1
    fi
    
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}❌ tmux not installed${NC}"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All dependencies found${NC}"
}

# Start MCP communication server
start_mcp_server() {
    echo -e "\n${YELLOW}Starting MCP communication server...${NC}"
    
    # Check if already running
    if lsof -Pi :$MCP_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ MCP server already running on port $MCP_PORT${NC}"
    else
        # Start in background tmux session
        tmux new-session -d -s mcp-server "cd mcp-agent-communication && npm start"
        sleep 3
        echo -e "${GREEN}✅ MCP server started on port $MCP_PORT${NC}"
    fi
}

# Create agent mission files
create_agent_missions() {
    echo -e "\n${YELLOW}Creating agent missions...${NC}"
    
    mkdir -p missions
    
    for i in $(seq 1 $AGENT_COUNT); do
        cat > missions/agent-$i.md << EOF
# Agent $i Mission

## Identity
You are Agent $i in a multi-agent system.

## Communication
You can communicate with other agents using MCP tools:
- send_message: Broadcast updates
- wait_for_message: Wait for specific messages
- check_messages: See what others are doing

## Mission
$MISSION

## Your Specific Role
$(get_agent_role $i)

## Coordination Protocol
1. Send status update when you start
2. Check for messages from other agents
3. Coordinate on shared tasks
4. Report completion status
EOF
        echo -e "${GREEN}✅ Created mission for Agent $i${NC}"
    done
}

# Assign roles based on agent number
get_agent_role() {
    case $1 in
        1) echo "You are the COORDINATOR. Organize the other agents." ;;
        2) echo "You are the RESEARCHER. Gather information needed." ;;
        3) echo "You are the IMPLEMENTER. Write the actual code." ;;
        4) echo "You are the TESTER. Verify everything works." ;;
        5) echo "You are the DOCUMENTER. Create documentation." ;;
        *) echo "You are AGENT $1. Support the team as needed." ;;
    esac
}

# Launch agents via Claude Squad
launch_agents() {
    echo -e "\n${YELLOW}Launching $AGENT_COUNT agents...${NC}"
    
    # Create expect script to automate Claude Squad
    cat > squad-automation.exp << 'EOF'
#!/usr/bin/expect -f

set agent_count [lindex $argv 0]
set timeout 5

spawn ~/.local/bin/cs

# Wait for UI to load
sleep 2

# Create agents
for {set i 1} {$i <= $agent_count} {incr i} {
    send "n"
    sleep 1
}

# Keep running
interact
EOF
    
    chmod +x squad-automation.exp
    
    # Launch Claude Squad with automation
    tmux new-session -d -s squad-orchestrator "./squad-automation.exp $AGENT_COUNT"
    
    echo -e "${GREEN}✅ Claude Squad launched with $AGENT_COUNT agents${NC}"
}

# Monitor agent status
monitor_agents() {
    echo -e "\n${YELLOW}Monitoring agent status...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Get Claude Squad sessions
    tmux list-sessions | grep claudesquad_ | while read -r session; do
        session_name=$(echo "$session" | cut -d: -f1)
        echo -e "${GREEN}📍 Found session: $session_name${NC}"
    done
}

# Main execution
main() {
    check_dependencies
    start_mcp_server
    create_agent_missions
    launch_agents
    monitor_agents
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🚀 Multi-Agent System Deployed!${NC}"
    echo -e "\n${YELLOW}Commands:${NC}"
    echo "  Monitor MCP:     tmux attach -t mcp-server"
    echo "  View Squad:      tmux attach -t squad-orchestrator"
    echo "  Check agents:    tmux list-sessions | grep claudesquad_"
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "  1. Inject missions into each agent"
    echo "  2. Connect agents to MCP server"
    echo "  3. Watch them collaborate!"
}

# Handle cleanup
trap cleanup EXIT
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    rm -f squad-automation.exp
}

# Run main
main