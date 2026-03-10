#!/usr/bin/env python3
"""
Structure Analyzer

Analyzes directory structure, files, and categorizes codebase organization.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime


class StructureAnalyzer:
    """Analyzes codebase directory and file structure."""
    
    # File categories
    FILE_CATEGORIES = {
        "source": [".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".swift"],
        "config": [".json", ".yaml", ".yml", ".toml", ".ini", ".env", ".properties", ".xml"],
        "docs": [".md", ".rst", ".txt", ".adoc"],
        "test": ["_test.go", ".test.ts", ".test.tsx", ".test.js", ".spec.ts", ".spec.tsx", ".spec.js", "test_*.py", "*_test.py"],
        "style": [".css", ".scss", ".sass", ".less", ".styl"],
        "template": [".html", ".htm", ".hbs", ".ejs", ".pug", ".vue", ".svelte"],
        "data": [".sql", ".graphql", ".gql"],
        "build": ["Makefile", "Dockerfile", "docker-compose", ".github/workflows"],
        "assets": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot"],
    }
    
    # Important files to highlight
    IMPORTANT_FILES = [
        "main.go", "main.py", "index.ts", "index.tsx", "index.js", "app.ts", "app.tsx", "app.js",
        "server.go", "server.ts", "server.js", "router.go", "routes.ts", "routes.js",
        "package.json", "go.mod", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle",
        "README.md", "CHANGELOG.md", "LICENSE",
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".env.example", "config.yaml", "config.json",
    ]
    
    def __init__(self, root_dir: Path, excludes: List[str], depth: int = 3, verbose: bool = False):
        self.root_dir = Path(root_dir)
        self.excludes = excludes
        self.depth = depth
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(f"   [structure] {message}")
    
    def analyze(self) -> Dict:
        """Perform full structure analysis."""
        result = {
            "root": str(self.root_dir),
            "total_files": 0,
            "total_dirs": 0,
            "total_lines": 0,
            "total_size_bytes": 0,
            "tree": {},
            "categories": defaultdict(list),
            "by_extension": defaultdict(int),
            "by_directory": {},
            "important_files": [],
            "entry_points": [],
            "modules": [],
            "largest_files": [],
        }
        
        # Build directory tree
        result["tree"] = self._build_tree(self.root_dir, 0)
        
        # Analyze all files
        file_stats = self._analyze_files()
        result["total_files"] = file_stats["total_files"]
        result["total_dirs"] = file_stats["total_dirs"]
        result["total_lines"] = file_stats["total_lines"]
        result["total_size_bytes"] = file_stats["total_size"]
        result["by_extension"] = dict(file_stats["by_extension"])
        result["categories"] = {k: v for k, v in file_stats["categories"].items() if v}
        result["largest_files"] = file_stats["largest_files"]
        
        # Find entry points
        result["entry_points"] = self._find_entry_points()
        
        # Find important files
        result["important_files"] = self._find_important_files()
        
        # Identify modules/packages
        result["modules"] = self._identify_modules()
        
        # Analyze directory purposes
        result["by_directory"] = self._analyze_directories()
        
        return result
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)
        name = path.name
        
        # Always exclude hidden files/dirs (except .github)
        if name.startswith('.') and name != '.github':
            return True
        
        for pattern in self.excludes:
            if pattern in path_str or name == pattern:
                return True
        
        return False
    
    def _build_tree(self, path: Path, current_depth: int) -> Dict:
        """Build directory tree structure."""
        if current_depth > self.depth:
            return {"truncated": True}
        
        tree = {
            "name": path.name or str(path),
            "type": "directory" if path.is_dir() else "file",
        }
        
        if path.is_file():
            tree["size"] = path.stat().st_size
            tree["extension"] = path.suffix
            return tree
        
        if path.is_dir():
            children = []
            try:
                for child in sorted(path.iterdir()):
                    if not self._should_exclude(child):
                        children.append(self._build_tree(child, current_depth + 1))
            except PermissionError:
                tree["error"] = "Permission denied"
            
            tree["children"] = children
            tree["child_count"] = len(children)
        
        return tree
    
    def _analyze_files(self) -> Dict:
        """Analyze all files in codebase."""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_lines": 0,
            "total_size": 0,
            "by_extension": defaultdict(int),
            "categories": defaultdict(list),
            "largest_files": [],
        }
        
        all_files = []
        
        for path in self.root_dir.rglob("*"):
            if self._should_exclude(path):
                continue
            
            if path.is_dir():
                stats["total_dirs"] += 1
                continue
            
            if path.is_file():
                stats["total_files"] += 1
                
                try:
                    size = path.stat().st_size
                    stats["total_size"] += size
                    
                    ext = path.suffix.lower()
                    stats["by_extension"][ext] += 1
                    
                    rel_path = str(path.relative_to(self.root_dir))
                    
                    # Categorize file
                    category = self._categorize_file(path)
                    if category:
                        stats["categories"][category].append(rel_path)
                    
                    # Count lines for source files
                    if ext in self.FILE_CATEGORIES["source"]:
                        try:
                            lines = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
                            stats["total_lines"] += lines
                            all_files.append({
                                "path": rel_path,
                                "size": size,
                                "lines": lines,
                            })
                        except:
                            pass
                    else:
                        all_files.append({
                            "path": rel_path,
                            "size": size,
                            "lines": 0,
                        })
                    
                except (OSError, IOError):
                    pass
        
        # Find largest files
        all_files.sort(key=lambda x: x["size"], reverse=True)
        stats["largest_files"] = all_files[:20]
        
        return stats
    
    def _categorize_file(self, path: Path) -> Optional[str]:
        """Categorize a file by its extension or name."""
        name = path.name.lower()
        ext = path.suffix.lower()
        
        for category, patterns in self.FILE_CATEGORIES.items():
            for pattern in patterns:
                if pattern.startswith("*"):
                    if name.endswith(pattern[1:]):
                        return category
                elif pattern.startswith("."):
                    if ext == pattern:
                        return category
                elif pattern in name:
                    return category
        
        return None
    
    def _find_entry_points(self) -> List[Dict]:
        """Find application entry points."""
        entry_points = []
        
        # Go entry points
        for path in self.root_dir.rglob("main.go"):
            if not self._should_exclude(path):
                entry_points.append({
                    "file": str(path.relative_to(self.root_dir)),
                    "type": "Go main",
                    "language": "Go",
                })
        
        # Also check cmd directory
        cmd_dir = self.root_dir / "cmd"
        if cmd_dir.exists():
            for main_go in cmd_dir.rglob("main.go"):
                if not self._should_exclude(main_go):
                    entry_points.append({
                        "file": str(main_go.relative_to(self.root_dir)),
                        "type": "Go cmd",
                        "language": "Go",
                    })
        
        # JavaScript/TypeScript entry points
        for pattern in ["index.ts", "index.tsx", "index.js", "main.ts", "main.tsx", "main.js", "app.ts", "app.tsx", "app.js"]:
            for path in self.root_dir.rglob(pattern):
                if not self._should_exclude(path):
                    # Check if it's in src or root
                    rel_path = path.relative_to(self.root_dir)
                    if str(rel_path).count(os.sep) <= 2:  # Not too deep
                        entry_points.append({
                            "file": str(rel_path),
                            "type": "JavaScript/TypeScript entry",
                            "language": "TypeScript" if pattern.endswith(".ts") or pattern.endswith(".tsx") else "JavaScript",
                        })
        
        # Python entry points
        for pattern in ["main.py", "app.py", "manage.py", "__main__.py", "wsgi.py", "asgi.py"]:
            for path in self.root_dir.rglob(pattern):
                if not self._should_exclude(path):
                    entry_points.append({
                        "file": str(path.relative_to(self.root_dir)),
                        "type": "Python entry",
                        "language": "Python",
                    })
        
        return entry_points
    
    def _find_important_files(self) -> List[Dict]:
        """Find important configuration and documentation files."""
        important = []
        
        for filename in self.IMPORTANT_FILES:
            # Check root directory
            path = self.root_dir / filename
            if path.exists():
                important.append({
                    "file": filename,
                    "purpose": self._get_file_purpose(filename),
                })
        
        return important
    
    def _get_file_purpose(self, filename: str) -> str:
        """Get purpose description for important files."""
        purposes = {
            "main.go": "Go application entry point",
            "main.py": "Python application entry point",
            "index.ts": "TypeScript entry point",
            "index.tsx": "React application entry",
            "package.json": "Node.js dependencies and scripts",
            "go.mod": "Go module definition",
            "requirements.txt": "Python dependencies",
            "pyproject.toml": "Python project configuration",
            "Dockerfile": "Docker container definition",
            "docker-compose.yml": "Multi-container Docker setup",
            "docker-compose.yaml": "Multi-container Docker setup",
            "README.md": "Project documentation",
            "CHANGELOG.md": "Version history",
            ".env.example": "Environment variables template",
        }
        return purposes.get(filename, "Configuration file")
    
    def _identify_modules(self) -> List[Dict]:
        """Identify logical modules/packages in the codebase."""
        modules = []
        
        # Check common module patterns
        module_dirs = [
            "features",
            "modules", 
            "packages",
            "apps",
            "services",
            "src/features",
            "src/modules",
            "internal",
            "pkg",
            "lib",
        ]
        
        for module_dir in module_dirs:
            dir_path = self.root_dir / module_dir
            if dir_path.exists() and dir_path.is_dir():
                for child in dir_path.iterdir():
                    if child.is_dir() and not self._should_exclude(child):
                        # Count files in module
                        file_count = sum(1 for _ in child.rglob("*") if _.is_file() and not self._should_exclude(_))
                        modules.append({
                            "name": child.name,
                            "path": str(child.relative_to(self.root_dir)),
                            "file_count": file_count,
                            "type": module_dir.split("/")[-1],
                        })
        
        return modules
    
    def _analyze_directories(self) -> Dict:
        """Analyze purpose of directories."""
        directories = {}
        
        # Known directory purposes
        known_purposes = {
            "src": "Source code",
            "lib": "Library code",
            "pkg": "Public packages",
            "internal": "Internal packages",
            "cmd": "Command line applications",
            "features": "Feature modules",
            "modules": "Application modules",
            "models": "Data models",
            "services": "Business logic services",
            "repositories": "Data access layer",
            "controllers": "HTTP controllers",
            "handlers": "Request handlers",
            "routers": "Route definitions",
            "routes": "Route definitions",
            "middleware": "HTTP middleware",
            "utils": "Utility functions",
            "helpers": "Helper functions",
            "shared": "Shared code",
            "common": "Common code",
            "config": "Configuration",
            "configs": "Configuration files",
            "types": "Type definitions",
            "interfaces": "Interface definitions",
            "dto": "Data transfer objects",
            "entities": "Domain entities",
            "domain": "Domain layer",
            "application": "Application layer",
            "infrastructure": "Infrastructure layer",
            "presentation": "Presentation layer",
            "api": "API layer",
            "web": "Web layer",
            "components": "UI components",
            "pages": "Page components",
            "views": "View components",
            "hooks": "React hooks",
            "store": "State management",
            "stores": "State stores",
            "state": "Application state",
            "actions": "State actions",
            "reducers": "State reducers",
            "selectors": "State selectors",
            "tests": "Test files",
            "test": "Test files",
            "__tests__": "Test files",
            "specs": "Test specifications",
            "fixtures": "Test fixtures",
            "mocks": "Mock implementations",
            "docs": "Documentation",
            "documentation": "Documentation",
            "assets": "Static assets",
            "public": "Public static files",
            "static": "Static files",
            "scripts": "Utility scripts",
            "tools": "Development tools",
            "migrations": "Database migrations",
            "seeds": "Database seeds",
            "schemas": "Data schemas",
        }
        
        for path in self.root_dir.iterdir():
            if path.is_dir() and not self._should_exclude(path):
                name = path.name.lower()
                file_count = sum(1 for _ in path.rglob("*") if _.is_file() and not self._should_exclude(_))
                
                directories[path.name] = {
                    "path": str(path.relative_to(self.root_dir)),
                    "purpose": known_purposes.get(name, "Unknown"),
                    "file_count": file_count,
                }
        
        return directories


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze codebase structure")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Tree depth")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    analyzer = StructureAnalyzer(Path.cwd(), [], args.depth, args.verbose)
    result = analyzer.analyze()
    
    if args.output:
        output_path = Path(args.output) / "structure.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Saved to {output_path}")
    else:
        print(json.dumps(result, indent=2, default=str))
