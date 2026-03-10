#!/usr/bin/env python3
"""
validate_null_safety.py

Checks Java code for null safety issues:
- Methods returning null instead of Optional<T>
- Missing @NonNull/@Nullable annotations
- Potential NPE from direct dereference
- Optional<T> used incorrectly

Usage:
    python validate_null_safety.py <path> [--json]
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


class NullSafetyValidator:
    """Validates Java code for null safety issues."""

    def __init__(self):
        self.result = ValidationResult()

        # Patterns for null safety issues
        self.patterns = {
            "NULL_RETURN": re.compile(r'\breturn\s+null\s*;'),
            "DIRECT_DEREFERENCE": re.compile(r'(\w+)\.get\(\)\.'),  # Optional.get() without isPresent()
            "OPTIONAL_OF_NULLABLE": re.compile(r'Optional\.ofNullable\(.*\)'),  # Should use Optional.of() when non-null
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

            self._check_null_returns(file_path, content)
            self._check_optional_usage(file_path, content)
            self._check_method_signatures(file_path, content)
            self._check_nullable_annotations(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_null_returns(self, file_path: str, content: str) -> None:
        """Check for methods returning null directly."""
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            match = self.patterns["NULL_RETURN"].search(line)
            if match:
                # Skip test files and certain patterns
                if any(x in line.lower() for x in ["// null", "/* null", "* null", "default", "fallback"]):
                    continue

                self.result.add_issue(Issue(
                    level="WARNING",
                    category="NULL_RETURN",
                    file=file_path,
                    line=line_num,
                    message="Returning null directly. Consider using Optional<T> instead.",
                    code_snippet=line.strip()[:80]
                ))

    def _check_optional_usage(self, file_path: str, content: str) -> None:
        """Check for incorrect Optional usage."""
        lines = content.splitlines()

        # Check for .get() without isPresent() check (NPE risk)
        get_pattern = re.compile(r'(\w+)\.get\(\)')
        for line_num, line in enumerate(lines, 1):
            if '.get()' in line:
                # Check if there's an isPresent() or orElse() on same line or before
                if 'isPresent()' not in line and 'orElse' not in line and 'orElseGet' not in line and 'orElseThrow' not in line:
                    # Check previous line too
                    prev_line = lines[line_num - 2] if line_num > 1 else ""
                    if 'isPresent()' not in prev_line and 'if (' not in prev_line:
                        self.result.add_issue(Issue(
                            level="ERROR",
                            category="UNSAFE_GET",
                            file=file_path,
                            line=line_num,
                            message="Unsafe .get() call without isPresent() check. Use orElse()/orElseGet() instead.",
                            code_snippet=line.strip()[:80]
                        ))

        # Check for Optional.ofNullable() with non-null values
        for line_num, line in enumerate(lines, 1):
            if 'Optional.ofNullable(' in line:
                # If it's obviously non-null, warn
                if any(x in line for x in ['UUID.randomUUID()', 'LocalDateTime.now()', 'new ', 'valueOf(']):
                    self.result.add_issue(Issue(
                        level="INFO",
                        category="OPTIONAL_OF_NULLABLE",
                        file=file_path,
                        line=line_num,
                        message="Using Optional.ofNullable() with obviously non-null value. Use Optional.of() instead.",
                        code_snippet=line.strip()[:80]
                    ))

        # Check for Optional.get() in chains
        for match in re.finditer(r'(\w+)\.get\(\)\.', content):
            line_num = content[:match.start()].count('\n') + 1
            self.result.add_issue(Issue(
                level="ERROR",
                category="UNSAFE_DEREFERENCE",
                file=file_path,
                line=line_num,
                message="Chaining .get() without null check. Use .map()/.flatMap() instead.",
                code_snippet=match.group(0)[:50]
            ))

    def _check_method_signatures(self, file_path: str, content: str) -> None:
        """Check method signatures for Optional usage."""
        # Pattern for method declarations
        method_pattern = re.compile(
            r'(?:public|protected|private|static)\s+'
            r'(?:<[^>]+>\s+)?'
            r'([\w<>\[\], ]+)\s+'  # Return type
            r'(\w+)\s*'  # Method name
            r'\([^)]*\)\s*'
            r'(?:throws\s+[\w\s,]+)?',
            re.MULTILINE
        )

        matches = method_pattern.finditer(content)

        for match in matches:
            return_type = match.group(1).strip()
            method_name = match.group(2)

            # Skip common getters and test methods
            if method_name.startswith(('get', 'is', 'has', 'test')):
                continue

            # Methods that might return null should use Optional
            if 'Repository' in file_path or 'Service' in file_path:
                # Check if method name suggests it returns something that might be absent
                if any(keyword in method_name for keyword in ['find', 'get', 'query', 'fetch', 'search']):
                    # If it returns a type directly (not Optional, not List, not void)
                    if (return_type not in ['void', 'Void', 'int', 'long', 'boolean', 'double', 'float'] and
                        not return_type.startswith('List') and
                        not return_type.startswith('Set') and
                        not return_type.startswith('Collection') and
                        not return_type.startswith('Optional<') and
                        not return_type.startswith('Stream<')):
                        self.result.add_issue(Issue(
                            level="WARNING",
                            category="MISSING_OPTIONAL_RETURN",
                            file=file_path,
                            line=content[:match.start()].count('\n') + 1,
                            message=f"Method '{method_name}' returns {return_type}. Consider using Optional<{return_type}> for null safety.",
                            code_snippet=f"{return_type} {method_name}(...)"
                        ))

    def _check_nullable_annotations(self, file_path: str, content: str) -> None:
        """Check for @NonNull/@Nullable annotation usage."""
        lines = content.splitlines()

        # Check method parameters without nullability annotations
        method_pattern = re.compile(r'\(([^)]*)\)')

        for line_num, line in enumerate(lines, 1):
            if 'public' in line or 'private' in line or 'protected' in line:
                # Check for method declarations
                if '(' in line and ')' in line:
                    params_match = method_pattern.search(line)
                    if params_match:
                        params = params_match.group(1)
                        # If there are parameters but no @NonNull/@Nullable
                        if params.strip() and params.strip() != '':
                            if '@NonNull' not in line and '@Nullable' not in line:
                                # Only warn for Service/Repository layers
                                if 'Service' in file_path or 'Repository' in file_path:
                                    self.result.add_issue(Issue(
                                        level="INFO",
                                        category="MISSING_NULLABILITY_ANNOTATION",
                                        file=file_path,
                                        line=line_num,
                                        message="Method parameters missing @NonNull/@Nullable annotations.",
                                        code_snippet=line.strip()[:80]
                                    ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("NULL SAFETY VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"🔴 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"❌ ERROR: {result.get_count_by_level('ERROR')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")
    print(f"ℹ️  INFO: {result.get_count_by_level('INFO')}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        # Group by category
        issues_by_category: Dict[str, List[Issue]] = {}
        for issue in result.issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)

        for category, issues in sorted(issues_by_category.items()):
            level = issues[0].level
            emoji = "🔴" if level == "CRITICAL" else "❌" if level == "ERROR" else "⚠️" if level == "WARNING" else "ℹ️"
            print(f"\n{emoji} {category} ({len(issues)} occurrences):")

            for issue in issues[:5]:
                print(f"  {issue.file}:{issue.line}")
                if issue.code_snippet:
                    print(f"     {issue.code_snippet[:70]}")

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")
    else:
        print("\n✅ No null safety issues found!")

    print("\n" + "-" * 80)
    print("NULL SAFETY GUIDELINES:")
    print("  ✅ Use Optional<T> for return values that might be absent")
    print("  ✅ Use .orElse(), .orElseGet(), .orElseThrow() instead of .get()")
    print("  ✅ Add @NonNull/@Nullable annotations to parameters")
    print("  ✅ Avoid returning null directly")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for null safety issues"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = NullSafetyValidator()
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
