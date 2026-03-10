#!/usr/bin/env python3
"""
Generate Review Report Script
=============================
Generates a comprehensive code review report for a feature module by orchestrating multiple analysis tools.
This is the central tool for the Expert Code Reviewer.

It aggregates results from:
1. validate_architecture.py (Structure & Dependency Rules)
2. check_anti_patterns.py (Common Mistakes)
3. Expert Go: validate_production_ready.py (Go Quality)
4. Expert Go: analyze_code.py (Go Architecture)
5. Expert React: validate_frontend_architecture.py (React Quality)

Usage:
    python generate_review_report.py --feature <feature_name>
    python generate_review_report.py --be-path features/iov --fe-path apps/frontend/src/iov
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# === CONFIGURATION ===
SKILLS_ROOT = Path(__file__).parent.parent.parent

SCRIPTS = {
    "arch": SKILLS_ROOT / "expert-code-reviewer" / "scripts" / "validate_architecture.py",
    "anti": SKILLS_ROOT / "expert-code-reviewer" / "scripts" / "check_anti_patterns.py",
    "go_prod": SKILLS_ROOT / "expert-go-backend-developer" / "scripts" / "validate_production_ready.py",
    "go_analyze": SKILLS_ROOT / "expert-go-backend-developer" / "scripts" / "analyze_code.py",
    "go_ctx": SKILLS_ROOT / "expert-go-backend-developer" / "scripts" / "validate_context_propagation.py",
    "go_err": SKILLS_ROOT / "expert-go-backend-developer" / "scripts" / "validate_error_handling.py",
    "react_arch": SKILLS_ROOT / "expert-react-frontend-developer" / "scripts" / "validate_frontend_architecture.py",
    "contracts": SKILLS_ROOT / "expert-code-reviewer" / "scripts" / "compare_api_contracts.py",
}

class Issue:
    def __init__(self, severity: str, message: str, file: str, line: int, category: str, rule: str = ""):
        self.severity = severity.upper()  # CRITICAL, ERROR, WARNING, SUGGESTION
        self.message = message
        self.file = file
        self.line = line
        self.category = category
        self.rule = rule

def run_json_command(script_path: Path, target_path: str, extra_args: List[str] = []) -> Dict[str, Any]:
    """Run a script with --json and return parsed output."""
    if not os.path.exists(script_path):
        return {"error": f"Script not found: {script_path}"}
        
    cmd = [sys.executable, str(script_path), target_path, "--json"] + extra_args
    try:
        # Run command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        # Parse JSON from stdout
        output = result.stdout.strip()
        if not output:
             return {"error": "Empty output", "stderr": result.stderr}
             
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # Sometimes scripts print other things before JSON
            # Try to find the JSON blob
            match_start = output.find('{')
            match_end = output.rfind('}')
            if match_start != -1 and match_end != -1:
                try:
                    return json.loads(output[match_start:match_end+1])
                except:
                    pass
            return {"error": "Invalid JSON", "raw": output, "stderr": result.stderr}
            
    except Exception as e:
        return {"error": str(e)}

def normalize_issues(tool_name: str, data: Dict[str, Any]) -> List[Issue]:
    """Normalize output from different tools into a standard Issue format."""
    issues = []
    
    if "error" in data:
        print(f"Warning: Tool {tool_name} failed: {data['error']}", file=sys.stderr)
        return []

    # 1. validate_architecture.py
    if tool_name == "arch":
        for v in data.get("violations", []):
            issues.append(Issue(
                severity="CRITICAL" if v.get("severity") == "ERROR" else "WARNING",
                message=v.get("message"),
                file=v.get("file"),
                line=v.get("line"),
                category="Architecture",
                rule="arch-violation"
            ))

    # 2. check_anti_patterns.py - Returns List[Dict] directly usually, or wrapped
    elif tool_name == "anti":
        # Check if data is list or dict
        items = data if isinstance(data, list) else data.get("issues", [])
        for i in items:
            sev = i.get("severity", "WARNING").replace("🔴 ", "").replace("🟡 ", "").replace("🔵 ", "").upper()
            if "CRITICAL" in sev: sev = "CRITICAL"
            elif "WARNING" in sev: sev = "WARNING"
            elif "SUGGESTION" in sev: sev = "SUGGESTION"
            
            issues.append(Issue(
                severity=sev,
                message=i.get("message"),
                file=i.get("file"),
                line=i.get("line"),
                category=i.get("category", "Code Pattern"),
                rule=i.get("message") # Use message as rule identifier
            ))

    # 3. validate_production_ready.py (Go)
    elif tool_name == "go_prod":
        for v in data.get("violations", []):
            sev = v.get("severity", "WARNING")
            if sev == "ERROR": sev = "CRITICAL" # Treat errors here as critical
            issues.append(Issue(
                severity=sev,
                message=v.get("message"),
                file=v.get("file"),
                line=v.get("line"),
                category="Production Ready",
                rule=v.get("rule")
            ))

    # 4. analyze_code.py (Go)
    elif tool_name == "go_analyze":
        for i in data.get("issues", []):
            sev = i.get("severity", "WARNING")
            if sev == "ERROR": sev = "CRITICAL"
            issues.append(Issue(
                severity=sev,
                message=i.get("message"),
                file=i.get("file"),
                line=i.get("line"),
                category="Go Best Practices",
                rule=i.get("rule")
            ))

    # 5. validate_context_propagation.py (Go)
    elif tool_name == "go_ctx":
        for v in data.get("violations", []):
            issues.append(Issue(
                severity="CRITICAL",
                message=v.get("message"),
                file=v.get("file"),
                line=v.get("line"),
                category="Context Propagation",
                rule="context-background"
            ))

    # 6. validate_error_handling.py (Go)
    elif tool_name == "go_err":
        for v in data.get("violations", []):
            issues.append(Issue(
                severity="CRITICAL", # These are mandatory
                message=v.get("message"),
                file=v.get("file"),
                line=v.get("line"),
                category="Error Handling",
                rule=v.get("rule", "error-handling")
            ))

    # 7. validate_frontend_architecture.py (React)
    elif tool_name == "react_arch":
        for err in data.get("errors", []):
            # Format: "Avoid 'any' type in path/to/file:10. ..."
            # Need strict parsing or generic fallback
            parts = err.split(":")
            msg = err
            line = 0
            if len(parts) >= 2 and parts[-1].strip().isdigit(): # heuristic
                 # difficult to parse strictly without regex, simplifying
                 pass
            
            issues.append(Issue(
                severity="CRITICAL",
                message=err.replace("🔴 ERROR: ", ""),
                file="<unknown>", # Tool output needs improvement for strict parsing, but ok for now
                line=0,
                category="Frontend Architecture",
                rule="fe-arch"
            ))
        for warn in data.get("warnings", []):
             issues.append(Issue(
                severity="WARNING",
                message=warn.replace("🟡 WARNING: ", ""),
                file="<unknown>",
                line=0,
                category="Frontend Architecture",
                rule="fe-arch"
            ))

    # 8. API Contracts comparison
    elif tool_name == "contracts":
        for i in data.get("issues", []):
            sev = i.get("severity", "WARNING")
            issues.append(Issue(
                severity=sev,
                message=i.get("message"),
                file="API Contract",
                line=0,
                category="API Contract",
                rule="contract-mismatch"
            ))

    return issues

def find_project_root() -> str:
    current = Path.cwd()
    while current != current.parent:
        if (current / "go.mod").exists():
            return str(current)
        current = current.parent
    return str(Path.cwd())

def main():
    parser = argparse.ArgumentParser(description="Generate Comprehensive Code Review Report")
    parser.add_argument("--feature", help="Feature name")
    parser.add_argument("--be-path", help="Backend path")
    parser.add_argument("--fe-path", help="Frontend path")
    parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args()
    project_root = find_project_root()
    
    # Path Resolution
    be_path = args.be_path
    fe_path = args.fe_path
    feature_name = args.feature or "Unknown Feature"
    
    if args.feature:
        be_p = os.path.join(project_root, "features", args.feature)
        if os.path.exists(be_p): be_path = be_p
        
        fe_p = os.path.join(project_root, "apps", "frontend", "src", args.feature)
        if os.path.exists(fe_p): fe_path = fe_p
    
    if not be_path and not fe_path:
        print("Error: Provide --feature or paths.", file=sys.stderr)
        sys.exit(1)

    print(f"Generating Review Report for '{feature_name}'...")
    all_issues: List[Issue] = []

    # === RUN TOOLS ===

    # 1. Architecture Check (Generic)
    if be_path:
        print("Running Architecture Check (BE)...")
        all_issues.extend(normalize_issues("arch", run_json_command(SCRIPTS["arch"], be_path)))
    if fe_path:
        print("Running Architecture Check (FE)...")
        all_issues.extend(normalize_issues("arch", run_json_command(SCRIPTS["arch"], fe_path)))
        
    # 2. Anti-Patterns (Generic)
    if be_path:
        print("Running Anti-Patterns (BE)...")
        all_issues.extend(normalize_issues("anti", run_json_command(SCRIPTS["anti"], be_path, ["--type", "go"])))
    if fe_path:
        print("Running Anti-Patterns (FE)...")
        all_issues.extend(normalize_issues("anti", run_json_command(SCRIPTS["anti"], fe_path, ["--type", "ts"])))

    # 3. Go Specifics
    if be_path:
        print("Running Go Production Ready Check...")
        all_issues.extend(normalize_issues("go_prod", run_json_command(SCRIPTS["go_prod"], be_path)))
        print("Running Go Context Propagation Check...")
        all_issues.extend(normalize_issues("go_ctx", run_json_command(SCRIPTS["go_ctx"], be_path)))
        print("Running Go Error Handling Check...")
        all_issues.extend(normalize_issues("go_err", run_json_command(SCRIPTS["go_err"], be_path)))
        print("Running Go Analysis...")
        all_issues.extend(normalize_issues("go_analyze", run_json_command(SCRIPTS["go_analyze"], be_path)))

    # 4. React Specifics
    if fe_path:
        print("Running Frontend Architecture Check...")
        all_issues.extend(normalize_issues("react_arch", run_json_command(SCRIPTS["react_arch"], fe_path)))

    # 5. API Contracts
    if be_path and fe_path:
        print("Running API Contract Comparison...")
        # Need to point to models dir if possible
        be_models = os.path.join(be_path, "models")
        if not os.path.exists(be_models): be_models = be_path
        
        fe_models = os.path.join(fe_path, "core", "models")
        if not os.path.exists(fe_models): fe_models = fe_path
        
        all_issues.extend(normalize_issues("contracts", run_json_command(SCRIPTS["contracts"], "", ["--go-dir", be_models, "--zod-dir", fe_models])))

    # === GENERATE REPORT ===
    
    # Deduplicate issues (same file + line + message)
    unique_issues = {}
    for i in all_issues:
        key = f"{i.file}:{i.line}:{i.message}"
        if key not in unique_issues:
            unique_issues[key] = i
        else:
            # Upgrade severity if dup found
            if i.severity == "CRITICAL" and unique_issues[key].severity != "CRITICAL":
                unique_issues[key].severity = "CRITICAL"
    
    final_issues = list(unique_issues.values())
    
    # Sort: Critical -> Warning -> Suggestion
    sev_order = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2, "SUGGESTION": 3}
    final_issues.sort(key=lambda x: (sev_order.get(x.severity, 4), x.file, x.line))

    # Counts
    counts = {"CRITICAL": 0, "WARNING": 0, "SUGGESTION": 0}
    for i in final_issues:
        s = i.severity
        if s == "ERROR": s = "CRITICAL"
        counts[s] = counts.get(s, 0) + 1
        
    status = "✅ APPROVE"
    if counts["CRITICAL"] > 0: status = "❌ REJECT"
    elif counts["WARNING"] > 5: status = "🔄 REQUEST CHANGES"

    # Markdown Construction
    md = f"""# Code Review Report: {feature_name}

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Status**: {status}

## Summary
| Severity | Count |
|----------|-------|
| 🔴 **Critical** | {counts["CRITICAL"]} |
| 🟡 **Warning** | {counts["WARNING"]} |
| 🔵 **Suggestion** | {counts["SUGGESTION"]} |

---

"""

    if counts["CRITICAL"] > 0:
        md += "## 🔴 Critical Issues (MUST FIX)\n\n"
        for i in final_issues:
            if i.severity in ["CRITICAL", "ERROR"]:
                md += f"### [{i.category}] {i.message}\n"
                md += f"- **File**: `{i.file}:{i.line}`\n"
                if i.rule: md += f"- **Rule**: `{i.rule}`\n"
                md += "\n"

    if counts["WARNING"] > 0:
        md += "## 🟡 Warnings (SHOULD FIX)\n\n"
        count = 0
        for i in final_issues:
            if i.severity == "WARNING":
                if count >= 15:
                    md +=f"\n... and {counts['WARNING'] - 15} more warnings.\n"
                    break
                md += f"- `{i.file}:{i.line}`: {i.message} `[{i.category}]`\n"
                count += 1
        md += "\n"

    if counts["SUGGESTION"] > 0:
        md += "## 🔵 Suggestions\n\n"
        for i in final_issues:
            if i.severity == "SUGGESTION":
                md += f"- {i.message}\n"
        md += "\n"

    md += """---
## Verification Commands

To verify fixes, run:
```bash
# Architecture
python .github/skills/expert-code-reviewer/scripts/validate_architecture.py --path <feature_path>

# Backend
python .github/skills/expert-go-backend-developer/scripts/validate_production_ready.py <backend_path>
python .github/skills/expert-go-backend-developer/scripts/validate_context_propagation.py <backend_path>/controllers
python .github/skills/expert-go-backend-developer/scripts/validate_error_handling.py <backend_path>

# Frontend
python .github/skills/expert-react-frontend-developer/scripts/validate_frontend_architecture.py <frontend_path>
```
"""

    output_path = args.output
    if not output_path and args.feature:
        output_path = os.path.join("project-documentation", "report-review", args.feature, "REVIEW_REPORT.md")

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Report saved to {output_path}")
    else:
        print(md)

if __name__ == "__main__":
    main()
