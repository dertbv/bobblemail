#!/bin/bash

# 🔄 WORKING RECURSIVE COMPANION SCRIPT
# This creates the prompt and instructions for using within Claude

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get the task description
TASK="$1"

if [[ -z "$TASK" ]]; then
    echo -e "${RED}❌ Error: Please provide a task description${NC}"
    echo "Usage: $0 \"your task or topic to refine\""
    exit 1
fi

echo -e "${BLUE}🔄 Recursive Refinement Generator${NC}"
echo -e "${YELLOW}Task:${NC} $TASK"
echo ""

# Generate the incremental_refine command
cat << EOF > /tmp/refine_command.txt
Use the incremental_refine tool with this prompt:

$TASK

Context:
- Need comprehensive solution with implementation details
- Must include performance considerations
- Production-ready approach required

Requirements:
- Detailed implementation plan
- Code examples and architecture
- Performance analysis
- Risk mitigation strategies
- Testing and validation approach
- Monitoring and metrics

Output Requirements:
1. Show refinement metrics:
   - Number of iterations
   - Quality score for each iteration
   - Similarity scores between iterations
   - Convergence status and reason
   - Final quality score
2. Provide the refined deliverable with all sections needed for implementation
EOF

echo -e "${GREEN}✅ Refinement command generated!${NC}"
echo ""
echo -e "${YELLOW}Instructions:${NC}"
echo "1. Copy the command below"
echo "2. Paste it into this Claude session"
echo "3. Claude will use the incremental_refine tool to create a comprehensive solution"
echo ""
echo -e "${BLUE}=== COPY THIS COMMAND ===${NC}"
cat /tmp/refine_command.txt
echo -e "${BLUE}=========================${NC}"
echo ""
echo -e "${GREEN}The command has also been saved to: /tmp/refine_command.txt${NC}"