#!/bin/bash
# Auto Git Commit & Push Script

# Configuration
INTERVAL_MINUTES=${1:-30}  # Default: 30 minutes
REPO_PATH=${2:-.}          # Default: current directory

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if we're in a git repo
check_git_repo() {
    if [ ! -d "$REPO_PATH/.git" ]; then
        echo -e "${RED}Error: Not a git repository${NC}"
        exit 1
    fi
}

# Function to commit and push
auto_commit_push() {
    cd "$REPO_PATH" || exit 1
    
    # Check if there are changes
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] No changes to commit${NC}"
        return
    fi
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    COMMIT_MSG="Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    
    # Push to remote
    if git push; then
        echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Successfully committed and pushed${NC}"
    else
        echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] Push failed - changes committed locally${NC}"
    fi
}

# Main execution
main() {
    check_git_repo
    
    echo "Auto-commit started for: $REPO_PATH"
    echo "Interval: $INTERVAL_MINUTES minutes"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Run forever
    while true; do
        echo "=========================================="
        auto_commit_push
        echo ""
        echo "Next check in $INTERVAL_MINUTES minutes..."
        sleep $((INTERVAL_MINUTES * 60))
    done
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Auto-commit stopped by user${NC}"; exit 0' INT

# Run main function
main