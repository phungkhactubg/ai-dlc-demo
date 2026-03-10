#!/usr/bin/env python3
"""
API Extractor - Extracts API endpoints and interfaces from codebase.
"""

import json
import re
from pathlib import Path
from typing import Dict, List

class APIExtractor:
    """Extracts API definitions from codebase."""
    
    def __init__(self, root_dir: Path, excludes: List[str], verbose: bool = False):
        self.root_dir = Path(root_dir)
        self.excludes = excludes
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(f"   [api] {message}")
    
    def extract(self, project_info: Dict) -> Dict:
        """Extract all API definitions."""
        result = {"endpoints": [], "interfaces": [], "data_types": []}
        
        languages = project_info.get("languages", [])
        frameworks = project_info.get("frameworks", [])
        
        if "Go" in languages:
            self._extract_go_apis(result, frameworks)
        if "TypeScript" in languages or "JavaScript" in languages:
            self._extract_js_ts_apis(result, frameworks)
        if "Python" in languages:
            self._extract_python_apis(result, frameworks)
        if "Java" in languages:
            self._extract_java_apis(result, frameworks)
        if "C#" in languages:
            self._extract_csharp_apis(result, frameworks)
        
        return result
    
    def _should_exclude(self, path: Path) -> bool:
        path_str = str(path)
        for pattern in self.excludes:
            if pattern in path_str:
                return True
        return False
    
    def _extract_java_apis(self, result: Dict, frameworks: List[str]):
        """Extract Java (Spring) API endpoints."""
        self.log("Extracting Java API endpoints...")
        
        patterns = [
            (re.compile(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'), "Spring"),
        ]
        
        for path in self.root_dir.rglob("*.java"):
            if self._should_exclude(path):
                continue
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                
                for pattern, _Type in patterns:
                    for match in pattern.finditer(content):
                        method = match.group(1).replace("Mapping", "").upper()
                        if method == "REQUEST": method = "ALL"
                        result["endpoints"].append({
                            "method": method,
                            "path": match.group(2),
                            "file": rel_path,
                            "language": "Java",
                        })
            except:
                pass

    def _extract_csharp_apis(self, result: Dict, frameworks: List[str]):
        """Extract C# (ASP.NET) API endpoints."""
        self.log("Extracting C# API endpoints...")
        
        patterns = [
            (re.compile(r'\[(HttpGet|HttpPost|HttpPut|HttpDelete|Route)\s*\(\s*["\']([^"\']+)["\']\s*\)\]'), "ASP.NET"),
        ]
        
        for path in self.root_dir.rglob("*.cs"):
            if self._should_exclude(path):
                continue
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                
                for pattern, _Type in patterns:
                    for match in pattern.finditer(content):
                        method = match.group(1).replace("Http", "").upper()
                        if method == "ROUTE": method = "ALL"
                        result["endpoints"].append({
                            "method": method,
                            "path": match.group(2),
                            "file": rel_path,
                            "language": "C#",
                        })
            except:
                pass
    
    def _extract_go_apis(self, result: Dict, frameworks: List[str]):
        """Extract Go HTTP endpoints."""
        self.log("Extracting Go API endpoints...")
        
        patterns = [
            re.compile(r'\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"\s*,\s*(\w+)'),
        ]
        
        for path in self.root_dir.rglob("*.go"):
            if self._should_exclude(path):
                continue
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                
                for pattern in patterns:
                    for match in pattern.finditer(content):
                        result["endpoints"].append({
                            "method": match.group(1),
                            "path": match.group(2),
                            "handler": match.group(3),
                            "file": rel_path,
                        })
                
                # Extract interfaces
                iface = re.compile(r'type\s+(\w+)\s+interface\s*\{([^}]*)\}', re.DOTALL)
                for match in iface.finditer(content):
                    result["interfaces"].append({
                        "name": match.group(1),
                        "file": rel_path,
                        "language": "Go",
                    })
            except:
                pass
    
    def _extract_js_ts_apis(self, result: Dict, frameworks: List[str]):
        """Extract JS/TS API endpoints."""
        self.log("Extracting JavaScript/TypeScript APIs...")
        
        for ext in ["*.ts", "*.tsx", "*.js"]:
            for path in self.root_dir.rglob(ext):
                if self._should_exclude(path):
                    continue
                try:
                    content = path.read_text(encoding="utf-8")
                    rel_path = str(path.relative_to(self.root_dir))
                    
                    # Extract interfaces
                    iface = re.compile(r'(?:export\s+)?interface\s+(\w+)')
                    for match in iface.finditer(content):
                        result["interfaces"].append({
                            "name": match.group(1),
                            "file": rel_path,
                            "language": "TypeScript",
                        })
                except:
                    pass
    
    def _extract_python_apis(self, result: Dict, frameworks: List[str]):
        """Extract Python API endpoints."""
        self.log("Extracting Python APIs...")
        
        patterns = [
            re.compile(r'@\w+\.(get|post|put|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]'),
        ]
        
        for path in self.root_dir.rglob("*.py"):
            if self._should_exclude(path):
                continue
            try:
                content = path.read_text(encoding="utf-8")
                rel_path = str(path.relative_to(self.root_dir))
                
                for pattern in patterns:
                    for match in pattern.finditer(content):
                        result["endpoints"].append({
                            "method": match.group(1).upper(),
                            "path": match.group(2),
                            "file": rel_path,
                        })
            except:
                pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    project_info = {"languages": ["Go", "TypeScript", "Python"], "frameworks": []}
    extractor = APIExtractor(Path.cwd(), [], args.verbose)
    result = extractor.extract(project_info)
    
    if args.output:
        output_path = Path(args.output) / "apis.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))
