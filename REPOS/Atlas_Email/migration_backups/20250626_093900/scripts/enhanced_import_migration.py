#!/usr/bin/env python3
"""
Enhanced Import Migration System for Atlas_Email
Fixes issues found in initial dry run
"""

import os
import re
import shutil
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import json
from datetime import datetime


class EnhancedImportMigrator:
    """Enhanced migration that handles complex import patterns"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src" / "atlas_email"
        self.backup_dir = project_root / "migration_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []
        
        # Enhanced import mappings
        self.import_patterns = self._create_enhanced_patterns()
        
    def _create_enhanced_patterns(self) -> List[Tuple[str, str]]:
        """Create comprehensive regex patterns for import replacement"""
        patterns = []
        
        # Define module mappings
        mappings = {
            # Core modules
            'email_processor': 'atlas_email.core.email_processor',
            'processing_controller': 'atlas_email.core.processing_controller',
            'spam_classifier': 'atlas_email.core.spam_classifier',
            'logical_classifier': 'atlas_email.core.logical_classifier',
            'classification_utils': 'atlas_email.core.classification_utils',
            'email_authentication': 'atlas_email.core.email_authentication',
            'two_factor_email_validator': 'atlas_email.core.two_factor_validator',
            
            # ML modules
            'ensemble_hybrid_classifier': 'atlas_email.ml.ensemble_classifier',
            'ml_classifier': 'atlas_email.ml.naive_bayes',
            'random_forest_classifier': 'atlas_email.ml.random_forest',
            'ml_feature_extractor': 'atlas_email.ml.feature_extractor',
            'ml_category_classifier': 'atlas_email.ml.category_classifier',
            'ml_settings': 'atlas_email.ml.settings',
            'binary_feedback_processor': 'atlas_email.ml.feedback_processor',
            'learning_analytics': 'atlas_email.ml.analytics',
            
            # API modules
            'web_app': 'atlas_email.api.app',
            'web_app_manager': 'atlas_email.api.app_manager',
            'email_action_viewer': 'atlas_email.api.email_action_viewer',
            
            # CLI modules
            'main': 'atlas_email.cli.main',
            'menu_handler': 'atlas_email.cli.menu_handler',
            
            # Models
            'database': 'atlas_email.models.database',
            'db_logger': 'atlas_email.models.db_logger',
            'db_analytics': 'atlas_email.models.analytics',
            'db_keyword_inspector': 'atlas_email.models.keyword_inspector',
            'vendor_preferences_schema': 'atlas_email.models.vendor_preferences',
            
            # Filters
            'keyword_processor': 'atlas_email.filters.keyword_processor',
            'unified_keyword_manager': 'atlas_email.filters.unified_manager',
            'builtin_keywords_manager': 'atlas_email.filters.builtin_keywords',
            'category_keywords': 'atlas_email.filters.category_keywords',
            'selective_vendor_filter': 'atlas_email.filters.vendor_filter',
            'vendor_filter_integration': 'atlas_email.filters.vendor_integration',
            'legitimate_business_prefixes': 'atlas_email.filters.business_prefixes',
            
            # Utils
            'utils': 'atlas_email.utils.general',
            'domain_validator': 'atlas_email.utils.domain_validator',
            'domain_cache': 'atlas_email.utils.domain_cache',
            'provider_utils': 'atlas_email.utils.provider_utils',
            'regex_optimizer': 'atlas_email.utils.regex_optimizer',
            'smart_regex_selector': 'atlas_email.utils.smart_regex',
            'auto_batch_timer': 'atlas_email.utils.batch_timer',
            'processing_controls': 'atlas_email.utils.processing_controls',
            
            # Config modules (stay in config/)
            'settings': 'config.settings',
            'constants': 'config.constants',
            'config_loader': 'config.loader',
            'config_auth': 'config.auth',
            'configuration_manager': 'config.manager',
            'db_credentials': 'config.credentials',
        }
        
        # Create patterns for different import styles
        for old_module, new_module in mappings.items():
            # Pattern 1: from module import ...
            patterns.append((
                rf'^(\s*from\s+){re.escape(old_module)}(\s+import\s+.*)$',
                rf'\1{new_module}\2'
            ))
            
            # Pattern 2: import module
            patterns.append((
                rf'^(\s*)import\s+{re.escape(old_module)}(\s*)$',
                rf'\1import {new_module}\2'
            ))
            
            # Pattern 3: import module as alias
            patterns.append((
                rf'^(\s*)import\s+{re.escape(old_module)}(\s+as\s+\w+)(\s*)$',
                rf'\1import {new_module}\2\3'
            ))
            
            # Pattern 4: Dynamic imports in functions/methods (special handling)
            patterns.append((
                rf'(\s*from\s+){re.escape(old_module)}(\s+import\s+)',
                rf'\1{new_module}\2'
            ))
        
        return patterns
    
    def migrate_file_enhanced(self, file_path: Path) -> dict:
        """Enhanced file migration with better pattern matching"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            new_content = original_content
            changes_made = []
            
            # Apply regex patterns line by line to preserve structure
            lines = new_content.split('\n')
            new_lines = []
            
            for line_no, line in enumerate(lines, 1):
                new_line = line
                line_changed = False
                
                # Apply each pattern
                for pattern, replacement in self.import_patterns:
                    if re.search(pattern, new_line, re.MULTILINE):
                        old_line = new_line
                        new_line = re.sub(pattern, replacement, new_line, flags=re.MULTILINE)
                        if old_line != new_line:
                            changes_made.append(f"Line {line_no}: {old_line.strip()} → {new_line.strip()}")
                            line_changed = True
                
                new_lines.append(new_line)
            
            new_content = '\n'.join(new_lines)
            
            # Validate syntax
            try:
                ast.parse(new_content)
                syntax_valid = True
                errors = []
            except SyntaxError as e:
                syntax_valid = False
                errors = [f"Syntax error: {e}"]
            
            return {
                'file_path': str(file_path),
                'original_content': original_content,
                'new_content': new_content,
                'changes_made': changes_made,
                'errors': errors,
                'success': syntax_valid and (len(changes_made) > 0 or original_content == new_content)
            }
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'original_content': '',
                'new_content': '',
                'changes_made': [],
                'errors': [f"Migration failed: {e}"],
                'success': False
            }
    
    def create_backup(self) -> bool:
        """Create complete backup"""
        try:
            print(f"🔒 Creating backup at {self.backup_dir}")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            for py_file in self.project_root.rglob("*.py"):
                if "migration_backups" not in str(py_file):
                    relative_path = py_file.relative_to(self.project_root)
                    backup_path = self.backup_dir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(py_file, backup_path)
            
            print(f"✅ Backup created")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def run_enhanced_migration(self, dry_run: bool = True) -> bool:
        """Run enhanced migration"""
        print("🚀 Enhanced Atlas_Email Import Migration")
        print(f"🔧 Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
        
        if not dry_run and not self.create_backup():
            return False
        
        # Find Python files
        python_files = []
        for py_file in self.src_root.rglob("*.py"):
            if py_file.name != "__init__.py":
                python_files.append(py_file)
        
        # Also check config files
        config_dir = self.project_root / "config"
        if config_dir.exists():
            for py_file in config_dir.rglob("*.py"):
                python_files.append(py_file)
        
        print(f"🔍 Processing {len(python_files)} files")
        
        # Process files
        successful = 0
        failed = 0
        
        for file_path in python_files:
            result = self.migrate_file_enhanced(file_path)
            self.results.append(result)
            
            if result['success']:
                if result['changes_made']:
                    print(f"✅ {file_path.name}: {len(result['changes_made'])} changes")
                    if not dry_run:
                        # Apply changes
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(result['new_content'])
                else:
                    print(f"✅ {file_path.name}: No changes needed")
                successful += 1
            else:
                print(f"❌ {file_path.name}: {result['errors']}")
                failed += 1
        
        print(f"\n🎯 Summary: {successful}/{len(python_files)} successful")
        
        if failed > 0:
            print(f"⚠️  {failed} files need manual attention")
            
            # Show specific issues
            for result in self.results:
                if not result['success'] and result['errors']:
                    print(f"  - {Path(result['file_path']).name}: {result['errors'][0]}")
        
        return failed == 0


def main():
    """Enhanced migration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Atlas_Email Import Migration")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--live", action="store_true", help="Perform live migration")
    
    args = parser.parse_args()
    
    migrator = EnhancedImportMigrator(args.project_root)
    success = migrator.run_enhanced_migration(dry_run=not args.live)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()