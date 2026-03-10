#!/usr/bin/env python3
"""
Plan Validation Script
======================

Validate implementation plans against quality rules.

Usage:
    python validate_plan.py plan.md
    python validate_plan.py plan.md --strict
    python validate_plan.py --rules
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class PlanValidator:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.passed: List[str] = []
    
    def validate(self, content: str) -> bool:
        """Run all validation checks."""
        self._check_required_sections(content)
        self._check_data_models(content)
        self._check_api_contracts(content)
        self._check_use_cases(content)
        self._check_implementation_steps(content)
        self._check_verification_checklist(content)
        self._check_go_structs(content)
        self._check_zod_schemas(content)
        self._check_no_ambiguous_types(content)
        self._check_json_tags(content)
        
        if self.strict:
            # In strict mode, warnings become errors
            self.errors.extend([w.replace("WARNING", "ERROR") for w in self.warnings])
            self.warnings = []
        
        return len(self.errors) == 0
    
    def _check_required_sections(self, content: str):
        """Check for required sections."""
        required = [
            ("Executive Summary", r"##?\s*(Executive\s+Summary|1\.\s*Executive)"),
            ("Technical Architecture", r"##?\s*(Technical\s+Architecture|2\.\s*Technical)"),
            ("Data Models", r"##?\s*(Data\s+(Models?|Dictionary)|3\.\s*Data)"),
            ("API Contracts", r"##?\s*(API\s+Contracts?|4\.\s*API)"),
            ("Use Cases", r"##?\s*(Use\s+Cases?|4\.\s*Use)"),
            ("Implementation Steps", r"##?\s*(Implementation\s+Steps?|5\.\s*Implementation)"),
            ("Verification", r"##?\s*(Verification|6\.\s*Verification)"),
        ]
        
        for name, pattern in required:
            if re.search(pattern, content, re.IGNORECASE):
                self.passed.append(f"Section '{name}' found")
            else:
                self.warnings.append(f"WARNING: Section '{name}' not found")
    
    def _check_data_models(self, content: str):
        """Check data model completeness."""
        # Check for field definitions
        if re.search(r"\|\s*Field\s*\|\s*Type\s*\|", content, re.IGNORECASE):
            self.passed.append("Data model field table found")
        else:
            self.warnings.append("WARNING: No field definition table found")
        
        # Check for database indexes
        if re.search(r"(index|indexes|createIndex)", content, re.IGNORECASE):
            self.passed.append("Database indexes documented")
        else:
            self.warnings.append("WARNING: Database indexes not documented")
        
        # Check for tenant_id (multi-tenancy)
        if re.search(r"tenant[_\s]?id", content, re.IGNORECASE):
            self.passed.append("Multi-tenancy (tenant_id) documented")
        else:
            self.errors.append("ERROR: Multi-tenancy (tenant_id) not found - required for this project")
    
    def _check_api_contracts(self, content: str):
        """Check API contract completeness."""
        # Check for endpoint table
        if re.search(r"\|\s*Method\s*\|\s*Path\s*\|", content, re.IGNORECASE):
            self.passed.append("API endpoint table found")
        else:
            self.warnings.append("WARNING: No API endpoint table found")
        
        # Check for request/response examples
        if re.search(r"(Request|Response)\s*(Body|Example)", content, re.IGNORECASE):
            self.passed.append("Request/Response examples found")
        else:
            self.warnings.append("WARNING: No request/response examples found")
        
        # Check for error responses
        error_codes = re.findall(r"\b(400|401|403|404|500)\b", content)
        if len(error_codes) >= 3:
            self.passed.append(f"Error codes documented ({len(set(error_codes))} unique codes)")
        else:
            self.warnings.append("WARNING: Insufficient error code documentation")
    
    def _check_use_cases(self, content: str):
        """Check use case coverage."""
        required_cases = [
            ("Happy Path", r"happy\s*path"),
            ("Validation Errors", r"validation\s*(error|case)"),
            ("Not Found", r"(not\s*found|404)"),
            ("Authorization", r"(auth|unauthorized|forbidden)"),
            ("Edge Cases", r"edge\s*case"),
        ]
        
        found = 0
        for name, pattern in required_cases:
            if re.search(pattern, content, re.IGNORECASE):
                found += 1
            else:
                self.warnings.append(f"WARNING: Use case '{name}' not documented")
        
        if found >= 4:
            self.passed.append(f"Use cases well documented ({found}/5)")
        elif found >= 2:
            self.info.append(f"INFO: Partial use case coverage ({found}/5)")
    
    def _check_implementation_steps(self, content: str):
        """Check implementation steps are actionable."""
        # Check for numbered or checkbox steps
        steps = re.findall(r"(?:^\d+\.\s*\[.\]|^-\s*\[.\])", content, re.MULTILINE)
        
        if len(steps) >= 5:
            self.passed.append(f"Implementation steps found ({len(steps)} steps)")
        elif len(steps) > 0:
            self.warnings.append(f"WARNING: Only {len(steps)} implementation steps")
        else:
            self.errors.append("ERROR: No implementation checklist found")
        
        # Check for script references
        if re.search(r"(python\s+scripts/|scaffold_feature|generate_)", content):
            self.passed.append("Script references found")
        else:
            self.info.append("INFO: Consider adding script references")
    
    def _check_verification_checklist(self, content: str):
        """Check for verification checklist."""
        verification_items = re.findall(r"-\s*\[.\]\s*.+", content)
        
        if len(verification_items) >= 5:
            self.passed.append(f"Verification checklist found ({len(verification_items)} items)")
        else:
            self.warnings.append("WARNING: Insufficient verification items")
    
    def _check_go_structs(self, content: str):
        """Check Go struct definitions."""
        go_blocks = re.findall(r"```go\n(.*?)```", content, re.DOTALL)
        
        if go_blocks:
            self.passed.append(f"Go code blocks found ({len(go_blocks)})")
            
            for i, block in enumerate(go_blocks, 1):
                # Check for struct definitions
                if "type" in block and "struct" in block:
                    # Check for JSON tags
                    if 'json:"' not in block:
                        self.errors.append(f"ERROR: Go struct in block {i} missing JSON tags")
                    else:
                        self.passed.append(f"Block {i}: Go struct has JSON tags")
                    
                    # Check for BSON tags (for MongoDB)
                    if 'bson:"' not in block and "mongo" in content.lower():
                        self.warnings.append(f"WARNING: Go struct in block {i} may need BSON tags")
        else:
            self.warnings.append("WARNING: No Go code examples found")
    
    def _check_zod_schemas(self, content: str):
        """Check Zod schema definitions."""
        ts_blocks = re.findall(r"```typescript\n(.*?)```", content, re.DOTALL)
        
        has_zod = any("z.object" in block or "z.string" in block for block in ts_blocks)
        
        if has_zod:
            self.passed.append("Zod schemas found")
        elif ts_blocks:
            self.info.append("INFO: TypeScript blocks found but no Zod schemas")
    
    def _check_no_ambiguous_types(self, content: str):
        """Check for ambiguous type definitions."""
        ambiguous = [
            (r":\s*object\b", "object → use specific type or map[string]any"),
            (r":\s*any\b", "any → use unknown or specific type"),
            (r"interface\s*\{\s*\}", "empty interface → define specific fields"),
        ]
        
        for pattern, suggestion in ambiguous:
            if re.search(pattern, content):
                self.warnings.append(f"WARNING: Ambiguous type found - {suggestion}")
    
    def _check_json_tags(self, content: str):
        """Check JSON tag consistency."""
        # Look for Go struct fields without json tags
        struct_fields = re.findall(r"\s+\w+\s+\w+\s*`[^`]*`", content)
        
        for field in struct_fields:
            if 'json:"' not in field and "bson:" not in field:
                self.warnings.append(f"WARNING: Field may be missing JSON tag: {field.strip()[:50]}")
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("PLAN VALIDATION REPORT")
        print("=" * 70 + "\n")
        
        for msg in self.passed:
            print(f"✅ {msg}")
        
        if self.info:
            print()
            for msg in self.info:
                print(f"ℹ️  {msg}")
        
        if self.warnings:
            print()
            for msg in self.warnings:
                print(f"⚠️  {msg}")
        
        if self.errors:
            print()
            for msg in self.errors:
                print(f"❌ {msg}")
        
        print("\n" + "-" * 70)
        print(f"Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")
        
        if len(self.errors) == 0:
            print("\n✅ Plan validation PASSED")
            return True
        else:
            print("\n❌ Plan validation FAILED")
            return False


def print_rules():
    """Print validation rules."""
    print("""
PLAN QUALITY RULES
==================

Rule 1: No Ambiguous Types
  ❌ BAD:  settings: object
  ✅ GOOD: settings: map[string]any (Go) → z.record(...) (Zod)

Rule 2: JSON Tags Required
  ❌ BAD:  CreatedAt time.Time
  ✅ GOOD: CreatedAt time.Time `json:"created_at"`

Rule 3: Complete Use Case Coverage
  Required sections:
  - [ ] Happy path (success scenarios)
  - [ ] Validation error cases
  - [ ] Not found cases
  - [ ] Authorization cases
  - [ ] At least 2 edge cases

Rule 4: Matching BE/FE Contracts
  - Go structs with JSON tags
  - Zod schemas that match exactly
  - Field names, types, and validation rules aligned

Rule 5: Atomic Implementation Steps
  Each step should:
  - Be completable in isolation
  - Have clear verification criteria
  - Reference specific files/directories
  - Include relevant script commands

Rule 6: Multi-Tenancy Required
  - All entities must have tenant_id
  - Queries must filter by tenant
  - Documented in data models

Rule 7: Error Responses Documented
  At minimum:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
  - 500 Internal Error
""")


def main():
    parser = argparse.ArgumentParser(
        description="Validate implementation plans"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to plan file"
    )
    parser.add_argument(
        "--strict", "-s",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--rules", "-r",
        action="store_true",
        help="Print validation rules"
    )
    
    args = parser.parse_args()
    
    if args.rules:
        print_rules()
        return
    
    if not args.file:
        parser.print_help()
        return
    
    try:
        content = Path(args.file).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    print(f"\nValidating: {args.file}")
    
    validator = PlanValidator(strict=args.strict)
    is_valid = validator.validate(content)
    validator.print_report()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
