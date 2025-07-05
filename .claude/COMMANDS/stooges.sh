#!/bin/bash

# 🎭 UNIFIED THREE STOOGES DEPLOYMENT
# Combines mission generation and stooges deployment into one command

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🎬 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${CYAN}🎭 Three Stooges Deployment${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 \"<investigation/analysis task>\""
    echo ""
    echo "Examples:"
    echo "  $0 \"analyze Atlas Email performance plan\""
    echo "  $0 \"review and improve recursive refinement\""
    echo "  $0 \"create security audit for email system\""
    echo "  $0 \"investigate performance bottlenecks in data processing\""
    echo "  $0 \"evaluate current authentication system\""
    echo ""
    exit 1
}

# Function to generate mission file for stooges
generate_stooges_mission() {
    local task="$1"
    local mission_file="$2"
    
    # Extract task components
    local action=""
    local target=""
    
    # Determine action type
    if [[ "$task" =~ analyze|investigation|investigate ]]; then
        action="analyze"
    elif [[ "$task" =~ review|evaluate|audit|assess ]]; then
        action="review and evaluate"
    elif [[ "$task" =~ improve|optimize|enhance ]]; then
        action="improve"
    elif [[ "$task" =~ create|develop|design ]]; then
        action="create"
    else
        action="analyze"
    fi
    
    # Extract target from task
    target=$(echo "$task" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    
    # Create mission file
    cat > "$mission_file" << 'EOF'
<s>
You are building an **Agentic Loop** that can tackle any complex task with minimal role bloat.

**Core principles**
1. **Single prompt, multiple phases**: You'll act as different specialists in sequence
2. **Incremental refinement**: Each specialist builds on the previous work
3. **Quality gates**: Curly evaluates and may trigger re-work if quality < 80%
4. **Concrete outputs**: Every phase produces actionable deliverables
5. **Minimal coordination overhead**: No complex handoffs, just sequential execution
6. **Measurable quality**: Numeric scoring for objective evaluation
</s>

<Context>
**Task**: TASK_PLACEHOLDER
**Repo path (if any)**: /Users/Badman/Desktop/email (analyze existing structure and files)
**Desired parallelism**: 0  (sequential - act as all three in order)

The Orchestrator must decide:
- Whether to specialize the workflow to this repo or keep it generic.
- How many identical Specialist instances to launch (0 = sequential).
</Context>

<Instructions>

## Bootstrap Phase
Before starting the Three Stooges loop:
1. **Survey the landscape**: Quickly scan available files, docs, recent changes
2. **Identify key areas**: What are the 3-5 most critical aspects to investigate?
3. **Set success criteria**: What would constitute a successful analysis?
4. **Plan approach**: Sequential execution through Moe → Larry → Curly

## Phase 1: Moe (Orchestrator) 
**Role**: Project manager and strategic thinker

**Objectives**:
- Break down the task into manageable investigation areas
- Identify what information Larry needs to gather
- Set quality standards for the investigation
- Create investigation framework and checklist

**Deliverables**:
- `context.md`: High-level task breakdown and investigation strategy
- `checklist.md`: Specific items for Larry to investigate
- `success_criteria.md`: How we'll measure completion and quality

**Output Pattern**:
```
## MOE'S INVESTIGATION PLAN

### Task Breakdown
[3-5 key investigation areas]

### Information Gathering Strategy
[What Larry should focus on]

### Success Criteria
[Measurable outcomes]

### Next Steps for Larry
[Specific actionable items]
```

## Phase 2: Larry (Specialist)
**Role**: Deep technical investigator and analyst

**Objectives**:
- Execute Moe's investigation plan thoroughly
- Gather detailed information from all relevant sources
- Analyze patterns, issues, and opportunities
- Document findings with evidence and examples

**Deliverables**:
- `specialist.md`: Detailed investigation results
- `findings.md`: Key discoveries and insights
- `evidence/`: Supporting documents, code snippets, data
- `recommendations.md`: Specific improvement suggestions

**Output Pattern**:
```
## LARRY'S DETAILED INVESTIGATION

### Executive Summary
[High-level findings in 3-4 sentences]

### Detailed Analysis
[Section by section deep dive]

### Key Findings
[Most important discoveries]

### Evidence and Examples
[Concrete proof and data]

### Recommendations
[Specific, actionable suggestions]
```

## Phase 3: Curly (Evaluator)
**Role**: Quality control and final validator

**Objectives**:
- Evaluate completeness and quality of investigation
- Score the work objectively (0-100)
- Identify gaps or areas needing more work
- Provide final recommendations and next steps

**Deliverables**:
- `evaluation.md`: Quality assessment with numeric scores
- `gaps.md`: Areas needing additional investigation
- `final_report.md`: Executive summary and recommendations
- `next_steps.md`: Actionable follow-up items

**Output Pattern**:
```
## CURLY'S QUALITY EVALUATION

### Overall Score: [0-100]

### Quality Metrics:
- Completeness: [0-100] - Did we cover all important areas?
- Depth: [0-100] - Is the analysis thorough enough?
- Actionability: [0-100] - Are recommendations specific and practical?
- Evidence: [0-100] - Is everything backed by solid proof?

### Strengths
[What was done well]

### Gaps and Concerns
[What needs improvement]

### Final Recommendations
[Top 3-5 actionable items]

### Iteration Needed?
[YES/NO - if YES, specify what needs rework]
```

## Consolidate Phase
After all three specialists complete their work:
1. **Integrate outputs**: Combine all findings into coherent narrative
2. **Prioritize recommendations**: Rank suggestions by impact and feasibility  
3. **Create action plan**: Timeline and resource requirements
4. **Generate summary**: Executive briefing for stakeholders

</Instructions>

<Constraints>
- **File organization**: Create docs/[task-name]/ folder for all outputs
- **Evidence-based**: Every claim must have supporting evidence
- **Actionable outputs**: All recommendations must be specific and implementable
- **Quality threshold**: Curly must score ≥80% for completion, otherwise iterate
- **Time-boxed**: Complete investigation within reasonable scope
- **Stakeholder ready**: All outputs should be presentable to leadership
</Constraints>

<Output Format>
Each specialist should:
1. Clearly identify their role at the start
2. Follow their specific output pattern
3. Reference and build on previous work
4. End with clear handoff to next specialist
5. Save all work in appropriately named files

Final deliverable: Comprehensive investigation package ready for stakeholder review.
</Output Format>

<User Input>
```
TASK_PLACEHOLDER

Required Deliverables:
1. Comprehensive analysis document with executive summary
2. Detailed findings with supporting evidence
3. Specific recommendations with implementation steps
4. Risk assessment and mitigation strategies
5. Resource requirements and timeline estimates
6. Quality evaluation with objective scoring

Make sure all outputs are production-ready and suitable for executive presentation.
```
</User Input>
EOF

    # Replace placeholder with actual task
    sed -i.bak "s/TASK_PLACEHOLDER/$target/g" "$mission_file" && rm -f "${mission_file}.bak"
    
    print_success "Stooges mission file created: $mission_file"
}

# Function to deploy stooges with auto-approval
deploy_stooges() {
    local branch_name="$1"
    local worktree_path="$2"
    local mission_file="$3"
    
    # Create git worktree
    print_step "Creating git worktree: $branch_name"
    if ! git worktree add -b "$branch_name" "$worktree_path" 2>/dev/null; then
        print_warning "Branch $branch_name already exists, using existing worktree"
        if ! git worktree add "$worktree_path" "$branch_name" 2>/dev/null; then
            print_error "Failed to create or access worktree"
            exit 1
        fi
    fi
    
    # Copy stooges framework if it exists
    if [[ -f "Agents/stooges.md" ]]; then
        cp "Agents/stooges.md" "$worktree_path/"
        print_success "Stooges framework copied"
    elif [[ -f "stooges.md" ]]; then
        cp "stooges.md" "$worktree_path/"
        print_success "Stooges framework copied"
    else
        print_warning "No stooges.md framework file found - mission will be self-contained"
    fi
    
    # Copy mission file to worktree
    cp "$mission_file" "$worktree_path/STOOGES_MISSION.md"
    print_success "Mission file deployed to worktree"
    
    # Check if tmux session already exists
    if tmux has-session -t "$branch_name" 2>/dev/null; then
        print_warning "tmux session '$branch_name' already exists"
        print_step "Attaching to existing session..."
        echo ""
        echo -e "${CYAN}To connect:${NC}"
        echo "  tmux attach -t $branch_name"
        echo ""
        echo -e "${CYAN}For iTerm2 native windows:${NC}"
        echo "  tmux -CC attach -t $branch_name"
        return
    fi
    
    # Start tmux session
    print_step "Starting tmux session: $branch_name"
    tmux new-session -d -s "$branch_name" -c "$worktree_path"
    
    # Start Claude with auto-approval handling
    print_step "Starting Claude for stooges with auto-approval..."
    tmux send-keys -t "$branch_name" "claude --dangerously-skip-permissions" Enter
    
    # Auto-approval loop with timeout
    local timeout=45
    local start_time=$(date +%s)
    local claude_ready=false
    
    print_step "Handling potential first-time approvals..."
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $timeout ]]; then
            print_warning "Timeout reached. Claude may need manual approval."
            print_warning "Connect manually: tmux attach -t $branch_name"
            return
        fi
        
        # Get current tmux output
        local output=$(tmux capture-pane -t "$branch_name" -p -S -20)
        
        # Check for various approval prompts
        if echo "$output" | grep -qi "allow.*connection\|approve.*server\|grant.*permission\|enable.*tool"; then
            print_step "Auto-approving permission..."
            tmux send-keys -t "$branch_name" "y" Enter
            sleep 2
        elif echo "$output" | grep -qi "claude is ready\|claude>\|welcome to claude"; then
            claude_ready=true
            break
        elif echo "$output" | grep -qi "error\|failed\|cannot connect"; then
            print_error "Claude startup failed. Check output manually."
            print_warning "Connect to debug: tmux attach -t $branch_name"
            return
        fi
        
        sleep 1
    done
    
    if [[ "$claude_ready" == true ]]; then
        print_success "Claude started successfully with auto-approval!"
        
        # Deploy mission to the Three Stooges
        print_step "Deploying mission to the Three Stooges..."
        sleep 2
        
        tmux send-keys -t "$branch_name" "Read and execute STOOGES_MISSION.md. You are the Three Stooges investigation team. Execute the sequential workflow: Moe (orchestrator) → Larry (specialist) → Curly (evaluator)." Enter
        
        sleep 2
        
        # Send follow-up instruction
        tmux send-keys -t "$branch_name" "Start as MOE to create the investigation plan and strategy. Then switch to LARRY for detailed analysis, and finally CURLY for quality evaluation." Enter
        
        print_success "Mission deployed successfully to the Three Stooges!"
    else
        print_warning "Could not confirm Claude startup. Manual check may be needed."
        print_warning "Connect to debug: tmux attach -t $branch_name"
    fi
}

# Function to show connection instructions
show_connection_info() {
    local branch_name="$1"
    local worktree_path="$2"
    
    echo ""
    print_success "🎭 Three Stooges deployed with auto-approval and ready for action!"
    echo ""
    echo -e "${CYAN}📍 Worktree Location:${NC} $worktree_path"
    echo -e "${CYAN}🌿 Branch Name:${NC} $branch_name"
    echo ""
    echo -e "${PURPLE}🔗 Connection Options:${NC}"
    echo ""
    echo -e "${YELLOW}Standard tmux:${NC}"
    echo "  tmux attach -t $branch_name"
    echo ""
    echo -e "${YELLOW}iTerm2 native windows:${NC}"
    echo "  tmux -CC attach -t $branch_name"
    echo ""
    echo -e "${YELLOW}Quick progress check:${NC}"
    echo "  tmux capture-pane -t $branch_name -S -20 -p"
    echo ""
    echo -e "${YELLOW}Monitor docs folder:${NC}"
    echo "  watch -n 5 'ls -la $worktree_path/docs/ 2>/dev/null || echo \"No docs folder yet\"'"
    echo ""
    echo -e "${CYAN}🎬 Expected Workflow:${NC}"
    echo "  1. 🎯 MOE (Orchestrator) - Creates investigation plan and strategy"
    echo "  2. 🔍 LARRY (Specialist) - Performs detailed technical analysis"
    echo "  3. ⚖️  CURLY (Evaluator) - Quality control and final scoring"
    echo "  4. 📊 Consolidation - Integrates all findings into final report"
    echo ""
    echo -e "${GREEN}💡 Key Files to Watch:${NC}"
    echo "  - context.md (Moe's plan)"
    echo "  - specialist.md (Larry's findings)"
    echo "  - evaluation.md (Curly's scoring)"
    echo "  - final_report.md (Consolidated results)"
    echo ""
    echo -e "${CYAN}🏁 Bringing Them Home:${NC}"
    echo "  # Copy results to main repo"
    echo "  cp -r $worktree_path/docs/* ./DOCS/ 2>/dev/null || true"
    echo "  # Clean up worktree when done"
    echo "  git worktree remove $worktree_path --force"
    echo "  tmux kill-session -t $branch_name"
}

# Function to cleanup on exit
cleanup() {
    if [[ -n "$TEMP_MISSION_FILE" && -f "$TEMP_MISSION_FILE" ]]; then
        rm -f "$TEMP_MISSION_FILE"
    fi
}

# Set cleanup trap
trap cleanup EXIT

# Main execution
main() {
    # Check if task description is provided
    if [[ $# -eq 0 ]]; then
        show_usage
    fi
    
    local task="$1"
    
    # Validate we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository. Please run from your project root."
        exit 1
    fi
    
    # Check for required commands
    for cmd in git tmux claude; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Required command '$cmd' not found. Please install it first."
            exit 1
        fi
    done
    
    print_step "🎭 Initializing Three Stooges Investigation"
    echo -e "${CYAN}Mission:${NC} $task"
    echo ""
    
    # Generate timestamp and names
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local clean_task=$(echo "$task" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g' | cut -c1-30)
    local branch_name="stooges-${clean_task}-${timestamp}"
    local worktree_path="/Users/Badman/Desktop/email/stooges-work-${clean_task}-${timestamp}"
    
    # Create temporary mission file
    TEMP_MISSION_FILE=$(mktemp)
    
    # Generate mission
    print_step "Generating stooges mission specification..."
    generate_stooges_mission "$task" "$TEMP_MISSION_FILE"
    
    # Deploy stooges
    print_step "Deploying the Three Stooges..."
    deploy_stooges "$branch_name" "$worktree_path" "$TEMP_MISSION_FILE"
    
    # Show connection information
    show_connection_info "$branch_name" "$worktree_path"
    
    # Cleanup temp file
    rm -f "$TEMP_MISSION_FILE"
    TEMP_MISSION_FILE=""
}

# Run main function with all arguments
main "$@"
