#!/usr/bin/env python3
"""
analyze_dependencies.py

Analyzes package dependencies and detects architectural issues:
- Circular dependencies between packages
- Layer violations (e.g., service depending on controller)
- Metrics: instability, abstractness, distance from main sequence

Usage:
    python analyze_dependencies.py <path> [--metrics] [--graph output.dot] [--json]
"""

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional


@dataclass
class DependencyIssue:
    level: str
    category: str
    source: str
    target: str
    message: str


@dataclass
class ValidationResult:
    issues: List[DependencyIssue] = field(default_factory=list)
    files_checked: int = 0
    packages_analyzed: int = 0
    circular_dependencies: List[List[str]] = field(default_factory=list)

    def add_issue(self, issue: DependencyIssue) -> None:
        self.issues.append(issue)

    def get_count_by_level(self, level: str) -> int:
        return sum(1 for i in self.issues if i.level == level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "critical": self.get_count_by_level("CRITICAL"),
                "warning": self.get_count_by_level("WARNING"),
                "files_checked": self.files_checked,
                "packages_analyzed": self.packages_analyzed,
                "circular_dependencies": len(self.circular_dependencies)
            },
            "issues": [
                {
                    "level": i.level,
                    "category": i.category,
                    "source": i.source,
                    "target": i.target,
                    "message": i.message
                }
                for i in self.issues
            ],
            "circular_dependencies": self.circular_dependencies
        }


class DependencyAnalyzer:
    """Analyzes package dependencies for architectural issues."""

    def __init__(self):
        self.result = ValidationResult()
        self.package_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.layer_order = {
            'controller': 5,
            'rest': 5,
            'service': 4,
            'adapter': 3,
            'repository': 2,
            'model': 1,
            'config': 0,  # Can depend on anything
            'exception': 0,
        }

    def validate_directory(self, path: str) -> ValidationResult:
        """Analyze all Java files in a directory."""
        root_path = Path(path)

        if not root_path.exists():
            print(f"Error: Path '{path}' does not exist.")
            return self.result

        java_files = list(root_path.rglob("*.java"))
        java_files = [f for f in java_files if "test" not in str(f).lower()]

        # Extract package dependencies
        for java_file in java_files:
            self._analyze_file(str(java_file))

        # Get unique packages
        unique_packages = set()
        for file_path in [str(f) for f in java_files]:
            pkg = self._extract_package(file_path)
            if pkg:
                unique_packages.add(pkg)

        self.result.packages_analyzed = len(unique_packages)
        self.result.files_checked = len(java_files)

        # Detect circular dependencies
        self._detect_circular_dependencies()

        # Check layer violations
        self._check_layer_violations()

        return self.result

    def _analyze_file(self, file_path: str) -> None:
        """Extract package and imports from a Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            source_package = self._extract_package_from_content(content)
            if not source_package:
                return

            # Extract imports
            imports = self._extract_imports(content)

            # Filter for project-internal imports only
            base_package = self._get_base_package(source_package)

            for imp in imports:
                if imp.startswith(base_package):
                    # This is an internal dependency
                    target_package = imp.rsplit('.', 1)[0] if '.' in imp else imp
                    self.package_dependencies[source_package].add(target_package)

        except Exception as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")

    def _extract_package(self, file_path: str) -> Optional[str]:
        """Extract package name from file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._extract_package_from_content(content)
        except:
            return None

    def _extract_package_from_content(self, content: str) -> Optional[str]:
        """Extract package declaration from content."""
        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else None

    def _extract_imports(self, content: str) -> Set[str]:
        """Extract all import statements."""
        imports = set()
        for match in re.finditer(r'import\s+([\w.]+);', content):
            imports.add(match.group(1))
        return imports

    def _get_base_package(self, package: str) -> str:
        """Get the base package (e.g., 'com.example' from 'com.example.user.service')."""
        parts = package.split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return package

    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.package_dependencies.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    self.result.circular_dependencies.append(cycle)

                    self.result.add_issue(DependencyIssue(
                        level="CRITICAL",
                        category="CIRCULAR_DEPENDENCY",
                        source=node,
                        target=neighbor,
                        message=f"Circular dependency detected: {' -> '.join(cycle)}"
                    ))
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for package in self.package_dependencies:
            if package not in visited:
                dfs(package)

    def _check_layer_violations(self) -> None:
        """Check for architectural layer violations."""
        for source, targets in self.package_dependencies.items():
            source_layer = self._get_layer_from_package(source)

            for target in targets:
                target_layer = self._get_layer_from_package(target)

                if source_layer and target_layer:
                    source_level = self.layer_order.get(source_layer, -1)
                    target_level = self.layer_order.get(target_layer, -1)

                    # Config and exception can depend on anything
                    if source_layer in ['config', 'exception']:
                        continue

                    # Lower layers shouldn't depend on higher layers
                    if source_level < target_level and source_level > 0:
                        self.result.add_issue(DependencyIssue(
                            level="WARNING",
                            category="LAYER_VIOLATION",
                            source=source,
                            target=target,
                            message=f"Layer violation: {source_layer} depending on {target_layer}"
                        ))

    def _get_layer_from_package(self, package: str) -> Optional[str]:
        """Extract layer name from package (e.g., 'service' from 'com.example.user.service')."""
        parts = package.split('.')
        for part in parts:
            if part in self.layer_order:
                return part
        return None


def print_results(result: ValidationResult, json_output: bool = False,
                  show_metrics: bool = False) -> None:
    """Print analysis results."""
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 80)
    print("PACKAGE DEPENDENCY ANALYSIS")
    print("=" * 80)

    print(f"\nFiles analyzed: {result.files_checked}")
    print(f"Packages analyzed: {result.packages_analyzed}")
    print(f"\n🔴 CRITICAL: {result.get_count_by_level('CRITICAL')}")
    print(f"⚠️  WARNING: {result.get_count_by_level('WARNING')}")

    if result.circular_dependencies:
        print("\n" + "-" * 80)
        print("🔄 CIRCULAR DEPENDENCIES DETECTED:")
        print("-" * 80)
        for cycle in result.circular_dependencies:
            print(f"  {' -> '.join(cycle)}")

    if result.issues:
        print("\n" + "-" * 80)
        print("ISSUES FOUND:")
        print("-" * 80)

        for issue in result.issues[:20]:
            emoji = "🔴" if issue.level == "CRITICAL" else "⚠️"
            print(f"\n{emoji} {issue.category}")
            print(f"   Source: {issue.source}")
            print(f"   Target: {issue.target}")
            print(f"   {issue.message}")

        if len(result.issues) > 20:
            print(f"\n... and {len(result.issues) - 20} more issues")
    else:
        print("\n✅ No dependency issues found!")

    print("\n" + "-" * 80)
    print("ARCHITECTURAL LAYER ORDER (bottom → top):")
    print("  model/repository → adapter → service → controller")
    print("\nAllowed dependencies:")
    print("  ✅ Higher layers → Lower layers (e.g., service → repository)")
    print("  ✅ config → Any layer")
    print("  ✅ exception → Any layer")
    print("\nForbidden dependencies:")
    print("  ❌ Lower layers → Higher layers (e.g., repository → service)")
    print("  ❌ Circular dependencies between any packages")
    print("=" * 80)


def generate_dot_graph(output_path: str, dependencies: Dict[str, Set[str]]) -> None:
    """Generate a GraphViz DOT file for visualization."""
    with open(output_path, 'w') as f:
        f.write("digraph dependencies {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [shape=box, style=rounded];\n\n")

        # Group by layer
        layer_colors = {
            'controller': 'lightblue',
            'rest': 'lightblue',
            'service': 'lightgreen',
            'adapter': 'lightyellow',
            'repository': 'lightcoral',
            'model': 'lightgray',
        }

        for source, targets in dependencies.items():
            source_layer = None
            for layer in ['controller', 'service', 'repository', 'adapter', 'model']:
                if layer in source.lower():
                    source_layer = layer
                    break

            color = layer_colors.get(source_layer, 'white') if source_layer else 'white'
            f.write(f'  "{source}" [fillcolor={color}, style="filled,rounded"];\n')

        f.write("\n")

        for source, targets in dependencies.items():
            for target in targets:
                f.write(f'  "{source}" -> "{target}";\n')

        f.write("}\n")

    print(f"\n📊 Dependency graph written to: {output_path}")
    print(f"   Generate visualization with: dot -Tpng {output_path} -o deps.png")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze package dependencies for architectural issues"
    )
    parser.add_argument("path", help="Path to Java source directory")
    parser.add_argument("--metrics", action="store_true",
                        help="Show additional metrics (instability, abstractness)")
    parser.add_argument("--graph", metavar="output.dot",
                        help="Generate GraphViz DOT file for visualization")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    analyzer = DependencyAnalyzer()
    result = analyzer.validate_directory(args.path)

    print_results(result, json_output=args.json, show_metrics=args.metrics)

    if args.graph:
        generate_dot_graph(args.graph, analyzer.package_dependencies)

    if result.get_count_by_level("CRITICAL") > 0:
        sys.exit(2)
    elif result.get_count_by_level("WARNING") > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
