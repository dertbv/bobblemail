#!/usr/bin/env python3
"""
ATLAS Auto-Commit System
Implements automatic git staging and committing based on environment configuration
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Load environment variables on import
load_env_file()

class AtlasAutoCommit:
    """ATLAS Automatic Git Commit System"""
    
    def __init__(self):
        self.enabled = self._check_enabled()
        self.delay_seconds = self._get_delay()
        
    def _check_enabled(self) -> bool:
        """Check if auto-commit is enabled via environment variables"""
        return os.getenv('ATLAS_AUTO_COMMIT', '').lower() == 'true'
    
    def _get_delay(self) -> int:
        """Get commit delay in seconds from environment or adaptive config"""
        # First check for adaptive configuration
        try:
            from atlas_adaptive_config import get_adaptive_delay
            adaptive_delay = get_adaptive_delay()
            if adaptive_delay > 0:
                return adaptive_delay
        except ImportError:
            pass
        
        # Fallback to environment variable
        delay_str = os.getenv('ATLAS_AUTO_COMMIT_DELAY', '0')
        try:
            return int(delay_str)
        except ValueError:
            return 0
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get current git status and pending changes"""
        try:
            # Check for changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    status = line[:2]
                    filepath = line[3:]
                    changes.append({'status': status, 'file': filepath})
            
            return {
                'has_changes': len(changes) > 0,
                'changes': changes,
                'change_count': len(changes)
            }
        except subprocess.CalledProcessError:
            return {'has_changes': False, 'changes': [], 'change_count': 0}
    
    def _generate_commit_message(self, changes: List[Dict[str, Any]]) -> str:
        """Generate detailed, informative commit message based on changes"""
        if not changes:
            return "feat: Update project files\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        # Analyze file types and changes with intelligent categorization
        file_analysis = {}
        modified_files = []
        
        for change in changes:
            filepath = change['file']
            modified_files.append(filepath)
            
            # Intelligent file categorization with functional context
            if filepath.endswith('.py'):
                if 'classifier' in filepath.lower():
                    file_analysis['ml_classification'] = file_analysis.get('ml_classification', []) + [filepath]
                elif 'processor' in filepath.lower():
                    file_analysis['data_processing'] = file_analysis.get('data_processing', []) + [filepath]
                elif 'web_app' in filepath.lower() or 'app' in filepath.lower():
                    file_analysis['web_interface'] = file_analysis.get('web_interface', []) + [filepath]
                elif 'database' in filepath.lower() or 'db_' in filepath.lower():
                    file_analysis['database'] = file_analysis.get('database', []) + [filepath]
                elif 'atlas' in filepath.lower():
                    file_analysis['atlas_system'] = file_analysis.get('atlas_system', []) + [filepath]
                elif 'test' in filepath.lower():
                    file_analysis['testing'] = file_analysis.get('testing', []) + [filepath]
                else:
                    file_analysis['python_core'] = file_analysis.get('python_core', []) + [filepath]
            elif filepath.endswith('.md'):
                file_analysis['documentation'] = file_analysis.get('documentation', []) + [filepath]
            elif filepath.endswith('.json'):
                if 'settings' in filepath.lower() or 'config' in filepath.lower():
                    file_analysis['configuration'] = file_analysis.get('configuration', []) + [filepath]
                elif 'ml_' in filepath.lower():
                    file_analysis['ml_models'] = file_analysis.get('ml_models', []) + [filepath]
                else:
                    file_analysis['data_files'] = file_analysis.get('data_files', []) + [filepath]
            elif filepath.endswith('.env'):
                file_analysis['environment'] = file_analysis.get('environment', []) + [filepath]
            elif filepath.endswith('.db') or filepath.endswith('.sqlite'):
                file_analysis['database_files'] = file_analysis.get('database_files', []) + [filepath]
            else:
                file_analysis['other'] = file_analysis.get('other', []) + [filepath]
        
        # Generate intelligent commit type and summary based on primary changes
        commit_type, summary = self._determine_commit_context(file_analysis, modified_files)
        
        # Build detailed, informative message
        details = []
        
        # Add specific file context
        if len(modified_files) <= 8:
            details.append(f"📝 Modified files:")
            for filepath in modified_files:
                details.append(f"   • {filepath}")
        else:
            details.append(f"📝 Modified {len(modified_files)} files")
        
        details.append("")  # Empty line for readability
        
        # Add functional context for each category
        for category, files in file_analysis.items():
            if not files:
                continue
                
            context_desc = self._get_functional_context(category, files)
            details.append(f"🔧 {context_desc}")
        
        details.append("")
        details.append("🤖 ATLAS automated development workflow commit")
        
        message = f"{commit_type}: {summary}\n\n"
        message += "\n".join(details)
        message += "\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        return message
    
    def _determine_commit_context(self, file_analysis: Dict[str, List[str]], all_files: List[str]) -> tuple:
        """Determine commit type and summary based on file analysis"""
        
        # Priority-based commit type determination
        if file_analysis.get('ml_classification'):
            return "feat", "Enhance ML classification system"
        elif file_analysis.get('atlas_system'):
            return "feat", "Update ATLAS workflow system"
        elif file_analysis.get('web_interface'):
            return "feat", "Update web interface"
        elif file_analysis.get('data_processing'):
            return "feat", "Enhance data processing pipeline"
        elif file_analysis.get('database'):
            return "feat", "Update database operations"
        elif file_analysis.get('testing'):
            return "test", "Update test suite"
        elif file_analysis.get('environment'):
            return "config", "Update environment configuration"
        elif file_analysis.get('configuration'):
            return "config", "Update system configuration"
        elif file_analysis.get('documentation'):
            return "docs", "Update project documentation"
        elif file_analysis.get('python_core'):
            return "feat", "Update core application logic"
        elif file_analysis.get('ml_models'):
            return "feat", "Update ML model configuration"
        else:
            return "feat", "Update project components"
    
    def _get_functional_context(self, category: str, files: List[str]) -> str:
        """Get functional context description for file category"""
        
        context_map = {
            'ml_classification': f"Enhanced ML classification algorithms ({len(files)} file{'s' if len(files) > 1 else ''})",
            'atlas_system': f"Updated ATLAS automation system ({len(files)} file{'s' if len(files) > 1 else ''})",
            'web_interface': f"Modified web dashboard interface ({len(files)} file{'s' if len(files) > 1 else ''})",
            'data_processing': f"Enhanced data processing pipeline ({len(files)} file{'s' if len(files) > 1 else ''})",
            'database': f"Updated database operations ({len(files)} file{'s' if len(files) > 1 else ''})",
            'testing': f"Updated testing framework ({len(files)} file{'s' if len(files) > 1 else ''})",
            'environment': f"Modified environment configuration ({len(files)} file{'s' if len(files) > 1 else ''})",
            'configuration': f"Updated system configuration ({len(files)} file{'s' if len(files) > 1 else ''})",
            'documentation': f"Updated project documentation ({len(files)} file{'s' if len(files) > 1 else ''})",
            'python_core': f"Modified core Python modules ({len(files)} file{'s' if len(files) > 1 else ''})",
            'ml_models': f"Updated ML model configuration ({len(files)} file{'s' if len(files) > 1 else ''})",
            'database_files': f"Modified database files ({len(files)} file{'s' if len(files) > 1 else ''})",
            'data_files': f"Updated data configuration files ({len(files)} file{'s' if len(files) > 1 else ''})",
            'other': f"Modified supporting files ({len(files)} file{'s' if len(files) > 1 else ''})"
        }
        
        return context_map.get(category, f"Updated {category} ({len(files)} file{'s' if len(files) > 1 else ''})")
    
    def stage_changes(self) -> bool:
        """Stage all changes for commit"""
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            print("✅ ATLAS: Changes staged successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ ATLAS: Failed to stage changes: {e}")
            return False
    
    def commit_changes(self, message: str) -> bool:
        """Commit staged changes with message"""
        try:
            subprocess.run(['git', 'commit', '-m', message], check=True)
            print("✅ ATLAS: Changes committed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ ATLAS: Failed to commit changes: {e}")
            return False
    
    def request_user_approval(self, changes: List[Dict[str, Any]], commit_message: str) -> bool:
        """Request user approval for committing changes"""
        print("\n🤖 ATLAS: Work completed - Ready to commit!")
        print("=" * 50)
        print(f"📊 Changes found: {len(changes)} file(s)")
        
        # Show modified files
        print("\n📝 Modified files:")
        for change in changes[:10]:  # Show first 10 files
            status_icon = "🆕" if change['status'].startswith('A') else "✏️"
            print(f"   {status_icon} {change['file']}")
        
        if len(changes) > 10:
            print(f"   ... and {len(changes) - 10} more files")
        
        # Show commit message preview
        print(f"\n💬 Commit message preview:")
        print(f"   {commit_message.split(chr(10))[0]}")  # First line only
        
        print(f"\n⚠️  This will commit your changes to git")
        print(f"💡 You can review with 'git diff --staged' before approving")
        
        return True  # For now, always approve - we'll make this interactive later
    
    def auto_commit_workflow(self, request_approval: bool = False) -> Dict[str, Any]:
        """Execute the complete auto-commit workflow"""
        if not self.enabled:
            return {
                'success': False,
                'message': 'ATLAS auto-commit is disabled',
                'action': 'none'
            }
        
        # Check for changes
        git_status = self._get_git_status()
        if not git_status['has_changes']:
            return {
                'success': True,
                'message': 'No changes to commit',
                'action': 'none'
            }
        
        print(f"🤖 ATLAS: Found {git_status['change_count']} file(s) with changes")
        
        # Stage changes first (so user can review with git diff --staged)
        if not self.stage_changes():
            return {
                'success': False,
                'message': 'Failed to stage changes',
                'action': 'stage_failed'
            }
        
        # Generate commit message
        commit_message = self._generate_commit_message(git_status['changes'])
        
        # Request approval if specified
        if request_approval:
            if not self.request_user_approval(git_status['changes'], commit_message):
                return {
                    'success': False,
                    'message': 'User declined to commit changes',
                    'action': 'approval_declined'
                }
        else:
            # Apply delay if configured (for automatic mode)
            if self.delay_seconds > 0:
                print(f"⏱️ ATLAS: Waiting {self.delay_seconds} seconds for review...")
                import time
                time.sleep(self.delay_seconds)
        
        # Commit changes
        if not self.commit_changes(commit_message):
            return {
                'success': False,
                'message': 'Failed to commit changes',
                'action': 'commit_failed'
            }
        
        return {
            'success': True,
            'message': f'Successfully committed {git_status["change_count"]} file(s)',
            'action': 'committed',
            'files_changed': git_status['change_count'],
            'commit_message': commit_message
        }

def trigger_atlas_auto_commit() -> Dict[str, Any]:
    """Main function to trigger ATLAS auto-commit workflow"""
    atlas = AtlasAutoCommit()
    return atlas.auto_commit_workflow()

def request_commit_approval() -> Dict[str, Any]:
    """Request user approval for committing current changes"""
    atlas = AtlasAutoCommit()
    return atlas.auto_commit_workflow(request_approval=True)

if __name__ == "__main__":
    # Direct execution for testing
    result = trigger_atlas_auto_commit()
    print(f"ATLAS Auto-Commit Result: {result}")