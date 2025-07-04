---
title: Critical Reminders
type: must_not_forget_safety_critical
maintenance: remove_resolved_add_new_critical
---

# Critical Reminders

## Claude CLI Usage (CRITICAL)
- **Command**: Use `claude` NOT `claude-code` on this system
- **Correct**: `claude --dangerously-skip-permissions`
- **Incorrect**: `claude-code --dangerously-skip-permissions`
- **Note**: System uses `claude` as the CLI command for Claude interactions
- **IMPORTANT**: Even with --dangerously-skip-permissions, user must manually approve Claude startup in tmux session

## Memory Conservation (CRITICAL)
- **Rule**: NEVER capture entire tmux pane scrollback (burns massive tokens)
- **Correct**: `tmux capture-pane -t [agent] -S -10 -p`
- **File Operations**: Use offset/limit for large files, surgical precision only

## Protocol Hierarchy (ACTIVE)
- **Idea Clarification**: STOP and ask 5 questions before implementation when user says "IDEA"
- **Discussion vs Action**: Questions are for exploration, not immediate execution
- **Complexity Radar**: Partner consultation required for >100 line changes

## Agent Deployment (IMPORTANT)
- **Deployment Method**: Commands in `.claude/COMMANDS/` are TEMPLATES - copy/paste to terminal to run
- **Six Agent System**: Copy from `deploy-agents.md`, paste to terminal
- **Three Stooges**: Copy from `three-stooges-deploy.md`, paste to terminal
- **Recursive Companion**: Use `recursive-companion-generator.md` to create refine/incremental_refine commands
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

## Preview Display Fix Requirements (CRITICAL)
- **Constraint**: Flags must persist indefinitely until manually reviewed
- **Failed Approaches**: Filtering by recent session, auto-cleanup, in-memory caching
- **Issue**: Preview shows historical data instead of current server state
- **Need**: Solution that shows current emails while preserving all flag history

## Todo Persistence (RESOLVED BUT CRITICAL)
- **Implementation**: save-v2.md Step 4.5 now saves todos to session-todos.md
- **Format**: JSON array compatible with TodoWrite tool
- **Filtering**: Only pending/in_progress todos saved (completed excluded)
- **Testing**: Needs validation with actual save/restore cycle

---
*Active warnings and safety-critical items only*