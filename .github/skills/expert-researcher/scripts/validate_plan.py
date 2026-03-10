#!/usr/bin/env python3
"""
Plan Validator
Validates implementation plans for completeness and consistency.
Ensures plans have all required sections to prevent ambiguity for BE/FE developers.
"""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "executive_summary": {
        "pattern": r"##\s*1\.\s*Executive Summary",
        "description": "Executive Summary with Objective and Scope",
        "subsections": ["objective", "scope"]
    },
    "backend_design": {
        "pattern": r"###\s*Backend Design|###\s*2\.1.*Backend",
        "description": "Backend Design with Go module and interfaces",
        "subsections": ["module", "interfaces", "dependencies"]
    },
    "frontend_design": {
        "pattern": r"###\s*Frontend Design|###\s*2\.2.*Frontend", 
        "description": "Frontend Design with Feature Slice and Components",
        "subsections": ["feature slice", "state management", "component"]
    },
    "api_contracts": {
        "pattern": r"###\s*API Contracts|##\s*3\.\s*Data Dictionary",
        "description": "API Contracts with exact endpoints",
        "subsections": ["request", "response", "method", "path"]
    },
    "go_structs": {
        "pattern": r"```go[\s\S]*?type\s+\w+\s+struct",
        "description": "Go struct definitions with json tags",
        "subsections": []
    },
    "zod_schemas": {
        "pattern": r"```typescript[\s\S]*?z\.object\(|z\.string\(\)|z\.number\(\)",
        "description": "Zod schema definitions for Frontend",
        "subsections": []
    },
    "implementation_steps": {
        "pattern": r"##\s*4\.\s*Implementation Steps|###\s*Phase\s*\d",
        "description": "Step-by-step implementation guide",
        "subsections": ["backend", "frontend"]
    }
}

COMPLETENESS_CHECKS = [
    {
        "name": "API Endpoint Path",
        "pattern": r"(GET|POST|PUT|PATCH|DELETE)\s+/api/v\d+/\w+",
        "message": "API endpoints should have exact paths (e.g., POST /api/v1/users)"
    },
    {
        "name": "Go JSON Tags",
        "pattern": r"`json:\"[a-z_]+\"`",
        "message": "Go structs should have json tags for field mapping"
    },
    {
        "name": "Request/Response Examples",
        "pattern": r"\*\*Request\*\*:.*\{|\*\*Response\*\*:.*\{",
        "message": "Include example Request/Response JSON bodies"
    },
    {
        "name": "Field Types Specified",
        "pattern": r"(string|number|boolean|int|int64|float64|\[\]|map\[)",
        "message": "Field types should be explicitly specified"
    },
    {
        "name": "Feature Directory",
        "pattern": r"features/[a-z_]+|apps/frontend/src/[a-z_]+",
        "message": "Specify exact feature directory paths"
    },
    {
        "name": "Component Names",
        "pattern": r"[A-Z][a-zA-Z]+Component|[A-Z][a-zA-Z]+Panel|[A-Z][a-zA-Z]+Page",
        "message": "Use PascalCase component names (e.g., UserListComponent)"
    },
    {
        "name": "Zustand Store",
        "pattern": r"(store|Store|useStore|zustand)",
        "message": "Mention Zustand store strategy for state management"
    },
    {
        "name": "Error Handling",
        "pattern": r"(error|Error|ErrNotFound|400|401|404|500)",
        "message": "Include error handling considerations"
    },
    {
        "name": "Backend Scaffold Script",
        "pattern": r"scaffold_feature\.py.*go-backend",
        "message": "Plan must include running backend scaffold_feature.py"
    },
    {
        "name": "Frontend Scaffold Script",
        "pattern": r"scaffold_feature\.py.*react-frontend",
        "message": "Plan must include running frontend scaffold_feature.py"
    },
    {
        "name": "DI Wiring Script",
        "pattern": r"generate_di_wiring\.py",
        "message": "Plan must include running generate_di_wiring.py"
    },
    {
        "name": "API Extraction Script",
        "pattern": r"extract_go_api\.py",
        "message": "Plan must include running extract_go_api.py for contract alignment"
    }
]

USE_CASE_PATTERNS = [
    {
        "name": "Happy Path",
        "pattern": r"(success|successful|when.*valid|正常|happy)",
        "importance": "CRITICAL"
    },
    {
        "name": "Validation Error",
        "pattern": r"(invalid|validation|required field|missing)",
        "importance": "HIGH"
    },
    {
        "name": "Not Found",
        "pattern": r"(not found|doesn't exist|404)",
        "importance": "HIGH"
    },
    {
        "name": "Unauthorized",
        "pattern": r"(unauthorized|401|permission|access denied)",
        "importance": "MEDIUM"
    },
    {
        "name": "Edge Cases",
        "pattern": r"(edge case|boundary|empty|null|zero)",
        "importance": "MEDIUM"
    }
]

def validate_plan(content: str) -> dict:
    """Validate plan content and return results."""
    results = {
        "sections": {},
        "completeness": {},
        "use_cases": {},
        "score": 0,
        "max_score": 0,
        "issues": [],
        "warnings": []
    }
    
    # Check required sections
    for section_id, section_info in REQUIRED_SECTIONS.items():
        found = bool(re.search(section_info["pattern"], content, re.IGNORECASE))
        results["sections"][section_id] = {
            "found": found,
            "description": section_info["description"]
        }
        results["max_score"] += 10
        if found:
            results["score"] += 10
        else:
            results["issues"].append(f"Missing: {section_info['description']}")
    
    # Check completeness
    for check in COMPLETENESS_CHECKS:
        found = bool(re.search(check["pattern"], content, re.IGNORECASE))
        results["completeness"][check["name"]] = found
        results["max_score"] += 5
        if found:
            results["score"] += 5
        else:
            results["warnings"].append(f"Consider adding: {check['message']}")
    
    # Check use case coverage
    for uc in USE_CASE_PATTERNS:
        found = bool(re.search(uc["pattern"], content, re.IGNORECASE))
        results["use_cases"][uc["name"]] = {
            "found": found,
            "importance": uc["importance"]
        }
        if uc["importance"] == "CRITICAL":
            results["max_score"] += 10
            if found:
                results["score"] += 10
            else:
                results["issues"].append(f"Missing use case: {uc['name']} ({uc['importance']})")
        else:
            results["max_score"] += 3
            if found:
                results["score"] += 3
    
    return results

def print_report(results: dict, verbose: bool = False):
    """Print validation report."""
    percentage = (results["score"] / results["max_score"] * 100) if results["max_score"] > 0 else 0
    
    print("\n" + "=" * 60)
    print("   IMPLEMENTATION PLAN VALIDATION REPORT")
    print("=" * 60)
    
    # Score
    if percentage >= 80:
        status = "✅ PASS"
        color = "\033[92m"
    elif percentage >= 60:
        status = "⚠️  NEEDS IMPROVEMENT"
        color = "\033[93m"
    else:
        status = "❌ FAIL"
        color = "\033[91m"
    
    print(f"\n{color}Score: {results['score']}/{results['max_score']} ({percentage:.1f}%) - {status}\033[0m")
    
    # Required Sections
    print("\n--- Required Sections ---")
    for section_id, info in results["sections"].items():
        icon = "✓" if info["found"] else "✗"
        print(f"  [{icon}] {info['description']}")
    
    # Completeness
    if verbose:
        print("\n--- Completeness Checks ---")
        for name, found in results["completeness"].items():
            icon = "✓" if found else "○"
            print(f"  [{icon}] {name}")
    
    # Use Cases
    print("\n--- Use Case Coverage ---")
    for name, info in results["use_cases"].items():
        icon = "✓" if info["found"] else "○"
        print(f"  [{icon}] {name} ({info['importance']})")
    
    # Issues
    if results["issues"]:
        print("\n--- Issues (MUST FIX) ---")
        for issue in results["issues"]:
            print(f"  ❌ {issue}")
    
    # Warnings
    if results["warnings"] and verbose:
        print("\n--- Warnings (Recommended) ---")
        for warning in results["warnings"]:
            print(f"  ⚠️  {warning}")
    
    print("\n" + "=" * 60)
    
    return percentage >= 60

def main():
    parser = argparse.ArgumentParser(description="Validate implementation plan completeness")
    parser.add_argument("file", help="Path to markdown plan file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed report")
    parser.add_argument("--strict", action="store_true", help="Return non-zero exit code if score less than 80 percent")
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[!] File not found: {args.file}")
        sys.exit(1)
    
    content = file_path.read_text(encoding="utf-8")
    results = validate_plan(content)
    passed = print_report(results, args.verbose)
    
    if args.strict:
        percentage = (results["score"] / results["max_score"] * 100)
        sys.exit(0 if percentage >= 80 else 1)
    else:
        sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
