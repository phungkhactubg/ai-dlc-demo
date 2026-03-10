#!/usr/bin/env python3
"""
Validate that Python code is production-ready.

Checks for:
- TODOs, FIXMEs, placeholders
- Missing type hints
- Missing docstrings
- Hardcoded secrets
- Print statements (should use logging)
- Bare exception handling

Usage:
    python validate_production_ready.py src/
    python validate_production_ready.py src/ --strict
    python validate_production_ready.py src/ --json
"""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Issue severity levels
CRITICAL = "CRITICAL"
ERROR = "ERROR"
WARNING = "WARNING"

# Patterns to detect
TODO_PATTERNS = [
    r"\b(TODO|FIXME|XXX|HACK|BUG)\b",
    r"#\s*(todo|fixme|xxx|hack)\s*:",
]

PLACEHOLDER_PATTERNS = [
    r"placeholder",
    r"will implement",
    r"to be implemented",
    r"not implemented",
    r"implement later",
]

SECRET_PATTERNS = [
    r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
    r'password\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\']sk-[^"\']+["\']',
    r'sk-[a-zA-Z0-9]{20,}',
    r'ghp_[a-zA-Z0-9]{36}',
]


@dataclass
class Issue:
    """Represents a validation issue."""
    severity: str
    category: str
    file: str
    line: int
    message: str
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    """Validation result for a file or directory."""
    issues: List[Issue] = field(default_factory=list)
    files_scanned: int = 0
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == CRITICAL)
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == WARNING)
    
    @property
    def passed(self) -> bool:
        return self.critical_count == 0 and self.error_count == 0


def check_todos_and_placeholders(file_path: Path, content: str) -> List[Issue]:
    """Check for TODOs and placeholder comments."""
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Check TODOs
        for pattern in TODO_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(Issue(
                    severity=CRITICAL,
                    category="TODO",
                    file=str(file_path),
                    line=line_num,
                    message="TODO/FIXME found - must be resolved before production",
                    code_snippet=line.strip()[:100],
                ))
                break
        
        # Check placeholders
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(Issue(
                    severity=CRITICAL,
                    category="PLACEHOLDER",
                    file=str(file_path),
                    line=line_num,
                    message="Placeholder comment found - must be implemented",
                    code_snippet=line.strip()[:100],
                ))
                break
    
    return issues


def check_hardcoded_secrets(file_path: Path, content: str) -> List[Issue]:
    """Check for hardcoded secrets."""
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(Issue(
                    severity=CRITICAL,
                    category="SECURITY",
                    file=str(file_path),
                    line=line_num,
                    message="Potential hardcoded secret detected",
                    code_snippet=line.strip()[:50] + "...",
                ))
                break
    
    return issues


def check_print_statements(file_path: Path, content: str) -> List[Issue]:
    """Check for print statements (should use logging)."""
    issues = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'print':
                issues.append(Issue(
                    severity=ERROR,
                    category="LOGGING",
                    file=str(file_path),
                    line=node.lineno,
                    message="print() used - use logging instead",
                ))
    
    return issues


def check_bare_exceptions(file_path: Path, content: str) -> List[Issue]:
    """Check for bare exception handling."""
    issues = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(Issue(
                    severity=ERROR,
                    category="ERROR_HANDLING",
                    file=str(file_path),
                    line=node.lineno,
                    message="Bare except clause - use specific exceptions",
                ))
    
    return issues


def check_empty_functions(file_path: Path, content: str) -> List[Issue]:
    """Check for empty function bodies (only pass or ...)."""
    issues = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            
            # Remove docstring if present
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, (ast.Str, ast.Constant)):
                body = body[1:]
            
            # Check if only pass or ellipsis
            if len(body) == 1:
                if isinstance(body[0], ast.Pass):
                    issues.append(Issue(
                        severity=CRITICAL,
                        category="EMPTY_FUNCTION",
                        file=str(file_path),
                        line=node.lineno,
                        message=f"Function '{node.name}' has only 'pass' - must be implemented",
                    ))
                elif isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    if body[0].value.value is ...:
                        issues.append(Issue(
                            severity=CRITICAL,
                            category="EMPTY_FUNCTION",
                            file=str(file_path),
                            line=node.lineno,
                            message=f"Function '{node.name}' has only '...' - must be implemented",
                        ))
    
    return issues


def check_missing_type_hints(file_path: Path, content: str) -> List[Issue]:
    """Check for missing type hints on functions."""
    issues = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private/dunder methods
            if node.name.startswith('_') and not node.name.startswith('__'):
                continue
            
            # Check parameters
            for arg in node.args.args:
                if arg.arg != 'self' and arg.arg != 'cls' and arg.annotation is None:
                    issues.append(Issue(
                        severity=ERROR,
                        category="TYPE_HINTS",
                        file=str(file_path),
                        line=node.lineno,
                        message=f"Function '{node.name}' param '{arg.arg}' missing type hint",
                    ))
            
            # Check return type
            if node.returns is None and not node.name.startswith('__'):
                issues.append(Issue(
                    severity=WARNING,
                    category="TYPE_HINTS",
                    file=str(file_path),
                    line=node.lineno,
                    message=f"Function '{node.name}' missing return type hint",
                ))
    
    return issues


def check_missing_docstrings(file_path: Path, content: str) -> List[Issue]:
    """Check for missing docstrings on public functions/classes."""
    issues = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Skip private methods
            if node.name.startswith('_') and not node.name.startswith('__'):
                continue
            
            # Check for docstring
            if not ast.get_docstring(node):
                node_type = "Class" if isinstance(node, ast.ClassDef) else "Function"
                issues.append(Issue(
                    severity=WARNING,
                    category="DOCSTRING",
                    file=str(file_path),
                    line=node.lineno,
                    message=f"{node_type} '{node.name}' missing docstring",
                ))
    
    return issues


def validate_file(file_path: Path, strict: bool = False) -> List[Issue]:
    """Validate a single Python file."""
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        issues.append(Issue(
            severity=ERROR,
            category="FILE_ERROR",
            file=str(file_path),
            line=0,
            message=f"Could not read file: {e}",
        ))
        return issues
    
    # Run all checks
    issues.extend(check_todos_and_placeholders(file_path, content))
    issues.extend(check_hardcoded_secrets(file_path, content))
    issues.extend(check_empty_functions(file_path, content))
    issues.extend(check_bare_exceptions(file_path, content))
    issues.extend(check_print_statements(file_path, content))
    issues.extend(check_missing_type_hints(file_path, content))
    
    if strict:
        issues.extend(check_missing_docstrings(file_path, content))
    
    return issues


def validate_directory(directory: Path, strict: bool = False) -> ValidationResult:
    """Validate all Python files in a directory."""
    result = ValidationResult()
    
    for file_path in directory.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(file_path) or ".venv" in str(file_path):
            continue
        
        result.files_scanned += 1
        result.issues.extend(validate_file(file_path, strict))
    
    return result


def print_results(result: ValidationResult) -> None:
    """Print validation results to console."""
    print("\n" + "=" * 60)
    print("PRODUCTION READINESS VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\nFiles scanned: {result.files_scanned}")
    print(f"Critical: {result.critical_count}")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")
    
    if result.issues:
        print("\n" + "-" * 60)
        print("ISSUES FOUND:")
        print("-" * 60)
        
        for issue in result.issues:
            icon = "🚨" if issue.severity == CRITICAL else "❌" if issue.severity == ERROR else "⚠️"
            print(f"\n{icon} [{issue.severity}] {issue.category}")
            print(f"   File: {issue.file}:{issue.line}")
            print(f"   {issue.message}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")
    
    print("\n" + "=" * 60)
    if result.passed:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Python code for production readiness")
    parser.add_argument("path", type=Path, help="File or directory to validate")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    if args.path.is_file():
        result = ValidationResult(files_scanned=1)
        result.issues = validate_file(args.path, args.strict)
    else:
        result = validate_directory(args.path, args.strict)
    
    # Standardized Output Path
    target_abs = args.path.absolute()
    report_name = target_abs.name
    if not report_name or report_name == ".":
        report_name = "root"
    
    output_dir = Path("project-documentation/quality-reports") / report_name
    default_json_output = output_dir / "PRODUCTION_READY_VALIDATION.json"

    if args.json:
        output = {
            "files_scanned": result.files_scanned,
            "critical_count": result.critical_count,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "passed": result.passed,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "file": i.file,
                    "line": i.line,
                    "message": i.message,
                    "code_snippet": i.code_snippet,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        # Always save JSON report in addition to printing to stdout
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output = {
            "files_scanned": result.files_scanned,
            "critical_count": result.critical_count,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "passed": result.passed,
            "issues": [i.__dict__ for i in result.issues],
        }
        
        with open(default_json_output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ JSON report saved to: {default_json_output}")
        print_results(result)
    
    # Exit codes
    if result.critical_count > 0:
        sys.exit(2)
    elif result.error_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
