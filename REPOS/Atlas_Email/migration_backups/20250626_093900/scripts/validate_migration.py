#!/usr/bin/env python3
"""
Migration Validation Script
DevSecOps/SRE expertise: Comprehensive testing and validation
"""

import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple
import ast


class MigrationValidator:
    """Validate that the import migration was successful"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src"
        self.errors = []
        self.warnings = []
        
    def test_python_syntax(self) -> bool:
        """Test that all Python files have valid syntax"""
        print("🔍 Testing Python syntax...")
        
        syntax_errors = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "migration_backups" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")
        
        if syntax_errors:
            print(f"❌ Found {len(syntax_errors)} syntax errors:")
            for error in syntax_errors:
                print(f"  - {error}")
            self.errors.extend(syntax_errors)
            return False
        else:
            print("✅ All Python files have valid syntax")
            return True
    
    def test_import_resolution(self) -> bool:
        """Test that imports can be resolved"""
        print("🔍 Testing import resolution...")
        
        # Add src to Python path for testing
        src_path = str(self.src_root)
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        import_errors = []
        
        # Test core modules
        core_modules = [
            "atlas_email.core.spam_classifier",
            "atlas_email.core.email_processor", 
            "atlas_email.ml.ensemble_classifier",
            "atlas_email.models.database",
            "atlas_email.api.app",
            "atlas_email.cli.main",
        ]
        
        for module_name in core_modules:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    import_errors.append(f"Module not found: {module_name}")
                else:
                    print(f"  ✅ {module_name}")
            except Exception as e:
                import_errors.append(f"Import error for {module_name}: {e}")
        
        if import_errors:
            print(f"❌ Found {len(import_errors)} import errors:")
            for error in import_errors:
                print(f"  - {error}")
            self.errors.extend(import_errors)
            return False
        else:
            print("✅ All core imports can be resolved")
            return True
    
    def test_configuration_paths(self) -> bool:
        """Test that configuration files are accessible"""
        print("🔍 Testing configuration paths...")
        
        config_files = [
            self.project_root / "config" / "settings.py",
            self.project_root / "config" / "constants.py",
            self.project_root / "config" / "credentials.py",
        ]
        
        missing_configs = []
        for config_file in config_files:
            if not config_file.exists():
                missing_configs.append(str(config_file))
        
        if missing_configs:
            print(f"❌ Missing configuration files:")
            for missing in missing_configs:
                print(f"  - {missing}")
            self.errors.extend(missing_configs)
            return False
        else:
            print("✅ All configuration files found")
            return True
    
    def test_data_paths(self) -> bool:
        """Test that data files are accessible"""
        print("🔍 Testing data file paths...")
        
        data_files = [
            self.project_root / "data" / "keywords.txt",
            self.project_root / "data" / "models" / "naive_bayes_model.json",
            self.project_root / "data" / "models" / "category_classifier.json",
        ]
        
        missing_data = []
        for data_file in data_files:
            if not data_file.exists():
                missing_data.append(str(data_file))
        
        if missing_data:
            print(f"❌ Missing data files:")
            for missing in missing_data:
                print(f"  - {missing}")
            self.errors.extend(missing_data)
            return False
        else:
            print("✅ All data files found")
            return True
    
    def test_entry_points(self) -> bool:
        """Test that entry points can be executed"""
        print("🔍 Testing entry points...")
        
        entry_point_errors = []
        
        # Test CLI entry point
        cli_main = self.src_root / "atlas_email" / "cli" / "main.py"
        if cli_main.exists():
            try:
                # Test that the file can be imported (syntax check)
                result = subprocess.run([
                    sys.executable, "-c", 
                    f"import sys; sys.path.insert(0, '{self.src_root}'); import atlas_email.cli.main"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    entry_point_errors.append(f"CLI main import failed: {result.stderr}")
                else:
                    print("  ✅ CLI main can be imported")
            except Exception as e:
                entry_point_errors.append(f"CLI main test failed: {e}")
        
        # Test API entry point  
        api_app = self.src_root / "atlas_email" / "api" / "app.py"
        if api_app.exists():
            try:
                result = subprocess.run([
                    sys.executable, "-c",
                    f"import sys; sys.path.insert(0, '{self.src_root}'); import atlas_email.api.app"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    entry_point_errors.append(f"API app import failed: {result.stderr}")
                else:
                    print("  ✅ API app can be imported")
            except Exception as e:
                entry_point_errors.append(f"API app test failed: {e}")
        
        if entry_point_errors:
            print(f"❌ Entry point errors:")
            for error in entry_point_errors:
                print(f"  - {error}")
            self.errors.extend(entry_point_errors)
            return False
        else:
            print("✅ Entry points can be imported")
            return True
    
    def test_package_structure(self) -> bool:
        """Test that package structure is valid"""
        print("🔍 Testing package structure...")
        
        required_dirs = [
            self.src_root / "atlas_email",
            self.src_root / "atlas_email" / "core",
            self.src_root / "atlas_email" / "ml", 
            self.src_root / "atlas_email" / "api",
            self.src_root / "atlas_email" / "cli",
            self.src_root / "atlas_email" / "models",
            self.src_root / "atlas_email" / "filters",
            self.src_root / "atlas_email" / "utils",
        ]
        
        missing_dirs = []
        for req_dir in required_dirs:
            if not req_dir.exists():
                missing_dirs.append(str(req_dir))
        
        if missing_dirs:
            print(f"❌ Missing required directories:")
            for missing in missing_dirs:
                print(f"  - {missing}")
            self.errors.extend(missing_dirs)
            return False
        else:
            print("✅ Package structure is valid")
            return True
    
    def run_validation(self) -> bool:
        """Run all validation tests"""
        print("🧪 Atlas_Email Migration Validation")
        print("=" * 50)
        
        tests = [
            ("Package Structure", self.test_package_structure),
            ("Python Syntax", self.test_python_syntax),
            ("Configuration Paths", self.test_configuration_paths),
            ("Data Paths", self.test_data_paths),
            ("Import Resolution", self.test_import_resolution),
            ("Entry Points", self.test_entry_points),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            if test_func():
                passed += 1
            print()
        
        print("=" * 50)
        print(f"🎯 Validation Summary: {passed}/{total} tests passed")
        
        if self.errors:
            print(f"\n❌ Found {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        success = passed == total and len(self.errors) == 0
        
        if success:
            print("\n✅ All validation tests passed! Migration was successful.")
        else:
            print("\n❌ Validation failed. Please review errors and fix issues.")
        
        return success


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Atlas_Email Import Migration")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    
    args = parser.parse_args()
    
    validator = MigrationValidator(args.project_root)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()