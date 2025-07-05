# 🎭 Three Stooges System - Quick Start Guide

## Usage

The unified deployment script combines mission generation and stooges deployment for fast investigation and analysis:

```bash
./stooges.sh "your investigation task"
```

## Examples

```bash
# Analysis Tasks
./stooges.sh "analyze Atlas Email performance plan"
./stooges.sh "investigate performance bottlenecks in data processing"
./stooges.sh "analyze current authentication system architecture"

# Review & Evaluation
./stooges.sh "review and improve recursive refinement implementation"
./stooges.sh "evaluate email processing pipeline efficiency"
./stooges.sh "assess security posture of current system"

# Audit Tasks
./stooges.sh "create security audit for email system"
./stooges.sh "audit code quality and technical debt"
./stooges.sh "review database performance and optimization"
```

## What It Does

1. **Analyzes your request** and creates a comprehensive investigation mission
2. **Generates a detailed mission file** with roles, objectives, and deliverables
3. **Creates a git worktree** with timestamped branch for isolated work
4. **Launches tmux session** with Claude configured for the Three Stooges workflow
5. **Deploys the mission** with clear sequential execution plan
6. **Provides monitoring instructions** and result extraction commands

## Three Stooges Workflow

The system executes these roles **sequentially** (not parallel):

### 1. 🎯 **MOE (Orchestrator)**
- Creates investigation strategy and plan
- Breaks down task into manageable areas
- Sets success criteria and quality standards
- **Output**: `context.md`, `checklist.md`, `success_criteria.md`

### 2. 🔍 **LARRY (Specialist)** 
- Executes detailed technical investigation
- Gathers evidence and analyzes patterns
- Documents findings with supporting proof
- **Output**: `specialist.md`, `findings.md`, `recommendations.md`

### 3. ⚖️ **CURLY (Evaluator)**
- Quality control and objective scoring (0-100)
- Identifies gaps and areas needing improvement
- Creates final executive summary
- **Output**: `evaluation.md`, `final_report.md`, `next_steps.md`

### 4. 📊 **Consolidation**
- Integrates all findings into coherent narrative
- Prioritizes recommendations by impact
- Creates actionable timeline and resource plan

## Connection Options

After deployment, connect using:

**Standard tmux:**
```bash
tmux attach -t [session-name]
```

**iTerm2 native windows:**
```bash
tmux -CC attach -t [session-name]
```

**Quick progress check:**
```bash
tmux capture-pane -t [session-name] -S -20 -p
```

## Key Files to Monitor

- **context.md** - Moe's investigation strategy
- **specialist.md** - Larry's detailed findings
- **evaluation.md** - Curly's quality scores
- **final_report.md** - Consolidated executive summary

## Quality Standards

- **Completeness Score**: ≥80% (covers all important areas)
- **Depth Score**: ≥80% (thorough analysis with evidence)
- **Actionability Score**: ≥80% (specific, implementable recommendations)
- **Evidence Score**: ≥80% (all claims backed by solid proof)

If any score < 80%, Curly will trigger iteration for improvement.

## File Organization

All outputs are organized in:
```
docs/[task-name]/
├── context.md          # Moe's plan
├── checklist.md        # Investigation items
├── specialist.md       # Larry's analysis
├── findings.md         # Key discoveries
├── evaluation.md       # Curly's scores
├── final_report.md     # Executive summary
├── next_steps.md       # Action items
└── evidence/           # Supporting files
```

## Bringing Results Home

```bash
# Copy all investigation results to main repo
cp -r [worktree-path]/docs/* ./DOCS/

# Clean up when done
git worktree remove [worktree-path] --force
tmux kill-session -t [session-name]
```

## Best Use Cases

The Three Stooges system excels at:

- **🔍 Quick Investigations** - Fast parallel analysis with quality control
- **📊 System Analysis** - Deep dives into architecture and performance
- **🔒 Security Audits** - Comprehensive security posture evaluation
- **⚡ Root Cause Analysis** - Finding and fixing core issues
- **📈 Performance Reviews** - Bottleneck identification and optimization
- **🏗️ Technical Debt Assessment** - Code quality and improvement planning

## Monitoring Progress

Watch for sequential progression:
1. **Moe** creates files in docs/ folder
2. **Larry** adds detailed analysis and evidence
3. **Curly** provides scoring and final evaluation
4. **Consolidation** creates executive-ready summary

## Error Recovery

If stooges get stuck:
1. Check tmux output for current phase
2. Provide clarification through tmux session
3. If blocked >5 minutes, restart with clearer mission
4. Quality gates will trigger automatic iteration if needed

---

**Tip**: The Three Stooges are designed for **fast, thorough investigation**. They work sequentially but efficiently, with built-in quality control to ensure reliable results. Perfect for when you need answers quickly but thoroughly!
