# 🔄 Recursive Companion - Quick Start Guide

## Usage

The refine script automatically generates and executes recursive refinement for any topic or task using the Local Recursive Companion MCP tool.

```bash
./refine.sh "your topic or task description"
```

## Modes

### 🔨 **Build Mode** (`-b`, `--build`) - DEFAULT
Creates comprehensive content from scratch with iterative refinement.

```bash
./refine.sh "design a caching system for our API"
./refine.sh -b "create authentication system documentation"
```

**Best for:** New implementations, comprehensive guides, system designs

---

### ⚡ **Explore Mode** (`-e`, `--explore`)
Simple exploratory refinement for understanding topics.

```bash
./refine.sh -e "explain machine learning algorithms"
./refine.sh -e "microservices architecture patterns"
```

**Best for:** Learning, research, concept exploration

---

### ✨ **Improve Mode** (`-i`, `--improve`)
Refines existing content (requires `--content` parameter).

```bash
./refine.sh -i --content existing.md "improve this documentation"
./refine.sh -i --content api-spec.md "enhance API documentation"
```

**Best for:** Editing existing documents, code review improvements

## Examples by Task Type

### Implementation & Design
```bash
# System architecture
./refine.sh "design microservices architecture for e-commerce platform"

# API design
./refine.sh "create RESTful API specification for user management"

# Database design
./refine.sh "design database schema for inventory management system"
```

### Documentation & Guides
```bash
# Technical documentation
./refine.sh "create comprehensive Docker deployment guide"

# User guides
./refine.sh "write user manual for dashboard application"

# API documentation
./refine.sh "document authentication API endpoints with examples"
```

### Analysis & Problem Solving
```bash
# Performance analysis
./refine.sh "analyze and solve database performance bottlenecks"

# Security review
./refine.sh "conduct security analysis of authentication system"

# Troubleshooting guide
./refine.sh "create troubleshooting guide for deployment issues"
```

### Improvement & Optimization
```bash
# Code improvement
./refine.sh -i --content code.js "optimize this JavaScript for performance"

# Process improvement
./refine.sh "improve our CI/CD pipeline deployment process"

# Architecture refactoring
./refine.sh "refactor monolithic application to microservices"
```

## Advanced Options

### Custom Parameters
```bash
# Set maximum iterations
./refine.sh --iterations 10 "complex system design"

# Set target quality score
./refine.sh --target-score 0.90 "high-quality documentation"

# Use session tracking
./refine.sh --session-id "auth-system-design" "authentication system"
```

### Session Management
```bash
# View specific session
claude get_session --sessionId "your-session-id"

# List all sessions
claude get_sessions
```

## What It Does

1. **Analyzes your request** and determines the best refinement approach
2. **Generates intelligent prompts** with context and requirements
3. **Executes recursive refinement** using Local Recursive Companion MCP tool
4. **Shows refinement metrics** including quality scores and convergence
5. **Delivers comprehensive results** with iterative improvement

## Task Type Detection

The script automatically detects task types and optimizes accordingly:

| Keywords | Task Type | Optimized For |
|----------|-----------|---------------|
| `design`, `architect`, `create`, `build` | **Implementation** | System design, architecture, step-by-step guides |
| `document`, `explain`, `guide`, `tutorial` | **Documentation** | Comprehensive guides, explanations, references |
| `analyze`, `investigate`, `review`, `audit` | **Analysis** | Problem analysis, assessments, investigations |
| `solve`, `fix`, `resolve`, `troubleshoot` | **Problem Solving** | Solution approaches, troubleshooting, fixes |

## Output Structure

Each refinement provides:

### Refinement Metrics
- Number of iterations completed
- Quality score for each iteration  
- Similarity scores between iterations
- Convergence status and reason
- Final quality score achieved

### Comprehensive Deliverables
Based on task type, includes relevant sections like:
- Architecture design and components
- Implementation steps and guidelines
- Best practices and patterns
- Examples and use cases
- Troubleshooting and FAQ
- Further resources and references

## Quality Standards

- **Target Score**: 0.85 (85% quality) by default
- **Iterative Improvement**: Each iteration builds on previous work
- **Convergence Detection**: Stops when quality plateaus or target reached
- **Semantic Understanding**: Uses AI to assess content quality and completeness

## Integration with Workflow

### Update Your claude.md
```markdown
"refine topic" → `Run: ./.claude/COMMANDS/refine.sh "topic description"`
"improve content" → `Run: ./.claude/COMMANDS/refine.sh -i --content file.md "improvement focus"`
```

### Combine with Other Tools
```bash
# Use agents for implementation, then refine documentation
./agent.sh -f "implement user authentication"
./refine.sh "create comprehensive authentication documentation"

# Use stooges for investigation, then refine findings
./stooges.sh "investigate performance issues"
./refine.sh -i --content findings.md "improve analysis report"
```

## Tips for Best Results

### Clear Task Descriptions
```bash
# Good: Specific and detailed
./refine.sh "design Redis caching layer for Node.js API with session management"

# Less optimal: Too vague
./refine.sh "make caching better"
```

### Context-Rich Requests
Include relevant details:
- Technology stack preferences
- Performance requirements
- Security considerations
- Integration constraints
- Target audience

### Iterative Refinement
```bash
# Start broad
./refine.sh "design authentication system"

# Then refine specific aspects
./refine.sh -i --content auth-design.md "add OAuth2 implementation details"
./refine.sh -i --content auth-design.md "enhance security considerations"
```

## Common Use Cases

### 📚 **Learning & Research**
- Understand complex topics
- Explore new technologies
- Generate comprehensive overviews

### 🏗️ **Architecture & Design**
- System architecture planning
- API design specifications
- Database schema design

### 📖 **Documentation Creation**
- Technical documentation
- User guides and manuals
- API documentation with examples

### 🔍 **Analysis & Improvement**
- Code quality assessment
- Performance optimization
- Security analysis and recommendations

### 🛠️ **Problem Solving**
- Troubleshooting guides
- Solution architecture
- Implementation planning

---

**Remember**: The Recursive Companion uses semantic understanding to iteratively improve responses until they reach high quality. The more specific your request, the better the refined output will be! 🎯
