# 🤖 SIX AGENT SYSTEM MISSION GENERATOR

## PURPOSE
Automatically generate comprehensive missions for Six Agent System deployment based on user requests.

## MISSION TEMPLATE

When user says "Deploy agents to [TASK]", create this file as AGENT_MISSION.md:

```markdown
# MISSION: [TASK TITLE]

## 🎯 PRIMARY OBJECTIVE
[Clear statement of what needs to be accomplished]

## 📋 DETAILED REQUIREMENTS

### Functional Requirements
1. [Specific feature/fix/analysis needed]
2. [Expected behavior/output]
3. [Success criteria]

### Technical Constraints
- **Codebase**: [Relevant directories/files]
- **Dependencies**: [External systems/APIs]
- **Performance**: [Speed/scale requirements]
- **Compatibility**: [Browser/platform requirements]

## 🔍 INVESTIGATION SCOPE

### Primary Investigation Areas
1. **[Component/System 1]**: [What to investigate]
2. **[Component/System 2]**: [What to analyze]
3. **[Integration Points]**: [How systems connect]

### Required Documentation Review
- `docs/[relevant-guide].md` - [Why needed]
- `LEARNINGS.md` - [Specific patterns to check]
- Recent reports in `reports/` - [What to look for]

## 📦 REQUIRED DELIVERABLES

### 1. WORK.md (Planner Output)
- Root cause analysis
- Solution architecture
- Task breakdown for all agents
- Risk assessment

### 2. Implementation Files (Executer Output)
- [ ] Core feature implementation
- [ ] Integration code
- [ ] Configuration updates
- [ ] Migration scripts (if needed)

### 3. Test Suite (Tester Output)
- [ ] Unit tests with >90% coverage
- [ ] Integration tests
- [ ] Edge case scenarios
- [ ] Performance benchmarks

### 4. Documentation (Documenter Output)
- [ ] Technical documentation
- [ ] API documentation (if applicable)
- [ ] User guide updates
- [ ] Troubleshooting guide

### 5. Verification Report (Verifier Output)
- [ ] All requirements met
- [ ] Quality standards passed
- [ ] Security review complete
- [ ] Performance validated

## 🚀 EXECUTION PREFERENCES

### Development Approach
- **Methodology**: [TDD/BDD/Iterative]
- **Code Style**: Follow existing patterns in codebase
- **Error Handling**: Comprehensive with proper logging
- **Security**: Input validation, sanitization required

### Agent Coordination
- **Parallelization**: [Which tasks can run simultaneously]
- **Dependencies**: [Task ordering requirements]
- **Communication**: Update WORK.md after each phase
- **Iteration**: Max 2 rounds if quality < 90%

## ⚠️ CRITICAL WARNINGS
[Any specific pitfalls to avoid based on task type]

## 🎲 AUTONOMOUS AUTHORITY
You have full authority to:
- Make implementation decisions within these constraints
- Create necessary files and directories
- Refactor existing code for better integration
- Add dependencies if absolutely necessary (document why)

Begin by reading all *AGENT*.md files to understand your roles, then start with PLANNER to create comprehensive WORK.md.
```

## TASK EXTRACTION PATTERNS

### From: "Deploy agents to implement user authentication"
Extract:
- **Action**: implement
- **Target**: user authentication system
- **Deliverables**: auth system, tests, docs, security review

### From: "Deploy agents to refactor the email processing pipeline"
Extract:
- **Action**: refactor
- **Target**: email processing pipeline
- **Deliverables**: refactored code, migration plan, tests, performance report

### From: "Deploy agents to add real-time notifications"
Extract:
- **Action**: add feature
- **Target**: real-time notification system
- **Deliverables**: WebSocket implementation, UI components, tests, docs

## STANDARD ENHANCEMENTS BY TASK TYPE

### For Feature Implementation:
- Database schema changes
- API endpoint specifications
- Frontend component requirements
- State management approach
- Rollback procedures

### For Bug Fixes:
- Steps to reproduce
- Root cause investigation areas
- Regression test requirements
- Monitoring additions
- Fix verification criteria

### For Refactoring:
- Current pain points
- Desired architecture
- Migration strategy
- Backwards compatibility
- Performance targets

### For Analysis Tasks:
- Current state assessment
- Problem identification
- Solution options with tradeoffs
- Implementation roadmap
- Resource estimates

## DEPLOYMENT STEPS

1. **Parse user request**
   - Extract primary action
   - Identify target system
   - Determine task type
   - List expected deliverables

2. **Generate mission file**
   - Use template above
   - Fill in all sections
   - Add task-specific enhancements
   - Include relevant file paths

3. **Deploy automatically**
   ```bash
   MISSION_NAME="[descriptive-name]"
   git worktree add -b agent-system-$MISSION_NAME ./Agents/agent-system-$MISSION_NAME
   cp Agents/*\ AGENT.md ./Agents/agent-system-$MISSION_NAME/
   # Create AGENT_MISSION.md in worktree
   tmux new-session -d -s agent-system-$MISSION_NAME -c $(pwd)/Agents/agent-system-$MISSION_NAME
   tmux send-keys -t agent-system-$MISSION_NAME "claude --dangerously-skip-permissions" Enter
   sleep 3
   tmux send-keys -t agent-system-$MISSION_NAME "Read the *AGENT*.md files and AGENT_MISSION.md. Implement the six-agent system to accomplish this mission." Enter
   ```

4. **Monitor progress**
   - Check for WORK.md creation
   - Monitor implementation progress
   - Watch test results
   - Track verification scores

5. **Extract results**
   - Copy all deliverables to main repo
   - Organize by type (code/tests/docs)
   - Create summary report
   - Clean up worktree

## QUALITY STANDARDS

All agent outputs must meet:
- **Code**: Follows project conventions, properly tested
- **Tests**: >90% coverage, edge cases included
- **Docs**: Clear, complete, with examples
- **Security**: No vulnerabilities introduced
- **Performance**: Meets or exceeds requirements

## ERROR RECOVERY

If agents stall:
1. Check last agent output
2. Send clarification via tmux
3. If VERIFIER rejects, agents auto-iterate
4. If stuck >10 min, provide additional context

---

*This generator ensures comprehensive, well-structured Six Agent deployments for complex implementation tasks!*