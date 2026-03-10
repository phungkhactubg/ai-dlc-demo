#!/usr/bin/env python3
"""
Architecture Validation Script
==============================

Validate architecture documents against best practices and standards.

Usage:
    python validate_architecture.py plan.md
    python validate_architecture.py --strict plan.md
    python validate_architecture.py --checklist
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.passed: List[str] = []
    
    def add_error(self, msg: str):
        self.errors.append(f"❌ ERROR: {msg}")
    
    def add_warning(self, msg: str):
        self.warnings.append(f"⚠️  WARNING: {msg}")
    
    def add_info(self, msg: str):
        self.info.append(f"ℹ️  INFO: {msg}")
    
    def add_passed(self, msg: str):
        self.passed.append(f"✅ PASS: {msg}")
    
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def print_report(self):
        print("\n" + "=" * 60)
        print("ARCHITECTURE VALIDATION REPORT")
        print("=" * 60 + "\n")
        
        for msg in self.passed:
            print(msg)
        
        if self.info:
            print()
            for msg in self.info:
                print(msg)
        
        if self.warnings:
            print()
            for msg in self.warnings:
                print(msg)
        
        if self.errors:
            print()
            for msg in self.errors:
                print(msg)
        
        print("\n" + "-" * 60)
        print(f"Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")
        
        if self.is_valid():
            print("\n✅ Architecture document is VALID")
        else:
            print("\n❌ Architecture document has ERRORS")


def read_document(path: str) -> str:
    """Read document content."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        sys.exit(1)


def check_required_sections(content: str, result: ValidationResult):
    """Check for required sections in architecture document."""
    required_sections = [
        ("Executive Summary", r"##?\s*(Executive\s+Summary|1\.\s*Executive)"),
        ("Technical Architecture", r"##?\s*(Technical\s+Architecture|2\.\s*Technical)"),
        ("Data Models", r"##?\s*(Data\s+Models?|3\.\s*Data)"),
        ("API Contracts", r"##?\s*(API\s+Contracts?|4\.\s*API)"),
        ("Implementation Steps", r"##?\s*(Implementation\s+Steps?|5\.\s*Implementation)"),
    ]
    
    for section_name, pattern in required_sections:
        if re.search(pattern, content, re.IGNORECASE):
            result.add_passed(f"Section '{section_name}' found")
        else:
            result.add_warning(f"Section '{section_name}' not found")


def check_go_struct_definitions(content: str, result: ValidationResult):
    """Validate Go struct definitions."""
    # Check for Go code blocks
    go_blocks = re.findall(r"```go\n(.*?)```", content, re.DOTALL)
    
    if not go_blocks:
        result.add_warning("No Go code examples found")
        return
    
    result.add_passed(f"Found {len(go_blocks)} Go code blocks")
    
    for i, block in enumerate(go_blocks, 1):
        # Check for JSON tags
        if "type" in block and "struct" in block:
            if 'json:"' not in block:
                result.add_warning(f"Go struct in block {i} missing JSON tags")
            else:
                result.add_passed(f"Block {i}: Struct has JSON tags")
        
        # Check for context.Context
        if "func" in block and "ctx" not in block.lower():
            if "context" not in block.lower():
                result.add_info(f"Block {i}: Consider adding context.Context parameter")


def check_api_endpoints(content: str, result: ValidationResult):
    """Check API endpoint definitions."""
    # Look for HTTP methods
    http_patterns = [
        (r"(?:POST|GET|PUT|DELETE|PATCH)\s+/api/", "REST endpoints"),
        (r"\|.*?Method.*?\|.*?Path.*?\|", "API table format"),
    ]
    
    has_endpoints = False
    for pattern, name in http_patterns:
        if re.search(pattern, content):
            result.add_passed(f"API endpoints documented ({name})")
            has_endpoints = True
            break
    
    if not has_endpoints:
        result.add_warning("No API endpoints found in document")
    
    # Check for error response documentation
    if re.search(r"(error|4\d{2}|5\d{2})", content, re.IGNORECASE):
        result.add_passed("Error responses documented")
    else:
        result.add_warning("Error responses not documented")


def check_database_schema(content: str, result: ValidationResult):
    """Check database schema definitions."""
    # Look for collection/table definitions
    if re.search(r"(collection|table)", content, re.IGNORECASE):
        result.add_passed("Database schema documented")
    else:
        result.add_warning("No database schema found")
    
    # Check for indexes
    if re.search(r"index(es)?", content, re.IGNORECASE):
        result.add_passed("Database indexes documented")
    else:
        result.add_info("Consider documenting database indexes")
    
    # Check for tenant_id (multi-tenancy)
    if re.search(r"tenant[_\s]?id", content, re.IGNORECASE):
        result.add_passed("Multi-tenancy field (tenant_id) documented")
    else:
        result.add_warning("Multi-tenancy (tenant_id) not mentioned")


def check_implementation_checklist(content: str, result: ValidationResult):
    """Check for implementation checklist."""
    # Check for task lists
    checkboxes = re.findall(r"- \[([ xX])\]", content)
    
    if checkboxes:
        result.add_passed(f"Found {len(checkboxes)} checklist items")
    else:
        result.add_warning("No implementation checklist found")


def check_diagrams(content: str, result: ValidationResult):
    """Check for architecture diagrams."""
    if "```mermaid" in content:
        mermaid_count = content.count("```mermaid")
        result.add_passed(f"Found {mermaid_count} Mermaid diagram(s)")
    else:
        result.add_info("Consider adding Mermaid diagrams for visualization")


def check_clean_architecture_compliance(content: str, result: ValidationResult):
    """Check for Clean Architecture patterns."""
    patterns = {
        "Interface-First": r"(interface|Interface\s*\{)",
        "Repository Pattern": r"(repository|Repository)",
        "Service Layer": r"(service|Service)",
        "Controller Layer": r"(controller|Controller|handler|Handler)",
        "Domain/Models": r"(model|Model|entity|Entity|domain|Domain)",
    }
    
    found = []
    missing = []
    
    for name, pattern in patterns.items():
        if re.search(pattern, content):
            found.append(name)
        else:
            missing.append(name)
    
    if found:
        result.add_passed(f"Clean Architecture patterns: {', '.join(found)}")
    
    if missing:
        result.add_info(f"Patterns not explicitly mentioned: {', '.join(missing)}")


def check_security_considerations(content: str, result: ValidationResult):
    """Check for security documentation."""
    security_keywords = [
        "auth", "authentication", "authorization",
        "jwt", "token", "credential",
        "validation", "sanitize", "injection",
        "permission", "role", "access"
    ]
    
    found = [kw for kw in security_keywords if kw.lower() in content.lower()]
    
    if len(found) >= 3:
        result.add_passed(f"Security considerations documented ({len(found)} keywords)")
    elif found:
        result.add_warning(f"Limited security documentation ({len(found)} keywords)")
    else:
        result.add_error("No security considerations documented")


def check_error_handling(content: str, result: ValidationResult):
    """Check for error handling documentation."""
    error_patterns = [
        r"fmt\.Errorf",
        r"errors\.Is",
        r"errors\.As",
        r"ErrNotFound",
        r"error\s+handling",
    ]
    
    found = any(re.search(p, content) for p in error_patterns)
    
    if found:
        result.add_passed("Error handling patterns documented")
    else:
        result.add_warning("Error handling not explicitly documented")


def print_checklist():
    """Print validation checklist."""
    print("""
ARCHITECTURE DOCUMENT CHECKLIST
================================

Required Sections:
  [ ] Executive Summary (objective, scope, dependencies)
  [ ] Technical Architecture (component diagram, directory structure)
  [ ] Data Models (database schema, Go structs with JSON tags)
  [ ] API Contracts (endpoints, request/response, error codes)
  [ ] Implementation Steps (numbered tasks with checkboxes)

Best Practices:
  [ ] Multi-tenancy (tenant_id in all data models)
  [ ] Context propagation (context.Context in function signatures)
  [ ] Interface-first design (service interfaces defined)
  [ ] Error wrapping (fmt.Errorf with %w)
  [ ] Security considerations (auth, validation, sanitization)

Visual Aids:
  [ ] Component diagram (Mermaid)
  [ ] Sequence diagram for key flows
  [ ] Data flow diagram

Quality:
  [ ] No TODOs or placeholders
  [ ] Verification checklist
  [ ] Risk assessment
  [ ] Rollback plan
""")


def validate_document(path: str, strict: bool = False) -> bool:
    """Validate architecture document."""
    content = read_document(path)
    result = ValidationResult()
    
    print(f"\nValidating: {path}\n")
    
    # Run all checks
    check_required_sections(content, result)
    check_go_struct_definitions(content, result)
    check_api_endpoints(content, result)
    check_database_schema(content, result)
    check_implementation_checklist(content, result)
    check_diagrams(content, result)
    check_clean_architecture_compliance(content, result)
    check_security_considerations(content, result)
    check_error_handling(content, result)
    
    # In strict mode, warnings become errors
    if strict:
        for warning in result.warnings:
            result.errors.append(warning.replace("WARNING", "ERROR"))
        result.warnings = []
    
    result.print_report()
    return result.is_valid()


def main():
    parser = argparse.ArgumentParser(
        description="Validate architecture documents against best practices"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to architecture document"
    )
    parser.add_argument(
        "--strict", "-s",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--checklist", "-c",
        action="store_true",
        help="Print validation checklist"
    )
    
    args = parser.parse_args()
    
    if args.checklist:
        print_checklist()
        return
    
    if not args.file:
        parser.print_help()
        return
    
    is_valid = validate_document(args.file, args.strict)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
