#!/bin/bash

# Smart Auto-Commit Script for ATLAS
# Analyzes changes and creates meaningful commit messages

# Configuration
COMMIT_INTERVAL=1800  # 30 minutes in seconds
PUSH_INTERVAL=3600    # 60 minutes in seconds
BRANCH_PREFIX="auto-backup"
LAST_PUSH_FILE="/tmp/.last_auto_push"
LOG_FILE="$HOME/.auto-commit.log"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo -e "${GREEN}[AUTO-COMMIT]${NC} $1"
}

analyze_changes() {
    # Get file statistics
    local changed_files=$(git status --porcelain | wc -l | tr -d ' ')
    local modified=$(git status --porcelain | grep -c "^ M")
    local added=$(git status --porcelain | grep -c "^??")
    local deleted=$(git status --porcelain | grep -c "^ D")
    
    # Get primary directories affected
    local dirs=$(git status --porcelain | awk '{print $2}' | xargs -I {} dirname {} | sort | uniq | head -3 | paste -sd, -)
    
    # Get file types changed
    local extensions=$(git status --porcelain | awk '{print $2}' | grep -E '\.[a-zA-Z]+$' | sed 's/.*\.//' | sort | uniq | paste -sd, -)
    
    # Build commit message
    local msg="auto: "
    
    # Add change summary
    if [ $changed_files -eq 0 ]; then
        echo ""
        return
    elif [ $changed_files -eq 1 ]; then
        # Single file - be specific
        local file=$(git status --porcelain | awk '{print $2}' | head -1)
        msg+="update $(basename $file)"
    else
        # Multiple files - summarize
        msg+="${changed_files} files"
        [ $modified -gt 0 ] && msg+=" (${modified}M"
        [ $added -gt 0 ] && msg+=",${added}A"
        [ $deleted -gt 0 ] && msg+=",${deleted}D"
        [ $modified -gt 0 ] || [ $added -gt 0 ] || [ $deleted -gt 0 ] && msg+=")"
    fi
    
    # Add context
    [ -n "$dirs" ] && msg+=" in $dirs"
    [ -n "$extensions" ] && msg+=" [${extensions}]"
    
    # Add work context if possible
    if git log -1 --oneline 2>/dev/null | grep -q "classifier"; then
        msg+=" - continuing classifier work"
    elif git log -1 --oneline 2>/dev/null | grep -q "email"; then
        msg+=" - email system updates"
    elif git log -1 --oneline 2>/dev/null | grep -q "agent"; then
        msg+=" - agent system work"
    fi
    
    echo "$msg"
}

should_commit() {
    # Check if there are changes
    if ! git status --porcelain | grep -q .; then
        return 1
    fi
    
    # Don't commit if in middle of merge/rebase
    if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] || [ -f .git/MERGE_HEAD ]; then
        log "Skipping - merge/rebase in progress"
        return 1
    fi
    
    return 0
}

should_push() {
    # Check if enough time has passed since last push
    if [ -f "$LAST_PUSH_FILE" ]; then
        local last_push=$(cat "$LAST_PUSH_FILE")
        local now=$(date +%s)
        local diff=$((now - last_push))
        
        if [ $diff -lt $PUSH_INTERVAL ]; then
            return 1
        fi
    fi
    
    # Check if we have commits to push
    if ! git status | grep -q "ahead"; then
        return 1
    fi
    
    return 0
}

auto_commit() {
    if ! should_commit; then
        return
    fi
    
    local commit_msg=$(analyze_changes)
    if [ -z "$commit_msg" ]; then
        return
    fi
    
    log "Committing: $commit_msg"
    
    # Stage all changes
    git add -A
    
    # Commit with our analyzed message
    git commit -m "$commit_msg" --quiet
    
    if [ $? -eq 0 ]; then
        log "✓ Committed successfully"
        
        # Check if we should push
        if should_push; then
            log "Pushing to origin..."
            git push origin HEAD --quiet
            if [ $? -eq 0 ]; then
                date +%s > "$LAST_PUSH_FILE"
                log "✓ Pushed successfully"
            else
                log "✗ Push failed - will retry later"
            fi
        fi
    else
        log "✗ Commit failed"
    fi
}

# Single run mode
if [ "$1" = "--once" ]; then
    auto_commit
    exit 0
fi

# Daemon mode
log "Starting auto-commit daemon (commit every 30m, push every 60m)"
log "Watching: $(pwd)"

# Set up clean exit
trap 'log "Stopping auto-commit daemon"; exit 0' SIGTERM SIGINT

# Main loop
while true; do
    auto_commit
    sleep $COMMIT_INTERVAL
done