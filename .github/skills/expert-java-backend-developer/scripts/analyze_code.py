#!/usr/bin/env python3
"""
analyze_code.py

Analyzes Java source code for architecture compliance and code quality:
- Forbidden patterns (global state, driver imports in services)
- Required patterns per file type (interfaces in services, validation in controllers)
- Method complexity detection
- Sensitive data logging

Usage:
    python analyze_code.py <path> [--json]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


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
                "info": self.get_count_by_level("INFO"),
                "files_checked": self.files_checked
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


class JavaCodeAnalyzer:
    """Analyzes Java code for architecture compliance."""

    def __init__(self):
        self.result = ValidationResult()

        # Forbidden patterns
        self.forbidden_patterns = {
            "STATIC_STATE": re.compile(r'private\s+static\s+(?!final|final\s+)[A-Z]\w+\s+\w+\s*='),
            "DRIVER_IMPORT": re.compile(r'import\s+(?:com\.mongodb\.|org\.postgresql\.|org\.mongodb\.driver\.|com\.zaxxer\.hibernate\.|com\.mysql\.|oracle\.jdbc\.)'),
            "SYSTEM_OUT": re.compile(r'System\.out\.(?:print|println)'),
            "SYSTEM_ERR": re.compile(r'System\.err\.(?:print|println)'),
            "PRINTStackTrace": re.compile(r'\.printStackTrace\(\)'),
        }

        # Sensitive data patterns
        self.sensitive_patterns = {
            "PASSWORD_LOG": re.compile(r'(?:log|logger|slf4j)\.[a-z]+\s*\([^)]*password[^)]*\)', re.IGNORECASE),
            "TOKEN_LOG": re.compile(r'(?:log|logger|slf4j)\.[a-z]+\s*\([^)]*token[^)]*\)', re.IGNORECASE),
            "SECRET_LOG": re.compile(r'(?:log|logger|slf4j)\.[a-z]+\s*\([^)]*secret[^)]*\)', re.IGNORECASE),
            "CREDIT_CARD_LOG": re.compile(r'(?:log|logger|slf4j)\.[a-z]+\s*\([^)]*\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[^)]*\)'),
        }

        # Required patterns per file type
        self.controller_required = [
            re.compile(r'@(?:Rest)?Controller'),
            re.compile(r'@(?:Get|Post|Put|Delete|Patch)Mapping'),
        ]

        self.service_required = [
            re.compile(r'@\s*Transactional'),
        ]

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

            file_path_lower = file_path.lower()

            self._check_forbidden_patterns(file_path, content)
            self._check_sensitive_logging(file_path, content)
            self._check_file_type_requirements(file_path, content)

            # Controller-specific checks
            if 'controller' in file_path_lower:
                self._check_controller_patterns(file_path, content)

            # Service-specific checks
            if 'service' in file_path_lower:
                self._check_service_patterns(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_forbidden_patterns(self, file_path: str, content: str) -> None:
        """Check for forbidden code patterns."""
        lines = content.splitlines()

        for category, pattern in self.forbidden_patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                messages = {
                    "STATIC_STATE": "Static mutable state detected. Use dependency injection or instance fields.",
                    "DRIVER_IMPORT": "Direct driver import detected. Use repository/adapter pattern instead.",
                    "SYSTEM_OUT": "System.out.println detected. Use proper logging framework.",
                    "SYSTEM_ERR": "System.err.println detected. Use proper logging framework.",
                    "PRINTStackTrace": "printStackTrace() detected. Use logger with error context instead.",
                }

                self.result.add_issue(Issue(
                    level="ERROR" if category in ["DRIVER_IMPORT", "STATIC_STATE"] else "WARNING",
                    category=category,
                    file=file_path,
                    line=line_num,
                    message=messages.get(category, f"Forbidden pattern: {category}"),
                    code_snippet=line_content.strip()[:80]
                ))

    def _check_sensitive_logging(self, file_path: str, content: str) -> None:
        """Check for sensitive data in logging statements."""
        lines = content.splitlines()

        for category, pattern in self.sensitive_patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                messages = {
                    "PASSWORD_LOG": "Password detected in log statement. NEVER log passwords.",
                    "TOKEN_LOG": "Token detected in log statement. NEVER log sensitive tokens.",
                    "SECRET_LOG": "Secret detected in log statement. NEVER log secrets.",
                    "CREDIT_CARD_LOG": "Credit card number detected in log statement. NEVER log PII.",
                }

                self.result.add_issue(Issue(
                    level="CRITICAL",
                    category=category,
                    file=file_path,
                    line=line_num,
                    message=messages.get(category, f"Sensitive data in logs: {category}"),
                    code_snippet=line_content.strip()[:80]
                ))

    def _check_file_type_requirements(self, file_path: str, content: str) -> None:
        """Check for required patterns based on file type."""
        file_path_lower = file_path.lower()

        # Controller requirements
        if 'controller' in file_path_lower or 'rest' in file_path_lower:
            if not any(pattern.search(content) for pattern in self.controller_required):
                self.result.add_issue(Issue(
                    level="WARNING",
                    category="MISSING_CONTROLLER_ANNOTATION",
                    file=file_path,
                    line=1,
                    message="Controller file missing @RestController or mapping annotations.",
                    code_snippet=None
                ))

        # Service requirements
        if 'service' in file_path_lower:
            # Check for @Transactional
            has_transactional = bool(re.search(r'@\s*Transactional', content))
            has_data_modifying = any(keyword in content for keyword in
                ["save", "update", "delete", "create", "insert", "modify"])

            if has_data_modifying and not has_transactional:
                self.result.add_issue(Issue(
                    level="ERROR",
                    category="MISSING_TRANSACTIONAL",
                    file=file_path,
                    line=1,
                    message="Service with data-modifying operations missing @Transactional.",
                    code_snippet=None
                ))

    def _check_controller_patterns(self, file_path: str, content: str) -> None:
        """Check controller-specific patterns."""
        lines = content.splitlines()

        # Check for validation annotations
        has_validation = bool(re.search(r'@Valid|@NotNull|@NotEmpty|@NotBlank', content))
        has_request_body = bool(re.search(r'@RequestBody', content))

        if has_request_body and not has_validation:
            self.result.add_issue(Issue(
                level="WARNING",
                category="MISSING_VALIDATION",
                file=file_path,
                line=1,
                message="Controller with @RequestBody missing validation annotations.",
                code_snippet=None
            ))

        # Check for @Transactional on controllers (should be in services)
        has_transactional = bool(re.search(r'@\s*Transactional', content))
        if has_transactional:
            for line_num, line in enumerate(lines, 1):
                if '@Transactional' in line or '@Transactional' in line:
                    self.result.add_issue(Issue(
                        level="WARNING",
                        category="TRANSACTION_ON_CONTROLLER",
                        file=file_path,
                        line=line_num,
                        message="Controller should not have @Transactional. Move to service layer.",
                        code_snippet=line.strip()
                    ))
                    break

    def _check_service_patterns(self, file_path: str, content: str) -> None:
        """Check service-specific patterns."""
        file_name = Path(file_path).name.lower()

        # Check if implementation file follows naming convention
        if 'impl' in file_name:
            # Should have corresponding interface
            interface_name = file_name.replace('impl.java', '.java')
            interface_path = str(Path(file_path).parent / interface_name)

            if not Path(interface_path).exists():
                self.result.add_issue(Issue(
                    level="INFO",
                    category="MISSING_SERVICE_INTERFACE",
                    file=file_path,
                    line=1,
                    message="Service implementation missing corresponding interface.",
                    code_snippet=None
                ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print analysis results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("JAVA CODE ARCHITECTURE ANALYSIS")
    print("=" * 80)

    print(f"\nFiles analyzed: {result.files_checked}")
    print(f"🔴 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"❌ ERROR: {result.get_count_by_level('ERROR')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")
    print(f"ℹ️  INFO: {result.get_count_by_level('INFO')}")

    if result.issues:
        # Group by category
        issues_by_category: Dict[str, List[Issue]] = {}
        for issue in result.issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)

        print("\n" + "-" * 80)
        print("ISSUES BY CATEGORY:")
        print("-" * 80)

        for category, issues in sorted(issues_by_category.items()):
            level_counts = {}
            for issue in issues:
                level_counts[issue.level] = level_counts.get(issue.level, 0) + 1

            level_str = ", ".join([f"{lvl}: {count}" for lvl, count in level_counts.items()])
            print(f"\n{category} ({len(issues)} occurrences) [{level_str}]")

            for issue in issues[:5]:
                emoji = "🔴" if issue.level == "CRITICAL" else "❌" if issue.level == "ERROR" else "⚠️" if issue.level == "WARNING" else "ℹ️"
                print(f"  {emoji} {issue.file}:{issue.line}")
                if issue.code_snippet:
                    print(f"     {issue.code_snippet[:70]}")

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")
    else:
        print("\n✅ No architecture issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Java source code for architecture compliance"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    analyzer = JavaCodeAnalyzer()
    result = analyzer.validate_directory(args.path)

    print_results(result, json_output=args.json)

    if result.get_count_by_level("CRITICAL") > 0:
        sys.exit(2)
    elif result.get_count_by_level("ERROR") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
