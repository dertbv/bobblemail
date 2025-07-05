# Deploy Three Stooges Command

Deploy the Three Stooges (Moe, Larry, Curly) for fast parallel investigation and analysis.

## Usage

```bash
deploy-stooges [mission-file]
```

## Examples

```bash
# Deploy with specific mission
deploy-stooges preview-investigation.md

# Deploy with verbal mission
deploy-stooges
# Then describe mission in tmux
```

## Implementation Script

```bash
#!/bin/bash
# deploy-stooges.sh

MISSION_FILE=$1
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH_NAME="stooges-$TIMESTAMP"
WORKTREE_PATH="stooges-work-$TIMESTAMP"

# Create worktree
git worktree add -b $BRANCH_NAME $WORKTREE_PATH

# Copy stooges framework
cp Agents/stooges.md $WORKTREE_PATH/
if [ -f "$MISSION_FILE" ]; then
  cp $MISSION_FILE $WORKTREE_PATH/MISSION.md
fi

# Create tmux session
tmux new-session -d -s $BRANCH_NAME -c $WORKTREE_PATH
tmux send-keys -t $BRANCH_NAME "claude --dangerously-skip-permissions" Enter
sleep 3

if [ -f "$MISSION_FILE" ]; then
  tmux send-keys -t $BRANCH_NAME "cat MISSION.md && echo 'Deploy the Three Stooges as described in stooges.md'" Enter
else
  tmux send-keys -t $BRANCH_NAME "echo 'Three Stooges ready. Please provide mission.'" Enter
fi

echo "🎭 Three Stooges deployed!"
echo "Connect with: tmux -CC attach -t $BRANCH_NAME"
echo "Quick check: tmux capture-pane -t $BRANCH_NAME -S -10 -p"
```

## What They Do

- **Moe (Orchestrator)**: Manages the investigation, coordinates the team
- **Larry (Specialist)**: Deep technical analysis, finds root causes  
- **Curly (Evaluator)**: Quality control, numeric scoring (0-100)

## Best For

- Quick investigations
- Parallel analysis 
- Finding root causes
- Creative problem solving
- When you need results FAST

## Bringing Them Home

```bash
# Copy their work
cp stooges-work-*/outputs/* ./DOCS/

# Remove worktree
git worktree remove stooges-work-* --force

# End session
tmux kill-session -t stooges-*
```