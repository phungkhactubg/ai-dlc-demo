#!/usr/bin/env python3
"""
validate_security.py

Checks Java code for security vulnerabilities:
- SQL Injection: String concatenation in queries
- Hardcoded Secrets: Passwords, API keys, tokens
- Weak Crypto: MD5, SHA1, DES, RC4
- SSRF: User-controlled URLs in HTTP requests
- Command Injection: Runtime.exec with user input

Usage:
    python validate_security.py <path> [--strict] [--json]
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
                "high": self.get_count_by_level("HIGH"),
                "medium": self.get_count_by_level("MEDIUM"),
                "low": self.get_count_by_level("LOW"),
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


class JavaSecurityValidator:
    """Validates Java code for security vulnerabilities."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.result = ValidationResult()

        # Security patterns
        self.patterns = {
            # SQL Injection patterns
            "SQL_INJECTION": [
                re.compile(r'executeQuery\s*\(\s*"[^"]*\+"\s*\)', re.MULTILINE),
                re.compile(r'executeUpdate\s*\(\s*"[^"]*\+"\s*\)', re.MULTILINE),
                re.compile(r'createNativeQuery\s*\(\s*"[^"]*\+"\s*\)', re.MULTILINE),
                re.compile(r'query\s*=\s*"[^"]*"\s*\+\s*\w+', re.MULTILINE),
            ],
            # Hardcoded secrets
            "HARDCODED_PASSWORD": [
                re.compile(r'password\s*=\s*"[^"]{8,}"', re.IGNORECASE),
                re.compile(r'password\s*:\s*"[^"]{8,}"', re.IGNORECASE),
                re.compile(r'secret\s*=\s*"[^"]{16,}"', re.IGNORECASE),
                re.compile(r'api_key\s*=\s*"[^"]{16,}"', re.IGNORECASE),
                re.compile(r'apikey\s*=\s*"[^"]{16,}"', re.IGNORECASE),
            ],
            # Weak crypto
            "WEAK_CRYPTO": [
                re.compile(r'MessageDigest\s*\.+getInstance\s*\(\s*["\']MD5["\']', re.IGNORECASE),
                re.compile(r'MessageDigest\s*\.+getInstance\s*\(\s*["\']SHA1["\']', re.IGNORECASE),
                re.compile(r'MessageDigest\s*\.+getInstance\s*\(\s*["\']SHA-1["\']', re.IGNORECASE),
                re.compile(r'Cipher\s*\.+getInstance\s*\(\s*["\']DES/', re.IGNORECASE),
                re.compile(r'Cipher\s*\.+getInstance\s*\(\s*["\']RC4', re.IGNORECASE),
            ],
            # Command injection
            "COMMAND_INJECTION": [
                re.compile(r'Runtime\.getRuntime\(\)\.exec\s*\(\s*"[^"]*\+"\s*\)', re.MULTILINE),
                re.compile(r'ProcessBuilder\s*\([^)]*\+\s*\)', re.MULTILINE),
            ],
            # SSRF
            "SSRF": [
                re.compile(r'restTemplate\.(?:getForEntity|exchange|getForObject)\s*\(\s*\w+\s*\+\s*', re.MULTILINE),
                re.compile(r'webClient\.(?:get|post|put|delete)\(\)\.uri\s*\(\s*\w+\s*\+\s*', re.MULTILINE),
                re.compile(r'new\s+URL\s*\(\s*\w+\s*\+\s*', re.MULTILINE),
            ],
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

            self._check_sql_injection(file_path, content)
            self._check_hardcoded_secrets(file_path, content)
            self._check_weak_crypto(file_path, content)
            self._check_command_injection(file_path, content)
            self._check_ssrf(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")

    def _check_sql_injection(self, file_path: str, content: str) -> None:
        """Check for SQL injection vulnerabilities."""
        lines = content.splitlines()

        for category, patterns in self.patterns.items():
            if category == "SQL_INJECTION":
                for pattern in patterns:
                    matches = pattern.finditer(content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                        self.result.add_issue(Issue(
                            level="CRITICAL",
                            category=category,
                            file=file_path,
                            line=line_num,
                            message="SQL injection risk: String concatenation in query. Use parameterized queries.",
                            code_snippet=line_content.strip()[:80]
                        ))

    def _check_hardcoded_secrets(self, file_path: str, content: str) -> None:
        """Check for hardcoded secrets."""
        lines = content.splitlines()

        # Skip test files and config files (they might have example values)
        if any(x in file_path.lower() for x in ["test", "config", "application", "properties"]):
            return

        for category, patterns in self.patterns.items():
            if category == "HARDCODED_PASSWORD":
                for pattern in patterns:
                    matches = pattern.finditer(content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                        self.result.add_issue(Issue(
                            level="CRITICAL",
                            category=category,
                            file=file_path,
                            line=line_num,
                            message="Hardcoded secret detected. Use environment variables or secure vault.",
                            code_snippet=line_content.strip()[:80]
                        ))

    def _check_weak_crypto(self, file_path: str, content: str) -> None:
        """Check for weak cryptographic algorithms."""
        lines = content.splitlines()

        for category, patterns in self.patterns.items():
            if category == "WEAK_CRYPTO":
                for pattern in patterns:
                    matches = pattern.finditer(content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                        self.result.add_issue(Issue(
                            level="HIGH",
                            category=category,
                            file=file_path,
                            line=line_num,
                            message="Weak cryptographic algorithm detected. Use SHA-256, SHA-3, or bcrypt.",
                            code_snippet=line_content.strip()[:80]
                        ))

    def _check_command_injection(self, file_path: str, content: str) -> None:
        """Check for command injection vulnerabilities."""
        lines = content.splitlines()

        for category, patterns in self.patterns.items():
            if category == "COMMAND_INJECTION":
                for pattern in patterns:
                    matches = pattern.finditer(content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                        self.result.add_issue(Issue(
                            level="CRITICAL",
                            category=category,
                            file=file_path,
                            line=line_num,
                            message="Command injection risk: User input in command execution.",
                            code_snippet=line_content.strip()[:80]
                        ))

    def _check_ssrf(self, file_path: str, content: str) -> None:
        """Check for Server-Side Request Forgery vulnerabilities."""
        lines = content.splitlines()

        for category, patterns in self.patterns.items():
            if category == "SSRF":
                for pattern in patterns:
                    matches = pattern.finditer(content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                        self.result.add_issue(Issue(
                            level="HIGH",
                            category=category,
                            file=file_path,
                            line=line_num,
                            message="SSRF risk: User-controlled URL in HTTP request. Validate and whitelist URLs.",
                            code_snippet=line_content.strip()[:80]
                        ))


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print validation results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("SECURITY VALIDATION RESULTS")
    print("=" * 80)

    print(f"\nFiles checked: {result.files_checked}")
    print(f"🔴 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"🟠 HIGH: {result.get_count_by_level('HIGH')}")
    print(f"🟡 MEDIUM: {result.get_count_by_level('MEDIUM')}")
    print(f"🔵 LOW: {result.get_count_by_level('LOW')}")

    if result.issues:
        print("\n" + "-" * 80)
        print("SECURITY ISSUES FOUND:")
        print("-" * 80)

        for issue in result.issues[:20]:
            emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🔵"
            }.get(issue.level, "⚠️")

            print(f"\n{emoji} {issue.file}:{issue.line} - {issue.category}")
            print(f"   {issue.message}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")

        if len(result.issues) > 20:
            print(f"\n... and {len(result.issues) - 20} more issues")
    else:
        print("\n✅ No security issues found!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Java code for security vulnerabilities"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    validator = JavaSecurityValidator(strict=args.strict)
    result = validator.validate_directory(args.path)

    print_results(result, json_output=args.json)

    if result.get_count_by_level("CRITICAL") > 0:
        sys.exit(2)
    elif result.get_count_by_level("HIGH") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
