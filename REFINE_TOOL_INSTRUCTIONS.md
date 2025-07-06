# 🔄 Recursive Refinement Tool Instructions

## For ATLAS: How to Use the Refine Tool

### Quick Usage
When user says "refine [topic]", run:
```bash
./.claude/COMMANDS/refine-working.sh "topic description"
```

### Important Notes for ATLAS
1. **The refine.sh script is BROKEN** - Use `refine-working.sh` instead
2. **MCP tools (incremental_refine) only work INSIDE Claude sessions**, not via CLI
3. **The script generates a command that must be pasted into Claude**
4. **I (ATLAS) have direct access to incremental_refine tool** - I can run it directly after the script generates the command

### Workflow
1. User requests refinement: "refine spam pipeline optimization"
2. I run: `./.claude/COMMANDS/refine-working.sh "spam pipeline optimization"`
3. Script outputs the incremental_refine command
4. I copy that command and run it directly using my MCP tool access
5. Recursive refinement executes with quality scores and iterations

### Common Use Cases
```bash
# Optimization
./refine-working.sh "optimize database query performance"

# Architecture Design
./refine-working.sh "design microservices architecture for payment system"

# Problem Solving
./refine-working.sh "solve memory leak in Node.js application"

# Documentation
./refine-working.sh "create comprehensive API documentation"

# Analysis
./refine-working.sh "analyze security vulnerabilities in authentication"
```

### Script Locations
- **Working Script**: `/Users/Badman/Desktop/email/.claude/COMMANDS/refine-working.sh`
- **Broken Script**: `/Users/Badman/Desktop/email/.claude/COMMANDS/refine.sh` (DO NOT USE)
- **Output**: Commands saved to `/tmp/refine_command.txt`

### How It Works
1. Script takes user's task description
2. Wraps it with context and requirements
3. Formats it as an incremental_refine tool command
4. Outputs command for copying into Claude

### For Future ATLAS Sessions
Add to CLAUDE.md:
```markdown
- "refine topic" → `Run: ./.claude/COMMANDS/refine-working.sh "topic description"`
```

### Technical Details
- The Local Recursive Companion MCP server provides `incremental_refine` and `refine` tools
- These tools iterate on responses until quality score ≥ 0.85 or convergence
- Shows metrics: iterations, quality scores, similarity, convergence reason
- Only accessible within Claude sessions, not via claude CLI

### Troubleshooting
- If "command not found": Check script exists at `.claude/COMMANDS/refine-working.sh`
- If "permission denied": Run `chmod +x .claude/COMMANDS/refine-working.sh`
- If MCP errors: The tool only works inside Claude, not from command line

---
*Created: 2025-07-05 | Purpose: Ensure ATLAS can always use recursive refinement correctly*