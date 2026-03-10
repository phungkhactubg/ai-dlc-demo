#!/usr/bin/env python3
import os
import re
import argparse
import sys
import json
from typing import List, Dict, Tuple, Any

"""
Frontend Architecture & Quality Validator
-----------------------------------------
This script enforces architectural rules and code quality standards for the React Frontend.
It is designed to prevent common anti-patterns identified in code reviews.

Rules Enforced:
1. NO Direct Service Imports in Components: Components must use Hooks.
2. NO 'any' Type Usage: Strict type safety is required.
3. Component Size Limits: Components should be focused and small (< 250 lines).
4. Hook Size Limits: Hooks should be focused (< 200 lines).
5. Zod Validation Usage: Services must validata data (heuristic check).
"""

class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str):
        self.errors.append(f"🔴 ERROR: {message}")

    def add_warning(self, message: str):
        self.warnings.append(f"🟡 WARNING: {message}")

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def print_report(self):
        print("\n" + "="*50)
        print("🔍 FRONTEND ARCHITECTURE & QUALITY REPORT")
        print("="*50)
        
        if not self.errors and not self.warnings:
            print("\n✅ PASSED: No issues found. Great job!")
            return

        if self.errors:
            print(f"\nFound {len(self.errors)} Critical Issues:")
            for err in self.errors:
                print(err)
        
        if self.warnings:
            print(f"\nFound {len(self.warnings)} Warnings:")
            for warn in self.warnings:
                print(warn)
        
        print("\n" + "="*50)
        if self.errors:
            print("❌ VALIDATION FAILED")
            sys.exit(1)
        else:
            print("✅ VALIDATION PASSED (with warnings)")
            sys.exit(0)

    def to_json(self) -> Dict[str, Any]:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "success": len(self.errors) == 0
        }

class FrontendValidator:
    def __init__(self, root_path: str):
        self.root_path = os.path.abspath(root_path)
        self.result = ValidationResult()

    def validate(self):
        print(f"Starting validation in: {self.root_path}")
        for root, _, files in os.walk(self.root_path):
            if "node_modules" in root or ".git" in root or "dist" in root or "build" in root:
                continue
            
            for file in files:
                if not file.endswith(('.ts', '.tsx')):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.root_path)
                
                self._validate_file(file_path, rel_path, file)
        
        self.result.print_report()

    def _validate_file(self, file_path: str, rel_path: str, filename: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = "".join(lines)

        is_component = filename.endswith('.tsx') and not filename.startswith('use')
        is_hook = filename.startswith('use') and filename.endswith('.ts')
        is_service = 'service' in filename.lower() and filename.endswith('.ts')

        # 1. Check for 'any' usage (Exclude .test.ts/tsx and explicitly ignored lines)
        if not filename.endswith('.test.ts') and not filename.endswith('.test.tsx'):
             self._check_no_any(lines, rel_path)

        # 2. Check for Direct Service Imports in Components
        if is_component:
            self._check_direct_service_imports(lines, rel_path)
            # 3. Check Component Size
            if len(lines) > 250:
                self.result.add_warning(f"Component too large: {rel_path} ({len(lines)} lines). Consider breaking it down.")

        # 4. Check Hook Size
        if is_hook and len(lines) > 200:
            self.result.add_warning(f"Hook too large: {rel_path} ({len(lines)} lines). Consider splitting logic.")

        # 5. Check Service Zod Usage (Heuristic)
        if is_service:
            self._check_service_zod_usage(content, rel_path)

    def _check_no_any(self, lines: List[str], rel_path: str):
        # Regex to find ': any' or 'as any' or '<any>'
        # Very basic regex, might have false positives in string literals, but good enough for enforcement
        any_pattern = re.compile(r':\s*any\b|as\s+any\b|<\s*any\s*>')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('//') or 'eslint-disable' in stripped or 'ts-ignore' in stripped:
                continue
                
            if any_pattern.search(line):
                # Check if it's really a type definition or usage
                self.result.add_error(f"Avoid 'any' type in {rel_path}:{i+1}. Use 'unknown', generics, or specific types.")

    def _check_direct_service_imports(self, lines: List[str], rel_path: str):
        # Pattern to catch imports from infrastructure/services
        # e.g., import { XService } from '../../infrastructure/services/XService';
        service_import_pattern = re.compile(r'from\s+[\'"].*infrastructure\/services\/.*[\'"]')
        
        for i, line in enumerate(lines):
            if service_import_pattern.search(line):
                self.result.add_error(f"Violation: Direct service import in Component at {rel_path}:{i+1}. Use a custom hook instead.")

    def _check_service_zod_usage(self, content: str, rel_path: str):
        # Simple heuristic: excessive use of 'any' or missing 'parse' usually indicates lack of validation
        # Ideally, we want to see .parse( or .safeParse(
        if '.parse(' not in content and '.safeParse(' not in content:
            self.result.add_warning(f"Service might be missing Zod validation: {rel_path}. No '.parse()' or '.safeParse()' found.")

def main():
    parser = argparse.ArgumentParser(description="Validate Frontend Architecture & Code Quality")
    parser.add_argument("path", help="Path to the directory to validate (e.g., apps/frontend/src)")
    args = parser.parse_args()
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        if args.json:
            print(json.dumps({"errors": [f"Path {args.path} does not exist"], "warnings": [], "success": False}))
            sys.exit(1)
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)

    validator = FrontendValidator(args.path)
    validator.validate()
    
    # Standardized Output Path
    output_dir = os.path.join("project-documentation", "quality-reports", "frontend")
    default_json_output = os.path.join(output_dir, "QUALITY_REPORT.json")

    if args.json:
        print(json.dumps(validator.result.to_json(), indent=2))
        sys.exit(1 if validator.result.has_errors() else 0)
    else:
        # Always save JSON report in addition to printing to stdout
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(default_json_output, "w", encoding="utf-8") as f:
            json.dump(validator.result.to_json(), f, indent=2)
        
        print(f"\n✅ JSON report saved to: {default_json_output}")
        validator.result.print_report()

if __name__ == "__main__":
    main()
