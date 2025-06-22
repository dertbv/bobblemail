#!/usr/bin/env python3
"""
Import dependency analyzer for email project
Analyzes import statements and detects circular dependencies
"""

import os
import re
import ast
from collections import defaultdict, deque
from pathlib import Path

class ImportAnalyzer:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.dependencies = defaultdict(set)  # module -> set of modules it imports
        self.reverse_dependencies = defaultdict(set)  # module -> set of modules that import it
        self.all_files = []
        self.module_names = set()
        
    def find_python_files(self):
        """Find all Python files in the project"""
        self.all_files = list(self.project_path.rglob("*.py"))
        return self.all_files
    
    def get_module_name(self, file_path):
        """Convert file path to module name"""
        rel_path = file_path.relative_to(self.project_path)
        # Remove .py extension and convert path separators to dots
        module_name = str(rel_path.with_suffix(''))
        module_name = module_name.replace(os.sep, '.')
        return module_name
    
    def extract_imports(self, file_path):
        """Extract import statements from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                print(f"Warning: Could not parse {file_path} due to syntax error")
                return []
            
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            return imports
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def is_internal_module(self, import_name):
        """Check if an import is an internal project module"""
        # Check if it's a relative import or matches our project modules
        if import_name.startswith('.'):
            return True
        
        # Check if it matches any of our module names
        for module_name in self.module_names:
            if import_name == module_name or import_name.startswith(module_name + '.'):
                return True
        
        # Check if it's a direct file name match
        base_name = import_name.split('.')[0]
        return base_name in [m.split('.')[0] for m in self.module_names]
    
    def build_dependency_graph(self):
        """Build the dependency graph from all Python files"""
        files = self.find_python_files()
        
        # First pass: collect all module names
        for file_path in files:
            module_name = self.get_module_name(file_path)
            self.module_names.add(module_name)
        
        # Second pass: extract imports and build dependencies
        for file_path in files:
            module_name = self.get_module_name(file_path)
            imports = self.extract_imports(file_path)
            
            for import_name in imports:
                if self.is_internal_module(import_name):
                    # Normalize the import name
                    if import_name.startswith('.'):
                        # Handle relative imports
                        parent_module = '.'.join(module_name.split('.')[:-1])
                        if import_name == '.':
                            normalized_import = parent_module
                        else:
                            normalized_import = parent_module + import_name
                    else:
                        normalized_import = import_name
                    
                    # Find the actual module name that matches
                    matched_module = None
                    for mod_name in self.module_names:
                        if normalized_import == mod_name or mod_name.endswith('.' + normalized_import):
                            matched_module = mod_name
                            break
                    
                    if not matched_module:
                        # Try to match by base name
                        base_import = normalized_import.split('.')[0]
                        for mod_name in self.module_names:
                            if mod_name.split('.')[0] == base_import:
                                matched_module = mod_name
                                break
                    
                    if matched_module and matched_module != module_name:
                        self.dependencies[module_name].add(matched_module)
                        self.reverse_dependencies[matched_module].add(module_name)
    
    def find_circular_dependencies(self):
        """Find circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependencies[node]:
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def analyze_complexity(self):
        """Analyze import complexity"""
        complexity_stats = {}
        
        for module, deps in self.dependencies.items():
            complexity_stats[module] = {
                'imports_count': len(deps),
                'imported_by_count': len(self.reverse_dependencies[module]),
                'imports': list(deps),
                'imported_by': list(self.reverse_dependencies[module])
            }
        
        return complexity_stats
    
    def generate_report(self):
        """Generate a comprehensive report"""
        print("=" * 80)
        print("EMAIL PROJECT IMPORT DEPENDENCY ANALYSIS")
        print("=" * 80)
        
        # Build the dependency graph
        self.build_dependency_graph()
        
        print(f"\nTotal Python files analyzed: {len(self.all_files)}")
        print(f"Total internal modules: {len(self.module_names)}")
        
        # Find circular dependencies
        cycles = self.find_circular_dependencies()
        
        print(f"\n{'='*50}")
        print("CIRCULAR DEPENDENCIES")
        print(f"{'='*50}")
        
        if cycles:
            print(f"Found {len(cycles)} circular dependency cycles:")
            for i, cycle in enumerate(cycles, 1):
                print(f"\nCycle {i}:")
                for j in range(len(cycle) - 1):
                    print(f"  {cycle[j]} -> {cycle[j+1]}")
        else:
            print("No circular dependencies found!")
        
        # Analyze complexity
        complexity_stats = self.analyze_complexity()
        
        print(f"\n{'='*50}")
        print("IMPORT COMPLEXITY ANALYSIS")
        print(f"{'='*50}")
        
        # Sort modules by import count
        sorted_by_imports = sorted(complexity_stats.items(), 
                                 key=lambda x: x[1]['imports_count'], 
                                 reverse=True)
        
        print("\nModules with most imports (top 10):")
        for module, stats in sorted_by_imports[:10]:
            if stats['imports_count'] > 0:
                print(f"  {module}: {stats['imports_count']} imports")
                for imp in stats['imports']:
                    print(f"    -> {imp}")
        
        # Sort modules by how many times they're imported
        sorted_by_imported = sorted(complexity_stats.items(), 
                                  key=lambda x: x[1]['imported_by_count'], 
                                  reverse=True)
        
        print("\nMost imported modules (top 10):")
        for module, stats in sorted_by_imported[:10]:
            if stats['imported_by_count'] > 0:
                print(f"  {module}: imported by {stats['imported_by_count']} modules")
                for imp in stats['imported_by']:
                    print(f"    <- {imp}")
        
        # Focus on newly refactored modules
        refactored_modules = ['main', 'menu_handler', 'processing_controller', 
                            'configuration_manager', 'settings']
        
        print(f"\n{'='*50}")
        print("REFACTORED MODULES ANALYSIS")
        print(f"{'='*50}")
        
        for module_name in refactored_modules:
            matching_modules = [m for m in complexity_stats.keys() if m.endswith(module_name)]
            for module in matching_modules:
                stats = complexity_stats[module]
                print(f"\n{module}:")
                print(f"  Imports: {stats['imports_count']} modules")
                print(f"  Imported by: {stats['imported_by_count']} modules")
                if stats['imports']:
                    print("  Imports:")
                    for imp in stats['imports']:
                        print(f"    -> {imp}")
                if stats['imported_by']:
                    print("  Imported by:")
                    for imp in stats['imported_by']:
                        print(f"    <- {imp}")
        
        print(f"\n{'='*50}")
        print("RECOMMENDATIONS")
        print(f"{'='*50}")
        
        # Generate recommendations
        recommendations = []
        
        if cycles:
            recommendations.append("🔄 CRITICAL: Resolve circular dependencies immediately")
        
        high_import_modules = [m for m, s in complexity_stats.items() if s['imports_count'] > 5]
        if high_import_modules:
            recommendations.append(f"📊 Consider refactoring modules with high import counts: {', '.join(high_import_modules[:3])}")
        
        central_modules = [m for m, s in complexity_stats.items() if s['imported_by_count'] > 5]
        if central_modules:
            recommendations.append(f"🎯 Central modules (consider dependency injection): {', '.join(central_modules[:3])}")
        
        if not recommendations:
            recommendations.append("✅ Import structure looks healthy!")
        
        for rec in recommendations:
            print(f"  {rec}")
        
        return {
            'cycles': cycles,
            'complexity_stats': complexity_stats,
            'recommendations': recommendations
        }

if __name__ == "__main__":
    project_path = "/Users/Badman/Desktop/email/REPOS/email_project"
    analyzer = ImportAnalyzer(project_path)
    results = analyzer.generate_report()