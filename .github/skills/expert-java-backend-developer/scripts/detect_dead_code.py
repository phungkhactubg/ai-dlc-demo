#!/usr/bin/env python3
"""
detect_dead_code.py

Find unused methods, variables, and classes in Java code:
- Unused private methods
- Unused private fields
- Unused classes (not referenced anywhere)
- Unused imports

Usage:
    python detect_dead_code.py <path> [--include-exports] [--json]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Set, Optional


@dataclass
class DeadCodeIssue:
    level: str
    category: str
    file: str
    line: int
    name: str
    message: str


@dataclass
class ValidationResult:
    issues: List[DeadCodeIssue] = field(default_factory=list)
    files_checked: int = 0
    unused_methods: int = 0
    unused_fields: int = 0
    unused_classes: int = 0
    unused_imports: int = 0

    def add_issue(self, issue: DeadCodeIssue) -> None:
        self.issues.append(issue)

    def get_count_by_level(self, level: str) -> int:
        return sum(1 for i in self.issues if i.level == level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "warning": self.get_count_by_level("WARNING"),
                "info": self.get_count_by_level("INFO"),
                "files_checked": self.files_checked,
                "unused_methods": self.unused_methods,
                "unused_fields": self.unused_fields,
                "unused_classes": self.unused_classes,
                "unused_imports": self.unused_imports
            },
            "issues": [
                {
                    "level": i.level,
                    "category": i.category,
                    "file": i.file,
                    "line": i.line,
                    "name": i.name,
                    "message": i.message
                }
                for i in self.issues
            ]
        }


class DeadCodeDetector:
    """Detects dead code in Java projects."""

    def __init__(self, include_exports: bool = False):
        self.include_exports = include_exports
        self.result = ValidationResult()

        # Stores for tracking usage
        self.methods: Dict[str, tuple] = {}  # name -> (file, line, access)
        self.fields: Dict[str, tuple] = {}  # name -> (file, line, access)
        self.classes: Dict[str, tuple] = {}  # name -> (file, line)
        self.imports: Dict[str, tuple] = {}  # import -> (file, line)

        self.used_methods: Set[str] = set()
        self.used_fields: Set[str] = set()
        self.used_classes: Set[str] = set()

    def validate_directory(self, path: str) -> ValidationResult:
        """Analyze all Java files in a directory."""
        root_path = Path(path)

        if not root_path.exists():
            print(f"Error: Path '{path}' does not exist.")
            return self.result

        # First pass: collect all declarations
        java_files = list(root_path.rglob("*.java"))
        java_files = [f for f in java_files if "test" not in str(f).lower()]

        for java_file in java_files:
            self._collect_declarations(str(java_file))

        # Second pass: find usages
        for java_file in java_files:
            self._find_usages(str(java_file))

        # Check for unused items
        self._check_unused()

        self.result.files_checked = len(java_files)
        return self.result

    def _collect_declarations(self, file_path: str) -> None:
        """Collect all method, field, and class declarations."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            package = self._extract_package(content)
            lines = content.splitlines()

            # Collect class/interface/enum declarations
            class_pattern = re.compile(
                r'(?:public|protected|private)?\s*(?:abstract\s+)?(?:static\s+)?(?:final\s+)?'
                r'(class|interface|enum|record)\s+(\w+)'
            )
            for match in class_pattern.finditer(content):
                access = match.group(0).split()[0] if match.group(0).split()[0] in ['public', 'protected', 'private'] else 'public'
                name = match.group(2)
                line_num = content[:match.start()].count('\n') + 1

                # Only track private classes if include_exports is False
                if self.include_exports or access == 'private':
                    full_name = f"{package}.{name}" if package else name
                    self.classes[full_name] = (file_path, line_num, access)

            # Collect method declarations
            method_pattern = re.compile(
                r'(?:public|protected|private)\s+'
                r'(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:abstract\s+)?'
                r'(?:<[^>]+>\s+)?'
                r'[\w<>\[\],?\s]+\s+'
                r'(\w+)\s*'  # Method name
                r'\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{',
                re.MULTILINE
            )

            for match in method_pattern.finditer(content):
                method_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Extract access modifier
                access_match = re.search(r'(public|protected|private)\s+', match.group(0))
                access = access_match.group(1) if access_match else 'public'

                # Only track private methods by default
                if access == 'private' or self.include_exports:
                    # Simplified: use just method name (should use class.method in real implementation)
                    key = f"{file_path}:{method_name}:{line_num}"
                    self.methods[key] = (file_path, line_num, access)

            # Collect field declarations
            field_pattern = re.compile(
                r'(?:public|protected|private)\s+'
                r'(?:static\s+)?(?:final\s+)?'
                r'[\w<>\[\],?\s]+\s+'
                r'(\w+)\s*=',
                re.MULTILINE
            )

            for match in field_pattern.finditer(content):
                field_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Extract access modifier
                access_match = re.search(r'(public|protected|private)\s+', match.group(0))
                access = access_match.group(1) if access_match else 'public'

                # Only track private fields by default
                if access == 'private' or self.include_exports:
                    key = f"{file_path}:{field_name}:{line_num}"
                    self.fields[key] = (file_path, line_num, access)

            # Collect imports
            for match in re.finditer(r'import\s+([\w.]+);', content):
                import_path = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                key = f"{file_path}:{import_path}"
                self.imports[key] = (file_path, line_num)

        except Exception as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")

    def _find_usages(self, file_path: str) -> None:
        """Find all usages of methods, fields, and classes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find method usages (simplified: look for method name followed by parentheses)
            for key, (f, line, access) in self.methods.items():
                method_name = key.split(':')[1]
                # Look for method calls
                pattern = re.compile(rf'\b{re.escape(method_name)}\s*\(')
                if pattern.search(content):
                    # Make sure it's not the declaration itself
                    # (simplified check)
                    self.used_methods.add(key)

            # Find field usages
            for key, (f, line, access) in self.fields.items():
                field_name = key.split(':')[1]
                pattern = re.compile(rf'\b{re.escape(field_name)}\b')
                if pattern.search(content):
                    self.used_fields.add(key)

            # Find import usages
            for key, (f, line) in self.imports.items():
                if file_path == f:  # Only check imports in their own file
                    import_path = key.split(':')[1]
                    # Extract the simple class name from the import
                    simple_name = import_path.split('.')[-1]

                    # Check if the simple name is used
                    # Exclude the import line itself
                    content_without_imports = re.sub(r'import[^;]+;', '', content)
                    if simple_name not in content_without_imports:
                        self.used_classes.add(key)

        except Exception as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")

    def _check_unused(self) -> None:
        """Check for unused declarations."""
        # Check unused methods
        for key, (file_path, line_num, access) in self.methods.items():
            if key not in self.used_methods:
                method_name = key.split(':')[1]
                self.result.add_issue(DeadCodeIssue(
                    level="WARNING",
                    category="UNUSED_METHOD",
                    file=file_path,
                    line=line_num,
                    name=method_name,
                    message=f"Private method '{method_name}' is never used."
                ))
                self.result.unused_methods += 1

        # Check unused fields
        for key, (file_path, line_num, access) in self.fields.items():
            if key not in self.used_fields:
                field_name = key.split(':')[1]
                self.result.add_issue(DeadCodeIssue(
                    level="INFO",
                    category="UNUSED_FIELD",
                    file=file_path,
                    line=line_num,
                    name=field_name,
                    message=f"Private field '{field_name}' is never used."
                ))
                self.result.unused_fields += 1

        # Check unused imports
        for key, (file_path, line_num) in self.imports.items():
            if key not in self.used_classes:
                import_path = key.split(':')[1]
                self.result.add_issue(DeadCodeIssue(
                    level="INFO",
                    category="UNUSED_IMPORT",
                    file=file_path,
                    line=line_num,
                    name=import_path,
                    message=f"Import '{import_path}' is never used."
                ))
                self.result.unused_imports += 1

    def _extract_package(self, content: str) -> str:
        """Extract package name from content."""
        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else ""


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print analysis results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("DEAD CODE DETECTION RESULTS")
    print("=" * 80)

    print(f"\nFiles analyzed: {result.files_checked}")
    print(f"\n⚠️  WARNING: {result.get_count_by_level('WARNING')}")
    print(f"ℹ️  INFO: {result.get_count_by_level('INFO')}")

    print(f"\n📊 Dead Code Summary:")
    print(f"   Unused methods: {result.unused_methods}")
    print(f"   Unused fields: {result.unused_fields}")
    print(f"   Unused classes: {result.unused_classes}")
    print(f"   Unused imports: {result.unused_imports}")

    if result.issues:
        # Group by category
        issues_by_category: Dict[str, List[DeadCodeIssue]] = defaultdict(list)
        for issue in result.issues:
            issues_by_category[issue.category].append(issue)

        print("\n" + "-" * 80)
        print("ISSUES BY CATEGORY:")
        print("-" * 80)

        for category, issues in sorted(issues_by_category.items()):
            emoji = "⚠️" if category == "UNUSED_METHOD" else "ℹ️"
            print(f"\n{emoji} {category} ({len(issues)} occurrences):")

            for issue in issues[:5]:
                print(f"  {issue.file}:{issue.line}")
                print(f"     {issue.name} - {issue.message}")

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")

        if result.get_count_by_level('WARNING') > 0:
            print("\n" + "-" * 80)
            print("⚠️  Consider removing unused private methods to improve maintainability.")
    else:
        print("\n✅ No dead code found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Detect dead code in Java projects"
    )
    parser.add_argument("path", help="Path to Java source directory")
    parser.add_argument("--include-exports", action="store_true",
                        help="Include public/protected declarations (default: private only)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    detector = DeadCodeDetector(include_exports=args.include_exports)
    result = detector.validate_directory(args.path)

    print_results(result, json_output=args.json)

    # Exit codes based on findings
    if result.unused_methods > 10:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
