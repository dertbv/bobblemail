#!/bin/bash

# 🤖 UNIFIED SIX AGENT SYSTEM DEPLOYMENT
# Combines mission generation and agent deployment into one command

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
    echo -e "${BLUE}🔷 $1${NC}"
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
    echo -e "${CYAN}🤖 Six Agent System Deployment${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 \"<mission description>\""
    echo ""
    echo "Examples:"
    echo "  $0 \"implement user authentication system\""
    echo "  $0 \"refactor email processing pipeline\""
    echo "  $0 \"add real-time notifications\""
    echo "  $0 \"fix memory leak in data parser\""
    echo "  $0 \"analyze performance bottlenecks\""
    echo ""
    exit 1
}

# Function to extract task type and generate mission
generate_mission() {
    local task="$1"
    local mission_file="$2"
    
    # Extract task components
    local action=""
    local target=""
    local task_type=""
    
    # Determine action type
    if [[ "$task" =~ implement|add|create|build ]]; then
        action="implement"
        task_type="feature"
    elif [[ "$task" =~ fix|resolve|debug|patch ]]; then
        action="fix"
        task_type="bug"
    elif [[ "$task" =~ refactor|restructure|redesign|optimize ]]; then
        action="refactor"
        task_type="refactoring"
    elif [[ "$task" =~ analyze|investigate|review|audit ]]; then
        action="analyze"
        task_type="analysis"
    else
        action="implement"
        task_type="feature"
    fi
    
    # Generate clean task title
    local task_title=$(echo "$task" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | tr '[:lower:]' '[:upper:]')
    
    # Create mission file
    cat > "$mission_file" << EOF
# MISSION: $task_title

## 🎯 PRIMARY OBJECTIVE
$task

## 📋 DETAILED REQUIREMENTS

### Functional Requirements
1. $(echo "$task" | sed 's/^./\U&/')
2. Ensure robust error handling and edge case coverage
3. Maintain backward compatibility where applicable
4. Follow existing code patterns and conventions

### Technical Constraints
- **Codebase**: Analyze entire project structure for relevant files
- **Dependencies**: Minimize new dependencies, document if absolutely necessary
- **Performance**: Maintain or improve current performance metrics
- **Compatibility**: Ensure cross-platform compatibility
- **Security**: Implement proper input validation and sanitization

## 🔍 INVESTIGATION SCOPE

### Primary Investigation Areas
1. **Current Implementation**: Analyze existing related functionality
2. **Dependencies & Integrations**: Map all system connections
3. **Impact Analysis**: Identify potential side effects
4. **Performance Considerations**: Assess resource requirements

### Required Documentation Review
- \`README.md\` - Project overview and setup
- \`docs/\` directory - Technical documentation
- \`LEARNINGS.md\` - Previous insights and patterns
- Recent reports in \`reports/\` - Historical context
- Existing test files - Current coverage and patterns

## 📦 REQUIRED DELIVERABLES

### 1. WORK.md (Planner Output)
- Comprehensive analysis of current state
- Detailed solution architecture
- Step-by-step implementation plan
- Risk assessment and mitigation strategies
- Resource and timeline estimates

### 2. Implementation Files (Executer Output)
- [ ] Core implementation code
- [ ] Integration and configuration updates
- [ ] Database migrations (if needed)
- [ ] API endpoints (if applicable)
- [ ] Frontend components (if applicable)

### 3. Test Suite (Tester Output)
- [ ] Unit tests with >90% coverage
- [ ] Integration tests for all components
- [ ] Edge case and error condition tests
- [ ] Performance benchmarks
- [ ] Security vulnerability tests

### 4. Documentation (Documenter Output)
- [ ] Technical implementation documentation
- [ ] API documentation (if applicable)
- [ ] User guide updates
- [ ] Installation/deployment instructions
- [ ] Troubleshooting guide

### 5. Verification Report (Verifier Output)
- [ ] All functional requirements validated
- [ ] Quality standards compliance verified
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Integration testing passed

## 🚀 EXECUTION PREFERENCES

### Development Approach
- **Methodology**: Test-Driven Development where applicable
- **Code Style**: Follow existing project conventions
- **Error Handling**: Comprehensive logging and graceful degradation
- **Security**: Zero-trust approach with input validation
- **Performance**: Optimize for both speed and memory usage

### Agent Coordination
- **Parallelization**: Tests can be written while implementation is in progress
- **Dependencies**: Planning → Implementation → Testing → Documentation → Verification
- **Communication**: Update WORK.md after each major milestone
- **Quality Gates**: Each phase must meet 90% quality threshold before proceeding
- **Iteration**: Maximum 2 revision cycles if initial quality < 90%

## ⚠️ CRITICAL WARNINGS
- Always backup critical data before making changes
- Test thoroughly in isolated environment first
- Document any breaking changes clearly
- Ensure rollback procedures are in place
- Monitor system performance during and after deployment

## 🎲 AUTONOMOUS AUTHORITY
You have full authority to:
- Make implementation decisions within scope and constraints
- Create necessary files, directories, and configurations
- Refactor existing code for better integration and maintainability
- Add dependencies if absolutely necessary (document justification)
- Modify database schemas with proper migration scripts
- Update APIs while maintaining backward compatibility

## 🎯 SUCCESS CRITERIA
- All functional requirements are met and verified
- Code coverage exceeds 90% with meaningful tests
- Performance meets or exceeds current baselines
- Security vulnerabilities are addressed
- Documentation is complete and accurate
- System integration is seamless

Begin by reading all *AGENT*.md files to understand your roles and capabilities, then start with PLANNER to create a comprehensive WORK.md that will guide all other agents.

**Remember**: Quality over speed. It's better to deliver excellent work that might take longer than rushed work that creates technical debt.
EOF

    print_success "Mission file created: $mission_file"
}

# Function to deploy agents
deploy_agents() {
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
    
    # Copy agent files to worktree
    print_step "Copying agent files to worktree"
    if ls *AGENT*.md 1> /dev/null 2>&1; then
        cp *AGENT*.md "$worktree_path/"
        print_success "Agent files copied"
    else
        print_warning "No *AGENT*.md files found in current directory"
        print_warning "Make sure you have the agent definition files available"
    fi
    
    # Copy mission file to worktree
    cp "$mission_file" "$worktree_path/AGENT_MISSION.md"
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
    
    # Start Claude with permissions flag
    print_step "Starting Claude agent system..."
    tmux send-keys -t "$branch_name" "claude --dangerously-skip-permissions" Enter
    
    # Wait for Claude to start
    print_step "Waiting for Claude to initialize..."
    sleep 5
    
    # Send the mission
    print_step "Deploying mission to agents..."
    tmux send-keys -t "$branch_name" "Read all *AGENT*.md files and AGENT_MISSION.md carefully. You are part of a six-agent system. Implement the mission using the coordinated agent approach described in the files." Enter
    
    sleep 2
    
    # Send follow-up instruction
    tmux send-keys -t "$branch_name" "Start with the PLANNER agent role to analyze the mission and create a comprehensive WORK.md file that will guide all other agents." Enter
}

# Function to show connection instructions
show_connection_info() {
    local branch_name="$1"
    local worktree_path="$2"
    
    echo ""
    print_success "🚀 Agent system deployed successfully!"
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
    echo -e "${YELLOW}Monitor specific file:${NC}"
    echo "  watch -n 5 'ls -la $worktree_path/WORK.md 2>/dev/null || echo \"WORK.md not created yet\"'"
    echo ""
    echo -e "${CYAN}📋 Expected Workflow:${NC}"
    echo "  1. PLANNER creates WORK.md with analysis and tasks"
    echo "  2. EXECUTER implements the solution"
    echo "  3. TESTER creates comprehensive test suite"
    echo "  4. DOCUMENTER creates documentation"
    echo "  5. VERIFIER validates everything meets requirements"
    echo "  6. REPORTER generates final summary"
    echo ""
    echo -e "${GREEN}💡 Tip:${NC} The agents will coordinate automatically. Check WORK.md for progress updates."
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
    
    print_step "🤖 Initializing Six Agent System Deployment"
    echo -e "${CYAN}Mission:${NC} $task"
    echo ""
    
    # Generate timestamp and names
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local clean_task=$(echo "$task" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g' | cut -c1-30)
    local branch_name="agent-${clean_task}-${timestamp}"
    local worktree_path="/Users/Badman/Desktop/email/Agents/$branch_name"
    
    # Create temporary mission file
    TEMP_MISSION_FILE=$(mktemp)
    
    # Generate mission
    print_step "Generating mission specification..."
    generate_mission "$task" "$TEMP_MISSION_FILE"
    
    # Deploy agents
    print_step "Deploying agent system..."
    deploy_agents "$branch_name" "$worktree_path" "$TEMP_MISSION_FILE"
    
    # Show connection information
    show_connection_info "$branch_name" "$worktree_path"
    
    # Cleanup temp file
    rm -f "$TEMP_MISSION_FILE"
    TEMP_MISSION_FILE=""
}

# Run main function with all arguments
main "$@"
