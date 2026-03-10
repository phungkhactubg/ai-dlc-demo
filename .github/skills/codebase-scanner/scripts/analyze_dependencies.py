#!/usr/bin/env python3
"""
Dependency Analyzer

Analyzes import statements and dependencies between modules.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


class DependencyAnalyzer:
    """Analyzes codebase dependencies and module relationships."""
    
    def __init__(self, root_dir: Path, excludes: List[str], verbose: bool = False):
        self.root_dir = Path(root_dir)
        self.excludes = excludes
        self.verbose = verbose
        self.modules: Dict[str, Dict] = {}
    
    def log(self, message: str):
        if self.verbose:
            print(f"   [deps] {message}")
    
    def analyze(self, project_info: Dict) -> Dict:
        """Analyze all dependencies based on detected languages."""
        result = {
            "modules": {},
            "external_deps": [],
            "internal_deps": [],
            "circular_deps": [],
            "dependency_graph": {},
            "most_imported": [],
            "most_dependent": [],
        }
        
        languages = project_info.get("languages", [])
        
        # Analyze based on language
        if "Go" in languages:
            self._analyze_go_deps(result)
        
        if "TypeScript" in languages or "JavaScript" in languages:
            self._analyze_js_ts_deps(result)
        
        if "Python" in languages:
            self._analyze_python_deps(result)
        
        if "Java" in languages:
            self._analyze_java_deps(result)
            
        if "C#" in languages:
            self._analyze_csharp_deps(result)
        
        # Build dependency graph
        result["dependency_graph"] = self._build_graph()
        
        # Find circular dependencies
        result["circular_deps"] = self._find_circular_deps()
        
        # Calculate metrics
        result["most_imported"] = self._get_most_imported()
        result["most_dependent"] = self._get_most_dependent()
        
        return result
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)
        for pattern in self.excludes:
            if pattern in path_str:
                return True
        return False
    
    def _analyze_java_deps(self, result: Dict):
        """Analyze Java imports."""
        self.log("Analyzing Java dependencies...")
        
        import_pattern = re.compile(r'import\s+([\w\.]+);')
        
        for path in self.root_dir.rglob("*.java"):
            if self._should_exclude(path):
                continue
            
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                
                # Use package as module identifier if possible
                pkg_match = re.search(r'package\s+([\w\.]+);', content)
                module_id = pkg_match.group(1) if pkg_match else str(path.parent.relative_to(self.root_dir))
                
                self._ensure_module(module_id, "Java")
                self.modules[module_id]["files"].append(rel_path)
                
                # Find imports
                for match in import_pattern.finditer(content):
                    imp = match.group(1)
                    self.modules[module_id]["imports"].add(imp)
                    
                    if not imp.startswith("java.") and not imp.startswith("javax."):
                        result["external_deps"].append({
                            "from": module_id,
                            "import": imp,
                            "type": "external",
                        })
                
                # Find exports
                export_patterns = [
                    (r'public\s+(?:class|interface|enum)\s+(\w+)', 'type'),
                ]
                for pattern, kind in export_patterns:
                    for match in re.finditer(pattern, content):
                        self.modules[module_id]["exports"].add((match.group(1), kind))
                        
            except:
                pass

    def _analyze_csharp_deps(self, result: Dict):
        """Analyze C# imports."""
        self.log("Analyzing C# dependencies...")
        
        import_pattern = re.compile(r'using\s+([\w\.]+);')
        
        for path in self.root_dir.rglob("*.cs"):
            if self._should_exclude(path):
                continue
            
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                
                # Use namespace as module identifier
                ns_match = re.search(r'namespace\s+([\w\.]+)', content)
                module_id = ns_match.group(1) if ns_match else str(path.parent.relative_to(self.root_dir))
                
                self._ensure_module(module_id, "C#")
                self.modules[module_id]["files"].append(rel_path)
                
                # Find imports
                for match in import_pattern.finditer(content):
                    imp = match.group(1)
                    self.modules[module_id]["imports"].add(imp)
                    
                    if not imp.startswith("System") and not imp.startswith("Microsoft"):
                        result["external_deps"].append({
                            "from": module_id,
                            "import": imp,
                            "type": "external",
                        })
                
                # Find exports
                export_patterns = [
                    (r'(?:public|internal)\s+(?:class|interface|enum|struct)\s+(\w+)', 'type'),
                ]
                for pattern, kind in export_patterns:
                    for match in re.finditer(pattern, content):
                        self.modules[module_id]["exports"].add((match.group(1), kind))
                        
            except:
                pass

    def _ensure_module(self, module_id: str, language: str):
        """Ensure module exists in self.modules."""
        if module_id not in self.modules:
            self.modules[module_id] = {
                "name": module_id,
                "language": language,
                "files": [],
                "imports": set(),
                "imported_by": set(),
                "exports": set(),
            }
    
    def _analyze_go_deps(self, result: Dict):
        """Analyze Go imports."""
        self.log("Analyzing Go dependencies...")
        
        import_pattern = re.compile(r'import\s+\(\s*([\s\S]*?)\s*\)|import\s+"([^"]+)"')
        single_import = re.compile(r'"([^"]+)"')
        
        for path in self.root_dir.rglob("*.go"):
            if self._should_exclude(path) or "_test.go" in str(path):
                continue
            
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                parent_dir = str(path.parent.relative_to(self.root_dir))
                
                if parent_dir not in self.modules:
                    self.modules[parent_dir] = {
                        "name": parent_dir,
                        "language": "Go",
                        "files": [],
                        "imports": set(),
                        "imported_by": set(),
                        "exports": set(),
                    }
                
                self.modules[parent_dir]["files"].append(rel_path)
                
                # Find imports
                imports = set()
                for match in import_pattern.finditer(content):
                    if match.group(1):  # Multi-import
                        for imp in single_import.findall(match.group(1)):
                            imports.add(imp)
                    elif match.group(2):  # Single import
                        imports.add(match.group(2))
                
                # Classify imports
                for imp in imports:
                    if imp.startswith("github.com") or imp.startswith("go.") or imp.startswith("golang.org"):
                        # Could be internal or external
                        result["external_deps"].append({
                            "from": parent_dir,
                            "import": imp,
                            "type": "external",
                        })
                    elif "/" in imp:
                        result["external_deps"].append({
                            "from": parent_dir,
                            "import": imp,
                            "type": "external",
                        })
                    else:
                        # Standard library
                        pass
                    
                    self.modules[parent_dir]["imports"].add(imp)
                
                # Find exports (public functions/types)
                export_patterns = [
                    (r'func\s+([A-Z][a-zA-Z0-9_]*)\s*\(', 'function'),
                    (r'type\s+([A-Z][a-zA-Z0-9_]*)\s+', 'type'),
                    (r'var\s+([A-Z][a-zA-Z0-9_]*)\s+', 'variable'),
                    (r'const\s+([A-Z][a-zA-Z0-9_]*)\s+', 'constant'),
                ]
                
                for pattern, kind in export_patterns:
                    for match in re.finditer(pattern, content):
                        self.modules[parent_dir]["exports"].add((match.group(1), kind))
                
            except (UnicodeDecodeError, IOError) as e:
                self.log(f"Error reading {path}: {e}")
    
    def _analyze_js_ts_deps(self, result: Dict):
        """Analyze JavaScript/TypeScript imports."""
        self.log("Analyzing JavaScript/TypeScript dependencies...")
        
        import_patterns = [
            re.compile(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'),
            re.compile(r'import\s+[\'"]([^\'"]+)[\'"]'),
            re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'),
            re.compile(r'export\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'),
        ]
        
        export_patterns = [
            re.compile(r'export\s+(default\s+)?(function|class|const|let|var|interface|type)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'),
            re.compile(r'export\s*\{\s*([^}]+)\s*\}'),
            re.compile(r'module\.exports\s*=\s*'),
        ]
        
        for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
            for path in self.root_dir.rglob(ext):
                if self._should_exclude(path):
                    continue
                
                try:
                    content = path.read_text(encoding="utf-8")
                    rel_path = str(path.relative_to(self.root_dir))
                    
                    # Use file as module identifier
                    module_id = rel_path
                    
                    if module_id not in self.modules:
                        self.modules[module_id] = {
                            "name": path.stem,
                            "path": rel_path,
                            "language": "TypeScript" if path.suffix in [".ts", ".tsx"] else "JavaScript",
                            "files": [rel_path],
                            "imports": set(),
                            "imported_by": set(),
                            "exports": set(),
                        }
                    
                    # Find imports
                    for pattern in import_patterns:
                        for match in pattern.finditer(content):
                            imp = match.group(1)
                            self.modules[module_id]["imports"].add(imp)
                            
                            if imp.startswith("."):
                                result["internal_deps"].append({
                                    "from": rel_path,
                                    "import": imp,
                                    "type": "internal",
                                })
                            elif not imp.startswith("@") or imp.startswith("@/"):
                                result["external_deps"].append({
                                    "from": rel_path,
                                    "import": imp,
                                    "type": "external",
                                })
                    
                    # Find exports
                    for pattern in export_patterns:
                        for match in pattern.finditer(content):
                            if match.lastindex and match.lastindex >= 3:
                                self.modules[module_id]["exports"].add((match.group(3), match.group(2)))
                            elif match.lastindex and match.lastindex >= 1:
                                # Named exports
                                exports = match.group(1).split(",")
                                for export in exports:
                                    export = export.strip().split(" ")[0]
                                    if export:
                                        self.modules[module_id]["exports"].add((export, "named"))
                    
                except (UnicodeDecodeError, IOError) as e:
                    self.log(f"Error reading {path}: {e}")
    
    def _analyze_python_deps(self, result: Dict):
        """Analyze Python imports."""
        self.log("Analyzing Python dependencies...")
        
        import_patterns = [
            re.compile(r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)(?:\s+as\s+\w+)?', re.MULTILINE),
            re.compile(r'^from\s+([a-zA-Z_.][a-zA-Z0-9_.]*)\s+import', re.MULTILINE),
        ]
        
        for path in self.root_dir.rglob("*.py"):
            if self._should_exclude(path):
                continue
            
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                parent_dir = str(path.parent.relative_to(self.root_dir))
                
                # Use directory as module for packages, file for scripts
                if (path.parent / "__init__.py").exists():
                    module_id = parent_dir
                else:
                    module_id = rel_path
                
                if module_id not in self.modules:
                    self.modules[module_id] = {
                        "name": module_id,
                        "language": "Python",
                        "files": [],
                        "imports": set(),
                        "imported_by": set(),
                        "exports": set(),
                    }
                
                if rel_path not in self.modules[module_id]["files"]:
                    self.modules[module_id]["files"].append(rel_path)
                
                # Find imports
                for pattern in import_patterns:
                    for match in pattern.finditer(content):
                        imp = match.group(1)
                        self.modules[module_id]["imports"].add(imp)
                        
                        if imp.startswith("."):
                            result["internal_deps"].append({
                                "from": rel_path,
                                "import": imp,
                                "type": "internal",
                            })
                        else:
                            result["external_deps"].append({
                                "from": rel_path,
                                "import": imp,
                                "type": "external",
                            })
                
                # Find exports (public classes/functions)
                export_patterns = [
                    (r'^class\s+([A-Z][a-zA-Z0-9_]*)\s*[:\(]', 'class'),
                    (r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', 'function'),
                    (r'^([A-Z_][A-Z0-9_]*)\s*=', 'constant'),
                ]
                
                for pattern, kind in export_patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        name = match.group(1)
                        if not name.startswith("_"):  # Skip private
                            self.modules[module_id]["exports"].add((name, kind))
                
            except (UnicodeDecodeError, IOError) as e:
                self.log(f"Error reading {path}: {e}")
    
    def _build_graph(self) -> Dict:
        """Build dependency graph structure."""
        graph = {
            "nodes": [],
            "edges": [],
        }
        
        # Create nodes
        for module_id, module_info in self.modules.items():
            graph["nodes"].append({
                "id": module_id,
                "name": module_info["name"],
                "language": module_info.get("language", "Unknown"),
                "file_count": len(module_info.get("files", [])),
                "export_count": len(module_info.get("exports", set())),
                "import_count": len(module_info.get("imports", set())),
            })
        
        # Create edges based on internal imports
        module_names = set(self.modules.keys())
        for module_id, module_info in self.modules.items():
            for imp in module_info.get("imports", set()):
                # Try to match import to a module
                for target_id in module_names:
                    if target_id != module_id:
                        if imp in target_id or target_id in imp:
                            graph["edges"].append({
                                "source": module_id,
                                "target": target_id,
                                "type": "imports",
                            })
                            # Update imported_by
                            if target_id in self.modules:
                                self.modules[target_id]["imported_by"].add(module_id)
        
        return graph
    
    def _find_circular_deps(self) -> List[Dict]:
        """Find circular dependencies."""
        circular = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            module = self.modules.get(node, {})
            for imported in module.get("imports", set()):
                # Find matching module
                for target in self.modules.keys():
                    if imported in target or target in imported:
                        if target in rec_stack:
                            # Found cycle
                            cycle_start = path.index(target) if target in path else 0
                            cycle = path[cycle_start:] + [target]
                            circular.append({
                                "cycle": cycle,
                                "length": len(cycle) - 1,
                            })
                        elif target not in visited:
                            dfs(target, path.copy())
            
            rec_stack.discard(node)
        
        for module_id in self.modules.keys():
            if module_id not in visited:
                dfs(module_id, [])
        
        # Remove duplicates
        unique_circular = []
        seen = set()
        for c in circular:
            key = tuple(sorted(c["cycle"]))
            if key not in seen:
                seen.add(key)
                unique_circular.append(c)
        
        return unique_circular[:10]  # Limit to 10
    
    def _get_most_imported(self) -> List[Dict]:
        """Get most imported modules."""
        counts = []
        for module_id, module_info in self.modules.items():
            imported_by_count = len(module_info.get("imported_by", set()))
            if imported_by_count > 0:
                counts.append({
                    "module": module_id,
                    "imported_by_count": imported_by_count,
                })
        
        counts.sort(key=lambda x: x["imported_by_count"], reverse=True)
        return counts[:10]
    
    def _get_most_dependent(self) -> List[Dict]:
        """Get modules with most dependencies."""
        counts = []
        for module_id, module_info in self.modules.items():
            import_count = len(module_info.get("imports", set()))
            if import_count > 0:
                counts.append({
                    "module": module_id,
                    "import_count": import_count,
                })
        
        counts.sort(key=lambda x: x["import_count"], reverse=True)
        return counts[:10]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze codebase dependencies")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Simple project info for standalone run
    project_info = {"languages": ["Go", "TypeScript", "Python"]}
    
    analyzer = DependencyAnalyzer(Path.cwd(), [], args.verbose)
    result = analyzer.analyze(project_info)
    
    # Convert sets to lists for JSON
    for module_id, module_info in result.get("modules", {}).items():
        if "imports" in module_info:
            module_info["imports"] = list(module_info["imports"])
        if "imported_by" in module_info:
            module_info["imported_by"] = list(module_info["imported_by"])
        if "exports" in module_info:
            module_info["exports"] = list(module_info["exports"])
    
    if args.output:
        output_path = Path(args.output) / "dependencies.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Saved to {output_path}")
    else:
        print(json.dumps(result, indent=2, default=str))
