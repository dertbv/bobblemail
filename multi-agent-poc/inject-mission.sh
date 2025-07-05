#!/bin/bash

# Inject missions into waiting Claude agents

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎯 Mission Injection Script${NC}"

# Find all Claude Squad sessions
inject_missions() {
    local sessions=$(tmux list-sessions 2>/dev/null | grep claudesquad_ | cut -d: -f1)
    local count=1
    
    if [[ -z "$sessions" ]]; then
        echo -e "${YELLOW}No Claude Squad sessions found${NC}"
        return
    fi
    
    echo "$sessions" | while read -r session; do
        echo -e "\n${YELLOW}Processing: $session${NC}"
        
        # Check if at trust prompt
        local content=$(tmux capture-pane -t "$session" -p | tail -5)
        
        if echo "$content" | grep -q "Yes, proceed"; then
            echo -e "${GREEN}✓ Found trust prompt${NC}"
            
            # Send option 1 to trust the folder
            tmux send-keys -t "$session" "1" Enter
            sleep 2
            
            # Now inject the mission
            if [[ -f "missions/agent-$count.md" ]]; then
                echo -e "${GREEN}✓ Injecting mission for Agent $count${NC}"
                
                # Read mission file and send it
                local mission=$(cat "missions/agent-$count.md")
                
                # Send mission line by line
                echo "$mission" | while IFS= read -r line; do
                    tmux send-keys -t "$session" "$line" Enter
                done
                
                # Send completion marker
                tmux send-keys -t "$session" Enter
                tmux send-keys -t "$session" "# Mission injected. Begin work." Enter
            fi
        else
            echo -e "${YELLOW}⚠ Not at trust prompt, checking status...${NC}"
            echo "$content"
        fi
        
        ((count++))
    done
}

# Auto-accept mode for agents
enable_auto_accept() {
    echo -e "\n${YELLOW}Enabling auto-accept mode...${NC}"
    
    local sessions=$(tmux list-sessions 2>/dev/null | grep claudesquad_ | cut -d: -f1)
    
    echo "$sessions" | while read -r session; do
        # Send --dangerously-skip-permissions equivalent
        tmux send-keys -t "$session" C-c  # Cancel current
        sleep 1
        tmux send-keys -t "$session" "claude --dangerously-skip-permissions" Enter
        echo -e "${GREEN}✓ Enabled auto mode for $session${NC}"
    done
}

# Main
case "${1:-inject}" in
    inject)
        inject_missions
        ;;
    auto)
        enable_auto_accept
        ;;
    both)
        inject_missions
        enable_auto_accept
        ;;
    *)
        echo "Usage: $0 [inject|auto|both]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✅ Mission injection complete!${NC}"