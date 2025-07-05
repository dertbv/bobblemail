#!/bin/bash

# Git cleanup script - remove old agent and stooge branches

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Git Cleanup Script${NC}"
echo -e "${BLUE}=====================${NC}\n"

# Safety check
echo -e "${YELLOW}⚠️  This will delete many branches!${NC}"
echo -e "Current branch: $(git branch --show-current)"
echo ""

# Count branches to clean
AGENT_BRANCHES=$(git branch | grep -E "(agent-|stooge)" | wc -l | tr -d ' ')
echo -e "Found ${RED}$AGENT_BRANCHES${NC} agent/stooge branches to potentially clean"
echo ""

echo "Branches that will be kept:"
echo "  - main"
echo "  - Current work branches you're actively using"
echo ""

read -p "Do you want to see the list of branches that will be deleted? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Branches to be deleted:${NC}"
    git branch | grep -E "(agent-test-|stooges-test-|stooges-hello-|agent-system-preview)" | cat
    echo ""
fi

read -p "Proceed with cleanup? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Cleanup cancelled${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Starting cleanup...${NC}"

# Remove test branches
echo -e "\n${BLUE}Removing test branches...${NC}"
git branch | grep -E "(agent-test-|stooges-test-|stooges-hello-)" | while read branch; do
    echo -e "  Deleting: $branch"
    git branch -D "$branch" 2>/dev/null || echo "    Already deleted or protected"
done

# Remove old investigation branches
echo -e "\n${BLUE}Removing old investigation branches...${NC}"
git branch | grep -E "(preview-investigation-stooges|geographic-stooges-investigation)" | while read branch; do
    echo -e "  Deleting: $branch"
    git branch -D "$branch" 2>/dev/null || echo "    Already deleted or protected"
done

# Check for any remaining worktrees
echo -e "\n${BLUE}Checking for stale worktrees...${NC}"
git worktree prune
echo -e "${GREEN}✓ Worktrees pruned${NC}"

# Summary
echo -e "\n${BLUE}Summary:${NC}"
REMAINING=$(git branch | grep -E "(agent-|stooge)" | wc -l | tr -d ' ')
echo -e "  Remaining agent/stooge branches: $REMAINING"
echo -e "  Current branch: $(git branch --show-current)"
echo ""

echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "To see remaining branches: git branch | grep -E '(agent-|stooge)'"
echo "To delete a specific branch: git branch -D branch-name"