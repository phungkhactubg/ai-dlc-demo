#!/usr/bin/env python3
"""
Check Anti-Patterns Script

Scans code files for common anti-patterns in both Go and TypeScript/React code.
Reports issues with severity levels and suggested fixes.

Usage:
    python check_anti_patterns.py <path> [--type go|ts|all] [--format json|text]

Examples:
    python check_anti_patterns.py features/iov
    python check_anti_patterns.py apps/frontend/src/workflow --type ts
    python check_anti_patterns.py . --format json
"""

import argparse
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


class Severity(Enum):
    CRITICAL = "🔴 CRITICAL"
    WARNING = "🟡 WARNING"
    SUGGESTION = "🔵 SUGGESTION"


@dataclass
class Issue:
    file: str
    line: int
    severity: Severity
    category: str
    message: str
    code_snippet: str
    suggestion: str


# === GO ANTI-PATTERNS ===
GO_PATTERNS: List[Tuple[str, Severity, str, str, str]] = [
    # Pattern, Severity, Category, Message, Suggestion
    
    # Critical: Ignored errors
    (r',\s*_\s*:?=\s*\w+\.\w+\([^)]*\)(?!\s*//\s*intentionally)',
     Severity.CRITICAL, "Error Handling",
     "Ignored error return value",
     "Handle the error explicitly or add '// intentionally' comment if intentional"),
    
    # Critical: Panic in business logic
    (r'\bpanic\s*\(',
     Severity.CRITICAL, "Error Handling",
     "Using panic() in business logic",
     "Return error instead of panicking. Panics should only be used for unrecoverable errors in initialization."),
    
    # Critical: String concatenation in DB queries
    (r'(?:Find|Insert|Update|Delete|Aggregate|Query|Exec)\s*\([^)]*\+[^)]*\)',
     Severity.CRITICAL, "Security",
     "Potential SQL/NoSQL injection via string concatenation",
     "Use parameterized queries or builder patterns instead of string concatenation."),
    
    # Critical: TODO/FIXME/HACK
    (r'//\s*(TODO|FIXME|XXX|HACK)\s*:?',
     Severity.CRITICAL, "Production Ready",
     "TODO/FIXME/HACK comment found",
     "Complete the implementation or remove the comment before merge."),
    
    # Critical: context.Background() in request handlers
    (r'context\.Background\(\)',
     Severity.CRITICAL, "Concurrency",
     "Using context.Background() - may lose cancellation/timeout signals",
     "Use the parent context from the request (ctx) instead."),
    
    # BLOCKER: context.TODO() in production code
    (r'context\.TODO\(\)',
     Severity.CRITICAL, "Production Ready",
     "⛔ DEPLOYMENT BLOCKER: context.TODO() = incomplete refactoring",
     "Replace with proper context propagation from caller. context.TODO() means 'fix later' - but later never comes."),
    
    # Critical: Goroutine without context
    (r'go\s+func\s*\(\s*\)\s*\{[^}]*context\.Background\(\)',
     Severity.CRITICAL, "Concurrency",
     "Goroutine using context.Background() instead of parent context",
     "Pass parent context to goroutine and check ctx.Done() for cancellation."),
    
    # Warning: Wrong package name (subfolder)
    (r'^package\s+(controllers|services|repositories|adapters|models)\s*$',
     Severity.WARNING, "Package Naming",
     "Package name is subfolder name instead of feature name",
     "Use the feature name as package name (e.g., 'package iov' not 'package controllers')."),
    
    # Warning: Standard log package
    (r'import\s+"log"',
     Severity.WARNING, "Logging",
     "Using standard 'log' package instead of custom logger",
     "Use 'import logger \"system_integration_management/utils/logging\"' instead."),
    
    # Warning: log.Printf/log.Println
    (r'\blog\.(Printf?|Println|Fatal|Panic)\s*\(',
     Severity.WARNING, "Logging",
     "Using standard log functions",
     "Use logger.Info(), logger.Error(), etc. from utils/logging package."),
    
    # Warning: fmt.Sprintf in log calls
    (r'logger\.\w+\s*\(\s*fmt\.Sprintf\s*\(',
     Severity.WARNING, "Logging",
     "Using fmt.Sprintf in logger calls",
     "Use structured logging with key-value pairs: logger.Info(\"message\", \"key\", value)"),
    
    # Warning: Long function
    (r'func\s+\([^)]+\)\s+\w+\s*\([^)]*\)[^{]*\{',
     Severity.SUGGESTION, "Clean Code",
     "Consider checking function length",
     "Functions should ideally be < 30 lines, max 50 lines. Use validate_function_size.py for detailed analysis."),
    
    # Suggestion: Missing error context
    (r'return\s+err\s*$',
     Severity.SUGGESTION, "Error Handling",
     "Returning raw error without context",
     "Consider wrapping: return fmt.Errorf(\"context: %w\", err)"),

    # Warning: Weak Crypto (MD5/SHA1)
    (r'"crypto/(md5|sha1)"',
     Severity.WARNING, "Security",
     "Weak cryptographic hashing algorithm detected",
     "Use 'crypto/sha256' or 'golang.org/x/crypto/bcrypt' instead."),

    # Warning: time.Sleep in production
    (r'time\.Sleep\s*\(',
     Severity.WARNING, "Performance",
     "Hardcoded sleep detected",
     "Use context cancellation, tickers, or channels instead of blocking sleep."),

    # Warning: Defer in loop (simple heuristic)
    (r'^\s*defer\s+.*Close\(\)',
     Severity.SUGGESTION, "Performance",
     "Defer .Close() might be inside a loop/block",
     "Check if this defer is inside a loop. If so, wrap body in a function."),

    # Critical: JSON Marshal/Unmarshal ignored
    (r'json\.(Marshal|Unmarshal)\([^)]*\)(?!\s*,)',
     Severity.CRITICAL, "Error Handling",
     "Ignoring JSON error",
     "Always check the error returned by json.Marshal/Unmarshal."),

    # Critical: Unsafe Type Assertion
    (r'\.([a-zA-Z0-9_*\[\]]+)\)(?:\s*//.*)?$',
     Severity.CRITICAL, "Type Safety",
     "Unsafe type assertion (missing 'ok' check)",
     "Use 'val, ok := x.(T)' to prevent panics."),

    # Warning: fmt.Print (Debugging leftovers)
    (r'\bfmt\.Print(f|ln)?\s*\(',
     Severity.WARNING, "Production Ready",
     "fmt.Print detected",
     "Use the logger for actual logs, or remove debug prints."),
]

# === TYPESCRIPT/REACT ANTI-PATTERNS ===
TS_PATTERNS: List[Tuple[str, Severity, str, str, str]] = [
    # Critical: Using 'any' type
    (r':\s*any\b',
     Severity.CRITICAL, "Type Safety",
     "Using 'any' type",
     "Use specific types or 'unknown' with type narrowing."),
    
    # Critical: as any cast
    (r'\bas\s+any\b',
     Severity.CRITICAL, "Type Safety",
     "Casting to 'any'",
     "Use proper type assertions or type guards instead."),
    
    # Critical: dangerouslySetInnerHTML without sanitize
    (r'dangerouslySetInnerHTML\s*=\s*\{\s*\{[^}]*__html\s*:[^}]*(?!sanitize|DOMPurify)',
     Severity.CRITICAL, "Security",
     "dangerouslySetInnerHTML without sanitization",
     "Sanitize HTML with DOMPurify before rendering."),
    
    # Critical: TODO/FIXME/HACK
    (r'//\s*(TODO|FIXME|XXX|HACK)\s*:?',
     Severity.CRITICAL, "Production Ready",
     "TODO/FIXME/HACK comment found",
     "Complete the implementation or remove the comment before merge."),
    
    # Warning: console.log in production
    (r'\bconsole\.(log|debug|info|warn|error)\s*\(',
     Severity.WARNING, "Production Ready",
     "Console statement found",
     "Remove console statements before commit or use proper logging service."),
    
    # Warning: Missing .parse() on API response
    (r'response\.data(?!\s*\)|\.)',
     Severity.WARNING, "Type Safety",
     "Using API response without Zod validation",
     "Validate with Schema.parse(response.data) or .safeParse()"),
    
    # Warning: Direct service import in component
    (r'from\s+[\'"]@?[^\'\"]*infrastructure/services',
     Severity.WARNING, "Architecture",
     "Direct service import in component (likely)",
     "Import services through hooks instead for proper dependency injection."),
    
    # Warning: Barrel import from Lodash
    (r'import\s+\{.*\}\s+from\s+[\'"]lodash[\'"]',
     Severity.WARNING, "Performance",
     "Barrel import from lodash",
     "Import specific functions to avoid bundling the whole library: import map from 'lodash/map'."),

    # Suggestion: Inline Zustand selector
    (r'useStore\(\s*(state|s)\s*=>',
     Severity.SUGGESTION, "Performance",
     "Inline Zustand selector detected",
     "Define selectors outside the component to prevent unnecessary re-runs if using complex logic."),
    
    # Warning: Missing useCallback for handlers
    (r'onClick\s*=\s*\{\s*\(\)\s*=>\s*',
     Severity.SUGGESTION, "Performance",
     "Inline arrow function in event handler",
     "Consider useCallback if this component re-renders frequently."),
    
    # Suggestion: Large component file
    (r'^export\s+(default\s+)?function\s+\w+',
     Severity.SUGGESTION, "Clean Code",
     "Check component file size",
     "Components should ideally be < 200 lines. Consider splitting."),
    
    # Warning: Missing ErrorBoundary
    (r'<Route\s+[^>]*element\s*=\s*\{(?!.*ErrorBoundary)',
     Severity.WARNING, "Error Handling",
     "Route without ErrorBoundary wrapper",
     "Wrap route components in ErrorBoundary for graceful error handling."),

    # Warning: Hardcoded Secret Keys
    (r'(REACT_APP_)?(SECRET|KEY|TOKEN|PASSWORD)\s*[:=]\s*[\'"][a-zA-Z0-9]{10,}[\'"]',
     Severity.CRITICAL, "Security",
     "Potential hardcoded secret key detected",
     "Use environment variables (VITE_...) and never commit secrets to repo."),

    # Suggestion: Inline Object Styles
    (r'style\s*=\s*\{\{\s*[a-zA-Z0-9]+\s*:',
     Severity.SUGGESTION, "Performance",
     "Inline object styles trigger re-renders",
     "Extract style object to a constant or use CSS classes/styled-components."),
]


def find_files(path: str, extensions: List[str]) -> List[str]:
    """Find all files with given extensions recursively."""
    result = []
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix in extensions:
            return [str(path_obj)]
        return []
    
    for ext in extensions:
        result.extend([str(p) for p in path_obj.rglob(f"*{ext}")])
    
    # Exclude common directories
    exclude_dirs = ['node_modules', 'vendor', '.git', 'dist', 'build', '__pycache__']
    result = [f for f in result if not any(d in f for d in exclude_dirs)]
    
    return result


def scan_file(filepath: str, patterns: List[Tuple[str, Severity, str, str, str]]) -> List[Issue]:
    """Scan a single file for anti-patterns."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return []
    
    for line_num, line in enumerate(lines, 1):
        for pattern, severity, category, message, suggestion in patterns:
            if re.search(pattern, line, re.MULTILINE):
                issues.append(Issue(
                    file=filepath,
                    line=line_num,
                    severity=severity,
                    category=category,
                    message=message,
                    code_snippet=line.strip()[:100],
                    suggestion=suggestion
                ))
    
    return issues


def check_function_length(filepath: str) -> List[Issue]:
    """Check for overly long functions in Go files."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return []
    
    if not filepath.endswith('.go'):
        return []
    
    # Simple heuristic: count lines between func and closing brace
    in_func = False
    func_start = 0
    func_name = ""
    brace_count = 0
    
    for i, line in enumerate(lines):
        if re.match(r'\s*func\s+', line):
            in_func = True
            func_start = i + 1
            match = re.search(r'func\s+(?:\([^)]+\)\s+)?(\w+)', line)
            func_name = match.group(1) if match else "unknown"
            brace_count = line.count('{') - line.count('}')
        elif in_func:
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                func_length = i - func_start + 1
                if func_length > 70:
                    issues.append(Issue(
                        file=filepath,
                        line=func_start,
                        severity=Severity.CRITICAL,
                        category="Clean Code",
                        message=f"Function '{func_name}' is {func_length} lines (>70) - MUST REFACTOR",
                        code_snippet=f"func {func_name}...",
                        suggestion="Decompose into smaller helper functions. Use validate_function_size.py for details."
                    ))
                elif func_length > 50:
                    issues.append(Issue(
                        file=filepath,
                        line=func_start,
                        severity=Severity.WARNING,
                        category="Clean Code",
                        message=f"Function '{func_name}' is {func_length} lines (>50)",
                        code_snippet=f"func {func_name}...",
                        suggestion="Consider breaking down into smaller functions."
                    ))
                in_func = False
    
    return issues


def check_file_size(filepath: str) -> List[Issue]:
    """Check for overly large files."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return []
    
    # Count non-empty, non-comment lines
    code_lines = 0
    in_block_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        if '/*' in stripped:
            in_block_comment = True
        if '*/' in stripped:
            in_block_comment = False
            continue
        
        if in_block_comment:
            continue
        
        if stripped and not stripped.startswith('//'):
            code_lines += 1
    
    if code_lines > 700:
        issues.append(Issue(
            file=filepath,
            line=1,
            severity=Severity.CRITICAL,
            category="Clean Code",
            message=f"File has {code_lines} code lines (>700) - MUST SPLIT",
            code_snippet=f"File: {Path(filepath).name}",
            suggestion="Split by concern: *_internal.go, *_helpers.go, or by domain entity."
        ))
    elif code_lines > 500:
        issues.append(Issue(
            file=filepath,
            line=1,
            severity=Severity.WARNING,
            category="Clean Code",
            message=f"File has {code_lines} code lines (>500)",
            code_snippet=f"File: {Path(filepath).name}",
            suggestion="Consider splitting large files to improve maintainability."
        ))
    
    return issues


def format_text(issues: List[Issue]) -> str:
    """Format issues as human-readable text."""
    if not issues:
        return "✅ No anti-patterns detected!\n"
    
    output = []
    
    # Group by severity
    by_severity: Dict[Severity, List[Issue]] = {}
    for issue in issues:
        by_severity.setdefault(issue.severity, []).append(issue)
    
    # Summary
    output.append("=" * 60)
    output.append("ANTI-PATTERN CHECK RESULTS")
    output.append("=" * 60)
    output.append("")
    output.append(f"Total Issues: {len(issues)}")
    for sev in [Severity.CRITICAL, Severity.WARNING, Severity.SUGGESTION]:
        count = len(by_severity.get(sev, []))
        output.append(f"  {sev.value}: {count}")
    output.append("")
    
    # Details by severity
    for sev in [Severity.CRITICAL, Severity.WARNING, Severity.SUGGESTION]:
        sev_issues = by_severity.get(sev, [])
        if not sev_issues:
            continue
        
        output.append("-" * 40)
        output.append(f"{sev.value} ({len(sev_issues)} issues)")
        output.append("-" * 40)
        
        for i, issue in enumerate(sev_issues, 1):
            output.append(f"\n{i}. [{issue.category}] {issue.message}")
            output.append(f"   File: {issue.file}:{issue.line}")
            output.append(f"   Code: {issue.code_snippet}")
            output.append(f"   Fix:  {issue.suggestion}")
    
    return "\n".join(output)


def format_json(issues: List[Issue]) -> str:
    """Format issues as JSON."""
    return json.dumps([{
        "file": i.file,
        "line": i.line,
        "severity": i.severity.name,
        "category": i.category,
        "message": i.message,
        "code_snippet": i.code_snippet,
        "suggestion": i.suggestion
    } for i in issues], indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Check code for common anti-patterns"
    )
    parser.add_argument("path", help="Path to file or directory to check")
    parser.add_argument("--type", choices=["go", "ts", "all"], default="all",
                        help="Type of code to check (default: all)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Determine which file types to check
    extensions = []
    patterns_to_use = []
    
    if args.type in ["go", "all"]:
        extensions.append(".go")
        patterns_to_use.extend(GO_PATTERNS)
    
    if args.type in ["ts", "all"]:
        extensions.extend([".ts", ".tsx"])
        patterns_to_use.extend(TS_PATTERNS)
    
    # Find files
    files = find_files(args.path, extensions)
    
    if not files:
        print(f"No matching files found in {args.path}")
        sys.exit(0)
    
    # Scan files
    all_issues: List[Issue] = []
    
    for filepath in files:
        if filepath.endswith('.go'):
            all_issues.extend(scan_file(filepath, GO_PATTERNS))
            all_issues.extend(check_function_length(filepath))
            all_issues.extend(check_file_size(filepath))
        elif filepath.endswith(('.ts', '.tsx')):
            all_issues.extend(scan_file(filepath, TS_PATTERNS))
    
    # Sort by severity
    severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.SUGGESTION: 2}
    all_issues.sort(key=lambda x: (severity_order[x.severity], x.file, x.line))
    
    # Output
    if args.format == "json":
        print(format_json(all_issues))
    else:
        print(format_text(all_issues))
    
    # Exit code based on critical issues
    critical_count = sum(1 for i in all_issues if i.severity == Severity.CRITICAL)
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
