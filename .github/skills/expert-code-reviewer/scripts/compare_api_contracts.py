#!/usr/bin/env python3
"""
Compare API Contracts Script

Compares Go backend DTOs with Frontend Zod schemas to detect contract mismatches.
Helps ensure API contracts are synchronized between BE and FE.

Usage:
    python compare_api_contracts.py --go <go_file> --zod <zod_file>
    python compare_api_contracts.py --go-dir features/workflow/models --zod-dir apps/frontend/src/workflow/core/models

Examples:
    python compare_api_contracts.py --go features/iov/models/vehicle.go --zod apps/frontend/src/iov/core/models/vehicle.model.ts
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Field:
    name: str
    type: str
    json_name: str
    optional: bool


@dataclass
class Struct:
    name: str
    fields: List[Field]
    source_file: str


# Go to Zod type mapping
GO_TO_ZOD_MAP = {
    "string": "z.string()",
    "int": "z.number().int()",
    "int8": "z.number().int()",
    "int16": "z.number().int()",
    "int32": "z.number().int()",
    "int64": "z.number().int()",
    "uint": "z.number().int()",
    "uint8": "z.number().int()",
    "uint16": "z.number().int()",
    "uint32": "z.number().int()",
    "uint64": "z.number().int()",
    "float32": "z.number()",
    "float64": "z.number()",
    "bool": "z.boolean()",
    "time.Time": "z.string().datetime()",
    "primitive.ObjectID": "z.string()",
    "bson.ObjectID": "z.string()",
    "[]string": "z.array(z.string())",
    "[]int": "z.array(z.number().int())",
    "[]int64": "z.array(z.number().int())",
    "map[string]any": "z.record(z.string(), z.unknown())",
    "map[string]interface{}": "z.record(z.string(), z.unknown())",
    "interface{}": "z.unknown()",
    "any": "z.unknown()",
}


def parse_go_struct(content: str, filename: str) -> List[Struct]:
    """Parse Go structs from file content."""
    structs: List[Struct] = []
    
    # Match struct definitions
    struct_pattern = r'type\s+(\w+)\s+struct\s*\{([^}]+)\}'
    
    for match in re.finditer(struct_pattern, content, re.DOTALL):
        struct_name = match.group(1)
        body = match.group(2)
        fields: List[Field] = []
        
        # Parse each field
        field_pattern = r'(\w+)\s+(`?[\w\[\]\*\.]+`?)\s*`([^`]*)`'
        for field_match in re.finditer(field_pattern, body):
            go_name = field_match.group(1)
            go_type = field_match.group(2).strip('`')
            tags = field_match.group(3)
            
            # Extract JSON tag
            json_match = re.search(r'json:"([^"]*)"', tags)
            if json_match:
                json_tag = json_match.group(1)
                json_parts = json_tag.split(',')
                json_name = json_parts[0] if json_parts[0] != "-" else None
                optional = 'omitempty' in json_parts
            else:
                json_name = go_name
                optional = False
            
            if json_name:  # Skip fields with json:"-"
                fields.append(Field(
                    name=go_name,
                    type=go_type,
                    json_name=json_name,
                    optional=optional
                ))
        
        if fields:
            structs.append(Struct(
                name=struct_name,
                fields=fields,
                source_file=filename
            ))
    
    return structs


def parse_zod_schema(content: str, filename: str) -> List[Struct]:
    """Parse Zod schemas from TypeScript file content."""
    structs: List[Struct] = []
    
    # Match Zod schema definitions
    # Patterns: const XxxSchema = z.object({ ... }) or export const XxxSchema = z.object({ ... })
    schema_pattern = r'(?:export\s+)?const\s+(\w+Schema)\s*=\s*z\.object\s*\(\s*\{([^}]+)\}\s*\)'
    
    for match in re.finditer(schema_pattern, content, re.DOTALL):
        schema_name = match.group(1)
        body = match.group(2)
        fields: List[Field] = []
        
        # Parse each field in the Zod schema
        # Pattern: fieldName: z.string(), or field_name: z.number().optional(),
        field_pattern = r'(\w+)\s*:\s*(z\.[^,\n]+)'
        for field_match in re.finditer(field_pattern, body):
            field_name = field_match.group(1)
            zod_type = field_match.group(2).strip().rstrip(',')
            optional = '.optional()' in zod_type or '.nullable()' in zod_type
            
            fields.append(Field(
                name=field_name,
                type=zod_type,
                json_name=field_name,  # In Zod, field name = json name
                optional=optional
            ))
        
        if fields:
            # Remove 'Schema' suffix for comparison
            struct_name = schema_name.replace('Schema', '')
            structs.append(Struct(
                name=struct_name,
                fields=fields,
                source_file=filename
            ))
    
    return structs


def normalize_go_type_to_zod(go_type: str) -> str:
    """Convert Go type to expected Zod type pattern."""
    # Handle pointers
    if go_type.startswith('*'):
        base_type = go_type[1:]
        base_zod = GO_TO_ZOD_MAP.get(base_type, f"<{base_type}>Schema")
        return f"{base_zod}.nullable()"
    
    # Handle slices
    if go_type.startswith('[]'):
        elem_type = go_type[2:]
        elem_zod = GO_TO_ZOD_MAP.get(elem_type, f"<{elem_type}>Schema")
        return f"z.array({elem_zod})"
    
    # Direct mapping
    if go_type in GO_TO_ZOD_MAP:
        return GO_TO_ZOD_MAP[go_type]
    
    # Assume custom type -> custom schema
    return f"{go_type}Schema"


def compare_structs(go_structs: List[Struct], zod_structs: List[Struct]) -> List[str]:
    """Compare Go structs with Zod schemas and return issues."""
    issues: List[str] = []
    
    go_by_name = {s.name: s for s in go_structs}
    zod_by_name = {s.name: s for s in zod_structs}
    
    all_names = set(go_by_name.keys()) | set(zod_by_name.keys())
    
    for name in sorted(all_names):
        go_struct = go_by_name.get(name)
        zod_struct = zod_by_name.get(name)
        
        if go_struct and not zod_struct:
            issues.append(f"🔴 MISSING ZOD SCHEMA: '{name}' exists in Go ({go_struct.source_file}) but not in Frontend")
            continue
        
        if zod_struct and not go_struct:
            issues.append(f"🟡 EXTRA ZOD SCHEMA: '{name}' exists in Frontend ({zod_struct.source_file}) but not in Go")
            continue
        
        # Both exist - compare fields
        go_fields = {f.json_name: f for f in go_struct.fields}
        zod_fields = {f.json_name: f for f in zod_struct.fields}
        
        all_field_names = set(go_fields.keys()) | set(zod_fields.keys())
        
        for field_name in sorted(all_field_names):
            go_field = go_fields.get(field_name)
            zod_field = zod_fields.get(field_name)
            
            if go_field and not zod_field:
                severity = "🟡" if go_field.optional else "🔴"
                issues.append(f"{severity} [{name}] MISSING FIELD: '{field_name}' in Zod schema (Go: {go_field.type})")
                continue
            
            if zod_field and not go_field:
                issues.append(f"🟡 [{name}] EXTRA FIELD: '{field_name}' in Zod schema but not in Go")
                continue
            
            # Both exist - compare types
            expected_zod = normalize_go_type_to_zod(go_field.type)
            
            # Basic type compatibility check
            if not is_type_compatible(expected_zod, zod_field.type):
                issues.append(
                    f"🔴 [{name}] TYPE MISMATCH: '{field_name}'\n"
                    f"   Go: {go_field.type} -> Expected Zod: {expected_zod}\n"
                    f"   Actual Zod: {zod_field.type}"
                )
            
            # Check optional mismatch
            if go_field.optional and not zod_field.optional:
                issues.append(
                    f"🟡 [{name}] OPTIONAL MISMATCH: '{field_name}' is optional in Go (omitempty) "
                    f"but required in Zod"
                )
    
    return issues


def is_type_compatible(expected: str, actual: str) -> bool:
    """Check if Zod type is compatible with expected type."""
    # Normalize for comparison
    expected_norm = expected.lower().replace(' ', '')
    actual_norm = actual.lower().replace(' ', '')
    
    # Direct match
    if expected_norm in actual_norm:
        return True
    
    # Common compatible pairs
    compatible_pairs = [
        ("z.string()", "z.string()"),
        ("z.number()", "z.number()"),
        ("z.boolean()", "z.boolean()"),
        ("z.string().datetime()", "z.string()"),
        ("z.unknown()", "z.unknown()"),
    ]
    
    for exp, act in compatible_pairs:
        if exp in expected_norm and exp in actual_norm:
            return True
    
    return False


def scan_directory(path: str, parser_func, extensions: List[str]) -> List[Struct]:
    """Scan a directory and parse all matching files."""
    all_structs: List[Struct] = []
    path_obj = Path(path)
    
    if path_obj.is_file():
        with open(path_obj, 'r', encoding='utf-8') as f:
            content = f.read()
        return parser_func(content, str(path_obj))
    
    for ext in extensions:
        for file_path in path_obj.rglob(f"*{ext}"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                all_structs.extend(parser_func(content, str(file_path)))
            except Exception as e:
                print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
    
    return all_structs


def main():
    parser = argparse.ArgumentParser(
        description="Compare Go DTOs with Zod schemas for API contract validation"
    )
    parser.add_argument("--go", dest="go_path", help="Path to Go file or directory")
    parser.add_argument("--zod", dest="zod_path", help="Path to Zod/TS file or directory")
    parser.add_argument("--go-dir", dest="go_dir", help="Directory containing Go model files")
    parser.add_argument("--zod-dir", dest="zod_dir", help="Directory containing Zod schema files")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    go_path = args.go_path or args.go_dir
    zod_path = args.zod_path or args.zod_dir
    
    if not go_path or not zod_path:
        print("Error: Both --go and --zod paths are required", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    if not os.path.exists(go_path):
        print(f"Error: Go path '{go_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(zod_path):
        print(f"Error: Zod path '{zod_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Parse Go structs
    if not args.json:
        print(f"Scanning Go files in: {go_path}")
    go_structs = scan_directory(go_path, parse_go_struct, [".go"])
    if not args.json:
        print(f"  Found {len(go_structs)} structs")
    
    # Parse Zod schemas
    if not args.json:
        print(f"Scanning Zod files in: {zod_path}")
    zod_structs = scan_directory(zod_path, parse_zod_schema, [".ts", ".tsx"])
    if not args.json:
        print(f"  Found {len(zod_structs)} schemas")
        print()
    
    # Compare
    # Compare
    issues = compare_structs(go_structs, zod_structs)
    
    if args.json:
        import json
        output = {
             "go_structs_count": len(go_structs),
             "zod_structs_count": len(zod_structs),
             "issues": [{"message": i, "severity": "CRITICAL" if "🔴" in i else "WARNING"} for i in issues],
             "success": len([i for i in issues if "🔴" in i]) == 0
        }
        print(json.dumps(output, indent=2))
        sys.exit(0 if output["success"] else 1)

    if not issues:
        print("=" * 50)
        print("✅ API CONTRACTS MATCH!")
        print("=" * 50)
        print(f"\nCompared {len(go_structs)} Go structs with {len(zod_structs)} Zod schemas")
        print("No mismatches found.")
        sys.exit(0)
    
    print("=" * 50)
    print("API CONTRACT COMPARISON RESULTS")
    print("=" * 50)
    print()
    
    critical = sum(1 for i in issues if i.startswith("🔴"))
    warning = sum(1 for i in issues if i.startswith("🟡"))
    
    print(f"Total Issues: {len(issues)}")
    print(f"  🔴 Critical: {critical}")
    print(f"  🟡 Warning: {warning}")
    print()
    
    for issue in issues:
        print(issue)
        print()
    
    print("-" * 50)
    print("RECOMMENDATIONS:")
    print("-" * 50)
    if critical > 0:
        print("1. Fix CRITICAL (🔴) issues before deployment")
        print("2. Run: python extract_go_api.py <go_file> --format zod")
        print("3. Update frontend Zod schemas to match")
    if warning > 0:
        print("- Review WARNING (🟡) issues for potential bugs")
    
    sys.exit(1 if critical > 0 else 0)


if __name__ == "__main__":
    main()
