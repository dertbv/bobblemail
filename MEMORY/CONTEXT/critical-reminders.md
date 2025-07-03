---
title: Critical Reminders
type: must_not_forget_safety_critical
maintenance: remove_resolved_add_new_critical
---

# Critical Reminders

## Memory Conservation (CRITICAL)
- **Rule**: NEVER capture entire tmux pane scrollback (burns massive tokens)
- **Correct**: `tmux capture-pane -t [agent] -S -10 -p`
- **File Operations**: Use offset/limit for large files, surgical precision only

## Protocol Hierarchy (ACTIVE)
- **Idea Clarification**: STOP and ask 5 questions before implementation when user says "IDEA"
- **Discussion vs Action**: Questions are for exploration, not immediate execution
- **Complexity Radar**: Partner consultation required for >100 line changes

## Agent Deployment (IMPORTANT)
- **Results Preservation**: NEVER remove agent worktrees without extracting results first
- **iTerm2 Commands**: Always provide native integration commands after deployment
- **Autonomous Authority**: Include "option 2 yes and don't ask again" in missions

## Partnership Communication (ACTIVE)
- **Boss (Bobble)**: Direct feedback style, values working solutions over elegant architecture
- **UI/UX Changes**: Ask about ALL elements in affected area, don't modify related items
- **Email Research**: Use Atlas_Email analyzer tool for email research requests

## Template Implementation (CRITICAL)
- **Discovered**: Templates created but NOT connected to app.py routes
- **Status**: 2,781 lines in templates, but app.py still generates HTML inline (5,604 lines)
- **Action Required**: Must connect templates using templates.TemplateResponse()
- **Priority**: Blocking all other frontend improvements

## Security Protocols (ONGOING)
- **Whitelist Prohibition**: Never suggest adding domains/emails to lists unless user requests
- **Input Validation**: All user inputs require sanitization and validation
- **Authentication**: SPF/DKIM/DMARC validation before spam detection

## Development Standards (ACTIVE)
- **KISS Checkpoints**: Simplest solution that works, partner consultation for major changes
- **Git Discipline**: Stage confidently, request review, commit only after QA approval
- **Information Entropy**: Document only surprising, valuable, or critical information

## Todo Persistence (RESOLVED BUT CRITICAL)
- **Implementation**: save-v2.md Step 4.5 now saves todos to session-todos.md
- **Format**: JSON array compatible with TodoWrite tool
- **Filtering**: Only pending/in_progress todos saved (completed excluded)
- **Testing**: Needs validation with actual save/restore cycle

---
*Active warnings and safety-critical items only*