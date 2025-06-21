#!/usr/bin/env python3
"""
TODO-Based Auto Commit
Monitors TODO file/database and commits when tasks are marked complete
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class TodoCommit:
    def __init__(self, repo_path=".", todo_file="TODO.md"):
        self.repo_path = Path(repo_path).resolve()
        self.todo_file = self.repo_path / todo_file
        self.state_file = self.repo_path / ".todo_state.json"
        self.last_state = self.load_state()
        
    def load_state(self):
        """Load last known TODO state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"todos": [], "last_check": None}
    
    def save_state(self, todos):
        """Save current TODO state"""
        state = {
            "todos": todos,
            "last_check": datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        self.last_state = state
    
    def parse_markdown_todos(self):
        """Parse TODO.md file for tasks"""
        if not self.todo_file.exists():
            return []
        
        todos = []
        with open(self.todo_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Match different TODO formats
                if line.startswith('- [ ]'):  # Uncompleted
                    todos.append({
                        'task': line[6:].strip(),
                        'completed': False,
                        'raw': line
                    })
                elif line.startswith('- [x]') or line.startswith('- [X]'):  # Completed
                    todos.append({
                        'task': line[6:].strip(),
                        'completed': True,
                        'raw': line
                    })
                elif line.startswith('* [ ]'):  # Alternative format
                    todos.append({
                        'task': line[6:].strip(),
                        'completed': False,
                        'raw': line
                    })
                elif line.startswith('* [x]') or line.startswith('* [X]'):
                    todos.append({
                        'task': line[6:].strip(),
                        'completed': True,
                        'raw': line
                    })
        
        return todos
    
    def parse_json_todos(self):
        """Parse JSON TODO file"""
        if not self.todo_file.exists():
            return []
        
        with open(self.todo_file, 'r') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'todos' in data:
            return data['todos']
        else:
            return []
    
    def get_todos(self):
        """Get current TODO list based on file type"""
        if self.todo_file.suffix == '.md':
            return self.parse_markdown_todos()
        elif self.todo_file.suffix == '.json':
            return self.parse_json_todos()
        else:
            # Try to parse as text file with simple format
            todos = []
            if self.todo_file.exists():
                with open(self.todo_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # Simple format: "TODO: " or "DONE: " prefix
                            if line.startswith('DONE:'):
                                todos.append({
                                    'task': line[5:].strip(),
                                    'completed': True
                                })
                            elif line.startswith('TODO:'):
                                todos.append({
                                    'task': line[5:].strip(),
                                    'completed': False
                                })
            return todos
    
    def find_completed_tasks(self, current_todos):
        """Find newly completed tasks"""
        completed = []
        
        # Get previous todos
        prev_todos = {todo['task']: todo for todo in self.last_state.get('todos', [])}
        
        # Find tasks that were not completed before but are now
        for todo in current_todos:
            if todo['completed']:
                prev_todo = prev_todos.get(todo['task'])
                if not prev_todo or not prev_todo.get('completed', False):
                    completed.append(todo['task'])
        
        return completed
    
    def analyze_changes(self):
        """Analyze what changed in the repository"""
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if status.returncode != 0:
            return []
        
        changes = []
        for line in status.stdout.strip().split('\n'):
            if line:
                parts = line.strip().split(maxsplit=1)
                if len(parts) > 1:
                    changes.append(parts[1])
        
        return changes
    
    def generate_commit_message(self, completed_tasks, changed_files):
        """Generate meaningful commit message"""
        if len(completed_tasks) == 1:
            task = completed_tasks[0]
            # Analyze task for type
            task_lower = task.lower()
            if any(word in task_lower for word in ['fix', 'bug', 'issue']):
                prefix = 'fix'
            elif any(word in task_lower for word in ['add', 'implement', 'create']):
                prefix = 'feat'
            elif any(word in task_lower for word in ['update', 'improve']):
                prefix = 'enhance'
            elif any(word in task_lower for word in ['refactor', 'cleanup']):
                prefix = 'refactor'
            elif any(word in task_lower for word in ['test', 'spec']):
                prefix = 'test'
            elif any(word in task_lower for word in ['doc', 'readme']):
                prefix = 'docs'
            else:
                prefix = 'chore'
            
            message = f"{prefix}: {task}\n\n"
        else:
            message = f"feat: Complete {len(completed_tasks)} tasks\n\n"
            message += "Completed:\n"
            for task in completed_tasks:
                message += f"- {task}\n"
            message += "\n"
        
        # Add file change summary
        if len(changed_files) <= 5:
            message += "Modified files:\n"
            for file in changed_files:
                message += f"- {file}\n"
        else:
            message += f"Modified {len(changed_files)} files across the project\n"
        
        message += f"\nAuto-committed on task completion"
        return message
    
    def commit_and_push(self, completed_tasks):
        """Commit completed tasks and push"""
        # Get changed files
        changed_files = self.analyze_changes()
        
        if not changed_files:
            print("No changes to commit")
            return False
        
        # Stage all changes
        subprocess.run(["git", "add", "."], cwd=self.repo_path)
        
        # Generate commit message
        message = self.generate_commit_message(completed_tasks, changed_files)
        
        print(f"\n📝 Committing {len(completed_tasks)} completed task(s):")
        for task in completed_tasks:
            print(f"   ✓ {task}")
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Changes committed")
            
            # Push
            push_result = subprocess.run(
                ["git", "push"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if push_result.returncode == 0:
                print("✅ Pushed to remote")
                return True
            else:
                print("⚠️  Push failed - changes committed locally")
                return False
        else:
            print(f"❌ Commit failed: {result.stderr}")
            return False
    
    def check_and_commit(self):
        """Check for completed tasks and commit if found"""
        current_todos = self.get_todos()
        completed_tasks = self.find_completed_tasks(current_todos)
        
        if completed_tasks:
            print(f"\n🎯 Found {len(completed_tasks)} completed task(s)")
            success = self.commit_and_push(completed_tasks)
            if success:
                # Save new state after successful commit
                self.save_state(current_todos)
        
        return len(completed_tasks) > 0
    
    def watch(self, interval=10):
        """Watch TODO file for changes"""
        print(f"👀 Watching {self.todo_file.name} for completed tasks")
        print(f"Checking every {interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_and_commit()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n✋ TODO watcher stopped")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-commit on TODO completion")
    parser.add_argument('--path', '-p', default='.', help='Repository path')
    parser.add_argument('--file', '-f', default='TODO.md', help='TODO file name')
    parser.add_argument('--interval', '-i', type=int, default=10, 
                       help='Check interval in seconds')
    parser.add_argument('--once', '-o', action='store_true',
                       help='Check once and exit')
    
    args = parser.parse_args()
    
    # Verify git repository
    if not os.path.exists(os.path.join(args.path, '.git')):
        print(f"Error: {args.path} is not a git repository")
        return
    
    todo_commit = TodoCommit(args.path, args.file)
    
    if args.once:
        found = todo_commit.check_and_commit()
        if not found:
            print("No completed tasks found")
    else:
        todo_commit.watch(args.interval)

if __name__ == "__main__":
    main()