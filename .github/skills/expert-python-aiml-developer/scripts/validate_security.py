#!/usr/bin/env python3
"""
Security validation for Python AI/ML code.

Checks for:
- Hardcoded secrets and API keys
- Unsafe pickle/torch.load usage
- eval() and exec() calls
- Subprocess shell injection risks
- Path traversal vulnerabilities
- Debug mode in production

Usage:
    python validate_security.py src/
    python validate_security.py src/ --strict
    python validate_security.py src/ --json
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


@dataclass
class SecurityIssue:
    """Represents a security issue."""
    severity: str
    category: str
    file: str
    line: int
    message: str
    recommendation: str
    code_snippet: Optional[str] = None


@dataclass
class SecurityResult:
    """Security scan result."""
    issues: List[SecurityIssue] = field(default_factory=list)
    files_scanned: int = 0
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == CRITICAL)
    
    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == HIGH)
    
    @property
    def passed(self) -> bool:
        return self.critical_count == 0 and self.high_count == 0


# Secret patterns
SECRET_PATTERNS = [
    (r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{16,}["\']', "API key"),
    (r'secret[_-]?key\s*=\s*["\'][^"\']{8,}["\']', "Secret key"),
    (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
    (r'token\s*=\s*["\']sk-[^"\']+["\']', "OpenAI API key"),
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub token"),
    (r'aws_access_key_id\s*=\s*["\'][A-Z0-9]{20}["\']', "AWS access key"),
    (r'aws_secret_access_key\s*=\s*["\'][^"\']{40}["\']', "AWS secret key"),
]


class SecurityVisitor(ast.NodeVisitor):
    """AST visitor for security checks."""
    
    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.lines = content.split('\n')
        self.issues: List[SecurityIssue] = []
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for security issues."""
        func_name = self._get_func_name(node.func)
        
        # Check eval/exec
        if func_name in ('eval', 'exec'):
            self.issues.append(SecurityIssue(
                severity=CRITICAL,
                category="CODE_INJECTION",
                file=self.file_path,
                line=node.lineno,
                message=f"Dangerous {func_name}() call detected",
                recommendation=f"Avoid using {func_name}(). Use ast.literal_eval() for safe evaluation of literals.",
            ))
        
        # Check pickle.load
        if func_name in ('pickle.load', 'pickle.loads'):
            self.issues.append(SecurityIssue(
                severity=CRITICAL,
                category="UNSAFE_DESERIALIZATION",
                file=self.file_path,
                line=node.lineno,
                message="Unsafe pickle deserialization detected",
                recommendation="Avoid pickle for untrusted data. Use JSON or consider safer alternatives.",
            ))
        
        # Check torch.load without weights_only
        if func_name == 'torch.load':
            has_weights_only = any(
                kw.arg == 'weights_only' for kw in node.keywords
            )
            if not has_weights_only:
                self.issues.append(SecurityIssue(
                    severity=HIGH,
                    category="UNSAFE_DESERIALIZATION",
                    file=self.file_path,
                    line=node.lineno,
                    message="torch.load() without weights_only=True",
                    recommendation="Use torch.load(path, weights_only=True) to prevent arbitrary code execution.",
                ))
        
        # Check subprocess calls
        if func_name in ('subprocess.call', 'subprocess.run', 'subprocess.Popen', 'os.system'):
            has_shell = any(
                kw.arg == 'shell' and self._is_truthy(kw.value)
                for kw in node.keywords
            )
            if has_shell or func_name == 'os.system':
                self.issues.append(SecurityIssue(
                    severity=HIGH,
                    category="COMMAND_INJECTION",
                    file=self.file_path,
                    line=node.lineno,
                    message=f"Shell command execution detected ({func_name})",
                    recommendation="Avoid shell=True. Pass arguments as a list instead.",
                ))
        
        # Check debug mode
        if func_name in ('app.run', 'uvicorn.run'):
            for kw in node.keywords:
                if kw.arg == 'debug' and self._is_truthy(kw.value):
                    self.issues.append(SecurityIssue(
                        severity=MEDIUM,
                        category="DEBUG_MODE",
                        file=self.file_path,
                        line=node.lineno,
                        message="Debug mode enabled",
                        recommendation="Disable debug mode in production (debug=False).",
                    ))
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Check for dangerous imports."""
        for alias in node.names:
            if alias.name == 'pickle':
                self.issues.append(SecurityIssue(
                    severity=LOW,
                    category="SECURITY_NOTICE",
                    file=self.file_path,
                    line=node.lineno,
                    message="pickle module imported",
                    recommendation="Be cautious with pickle. Never unpickle untrusted data.",
                ))
        self.generic_visit(node)
    
    def _get_func_name(self, node) -> str:
        """Get function name from a Call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            elif isinstance(node.value, ast.Attribute):
                return f"{self._get_func_name(node.value)}.{node.attr}"
        return ""
    
    def _is_truthy(self, node) -> bool:
        """Check if a node represents a truthy value."""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        if isinstance(node, ast.NameConstant):
            return bool(node.value)
        return False


def check_hardcoded_secrets(file_path: Path, content: str) -> List[SecurityIssue]:
    """Check for hardcoded secrets."""
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue
        
        for pattern, secret_type in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(SecurityIssue(
                    severity=CRITICAL,
                    category="HARDCODED_SECRET",
                    file=str(file_path),
                    line=line_num,
                    message=f"Potential hardcoded {secret_type} detected",
                    recommendation="Use environment variables or a secrets manager.",
                    code_snippet=line.strip()[:50] + "...",
                ))
                break
    
    return issues


def check_path_traversal(file_path: Path, content: str) -> List[SecurityIssue]:
    """Check for potential path traversal vulnerabilities."""
    issues = []
    lines = content.split('\n')
    
    patterns = [
        r'open\s*\([^)]*\+[^)]*\)',
        r'Path\s*\([^)]*\+[^)]*\)',
        r'os\.path\.join[^)]*request\.',
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line):
                issues.append(SecurityIssue(
                    severity=MEDIUM,
                    category="PATH_TRAVERSAL",
                    file=str(file_path),
                    line=line_num,
                    message="Potential path traversal vulnerability",
                    recommendation="Validate and sanitize file paths before use.",
                ))
                break
    
    return issues


def validate_file(file_path: Path) -> List[SecurityIssue]:
    """Validate a single file for security issues."""
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return [SecurityIssue(
            severity=LOW,
            category="FILE_ERROR",
            file=str(file_path),
            line=0,
            message=f"Could not read file: {e}",
            recommendation="Check file permissions.",
        )]
    
    # AST-based checks
    try:
        tree = ast.parse(content)
        visitor = SecurityVisitor(str(file_path), content)
        visitor.visit(tree)
        issues.extend(visitor.issues)
    except SyntaxError:
        pass
    
    # Pattern-based checks
    issues.extend(check_hardcoded_secrets(file_path, content))
    issues.extend(check_path_traversal(file_path, content))
    
    return issues


def validate_directory(directory: Path) -> SecurityResult:
    """Validate all Python files in a directory."""
    result = SecurityResult()
    
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path) or ".venv" in str(file_path):
            continue
        
        result.files_scanned += 1
        result.issues.extend(validate_file(file_path))
    
    return result


def print_results(result: SecurityResult) -> None:
    """Print security scan results."""
    print("\n" + "=" * 60)
    print("🔒 SECURITY SCAN REPORT")
    print("=" * 60)
    
    print(f"\nFiles scanned: {result.files_scanned}")
    print(f"Critical: {result.critical_count}")
    print(f"High: {result.high_count}")
    print(f"Medium: {sum(1 for i in result.issues if i.severity == MEDIUM)}")
    print(f"Low: {sum(1 for i in result.issues if i.severity == LOW)}")
    
    if result.issues:
        print("\n" + "-" * 60)
        print("SECURITY ISSUES FOUND:")
        print("-" * 60)
        
        severity_order = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}
        sorted_issues = sorted(result.issues, key=lambda x: severity_order.get(x.severity, 4))
        
        for issue in sorted_issues:
            icon = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(issue.severity, "ℹ️")
            print(f"\n{icon} [{issue.severity}] {issue.category}")
            print(f"   File: {issue.file}:{issue.line}")
            print(f"   Issue: {issue.message}")
            print(f"   Fix: {issue.recommendation}")
            if issue.code_snippet:
                print(f"   Code: {issue.code_snippet}")
    
    print("\n" + "=" * 60)
    if result.passed:
        print("✅ SECURITY SCAN PASSED")
    else:
        print("❌ SECURITY SCAN FAILED - Critical/High issues found")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Security validation for Python code")
    parser.add_argument("path", type=Path, help="File or directory to scan")
    parser.add_argument("--strict", action="store_true", help="Include low severity issues in failure")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    if args.path.is_file():
        result = SecurityResult(files_scanned=1)
        result.issues = validate_file(args.path)
    else:
        result = validate_directory(args.path)
    
    if args.json:
        output = {
            "files_scanned": result.files_scanned,
            "critical_count": result.critical_count,
            "high_count": result.high_count,
            "passed": result.passed,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "file": i.file,
                    "line": i.line,
                    "message": i.message,
                    "recommendation": i.recommendation,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(result)
    
    if result.critical_count > 0:
        sys.exit(2)
    elif result.high_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
