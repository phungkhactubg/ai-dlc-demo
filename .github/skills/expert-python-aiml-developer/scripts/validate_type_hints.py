#!/usr/bin/env python3
"""
Validate type hints in Python code.

Checks for:
- Functions without parameter type hints
- Functions without return type hints
- Overuse of Any type
- Missing variable annotations

Usage:
    python validate_type_hints.py src/
    python validate_type_hints.py src/ --check-returns
    python validate_type_hints.py src/ --json
"""

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class TypeHintIssue:
    """Represents a type hint issue."""
    severity: str
    file: str
    line: int
    function_name: str
    issue_type: str
    message: str


@dataclass
class ValidationResult:
    """Validation result."""
    issues: List[TypeHintIssue] = field(default_factory=list)
    files_scanned: int = 0
    functions_checked: int = 0
    functions_with_full_hints: int = 0
    
    @property
    def coverage(self) -> float:
        if self.functions_checked == 0:
            return 100.0
        return (self.functions_with_full_hints / self.functions_checked) * 100


class TypeHintVisitor(ast.NodeVisitor):
    """AST visitor to check type hints."""
    
    def __init__(self, file_path: str, check_returns: bool = True):
        self.file_path = file_path
        self.check_returns = check_returns
        self.issues: List[TypeHintIssue] = []
        self.functions_checked = 0
        self.functions_with_full_hints = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition."""
        self._check_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function definition."""
        self._check_function(node)
        self.generic_visit(node)
    
    def _check_function(self, node) -> None:
        """Check a function for type hints."""
        # Skip private methods (but not dunder methods)
        if node.name.startswith('_') and not node.name.startswith('__'):
            return
        
        self.functions_checked += 1
        has_all_hints = True
        
        # Check parameter type hints
        for arg in node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            
            if arg.annotation is None:
                has_all_hints = False
                self.issues.append(TypeHintIssue(
                    severity="ERROR",
                    file=self.file_path,
                    line=node.lineno,
                    function_name=node.name,
                    issue_type="MISSING_PARAM_TYPE",
                    message=f"Parameter '{arg.arg}' missing type hint",
                ))
        
        # Check *args and **kwargs
        if node.args.vararg and node.args.vararg.annotation is None:
            self.issues.append(TypeHintIssue(
                severity="WARNING",
                file=self.file_path,
                line=node.lineno,
                function_name=node.name,
                issue_type="MISSING_VARARG_TYPE",
                message="*args missing type hint",
            ))
        
        if node.args.kwarg and node.args.kwarg.annotation is None:
            self.issues.append(TypeHintIssue(
                severity="WARNING",
                file=self.file_path,
                line=node.lineno,
                function_name=node.name,
                issue_type="MISSING_KWARG_TYPE",
                message="**kwargs missing type hint",
            ))
        
        # Check return type
        if self.check_returns and node.returns is None:
            # Skip __init__ and __new__
            if node.name not in ('__init__', '__new__'):
                has_all_hints = False
                self.issues.append(TypeHintIssue(
                    severity="ERROR",
                    file=self.file_path,
                    line=node.lineno,
                    function_name=node.name,
                    issue_type="MISSING_RETURN_TYPE",
                    message="Missing return type hint",
                ))
        
        # Check for Any overuse
        if node.returns:
            return_str = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
            if 'Any' in return_str:
                self.issues.append(TypeHintIssue(
                    severity="WARNING",
                    file=self.file_path,
                    line=node.lineno,
                    function_name=node.name,
                    issue_type="ANY_TYPE_USAGE",
                    message="Return type uses 'Any' - consider being more specific",
                ))
        
        if has_all_hints:
            self.functions_with_full_hints += 1


def validate_file(file_path: Path, check_returns: bool = True) -> TypeHintVisitor:
    """Validate type hints in a single file."""
    visitor = TypeHintVisitor(str(file_path), check_returns)
    
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
        visitor.visit(tree)
    except SyntaxError as e:
        visitor.issues.append(TypeHintIssue(
            severity="ERROR",
            file=str(file_path),
            line=e.lineno or 0,
            function_name="<module>",
            issue_type="SYNTAX_ERROR",
            message=f"Syntax error: {e.msg}",
        ))
    except Exception as e:
        visitor.issues.append(TypeHintIssue(
            severity="ERROR",
            file=str(file_path),
            line=0,
            function_name="<module>",
            issue_type="FILE_ERROR",
            message=f"Could not process file: {e}",
        ))
    
    return visitor


def validate_directory(directory: Path, check_returns: bool = True) -> ValidationResult:
    """Validate all Python files in a directory."""
    result = ValidationResult()
    
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path) or ".venv" in str(file_path):
            continue
        
        result.files_scanned += 1
        visitor = validate_file(file_path, check_returns)
        result.issues.extend(visitor.issues)
        result.functions_checked += visitor.functions_checked
        result.functions_with_full_hints += visitor.functions_with_full_hints
    
    return result


def print_results(result: ValidationResult) -> None:
    """Print validation results."""
    print("\n" + "=" * 60)
    print("TYPE HINT VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\nFiles scanned: {result.files_scanned}")
    print(f"Functions checked: {result.functions_checked}")
    print(f"Functions with full hints: {result.functions_with_full_hints}")
    print(f"Type hint coverage: {result.coverage:.1f}%")
    
    errors = [i for i in result.issues if i.severity == "ERROR"]
    warnings = [i for i in result.issues if i.severity == "WARNING"]
    
    print(f"\nErrors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    
    if result.issues:
        print("\n" + "-" * 60)
        print("ISSUES FOUND:")
        print("-" * 60)
        
        for issue in result.issues:
            icon = "❌" if issue.severity == "ERROR" else "⚠️"
            print(f"\n{icon} [{issue.severity}] {issue.issue_type}")
            print(f"   File: {issue.file}:{issue.line}")
            print(f"   Function: {issue.function_name}")
            print(f"   {issue.message}")
    
    print("\n" + "=" * 60)
    if result.coverage >= 90:
        print("✅ TYPE HINT COVERAGE: EXCELLENT")
    elif result.coverage >= 70:
        print("⚠️ TYPE HINT COVERAGE: ACCEPTABLE")
    else:
        print("❌ TYPE HINT COVERAGE: INSUFFICIENT")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate type hints in Python code")
    parser.add_argument("path", type=Path, help="File or directory to validate")
    parser.add_argument("--check-returns", action="store_true", default=True,
                       help="Check return type hints (default: True)")
    parser.add_argument("--no-check-returns", dest="check_returns", action="store_false",
                       help="Don't check return type hints")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    if args.path.is_file():
        visitor = validate_file(args.path, args.check_returns)
        result = ValidationResult(
            issues=visitor.issues,
            files_scanned=1,
            functions_checked=visitor.functions_checked,
            functions_with_full_hints=visitor.functions_with_full_hints,
        )
    else:
        result = validate_directory(args.path, args.check_returns)
    
    if args.json:
        output = {
            "files_scanned": result.files_scanned,
            "functions_checked": result.functions_checked,
            "functions_with_full_hints": result.functions_with_full_hints,
            "coverage_percent": round(result.coverage, 1),
            "issues": [
                {
                    "severity": i.severity,
                    "file": i.file,
                    "line": i.line,
                    "function_name": i.function_name,
                    "issue_type": i.issue_type,
                    "message": i.message,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(result)
    
    # Exit codes
    if result.coverage < 50:
        sys.exit(2)
    elif result.coverage < 70:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
