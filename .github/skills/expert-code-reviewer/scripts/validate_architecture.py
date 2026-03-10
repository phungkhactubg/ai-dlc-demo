#!/usr/bin/env python3
"""
Unified Architecture Validator
------------------------------
Validates architectural compliance for both Backend (Go) and Frontend (React/TS).
Enforces dependency rules, package naming, and directory structure.

Usage:
    python validate_architecture.py --path <path_to_scan> [--type go|ts|auto]

Examples:
    python validate_architecture.py --path features/iov --type go
    python validate_architecture.py --path apps/frontend/src/workflow --type ts
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

class Violation:
    def __init__(self, file: str, line: int, message: str, severity: str = "ERROR"):
        self.file = file
        self.line = line
        self.message = message
        self.severity = severity

    def __str__(self):
        icon = "🔴" if self.severity == "ERROR" else "🟡"
        return f"{icon} {self.severity}: {self.message}\n   File: {self.file}:{self.line}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "severity": self.severity
        }

class ArchitectureValidator:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.violations: List[Violation] = []

    def add_violation(self, file: Path, line: int, message: str, severity: str = "ERROR"):
        rel_path = file.relative_to(self.root_path) if file.is_relative_to(self.root_path) else file
        self.violations.append(Violation(str(rel_path), line, message, severity))

    def validate_go_package_naming(self, file_path: Path, content: str):
        """
        Rule: Package name must match the feature name (parent of parent usually),
        NOT the subfolder (controllers, services, etc).
        Exception: main, *_test
        """
        # Heuristic: features/<feature>/<layer>/file.go
        parts = file_path.parts
        if "features" not in parts:
            return

        try:
            feat_idx = parts.index("features")
            if feat_idx + 2 >= len(parts): # Inside features/ but not deep enough
                return
            
            feature_name = parts[feat_idx + 1]
            
            # Find package declaration
            match = re.search(r'^package\s+(\w+)', content, re.MULTILINE)
            if not match:
                return
            
            pkg_name = match.group(1)
            
            # proper package name should be the feature name
            # EXCEPT if we are in a 'sub-feature' or strictly separated module
            # But per rules: "Package name is <feature_name>"
            
            if pkg_name != feature_name and pkg_name != "main" and not pkg_name.endswith("_test"):
                # Common mistake: package controllers, package services
                if pkg_name in ["controllers", "services", "repositories", "models", "adapters", "dto"]:
                   self.add_violation(file_path, 1, f"Invalid package naming '{pkg_name}'. Should be '{feature_name}'.")

        except ValueError:
            pass

    def validate_go_layers(self, file_path: Path, content: str):
        """
        Rule:
        - Models depends on nothing (std lib only)
        - Repositories depend on Models (and drivers)
        - Services depend on Repositories, Models
        - Controllers depend on Services, Models
        """
        # Simplified import check
        # We look for imports of other layers within the same feature
        # e.g. in models, importing "features/ipv/services" is bad
        
        parts = file_path.parts
        if "features" not in parts: 
            return
            
        layer = parts[-2] if len(parts) >= 2 else ""
        if layer == "models":
            if re.search(r'features/.*/(services|controllers|repositories)', content):
                self.add_violation(file_path, 0, "Models layer imports upper layers (services/controllers/repos). Circular dependency risk.")
        
        if layer == "repositories":
             if re.search(r'features/.*/(services|controllers)', content):
                self.add_violation(file_path, 0, "Repositories layer imports upper layers (services/controllers). Violation of Dependency Rule.")

    def validate_go_context(self, file_path: Path, content: str):
        """Rule: Don't use context.Background() in controllers/services (except tests)."""
        if str(file_path).endswith("_test.go"):
            return
            
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
             if "context.Background()" in line:
                 # Check if it's in main or init - simple heuristic failure
                 if "func main()" not in content and "func init()" not in content:
                     self.add_violation(file_path, i, "Avoid context.Background() in business logic. Propagate context from request.", "WARNING")

    def validate_ts_layers(self, file_path: Path, content: str):
        """
        Rule:
        - Core depends on NOTHING (external libs ok)
        - Infrastructure depends on Core
        - Shared depends on Core, Hooks
        - Features (UI) depends on everything
        """
        # Heuristic check based on path and imports
        # Path: apps/frontend/src/<feature>/core/...
        
        str_path = str(file_path).replace("\\", "/")
        
        if "/core/" in str_path:
            # Core violating imports
            if re.search(r'from\s+[\'"]\.\./infrastructure', content):
                self.add_violation(file_path, 0, "Core layer imports Infrastructure. Violation of Dependency Rule.")
            if re.search(r'from\s+[\'"]@/.*infrastructure', content):
                self.add_violation(file_path, 0, "Core layer imports Infrastructure (@/). Violation of Dependency Rule.")
                
        if "/shared/components/" in str_path:
             # Component importing service directly
             if re.search(r'infrastructure/services', content):
                 self.add_violation(file_path, 0, "UI Component imports Service directly. Use a Hook.")

    def scan_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.suffix == '.go':
                self.validate_go_package_naming(file_path, content)
                self.validate_go_layers(file_path, content)
                self.validate_go_context(file_path, content)
            
            elif file_path.suffix in ['.ts', '.tsx']:
                self.validate_ts_layers(file_path, content)
                # Any check
                if ": any" in content or "as any" in content:
                     self.add_violation(file_path, 0, "Usage of 'any' type detected.", "ERROR")
                     
        except Exception as e:
            pass # Ignore read errors

    def run(self, json_output: bool = False):
        if not json_output:
            print(f"Scanning {self.root_path}...")
        
        extensions = {'.go', '.ts', '.tsx'}
        
        for path in self.root_path.rglob('*'):
            if path.is_file() and path.suffix in extensions:
                if any(x in str(path) for x in ['node_modules', 'vendor', '.git', 'dist', 'build']):
                    continue
                self.scan_file(path)
                
        if json_output:
            self.report_json()
        else:
            self.report()

    def report_json(self):
        output = {
            "violations": [v.to_dict() for v in self.violations],
            "success": all(v.severity != "ERROR" for v in self.violations)
        }
        print(json.dumps(output, indent=2))
        sys.exit(1 if not output["success"] else 0)

    def report(self):
        print("\n" + "="*60)
        print("ARCHITECTURE VALIDATION REPORT")
        print("="*60)
        
        if not self.violations:
            print("✅ No architectural violations found.")
            sys.exit(0)
            
        # Sort by file
        self.violations.sort(key=lambda x: x.file)
        
        for v in self.violations:
            print(v)
            
        err_count = sum(1 for v in self.violations if v.severity == "ERROR")
        print(f"\nFound {len(self.violations)} violations ({err_count} Errors).")
        
        if err_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to scan")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        if args.json:
            print(json.dumps({"violations": [{"message": f"Path not found: {args.path}", "severity": "ERROR", "file": "", "line": 0}], "success": False}))
            sys.exit(1)
        print(f"Path not found: {args.path}")
        sys.exit(1)
        
    target = Path(args.path).absolute()
    validator = ArchitectureValidator(str(target))
    
    # Standardized Output Path
    report_name = target.name
    if not report_name or report_name == ".":
        report_name = "root"
    
    output_dir = Path("project-documentation/quality-reports") / report_name
    default_json_output = output_dir / "ARCHITECTURE_VALIDATION.json"

    if args.json:
        validator.run(json_output=True)
    else:
        # Always save JSON report in addition to printing to stdout
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # We need to capture the results without sys.exit
        validator.run(json_output=False)
        
        output = {
            "violations": [v.to_dict() for v in validator.violations],
            "success": all(v.severity != "ERROR" for v in validator.violations)
        }
        
        with open(default_json_output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ JSON report saved to: {default_json_output}")
        
        if not output["success"]:
            sys.exit(1)

if __name__ == "__main__":
    main()
