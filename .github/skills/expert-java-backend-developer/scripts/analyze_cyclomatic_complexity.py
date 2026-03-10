#!/usr/bin/env python3
"""
analyze_cyclomatic_complexity.py

Measures cyclomatic complexity to identify overly complex methods.

Cyclomatic complexity is calculated as:
    V(G) = E - N + 2*P
Where:
    E = Number of edges
    N = Number of nodes
    P = Number of connected components

Simplified calculation for Java:
    Complexity = 1 + (number of decision points)

Decision points:
    if, else if, else
    switch cases
    for, while, do-while loops
    catch blocks
    conditional operators (?:)
    logical AND (&&) and logical OR (||)

Usage:
    python analyze_cyclomatic_complexity.py <path> [--threshold N] [--json]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class ComplexityIssue:
    file: str
    method_name: str
    line: int
    complexity: int
    threshold: int


@dataclass
class ValidationResult:
    issues: List[ComplexityIssue] = field(default_factory=list)
    files_checked: int = 0
    methods_analyzed: int = 0
    avg_complexity: float = 0.0

    def add_issue(self, issue: ComplexityIssue) -> None:
        self.issues.append(issue)

    def get_count_by_severity(self, severity: str) -> int:
        if severity == "high":
            return sum(1 for i in self.issues if i.complexity > i.threshold * 1.5)
        elif severity == "medium":
            return sum(1 for i in self.issues if i.complexity > i.threshold)
        return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "high_severity": self.get_count_by_severity("high"),
                "medium_severity": self.get_count_by_severity("medium"),
                "files_checked": self.files_checked,
                "methods_analyzed": self.methods_analyzed,
                "avg_complexity": round(self.avg_complexity, 2)
            },
            "issues": [
                {
                    "file": i.file,
                    "method": i.method_name,
                    "line": i.line,
                    "complexity": i.complexity,
                    "threshold": i.threshold
                }
                for i in self.issues
            ]
        }


class CyclomaticComplexityAnalyzer:
    """Analyzes cyclomatic complexity of Java methods."""

    def __init__(self, threshold: int = 10):
        self.threshold = threshold
        self.result = ValidationResult()

        # Patterns for decision points
        self.decision_patterns = [
            (re.compile(r'\bif\s*\('), 1),
            (re.compile(r'\belse\s+if\s*\('), 1),
            (re.compile(r'\bswitch\s*\('), 1),
            (re.compile(r'\bcase\s+'), 1),
            (re.compile(r'\bfor\s*\('), 1),
            (re.compile(r'\bwhile\s*\('), 1),
            (re.compile(r'\bdo\s*\{'), 1),
            (re.compile(r'\bcatch\s*\('), 1),
            (re.compile(r'\?\s*[^:]+\s*:'), 1),  # Ternary operator
            (re.compile(r'&&'), 1),  # Short-circuit AND
            (re.compile(r'\|\|'), 1),  # Short-circuit OR
        ]

    def validate_directory(self, path: str) -> ValidationResult:
        """Analyze all Java files in a directory."""
        root_path = Path(path)

        if not root_path.exists():
            print(f"Error: Path '{path}' does not exist.")
            return self.result

        java_files = list(root_path.rglob("*.java"))
        java_files = [f for f in java_files if "test" not in str(f).lower()]

        all_complexities = []

        for java_file in java_files:
            file_complexities = self.analyze_file(str(java_file))
            all_complexities.extend(file_complexities)

        self.result.files_checked = len(java_files)
        self.result.methods_analyzed = len(all_complexities)
        self.result.avg_complexity = sum(all_complexities) / len(all_complexities) if all_complexities else 0.0

        return self.result

    def analyze_file(self, file_path: str) -> List[int]:
        """Analyze a single Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self._analyze_methods(file_path, content)

        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")
            return []

    def _analyze_methods(self, file_path: str, content: str) -> List[int]:
        """Analyze all methods in the file."""
        complexities = []

        # Find all methods
        methods = self._extract_methods(content)

        for method_name, method_content, start_line in methods:
            complexity = self._calculate_complexity(method_content)
            complexities.append(complexity)

            if complexity > self.threshold:
                self.result.add_issue(ComplexityIssue(
                    file=file_path,
                    method_name=method_name,
                    line=start_line,
                    complexity=complexity,
                    threshold=self.threshold
                ))

        return complexities

    def _extract_methods(self, content: str) -> List[Tuple[str, str, int]]:
        """Extract all methods from the content."""
        methods = []

        # Pattern for method/constructor declarations
        # This is simplified - real Java parsing would need a proper parser
        method_pattern = re.compile(
            r'(?:@[\w]+\s*(?:\([^)]*\))?\s*)*'  # Annotations
            r'(?:public|protected|private|static|final|abstract|synchronized|default|native)\s+'
            r'(?:<[^>]+>\s+)?'
            r'[\w<>\[\],?\s]+\s+'
            r'(\w+)\s*'  # Method name
            r'\([^)]*\)\s*'
            r'(?:throws\s+[\w\s,]+)?\s*'
            r'\{',
            re.MULTILINE
        )

        # Also catch constructors
        constructor_pattern = re.compile(
            r'(?:@[\w]+\s*(?:\([^)]*\))?\s*)*'
            r'(?:public|protected|private)\s+'
            r'(\w+)\s*'  # Constructor name
            r'\([^)]*\)\s*'
            r'(?:throws\s+[\w\s,]+)?\s*'
            r'\{',
            re.MULTILINE
        )

        # Get class names to filter constructors
        class_names = set()
        class_pattern = re.compile(r'(?:class|interface|enum|record)\s+(\w+)')
        for match in class_pattern.finditer(content):
            class_names.add(match.group(1))

        matches = list(method_pattern.finditer(content))
        matches.extend(constructor_pattern.finditer(content))

        for match in matches:
            method_name = match.group(1)
            start_pos = match.start()

            # Skip if it's a class declaration
            if method_name in class_names:
                continue

            # Skip getters, setters, toString, equals, hashCode
            if method_name in ['toString', 'equals', 'hashCode'] or \
               method_name.startswith(('get', 'set', 'is')):
                continue

            # Find method body
            open_brace = content.find('{', start_pos)
            if open_brace == -1:
                continue

            brace_count = 0
            i = open_brace
            while i < len(content):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                i += 1

            method_content = content[open_brace:i + 1]
            start_line = content[:start_pos].count('\n') + 1

            methods.append((method_name, method_content, start_line))

        return methods

    def _calculate_complexity(self, method_content: str) -> int:
        """Calculate cyclomatic complexity of a method."""
        # Base complexity is 1 (one path through the method)
        complexity = 1

        # Count decision points
        for pattern, weight in self.decision_patterns:
            matches = pattern.findall(method_content)
            complexity += len(matches) * weight

        return int(complexity)


def print_results(result: ValidationResult, json_output: bool = False) -> None:
    """Print analysis results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("CYCLOMATIC COMPLEXITY ANALYSIS")
    print("=" * 80)

    print(f"\nFiles analyzed: {result.files_checked}")
    print(f"Methods analyzed: {result.methods_analyzed}")
    print(f"Average complexity: {result.avg_complexity:.2f}")
    print(f"\n🔴 High severity (> {result.threshold * 1.5:.0f}): {result.get_count_by_severity('high')}")
    print(f"🟡 Medium severity (> {result.threshold}): {result.get_count_by_severity('medium')}")

    if result.issues:
        # Sort by complexity (descending)
        sorted_issues = sorted(result.issues, key=lambda x: x.complexity, reverse=True)

        print("\n" + "-" * 80)
        print("COMPLEX METHODS:")
        print("-" * 80)

        for issue in sorted_issues[:15]:
            severity = "🔴" if issue.complexity > issue.threshold * 1.5 else "🟡"
            print(f"\n{severity} {issue.file}:{issue.line}")
            print(f"   Method: {issue.method_name}()")
            print(f"   Complexity: {issue.complexity} (threshold: {issue.threshold})")

            if issue.complexity > 20:
                print(f"   ⚠️  SEVERELY COMPLEX - Must refactor")
            elif issue.complexity > 15:
                print(f"   ⚠️  Very complex - Should refactor")
            elif issue.complexity > 10:
                print(f"   ℹ️  Moderately complex - Consider refactoring")

        if len(sorted_issues) > 15:
            print(f"\n... and {len(sorted_issues) - 15} more complex methods")

        print("\n" + "-" * 80)
        print("COMPLEXITY GUIDELINES:")
        print("  1-10:   ✅ Good")
        print("  11-15:  ⚠️  Consider refactoring")
        print("  16-20:  🟡 Should refactor")
        print("  > 20:   🔴 Must refactor")
    else:
        print("\n✅ All methods have acceptable complexity!")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze cyclomatic complexity of Java methods"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--threshold", type=int, default=10,
                        help="Complexity threshold (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    analyzer = CyclomaticComplexityAnalyzer(threshold=args.threshold)
    result = analyzer.validate_directory(args.path)

    print_results(result, json_output=args.json)

    if result.get_count_by_severity("high") > 0:
        sys.exit(2)
    elif result.get_count_by_severity("medium") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
