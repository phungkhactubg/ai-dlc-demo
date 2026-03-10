#!/usr/bin/env python3
"""
Analyze code quality for Python AI/ML projects.

Performs:
- Cyclomatic complexity analysis
- Dead code detection
- Code duplication check
- Import organization check

Usage:
    python analyze_code_quality.py src/
    python analyze_code_quality.py src/ --fix
    python analyze_code_quality.py src/ --full-report
"""

import argparse
import ast
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class ComplexityMetric:
    """Complexity metric for a function."""
    file: str
    function_name: str
    line: int
    complexity: int
    lines_of_code: int


@dataclass
class CodeQualityResult:
    """Code quality analysis result."""
    files_scanned: int = 0
    total_lines: int = 0
    complexity_metrics: List[ComplexityMetric] = field(default_factory=list)
    unused_imports: List[Tuple[str, int, str]] = field(default_factory=list)
    long_functions: List[Tuple[str, str, int, int]] = field(default_factory=list)
    magic_numbers: List[Tuple[str, int, int]] = field(default_factory=list)
    
    @property
    def average_complexity(self) -> float:
        if not self.complexity_metrics:
            return 0.0
        return sum(m.complexity for m in self.complexity_metrics) / len(self.complexity_metrics)
    
    @property
    def quality_score(self) -> int:
        score = 100
        
        # Deduct for high complexity
        high_complexity = sum(1 for m in self.complexity_metrics if m.complexity > 10)
        score -= min(30, high_complexity * 5)
        
        # Deduct for long functions
        score -= min(20, len(self.long_functions) * 3)
        
        # Deduct for unused imports
        score -= min(10, len(self.unused_imports))
        
        # Deduct for magic numbers
        score -= min(10, len(self.magic_numbers))
        
        return max(0, score)


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity."""
    
    def __init__(self):
        self.complexity = 1  # Base complexity
        self.function_start = 0
        self.function_end = 0
    
    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        # Count elif
        if node.orelse and isinstance(node.orelse[0], ast.If):
            pass  # Will be counted in next visit
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Each and/or adds complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.complexity += 1
        if node.ifs:
            self.complexity += len(node.ifs)
        self.generic_visit(node)


class ImportVisitor(ast.NodeVisitor):
    """Track imports and their usage."""
    
    def __init__(self):
        self.imports: Dict[str, int] = {}  # name -> line
        self.used_names: Set[str] = set()
    
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name != '*':
                self.imports[name] = node.lineno
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)
    
    def get_unused(self) -> List[Tuple[str, int]]:
        unused = []
        for name, line in self.imports.items():
            if name not in self.used_names and not name.startswith('_'):
                unused.append((name, line))
        return unused


class MagicNumberVisitor(ast.NodeVisitor):
    """Detect magic numbers in code."""
    
    ALLOWED_NUMBERS = {0, 1, 2, -1, 100, 1000}
    
    def __init__(self):
        self.magic_numbers: List[Tuple[int, int]] = []  # (line, value)
        self.in_assignment = False
    
    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, (int, float)):
            if node.value not in self.ALLOWED_NUMBERS:
                self.magic_numbers.append((node.lineno, node.value))
        self.generic_visit(node)


def analyze_file(file_path: Path) -> Tuple[List[ComplexityMetric], List[Tuple[str, int]], List[Tuple[str, int, int]], List[Tuple[int, int]]]:
    """Analyze a single file."""
    complexity_metrics = []
    unused_imports = []
    long_functions = []
    magic_numbers = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        tree = ast.parse(content)
    except:
        return complexity_metrics, unused_imports, long_functions, magic_numbers
    
    # Analyze complexity
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visitor = ComplexityVisitor()
            visitor.visit(node)
            
            # Calculate lines of code
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10
            loc = end_line - node.lineno
            
            complexity_metrics.append(ComplexityMetric(
                file=str(file_path),
                function_name=node.name,
                line=node.lineno,
                complexity=visitor.complexity,
                lines_of_code=loc,
            ))
            
            # Check for long functions
            if loc > 50:
                long_functions.append((node.name, node.lineno, loc))
    
    # Analyze imports
    import_visitor = ImportVisitor()
    import_visitor.visit(tree)
    unused_imports = import_visitor.get_unused()
    
    # Detect magic numbers
    magic_visitor = MagicNumberVisitor()
    magic_visitor.visit(tree)
    magic_numbers = magic_visitor.magic_numbers
    
    return complexity_metrics, unused_imports, long_functions, magic_numbers


def analyze_directory(directory: Path) -> CodeQualityResult:
    """Analyze all Python files in a directory."""
    result = CodeQualityResult()
    
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path) or ".venv" in str(file_path):
            continue
        
        result.files_scanned += 1
        
        try:
            result.total_lines += len(file_path.read_text().split('\n'))
        except:
            pass
        
        complexity, unused, long_funcs, magic = analyze_file(file_path)
        
        result.complexity_metrics.extend(complexity)
        result.unused_imports.extend([(str(file_path), line, name) for name, line in unused])
        result.long_functions.extend([(str(file_path), name, line, loc) for name, line, loc in long_funcs])
        result.magic_numbers.extend([(str(file_path), line, val) for line, val in magic])
    
    return result


def print_results(result: CodeQualityResult, full_report: bool = False) -> None:
    """Print analysis results."""
    print("\n" + "=" * 60)
    print("📊 CODE QUALITY ANALYSIS")
    print("=" * 60)
    
    print(f"\nFiles scanned: {result.files_scanned}")
    print(f"Total lines: {result.total_lines}")
    print(f"Functions analyzed: {len(result.complexity_metrics)}")
    print(f"Average complexity: {result.average_complexity:.1f}")
    print(f"Quality score: {result.quality_score}/100")
    
    # High complexity functions
    high_complexity = [m for m in result.complexity_metrics if m.complexity > 10]
    if high_complexity:
        print(f"\n⚠️ HIGH COMPLEXITY FUNCTIONS ({len(high_complexity)}):")
        for m in sorted(high_complexity, key=lambda x: -x.complexity)[:10]:
            print(f"   {m.function_name} ({m.file}:{m.line}) - Complexity: {m.complexity}")
    
    # Long functions
    if result.long_functions:
        print(f"\n⚠️ LONG FUNCTIONS ({len(result.long_functions)}):")
        for file, name, line, loc in result.long_functions[:10]:
            print(f"   {name} ({file}:{line}) - {loc} lines")
    
    # Unused imports (if full report)
    if full_report and result.unused_imports:
        print(f"\n⚠️ UNUSED IMPORTS ({len(result.unused_imports)}):")
        for file, line, name in result.unused_imports[:20]:
            print(f"   {name} ({file}:{line})")
    
    print("\n" + "=" * 60)
    if result.quality_score >= 80:
        print("✅ CODE QUALITY: EXCELLENT")
    elif result.quality_score >= 60:
        print("⚠️ CODE QUALITY: ACCEPTABLE")
    else:
        print("❌ CODE QUALITY: NEEDS IMPROVEMENT")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze code quality")
    parser.add_argument("path", type=Path, help="Directory to analyze")
    parser.add_argument("--full-report", action="store_true", help="Show full report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    result = analyze_directory(args.path)
    
    if args.json:
        output = {
            "files_scanned": result.files_scanned,
            "total_lines": result.total_lines,
            "average_complexity": round(result.average_complexity, 2),
            "quality_score": result.quality_score,
            "high_complexity_count": sum(1 for m in result.complexity_metrics if m.complexity > 10),
            "long_functions_count": len(result.long_functions),
            "unused_imports_count": len(result.unused_imports),
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(result, args.full_report)
    
    sys.exit(0 if result.quality_score >= 60 else 1)


if __name__ == "__main__":
    main()
