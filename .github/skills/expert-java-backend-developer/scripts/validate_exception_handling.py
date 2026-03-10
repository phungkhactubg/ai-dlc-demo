#!/usr/bin/env python3
"""
validate_exception_handling.py

Checks Java code for exception handling issues:
- Empty catch blocks
- Catching generic Exception without rethrowing
- Throwing generic Exception
- Missing custom exceptions

Usage:
    python validate_exception_handling.py <path> [--strict] [--json]
"""

import argparse
import json
import os
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


class JavaExceptionValidator:
    """Validates Java code for exception handling issues."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.result = ValidationResult()

        self.patterns = {
            "EMPTY_CATCH": re.compile(r'}\s*catch\s*\(([^)]+)\)\s*\{\s*\}', re.MULTILINE),
            "CATCH_GENERIC": re.compile(r'catch\s*\(\s*Exception\s+\w+\s*\)', re.MULTILINE),
            "CATCH_RUNTIME": re.compile(r'catch\s*\(\s*RuntimeException\s+\w+\s*\)', re.MULTILINE),
        }

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

            self._check_empty_catch_blocks(file_path, content)
            self._check_generic_catch(file_path, content)
            self._check_exception_throwing(file_path, content)
            self._check_custom_exceptions(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_empty_catch_blocks(self, file_path: str, content: str) -> None:
        """Check for empty catch blocks."""
        matches = self.patterns["EMPTY_CATCH"].finditer(content)
        lines = content.splitlines()

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            self.result.add_issue(Issue(
                level="CRITICAL",
                category="EMPTY_CATCH",
                file=file_path,
                line=line_num,
                message="Empty catch block. All exceptions must be logged or rethrown.",
                code_snippet=line_content.strip()[:80]
            ))

    def _check_generic_catch(self, file_path: str, content: str) -> None:
        """Check for catching generic Exception without proper handling."""
        # Find all catch blocks
        catch_pattern = re.compile(r'catch\s*\(([^)]+)\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.MULTILINE | re.DOTALL)

        matches = catch_pattern.finditer(content)
        lines = content.splitlines()

        for match in matches:
            exception_type = match.group(1).strip()
            catch_body = match.group(2)

            # Check if catching Exception or RuntimeException
            if "Exception" in exception_type or "RuntimeException" in exception_type:
                # Check if there's logging or rethrowing
                has_log = bool(re.search(r'\.(?:error|warn|info|debug|trace)\s*\(', catch_body))
                has_rethrow = bool(re.search(r'throw\s+', catch_body))

                if not has_log and not has_rethrow:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    self.result.add_issue(Issue(
                        level="CRITICAL",
                        category="GENERIC_CATCH_NO_HANDLING",
                        file=file_path,
                        line=line_num,
                        message=f"Catching generic '{exception_type}' without logging or rethrowing.",
                        code_snippet=line_content.strip()[:80]
                    ))

    def _check_exception_throwing(self, file_path: str, content: str) -> None:
        """Check for throwing generic Exception."""
        # Check method signatures with throws Exception
        throws_pattern = re.compile(r'(public|protected|private)[^(]*throws\s+Exception[^a-zA-Z]')

        matches = throws_pattern.finditer(content)
        lines = content.splitlines()

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            self.result.add_issue(Issue(
                level="ERROR",
                category="THROWS_GENERIC",
                file=file_path,
                line=line_num,
                message="Method throws generic 'Exception'. Use specific custom exceptions.",
                code_snippet=line_content.strip()[:80]
            ))

        # Check throw new Exception()
        throw_pattern = re.compile(r'throw\s+new\s+Exception\s*\(')

        matches = throw_pattern.finditer(content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            self.result.add_issue(Issue(
                level="ERROR",
                category="THROW_GENERIC_EXCEPTION",
                file=file_path,
                line=line_num,
                message="Throwing generic 'Exception'. Use specific custom exceptions.",
                code_snippet=line_content.strip()[:80]
            ))

    def _check_custom_exceptions(self, file_path: str, content: str) -> None:
        """Check if custom exceptions are defined for the feature."""
        # Just check if the file has proper exception handling patterns
        if "exception" in file_path.lower():
            # This is an exception file, check if it extends Exception properly
            if "extends RuntimeException" not in content and "extends Exception" not in content:
                line_num = 1
                self.result.add_issue(Issue(
                    level="WARNING",
                    category="CUSTOM_EXCEPTION_PATTERN",
                    file=file_path,
                    line=line_num,
                    message="Custom exception should extend RuntimeException (for unchecked) or Exception (for checked).",
                    code_snippet="File content"
                ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("EXCEPTION HANDLING VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"🚨 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"❌ ERROR: {result.get_count_by_level('ERROR')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        for issue in result.issues[:20]:  # Show first 20
            emoji = "🚨" if issue.level == "CRITICAL" else "❌" if issue.level == "ERROR" else "⚠️"
            print(f"\n{emoji} {issue.file}:{issue.line} - {issue.category}")
            print(f"   {issue.message}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")

        if len(result.issues) > 20:
            print(f"\n... and {len(result.issues) - 20} more issues")
    else:
        print("\n✅ No exception handling issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for exception handling issues"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = JavaExceptionValidator(strict=args.strict)
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
