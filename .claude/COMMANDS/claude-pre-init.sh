#!/bin/bash

# 🔧 CLAUDE PRE-INITIALIZATION
# Run this once to handle all first-time approvals

pre_initialize_claude() {
    print_step "Pre-initializing Claude with all permissions..."
    
    # Create temporary session for initialization
    local init_session="claude-init-$(date +%s)"
    
    # Start Claude in background
    tmux new-session -d -s "$init_session"
    tmux send-keys -t "$init_session" "claude --dangerously-skip-permissions" Enter
    
    # Wait and auto-approve everything
    sleep 5
    
    # Check for prompts and approve
    local max_attempts=10
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        local output=$(tmux capture-pane -t "$init_session" -p)
        
        if echo "$output" | grep -q "Allow\|Approve\|Grant\|Enable"; then
            print_step "Auto-approving permission request..."
            tmux send-keys -t "$init_session" "y" Enter
            sleep 2
        elif echo "$output" | grep -q "claude>"; then
            print_success "Claude pre-initialization complete!"
            break
        fi
        
        ((attempt++))
        sleep 2
    done
    
    # Test a simple command to ensure everything works
    tmux send-keys -t "$init_session" "echo 'Pre-initialization test successful'" Enter
    sleep 2
    
    # Clean up
    tmux kill-session -t "$init_session" 2>/dev/null
    
    print_success "Claude is now pre-configured for zero-approval deployment!"
}

# Run pre-initialization if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    source "$(dirname "$0")/auto-approval-helper.sh" 2>/dev/null || {
        # Define print functions if not available
        print_step() { echo "🔧 $1"; }
        print_success() { echo "✅ $1"; }
        print_error() { echo "❌ $1"; }
    }
    
    echo "🔧 Claude Pre-Initialization Tool"
    echo ""
    echo "This will handle all first-time approvals for Claude CLI."
    echo "Run this once, then use your deployment scripts normally."
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pre_initialize_claude
    else
        echo "Pre-initialization cancelled."
        exit 0
    fi
fi
