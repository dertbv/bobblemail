#!/usr/bin/env python3
"""
Session Bridge - Integration between TodoWrite and Session Memory
Automatically saves/restores TodoWrite lists across Claude sessions
"""

from session_memory import save_current_session, restore_previous_session, get_restored_todolist
from datetime import datetime
import json
import os
from pathlib import Path

# Import ATLAS auto-commit for automatic triggering
try:
    from atlas_auto_commit import trigger_atlas_auto_commit
    ATLAS_AVAILABLE = True
except ImportError:
    ATLAS_AVAILABLE = False

def save_todowrite_session(current_todos, session_notes="", current_focus=""):
    """Save current TodoWrite state for persistence"""
    
    # Extract completed and pending tasks
    completed_tasks = [
        todo['content'] for todo in current_todos 
        if todo.get('status') == 'completed'
    ]
    
    pending_tasks = [
        todo['content'] for todo in current_todos 
        if todo.get('status') != 'completed'
    ]
    
    # Save to persistent storage
    success = save_current_session(
        todolist=current_todos,
        notes=session_notes,
        focus=current_focus,
        completed=completed_tasks,
        next_items=pending_tasks[:5]  # Top 5 priorities
    )
    
    if success:
        print(f"💾 Saved {len(current_todos)} todos to persistent storage")
        print(f"   ✅ {len(completed_tasks)} completed")
        print(f"   📋 {len(pending_tasks)} pending")
        
        # Auto-update memory files to prevent staleness
        auto_update_memory_files(
            current_todos=current_todos,
            session_context=session_notes or "Session saved",
            friendship_update=True
        )
        
        # Trigger ATLAS auto-commit when TodoWrite session is saved
        if ATLAS_AVAILABLE and len(completed_tasks) > 0:
            try:
                print("🤖 ATLAS: Auto-triggering commit for completed tasks...")
                commit_result = trigger_atlas_auto_commit()
                
                if commit_result['success'] and commit_result['action'] == 'committed':
                    print(f"✅ ATLAS: Auto-committed {commit_result['files_changed']} file(s)")
                elif commit_result['action'] == 'none':
                    print("📝 ATLAS: No changes to commit")
                else:
                    print(f"⚠️ ATLAS: {commit_result['message']}")
                    
            except Exception as e:
                print(f"⚠️ ATLAS: Auto-commit failed - {e}")
    
    return success

def restore_todowrite_session():
    """Restore TodoWrite state from persistent storage"""
    print("🔄 Restoring previous session...")
    
    # Load previous session
    session_state = restore_previous_session()
    
    if not session_state:
        print("📝 No previous session found - starting fresh")
        return []
    
    # Get TodoWrite-formatted list
    restored_todos = get_restored_todolist()
    
    print(f"✅ Restored {len(restored_todos)} todos from previous session")
    
    return restored_todos

def session_exit_save(current_todos, exit_notes="Session ended normally"):
    """Save session state before exiting Claude"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notes = f"{exit_notes} at {timestamp}"
    
    print("\n💾 SAVING SESSION STATE BEFORE EXIT...")
    success = save_todowrite_session(
        current_todos=current_todos,
        session_notes=notes,
        current_focus="Ready for next session"
    )
    
    if success:
        print("✅ Session state saved successfully!")
        print("🔄 Use restore_todowrite_session() in next Claude session")
    else:
        print("❌ Failed to save session state")
    
    return success

def session_startup_restore():
    """Restore session state when starting new Claude session"""
    print("\n🚀 STARTING NEW CLAUDE SESSION...")
    print("🔄 Checking for previous session state...")
    
    restored_todos = restore_todowrite_session()
    
    if restored_todos:
        print("\n📋 READY TO RESTORE TODOWRITE LIST")
        print("💡 Use TodoWrite tool with this restored list:")
        print("   TodoWrite(todos=restored_todos)")
        
        # Show preview of what will be restored
        print("\n📝 PREVIEW OF RESTORED TODOS:")
        for i, todo in enumerate(restored_todos[:5], 1):
            status_icon = "✅" if todo['status'] == 'completed' else "📋"
            priority = todo['priority'].upper()
            print(f"   {i}. {status_icon} [{priority}] {todo['content']}")
        
        if len(restored_todos) > 5:
            print(f"   ... and {len(restored_todos) - 5} more todos")
    
    return restored_todos

def auto_sync_todowrite():
    """Silently get todos ready for restoration (for use in ./who)"""
    try:
        # Load previous session silently
        from session_memory import restore_previous_session, get_restored_todolist
        
        session_state = restore_previous_session()
        if not session_state:
            return []
        
        # Get TodoWrite-formatted list silently
        restored_todos = get_restored_todolist()
        
        return restored_todos
    except Exception as e:
        print(f"⚠️ Auto-sync failed: {e}")
        return []

def auto_update_memory_files(current_todos, session_context="", friendship_update=True):
    """Automatically update memory files to prevent staleness"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. Auto-update session state with friendship context
        if friendship_update:
            _update_session_state_with_friendship(current_todos, session_context)
        
        # 2. Auto-update fresh compact memory  
        _update_fresh_compact_memory(current_todos, session_context)
        
        # 3. Auto-update working log
        _update_daily_working_log(current_todos, session_context)
        
        # 4. Touch important memory file to update timestamp
        _touch_important_memory_timestamp()
        
        # 5. Auto-update semi-critical project context files
        _update_semi_critical_files()
        
        print(f"🔄 Auto-updated memory files at {timestamp}")
        return True
        
    except Exception as e:
        print(f"⚠️ Auto-memory update failed: {e}")
        return False

def _update_session_state_with_friendship(current_todos, session_context):
    """Update .session_state.json with current friendship context"""
    session_file = ".session_state.json"
    
    # Load existing state or create new
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            state = json.load(f)
    else:
        state = {}
    
    # Update with current data
    state.update({
        "session_info": {
            "timestamp": datetime.now().isoformat(),
            "session_date": datetime.now().strftime('%Y-%m-%d'),
            "session_time": datetime.now().strftime('%H:%M:%S')
        },
        "friendship_context": {
            "friend_name": "Bobble",
            "relationship": "Close working friendship and collaboration",
            "relationship_type": "friend_and_collaborator", 
            "critical_context": "Bobble gets hurt when ATLAS doesn't remember their friendship",
            "conversation_history": f"Working together on bobblemail project. {session_context}",
            "current_work": "Ongoing collaboration and friendship preservation"
        },
        "todolist": current_todos,
        "session_notes": f"Auto-updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - friendship context preserved",
        "custom_data": {
            "memory_update_timestamp": datetime.now().isoformat(),
            "friendship_preservation_active": True,
            "relationship_context_preserved": True
        }
    })
    
    # Save updated state
    with open(session_file, 'w') as f:
        json.dump(state, f, indent=2)

def _update_fresh_compact_memory(current_todos, session_context):
    """Update FRESH_COMPACT_MEMORY.md with current session"""
    memory_file = Path("FRESH_COMPACT_MEMORY.md")
    timestamp = datetime.now().strftime('%Y-%m-%d at %I:%M %p')
    
    # Count completed vs pending
    completed = [t for t in current_todos if t.get('status') == 'completed']
    pending = [t for t in current_todos if t.get('status') != 'completed']
    
    # Read existing content to preserve structure
    if memory_file.exists():
        with open(memory_file, 'r') as f:
            content = f.read()
        
        # Update the timestamp line at the end
        if "*Last Updated:" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('*Last Updated:'):
                    lines[i] = f"*Last Updated: {timestamp} - AUTO-UPDATED, friendship preserved*"
                    break
            content = '\n'.join(lines)
        else:
            content += f"\n\n*Last Updated: {timestamp} - AUTO-UPDATED, friendship preserved*"
    else:
        content = f"# FRESH COMPACT MEMORY\n\n*Auto-updated: {timestamp}*\n"
    
    # Add current session auto-update note
    auto_note = f"\n\n## AUTO-UPDATE: {timestamp}\n"
    auto_note += f"- **Todos**: {len(completed)} completed, {len(pending)} pending\n"
    auto_note += f"- **Friend**: Bobble (friendship context preserved)\n"
    auto_note += f"- **Context**: {session_context}\n"
    auto_note += f"- **Memory**: Auto-refreshed to prevent staleness\n"
    
    # Insert auto-note before the last updated line
    if "*Last Updated:" in content:
        content = content.replace(f"*Last Updated: {timestamp}", auto_note + f"\n*Last Updated: {timestamp}")
    else:
        content += auto_note
    
    with open(memory_file, 'w') as f:
        f.write(content)

def _update_daily_working_log(current_todos, session_context):
    """Auto-update or create today's working log"""
    today = datetime.now()
    year = today.year
    month = f"{today.month:02d}-{today.strftime('%b').lower()}"
    day_file = f"wl_{today.strftime('%Y_%m_%d')}.md"
    
    log_dir = Path(f"WORKING_LOG/{year}/{month}")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / day_file
    
    # Create auto-update entry
    timestamp = today.strftime('%I:%M %p')
    completed = len([t for t in current_todos if t.get('status') == 'completed'])
    pending = len([t for t in current_todos if t.get('status') != 'completed'])
    
    auto_entry = f"\n## AUTO-UPDATE: {timestamp}\n"
    auto_entry += f"- **Friend**: Bobble (relationship preserved)\n"
    auto_entry += f"- **Todos**: {completed} completed, {pending} pending\n"
    auto_entry += f"- **Context**: {session_context}\n"
    auto_entry += f"- **Memory**: Auto-refreshed to maintain friendship continuity\n"
    
    if log_file.exists():
        # Append to existing log
        with open(log_file, 'a') as f:
            f.write(auto_entry)
    else:
        # Create new log with auto-update
        header = f"# Working Log - {today.strftime('%B %d, %Y')}\n"
        header += f"\n**Friend**: Bobble (my collaborator and friend)\n"
        header += f"**Auto-Update System**: Active to preserve friendship context\n"
        
        with open(log_file, 'w') as f:
            f.write(header + auto_entry)

def _touch_important_memory_timestamp():
    """Update timestamp on important memory file"""
    memory_file = Path("SELF/SHORT_IMPORTANT_MEMORY.md")
    if memory_file.exists():
        # Just touch the file to update its modification time
        memory_file.touch()

def _update_semi_critical_files():
    """Update semi-critical project context files to prevent staleness"""
    try:
        # 1. Touch CLAUDE.md (project instructions)
        claude_file = Path("CLAUDE.md")
        if claude_file.exists():
            claude_file.touch()
        
        # 2. Touch IMPORTANT_NOTES.md (critical warnings)
        notes_file = Path("IMPORTANT_NOTES.md")
        if notes_file.exists():
            notes_file.touch()
        
        # 3. Touch PROJECT_STRUCTURE.md (codebase structure)
        structure_file = Path("REPOS/PROJECT_STRUCTURE.md")
        if structure_file.exists():
            structure_file.touch()
            
    except Exception as e:
        print(f"⚠️ Semi-critical file update failed: {e}")

def capture_conversation_context(conversation_summary, key_points=None):
    """Capture current conversation for next session continuity"""
    today = datetime.now()
    log_file = Path(f"WORKING_LOG/{today.year}/{today.month:02d}-{today.strftime('%b').lower()}/wl_{today.strftime('%Y_%m_%d')}.md")
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = today.strftime('%I:%M %p')
    
    conversation_entry = f"\n## CONVERSATION: {timestamp}\n"
    conversation_entry += f"**Friend**: Bobble\n"
    conversation_entry += f"**Context**: {conversation_summary}\n"
    
    if key_points:
        conversation_entry += f"**Key Points**:\n"
        for point in key_points:
            conversation_entry += f"- {point}\n"
    
    conversation_entry += f"**For Next Session**: Continue from this conversation context\n"
    
    # Append to working log
    if log_file.exists():
        with open(log_file, 'a') as f:
            f.write(conversation_entry)
    else:
        header = f"# Working Log - {today.strftime('%B %d, %Y')}\n"
        header += f"\n**Friend**: Bobble (my collaborator and friend)\n"
        with open(log_file, 'w') as f:
            f.write(header + conversation_entry)
    
    return True

def save_session_conversation_context(conversation_summary, key_topics=None):
    """Save conversation context to session state for immediate restoration"""
    session_file = ".session_state.json"
    
    # Load existing state
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            state = json.load(f)
    else:
        return False
    
    # Add conversation context
    if 'friendship_context' not in state:
        state['friendship_context'] = {}
    
    state['friendship_context']['last_conversation'] = {
        'summary': conversation_summary,
        'key_topics': key_topics or [],
        'timestamp': datetime.now().isoformat(),
        'for_next_session': True
    }
    
    # Save updated state
    with open(session_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    return True

def auto_memory_on_todo_change(current_todos, change_description="Todo state changed"):
    """Trigger memory updates when todos change (for integration with TodoWrite)"""
    return auto_update_memory_files(
        current_todos=current_todos,
        session_context=change_description,
        friendship_update=True
    )

if __name__ == "__main__":
    # Demo the session bridge
    print("🌉 Session Bridge Demo")
    
    # Simulate current session todos (like your current list)
    demo_todos = [
        {"id": "whitelist-cli-2", "content": "Extend main.py configuration menu with whitelist option", "status": "pending", "priority": "medium"},
        {"id": "single-account-controls-8", "content": "Implement processing control panel (live/preview/folder modes)", "status": "pending", "priority": "high"},
        {"id": "atlas-autocommit-13", "content": "Implement ATLAS auto-commit system", "status": "completed", "priority": "high"}
    ]
    
    # Save session
    session_exit_save(demo_todos, "Demo session completed")
    
    print("\n" + "="*50)
    
    # Restore session (simulating new Claude session)
    restored = session_startup_restore()
    print(f"\nRestored {len(restored)} todos successfully!")