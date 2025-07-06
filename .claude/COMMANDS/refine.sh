#!/bin/bash

# 🔄 RECURSIVE COMPANION DEPLOYMENT
# Simple and direct execution of recursive refinement

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_step() { echo -e "${BLUE}🔄 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

show_usage() {
    echo -e "${CYAN}🔄 Recursive Companion Deployment${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS] \"<topic or task description>\""
    echo ""
    echo "Modes:"
    echo "  --build, -b         Build comprehensive content from scratch (default)"
    echo "  --improve, -i       Improve existing content (requires --content)"
    echo "  --explore, -e       Simple exploratory refinement"
    echo "  --content FILE      Existing content to improve (use with --improve)"
    echo ""
    echo "Options:"
    echo "  --iterations N      Maximum iterations (default: 5)"
    echo "  --target-score N    Target quality score (default: 0.85)"
    echo "  --session-id ID     Session identifier for tracking"
    echo ""
    echo "Examples:"
    echo "  $0 \"design a caching system for our API\""
    echo "  $0 -e \"explain machine learning algorithms\""
    echo "  $0 -i --content existing.md \"improve this documentation\""
    echo "  $0 -b \"create comprehensive authentication system guide\""
    echo ""
    exit 1
}

# Function to determine task type and generate appropriate refinement
generate_refinement_prompt() {
    local task="$1"
    local mode="$2"
    local existing_content="$3"
    
    case "$mode" in
        "improve")
            if [[ -z "$existing_content" ]]; then
                print_error "Improve mode requires existing content. Use --content option."
                exit 1
            fi
            generate_improve_prompt "$task" "$existing_content"
            ;;
        "explore")
            generate_explore_prompt "$task"
            ;;
        "build"|*)
            generate_build_prompt "$task"
            ;;
    esac
}

# Generate comprehensive building prompt
generate_build_prompt() {
    local task="$1"
    
    # Analyze task type
    local task_type=""
    local deliverables=""
    local requirements=""
    
    if [[ "$task" =~ design|architect|create|build|implement ]]; then
        task_type="implementation"
        deliverables="- Architecture design and components
- Implementation approach and steps
- Technology recommendations
- Best practices and patterns
- Edge cases and error handling
- Testing and validation strategy"
        requirements="- Detailed system design
- Step-by-step implementation guide
- Technology stack recommendations
- Security and performance considerations
- Deployment and maintenance approach"
    elif [[ "$task" =~ document|explain|guide|tutorial ]]; then
        task_type="documentation"
        deliverables="- Comprehensive overview and introduction
- Detailed explanation of concepts
- Practical examples and use cases
- Best practices and common pitfalls
- Reference information and resources
- Troubleshooting and FAQ section"
        requirements="- Clear, well-structured content
- Examples and code samples
- Visual aids where helpful
- Actionable guidance
- Complete reference information"
    elif [[ "$task" =~ analyze|investigate|review|audit ]]; then
        task_type="analysis"
        deliverables="- Current state assessment
- Problem identification and analysis
- Root cause investigation
- Impact and risk assessment
- Recommendations and solutions
- Implementation roadmap"
        requirements="- Thorough analysis methodology
- Evidence-based findings
- Quantified impact assessment
- Prioritized recommendations
- Actionable next steps"
    elif [[ "$task" =~ solve|fix|resolve|troubleshoot ]]; then
        task_type="problem_solving"
        deliverables="- Problem definition and scope
- Multiple solution approaches
- Tradeoff analysis and comparison
- Recommended solution with justification
- Implementation steps and timeline
- Risk mitigation strategies"
        requirements="- Clear problem articulation
- Multiple viable solutions
- Comparative analysis
- Detailed implementation plan
- Success metrics and validation"
    else
        task_type="general"
        deliverables="- Comprehensive topic overview
- Key concepts and principles
- Practical applications
- Best practices and guidelines
- Examples and case studies
- Further resources and references"
        requirements="- Well-structured information
- Clear explanations
- Practical examples
- Actionable insights
- Complete coverage of topic"
    fi
    
    # Extract context from task
    local context=""
    if [[ "$task" =~ API|api ]]; then
        context="$context\n- Working with API systems and endpoints"
    fi
    if [[ "$task" =~ database|db|sql ]]; then
        context="$context\n- Database and data management context"
    fi
    if [[ "$task" =~ security|auth|authentication ]]; then
        context="$context\n- Security and authentication requirements"
    fi
    if [[ "$task" =~ performance|scale|optimization ]]; then
        context="$context\n- Performance and scalability considerations"
    fi
    if [[ "$task" =~ frontend|ui|user ]]; then
        context="$context\n- User interface and experience focus"
    fi
    if [[ "$task" =~ backend|server|infrastructure ]]; then
        context="$context\n- Backend and infrastructure context"
    fi
    
    cat << EOF
$task

Context:$context
- Task type: $task_type
- Comprehensive coverage required
- Production-ready guidance needed

Requirements:
$requirements

Output Requirements:
1. Show refinement metrics:
   - Number of iterations completed
   - Quality score for each iteration
   - Similarity scores between iterations
   - Convergence status and reason
   - Final quality score achieved

2. Provide the refined deliverable with:
$deliverables

Focus on creating content that is immediately actionable, well-structured, and comprehensive enough to serve as a complete reference for the topic.
EOF
}

# Generate improvement prompt for existing content
generate_improve_prompt() {
    local task="$1"
    local existing_content="$2"
    
    cat << EOF
Improve this existing content: $task

Existing content to refine:
$existing_content

Focus Areas:
- Clarity and readability improvements
- Completeness and missing information
- Structure and organization
- Accuracy and up-to-date information
- Practical examples and actionable guidance
- Technical depth and detail
- Error correction and fact-checking

Please enhance the content while maintaining its core message and intent.
EOF
}

# Generate simple exploration prompt
generate_explore_prompt() {
    local task="$1"
    
    cat << EOF
Create a comprehensive explanation of: $task

Provide an in-depth exploration that covers:
- Fundamental concepts and principles
- Practical applications and use cases
- Best practices and recommendations
- Common challenges and solutions
- Real-world examples
- Further learning resources

Make it accessible yet thorough, suitable for both beginners and experienced practitioners.
EOF
}

# Execute the recursive companion tool directly
execute_refinement() {
    local prompt="$1"
    local iterations="$2"
    local target_score="$3"
    local session_id="$4"
    local mode="$5"
    
    print_step "Executing recursive refinement..."
    print_step "Mode: $mode | Max iterations: $iterations | Target score: $target_score"
    
    # Validate Claude CLI is available
    if ! command -v claude &> /dev/null; then
        print_error "Claude CLI not found. Please install it first."
        exit 1
    fi
    
    if [[ "$mode" == "improve" ]]; then
        # Use refine tool for improving existing content
        print_step "Using refine tool for content improvement..."
        
        # Create temporary file for the prompt
        local temp_prompt=$(mktemp)
        echo "$prompt" > "$temp_prompt"
        
        # Execute the refine command with correct syntax
        if ! claude run local-recursive-companion:refine \
            "$(cat "$temp_prompt")" \
            --max-iterations "$iterations" \
            --target-score "$target_score"; then
            print_error "Refine command failed"
            rm -f "$temp_prompt"
            exit 1
        fi
        
        rm -f "$temp_prompt"
    else
        # Use incremental_refine for building new content
        print_step "Using incremental_refine tool for comprehensive building..."
        
        # Create a temporary file with the prompt
        local temp_prompt=$(mktemp)
        echo "$prompt" > "$temp_prompt"
        
        # Execute the incremental_refine command with correct syntax
        if ! claude run local-recursive-companion:incremental_refine \
            "$(cat "$temp_prompt")" \
            --max-iterations "$iterations" \
            --target-score "$target_score"; then
            print_error "Incremental refine command failed"
            rm -f "$temp_prompt"
            exit 1
        fi
        
        rm -f "$temp_prompt"
    fi
}

# Parse command line arguments
MODE="build"
CONTENT_FILE=""
ITERATIONS=5
TARGET_SCORE=0.85
SESSION_ID=""
TASK=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            MODE="build"
            shift
            ;;
        --improve|-i)
            MODE="improve"
            shift
            ;;
        --explore|-e)
            MODE="explore"
            shift
            ;;
        --content)
            CONTENT_FILE="$2"
            shift 2
            ;;
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        --target-score)
            TARGET_SCORE="$2"
            shift 2
            ;;
        --session-id)
            SESSION_ID="$2"
            shift 2
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
    
    # Read existing content if provided
    local existing_content=""
    if [[ -n "$CONTENT_FILE" ]]; then
        if [[ ! -f "$CONTENT_FILE" ]]; then
            print_error "Content file not found: $CONTENT_FILE"
            exit 1
        fi
        existing_content=$(cat "$CONTENT_FILE")
        print_success "Loaded content from: $CONTENT_FILE"
    fi
    
    print_step "🔄 Recursive Companion Refinement"
    echo -e "${CYAN}Task:${NC} $TASK"
    echo -e "${CYAN}Mode:${NC} $MODE"
    
    if [[ -n "$CONTENT_FILE" ]]; then
        echo -e "${CYAN}Content File:${NC} $CONTENT_FILE"
    fi
    
    echo ""
    
    # Generate refinement prompt
    print_step "Generating refinement prompt for $MODE mode..."
    local prompt=$(generate_refinement_prompt "$TASK" "$MODE" "$existing_content")
    
    # Show prompt preview
    echo -e "${YELLOW}Generated Prompt Preview:${NC}"
    echo "$prompt" | head -5
    echo "..."
    echo ""
    
    # Execute refinement directly
    execute_refinement "$prompt" "$ITERATIONS" "$TARGET_SCORE" "$SESSION_ID" "$MODE"
    
    print_success "Recursive refinement completed!"
    
    # Show next steps
    echo ""
    echo -e "${CYAN}💡 Next Steps:${NC}"
    if [[ -n "$SESSION_ID" ]]; then
        echo "  - View session: claude local-recursive-companion:get_session --sessionId \"$SESSION_ID\""
        echo "  - List all sessions: claude local-recursive-companion:get_sessions"
    fi
    echo "  - Run again with different parameters if needed"
    echo "  - Use --improve mode to further refine the output"
}

main
