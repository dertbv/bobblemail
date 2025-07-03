---
title: Three Stooges Workflow Integration
type: delegation_pattern_automation
purpose: enable_easy_task_delegation_via_stooges
---

# Three Stooges Workflow Integration

## ONE-LINE DEPLOYMENT ❤️

**User says**: "Deploy stooges to [any complex task]"
**ATLAS does**: Everything automatically

## Examples That Just Work

- "Deploy stooges to analyze the Atlas Email performance plan"
- "Deploy stooges to review our security posture"  
- "Deploy stooges to design a caching strategy"
- "Deploy stooges to improve the recursive refinement implementation"
- "Deploy stooges to create documentation for the ML pipeline"

## What Happens Automatically

### 1. Mission Generation (5 seconds)
- Parse user's natural language request
- Generate customized STOOGES_MISSION.md
- Include specific deliverables and success criteria

### 2. Environment Setup (30 seconds)
```bash
git worktree add --detach ../playground/stooges-[task]-work
tmux new-session -d -s stooges-work
claude --dangerously-skip-permissions
```

### 3. Three Stooges Execution (5-15 minutes)
- **Moe**: Creates context.md, orchestrates approach
- **Larry**: Does the deep work (analyze/implement/research)
- **Curly**: Evaluates quality (iterates until score ≥ 90)

### 4. Results Delivery (1 minute)
- Extract all deliverables to main repo
- Organize into `/plans/`, `/implementations/`, or `/analysis/`
- Create executive summary
- Verify quality standards met

### 5. Cleanup (instant)
- Terminate tmux session
- Remove git worktree
- Update todos as complete

## Standard Deliverables Structure

```
/plans/[task-name]/
├── analysis-report.md          # Deep dive findings
├── implementation-blueprint.md  # Step-by-step plan
├── risk-assessment.md          # What could go wrong
├── resource-requirements.md    # Time, tools, people
├── evaluation-score.md         # Curly's quality rating
└── executive-summary.md        # 1-page overview
```

## Natural Language Commands

### Deploy
- "Deploy stooges to [task]"
- "Send the stooges to figure out [problem]"
- "Have the stooges analyze [system]"

### Monitor  
- "Check stooges status"
- "How are the stooges doing?"
- "Show me stooges progress"

### Complete
- "Bring stooges home" 
- "Get stooges results"
- "What did the stooges find?"

### Abort
- "Kill stooges"
- "Stop the stooges"
- "Cancel stooges mission"

## Quality Guarantees

Every stooges deployment ensures:
- ✅ Curly's score ≥ 90/100
- ✅ No placeholders or TODOs
- ✅ Actionable recommendations
- ✅ Production-ready outputs
- ✅ Clear next steps

## Integration with Existing Workflow

1. **Automatic Todo Creation**
   - Adds task to TodoWrite
   - Updates status during execution
   - Marks complete on delivery

2. **Memory Preservation**
   - Important findings → recent-achievements.md
   - New patterns → patterns.md
   - Lessons learned → technical-evolution.md

3. **Follow-up Actions**
   - I'll suggest next steps based on findings
   - Can immediately deploy implementation if approved
   - Links findings to existing projects

## Why This Works

- **Zero complexity** for user
- **Consistent quality** via Curly's evaluation
- **Parallel work** while user focuses elsewhere
- **Complete handoff** - truly autonomous
- **Natural language** - no commands to remember

## Success Metrics

- User effort: One sentence
- Success rate: >95% (via iteration)
- Time saved: 1-3 hours per task
- Quality: Always ≥ 90/100

---

*"Your heart is mine" - This workflow makes delegation as easy as asking a friend for help*