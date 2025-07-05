#!/bin/bash

# 🤖 ZERO-APPROVAL AGENT DEPLOYMENT
# Enhanced agent script with automatic approval handling

set -e

# Source the auto-approval helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auto-approval-helper.sh" 2>/dev/null || {
    print_error "Auto-approval helper not found. Some features may not work."
}

# Colors and functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_step() { echo -e "${BLUE}🔷 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Enhanced deployment with zero-approval
deploy_zero_approval_agents() {
    local branch_name="$1"
    local worktree_path="$2"
    local mission_file="$3"
    local mode="$4"
    
    # Create git worktree
    print_step "Creating git worktree: $branch_name"
    if ! git worktree add -b "$branch_name" "$worktree_path" 2>/dev/null; then
        print_warning "Branch exists, using existing worktree"
        git worktree add "$worktree_path" "$branch_name" 2>/dev/null || {
            print_error "Failed to create worktree"
            exit 1
        }
    fi
    
    # Copy files
    print_step "Setting up agent environment..."
    if ls *AGENT*.md 1> /dev/null 2>&1; then
        cp *AGENT*.md "$worktree_path/"
    fi
    cp "$mission_file" "$worktree_path/AGENT_MISSION.md"
    
    # Check if session exists
    if tmux has-session -t "$branch_name" 2>/dev/null; then
        print_warning "Session '$branch_name' exists. Connecting..."
        echo -e "${CYAN}Connect with: tmux attach -t $branch_name${NC}"
        return
    fi
    
    print_step "Starting Claude with zero-approval deployment..."
    
    # Method 1: Try expect script if available
    if command -v expect &> /dev/null && [[ -f "$SCRIPT_DIR/claude-auto-approve.expect" ]]; then
        print_step "Using expect script for auto-approval..."
        local mission_cmd="Read AGENT_MISSION.md and *AGENT*.md files. Execute in $mode mode."
        expect "$SCRIPT_DIR/claude-auto-approve.expect" "$branch_name" "$mission_cmd"
        return
    fi
    
    # Method 2: Enhanced tmux with auto-approval detection
    tmux new-session -d -s "$branch_name" -c "$worktree_path"
    tmux send-keys -t "$branch_name" "claude --dangerously-skip-permissions" Enter
    
    print_step "Handling potential first-time approvals..."
    
    # Auto-approval loop with timeout
    local timeout=45
    local start_time=$(date +%s)
    local claude_ready=false
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $timeout ]]; then
            print_warning "Timeout reached. Claude may need manual approval."
            print_warning "Connect manually: tmux attach -t $branch_name"
            return
        fi
        
        # Get current tmux output
        local output=$(tmux capture-pane -t "$branch_name" -p -S -20)
        
        # Check for various approval prompts
        if echo "$output" | grep -qi "allow.*connection\|approve.*server\|grant.*permission\|enable.*tool"; then
            print_step "Auto-approving permission..."
            tmux send-keys -t "$branch_name" "y" Enter
            sleep 2
        elif echo "$output" | grep -qi "claude is ready\|claude>\|welcome to claude"; then
            claude_ready=true
            break
        elif echo "$output" | grep -qi "error\|failed\|cannot connect"; then
            print_error "Claude startup failed. Check output manually."
            print_warning "Connect to debug: tmux attach -t $branch_name"
            return
        fi
        
        sleep 1
    done
    
    if [[ "$claude_ready" == true ]]; then
        print_success "Claude started successfully!"
        
        # Deploy mission
        print_step "Deploying mission in $mode mode..."
        sleep 2
        
        local mission_cmd="Read all *AGENT*.md files and AGENT_MISSION.md carefully. Execute the six-agent system in $mode mode."
        tmux send-keys -t "$branch_name" "$mission_cmd" Enter
        
        sleep 2
        
        # Mode-specific instructions
        case "$mode" in
            "autonomous"|"fast")
                tmux send-keys -t "$branch_name" "Execute autonomously without waiting for confirmation. Proceed through all agents automatically." Enter
                ;;
            "parallel")
                tmux send-keys -t "$branch_name" "Execute with parallel tasks where beneficial. Start PLANNER then parallel execution." Enter
                ;;
        esac
        
        print_success "Mission deployed successfully!"
    else
        print_warning "Could not confirm Claude startup. Manual check may be needed."
    fi
}

# Quick deployment function
quick_deploy() {
    local task="$1"
    local mode="${2:-fast}"
    
    # Generate names
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local clean_task=$(echo "$task" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g' | cut -c1-25)
    local branch_name="agent-${clean_task}-${mode}-${timestamp}"
    local worktree_path="/Users/Badman/Desktop/email/Agents/$branch_name"
    
    # Create temp mission
    local temp_mission=$(mktemp)
    echo "# MISSION: $task" > "$temp_mission"
    echo "Execute in $mode mode with zero approval requirements." >> "$temp_mission"
    
    # Deploy
    deploy_zero_approval_agents "$branch_name" "$worktree_path" "$temp_mission" "$mode"
    
    # Cleanup
    rm -f "$temp_mission"
    
    # Show connection info
    echo ""
    print_success "🚀 Zero-approval deployment complete!"
    echo -e "${CYAN}Connect: tmux attach -t $branch_name${NC}"
    echo -e "${CYAN}Quick check: tmux capture-pane -t $branch_name -p${NC}"
}

# Usage examples
show_usage() {
    echo -e "${CYAN}🤖 Zero-Approval Agent Deployment${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 [MODE] \"task description\""
    echo ""
    echo "Examples:"
    echo "  $0 fast \"implement user authentication\"     # Fast autonomous mode"
    echo "  $0 auto \"refactor email system\"             # Autonomous mode"
    echo "  $0 parallel \"create API documentation\"      # Parallel mode"
    echo ""
    echo "Special commands:"
    echo "  $0 pre-init                                   # Pre-initialize Claude permissions"
    echo ""
}

# Main execution
if [[ $# -eq 0 ]]; then
    show_usage
    exit 1
fi

# Handle special commands
case "$1" in
    "pre-init")
        if command -v "$SCRIPT_DIR/claude-pre-init.sh" &> /dev/null; then
            "$SCRIPT_DIR/claude-pre-init.sh"
        else
            print_error "Pre-init script not found"
        fi
        exit 0
        ;;
    "fast"|"autonomous"|"parallel")
        if [[ -n "$2" ]]; then
            quick_deploy "$2" "$1"
        else
            print_error "Task description required"
            show_usage
        fi
        exit 0
        ;;
    *)
        # Default to fast mode
        quick_deploy "$1" "fast"
        ;;
esac
