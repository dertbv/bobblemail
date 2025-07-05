#!/bin/bash

# 🤖 ZERO-APPROVAL AGENT DEPLOYMENT
# Handles first-time approvals automatically

deploy_with_auto_approval() {
    local branch_name="$1"
    local mission_command="$2"
    
    print_step "Starting Claude with auto-approval handling..."
    
    # Start tmux session
    tmux new-session -d -s "$branch_name" -c "$worktree_path"
    
    # Start Claude with expect script for auto-approval
    tmux send-keys -t "$branch_name" "claude --dangerously-skip-permissions" Enter
    
    # Wait for Claude to initialize
    sleep 3
    
    # Handle potential first-time approvals with timeout
    local approval_timeout=30
    local start_time=$(date +%s)
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $approval_timeout ]]; then
            print_warning "Timeout waiting for Claude initialization"
            break
        fi
        
        # Capture current tmux output
        local output=$(tmux capture-pane -t "$branch_name" -p)
        
        # Check for approval prompts and auto-approve
        if echo "$output" | grep -q "Allow.*connection\|Approve.*server\|Grant.*permission"; then
            print_step "Auto-approving MCP server connection..."
            tmux send-keys -t "$branch_name" "y" Enter
            sleep 2
        elif echo "$output" | grep -q "Allow.*tool\|Enable.*tool"; then
            print_step "Auto-approving tool permissions..."
            tmux send-keys -t "$branch_name" "y" Enter
            sleep 2
        elif echo "$output" | grep -q "Claude is ready\|claude>"; then
            print_success "Claude initialized successfully"
            break
        fi
        
        sleep 1
    done
    
    # Deploy the mission
    tmux send-keys -t "$branch_name" "$mission_command" Enter
}
