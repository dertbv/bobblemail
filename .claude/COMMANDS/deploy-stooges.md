# 🎭 THREE STOOGES DEPLOYMENT TEMPLATE

## SIMPLE ONE-LINER DEPLOYMENT

### Quick Deploy Format:
```
Deploy stooges to [TASK DESCRIPTION]
```

### Examples:
- "Deploy stooges to analyze the Atlas Email performance plan"
- "Deploy stooges to review and improve the recursive refinement implementation"
- "Deploy stooges to create a security audit blueprint for the email system"

## WHAT HAPPENS AUTOMATICALLY

When you say "Deploy stooges to [task]", I will:

1. **SETUP** (30 seconds)
   - Create git worktree
   - Start tmux session `stooges-work`
   - Launch Claude with --dangerously-skip-permissions
   - Deploy the meta prompt

2. **EXECUTION** (5-15 minutes)
   - Moe creates context and orchestrates
   - Larry analyzes/implements/researches
   - Curly evaluates (iterates until score ≥ 90)

3. **DELIVERY** (1 minute)
   - Extract all deliverables to main repo
   - Create summary report
   - Verify results quality
   - Clean up worktree and tmux

## STANDARD DELIVERABLES

### For Analysis Tasks:
```
/plans/[task-name]/
├── analysis-report.md      # Larry's deep analysis
├── implementation-blueprint.md  # Step-by-step plan
├── evaluation-score.md     # Curly's quality assessment
└── executive-summary.md    # Quick overview
```

### For Implementation Tasks:
```
/implementations/[task-name]/
├── context.md             # Full task understanding
├── solution.md            # Larry's implementation
├── code/                  # Any code files created
└── deployment-guide.md    # How to use it
```

## MONITORING COMMANDS

While stooges are working:
```bash
# Quick status check
tmux capture-pane -t stooges-work -S -10 -p

# Full view (iTerm2)
tmux -CC attach -t stooges-work
```

## TASK TEMPLATES

### 1. Plan Analysis Template
"Deploy stooges to analyze [plan-name] and provide:
- Comprehensive critique
- Risk assessment
- Implementation blueprint
- Resource requirements"

### 2. Code Review Template
"Deploy stooges to review [component] for:
- Security vulnerabilities
- Performance bottlenecks
- Code quality issues
- Improvement recommendations"

### 3. Feature Development Template
"Deploy stooges to implement [feature]:
- Requirements analysis
- Technical design
- Code implementation
- Testing strategy"

### 4. Documentation Template
"Deploy stooges to document [system]:
- Architecture overview
- API reference
- Deployment guide
- Troubleshooting tips"

## AUTOMATIC QUALITY CHECKS

Before bringing results home, I verify:
- ✅ All expected files created
- ✅ Curly's score ≥ 90
- ✅ No placeholder content
- ✅ Files properly formatted
- ✅ Actionable recommendations

## SIMPLE COMMANDS

### Deploy:
```
"Deploy stooges to [task]"
```

### Check Status:
```
"Check stooges status"
```

### Bring Home:
```
"Bring stooges home"  (I'll handle results extraction first)
```

### Emergency Stop:
```
"Kill stooges"
```

## INTEGRATION WITH TODOS

I'll automatically:
- Add "Deploy stooges for [task]" to TodoWrite
- Update status as they work
- Mark complete when results delivered

## SUCCESS METRICS

You'll know it worked when:
- 📊 Curly's score ≥ 90
- 📁 All deliverables in main repo
- ✅ Clear next steps provided
- 🎯 Actionable blueprints ready

---

*Just say "Deploy stooges to..." and I'll handle everything else!*