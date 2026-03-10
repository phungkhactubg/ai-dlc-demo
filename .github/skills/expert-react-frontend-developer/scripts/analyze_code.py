#!/usr/bin/env python3
"""
React/TypeScript Code Analyzer
==============================
Analyze React/TypeScript source code for architecture compliance, code quality, and potential issues.

Usage:
    python analyze_code.py <path_to_ts_file_or_directory>
    python analyze_code.py apps/frontend/src/dashboard
"""

import os
import sys
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set
from collections import defaultdict


@dataclass
class Issue:
    """Represents a code issue."""
    severity: str  # ERROR, WARNING, INFO
    file: str
    line: int
    message: str
    rule: str


@dataclass
class AnalysisResult:
    """Holds analysis results."""
    files_analyzed: int = 0
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)


class ReactCodeAnalyzer:
    """Analyzer for React/TypeScript code following Senior Frontend Developer guidelines."""

    def __init__(self):
        self.result = AnalysisResult()
        self.forbidden_patterns = [
            # TypeScript Anti-patterns
            (r':\s*any\b', 'Avoid using `any` type; use `unknown` or proper typing'),
            (r'as\s+any\b', 'Avoid type assertion to `any`'),
            (r'@ts-ignore', 'Avoid @ts-ignore; fix the underlying type issue'),
            (r'@ts-nocheck', 'Never use @ts-nocheck'),
            
            # React Anti-patterns
            (r'useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*fetch', 'Consider using a custom hook for data fetching in useEffect'),
            (r'console\.(log|warn|error|debug)\(', 'Remove console statements in production code'),
            (r'\.innerHTML\s*=', 'Avoid innerHTML; use React rendering or dangerouslySetInnerHTML with caution'),
            
            # State Management Anti-patterns
            (r'useState\s*<\s*any\s*>', 'Avoid useState<any>; provide proper type'),
            (r'createContext\s*<\s*any\s*>', 'Avoid createContext<any>; provide proper type'),
            
            # Import Anti-patterns
            (r'from\s+[\'"]\.\.\/\.\.\/\.\.\/\.\.', 'Deep relative imports; consider path aliases'),
            (r'import\s+\*\s+as', 'Avoid namespace imports; use named imports for tree-shaking'),
            
            # Security
            (r'dangerouslySetInnerHTML', 'dangerouslySetInnerHTML can lead to XSS; ensure input is sanitized'),
            (r'eval\(', 'Never use eval()'),
        ]

        self.required_patterns = {
            'store': [
                (r'immer|produce', 'Zustand stores should use immer for immutability'),
                (r'devtools', 'Zustand stores should wrap with devtools in development'),
            ],
            'model': [
                (r'z\.object|z\.string|z\.number', 'Model files should use Zod for schema definition'),
                (r'z\.infer', 'Types should be inferred from Zod schemas'),
            ],
            'service': [
                (r'implements\s+I\w+Service', 'Service should implement an interface'),
                (r'\.parse\(', 'Service should validate API responses with Zod'),
            ],
            'hook': [
                (r'export\s+(const|function)\s+use\w+', 'Custom hooks must start with "use"'),
            ],
            'component': [
                (r'(React\.)?memo\(', 'Consider memoizing presentational components'),
            ],
        }

        self.performance_warnings = [
            (r'sx=\{\{[^}]{100,}\}\}', 'Large sx prop object; consider using styled() for static styles'),
            (r'style=\{\{[^}]+\}\}', 'Inline style object creates new reference each render'),
            (r'onClick=\{\(\)\s*=>', 'Inline arrow function in onClick; consider useCallback'),
            (r'\.map\([^)]*\)\s*\.filter\(', 'Chain of array methods; consider reducing iterations'),
        ]

    def analyze_file(self, filepath: Path) -> None:
        """Analyze a single TypeScript/TSX file."""
        if filepath.suffix not in ['.ts', '.tsx']:
            return
        if filepath.name.endswith('.test.ts') or filepath.name.endswith('.test.tsx'):
            return  # Skip test files
        if filepath.name.endswith('.d.ts'):
            return  # Skip declaration files
        if 'node_modules' in str(filepath):
            return

        self.result.files_analyzed += 1

        try:
            content = filepath.read_text(encoding='utf-8')
            lines = content.split('\n')
        except Exception as e:
            self.result.issues.append(Issue(
                severity='ERROR',
                file=str(filepath),
                line=0,
                message=f'Failed to read file: {e}',
                rule='file-read'
            ))
            return

        # Determine file type based on path and content
        file_type = self._determine_file_type(filepath, content)

        # Check forbidden patterns
        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.forbidden_patterns:
                if re.search(pattern, line):
                    self.result.issues.append(Issue(
                        severity='WARNING',
                        file=str(filepath),
                        line=line_num,
                        message=message,
                        rule='forbidden-pattern'
                    ))

        # Check performance warnings
        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.performance_warnings:
                if re.search(pattern, line):
                    self.result.issues.append(Issue(
                        severity='INFO',
                        file=str(filepath),
                        line=line_num,
                        message=f'[PERF] {message}',
                        rule='performance'
                    ))

        # Check required patterns for specific file types
        if file_type in self.required_patterns:
            for pattern, message in self.required_patterns[file_type]:
                if not re.search(pattern, content):
                    self.result.issues.append(Issue(
                        severity='INFO',
                        file=str(filepath),
                        line=0,
                        message=message,
                        rule='required-pattern'
                    ))

        # Check component file structure
        if file_type == 'component':
            self._analyze_component(filepath, content, lines)

        # Check for large components
        self._analyze_complexity(filepath, content)

    def _determine_file_type(self, filepath: Path, content: str) -> str:
        """Determine the type of TypeScript file based on path and content."""
        path_str = str(filepath).lower()
        filename = filepath.name.lower()

        if '/stores/' in path_str or '.store.' in filename:
            return 'store'
        elif '/models/' in path_str or '.model.' in filename:
            return 'model'
        elif '/services/' in path_str or '.service.' in filename:
            return 'service'
        elif '/hooks/' in path_str or filename.startswith('use'):
            return 'hook'
        elif '/api/' in path_str or '.api.' in filename:
            return 'api'
        elif filepath.suffix == '.tsx':
            return 'component'
        return 'unknown'

    def _analyze_component(self, filepath: Path, content: str, lines: List[str]) -> None:
        """Analyze React component structure."""
        # Check for missing displayName on memo components
        if 'memo(' in content and '.displayName' not in content:
            self.result.issues.append(Issue(
                severity='INFO',
                file=str(filepath),
                line=0,
                message='Memoized component missing displayName; add it for DevTools debugging',
                rule='react-best-practice'
            ))

        # Check for missing key prop in map
        for line_num, line in enumerate(lines, 1):
            if '.map(' in line and 'key=' not in line and 'key:' not in line:
                # Look ahead for key prop
                next_lines = '\n'.join(lines[line_num:line_num+5])
                if 'key=' not in next_lines and 'key:' not in next_lines:
                    self.result.issues.append(Issue(
                        severity='WARNING',
                        file=str(filepath),
                        line=line_num,
                        message='Possible missing key prop in array rendering',
                        rule='react-key'
                    ))

    def _analyze_complexity(self, filepath: Path, content: str) -> None:
        """Check for overly complex files."""
        line_count = content.count('\n')

        if line_count > 300:
            self.result.issues.append(Issue(
                severity='WARNING',
                file=str(filepath),
                line=0,
                message=f'File has {line_count} lines. Consider splitting into smaller modules.',
                rule='file-complexity'
            ))

        # Count hooks in a single component file
        hook_count = len(re.findall(r'use\w+\(', content))
        if hook_count > 10:
            self.result.issues.append(Issue(
                severity='WARNING',
                file=str(filepath),
                line=0,
                message=f'File uses {hook_count} hooks. Consider extracting logic into custom hooks.',
                rule='hook-complexity'
            ))

    def analyze_directory(self, dirpath: Path) -> None:
        """Recursively analyze all TypeScript files in a directory."""
        for filepath in dirpath.rglob('*.ts'):
            self.analyze_file(filepath)
        for filepath in dirpath.rglob('*.tsx'):
            self.analyze_file(filepath)

    def print_report(self) -> None:
        """Print the analysis report."""
        print("=" * 60)
        print("REACT/TYPESCRIPT CODE ANALYSIS REPORT")
        print("=" * 60)
        print(f"Files analyzed: {self.result.files_analyzed}")
        print()

        if not self.result.issues:
            print("✅ No issues found! Code follows guidelines.")
            return

        # Group by severity
        by_severity = defaultdict(list)
        for issue in self.result.issues:
            by_severity[issue.severity].append(issue)

        for severity in ['ERROR', 'WARNING', 'INFO']:
            issues = by_severity.get(severity, [])
            if not issues:
                continue

            icon = {'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️'}[severity]
            print(f"\n{icon} {severity} ({len(issues)} issues)")
            print("-" * 40)

            for issue in issues:
                location = f"{issue.file}"
                if issue.line > 0:
                    location += f":{issue.line}"
                print(f"  [{issue.rule}] {location}")
                print(f"    {issue.message}")
                print()

        # Summary
        print("=" * 60)
        print("SUMMARY")
        print(f"  Errors:   {len(by_severity.get('ERROR', []))}")
        print(f"  Warnings: {len(by_severity.get('WARNING', []))}")
        print(f"  Info:     {len(by_severity.get('INFO', []))}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze React/TypeScript code for architecture compliance and quality"
    )
    parser.add_argument("path", help="Path to TypeScript file or directory to analyze")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    target = Path(args.path)

    if not target.exists():
        print(f"Error: Path does not exist: {target}")
        sys.exit(1)

    analyzer = ReactCodeAnalyzer()

    if target.is_file():
        analyzer.analyze_file(target)
    else:
        analyzer.analyze_directory(target)

    if args.json:
        import json
        output = {
            'files_analyzed': analyzer.result.files_analyzed,
            'issues': [
                {
                    'severity': i.severity,
                    'file': i.file,
                    'line': i.line,
                    'message': i.message,
                    'rule': i.rule
                }
                for i in analyzer.result.issues
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        analyzer.print_report()

    # Exit with error code if there are errors
    errors = [i for i in analyzer.result.issues if i.severity == 'ERROR']
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
