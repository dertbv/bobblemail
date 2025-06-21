#!/usr/bin/env python3
"""
Task Completion Watcher
Monitors files for task completion markers and auto-commits
"""

import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

class TaskCompletionHandler(FileSystemEventHandler):
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path).resolve()
        self.task_patterns = [
            r'#\s*DONE:\s*(.+)',           # # DONE: Task description
            r'//\s*DONE:\s*(.+)',          # // DONE: Task description
            r'#\s*COMPLETED:\s*(.+)',      # # COMPLETED: Task description
            r'//\s*COMPLETED:\s*(.+)',     # // COMPLETED: Task description
            r'<!--\s*DONE:\s*(.+)\s*-->',  # <!-- DONE: Task description -->
            r'/\*\s*DONE:\s*(.+)\s*\*/',   # /* DONE: Task description */
        ]
        self.processed_markers = set()
        self.load_processed_markers()
    
    def load_processed_markers(self):
        """Load already processed markers to avoid duplicates"""
        marker_file = self.repo_path / ".processed_tasks.json"
        if marker_file.exists():
            with open(marker_file, 'r') as f:
                data = json.load(f)
                self.processed_markers = set(data.get('processed', []))
    
    def save_processed_markers(self):
        """Save processed markers"""
        marker_file = self.repo_path / ".processed_tasks.json"
        with open(marker_file, 'w') as f:
            json.dump({'processed': list(self.processed_markers)}, f)
    
    def extract_task_info(self, file_path):
        """Extract task completion markers from file"""
        tasks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in self.task_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    task_id = f"{file_path}:{match}"
                    if task_id not in self.processed_markers:
                        tasks.append({
                            'description': match.strip(),
                            'file': str(file_path),
                            'id': task_id
                        })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return tasks
    
    def determine_task_type(self, task_description, file_path):
        """Determine task type from description and file"""
        desc_lower = task_description.lower()
        file_str = str(file_path).lower()
        
        if any(word in desc_lower for word in ['fix', 'bug', 'issue', 'error']):
            return 'fix'
        elif any(word in desc_lower for word in ['test', 'spec']):
            return 'test'
        elif any(word in desc_lower for word in ['doc', 'readme', 'comment']):
            return 'docs'
        elif any(word in desc_lower for word in ['refactor', 'cleanup', 'optimize']):
            return 'refactor'
        elif any(ext in file_str for ext in ['.config', '.json', '.yml', '.env']):
            return 'chore'
        else:
            return 'feat'
    
    def run_git_command(self, command):
        """Execute git command"""
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
            return None
    
    def commit_task(self, task):
        """Commit completed task"""
        # Check for changes
        status = self.run_git_command(["git", "status", "--porcelain"])
        if not status:
            print("No changes to commit")
            return False
        
        # Stage changes
        self.run_git_command(["git", "add", "."])
        
        # Determine task type
        task_type = self.determine_task_type(task['description'], task['file'])
        
        # Create commit message
        commit_message = f"{task_type}: {task['description']}\n\n"
        commit_message += f"- Completed in: {Path(task['file']).name}\n"
        commit_message += f"- Auto-committed on task completion\n"
        commit_message += f"- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Commit
        print(f"\n📝 Committing: {task_type}: {task['description']}")
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Push
            push_result = self.run_git_command(["git", "push"])
            if push_result is not None:
                print("✅ Successfully committed and pushed")
                
                # Mark as processed
                self.processed_markers.add(task['id'])
                self.save_processed_markers()
                return True
            else:
                print("⚠️  Committed locally (push failed)")
                return False
        else:
            print(f"❌ Commit failed: {result.stderr}")
            return False
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        # Skip git files and temp files
        file_path = Path(event.src_path)
        if '.git' in str(file_path) or file_path.suffix in ['.tmp', '.swp']:
            return
        
        # Check for task completion markers
        tasks = self.extract_task_info(file_path)
        
        for task in tasks:
            print(f"\n🎯 Task completed detected: {task['description']}")
            time.sleep(2)  # Small delay to ensure all changes are saved
            self.commit_task(task)

class TaskWatcher:
    def __init__(self, repo_path=".", watch_patterns=None):
        self.repo_path = Path(repo_path).resolve()
        self.watch_patterns = watch_patterns or ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.md']
        
    def run(self):
        """Start watching for task completions"""
        event_handler = TaskCompletionHandler(self.repo_path)
        observer = Observer()
        observer.schedule(event_handler, str(self.repo_path), recursive=True)
        
        print(f"👀 Watching for task completions in: {self.repo_path}")
        print("Mark tasks as done using:")
        print("  - # DONE: Task description")
        print("  - // DONE: Task description")
        print("  - # COMPLETED: Task description")
        print("\nPress Ctrl+C to stop\n")
        
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n\n✋ Task watcher stopped")
        observer.join()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Watch for task completions and auto-commit")
    parser.add_argument('--path', '-p', default='.', help='Repository path to watch')
    parser.add_argument('--patterns', '-w', nargs='+', help='File patterns to watch')
    
    args = parser.parse_args()
    
    # Verify git repository
    if not os.path.exists(os.path.join(args.path, '.git')):
        print(f"Error: {args.path} is not a git repository")
        return
    
    watcher = TaskWatcher(args.path, args.patterns)
    watcher.run()

if __name__ == "__main__":
    main()