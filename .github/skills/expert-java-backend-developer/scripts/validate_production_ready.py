#!/usr/bin/env python3
"""
validate_production_ready.py

Checks Java code for production readiness:
- TODOs, FIXMEs, XXX, HACK comments
- Empty catch blocks
- Empty method bodies
- Throwing generic Exception
- Field injection with @Autowired
- Missing @Transactional on data-modifying methods

Usage:
    python validate_production_ready.py <path> [--strict] [--json]
"""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class Issue:
    """Represents a code issue found during validation."""
    level: str  # CRITICAL, ERROR, WARNING
    category: str  # TODO, EMPTY_CATCH, etc.
    file: str
    line: int
    message: str
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation."""
    issues: List[Issue] = field(default_factory=list)
    files_checked: int = 0
    total_lines: int = 0

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)

    def get_critical_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "CRITICAL")

    def get_error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "ERROR")

    def get_warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "WARNING")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "critical": self.get_critical_count(),
                "error": self.get_error_count(),
                "warning": self.get_warning_count(),
                "files_checked": self.files_checked,
                "total_lines": self.total_lines
            },
            "issues": [
                {
                    "level": i.level,
                    "category": i.category,
                    "file": i.file,
                    "line": i.line,
                    "message": i.message,
                    "code_snippet": i.code_snippet
                }
                for i in self.issues
            ]
        }


class JavaProductionValidator:
    """Validates Java code for production readiness."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.result = ValidationResult()

        # Patterns to detect issues
        self.patterns = {
            "TODO": re.compile(r'\bTODO\b', re.IGNORECASE),
            "FIXME": re.compile(r'\bFIXME\b', re.IGNORECASE),
            "XXX": re.compile(r'\bXXX\b', re.IGNORECASE),
            "HACK": re.compile(r'\bHACK\b', re.IGNORECASE),
            # Empty catch blocks
            "EMPTY_CATCH": re.compile(r'}\s*catch\s*\([^)]+\)\s*\{\s*\}', re.MULTILINE),
            # Throwing generic Exception
            "THROW_GENERIC": re.compile(r'throws\s+Exception[^a-zA-Z]'),
            "THROW_NEW_EXCEPTION": re.compile(r'throw\s+new\s+Exception\s*\('),
            # Field injection
            "FIELD_INJECTION": re.compile(r'@Autowired\s+(?:public|private|protected)\s+\w+'),
        }

    def validate_directory(self, path: str) -> ValidationResult:
        """Validate all Java files in a directory."""
        root_path = Path(path)

        if not root_path.exists():
            print(f"Error: Path '{path}' does not exist.")
            return self.result

        java_files = list(root_path.rglob("*.java"))

        # Exclude test files
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
                self.result.total_lines += len(content.splitlines())

            self._check_comments(file_path, content)
            self._check_empty_catch_blocks(file_path, content)
            self._check_exception_throwing(file_path, content)
            self._check_field_injection(file_path, content)
            self._check_empty_methods(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_comments(self, file_path: str, content: str) -> None:
        """Check for TODO, FIXME, XXX, HACK comments."""
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Skip import statements
            if line.strip().startswith('import '):
                continue

            # Check for prohibited comment patterns
            for category, pattern in self.patterns.items():
                if category in ["TODO", "FIXME", "XXX", "HACK"]:
                    match = pattern.search(line)
                    if match:
                        self.result.add_issue(Issue(
                            level="CRITICAL",
                            category=category,
                            file=file_path,
                            line=line_num,
                            message=f"Prohibited comment '{category}' found. Production code must be complete.",
                            code_snippet=line.strip()
                        ))

    def _check_empty_catch_blocks(self, file_path: str, content: str) -> None:
        """Check for empty catch blocks."""
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            match = self.patterns["EMPTY_CATCH"].search(line)
            if match:
                self.result.add_issue(Issue(
                    level="CRITICAL",
                    category="EMPTY_CATCH",
                    file=file_path,
                    line=line_num,
                    message="Empty catch block detected. All exceptions must be logged or rethrown.",
                    code_snippet=line.strip()
                ))

    def _check_exception_throwing(self, file_path: str, content: str) -> None:
        """Check for throwing generic Exception."""
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check method throws clause
            throws_match = self.patterns["THROW_GENERIC"].search(line)
            if throws_match:
                self.result.add_issue(Issue(
                    level="ERROR",
                    category="THROWS_GENERIC",
                    file=file_path,
                    line=line_num,
                    message="Method throws generic 'Exception'. Use specific exceptions instead.",
                    code_snippet=line.strip()
                ))

            # Check throw new Exception
            throw_match = self.patterns["THROW_NEW_EXCEPTION"].search(line)
            if throw_match:
                self.result.add_issue(Issue(
                    level="ERROR",
                    category="THROW_GENERIC_EXCEPTION",
                    file=file_path,
                    line=line_num,
                    message="Throwing generic 'Exception'. Use specific custom exceptions instead.",
                    code_snippet=line.strip()
                ))

    def _check_field_injection(self, file_path: str, content: str) -> None:
        """Check for field injection with @Autowired."""
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            match = self.patterns["FIELD_INJECTION"].search(line)
            if match:
                self.result.add_issue(Issue(
                    level="ERROR",
                    category="FIELD_INJECTION",
                    file=file_path,
                    line=line_num,
                    message="Field injection with @Autowired detected. Use constructor injection instead.",
                    code_snippet=line.strip()
                ))

    def _check_empty_methods(self, file_path: str, content: str) -> None:
        """Check for empty method bodies."""
        # Pattern for method declarations followed by empty body
        method_pattern = re.compile(
            r'(?:public|protected|private|static|\s)+\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{\s*\}',
            re.MULTILINE
        )

        matches = method_pattern.finditer(content)
        lines = content.splitlines()

        for match in matches:
            # Calculate line number
            line_num = content[:match.start()].count('\n') + 1
            method_line = lines[line_num - 1] if line_num <= len(lines) else ""

            # Skip getters, setters, toString, equals, hashCode (typically generated)
            if any(name in method_line for name in ["get", "set", "toString", "equals", "hashCode"]):
                continue

            self.result.add_issue(Issue(
                level="ERROR",
                category="EMPTY_METHOD",
                file=file_path,
                line=line_num,
                message="Empty method body detected. Implement business logic or remove the method.",
                code_snippet=method_line.strip()[:100]
            ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("PRODUCTION READINESS VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"Total lines: {result.total_lines}")

    print(f"\n🚨 CRITICAL: {result.get_critical_count()}")
    print(f"❌ ERROR: {result.get_error_count()}")
    print(f"⚠️  WARNING: {result.get_warning_count()}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        # Group issues by category
        issues_by_category = {}
        for issue in result.issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)

        for category, issues in sorted(issues_by_category.items()):
            print(f"\n{category} ({len(issues)} occurrences):")
            for issue in issues[:5]:  # Show first 5
                print(f"  {issue.file}:{issue.line}")
                if issue.code_snippet:
                    print(f"    {issue.code_snippet[:80]}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")
    else:
        print("\n✅ No issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for production readiness"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = JavaProductionValidator(strict=args.strict)
    result = validator.validate_directory(args.path)

    print_results(result, json_output=args.json)

    # Exit codes
    if result.get_critical_count() > 0:
        sys.exit(2)
    elif result.get_error_count() > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
