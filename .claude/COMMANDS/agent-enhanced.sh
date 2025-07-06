#!/bin/bash

# 🤖 ENHANCED SIX AGENT SYSTEM DEPLOYMENT
# Autonomous and parallel execution options

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_step() { echo -e "${BLUE}🔷 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

show_usage() {
    echo -e "${CYAN}🤖 Enhanced Six Agent System Deployment${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS] \"<mission description>\""
    echo ""
    echo "Options:"
    echo "  --autonomous, -a     Full autonomous mode (no confirmations)"
    echo "  --parallel, -p       Enable parallel execution where possible"
    echo "  --fast, -f           Fast mode (autonomous + parallel)"
    echo "  --conservative, -c   Conservative mode (manual confirmations)"
    echo ""
    echo "Examples:"
    echo "  $0 \"implement user authentication\"                    # Default conservative"
    echo "  $0 -a \"implement user authentication\"                 # Autonomous"
    echo "  $0 -p \"implement user authentication\"                 # Parallel where possible"
    echo "  $0 -f \"implement user authentication\"                 # Fast (auto + parallel)"
    echo ""
    exit 1
}

generate_autonomous_mission() {
    local task="$1"
    local mission_file="$2"
    local mode="$3"  # autonomous, parallel, fast, conservative
    
    local task_title=$(echo "$task" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | tr '[:lower:]' '[:upper:]')
    
    # Set execution instructions based on mode
    local execution_mode=""
    local coordination_instructions=""
    
    case "$mode" in
        "autonomous"|"fast")
            execution_mode="AUTONOMOUS"
            coordination_instructions="**AUTONOMOUS MODE**: Proceed automatically through all phases without waiting for human confirmation. Use quality gates to self-validate and iterate if needed."
            ;;
        "parallel")
            execution_mode="PARALLEL"
            coordination_instructions="**PARALLEL MODE**: Execute compatible tasks in parallel. TESTER can start test frameworks while EXECUTER implements. DOCUMENTER can document completed components."
            ;;
        "fast")
            execution_mode="FAST"
            coordination_instructions="**FAST MODE**: Full autonomous execution with parallel tasks where safe. Proceed aggressively but maintain quality standards."
            ;;
        *)
            execution_mode="CONSERVATIVE"
            coordination_instructions="**CONSERVATIVE MODE**: Wait for confirmation between major phases. Human oversight at each transition."
            ;;
    esac

    cat > "$mission_file" << EOF
# MISSION: $task_title

## 🎯 PRIMARY OBJECTIVE
$task

## 🚀 EXECUTION MODE: $execution_mode
$coordination_instructions

## 📋 DETAILED REQUIREMENTS

### Functional Requirements
1. $(echo "$task" | sed 's/^./\U&/')
2. Robust error handling and edge case coverage
3. Backward compatibility where applicable
4. Follow existing code patterns and conventions

### Technical Constraints
- **Codebase**: Analyze entire project structure
- **Dependencies**: Minimize new dependencies
- **Performance**: Maintain or improve current metrics
- **Security**: Proper input validation and sanitization

## 🔗 AGENT COORDINATION STRATEGY

### Sequential Dependencies (Must be Sequential)
1. **PLANNER** → Must complete WORK.md before others start
2. **EXECUTER** → Core implementation must finish before verification
3. **VERIFIER** → Final validation requires all components
4. **REPORTER** → Summary requires all previous work

### Parallel Opportunities (Can Run Simultaneously)
- **TESTER** can start test frameworks while EXECUTER implements core logic
- **DOCUMENTER** can document completed components while implementation continues
- **EXECUTER** can work on independent modules in parallel

### Autonomous Progression Rules
EOF

    if [[ "$mode" == "autonomous" || "$mode" == "fast" ]]; then
        cat >> "$mission_file" << EOF
- **NO HUMAN CONFIRMATION REQUIRED** between phases
- Each agent automatically triggers the next when their work meets quality threshold (≥90%)
- Agents self-iterate if quality < 90% (max 2 iterations)
- Proceed immediately to next phase after successful completion
- Use WORK.md as coordination hub - update status and trigger next agent
EOF
    elif [[ "$mode" == "parallel" ]]; then
        cat >> "$mission_file" << EOF
- Start parallel-compatible tasks immediately after PLANNER completes
- TESTER begins test framework while EXECUTER implements
- DOCUMENTER starts documenting completed components
- Coordinate through WORK.md status updates
- Final integration in VERIFIER phase
EOF
    else
        cat >> "$mission_file" << EOF
- Wait for human confirmation before proceeding to next major phase
- Present completed work and request approval to continue
- Allow for mid-course corrections and feedback
- Quality gates require human validation
EOF
    fi

    cat >> "$mission_file" << EOF

## 📦 REQUIRED DELIVERABLES

### 1. WORK.md (Planner Output)
- Comprehensive implementation plan
- Task breakdown with dependencies
- Quality standards and success criteria
- **TRIGGER**: Automatically notify EXECUTER when complete (if autonomous)

### 2. Implementation Files (Executer Output)
- [ ] Core implementation code
- [ ] Integration and configuration updates
- [ ] Database migrations (if needed)
- [ ] API endpoints (if applicable)
- **TRIGGER**: Notify TESTER and DOCUMENTER when modules complete

### 3. Test Suite (Tester Output)
- [ ] Unit tests with >90% coverage
- [ ] Integration tests
- [ ] Performance benchmarks
- **PARALLEL**: Can start test framework while implementation proceeds

### 4. Documentation (Documenter Output)
- [ ] Technical documentation
- [ ] API documentation
- [ ] User guides
- **PARALLEL**: Document completed components incrementally

### 5. Verification Report (Verifier Output)
- [ ] All requirements validated
- [ ] Quality standards verified
- [ ] Security review completed
- **FINAL**: Requires all previous work to be complete

### 6. Executive Summary (Reporter Output)
- [ ] Project summary and outcomes
- [ ] Deployment instructions
- [ ] Lessons learned

## 🎯 AUTONOMOUS EXECUTION INSTRUCTIONS

**For PLANNER:**
- Complete analysis and create comprehensive WORK.md
- Set clear success criteria for each subsequent agent
- **AUTO-TRIGGER**: "EXECUTER: Your implementation tasks are ready in WORK.md. Begin immediately."

**For EXECUTER:**
- Implement according to WORK.md specifications
- Update WORK.md with progress and completed modules
- **AUTO-TRIGGER**: "TESTER: Module [X] is complete and ready for testing. DOCUMENTER: Component [Y] is ready for documentation."

**For TESTER:**
- Start test frameworks immediately after PLANNER completes
- Test completed modules as EXECUTER finishes them
- **AUTO-TRIGGER**: "All tests passing. VERIFIER: Implementation ready for validation."

**For DOCUMENTER:**
- Begin documentation as soon as components are complete
- Document incrementally rather than waiting for full completion
- **AUTO-TRIGGER**: "Documentation complete. VERIFIER: Ready for final review."

**For VERIFIER:**
- Validate all components meet requirements
- Run comprehensive integration tests
- **AUTO-TRIGGER**: "All validations passed. REPORTER: Create executive summary."

**For REPORTER:**
- Create final summary and deployment guide
- **COMPLETION**: Mission accomplished.

## 🚨 AUTONOMOUS QUALITY GATES

**Self-Validation Criteria:**
- Code quality: No critical issues, follows patterns
- Test coverage: >90% with meaningful tests
- Documentation: Complete and accurate
- Security: No vulnerabilities introduced
- Performance: Meets or exceeds baselines

**Auto-Iteration Triggers:**
- If quality < 90%: Self-iterate with specific improvements
- If tests fail: Fix and re-test automatically
- If integration issues: Resolve and re-validate
- Maximum 2 iteration cycles per agent

## 🎲 AUTONOMOUS AUTHORITY

You have FULL AUTHORITY to:
- Proceed through phases without human confirmation
- Make implementation decisions within scope
- Create files, directories, and configurations
- Refactor code for better integration
- Add dependencies if justified
- Trigger next agents when work is complete

**Quality over speed, but maintain momentum. Execute with confidence and coordination.**

Begin immediately with PLANNER reading all *AGENT*.md files and creating WORK.md. Subsequent agents trigger automatically upon completion of dependencies.
EOF

    print_success "Enhanced mission file created: $mission_file"
}

# Enhanced deployment function with auto-approval
deploy_enhanced_agents() {
    local branch_name="$1"
    local worktree_path="$2"
    local mission_file="$3"
    local mode="$4"
    
    # Create git worktree
    print_step "Creating git worktree: $branch_name"
    if ! git worktree add -b "$branch_name" "$worktree_path" 2>/dev/null; then
        print_warning "Branch exists, using existing worktree"
        git worktree add "$worktree_path" "$branch_name" 2>/dev/null || {
            print_error "Failed to create worktree"
            exit 1
        }
    fi
    
    # Copy agent files
    print_step "Copying agent files to worktree"
    if ls *AGENT*.md 1> /dev/null 2>&1; then
        cp *AGENT*.md "$worktree_path/"
        print_success "Agent files copied"
    else
        print_warning "No *AGENT*.md files found"
    fi
    
    # Copy mission file
    cp "$mission_file" "$worktree_path/AGENT_MISSION.md"
    print_success "Enhanced mission deployed"
    
    # Check existing session
    if tmux has-session -t "$branch_name" 2>/dev/null; then
        print_warning "Session '$branch_name' exists"
        echo -e "${CYAN}Connect with: tmux attach -t $branch_name${NC}"
        return
    fi
    
    # Start tmux session
    print_step "Starting tmux session: $branch_name"
    tmux new-session -d -s "$branch_name" -c "$worktree_path"
    
    # Start Claude with auto-approval handling
    print_step "Starting Claude with auto-approval ($mode mode)..."
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
        
        # Deploy mission with mode-specific instructions
        print_step "Deploying mission to agents..."
        sleep 2
        
        case "$mode" in
            "autonomous"|"fast")
                tmux send-keys -t "$branch_name" "Read AGENT_MISSION.md and *AGENT*.md files. Execute in AUTONOMOUS mode - proceed through all agents automatically without waiting for confirmation. Start with PLANNER immediately." Enter
                sleep 2
                tmux send-keys -t "$branch_name" "Execute the full agent workflow autonomously. Each agent should automatically trigger the next agent when their work is complete and meets quality standards." Enter
                ;;
            "parallel")
                tmux send-keys -t "$branch_name" "Read AGENT_MISSION.md and *AGENT*.md files. Execute in PARALLEL mode - run compatible tasks simultaneously. Start with PLANNER, then parallel execution." Enter
                ;;
            *)
                tmux send-keys -t "$branch_name" "Read AGENT_MISSION.md and *AGENT*.md files. Execute in CONSERVATIVE mode - wait for confirmation between phases. Start with PLANNER." Enter
                ;;
        esac
        
        print_success "Mission deployed successfully in $mode mode!"        
    else
        print_warning "Could not confirm Claude startup. Manual check may be needed."
        print_warning "Connect to debug: tmux attach -t $branch_name"
    fi
}

# Enhanced connection info
show_enhanced_connection_info() {
    local branch_name="$1"
    local worktree_path="$2"
    local mode="$3"
    
    echo ""
    print_success "🚀 Enhanced Agent System Deployed with Auto-Approval! (Mode: $mode)"
    echo ""
    echo -e "${CYAN}📍 Worktree:${NC} $worktree_path"
    echo -e "${CYAN}🌿 Branch:${NC} $branch_name"
    echo ""
    echo -e "${PURPLE}🔗 Connection:${NC}"
    echo "  tmux attach -t $branch_name"
    echo "  tmux -CC attach -t $branch_name  # iTerm2"
    echo ""
    echo -e "${YELLOW}Monitoring:${NC}"
    echo "  tmux capture-pane -t $branch_name -S -20 -p"
    echo "  watch -n 3 'ls -la $worktree_path/WORK.md 2>/dev/null'"
    echo ""
    
    case "$mode" in
        "autonomous"|"fast")
            echo -e "${GREEN}🤖 AUTONOMOUS MODE:${NC} Agents will proceed automatically!"
            echo "  - No human confirmation needed"
            echo "  - Auto-progression through phases"
            echo "  - Quality gates with self-iteration"
            ;;
        "parallel")
            echo -e "${BLUE}⚡ PARALLEL MODE:${NC} Compatible tasks run simultaneously!"
            echo "  - TESTER starts with EXECUTER"
            echo "  - DOCUMENTER documents incrementally"
            echo "  - Faster completion"
            ;;
        *)
            echo -e "${YELLOW}🛡️ CONSERVATIVE MODE:${NC} Manual confirmation between phases"
            echo "  - Human oversight at transitions"
            echo "  - Quality control checkpoints"
            ;;
    esac
    
    echo ""
    echo -e "${CYAN}📊 Expected Flow:${NC}"
    if [[ "$mode" == "parallel" || "$mode" == "fast" ]]; then
        echo "  1. PLANNER → Creates WORK.md"
        echo "  2. EXECUTER + TESTER (parallel) → Implementation + Testing"
        echo "  3. DOCUMENTER (parallel) → Documentation"
        echo "  4. VERIFIER → Final validation"
        echo "  5. REPORTER → Executive summary"
    else
        echo "  1. PLANNER → 2. EXECUTER → 3. TESTER → 4. DOCUMENTER → 5. VERIFIER → 6. REPORTER"
    fi
}

# Parse command line arguments
MODE="conservative"
TASK=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --autonomous|-a)
            MODE="autonomous"
            shift
            ;;
        --parallel|-p)
            MODE="parallel"
            shift
            ;;
        --fast|-f)
            MODE="fast"
            shift
            ;;
        --conservative|-c)
            MODE="conservative"
            shift
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            TASK="$1"
            shift
            ;;
    esac
done

# Main execution
main() {
    if [[ -z "$TASK" ]]; then
        show_usage
    fi
    
    # Validate environment
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
    
    for cmd in git tmux claude; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Required command '$cmd' not found"
            exit 1
        fi
    done
    
    print_step "🤖 Enhanced Six Agent System ($MODE mode)"
    echo -e "${CYAN}Mission:${NC} $TASK"
    echo ""
    
    # Generate names
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local clean_task=$(echo "$TASK" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g' | cut -c1-25)
    local branch_name="agent-${clean_task}-${MODE}-${timestamp}"
    local worktree_path="/Users/Badman/Desktop/email/Agents/$branch_name"
    
    # Create mission
    TEMP_MISSION_FILE=$(mktemp)
    trap 'rm -f "$TEMP_MISSION_FILE"' EXIT
    
    print_step "Generating enhanced mission ($MODE mode)..."
    generate_autonomous_mission "$TASK" "$TEMP_MISSION_FILE" "$MODE"
    
    # Deploy
    print_step "Deploying enhanced agent system..."
    deploy_enhanced_agents "$branch_name" "$worktree_path" "$TEMP_MISSION_FILE" "$MODE"
    
    # Show info
    show_enhanced_connection_info "$branch_name" "$worktree_path" "$MODE"
}

main
