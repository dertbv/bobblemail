#!/bin/bash

# Aggressive cleanup - remove ALL agent and stooge branches

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}⚠️  AGGRESSIVE GIT CLEANUP ⚠️${NC}"
echo -e "${RED}This will delete ALL agent and stooge branches!${NC}\n"

# List all branches that will be deleted
echo -e "${YELLOW}Branches to be deleted:${NC}"
git branch | grep -E "(agent-|stooge)" | cat
echo ""

TOTAL=$(git branch | grep -E "(agent-|stooge)" | wc -l | tr -d ' ')
echo -e "Total branches to delete: ${RED}$TOTAL${NC}"
echo ""

read -p "Are you SURE you want to delete all these branches? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 1
fi

# Delete all agent and stooge branches
git branch | grep -E "(agent-|stooge)" | while read branch; do
    echo -e "Deleting: $branch"
    git branch -D "$branch"
done

# Clean up any stale worktrees
git worktree prune

echo -e "\n${GREEN}✅ All agent/stooge branches deleted!${NC}"
git branch | head -10