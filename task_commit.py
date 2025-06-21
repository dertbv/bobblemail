#!/usr/bin/env python3
"""
Task-Based Auto Git Commit & Push
Commits when tasks are completed with meaningful messages
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class TaskCommit:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path).resolve()
        self.task_file = self.repo_path / ".task_status.json"
        self.load_tasks()
    
    def load_tasks(self):
        """Load task status from file"""
        if self.task_file.exists():
            with open(self.task_file, 'r') as f:
                self.tasks = json.load(f)
        else:
            self.tasks = {"completed": [], "in_progress": []}
    
    def save_tasks(self):
        """Save task status to file"""
        with open(self.task_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)
    
    def run_git_command(self, command):
        """Execute a git command and return output"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            return None
    
    def has_changes(self):
        """Check if there are any changes to commit"""
        status = self.run_git_command(["git", "status", "--porcelain"])
        return bool(status)
    
    def get_changed_files(self):
        """Get list of changed files"""
        status = self.run_git_command(["git", "status", "--porcelain"])
        if not status:
            return []
        
        files = []
        for line in status.split('\n'):
            if line.strip():
                # Extract filename from git status output
                parts = line.strip().split(maxsplit=1)
                if len(parts) > 1:
                    files.append(parts[1])
        return files
    
    def generate_commit_message(self, task_name: str, task_type: str, files_changed: List[str]) -> str:
        """Generate a meaningful commit message based on task and changes"""
        # Analyze file types and changes
        file_categories = {
            'docs': [],
            'tests': [],
            'config': [],
            'feature': [],
            'fix': [],
            'refactor': []
        }
        
        for file in files_changed:
            file_lower = file.lower()
            if any(x in file_lower for x in ['readme', '.md', 'doc']):
                file_categories['docs'].append(file)
            elif any(x in file_lower for x in ['test', 'spec']):
                file_categories['tests'].append(file)
            elif any(x in file_lower for x in ['.json', '.yml', '.yaml', '.config', '.env']):
                file_categories['config'].append(file)
            elif task_type == 'fix' or 'fix' in task_name.lower():
                file_categories['fix'].append(file)
            elif task_type == 'refactor' or 'refactor' in task_name.lower():
                file_categories['refactor'].append(file)
            else:
                file_categories['feature'].append(file)
        
        # Determine primary change type
        change_counts = {k: len(v) for k, v in file_categories.items() if v}
        if not change_counts:
            primary_type = 'chore'
        else:
            primary_type = max(change_counts.keys(), key=lambda k: change_counts[k])
        
        # Create commit message
        prefix_map = {
            'feature': 'feat',
            'fix': 'fix',
            'docs': 'docs',
            'tests': 'test',
            'config': 'chore',
            'refactor': 'refactor'
        }
        
        prefix = prefix_map.get(primary_type, 'chore')
        
        # Build detailed message
        message_lines = [f"{prefix}: {task_name}"]
        
        if len(files_changed) > 3:
            message_lines.append("")
            message_lines.append(f"- Modified {len(files_changed)} files")
            for category, files in file_categories.items():
                if files:
                    message_lines.append(f"- {category.capitalize()}: {len(files)} files")
        else:
            message_lines.append("")
            for file in files_changed:
                message_lines.append(f"- {file}")
        
        # Add task completion note
        message_lines.append("")
        message_lines.append(f"Task completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(message_lines)
    
    def commit_and_push(self, task_name: str, task_type: str = "feature"):
        """Commit with task-based message and push"""
        if not self.has_changes():
            print("No changes to commit")
            return False
        
        # Get changed files before staging
        changed_files = self.get_changed_files()
        
        # Add all changes
        print("Staging changes...")
        self.run_git_command(["git", "add", "."])
        
        # Generate commit message
        commit_message = self.generate_commit_message(task_name, task_type, changed_files)
        
        # Commit
        print(f"\nCommitting with message:")
        print("-" * 40)
        print(commit_message)
        print("-" * 40)
        
        # Use heredoc style for multi-line commit message
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Commit failed: {result.stderr}")
            return False
        
        # Push to remote
        print("\nPushing to remote...")
        push_result = self.run_git_command(["git", "push"])
        
        if push_result is not None:
            print(f"✅ Successfully committed and pushed: {task_name}")
            
            # Record completed task
            self.tasks["completed"].append({
                "name": task_name,
                "type": task_type,
                "completed_at": datetime.now().isoformat(),
                "files_changed": len(changed_files)
            })
            self.save_tasks()
            return True
        else:
            print("⚠️  Push failed - changes committed locally")
            return False
    
    def start_task(self, task_name: str):
        """Mark a task as in progress"""
        self.tasks["in_progress"].append({
            "name": task_name,
            "started_at": datetime.now().isoformat()
        })
        self.save_tasks()
        print(f"📋 Task started: {task_name}")
    
    def complete_task(self, task_name: str = None, task_type: str = "feature"):
        """Complete a task and commit changes"""
        if not task_name and self.tasks["in_progress"]:
            # Use the most recent in-progress task
            task = self.tasks["in_progress"][-1]
            task_name = task["name"]
            self.tasks["in_progress"].remove(task)
        elif not task_name:
            task_name = input("Enter task name: ")
        
        print(f"\n🎯 Completing task: {task_name}")
        self.commit_and_push(task_name, task_type)
    
    def list_tasks(self):
        """List current and completed tasks"""
        print("\n📋 In Progress Tasks:")
        if self.tasks["in_progress"]:
            for task in self.tasks["in_progress"]:
                print(f"  - {task['name']} (started: {task['started_at']})")
        else:
            print("  None")
        
        print("\n✅ Recently Completed Tasks:")
        for task in self.tasks["completed"][-5:]:
            print(f"  - {task['name']} ({task['type']}) - {task['completed_at']}")

# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Task-based git commit and push")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start task command
    start_parser = subparsers.add_parser('start', help='Start a new task')
    start_parser.add_argument('name', help='Task name')
    
    # Complete task command
    complete_parser = subparsers.add_parser('complete', help='Complete task and commit')
    complete_parser.add_argument('name', nargs='?', help='Task name (optional)')
    complete_parser.add_argument('--type', '-t', default='feature',
                                choices=['feature', 'fix', 'docs', 'test', 'refactor', 'chore'],
                                help='Type of task')
    
    # Quick commit command
    commit_parser = subparsers.add_parser('commit', help='Quick commit with task name')
    commit_parser.add_argument('name', help='Task/change description')
    commit_parser.add_argument('--type', '-t', default='feature',
                              choices=['feature', 'fix', 'docs', 'test', 'refactor', 'chore'],
                              help='Type of change')
    
    # List tasks command
    list_parser = subparsers.add_parser('list', help='List tasks')
    
    args = parser.parse_args()
    
    # Check if we're in a git repository
    if not os.path.exists(".git"):
        print("Error: Not in a git repository")
        return
    
    task_commit = TaskCommit()
    
    if args.command == 'start':
        task_commit.start_task(args.name)
    elif args.command == 'complete':
        task_commit.complete_task(args.name, args.type)
    elif args.command == 'commit':
        task_commit.commit_and_push(args.name, args.type)
    elif args.command == 'list':
        task_commit.list_tasks()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()