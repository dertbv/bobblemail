#!/usr/bin/env python3
"""
Import Analyzer - Analyzes Python imports for circular dependencies and complexity
"""
import ast
import os
import re
from collections import defaultdict, deque
from pathlib import Path
import json

class ImportAnalyzer:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.files = {}
        self.imports = defaultdict(set)
        self.local_imports = defaultdict(set)
        self.external_imports = defaultdict(set)
        self.circular_deps = []
        self.unused_imports = defaultdict(set)
        
    def find_python_files(self):
        """Find all Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def extract_imports(self, file_path):
        """Extract import statements from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = {
                'standard': set(),
                'local': set(),
                'external': set(),
                'relative': set(),
                'from_imports': set(),
                'import_statements': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports['import_statements'].append(f"import {alias.name}")
                        if self.is_local_import(alias.name):
                            imports['local'].add(alias.name)
                        elif self.is_standard_library(alias.name):
                            imports['standard'].add(alias.name)
                        else:
                            imports['external'].add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    level = node.level
                    
                    if level > 0:  # Relative import
                        imports['relative'].add(f"{'.' * level}{module}")
                        imports['import_statements'].append(f"from {'.' * level}{module} import {', '.join([alias.name for alias in node.names])}")
                    else:
                        imports['from_imports'].add(module)
                        imports['import_statements'].append(f"from {module} import {', '.join([alias.name for alias in node.names])}")
                        
                        if self.is_local_import(module):
                            imports['local'].add(module)
                        elif self.is_standard_library(module):
                            imports['standard'].add(module)
                        else:
                            imports['external'].add(module)
            
            return imports
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def is_local_import(self, module_name):
        """Check if an import is a local module"""
        if not module_name:
            return False
            
        # Check if it's a file in our project
        base_name = module_name.split('.')[0]
        local_files = [f.stem for f in self.find_python_files()]
        return base_name in local_files
    
    def is_standard_library(self, module_name):
        """Check if an import is from the standard library"""
        stdlib_modules = {
            'os', 'sys', 'json', 'ast', 'collections', 'pathlib', 'datetime',
            'time', 'random', 'math', 'statistics', 'itertools', 'functools',
            'operator', 'copy', 'pickle', 're', 'string', 'textwrap',
            'unicodedata', 'io', 'logging', 'argparse', 'configparser',
            'sqlite3', 'csv', 'urllib', 'http', 'email', 'smtplib',
            'imaplib', 'poplib', 'uuid', 'hashlib', 'hmac', 'secrets',
            'threading', 'multiprocessing', 'subprocess', 'socket',
            'ssl', 'asyncio', 'concurrent', 'queue', 'contextlib',
            'weakref', 'gc', 'types', 'inspect', 'importlib'
        }
        
        base_module = module_name.split('.')[0] if module_name else ''
        return base_module in stdlib_modules
    
    def build_dependency_graph(self):
        """Build a dependency graph of local imports"""
        graph = defaultdict(set)
        
        for file_path in self.find_python_files():
            imports = self.extract_imports(file_path)
            if imports:
                file_stem = file_path.stem
                self.files[file_stem] = {
                    'path': file_path,
                    'imports': imports
                }
                
                # Add local dependencies
                for local_import in imports['local']:
                    graph[file_stem].add(local_import)
                
                # Handle relative imports
                for rel_import in imports['relative']:
                    if rel_import.startswith('.'):
                        # Remove leading dots and resolve relative path
                        clean_import = rel_import.lstrip('.')
                        if clean_import:
                            graph[file_stem].add(clean_import)
        
        return graph
    
    def find_circular_dependencies(self, graph):
        """Find circular dependencies using DFS"""
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path.copy(), visited, rec_stack)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            rec_stack.remove(node)
            return None
        
        visited = set()
        cycles = []
        
        for node in graph:
            if node not in visited:
                cycle = dfs(node, [], visited, set())
                if cycle:
                    cycles.append(cycle)
        
        return cycles
    
    def analyze_import_complexity(self):
        """Analyze import complexity for each file"""
        complexity_report = {}
        
        for file_stem, file_info in self.files.items():
            imports = file_info['imports']
            complexity = {
                'total_imports': (len(imports['standard']) + 
                                len(imports['local']) + 
                                len(imports['external'])),
                'local_imports': len(imports['local']),
                'external_imports': len(imports['external']),
                'relative_imports': len(imports['relative']),
                'complexity_score': 0
            }
            
            # Calculate complexity score
            complexity['complexity_score'] = (
                complexity['total_imports'] * 1 +
                complexity['local_imports'] * 2 +  # Local imports are more complex
                complexity['relative_imports'] * 3  # Relative imports are most complex
            )
            
            complexity_report[file_stem] = complexity
        
        return complexity_report
    
    def find_potential_unused_imports(self):
        """Find potentially unused imports (basic heuristic)"""
        unused_report = {}
        
        for file_stem, file_info in self.files.items():
            try:
                with open(file_info['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                unused = set()
                
                # Check each import
                for import_type in ['standard', 'local', 'external']:
                    for imported_module in file_info['imports'][import_type]:
                        # Basic check: see if the module name appears in the file
                        module_base = imported_module.split('.')[0]
                        if module_base not in content.replace(f"import {module_base}", ""):
                            unused.add(imported_module)
                
                if unused:
                    unused_report[file_stem] = unused
                    
            except Exception as e:
                print(f"Error checking unused imports in {file_stem}: {e}")
        
        return unused_report
    
    def generate_report(self):
        """Generate comprehensive import analysis report"""
        print("🔍 EMAIL PROJECT IMPORT ANALYSIS REPORT")
        print("=" * 50)
        
        # Build dependency graph
        graph = self.build_dependency_graph()
        
        # Find circular dependencies
        cycles = self.find_circular_dependencies(graph)
        
        # Analyze complexity
        complexity = self.analyze_import_complexity()
        
        # Find unused imports
        unused = self.find_potential_unused_imports()
        
        print(f"\n📊 PROJECT OVERVIEW")
        print(f"Total Python files: {len(self.files)}")
        print(f"Total modules in dependency graph: {len(graph)}")
        
        # Circular Dependencies
        print(f"\n🔄 CIRCULAR DEPENDENCIES")
        if cycles:
            print(f"Found {len(cycles)} circular dependency chains:")
            for i, cycle in enumerate(cycles, 1):
                print(f"  {i}. {' → '.join(cycle)}")
        else:
            print("✅ No circular dependencies found!")
        
        # Complex Import Patterns
        print(f"\n📈 IMPORT COMPLEXITY ANALYSIS")
        sorted_complexity = sorted(complexity.items(), 
                                 key=lambda x: x[1]['complexity_score'], 
                                 reverse=True)
        
        print("Top 10 most complex files:")
        for file_stem, comp in sorted_complexity[:10]:
            print(f"  {file_stem}: Score {comp['complexity_score']} "
                  f"(Total: {comp['total_imports']}, "
                  f"Local: {comp['local_imports']}, "
                  f"Relative: {comp['relative_imports']})")
        
        # Files with many local imports (potential coupling issues)
        high_coupling = [(f, c) for f, c in complexity.items() if c['local_imports'] > 5]
        if high_coupling:
            print(f"\n⚠️  HIGH COUPLING FILES (>5 local imports):")
            for file_stem, comp in sorted(high_coupling, key=lambda x: x[1]['local_imports'], reverse=True):
                print(f"  {file_stem}: {comp['local_imports']} local imports")
        
        # Unused Imports
        print(f"\n🗑️  POTENTIALLY UNUSED IMPORTS")
        if unused:
            print(f"Files with potentially unused imports:")
            for file_stem, unused_imports in unused.items():
                print(f"  {file_stem}:")
                for imp in unused_imports:
                    print(f"    - {imp}")
        else:
            print("✅ No obviously unused imports detected!")
        
        # Detailed Import Breakdown
        print(f"\n📋 DETAILED IMPORT BREAKDOWN")
        
        # Most imported local modules
        local_import_count = defaultdict(int)
        for file_stem, file_info in self.files.items():
            for local_imp in file_info['imports']['local']:
                local_import_count[local_imp] += 1
        
        if local_import_count:
            print("Most imported local modules:")
            sorted_local = sorted(local_import_count.items(), key=lambda x: x[1], reverse=True)
            for module, count in sorted_local[:10]:
                print(f"  {module}: imported by {count} files")
        
        # Files with relative imports
        relative_files = [(f, len(info['imports']['relative'])) 
                         for f, info in self.files.items() 
                         if info['imports']['relative']]
        
        if relative_files:
            print(f"\n🔗 FILES WITH RELATIVE IMPORTS:")
            for file_stem, count in sorted(relative_files, key=lambda x: x[1], reverse=True):
                print(f"  {file_stem}: {count} relative imports")
                for rel_imp in self.files[file_stem]['imports']['relative']:
                    print(f"    - {rel_imp}")
        
        return {
            'cycles': cycles,
            'complexity': complexity,
            'unused': unused,
            'graph': {k: list(v) for k, v in graph.items()},
            'files': len(self.files)
        }

if __name__ == "__main__":
    analyzer = ImportAnalyzer("/Users/Badman/Desktop/email/REPOS/email_project/")
    report = analyzer.generate_report()