#!/usr/bin/env python3
"""
Go API Contract Extractor
=========================
Extract API contracts (Request/Response DTOs, Routes) from Go backend controllers
and generate matching TypeScript/Zod types for frontend integration.

Usage:
    python extract_go_api.py <controller_file.go>
    python extract_go_api.py features/workflow/controllers/workflow/workflow_controller.go
    python extract_go_api.py features/iov/controllers --output api_contracts.ts
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class GoField:
    """Represents a Go struct field."""
    name: str
    go_type: str
    json_tag: str
    optional: bool = False


@dataclass
class GoStruct:
    """Represents a Go struct."""
    name: str
    fields: List[GoField] = field(default_factory=list)
    is_request: bool = False
    is_response: bool = False


@dataclass
class GoEndpoint:
    """Represents an API endpoint."""
    method: str
    path: str
    handler: str
    request_type: Optional[str] = None
    response_type: Optional[str] = None


class GoAPIExtractor:
    """Extracts API contracts from Go source files."""

    GO_TO_TS_TYPES = {
        'string': 'string',
        'int': 'number',
        'int32': 'number',
        'int64': 'number',
        'float32': 'number',
        'float64': 'number',
        'bool': 'boolean',
        'time.Time': 'string',  # ISO datetime
        'any': 'unknown',
        'interface{}': 'unknown',
        'map[string]any': 'Record<string, unknown>',
        'map[string]interface{}': 'Record<string, unknown>',
        '[]string': 'string[]',
        '[]int': 'number[]',
        '[]any': 'unknown[]',
    }

    GO_TO_ZOD_TYPES = {
        'string': 'z.string()',
        'int': 'z.number().int()',
        'int32': 'z.number().int()',
        'int64': 'z.number().int()',
        'float32': 'z.number()',
        'float64': 'z.number()',
        'bool': 'z.boolean()',
        'time.Time': 'z.string().datetime()',
        'any': 'z.unknown()',
        'interface{}': 'z.unknown()',
        'map[string]any': 'z.record(z.string(), z.unknown())',
        'map[string]interface{}': 'z.record(z.string(), z.unknown())',
        '[]string': 'z.array(z.string())',
        '[]int': 'z.array(z.number().int())',
        '[]any': 'z.array(z.unknown())',
    }

    def __init__(self):
        self.structs: Dict[str, GoStruct] = {}
        self.endpoints: List[GoEndpoint] = []

    def extract_from_file(self, filepath: Path) -> None:
        """Extract structs and endpoints from a Go file."""
        content = filepath.read_text(encoding='utf-8')
        self._extract_structs(content)
        self._extract_endpoints(content)

    def _extract_structs(self, content: str) -> None:
        """Extract struct definitions from Go code."""
        # Pattern for struct definitions
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{([^}]+)\}'
        
        for match in re.finditer(struct_pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            
            struct = GoStruct(
                name=name,
                is_request='Request' in name,
                is_response='Response' in name
            )
            
            # Extract fields
            field_pattern = r'(\w+)\s+(\S+)\s+`json:"([^"]+)"`'
            for field_match in re.finditer(field_pattern, body):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                json_tag = field_match.group(3)
                
                # Check if optional (omitempty)
                optional = 'omitempty' in json_tag
                json_name = json_tag.split(',')[0]
                
                if json_name and json_name != '-':
                    struct.fields.append(GoField(
                        name=field_name,
                        go_type=field_type,
                        json_tag=json_name,
                        optional=optional
                    ))
            
            if struct.fields:
                self.structs[name] = struct

    def _extract_endpoints(self, content: str) -> None:
        """Extract route registrations from Go code."""
        # Pattern for Echo route registrations
        route_patterns = [
            r'\.(\w+)\("([^"]+)",\s*c\.(\w+)\)',  # .GET("/path", c.Handler)
            r'(\w+)\.(\w+)\("([^"]+)",\s*\w+\.(\w+)\)',  # group.GET("/path", ctrl.Handler)
        ]
        
        for pattern in route_patterns:
            for match in re.finditer(pattern, content):
                if len(match.groups()) == 3:
                    method, path, handler = match.groups()
                elif len(match.groups()) == 4:
                    _, method, path, handler = match.groups()
                else:
                    continue
                
                method = method.upper()
                if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue
                
                self.endpoints.append(GoEndpoint(
                    method=method,
                    path=path,
                    handler=handler
                ))

    def _convert_go_type_to_ts(self, go_type: str) -> str:
        """Convert Go type to TypeScript type."""
        # Handle pointers
        if go_type.startswith('*'):
            return self._convert_go_type_to_ts(go_type[1:])
        
        # Handle slices
        if go_type.startswith('[]'):
            inner = go_type[2:]
            if inner in self.structs:
                return f'{inner}[]'
            inner_ts = self.GO_TO_TS_TYPES.get(inner, 'unknown')
            return f'{inner_ts}[]'
        
        # Check known types
        if go_type in self.GO_TO_TS_TYPES:
            return self.GO_TO_TS_TYPES[go_type]
        
        # Check if it's a known struct
        if go_type in self.structs:
            return go_type
        
        return 'unknown'

    def _convert_go_type_to_zod(self, go_type: str, optional: bool = False) -> str:
        """Convert Go type to Zod schema."""
        # Handle pointers
        if go_type.startswith('*'):
            return self._convert_go_type_to_zod(go_type[1:], optional=True)
        
        # Handle slices
        if go_type.startswith('[]'):
            inner = go_type[2:]
            if inner in self.structs:
                inner_zod = f'{inner}Schema'
            else:
                inner_zod = self.GO_TO_ZOD_TYPES.get(inner, 'z.unknown()')
            base = f'z.array({inner_zod})'
        elif go_type in self.GO_TO_ZOD_TYPES:
            base = self.GO_TO_ZOD_TYPES[go_type]
        elif go_type in self.structs:
            base = f'{go_type}Schema'
        else:
            base = 'z.unknown()'
        
        if optional:
            return f'{base}.optional()'
        return base

    def generate_typescript(self) -> str:
        """Generate TypeScript interfaces."""
        lines = [
            '// Auto-generated from Go backend DTOs',
            '// Source: Go Controller files',
            '// DO NOT EDIT MANUALLY - Regenerate using extract_go_api.py',
            '',
        ]
        
        for name, struct in self.structs.items():
            lines.append(f'export interface {name} {{')
            for fld in struct.fields:
                ts_type = self._convert_go_type_to_ts(fld.go_type)
                optional = '?' if fld.optional else ''
                lines.append(f'  {fld.json_tag}{optional}: {ts_type};')
            lines.append('}')
            lines.append('')
        
        return '\n'.join(lines)

    def generate_zod(self) -> str:
        """Generate Zod schemas."""
        lines = [
            "import { z } from 'zod';",
            '',
            '// Auto-generated from Go backend DTOs',
            '// Source: Go Controller files',
            '// DO NOT EDIT MANUALLY - Regenerate using extract_go_api.py',
            '',
        ]
        
        for name, struct in self.structs.items():
            lines.append(f'export const {name}Schema = z.object({{')
            for fld in struct.fields:
                zod_type = self._convert_go_type_to_zod(fld.go_type, fld.optional)
                lines.append(f'  {fld.json_tag}: {zod_type},')
            lines.append('});')
            lines.append(f'export type {name} = z.infer<typeof {name}Schema>;')
            lines.append('')
        
        return '\n'.join(lines)

    def generate_api_client(self, base_path: str = '/api/v1') -> str:
        """Generate API client code."""
        lines = [
            "import axios from 'axios';",
            '',
            '// Auto-generated API client from Go backend',
            '',
            'const apiClient = axios.create({',
            f"  baseURL: import.meta.env.VITE_API_URL || '{base_path}',",
            '});',
            '',
        ]
        
        # Group endpoints by handler prefix
        for ep in self.endpoints:
            method_lower = ep.method.lower()
            lines.append(f'// {ep.method} {ep.path}')
            if ep.method in ['POST', 'PUT', 'PATCH']:
                lines.append(f"export const {ep.handler} = (data: unknown) => apiClient.{method_lower}('{ep.path}', data);")
            else:
                lines.append(f"export const {ep.handler} = () => apiClient.{method_lower}('{ep.path}');")
            lines.append('')
        
        return '\n'.join(lines)

    def print_summary(self) -> None:
        """Print extraction summary."""
        print("=" * 60)
        print("GO API CONTRACT EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"\nStructs found: {len(self.structs)}")
        for name, struct in self.structs.items():
            req = " [REQUEST]" if struct.is_request else ""
            res = " [RESPONSE]" if struct.is_response else ""
            print(f"  - {name}{req}{res} ({len(struct.fields)} fields)")
        
        print(f"\nEndpoints found: {len(self.endpoints)}")
        for ep in self.endpoints:
            print(f"  - {ep.method:6} {ep.path} -> {ep.handler}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract API contracts from Go backend and generate TypeScript/Zod types"
    )
    parser.add_argument("path", help="Path to Go controller file or directory")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", choices=["ts", "zod", "api", "all"], default="zod",
                        help="Output format (default: zod)")
    parser.add_argument("--base-path", default="/api/v1", help="API base path")

    args = parser.parse_args()
    target = Path(args.path)

    if not target.exists():
        print(f"Error: Path does not exist: {target}")
        sys.exit(1)

    extractor = GoAPIExtractor()

    if target.is_file():
        extractor.extract_from_file(target)
    else:
        for go_file in target.rglob('*.go'):
            if '_test.go' not in go_file.name:
                extractor.extract_from_file(go_file)

    extractor.print_summary()

    # Generate output
    if args.format == "ts":
        output = extractor.generate_typescript()
    elif args.format == "zod":
        output = extractor.generate_zod()
    elif args.format == "api":
        output = extractor.generate_api_client(args.base_path)
    else:  # all
        output = '\n\n// === ZOD SCHEMAS ===\n\n'
        output += extractor.generate_zod()
        output += '\n\n// === API CLIENT ===\n\n'
        output += extractor.generate_api_client(args.base_path)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"\nOutput saved to: {args.output}")
    else:
        print("\n" + "=" * 60)
        print("GENERATED CODE")
        print("=" * 60)
        print(output)


if __name__ == "__main__":
    main()
