# 🔄 RECURSIVE COMPANION GENERATOR

## PURPOSE
Generate perfect prompts for Local Recursive Companion MCP tool based on user's topic/task.

## USAGE
When user says "refine [TOPIC/TASK]" or "recursive [TOPIC/TASK]", generate the appropriate command.

## PROMPT TEMPLATES

### For incremental_refine (building comprehensive content from scratch):

```
Use the incremental_refine tool with this prompt:

[TASK DESCRIPTION IN DETAIL]

Context:
[RELEVANT CONTEXT POINTS - extract from user's description]

Requirements:
[SPECIFIC REQUIREMENTS - what the output should include]

Output Requirements:
1. Show refinement metrics:
   - Number of iterations
   - Quality score for each iteration
   - Similarity scores between iterations
   - Convergence status and reason
   - Final quality score
2. Provide the refined [DELIVERABLE TYPE] with:
   [SPECIFIC SECTIONS/COMPONENTS NEEDED]
```

### For refine (improving existing content):

```
Use the refine tool to improve this response:

[EXISTING CONTENT TO REFINE]

Focus Areas:
- [SPECIFIC ASPECTS TO IMPROVE]
- [QUALITY CRITERIA]
```

### For simple exploratory refinement:

```
Use the incremental_refine tool to create a comprehensive explanation of [TOPIC]
```

## EXAMPLE USAGE

**User**: "I need to design a caching system for our API"

**Generated Command**:
```
Use the incremental_refine tool with this prompt:

Design a caching system for API endpoints to improve performance and reduce database load.

Context:
- Need to cache API responses
- Multiple endpoints with different caching requirements
- Must handle cache invalidation

Requirements:
- Caching strategy for different endpoint types
- Cache invalidation mechanisms
- Performance metrics and monitoring
- Implementation approach

Output Requirements:
1. Show refinement metrics:
   - Number of iterations
   - Quality score for each iteration
   - Similarity scores between iterations
   - Convergence status and reason
   - Final quality score
2. Provide the refined implementation plan with:
   - Cache architecture design
   - Technology recommendations
   - Implementation steps
   - Cache invalidation strategy
   - Monitoring and metrics approach
```

## KEY PATTERNS

1. **Always include metrics requirement** - Users want to see the refinement process
2. **Be specific about deliverables** - List exactly what sections/components needed
3. **Include context** - Extract relevant background from user's request
4. **Structure requirements clearly** - Bullet points for clarity

## QUICK TEMPLATES

### Technical Implementation:
"Use the incremental_refine tool to design [SYSTEM/FEATURE] that [DOES WHAT]. Include implementation steps, architecture decisions, and edge case handling."

### Documentation:
"Use the incremental_refine tool to create comprehensive documentation for [TOPIC] including overview, detailed explanation, examples, and best practices."

### Problem Solving:
"Use the incremental_refine tool to solve [PROBLEM] considering [CONSTRAINTS]. Include analysis, multiple solutions, tradeoffs, and recommended approach."

### Code Review/Improvement:
"Use the refine tool to improve this [CODE/DESIGN]: [PASTE CODE]. Focus on [SPECIFIC ASPECTS]."

---

*Note: The Local Recursive Companion uses semantic understanding to iteratively improve responses until they reach high quality (typically 85%+ score) or converge.*