#!/bin/bash

# Comprehensive branch cleanup script

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}🧹 COMPREHENSIVE BRANCH CLEANUP${NC}"
echo -e "${RED}================================${NC}\n"

# Count branches
TOTAL=$(git branch | wc -l | tr -d ' ')
echo -e "Total local branches: ${RED}$TOTAL${NC}"
echo -e "Current branch: ${GREEN}$(git branch --show-current)${NC}\n"

# Show branch age and activity
echo -e "${YELLOW}Analyzing branches...${NC}"

# Important branches to keep
KEEP_BRANCHES="main|master|develop|staging|production"

# Show branches by pattern
echo -e "\n${BLUE}Branch patterns:${NC}"
git branch | cut -c3- | cut -d'-' -f1 | sort | uniq -c | sort -rn | head -10

# Find old merged branches
echo -e "\n${BLUE}Finding branches already merged into main...${NC}"
MERGED=$(git branch --merged main | grep -vE "^(\*|  (main|master)$)" | wc -l | tr -d ' ')
echo -e "Branches already merged: ${GREEN}$MERGED${NC}"

# Find branches with no commits ahead of main
echo -e "\n${BLUE}Finding empty branches (no commits ahead of main)...${NC}"
EMPTY_COUNT=0
for branch in $(git branch | grep -vE "^\*|main$" | tr -d ' '); do
    AHEAD=$(git rev-list --count main..$branch 2>/dev/null || echo "0")
    if [[ "$AHEAD" == "0" ]]; then
        ((EMPTY_COUNT++))
    fi
done
echo -e "Empty branches: ${GREEN}$EMPTY_COUNT${NC}"

# Options menu
echo -e "\n${YELLOW}Cleanup Options:${NC}"
echo "1. Delete all merged branches (safe)"
echo "2. Delete all empty branches (no unique commits)"
echo "3. Delete old feature branches (interactive)"
echo "4. Nuclear option - keep only main"
echo "5. Show branch details and exit"
echo "6. Cancel"

read -p "Choose option (1-6): " option

case $option in
    1)
        echo -e "\n${YELLOW}Deleting merged branches...${NC}"
        git branch --merged main | grep -vE "^(\*|  (main|master)$)" | xargs -n 1 git branch -d
        ;;
    2)
        echo -e "\n${YELLOW}Deleting empty branches...${NC}"
        for branch in $(git branch | grep -vE "^\*|main$" | tr -d ' '); do
            AHEAD=$(git rev-list --count main..$branch 2>/dev/null || echo "0")
            if [[ "$AHEAD" == "0" ]]; then
                echo "Deleting empty branch: $branch"
                git branch -D "$branch" 2>/dev/null || echo "  Skipped (protected)"
            fi
        done
        ;;
    3)
        echo -e "\n${YELLOW}Interactive cleanup...${NC}"
        for branch in $(git branch | grep -vE "^\*|main$" | tr -d ' '); do
            echo -e "\n${BLUE}Branch: $branch${NC}"
            AHEAD=$(git rev-list --count main..$branch 2>/dev/null || echo "0")
            BEHIND=$(git rev-list --count $branch..main 2>/dev/null || echo "0")
            echo "  Commits ahead: $AHEAD, behind: $BEHIND"
            git log --oneline -n 3 main..$branch 2>/dev/null || echo "  No unique commits"
            read -p "Delete this branch? (y/n/q to quit): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git branch -D "$branch"
            elif [[ $REPLY =~ ^[Qq]$ ]]; then
                break
            fi
        done
        ;;
    4)
        echo -e "\n${RED}⚠️  NUCLEAR OPTION - Delete all branches except main${NC}"
        read -p "Are you ABSOLUTELY SURE? Type 'DELETE ALL': " confirm
        if [[ "$confirm" == "DELETE ALL" ]]; then
            git branch | grep -v "main" | xargs -n 1 git branch -D
        else
            echo "Cancelled"
        fi
        ;;
    5)
        echo -e "\n${BLUE}Branch details:${NC}"
        git branch -v | head -20
        echo -e "\n${YELLOW}Run script again to perform cleanup${NC}"
        ;;
    *)
        echo -e "${YELLOW}Cleanup cancelled${NC}"
        ;;
esac

# Final summary
echo -e "\n${BLUE}Final status:${NC}"
REMAINING=$(git branch | wc -l | tr -d ' ')
echo -e "Remaining branches: $REMAINING"
echo -e "Current branch: $(git branch --show-current)"