#!/usr/bin/env python3
"""
Semantic Scanner - Extract business rules, data flow, security issues, and tech debt.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
import argparse


class SemanticScanner:
    """Semantic analysis of codebase for business logic, security, and tech debt."""
    
    # Business rule patterns
    BUSINESS_PATTERNS = {
        "comments": [
            r"//\s*RULE:?\s*(.+)",
            r"//\s*Business:?\s*(.+)",
            r"#\s*RULE:?\s*(.+)",
            r"/\*\*?\s*@BusinessRule\s*(.+?)\*/",
            r"//\s*IMPORTANT:?\s*(.+)",
            r"//\s*NOTE:?\s*(.+)",
        ],
        "validation": [
            r"if\s+.*\s*(!=|==|<|>|<=|>=)\s*.+\s*{",
            r"validate\w*\s*\(",
            r"check\w*\s*\(",
            r"assert\w*\s*\(",
        ],
        "state_machine": [
            r"switch\s+\w+\.?[Ss]tatus",
            r"switch\s+\w+\.?[Ss]tate",
            r"case\s+[\"']?\w*[Ss]tatus",
        ],
    }
    
    # Security risk patterns
    SECURITY_PATTERNS = {
        "sql_injection": [
            r"fmt\.Sprintf\s*\([^)]*SELECT",
            r"fmt\.Sprintf\s*\([^)]*INSERT",
            r"fmt\.Sprintf\s*\([^)]*UPDATE",
            r"fmt\.Sprintf\s*\([^)]*DELETE",
            r"query\s*\+\s*[\"']",
            r"exec\s*\([^)]*\+",
        ],
        "hardcoded_secrets": [
            r"password\s*[=:]\s*[\"'][^\"']+[\"']",
            r"api_key\s*[=:]\s*[\"'][^\"']+[\"']",
            r"secret\s*[=:]\s*[\"'][^\"']+[\"']",
            r"token\s*[=:]\s*[\"'][A-Za-z0-9]{20,}[\"']",
        ],
        "command_injection": [
            r"exec\.Command\s*\([^)]*\+",
            r"os\.system\s*\([^)]*\+",
            r"subprocess\.\w+\s*\([^)]*shell=True",
        ],
        "path_traversal": [
            r"os\.Open\s*\([^)]*\+",
            r"ioutil\.Read\w+\s*\([^)]*\+",
            r"open\s*\([^)]*\+",
        ],
        "xss": [
            r"innerHTML\s*=",
            r"dangerouslySetInnerHTML",
            r"\.html\s*\(",
        ],
        "insecure_random": [
            r"math/rand",
            r"Math\.random\(\)",
            r"java\.util\.Random",
            r"Random\s*=\s*new\s*Random\("
        ],
        "insecure_deserialize": [
            r"ObjectInputStream\.readObject",
            r"BinaryFormatter\.Deserialize",
            r"JsonConvert\.DeserializeObject<dynamic>",
        ],
        "unsafe_execution": [
            r"Runtime\.getRuntime\(\)\.exec",
            r"Process\.Start",
            r"system\s*\(",
            r"exec[lvp][e]?\s*\(",
        ],
    }
    
    # Tech debt patterns
    TECH_DEBT_PATTERNS = {
        "todo": [
            r"//\s*TODO:?\s*(.+)",
            r"#\s*TODO:?\s*(.+)",
            r"//\s*FIXME:?\s*(.+)",
            r"//\s*HACK:?\s*(.+)",
            r"//\s*XXX:?\s*(.+)",
            r"//\s*TEMP:?\s*(.+)",
        ],
        "deprecated": [
            r"@[Dd]eprecated",
            r"//\s*deprecated",
            r"#\s*deprecated",
        ],
        "error_handling": [
            r"_\s*=\s*\w+\(",  # Go: ignored errors
            r"catch\s*\(\s*\)",  # Empty catch
            r"except:\s*$",  # Bare except
            r"\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)",  # Empty catch in JS
        ],
        "magic_numbers": [
            r"[^a-zA-Z0-9_](?:100|1000|60|24|365|86400|3600)[^a-zA-Z0-9_]",
        ],
        "unsafe_memory": [
            r"malloc\s*\(",
            r"free\s*\(",
            r"strcpy\s*\(",
            r"strcat\s*\(",
            r"gets\s*\(",
        ],
    }
    
    # Data flow patterns
    DATA_FLOW_PATTERNS = {
        "input": [
            r"req\.(Body|Param|Query|Header|Form)",
            r"request\.(body|params|query|headers)",
            r"ctx\.Bind",
            r"json\.Unmarshal",
            r"json\.NewDecoder",
            r"@RequestBody",
            r"@RequestParam",
            r"@PathVariable",
            r"\[FromBody\]",
            r"\[FromQuery\]",
            r"scanf\s*\(",
        ],
        "transformation": [
            r"map\[",
            r"\.map\s*\(",
            r"\.filter\s*\(",
            r"\.reduce\s*\(",
            r"for\s+.*range",
        ],
        "output": [
            r"ctx\.JSON",
            r"res\.json",
            r"json\.Marshal",
            r"json\.NewEncoder",
            r"return\s+.*Response",
        ],
        "storage": [
            r"\.Insert",
            r"\.Update",
            r"\.Delete",
            r"\.Find",
            r"\.Save",
            r"repository\.",
            r"DbContext",
            r"DbSet",
            r"jdbcTemplate",
            r"EntityManager",
            r"fwrite\s*\(",
        ],
    }
    
    def __init__(self, root_dir: Path, output_dir: Path, verbose: bool = False):
        self.root_dir = Path(root_dir).absolute()
        self.output_dir = Path(output_dir) / "SEMANTIC"
        self.verbose = verbose
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, msg: str):
        if self.verbose:
            print(f"   [semantic] {msg}")
    
    def scan_all(self):
        """Run all semantic analyses."""
        print("\n" + "="*60)
        print("  SEMANTIC ANALYSIS")
        print("="*60 + "\n")
        
        self.scan_business_rules()
        self.scan_security()
        self.scan_tech_debt()
        self.scan_data_flow()
        self.scan_complexity()
        
        print("\n✅ Semantic analysis complete!")
        print(f"📁 Output: {self.output_dir}")
    
    def scan_business_rules(self):
        """Extract business rules from code."""
        print("📋 Scanning for business rules...")
        
        rules: List[Dict] = []
        validations: List[Dict] = []
        state_machines: List[Dict] = []
        
        for path in self._get_source_files():
            content = self._read_file(path)
            if not content:
                continue
            
            rel_path = str(path.relative_to(self.root_dir))
            
            # Find rule comments
            for pattern in self.BUSINESS_PATTERNS["comments"]:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    line_num = content[:match.start()].count('\n') + 1
                    rules.append({
                        "file": rel_path,
                        "line": line_num,
                        "rule": match.group(1).strip() if match.lastindex else match.group(0),
                    })
            
            # Find validations
            for pattern in self.BUSINESS_PATTERNS["validation"]:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    validations.append({
                        "file": rel_path,
                        "line": line_num,
                        "pattern": match.group(0)[:80],
                    })
            
            # Find state machines
            for pattern in self.BUSINESS_PATTERNS["state_machine"]:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    state_machines.append({
                        "file": rel_path,
                        "line": line_num,
                    })
        
        # Generate report
        content = f"""# Business Rules Analysis

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- **Documented Rules**: {len(rules)}
- **Validation Patterns**: {len(validations)}
- **State Machines**: {len(state_machines)}

## Documented Business Rules

| File | Line | Rule |
|------|------|------|
"""
        for r in rules[:100]:
            content += f"| `{r['file']}` | {r['line']} | {r['rule'][:60]} |\n"
        
        content += f"\n## State Machines Found\n\n"
        for sm in state_machines[:20]:
            content += f"- `{sm['file']}` line {sm['line']}\n"
        
        self._write_file("BUSINESS_RULES.md", content)
        print(f"   Found {len(rules)} documented rules, {len(state_machines)} state machines")
    
    def scan_security(self):
        """Scan for security issues."""
        print("🔒 Scanning for security issues...")
        
        issues: Dict[str, List[Dict]] = {k: [] for k in self.SECURITY_PATTERNS}
        
        for path in self._get_source_files():
            content = self._read_file(path)
            if not content:
                continue
            
            rel_path = str(path.relative_to(self.root_dir))
            
            for category, patterns in self.SECURITY_PATTERNS.items():
                for pattern in patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count('\n') + 1
                        issues[category].append({
                            "file": rel_path,
                            "line": line_num,
                            "snippet": match.group(0)[:50],
                        })
        
        # Generate report
        total = sum(len(v) for v in issues.values())
        severity = "🔴 HIGH" if total > 20 else "🟡 MEDIUM" if total > 5 else "🟢 LOW"
        
        content = f"""# Security Analysis

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

**Risk Level**: {severity}
**Total Issues**: {total}

| Category | Count | Severity |
|----------|-------|----------|
"""
        severity_map = {
            "sql_injection": "🔴 Critical",
            "hardcoded_secrets": "🔴 Critical",
            "command_injection": "🔴 Critical",
            "path_traversal": "🟡 High",
            "xss": "🟡 High",
            "insecure_random": "🟢 Low",
        }
        
        for cat, items in issues.items():
            if items:
                content += f"| {cat} | {len(items)} | {severity_map.get(cat, '🟡 Medium')} |\n"
        
        for cat, items in issues.items():
            if items:
                content += f"\n## {cat.replace('_', ' ').title()}\n\n"
                content += "| File | Line | Snippet |\n|------|------|--------|\n"
                for item in items[:20]:
                    content += f"| `{item['file']}` | {item['line']} | `{item['snippet']}` |\n"
        
        self._write_file("SECURITY_ANALYSIS.md", content)
        print(f"   Found {total} potential security issues")
    
    def scan_tech_debt(self):
        """Scan for technical debt."""
        print("🔧 Scanning for technical debt...")
        
        debt: Dict[str, List[Dict]] = {k: [] for k in self.TECH_DEBT_PATTERNS}
        long_functions: List[Dict] = []
        
        for path in self._get_source_files():
            content = self._read_file(path)
            if not content:
                continue
            
            rel_path = str(path.relative_to(self.root_dir))
            
            # Check patterns
            for category, patterns in self.TECH_DEBT_PATTERNS.items():
                for pattern in patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        line_num = content[:match.start()].count('\n') + 1
                        debt[category].append({
                            "file": rel_path,
                            "line": line_num,
                            "text": match.group(1) if match.lastindex else match.group(0)[:50],
                        })
            
            # Check function length (simplified)
            func_starts = list(re.finditer(r'^func\s+\w+|^def\s+\w+|^function\s+\w+', content, re.MULTILINE))
            for i, start in enumerate(func_starts):
                end_pos = func_starts[i+1].start() if i+1 < len(func_starts) else len(content)
                func_content = content[start.start():end_pos]
                lines = func_content.count('\n')
                if lines > 50:
                    line_num = content[:start.start()].count('\n') + 1
                    func_name = re.search(r'\w+', start.group()).group()
                    long_functions.append({
                        "file": rel_path,
                        "line": line_num,
                        "name": func_name,
                        "lines": lines,
                    })
        
        # Generate report
        total_todos = len(debt["todo"])
        total_issues = sum(len(v) for v in debt.values()) + len(long_functions)
        
        content = f"""# Technical Debt Analysis

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- **TODOs/FIXMEs**: {total_todos}
- **Long Functions (>50 lines)**: {len(long_functions)}
- **Ignored Errors**: {len(debt.get('error_handling', []))}
- **Deprecated Code**: {len(debt.get('deprecated', []))}
- **Total Issues**: {total_issues}

## TODOs and FIXMEs

| File | Line | Note |
|------|------|------|
"""
        for item in debt["todo"][:50]:
            content += f"| `{item['file']}` | {item['line']} | {item['text'][:60]} |\n"
        
        content += "\n## Long Functions (>50 lines)\n\n| File | Function | Lines |\n|------|----------|-------|\n"
        for item in sorted(long_functions, key=lambda x: -x['lines'])[:20]:
            content += f"| `{item['file']}` | {item['name']} | {item['lines']} |\n"
        
        content += "\n## Ignored Errors\n\n| File | Line |\n|------|------|\n"
        for item in debt.get("error_handling", [])[:30]:
            content += f"| `{item['file']}` | {item['line']} |\n"
        
        self._write_file("TECH_DEBT.md", content)
        print(f"   Found {total_todos} TODOs, {len(long_functions)} long functions")
    
    def scan_data_flow(self):
        """Trace data flow through the system."""
        print("🔄 Scanning for data flow patterns...")
        
        flows: Dict[str, List[Dict]] = {k: [] for k in self.DATA_FLOW_PATTERNS}
        
        for path in self._get_source_files():
            content = self._read_file(path)
            if not content:
                continue
            
            rel_path = str(path.relative_to(self.root_dir))
            
            for category, patterns in self.DATA_FLOW_PATTERNS.items():
                for pattern in patterns:
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count('\n') + 1
                        flows[category].append({
                            "file": rel_path,
                            "line": line_num,
                        })
        
        # Generate report
        content = f"""# Data Flow Analysis

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Stage | Occurrences |
|-------|-------------|
| Input (request parsing) | {len(flows['input'])} |
| Transformation (processing) | {len(flows['transformation'])} |
| Storage (database ops) | {len(flows['storage'])} |
| Output (responses) | {len(flows['output'])} |

## Data Flow Diagram

```mermaid
graph LR
    A[Input<br/>{len(flows['input'])}] --> B[Transform<br/>{len(flows['transformation'])}]
    B --> C[Storage<br/>{len(flows['storage'])}]
    B --> D[Output<br/>{len(flows['output'])}]
    C --> B
```

## Input Points (Request Handlers)

| File | Line |
|------|------|
"""
        for item in flows['input'][:30]:
            content += f"| `{item['file']}` | {item['line']} |\n"
        
        content += "\n## Storage Operations\n\n| File | Line |\n|------|------|\n"
        for item in flows['storage'][:30]:
            content += f"| `{item['file']}` | {item['line']} |\n"
        
        self._write_file("DATA_FLOW.md", content)
        print(f"   Mapped {sum(len(v) for v in flows.values())} data flow points")
    
    def scan_complexity(self):
        """Scan code complexity metrics."""
        print("📊 Scanning code complexity...")
        
        files_data: List[Dict] = []
        
        for path in self._get_source_files():
            content = self._read_file(path)
            if not content:
                continue
            
            rel_path = str(path.relative_to(self.root_dir))
            lines = content.count('\n')
            
            # Simple complexity metrics
            if_count = len(re.findall(r'\bif\b', content))
            for_count = len(re.findall(r'\bfor\b', content))
            switch_count = len(re.findall(r'\bswitch\b|\bcase\b', content))
            complexity = if_count + for_count + switch_count
            
            # Refined function count for different languages
            func_count = len(re.findall(r'\bfunc\s+\w+|def\s+\w+|\bfunction\s+\w+|(?:public|private|protected)\s+[\w<>]+\s+\w+\s*\(', content))
            
            files_data.append({
                "file": rel_path,
                "lines": lines,
                "functions": func_count,
                "complexity": complexity,
                "avg_complexity": complexity / max(func_count, 1),
            })
        
        # Sort by complexity
        files_data.sort(key=lambda x: -x['complexity'])
        
        total_lines = sum(f['lines'] for f in files_data)
        total_funcs = sum(f['functions'] for f in files_data)
        
        content = f"""# Code Complexity Analysis

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

- **Total Files**: {len(files_data)}
- **Total Lines**: {total_lines:,}
- **Total Functions**: {total_funcs}
- **Average File Size**: {total_lines // max(len(files_data), 1)} lines

## Most Complex Files

| File | Lines | Functions | Complexity |
|------|-------|-----------|------------|
"""
        for f in files_data[:30]:
            content += f"| `{f['file']}` | {f['lines']} | {f['functions']} | {f['complexity']} |\n"
        
        self._write_file("COMPLEXITY.md", content)
        print(f"   Analyzed {len(files_data)} files, {total_lines:,} lines")
    
    def _get_source_files(self) -> List[Path]:
        """Get all source files."""
        source_exts = {".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".cs", ".cpp", ".c", ".h", ".hpp"}
        exclude_dirs = {"node_modules", "vendor", ".git", "dist", "build", "__pycache__", "static"}
        
        files = []
        for path in self.root_dir.rglob("*"):
            if path.is_file() and path.suffix in source_exts:
                parts = path.relative_to(self.root_dir).parts
                if not any(ex in parts for ex in exclude_dirs):
                    files.append(path)
        
        return files
    
    def _read_file(self, path: Path) -> str:
        """Read file content safely."""
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except:
            return ""
    
    def _write_file(self, filename: str, content: str):
        """Write output file."""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"Generated: {path}")


def main():
    parser = argparse.ArgumentParser(description="Semantic code analysis")
    parser.add_argument("--all", action="store_true", help="Run all analyses")
    parser.add_argument("--business-rules", action="store_true", help="Business rules only")
    parser.add_argument("--security", action="store_true", help="Security analysis only")
    parser.add_argument("--tech-debt", action="store_true", help="Tech debt only")
    parser.add_argument("--data-flow", action="store_true", help="Data flow only")
    parser.add_argument("--complexity", action="store_true", help="Complexity only")
    parser.add_argument("--output", "-o", default="project-documentation/codebase-docs", help="Output dir")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Auto-append repo name if using default output path
    if args.output == "project-documentation/codebase-docs":
        repo_name = Path.cwd().name
        args.output = str(Path(args.output) / repo_name)
        if args.verbose:
            print(f"ℹ️  Output directory set to: {args.output}")

    scanner = SemanticScanner(Path.cwd(), Path(args.output), args.verbose)
    
    if args.all or not any([args.business_rules, args.security, args.tech_debt, args.data_flow, args.complexity]):
        scanner.scan_all()
    else:
        if args.business_rules:
            scanner.scan_business_rules()
        if args.security:
            scanner.scan_security()
        if args.tech_debt:
            scanner.scan_tech_debt()
        if args.data_flow:
            scanner.scan_data_flow()
        if args.complexity:
            scanner.scan_complexity()
    
    return 0


if __name__ == "__main__":
    exit(main())
