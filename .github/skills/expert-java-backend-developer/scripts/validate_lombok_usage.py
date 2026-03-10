#!/usr/bin/env python3
"""
validate_lombok_usage.py

Checks Java code for Lombok annotation best practices:
- Field injection with @Autowired (use @RequiredArgsConstructor)
- @Getter/@Setter when @Data would suffice
- Missing @RequiredArgsConstructor for constructor injection
- @AllArgsConstructor when @RequiredArgsConstructor is preferred

Usage:
    python validate_lombok_usage.py <path> [--json]
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
                "error": self.get_count_by_level("ERROR"),
                "warning": self.get_count_by_level("WARNING"),
                "info": self.get_count_by_level("INFO"),
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


class LombokValidator:
    """Validates Java code for Lombok annotation best practices."""

    def __init__(self):
        self.result = ValidationResult()

        # Patterns to detect issues
        self.patterns = {
            "FIELD_INJECTION": re.compile(r'@Autowired\s+(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?\w+'),
            "GETTER_SETTER_PAIR": re.compile(r'@Getter.*\n.*@Setter', re.MULTILINE | re.DOTALL),
            "ALL_ARGS_CONSTRUCTOR": re.compile(r'@AllArgsConstructor'),
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

            self._check_field_injection(file_path, content)
            self._check_getter_setter_usage(file_path, content)
            self._check_constructor_usage(file_path, content)
            self._check_value_annotation_usage(file_path, content)
            self._check_builder_usage(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_field_injection(self, file_path: str, content: str) -> None:
        """Check for @Autowired field injection."""
        matches = self.patterns["FIELD_INJECTION"].finditer(content)
        lines = content.splitlines()

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""

            self.result.add_issue(Issue(
                level="ERROR",
                category="FIELD_INJECTION",
                file=file_path,
                line=line_num,
                message="Field injection with @Autowired detected. Use constructor injection with @RequiredArgsConstructor.",
                code_snippet=line_content.strip()[:80]
            ))

    def _check_getter_setter_usage(self, file_path: str, content: str) -> None:
        """Check if @Getter/@Setter are used when @Data would suffice."""
        lines = content.splitlines()

        # Check for both @Getter and @Setter on same class
        has_getter = False
        has_setter = False
        has_data = False
        has_value = False
        class_start_line = 0

        for line_num, line in enumerate(lines, 1):
            if 'class ' in line and ('{' in line or line_num < len(lines) and '{' in lines[line_num]):
                # Reset for new class
                has_getter = False
                has_setter = False
                has_data = False
                has_value = False
                class_start_line = line_num

            if '@Getter' in line:
                has_getter = True
            if '@Setter' in line:
                has_setter = True
            if '@Data' in line:
                has_data = True
            if '@Value' in line:
                has_value = True

            # If class has both @Getter and @Setter but not @Data, warn
            if (has_getter or has_setter) and not (has_data or has_value):
                # Only warn if both are present or if it's near class declaration
                if line_num - class_start_line < 10:
                    if has_getter and has_setter:
                        self.result.add_issue(Issue(
                            level="WARNING",
                            category="REDUNDANT_LOMBOK",
                            file=file_path,
                            line=class_start_line,
                            message="Using both @Getter and @Setter. Consider using @Data for brevity.",
                            code_snippet="class with @Getter and @Setter"
                        ))
                        break

    def _check_constructor_usage(self, file_path: str, content: str) -> None:
        """Check for @AllArgsConstructor when @RequiredArgsConstructor is preferred."""
        # Check if file has final fields (indicates dependencies)
        has_final_fields = bool(re.search(r'private\s+final\s+\w+', content))
        has_all_args = bool(self.patterns["ALL_ARGS_CONSTRUCTOR"].search(content))
        has_required_args = bool(re.search(r'@RequiredArgsConstructor', content))

        if has_final_fields and has_all_args and not has_required_args:
            # Find the line
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if '@AllArgsConstructor' in line:
                    self.result.add_issue(Issue(
                        level="WARNING",
                        category="CONSTRUCTOR_USAGE",
                        file=file_path,
                        line=line_num,
                        message="Using @AllArgsConstructor with final fields. Consider @RequiredArgsConstructor for better immutability.",
                        code_snippet=line.strip()
                    ))
                    break

    def _check_value_annotation_usage(self, file_path: str, content: str) -> None:
        """Check for @Value annotation usage (immutable @Data)."""
        # @Value is good for DTOs, but check if it's used correctly
        has_value = bool(re.search(r'@Value', content))
        has_setter = bool(re.search(r'@Setter', content))

        if has_value and has_setter:
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if '@Value' in line or '@Setter' in line:
                    self.result.add_issue(Issue(
                        level="ERROR",
                        category="CONFLICTING_LOMBOK",
                        file=file_path,
                        line=line_num,
                        message="@Value creates immutable class (no setters). Using @Setter with @Value is contradictory.",
                        code_snippet=line.strip()
                    ))
                    break

    def _check_builder_usage(self, file_path: str, content: str) -> None:
        """Check for @Builder annotation usage patterns."""
        has_builder = bool(re.search(r'@Builder', content))
        has_args = bool(re.search(r'@(?:AllArgsConstructor|RequiredArgsConstructor|NoArgsConstructor)', content))

        # @Builder with @AllArgsConstructor can cause issues
        if has_builder and has_args:
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if '@Builder' in line:
                    self.result.add_issue(Issue(
                        level="WARNING",
                        category="BUILDER_PATTERN",
                        file=file_path,
                        line=line_num,
                        message="@Builder with constructor annotations may cause issues. Use @Builder.Default or @Value.",
                        code_snippet=line.strip()
                    ))
                    break

        # Check for @Builder on @Data classes
        has_data = bool(re.search(r'@Data', content))
        if has_builder and has_data:
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if '@Builder' in line:
                    self.result.add_issue(Issue(
                        level="INFO",
                        category="BUILDER_DATA_COMBO",
                        file=file_path,
                        line=line_num,
                        message="@Builder with @Data requires @Builder.Default for default values or use @Value for immutability.",
                        code_snippet=line.strip()
                    ))
                    break


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("LOMBOK USAGE VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"❌ ERROR: {result.get_count_by_level('ERROR')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")
    print(f"ℹ️  INFO: {result.get_count_by_level('INFO')}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        for issue in result.issues[:20]:
            emoji = "❌" if issue.level == "ERROR" else "⚠️" if issue.level == "WARNING" else "ℹ️"
            print(f"\n{emoji} {issue.file}:{issue.line} - {issue.category}")
            print(f"   {issue.message}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")

        if len(result.issues) > 20:
            print(f"\n... and {len(result.issues) - 20} more issues")
    else:
        print("\n✅ No Lombok usage issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for Lombok annotation best practices"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = LombokValidator()
    result = validator.validate_directory(args.path)

    print_results(result, json_output=args.json)

    if result.get_count_by_level("ERROR") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
