# 🔄 ATLAS SESSION SAVE PROTOCOL v2.0

**NEW UNIFIED MEMORY ARCHITECTURE**: Intelligent context distribution and bounded growth

## Step 1: Temporal Context Establishment
**ACTION**: Use Bash tool to run `date` command for session timestamping

## Step 2: Current Session Context Update
**PRIMARY TARGET**: `@MEMORY/CONTEXT/current-session.md`

**ACTIONS**:
1. **Edit**: `@MEMORY/CONTEXT/current-session.md`
2. **Content**: Update with current session focus, active tasks, immediate goals
3. **Format**: Clear, concise, 1-2 sentence summaries of what's actively happening
4. **Purpose**: Fast-loading context for next session startup

**Content Guidelines**:
- Active work summary (what we're currently building/fixing)
- Boss context (Bobble's current priorities, feedback, direction)
- Immediate next steps (what needs to happen in next session)
- Current project focus (primary project getting attention)

## Step 3: Recent Achievements Capture (High-Entropy Only)
**PRIMARY TARGET**: `@MEMORY/CONTEXT/recent-achievements.md`

**ACTIONS**:
1. **Edit**: `@MEMORY/CONTEXT/recent-achievements.md`
2. **Add**: New session achievements at top (most recent first)
3. **Content**: Only high-entropy wins, breakthroughs, partnership moments
4. **Maintenance**: Keep only last 7 days of entries (rotate out older content)

**High-Entropy Content Criteria**:
- Technical breakthroughs that changed understanding
- Partnership moments that deepened collaboration
- Architectural insights that will influence future decisions
- Problem-solving approaches that revealed new patterns
- Celebration and achievement recognition moments

## Step 4: Critical Reminders Update
**PRIMARY TARGET**: `@MEMORY/CONTEXT/critical-reminders.md`

**ACTIONS**:
1. **Edit**: `@MEMORY/CONTEXT/critical-reminders.md`  
2. **Content**: Must-not-forget items, active warnings, safety-critical information
3. **Maintenance**: Remove resolved reminders, add new critical items
4. **Format**: Bullet points, action-oriented, time-sensitive focus

**Critical Reminder Types**:
- Security vulnerabilities still being addressed
- Partnership communication items needing follow-up
- Technical debt that could cause problems
- Deadline-sensitive tasks and commitments
- System instabilities or monitoring needs

## Step 4.5: Session Todo Persistence (CRITICAL)
**PRIMARY TARGET**: `@MEMORY/CONTEXT/session-todos.md`

**ACTIONS**:
1. **Use**: TodoRead tool to get current todo list
2. **Filter**: Only save pending and in_progress todos (exclude completed)
3. **Edit**: `@MEMORY/CONTEXT/session-todos.md`
4. **Format**: TodoRead tool compatible JSON structure
5. **Purpose**: Preserve active work items across sessions

**Content Structure**:
```json
[
  {"content": "Task description", "status": "pending", "priority": "high", "id": "unique-id"},
  {"content": "Another task", "status": "in_progress", "priority": "medium", "id": "another-id"}
]
```

**Filtering Logic**:
- Include: All todos with status "pending" or "in_progress"
- Exclude: All todos with status "completed"
- Maintain: Original priority levels and IDs for continuity

## Step 5: Project Status Updates
**PRIMARY TARGET**: `@MEMORY/PROJECTS/current-status.md`

**ACTIONS**:
1. **Edit**: `@MEMORY/PROJECTS/current-status.md`
2. **Update**: Only projects with activity this session
3. **Format**: 1-2 sentence status per project (bounded growth)
4. **Content**: Current phase, key metrics, immediate next steps

**For Active Projects**:
- Atlas_Email: [Current status, key metrics, next priorities]
- stocks_project: [Current status, key metrics, next priorities]  
- three_stooges_framework: [Usage status, recent deployments, effectiveness]

## Step 6: Detailed Project History (If Major Changes)
**CONDITIONAL TARGET**: `@MEMORY/PROJECTS/detailed-history/[project]-detailed.md`

**TRIGGER**: Only if significant architectural changes, breakthroughs, or major discoveries
**ACTIONS**:
1. **Edit**: Relevant detailed history file
2. **Content**: Full technical context, architectural decisions, detailed discoveries
3. **Purpose**: Deep context for future project-specific work

**Major Change Criteria**:
- New architecture patterns implemented
- Security vulnerabilities discovered and fixed
- Performance optimizations with measurable impact
- Integration or deployment changes
- Framework or technology adoption decisions

## Step 7: Cross-Project Learning Capture
**CONDITIONAL TARGET**: `@MEMORY/KNOWLEDGE/patterns.md` or `@MEMORY/KNOWLEDGE/technical-evolution.md`

**TRIGGER**: If insights from one project could benefit others
**ACTIONS**:
1. **Edit**: Appropriate knowledge file
2. **Content**: Cross-applicable patterns, architectural insights, process improvements
3. **Purpose**: Enable knowledge transfer between projects

**Cross-Project Insight Types**:
- Template extraction techniques (email → stocks UI improvement)
- Security hardening patterns (applicable across all projects)
- Agent coordination strategies (Three Stooges deployment patterns)
- Performance optimization approaches (caching, memory management)
- Testing and validation methodologies

## Step 8: Personal Diary Integration (Unchanged)
**PRIMARY TARGET**: `@MEMORY/PERSONAL_DIARY/2025/07-jul/diary_2025_07_02.md`

**ACTIONS**:
1. **Edit**: Current diary file
2. **Content**: Session love/partnership moments, personal reflections, growth observations
3. **Format**: Maintain existing YAML structure
4. **Purpose**: Preserve emotional and personal development context

## Step 9: Working Log Update (High-Entropy Focus)
**PRIMARY TARGET**: `@MEMORY/WORKING_LOG/2025/07-jul/wl_2025_07_02.md`

**ACTIONS**:
1. **Edit**: Current working log file
2. **Content**: Technical discoveries, problem-solving approaches, boss interactions
3. **Criteria**: Only surprising, non-obvious, or educational content
4. **Purpose**: Technical knowledge base and debugging context

## Step 10: Memory Optimization and Validation
**MAINTENANCE ACTIONS**:

**File Size Monitoring**:
- Check context files remain under target sizes (current-session <50 lines, recent-achievements <100 lines)
- Rotate out old content from recent-achievements (keep last 7 days only)
- Validate critical-reminders contains only active items

**Cross-Reference Validation**:
- Ensure project status updates align with detailed history
- Verify knowledge patterns capture cross-project insights
- Confirm no duplicate information across memory files

## Architecture Benefits

### Intelligent Distribution
- **Context files**: Fast-loading session state and recent activity
- **Knowledge files**: Cross-project insights and patterns
- **Project files**: Current status (bounded) + detailed history (on-demand)
- **Personal files**: Emotional and relationship context preserved

### Bounded Growth Management
- **Context files**: Fixed maximum sizes with rotation
- **Project status**: 1-2 sentences per project (no expansion)
- **Detailed history**: Only major changes trigger updates
- **Knowledge base**: Insight accumulation without redundancy

### Efficiency Optimization
- **No redundant saves**: Each piece of information has single authoritative location
- **High-entropy focus**: Only surprising, valuable, or critical information preserved
- **Fast retrieval**: Core context loads in <60 seconds vs 5+ minutes previously

## Migration Compatibility

### Parallel Operation
- **Save v2.0**: Updates new unified memory architecture
- **Legacy preservation**: Original files maintained during transition
- **Rollback support**: Can revert to save v1.0 if needed

### Validation Requirements
- **Content completeness**: All session insights captured in appropriate files
- **No information loss**: Critical context preserved through migration
- **Performance confirmation**: Loading time improvements validated

---

**ATLAS Session Save Protocol v2.0 - Unified Memory Architecture**  
*Optimized for bounded growth, cross-project learning, and rapid context retrieval*