# 🎭 THREE STOOGES MISSION GENERATOR

## PURPOSE
Automatically generate perfect prompts for Three Stooges deployment based on simple user requests.

## PROMPT TEMPLATE

When user says "Deploy stooges to [TASK]", create this file as STOOGES_MISSION.md:

```markdown
<System>
You are building an **Agentic Loop** that can tackle any complex task with minimal role bloat.

**Core principles**
[Include all 6 principles from agent.md]
</System>

<Context>
**Task**: [EXTRACTED TASK DESCRIPTION]
**Repo path (if any)**: [/path/to/relevant/files OR none]
**Desired parallelism**: 0  (sequential - act as all three in order)

The Orchestrator must decide:
- Whether to specialize the workflow to this repo or keep it generic.
- How many identical Specialist instances to launch (0 = sequential).
</Context>

<Instructions>
[Include full instructions for Bootstrap, Moe, Larry, Curly, Consolidate from agent.md]
</Instructions>

<Constraints>
[Include all constraints from agent.md]
</Constraints>

<Output Format>
[Include output format from agent.md]
</Output Format>

<User Input>
```
[SPECIFIC TASK WITH REQUIREMENTS]

Required Deliverables:
1. Comprehensive analysis document
2. Implementation blueprint with concrete steps
3. Risk assessment and mitigation strategies
4. Resource requirements and timeline
5. Quality evaluation with numeric score

Make sure all outputs are production-ready and actionable.
```
</User Input>
```

## TASK EXTRACTION PATTERNS

### From: "Deploy stooges to analyze the Atlas Email performance plan"
Extract:
- **Action**: analyze
- **Target**: Atlas Email performance plan
- **Deliverables**: analysis, critique, blueprint

### From: "Deploy stooges to review and improve the recursive refinement"
Extract:
- **Action**: review and improve
- **Target**: recursive refinement implementation
- **Deliverables**: review report, improvements, implementation

### From: "Deploy stooges to create security audit for email system"
Extract:
- **Action**: create security audit
- **Target**: email system
- **Deliverables**: audit report, vulnerabilities, fixes

## DEPLOYMENT STEPS

1. **Parse user request**
   - Extract action verb(s)
   - Identify target system/plan/code
   - Determine expected deliverables

2. **Generate mission file**
   - Use template above
   - Fill in specific task details
   - Add relevant repo paths

3. **Deploy automatically**
   ```bash
   git worktree add --detach /Users/Badman/Desktop/playground/stooges-[task]-work
   tmux new-session -d -s stooges-work -c /path/to/worktree
   tmux send-keys -t stooges-work "claude --dangerously-skip-permissions" Enter
   sleep 3
   tmux send-keys -t stooges-work "Please read and execute STOOGES_MISSION.md" Enter
   ```

4. **Monitor progress**
   - Check for context.md creation
   - Watch for specialist.md output
   - Track Curly's scores

5. **Extract results**
   - Copy all docs/[task]/ files to main repo
   - Organize into appropriate folders
   - Create summary report

## STANDARD ENHANCEMENTS

Always add these to any task:

### For Analysis Tasks:
- Provide executive summary
- Include SWOT analysis
- Suggest quick wins vs long-term improvements
- Estimate implementation effort

### For Implementation Tasks:
- Include test cases
- Provide rollback procedures
- Document dependencies
- Create deployment checklist

### For Review Tasks:
- Use scoring rubric
- Prioritize findings
- Provide specific code examples
- Include before/after comparisons

## ERROR HANDLING

If stooges get stuck:
1. Check if they're waiting for input
2. Send clarification via tmux
3. If blocked > 5 minutes, restart with clearer mission

---

*This generator ensures consistent, high-quality Three Stooges deployments every time!*