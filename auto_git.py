#!/usr/bin/env python3
"""
Auto Git Commit & Push Script
Automatically commits and pushes changes at regular intervals
"""

import subprocess
import time
import os
import sys
from datetime import datetime
from pathlib import Path

class AutoGit:
    def __init__(self, repo_path=".", interval_minutes=30):
        self.repo_path = Path(repo_path).resolve()
        self.interval_seconds = interval_minutes * 60
        
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
    
    def commit_and_push(self):
        """Commit all changes and push to remote"""
        if not self.has_changes():
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No changes to commit")
            return False
        
        # Add all changes
        print("Adding changes...")
        self.run_git_command(["git", "add", "."])
        
        # Create commit message with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Auto-commit: {timestamp}"
        
        # Commit
        print(f"Committing: {commit_message}")
        self.run_git_command(["git", "commit", "-m", commit_message])
        
        # Push to remote
        print("Pushing to remote...")
        result = self.run_git_command(["git", "push"])
        
        if result is not None:
            print(f"[{timestamp}] Successfully committed and pushed changes")
            return True
        else:
            print(f"[{timestamp}] Push failed - changes committed locally")
            return False
    
    def run_once(self):
        """Run a single commit/push cycle"""
        print(f"\n{'='*50}")
        print(f"Checking repository: {self.repo_path}")
        self.commit_and_push()
    
    def run_forever(self):
        """Run continuously at specified interval"""
        print(f"Auto-commit started for: {self.repo_path}")
        print(f"Interval: {self.interval_seconds/60} minutes")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                print(f"\nNext check in {self.interval_seconds/60} minutes...")
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            print("\n\nAuto-commit stopped by user")
            sys.exit(0)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-commit and push Git changes")
    parser.add_argument("--path", "-p", default=".", 
                       help="Path to git repository (default: current directory)")
    parser.add_argument("--interval", "-i", type=int, default=30,
                       help="Interval in minutes between commits (default: 30)")
    parser.add_argument("--once", "-o", action="store_true",
                       help="Run once and exit instead of continuous loop")
    
    args = parser.parse_args()
    
    # Verify it's a git repository
    if not os.path.exists(os.path.join(args.path, ".git")):
        print(f"Error: {args.path} is not a git repository")
        sys.exit(1)
    
    auto_git = AutoGit(args.path, args.interval)
    
    if args.once:
        auto_git.run_once()
    else:
        auto_git.run_forever()

if __name__ == "__main__":
    main()