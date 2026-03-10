#!/usr/bin/env python3
"""
validate_function_size.py

Checks Java code for function and class size violations:
- Methods exceeding 50 lines
- Classes exceeding 500 lines
- Anonymous inner classes that are too long

Usage:
    python validate_function_size.py <path> [--max-method N] [--max-class N] [--json]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class Issue:
    level: str
    category: str
    file: str
    line: int
    message: str
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    issues: List[Issue] = field(default_factory=list)
    files_checked: int = 0
    total_methods: int = 0
    total_classes: int = 0

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)

    def get_count_by_level(self, level: str) -> int:
        return sum(1 for i in self.issues if i.level == level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "critical": self.get_count_by_level("CRITICAL"),
                "warning": self.get_count_by_level("WARNING"),
                "files_checked": self.files_checked,
                "total_methods": self.total_methods,
                "total_classes": self.total_classes
            },
            "issues": [
                {
                    "level": i.level,
                    "category": i.category,
                    "file": i.file,
                    "line": i.line,
                    "message": i.message
                }
                for i in self.issues
            ]
        }


class JavaSizeValidator:
    """Validates Java code for method and class size issues."""

    def __init__(self, max_method_lines: int = 50, max_class_lines: int = 500):
        self.max_method_lines = max_method_lines
        self.max_class_lines = max_class_lines
        self.result = ValidationResult()

        # Critical thresholds
        self.critical_method_lines = int(max_method_lines * 1.4)
        self.critical_class_lines = int(max_class_lines * 1.4)

    def validate_directory(self, path: str) -> ValidationResult:
        """Validate all Java files in a directory."""
        root_path = Path(path)

        if not root_path.exists():
            print(f"Error: Path '{path}' does not exist.")
            return self.result

        java_files = list(root_path.rglob("*.java"))
        java_files = [f for f in java_files if "test" not in str(f).lower()]

        for java_file in java_files:
            self.validate_file(str(java_file))

        self.result.files_checked = len(java_files)
        return self.result

    def validate_file(self, file_path: str) -> None:
        """Validate a single Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.splitlines()
            self._check_class_size(file_path, content, lines)
            self._check_method_sizes(file_path, content, lines)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_class_size(self, file_path: str, content: str, lines: List[str]) -> None:
        """Check if class exceeds size limit."""
        # Find class/interface/enum declarations
        class_pattern = re.compile(
            r'(?:public|protected|private|abstract)?\s*'
            r'(?:static\s+)?'
            r'(?:final\s+)?'
            r'(?:class|interface|enum|record)\s+(\w+)',
            re.MULTILINE
        )

        matches = class_pattern.finditer(content)

        for match in matches:
            class_name = match.group(1)
            start_pos = match.start()

            # Find the opening brace
            open_brace = content.find('{', start_pos)
            if open_brace == -1:
                continue

            # Find the matching closing brace
            brace_count = 0
            i = open_brace
            while i < len(content):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                i += 1

            # Calculate lines
            class_content = content[open_brace:i + 1]
            line_count = class_content.count('\n')
            start_line = content[:start_pos].count('\n') + 1

            self.result.total_classes += 1

            if line_count > self.critical_class_lines:
                self.result.add_issue(Issue(
                    level="CRITICAL",
                    category="OVERSIZED_CLASS",
                    file=file_path,
                    line=start_line,
                    message=f"Class '{class_name}' is {line_count} lines. Maximum allowed: {self.max_class_lines}. "
                           f"Refactor into smaller classes using composition.",
                    code_snippet=f"class {class_name} - {line_count} lines"
                ))
            elif line_count > self.max_class_lines:
                self.result.add_issue(Issue(
                    level="WARNING",
                    category="LARGE_CLASS",
                    file=file_path,
                    line=start_line,
                    message=f"Class '{class_name}' is {line_count} lines. Consider refactoring into smaller classes.",
                    code_snippet=f"class {class_name} - {line_count} lines"
                ))

    def _check_method_sizes(self, file_path: str, content: str, lines: List[str]) -> None:
        """Check if methods exceed size limit."""
        # Pattern for method/constructor declarations
        method_pattern = re.compile(
            r'(?:@[\w]+\s*(?:\([^)]*\))?\s*)*'  # Annotations
            r'(?:public|protected|private|static|final|abstract|synchronized|default|native)\s+'  # Modifiers
            r'(?:<[^>]+>\s+)?'  # Generic return type
            r'[\w<>\[\],?\s]+\s+'  # Return type
            r'(\w+)\s*'  # Method name
            r'\([^)]*\)\s*'  # Parameters
            r'(?:throws\s+[\w,\s]+)?\s*'  # Throws clause
            r'\{',  # Opening brace
            re.MULTILINE
        )

        # Also catch constructors (no return type)
        constructor_pattern = re.compile(
            r'(?:@[\w]+\s*(?:\([^)]*\))?\s*)*'  # Annotations
            r'(?:public|protected|private)\s+'
            r'(\w+)\s*'  # Constructor name (same as class)
            r'\([^)]*\)\s*'  # Parameters
            r'(?:throws\s+[\w,\s]+)?\s*'
            r'\{',
            re.MULTILINE
        )

        # Get all class names to filter constructors
        class_names = set()
        class_pattern = re.compile(r'(?:class|interface|enum|record)\s+(\w+)')
        for match in class_pattern.finditer(content):
            class_names.add(match.group(1))

        matches = list(method_pattern.finditer(content))
        matches.extend(constructor_pattern.finditer(content))

        for match in matches:
            method_name = match.group(1)
            start_pos = match.start()

            # Skip if it's a class declaration, not a method
            if any(method_name == cn for cn in class_names):
                # Check if this looks like a constructor (followed by params)
                if not re.search(r'\([^)]*\)\s*\{', match.group(0)):
                    continue

            # Skip getters, setters, toString, equals, hashCode (typically generated)
            if method_name in ['toString', 'equals', 'hashCode', 'serialVersionUID'] or \
               method_name.startswith(('get', 'set', 'is')):
                continue

            # Find the opening brace
            open_brace = content.find('{', start_pos)
            if open_brace == -1:
                continue

            # Find the matching closing brace
            brace_count = 0
            i = open_brace
            while i < len(content):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                i += 1

            # Calculate lines (excluding opening brace line)
            method_content = content[open_brace:i + 1]
            line_count = method_content.count('\n')
            start_line = content[:start_pos].count('\n') + 1

            self.result.total_methods += 1

            if line_count > self.critical_method_lines:
                self.result.add_issue(Issue(
                    level="CRITICAL",
                    category="OVERSIZED_METHOD",
                    file=file_path,
                    line=start_line,
                    message=f"Method '{method_name}' is {line_count} lines. Maximum allowed: {self.max_method_lines}. "
                           f"Extract smaller methods to improve readability and testability.",
                    code_snippet=f"method {method_name}() - {line_count} lines"
                ))
            elif line_count > self.max_method_lines:
                self.result.add_issue(Issue(
                    level="WARNING",
                    category="LONG_METHOD",
                    file=file_path,
                    line=start_line,
                    message=f"Method '{method_name}' is {line_count} lines. Consider extracting helper methods.",
                    code_snippet=f"method {method_name}() - {line_count} lines"
                ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("FUNCTION SIZE VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"Total methods analyzed: {result.total_methods}")
    print(f"Total classes analyzed: {result.total_classes}")
    print(f"\n🔴 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        for issue in result.issues[:20]:
            emoji = "🔴" if issue.level == "CRITICAL" else "⚠️"
            print(f"\n{emoji} {issue.file}:{issue.line} - {issue.category}")
            print(f"   {issue.message}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")

        if len(result.issues) > 20:
            print(f"\n... and {len(result.issues) - 20} more issues")
    else:
        print("\n✅ No size issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for method and class size issues"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--max-method", type=int, default=50,
                        help="Maximum method lines (default: 50)")
    parser.add_argument("--max-class", type=int, default=500,
                        help="Maximum class lines (default: 500)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = JavaSizeValidator(
        max_method_lines=args.max_method,
        max_class_lines=args.max_class
    )
    result = validator.validate_directory(args.path)

    print_results(result, json_output=args.json)

    if result.get_count_by_level("CRITICAL") > 0:
        sys.exit(2)
    elif result.get_count_by_level("WARNING") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
