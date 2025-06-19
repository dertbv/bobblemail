#!/usr/bin/env python3
"""
Session Bridge - Integration between TodoWrite and Session Memory
Automatically saves/restores TodoWrite lists across Claude sessions
"""

from session_memory import save_current_session, restore_previous_session, get_restored_todolist
from datetime import datetime

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