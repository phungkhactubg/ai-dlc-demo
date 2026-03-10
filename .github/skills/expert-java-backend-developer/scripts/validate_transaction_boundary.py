#!/usr/bin/env python3
"""
validate_transaction_boundary.py

Checks Java code for @Transactional annotation usage:
- Data-modifying methods without @Transactional
- @Transactional on controllers (should be in services)
- Read operations without readOnly = true

Usage:
    python validate_transaction_boundary.py <path> [--json]
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

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)

    def get_count_by_level(self, level: str) -> int:
        return sum(1 for i in self.issues if i.level == level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "critical": self.get_count_by_level("CRITICAL"),
                "error": self.get_count_by_level("ERROR"),
                "warning": self.get_count_by_level("WARNING"),
                "files_checked": self.files_checked
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


class JavaTransactionValidator:
    """Validates Java code for @Transactional usage."""

    def __init__(self):
        self.result = ValidationResult()

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

            file_name = Path(file_path).name.lower()

            if "controller" in file_name or "rest" in file_name:
                self._check_controller_transaction_usage(file_path, content)
            elif "service" in file_name or "impl" in file_name:
                self._check_service_transaction_usage(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_controller_transaction_usage(self, file_path: str, content: str) -> None:
        """Check for @Transactional on controllers."""
        pattern = re.compile(r'@Transactional', re.MULTILINE)
        matches = pattern.finditer(content)
        lines = content.splitlines()

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            self.result.add_issue(Issue(
                level="WARNING",
                category="TRANSACTION_ON_CONTROLLER",
                file=file_path,
                line=line_num,
                message="Controllers should not have @Transactional. Move to service layer.",
                code_snippet=line_content.strip()[:80]
            ))

    def _check_service_transaction_usage(self, file_path: str, content: str) -> None:
        """Check for proper @Transactional usage in services."""
        # Find all public methods
        method_pattern = re.compile(
            r'(?:@Transactional\s*(?:\([^)]*\))?\s*)?\s*'  # Optional @Transactional
            r'(?:public|protected|private)?\s*'  # Access modifier
            '(?:static|final|synchronized|default)?\s*'  # Modifiers
            r'(?:<[^>]+>)?\s*'  # Generic return type
            r'\w+\s+'  # Return type
            r'(\w+)\s*'  # Method name
            r'\([^)]*\)\s*'  # Parameters
            r'(?:throws\s+[\w\s,]+)?\s*'  # Throws clause
            r'\{',  # Method body start
            re.MULTILINE
        )

        lines = content.splitlines()

        # First, collect all @Transactional line numbers
        transactional_lines = set()
        for line_num, line in enumerate(lines, 1):
            if '@Transactional' in line:
                transactional_lines.add(line_num)

        matches = method_pattern.finditer(content)

        for match in matches:
            method_start = match.start()
            line_num = content[:method_start].count('\n') + 1

            # Check method signature for data-modifying keywords
            method_text = match.group(0)
            method_name = match.group(1) if len(match.groups()) > 0 else ""

            # Skip getters, setters, and common non-data-modifying methods
            if method_name.startswith(("get", "is", "has", "find", "query", "list", "count")):
                continue

            # Check if method is @Transactional
            has_transactional = False
            has_read_only = False

            # Look backward for @Transactional
            for i in range(max(0, line_num - 5), line_num):
                if i - 1 < len(lines) and '@Transactional' in lines[i - 1]:
                    has_transactional = True
                    if 'readOnly' in lines[i - 1] or 'read-only' in lines[i - 1]:
                        has_read_only = True
                    break

            # Check if method modifies data (heuristic)
            modifies_data = any(keyword in method_name for keyword in
                ["create", "save", "update", "delete", "remove", "add", "insert", "modify", "change", "process"])

            if modifies_data and not has_transactional:
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                self.result.add_issue(Issue(
                    level="ERROR",
                    category="MISSING_TRANSACTIONAL",
                    file=file_path,
                    line=line_num,
                    message=f"Method '{method_name}' appears to modify data but lacks @Transactional.",
                    code_snippet=line_content.strip()[:80]
                ))

            # Check if read operation has readOnly = true
            if not modifies_data and has_transactional and not has_read_only:
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                self.result.add_issue(Issue(
                    level="WARNING",
                    category="MISSING_READONLY",
                    file=file_path,
                    line=line_num,
                    message=f"Method '{method_name}' is a read operation. Consider using @Transactional(readOnly = true).",
                    code_snippet=line_content.strip()[:80]
                ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("TRANSACTION BOUNDARY VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"🚨 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"❌ ERROR: {result.get_count_by_level('ERROR')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        for issue in result.issues:
            emoji = "🚨" if issue.level == "CRITICAL" else "❌" if issue.level == "ERROR" else "⚠️"
            print(f"\n{emoji} {issue.file}:{issue.line} - {issue.category}")
            print(f"   {issue.message}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")
    else:
        print("\n✅ No transaction boundary issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for @Transactional usage"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = JavaTransactionValidator()
    result = validator.validate_directory(args.path)

    print_results(result, json_output=args.json)

    if result.get_count_by_level("CRITICAL") > 0:
        sys.exit(2)
    elif result.get_count_by_level("ERROR") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
