#!/usr/bin/env python3
"""
Session Memory Persistence Wrapper
Saves TodoWrite lists and session data across Claude shutdowns/reboots
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class SessionMemory:
    """Persistent storage for Claude session data"""
    
    def __init__(self, storage_file: str = ".session_state.json"):
        self.storage_file = storage_file
        
    def save_session_state(self, 
                          todolist: List[Dict] = None, 
                          session_notes: str = "",
                          current_focus: str = "",
                          completed_tasks: List[str] = None,
                          next_priorities: List[str] = None,
                          custom_data: Dict = None) -> bool:
        """Save complete session state to file"""
        try:
            state = {
                'session_info': {
                    'timestamp': datetime.now().isoformat(),
                    'session_date': datetime.now().strftime('%Y-%m-%d'),
                    'session_time': datetime.now().strftime('%H:%M:%S')
                },
                'todolist': todolist or [],
                'session_notes': session_notes,
                'current_focus': current_focus,
                'completed_tasks': completed_tasks or [],
                'next_priorities': next_priorities or [],
                'custom_data': custom_data or {}
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"✅ Session state saved to {self.storage_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save session state: {e}")
            return False
    
    def load_session_state(self) -> Optional[Dict]:
        """Load session state from file"""
        try:
            if not os.path.exists(self.storage_file):
                print(f"📝 No previous session state found ({self.storage_file})")
                return None
                
            with open(self.storage_file, 'r') as f:
                state = json.load(f)
            
            print(f"✅ Session state loaded from {self.storage_file}")
            return state
            
        except Exception as e:
            print(f"❌ Failed to load session state: {e}")
            return None
    
    def restore_todolist_format(self, raw_todolist: List[Dict]) -> List[Dict]:
        """Convert saved todolist back to TodoWrite format"""
        if not raw_todolist:
            return []
            
        formatted_todos = []
        for item in raw_todolist:
            # Ensure all required TodoWrite fields exist
            todo = {
                'id': item.get('id', f"restored-{len(formatted_todos)}"),
                'content': item.get('content', 'Restored task'),
                'status': item.get('status', 'pending'),
                'priority': item.get('priority', 'medium')
            }
            formatted_todos.append(todo)
            
        return formatted_todos
    
    def display_session_summary(self, state: Dict):
        """Display a summary of the loaded session"""
        if not state:
            print("No session data to display")
            return
            
        session_info = state.get('session_info', {})
        todolist = state.get('todolist', [])
        
        print("\n" + "="*50)
        print("📋 RESTORED SESSION SUMMARY")
        print("="*50)
        print(f"📅 Session Date: {session_info.get('session_date', 'Unknown')}")
        print(f"⏰ Session Time: {session_info.get('session_time', 'Unknown')}")
        print(f"🎯 Current Focus: {state.get('current_focus', 'Not specified')}")
        
        if todolist:
            completed = [t for t in todolist if t.get('status') == 'completed']
            pending = [t for t in todolist if t.get('status') != 'completed']
            
            print(f"\n📊 TODO SUMMARY:")
            print(f"   ✅ Completed: {len(completed)}")
            print(f"   📋 Pending: {len(pending)}")
            print(f"   📝 Total: {len(todolist)}")
            
            if pending:
                print(f"\n📋 PENDING TASKS:")
                for todo in pending[:5]:  # Show first 5 pending
                    priority = todo.get('priority', 'medium').upper()
                    content = todo.get('content', 'No description')
                    print(f"   • [{priority}] {content}")
                if len(pending) > 5:
                    print(f"   ... and {len(pending) - 5} more")
        
        completed_tasks = state.get('completed_tasks', [])
        if completed_tasks:
            print(f"\n🎉 RECENT COMPLETIONS:")
            for task in completed_tasks[-3:]:  # Show last 3
                print(f"   ✅ {task}")
        
        next_priorities = state.get('next_priorities', [])
        if next_priorities:
            print(f"\n🚀 NEXT PRIORITIES:")
            for priority in next_priorities:
                print(f"   🎯 {priority}")
        
        session_notes = state.get('session_notes', '')
        if session_notes:
            print(f"\n📝 SESSION NOTES:")
            print(f"   {session_notes}")
        
        print("="*50)

# Global session memory instance
session_memory = SessionMemory()

def save_current_session(todolist: List[Dict], 
                        notes: str = "",
                        focus: str = "",
                        completed: List[str] = None,
                        next_items: List[str] = None) -> bool:
    """Convenience function to save current session"""
    return session_memory.save_session_state(
        todolist=todolist,
        session_notes=notes,
        current_focus=focus,
        completed_tasks=completed or [],
        next_priorities=next_items or []
    )

def restore_previous_session() -> Optional[Dict]:
    """Convenience function to restore previous session"""
    state = session_memory.load_session_state()
    if state:
        session_memory.display_session_summary(state)
    return state

def get_restored_todolist() -> List[Dict]:
    """Get todolist in TodoWrite format from saved session"""
    state = session_memory.load_session_state()
    if state and state.get('todolist'):
        return session_memory.restore_todolist_format(state['todolist'])
    return []

if __name__ == "__main__":
    # Test the session memory system
    print("🧠 Session Memory Test")
    
    # Test save
    test_todos = [
        {"id": "test-1", "content": "Test task 1", "status": "completed", "priority": "high"},
        {"id": "test-2", "content": "Test task 2", "status": "pending", "priority": "medium"}
    ]
    
    save_current_session(
        todolist=test_todos,
        notes="Test session notes",
        focus="Testing session memory system",
        completed=["Implemented session memory"],
        next_items=["Test restoration", "Integrate with ATLAS"]
    )
    
    # Test restore
    restored = restore_previous_session()
    print(f"\nRestored todos: {get_restored_todolist()}")