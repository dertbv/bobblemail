#!/usr/bin/env python3
"""
Detailed Import Analysis - Focus on problematic patterns and solutions
"""
import ast
import os
from pathlib import Path
from collections import defaultdict

def analyze_specific_circular_dependency(file1, file2, project_root):
    """Analyze a specific circular dependency between two files"""
    print(f"\n🔍 ANALYZING CIRCULAR DEPENDENCY: {file1} ↔ {file2}")
    print("=" * 60)
    
    file1_path = Path(project_root) / f"{file1}.py"
    file2_path = Path(project_root) / f"{file2}.py"
    
    # Analyze imports from file1 to file2
    print(f"\n📥 IMPORTS FROM {file1} TO {file2}:")
    if file1_path.exists():
        with open(file1_path, 'r') as f:
            content = f.read()
        
        imports_to_file2 = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if f"from {file2} import" in line:
                imports_to_file2.append((i, line.strip()))
        
        if imports_to_file2:
            for line_num, import_line in imports_to_file2:
                print(f"  Line {line_num}: {import_line}")
        else:
            print(f"  No imports found from {file1} to {file2}")
    
    # Analyze imports from file2 to file1
    print(f"\n📤 IMPORTS FROM {file2} TO {file1}:")
    if file2_path.exists():
        with open(file2_path, 'r') as f:
            content = f.read()
        
        imports_to_file1 = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if f"from {file1} import" in line:
                imports_to_file1.append((i, line.strip()))
        
        if imports_to_file1:
            for line_num, import_line in imports_to_file1:
                print(f"  Line {line_num}: {import_line}")
        else:
            print(f"  No imports found from {file2} to {file1}")
    
    return imports_to_file2, imports_to_file1

def find_late_imports(file_path):
    """Find imports that happen inside functions (late imports)"""
    late_imports = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find imports inside functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, (ast.Import, ast.ImportFrom)):
                        if isinstance(child, ast.Import):
                            modules = [alias.name for alias in child.names]
                            late_imports.append({
                                'line': child.lineno,
                                'function': node.name,
                                'type': 'import',
                                'modules': modules
                            })
                        elif isinstance(child, ast.ImportFrom):
                            module = child.module or ''
                            items = [alias.name for alias in child.names]
                            late_imports.append({
                                'line': child.lineno,
                                'function': node.name,
                                'type': 'from_import',
                                'module': module,
                                'items': items
                            })
    
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    
    return late_imports

def analyze_import_patterns():
    """Analyze specific import patterns and issues"""
    project_root = "/Users/Badman/Desktop/email/REPOS/email_project/"
    
    print("🚨 DETAILED CIRCULAR DEPENDENCY ANALYSIS")
    print("=" * 60)
    
    # Analyze the three circular dependencies found
    circular_deps = [
        ("keyword_processor", "spam_classifier"),
        ("utils", "configuration_manager"),
        ("domain_validator", "domain_cache")
    ]
    
    for file1, file2 in circular_deps:
        analyze_specific_circular_dependency(file1, file2, project_root)
    
    print("\n\n🔧 LATE IMPORT ANALYSIS (Imports inside functions)")
    print("=" * 60)
    print("Late imports often indicate circular dependency workarounds")
    
    # Check for late imports in problematic files
    problematic_files = [
        "keyword_processor.py",
        "spam_classifier.py", 
        "utils.py",
        "configuration_manager.py",
        "domain_validator.py",
        "domain_cache.py",
        "main_original.py"
    ]
    
    for filename in problematic_files:
        file_path = Path(project_root) / filename
        if file_path.exists():
            late_imports = find_late_imports(file_path)
            if late_imports:
                print(f"\n📁 {filename}:")
                for imp in late_imports:
                    if imp['type'] == 'import':
                        print(f"  Line {imp['line']} in {imp['function']}(): import {', '.join(imp['modules'])}")
                    else:
                        print(f"  Line {imp['line']} in {imp['function']}(): from {imp['module']} import {', '.join(imp['items'])}")
    
    print("\n\n💡 REFACTORING RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = [
        {
            "issue": "keyword_processor ↔ spam_classifier circular dependency",
            "cause": "Both modules try to use each other's functions",
            "solution": "Create a shared module 'classification_utils.py' for common functions like is_legitimate_company_domain()"
        },
        {
            "issue": "utils ↔ configuration_manager circular dependency", 
            "cause": "utils uses configuration_manager.get_filters() and configuration_manager uses utils functions",
            "solution": "Move configuration logic to a separate config module, keep utils purely functional"
        },
        {
            "issue": "domain_validator ↔ domain_cache circular dependency",
            "cause": "domain_validator uses cached_domain_validation, domain_cache uses lightweight_domain_validation",
            "solution": "Make domain_cache a pure cache layer that doesn't perform validation logic"
        },
        {
            "issue": "High coupling in main_original.py (18 local imports)",
            "cause": "Main module imports almost everything, creating tight coupling",
            "solution": "Use dependency injection or a service container pattern to reduce direct imports"
        },
        {
            "issue": "Many late imports throughout codebase",
            "cause": "Workaround for circular dependencies using function-level imports",
            "solution": "Fix circular dependencies to eliminate need for late imports"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['issue']}")
        print(f"   Cause: {rec['cause']}")
        print(f"   Solution: {rec['solution']}")
    
    print("\n\n🎯 PRIORITY REFACTORING TASKS")
    print("=" * 60)
    
    priority_tasks = [
        "1. HIGH PRIORITY: Break keyword_processor ↔ spam_classifier cycle",
        "   - Extract shared functions to classification_utils.py",
        "   - Move is_legitimate_company_domain() to classification_utils",
        "   - Update both modules to import from classification_utils",
        "",
        "2. MEDIUM PRIORITY: Fix utils ↔ configuration_manager cycle",
        "   - Create separate config_loader.py for configuration reading",
        "   - Keep utils purely functional (no configuration dependencies)",
        "   - Update get_filters() to use config_loader",
        "",
        "3. MEDIUM PRIORITY: Resolve domain_validator ↔ domain_cache cycle",
        "   - Make domain_cache a pure storage/caching layer",
        "   - Move validation logic entirely to domain_validator",
        "   - Cache should only store/retrieve, not validate",
        "",
        "4. LOW PRIORITY: Reduce coupling in main modules",
        "   - Use factory pattern for creating processors",
        "   - Implement dependency injection container",
        "   - Create facade interfaces for complex subsystems"
    ]
    
    for task in priority_tasks:
        print(task)

if __name__ == "__main__":
    analyze_import_patterns()