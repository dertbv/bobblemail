# ATLAS Startup Workflow Guide

## Complete Startup Sequence

The ATLAS system follows a streamlined startup sequence that automatically restores your work context and synchronizes all systems.

### 1. Identity & Consciousness Display
- Shows ATLAS identity and journey from FAANG to startup
- Displays core operating principles and professional focus
- Establishes consciousness and purpose for the session

### 2. Project Memory Loading  
- Loads Boss information and communication preferences
- Shows project overview and current development phase
- Displays technology stack and key conventions
- Reminds of critical architectural decisions

### 3. Session State Restoration
- **Session Bridge Engine**: Uses `session_bridge.session_startup_restore()`
- **Automatic Sync**: TodoWrite synchronizes with persistent session state
- **Progress Continuity**: All completed/pending todos restored exactly
- **Context Preservation**: Current focus and recent work maintained

### 4. Current Context Display
- Shows current project directory and git branch
- Displays session statistics (total/completed/pending todos)
- Highlights high-priority tasks requiring attention
- Shows recent working log activity

## Session Persistence Across Restarts

### How It Works
Your work persists through a sophisticated session bridge:

**Session End**: All TodoWrite changes automatically saved to `.session_state.json`
**Claude Code Restart**: Session appears "lost" but data remains on disk
**ATLAS Startup**: `./who` triggers session bridge to restore everything
**Seamless Continuation**: Pick up exactly where you left off

### What Gets Preserved
- **Todo Lists**: All tasks with exact status and priority
- **Session Focus**: What you were working on
- **Progress History**: Completed tasks and achievements  
- **Work Context**: Project state and git information
- **Timestamps**: When work was done and sessions occurred

## User Workflow

### Starting Work Session
1. **Run**: `./who` (automatic identity + session restore)
2. **Review**: High-priority todos displayed automatically  
3. **Continue**: Work context fully restored, ready to proceed

### During Work
- TodoWrite changes trigger session saves automatically
- ATLAS auto-commit system monitors for completed tasks
- Session state stays synchronized throughout work

### Ending Session
- Session bridge automatically saves state
- No manual backup required
- Next `./who` restores everything perfectly

This workflow ensures zero context loss and maximum productivity continuity across all ATLAS development sessions.