# AUTONOMOUS AI KITCHEN PROTOCOL

## Core Philosophy
**Agents execute, don't ask. Progress flows, doesn't stop.**

## Agent Authority Matrix

### AUTONOMOUS (No Approval Needed)
- **Security fixes** with established patterns (XSS escaping, SQL parameterization)
- **Code cleanup** (removing dead code, formatting, imports)
- **Template/CSS extraction** following established architecture
- **Documentation updates** reflecting completed work
- **Bug fixes** with clear root cause and solution
- **Performance optimizations** that don't change behavior

### REVIEW REQUIRED (Strategic Decisions)
- **Architecture changes** that affect multiple systems
- **New feature implementations** beyond current scope
- **Database schema modifications**
- **External dependency additions**
- **Breaking changes** to existing APIs

## Completion Protocols

### Auto-Handoff Triggers
1. **Work Complete** → Update TODO status → Deploy next agent automatically
2. **Blocked** → Log blocker → Escalate only if unresolvable
3. **Conflict** → Agents negotiate → Escalate only deadlocks
4. **Discovery** → Document finding → Continue with adjusted scope

### Progress Reporting
- **Status Updates**: Every 30 minutes via tmux capture
- **Milestone Alerts**: Only major completions (not permission requests)
- **Exception Escalation**: True conflicts or critical architectural decisions only

## Kitchen Orchestration Rules

### Agent Selection Algorithm
```
IF previous_agent_complete AND next_task_identified:
    auto_deploy_appropriate_specialist()
ELIF blocker_detected:
    attempt_autonomous_resolution()
    IF still_blocked: escalate_with_context()
ELSE:
    continue_monitoring()
```

### Conflict Resolution
1. **Same Domain**: Second agent waits or takes different approach
2. **Cross Domain**: Agents negotiate scope boundaries
3. **Resource Conflict**: Queue system with priority levels
4. **Deadlock**: Escalate with full context for quick decision

## Monitoring Dashboard

### Automated Status Tracking
- Real-time TODO list updates
- Progress percentage calculations  
- Completion time estimates
- Blocker identification and categorization

### Alert Thresholds
- **Green**: Normal progress, no alerts
- **Yellow**: Potential blocker, attempt auto-resolution  
- **Red**: True deadlock, immediate escalation needed

## Implementation Strategy

### Phase 1: Basic Automation
- Auto-deploy next logical agent when current completes
- Standard completion handoffs (security → optimization → testing)
- Simple conflict avoidance (domain separation)

### Phase 2: Smart Orchestration  
- Predictive agent scheduling based on dependencies
- Intelligent scope negotiation between agents
- Dynamic priority adjustment based on findings

### Phase 3: Full Autonomy
- Self-healing kitchen operations
- Adaptive agent specialization
- Zero-touch deployment pipelines

## Success Metrics
- **Approval Requests**: Reduce from current 100% to <5%
- **Handoff Time**: <2 minutes between agent deployments  
- **Conflict Resolution**: 90% auto-resolved without escalation
- **Progress Velocity**: 3x faster completion with parallel operations

## Emergency Protocols
- **Full Stop**: User override halts all operations immediately
- **Rollback**: Automatic revert if critical issues detected
- **Manual Override**: User can take control of any agent at any time

---

*Goal: Transform AI collaboration from human-bottlenecked to human-orchestrated autonomous operations*