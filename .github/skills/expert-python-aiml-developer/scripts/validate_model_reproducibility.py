#!/usr/bin/env python3
"""
Validate ML code for reproducibility best practices.

Checks for:
- Random seed setting
- Deterministic operations
- Environment logging
- Version tracking

Usage:
    python validate_model_reproducibility.py src/
    python validate_model_reproducibility.py src/ --strict
    python validate_model_reproducibility.py src/ --json
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class ReproducibilityIssue:
    """Represents a reproducibility issue."""
    severity: str
    category: str
    file: str
    line: int
    message: str
    recommendation: str


@dataclass
class ReproducibilityResult:
    """Reproducibility validation result."""
    issues: List[ReproducibilityIssue] = field(default_factory=list)
    files_scanned: int = 0
    seeds_found: Set[str] = field(default_factory=set)
    has_seed_function: bool = False
    has_environment_logging: bool = False
    
    @property
    def passed(self) -> bool:
        critical = sum(1 for i in self.issues if i.severity == "CRITICAL")
        return critical == 0


class ReproducibilityVisitor(ast.NodeVisitor):
    """AST visitor for reproducibility checks."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues: List[ReproducibilityIssue] = []
        self.seeds_found: Set[str] = set()
        self.has_seed_function = False
        self.has_environment_logging = False
        self.in_function = False
        self.current_function = ""
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions."""
        old_in_function = self.in_function
        old_function = self.current_function
        self.in_function = True
        self.current_function = node.name
        
        # Check if this is a seed setting function
        if 'seed' in node.name.lower():
            self.has_seed_function = True
        
        if 'log_environment' in node.name.lower():
            self.has_environment_logging = True
        
        self.generic_visit(node)
        
        self.in_function = old_in_function
        self.current_function = old_function
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for seed setting."""
        func_name = self._get_func_name(node.func)
        
        # Track seed setting calls
        seed_patterns = [
            'random.seed',
            'np.random.seed',
            'numpy.random.seed',
            'torch.manual_seed',
            'torch.cuda.manual_seed',
            'torch.cuda.manual_seed_all',
            'tf.random.set_seed',
            'tensorflow.random.set_seed',
        ]
        
        for pattern in seed_patterns:
            if func_name.endswith(pattern.split('.')[-1]) or func_name == pattern:
                self.seeds_found.add(pattern)
        
        # Check for non-deterministic operations
        if func_name in ('torch.backends.cudnn.benchmark',):
            # This is usually set as an attribute, not a call
            pass
        
        # Check for shuffle without seed
        if func_name in ('random.shuffle', 'np.random.shuffle'):
            self.issues.append(ReproducibilityIssue(
                severity="WARNING",
                category="NON_DETERMINISTIC",
                file=self.file_path,
                line=node.lineno,
                message=f"{func_name}() may cause non-reproducible results",
                recommendation="Ensure random seed is set before calling shuffle.",
            ))
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Check assignments for reproducibility settings."""
        for target in node.targets:
            target_name = self._get_attr_name(target)
            
            # Check cudnn settings
            if 'cudnn.benchmark' in target_name:
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    self.issues.append(ReproducibilityIssue(
                        severity="WARNING",
                        category="NON_DETERMINISTIC",
                        file=self.file_path,
                        line=node.lineno,
                        message="cudnn.benchmark=True may cause non-deterministic behavior",
                        recommendation="Set torch.backends.cudnn.benchmark=False for reproducibility.",
                    ))
            
            if 'cudnn.deterministic' in target_name:
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    self.seeds_found.add('cudnn.deterministic')
        
        self.generic_visit(node)
    
    def _get_func_name(self, node) -> str:
        """Get full function name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parent = self._get_func_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""
    
    def _get_attr_name(self, node) -> str:
        """Get full attribute name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parent = self._get_attr_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""


def validate_file(file_path: Path) -> ReproducibilityVisitor:
    """Validate reproducibility in a single file."""
    visitor = ReproducibilityVisitor(str(file_path))
    
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
        visitor.visit(tree)
    except SyntaxError:
        pass
    except Exception as e:
        visitor.issues.append(ReproducibilityIssue(
            severity="WARNING",
            category="FILE_ERROR",
            file=str(file_path),
            line=0,
            message=f"Could not process file: {e}",
            recommendation="Check file for syntax errors.",
        ))
    
    return visitor


def validate_directory(directory: Path) -> ReproducibilityResult:
    """Validate all Python files in a directory."""
    result = ReproducibilityResult()
    
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path) or ".venv" in str(file_path):
            continue
        
        result.files_scanned += 1
        visitor = validate_file(file_path)
        result.issues.extend(visitor.issues)
        result.seeds_found.update(visitor.seeds_found)
        if visitor.has_seed_function:
            result.has_seed_function = True
        if visitor.has_environment_logging:
            result.has_environment_logging = True
    
    # Check for missing seed implementations
    if result.files_scanned > 5:  # Only for non-trivial projects
        if not result.has_seed_function:
            result.issues.insert(0, ReproducibilityIssue(
                severity="WARNING",
                category="MISSING_SEED_FUNCTION",
                file="<project>",
                line=0,
                message="No dedicated seed setting function found",
                recommendation="Create a set_seed() function to centralize reproducibility settings.",
            ))
        
        if not result.has_environment_logging:
            result.issues.insert(0, ReproducibilityIssue(
                severity="WARNING",
                category="MISSING_ENV_LOGGING",
                file="<project>",
                line=0,
                message="No environment logging function found",
                recommendation="Create a log_environment() function to track versions for reproducibility.",
            ))
        
        required_seeds = {'random.seed', 'np.random.seed', 'torch.manual_seed'}
        missing_seeds = required_seeds - result.seeds_found
        if missing_seeds and ('torch' in str(result.seeds_found) or 'np' in str(result.seeds_found)):
            result.issues.insert(0, ReproducibilityIssue(
                severity="CRITICAL",
                category="INCOMPLETE_SEED",
                file="<project>",
                line=0,
                message=f"Incomplete seed setting - missing: {missing_seeds}",
                recommendation="Set seeds for all random sources: random, numpy, torch, etc.",
            ))
    
    return result


def print_results(result: ReproducibilityResult) -> None:
    """Print validation results."""
    print("\n" + "=" * 60)
    print("🔄 REPRODUCIBILITY VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\nFiles scanned: {result.files_scanned}")
    print(f"Seed functions found: {len(result.seeds_found)}")
    print(f"Has seed function: {'✅' if result.has_seed_function else '❌'}")
    print(f"Has environment logging: {'✅' if result.has_environment_logging else '❌'}")
    
    if result.seeds_found:
        print(f"\nSeeds detected:")
        for seed in sorted(result.seeds_found):
            print(f"  ✅ {seed}")
    
    if result.issues:
        print("\n" + "-" * 60)
        print("ISSUES FOUND:")
        print("-" * 60)
        
        for issue in result.issues:
            icon = "🚨" if issue.severity == "CRITICAL" else "⚠️"
            print(f"\n{icon} [{issue.severity}] {issue.category}")
            print(f"   File: {issue.file}:{issue.line}")
            print(f"   Issue: {issue.message}")
            print(f"   Fix: {issue.recommendation}")
    
    print("\n" + "=" * 60)
    if result.passed:
        print("✅ REPRODUCIBILITY CHECK PASSED")
    else:
        print("❌ REPRODUCIBILITY CHECK FAILED")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate ML code reproducibility")
    parser.add_argument("path", type=Path, help="Directory to validate")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    result = validate_directory(args.path)
    
    if args.json:
        output = {
            "files_scanned": result.files_scanned,
            "seeds_found": list(result.seeds_found),
            "has_seed_function": result.has_seed_function,
            "has_environment_logging": result.has_environment_logging,
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
    
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
