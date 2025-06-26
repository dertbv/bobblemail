#!/usr/bin/env python3
"""
Safe Import Migration System for Atlas_Email
Combines Backend/Fullstack expertise with DevSecOps/SRE safety practices
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


@dataclass
class ImportMapping:
    """Maps old import to new import path"""
    old_pattern: str
    new_path: str
    import_type: str  # 'from', 'import', 'relative'


@dataclass
class MigrationResult:
    """Results of migration operation"""
    file_path: str
    original_content: str
    new_content: str
    changes_made: List[str]
    errors: List[str]
    success: bool


class SafeImportMigrator:
    """
    Backend/Fullstack Developer: Handles Python import logic and dependencies
    DevSecOps/SRE: Provides safety, validation, and rollback capabilities
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src" / "atlas_email"
        self.backup_dir = project_root / "migration_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: List[MigrationResult] = []
        
        # Backend expertise: Define import mappings
        self.import_mappings = self._create_import_mappings()
        
        # DevSecOps expertise: Safety tracking
        self.files_to_migrate = []
        self.validation_errors = []
        
    def _create_import_mappings(self) -> List[ImportMapping]:
        """Backend: Create comprehensive import mapping rules"""
        mappings = []
        
        # Core business logic mappings
        core_mappings = {
            'email_processor': 'atlas_email.core.email_processor',
            'processing_controller': 'atlas_email.core.processing_controller', 
            'spam_classifier': 'atlas_email.core.spam_classifier',
            'logical_classifier': 'atlas_email.core.logical_classifier',
            'classification_utils': 'atlas_email.core.classification_utils',
            'email_authentication': 'atlas_email.core.email_authentication',
            'two_factor_email_validator': 'atlas_email.core.two_factor_validator',
        }
        
        # ML component mappings
        ml_mappings = {
            'ensemble_hybrid_classifier': 'atlas_email.ml.ensemble_classifier',
            'ml_classifier': 'atlas_email.ml.naive_bayes',
            'random_forest_classifier': 'atlas_email.ml.random_forest',
            'ml_feature_extractor': 'atlas_email.ml.feature_extractor',
            'ml_category_classifier': 'atlas_email.ml.category_classifier',
            'ml_settings': 'atlas_email.ml.settings',
            'binary_feedback_processor': 'atlas_email.ml.feedback_processor',
            'learning_analytics': 'atlas_email.ml.analytics',
        }
        
        # API mappings
        api_mappings = {
            'web_app': 'atlas_email.api.app',
            'web_app_manager': 'atlas_email.api.app_manager',
            'email_action_viewer': 'atlas_email.api.email_action_viewer',
        }
        
        # CLI mappings
        cli_mappings = {
            'main': 'atlas_email.cli.main',
            'menu_handler': 'atlas_email.cli.menu_handler',
        }
        
        # Models mappings
        models_mappings = {
            'database': 'atlas_email.models.database',
            'db_logger': 'atlas_email.models.db_logger',
            'db_analytics': 'atlas_email.models.analytics',
            'db_keyword_inspector': 'atlas_email.models.keyword_inspector',
            'vendor_preferences_schema': 'atlas_email.models.vendor_preferences',
        }
        
        # Filters mappings
        filters_mappings = {
            'keyword_processor': 'atlas_email.filters.keyword_processor',
            'unified_keyword_manager': 'atlas_email.filters.unified_manager',
            'builtin_keywords_manager': 'atlas_email.filters.builtin_keywords',
            'category_keywords': 'atlas_email.filters.category_keywords',
            'selective_vendor_filter': 'atlas_email.filters.vendor_filter',
            'vendor_filter_integration': 'atlas_email.filters.vendor_integration',
            'legitimate_business_prefixes': 'atlas_email.filters.business_prefixes',
        }
        
        # Utils mappings
        utils_mappings = {
            'utils': 'atlas_email.utils.general',
            'domain_validator': 'atlas_email.utils.domain_validator',
            'domain_cache': 'atlas_email.utils.domain_cache',
            'provider_utils': 'atlas_email.utils.provider_utils',
            'regex_optimizer': 'atlas_email.utils.regex_optimizer',
            'smart_regex_selector': 'atlas_email.utils.smart_regex',
            'auto_batch_timer': 'atlas_email.utils.batch_timer',
            'processing_controls': 'atlas_email.utils.processing_controls',
        }
        
        # Configuration mappings (special case - moved to config/)
        config_mappings = {
            'settings': 'config.settings',
            'constants': 'config.constants',
            'config_loader': 'config.loader',
            'config_auth': 'config.auth',
            'configuration_manager': 'config.manager',
            'db_credentials': 'config.credentials',
        }
        
        # Convert all mappings to ImportMapping objects
        all_mappings = {**core_mappings, **ml_mappings, **api_mappings, **cli_mappings, 
                       **models_mappings, **filters_mappings, **utils_mappings, **config_mappings}
        
        for old_name, new_path in all_mappings.items():
            # Handle 'from X import Y' patterns
            mappings.append(ImportMapping(
                old_pattern=f"from {old_name} import",
                new_path=f"from {new_path} import",
                import_type="from"
            ))
            
            # Handle 'import X' patterns  
            mappings.append(ImportMapping(
                old_pattern=f"import {old_name}",
                new_path=f"import {new_path}",
                import_type="import"
            ))
            
            # Handle 'from . import X' relative patterns
            mappings.append(ImportMapping(
                old_pattern=f"from . import {old_name}",
                new_path=f"from {new_path} import",
                import_type="relative"
            ))
        
        return mappings
    
    def create_backup(self) -> bool:
        """DevSecOps: Create complete backup before any changes"""
        try:
            print(f"🔒 Creating safety backup at {self.backup_dir}")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup all Python files
            for py_file in self.project_root.rglob("*.py"):
                if "migration_backups" not in str(py_file):  # Don't backup backups
                    relative_path = py_file.relative_to(self.project_root)
                    backup_path = self.backup_dir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(py_file, backup_path)
            
            print(f"✅ Backup created with {len(list(self.backup_dir.rglob('*.py')))} files")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def discover_python_files(self) -> List[Path]:
        """Backend: Find all Python files that need migration"""
        python_files = []
        
        # Find all .py files in src/ directory
        for py_file in self.src_root.rglob("*.py"):
            if py_file.name != "__init__.py":  # Handle __init__.py separately
                python_files.append(py_file)
        
        # Also check config files
        config_dir = self.project_root / "config"
        if config_dir.exists():
            for py_file in config_dir.rglob("*.py"):
                python_files.append(py_file)
        
        print(f"🔍 Discovered {len(python_files)} Python files for migration")
        return python_files
    
    def analyze_imports(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Backend: Analyze existing imports in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find imports
            tree = ast.parse(content)
            imports = []
            errors = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(f"from {node.module} import {', '.join(alias.name for alias in node.names)}")
                    else:
                        imports.append(f"from . import {', '.join(alias.name for alias in node.names)}")
            
            return imports, errors
            
        except Exception as e:
            return [], [f"Failed to analyze {file_path}: {e}"]
    
    def migrate_file_imports(self, file_path: Path) -> MigrationResult:
        """Backend + DevSecOps: Safely migrate imports in a single file"""
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            new_content = original_content
            changes_made = []
            errors = []
            
            # Apply each mapping
            for mapping in self.import_mappings:
                if mapping.old_pattern in new_content:
                    old_line_count = new_content.count(mapping.old_pattern)
                    new_content = new_content.replace(mapping.old_pattern, mapping.new_path)
                    changes_made.append(f"Updated {old_line_count} instances: {mapping.old_pattern} → {mapping.new_path}")
            
            # Validate syntax after changes
            try:
                ast.parse(new_content)
                syntax_valid = True
            except SyntaxError as e:
                syntax_valid = False
                errors.append(f"Syntax error after migration: {e}")
            
            return MigrationResult(
                file_path=str(file_path),
                original_content=original_content,
                new_content=new_content,
                changes_made=changes_made,
                errors=errors,
                success=syntax_valid and len(changes_made) > 0
            )
            
        except Exception as e:
            return MigrationResult(
                file_path=str(file_path),
                original_content="",
                new_content="",
                changes_made=[],
                errors=[f"File migration failed: {e}"],
                success=False
            )
    
    def validate_migration(self, result: MigrationResult) -> bool:
        """DevSecOps: Validate migration was successful"""
        if not result.success:
            return False
        
        # Check that we didn't break Python syntax
        try:
            ast.parse(result.new_content)
        except SyntaxError:
            return False
        
        # Check that we made actual changes
        if result.original_content == result.new_content:
            return True  # No changes needed is OK
        
        return len(result.errors) == 0
    
    def apply_migration(self, result: MigrationResult) -> bool:
        """DevSecOps: Safely apply migration with error handling"""
        if not self.validate_migration(result):
            print(f"❌ Validation failed for {result.file_path}")
            return False
        
        try:
            # Write new content to file
            with open(result.file_path, 'w', encoding='utf-8') as f:
                f.write(result.new_content)
            
            print(f"✅ Migrated {result.file_path} ({len(result.changes_made)} changes)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to write {result.file_path}: {e}")
            return False
    
    def rollback_migration(self) -> bool:
        """DevSecOps: Emergency rollback to backup"""
        try:
            print(f"🔄 Rolling back from backup {self.backup_dir}")
            
            # Restore all files from backup
            for backup_file in self.backup_dir.rglob("*.py"):
                relative_path = backup_file.relative_to(self.backup_dir)
                target_path = self.project_root / relative_path
                shutil.copy2(backup_file, target_path)
            
            print("✅ Rollback completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False
    
    def generate_migration_report(self) -> str:
        """DevSecOps: Generate comprehensive migration report"""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        report = f"""
# Atlas_Email Import Migration Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total files processed: {len(self.results)}
- Successful migrations: {len(successful)}
- Failed migrations: {len(failed)}
- Backup location: {self.backup_dir}

## Successful Migrations
"""
        for result in successful:
            report += f"\n### {result.file_path}\n"
            for change in result.changes_made:
                report += f"- {change}\n"
        
        if failed:
            report += "\n## Failed Migrations\n"
            for result in failed:
                report += f"\n### {result.file_path}\n"
                for error in result.errors:
                    report += f"- ❌ {error}\n"
        
        return report
    
    def run_migration(self, dry_run: bool = True) -> bool:
        """Main migration orchestration combining both expertise areas"""
        print("🚀 Starting Atlas_Email Import Migration")
        print(f"📁 Project root: {self.project_root}")
        print(f"🔧 Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
        
        # DevSecOps: Safety checks first
        if not dry_run and not self.create_backup():
            print("❌ Cannot proceed without backup")
            return False
        
        # Backend: Discover and analyze files
        python_files = self.discover_python_files()
        
        if not python_files:
            print("❌ No Python files found for migration")
            return False
        
        # Process each file
        for file_path in python_files:
            print(f"\n🔄 Processing {file_path}")
            
            # Backend: Analyze current imports
            imports, errors = self.analyze_imports(file_path)
            if errors:
                print(f"⚠️  Analysis warnings: {errors}")
            
            # Backend: Migrate imports
            result = self.migrate_file_imports(file_path)
            self.results.append(result)
            
            # DevSecOps: Apply changes if not dry run
            if not dry_run and result.success:
                self.apply_migration(result)
            elif result.success:
                print(f"✅ Would migrate {file_path} ({len(result.changes_made)} changes)")
            else:
                print(f"❌ Migration failed for {file_path}: {result.errors}")
        
        # Generate final report
        report = self.generate_migration_report()
        
        # Save report
        report_path = self.project_root / f"migration_report_{'dry_run' if dry_run else 'live'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n📊 Migration report saved to: {report_path}")
        
        successful_count = len([r for r in self.results if r.success])
        total_count = len(self.results)
        
        print(f"\n🎯 Migration Summary: {successful_count}/{total_count} files successful")
        
        return successful_count == total_count


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Safe Atlas_Email Import Migration")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), 
                       help="Project root directory")
    parser.add_argument("--live", action="store_true", 
                       help="Perform live migration (default is dry run)")
    
    args = parser.parse_args()
    
    migrator = SafeImportMigrator(args.project_root)
    
    success = migrator.run_migration(dry_run=not args.live)
    
    if not success:
        print("\n❌ Migration completed with errors")
        sys.exit(1)
    else:
        print("\n✅ Migration completed successfully!")
        
        if not args.live:
            print("\n💡 This was a dry run. Use --live to apply changes.")
        else:
            print("\n🎉 Live migration complete! Verify functionality and run tests.")


if __name__ == "__main__":
    main()