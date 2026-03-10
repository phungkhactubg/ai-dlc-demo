#!/usr/bin/env python3
"""
extract_api_contract.py

Extract OpenAPI 3.0 specification from Spring Boot REST controllers.
Analyzes @RestController, @RequestMapping, and method annotations.

Usage:
    python extract_api_contract.py <path> [--output api.yaml] [--json]
    python extract_api_contract.py src/main/java/com/example/notifications/controller
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


@dataclass
class Endpoint:
    path: str
    method: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Any]
    controller: str


@dataclass
class ApiContract:
    title: str
    version: str
    description: str
    endpoints: List[Endpoint] = field(default_factory=list)

    def to_openapi(self) -> Dict[str, Any]:
        """Convert to OpenAPI 3.0 format."""
        paths = {}

        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "parameters": endpoint.parameters,
                "responses": endpoint.responses
            }

            if endpoint.request_body:
                operation["requestBody"] = endpoint.request_body

            paths[endpoint.path][endpoint.method.lower()] = operation

        return {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "paths": paths
        }


class ApiContractExtractor:
    """Extracts API contracts from Spring Boot controllers."""

    def __init__(self):
        self.contracts: List[ApiContract] = []

        # HTTP method annotations
        self.method_annotations = {
            '@GetMapping': 'get',
            '@PostMapping': 'post',
            '@PutMapping': 'put',
            '@DeleteMapping': 'delete',
            '@PatchMapping': 'patch',
        }

        # Parameter annotations
        self.param_annotations = {
            '@PathVariable': 'path',
            '@RequestParam': 'query',
            '@RequestHeader': 'header',
            '@RequestBody': 'body',
        }

    def extract_from_directory(self, path: str) -> List[Endpoint]:
        """Extract endpoints from all controller files."""
        root_path = Path(path)

        if not root_path.exists():
            print(f"Error: Path '{path}' does not exist.")
            return []

        endpoints = []
        java_files = list(root_path.rglob("*.java"))
        java_files = [f for f in java_files if "controller" in str(f).lower()]

        for java_file in java_files:
            file_endpoints = self._extract_from_file(str(java_file))
            endpoints.extend(file_endpoints)

        return endpoints

    def _extract_from_file(self, file_path: str) -> List[Endpoint]:
        """Extract endpoints from a single controller file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []

        # Check if it's a controller
        if '@RestController' not in content and '@Controller' not in content:
            return []

        # Extract controller info
        controller_name = self._extract_class_name(content)
        base_path = self._extract_base_path(content)
        tag = self._extract_tag(content, controller_name)

        # Extract endpoints
        endpoints = []

        # Find all method mappings
        method_pattern = re.compile(
            r'(@Get|@Post|@Put|@Delete|@Patch)Mapping\s*(?:\([^)]*\))?\s*'
            r'(?:public|private|protected)\s+'
            r'(?:[\w<>\[\],?\s]+\s+)'  # Return type
            r'(\w+)\s*'  # Method name
            r'\(([^)]*)\)',  # Parameters
            re.MULTILINE
        )

        for match in method_pattern.finditer(content):
            annotation_type = match.group(1)
            method_name = match.group(2)
            params_str = match.group(3)

            # Get full annotation
            annotation_start = match.start() - 50
            annotation_end = match.start()
            annotation_context = content[max(0, annotation_start):annotation_end]

            # Extract path from mapping annotation
            mapping_path = self._extract_mapping_path(annotation_context + match.group(0), annotation_type)

            # Combine base path and method path
            full_path = self._combine_paths(base_path, mapping_path)

            # Determine HTTP method
            http_method = self.method_annotations.get(f'@{annotation_type}Mapping', 'get')

            # Extract parameters
            parameters = self._extract_parameters(params_str, content)

            # Extract request body
            request_body = self._extract_request_body(params_str, content)

            # Extract Javadoc/annotations for summary
            summary = self._extract_summary(content, match.start(), method_name)

            endpoint = Endpoint(
                path=full_path,
                method=http_method,
                summary=summary or f"{http_method.upper()} {method_name}",
                description=f"Endpoint in {controller_name}",
                tags=[tag],
                parameters=parameters,
                request_body=request_body,
                responses={
                    "200": {"description": "Success"},
                    "400": {"description": "Bad Request"},
                    "404": {"description": "Not Found"},
                    "500": {"description": "Internal Server Error"}
                },
                controller=controller_name
            )

            endpoints.append(endpoint)

        return endpoints

    def _extract_class_name(self, content: str) -> str:
        """Extract class name from file."""
        match = re.search(r'class\s+(\w+)', content)
        return match.group(1) if match else "Unknown"

    def _extract_base_path(self, content: str) -> str:
        """Extract base path from @RequestMapping on class."""
        match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else ""

    def _extract_tag(self, content: str, class_name: str) -> str:
        """Extract tag from @Tag annotation or use class name."""
        match = re.search(r'@Tag\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)

        # Derive from class name (remove Controller suffix)
        tag = class_name.replace("Controller", "").replace("Rest", "")
        return tag if tag else class_name

    def _extract_mapping_path(self, annotation_text: str, annotation_type: str) -> str:
        """Extract path from mapping annotation."""
        # Try to find value attribute
        match = re.search(r'value\s*=\s*["\']([^"\']+)["\']', annotation_text)
        if match:
            return match.group(1)

        # Try to find path attribute
        match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', annotation_text)
        if match:
            return match.group(1)

        # Try to find string in annotation
        match = re.search(r'@"Mapping\s*\(\s*["\']([^"\']+)["\']', annotation_text)
        if match:
            return match.group(1)

        return ""

    def _combine_paths(self, base: str, path: str) -> str:
        """Combine base path and method path."""
        if not base:
            return path or "/"
        if not path:
            return base

        # Remove trailing slash from base
        base = base.rstrip("/")
        # Remove leading slash from path
        path = path.lstrip("/")

        return f"/{base}/{path}"

    def _extract_parameters(self, params_str: str, content: str) -> List[Dict[str, Any]]:
        """Extract parameters from method signature."""
        parameters = []

        # Parse parameter declarations
        params = [p.strip() for p in params_str.split(',') if p.strip()]

        for param in params:
            # Check for parameter annotations
            param_type = "query"  # Default
            param_name = None
            required = True

            if '@PathVariable' in param:
                param_type = "path"
                match = re.search(r'@PathVariable\s*(?:\([^)]*\))?\s+(\w+)', param)
                if match:
                    param_name = match.group(1)
                else:
                    match = re.search(r'@PathVariable\s*\(\s*["\']?(\w+)', param)
                    if match:
                        param_name = match.group(1)
                required = True

            elif '@RequestParam' in param:
                param_type = "query"
                match = re.search(r'@RequestParam\s*(?:\([^)]*\))?\s+(\w+)', param)
                if match:
                    param_name = match.group(1)
                else:
                    match = re.search(r'@RequestParam\s*\(\s*["\']?(\w+)', param)
                    if match:
                        param_name = match.group(1)

                # Check for defaultValue or required = false
                if 'defaultValue' in param or 'required = false' in param:
                    required = False

            elif '@RequestHeader' in param:
                param_type = "header"
                match = re.search(r'@RequestHeader\s*(?:\([^)]*\))?\s+(\w+)', param)
                if match:
                    param_name = match.group(1)

            if param_name:
                parameters.append({
                    "name": param_name,
                    "in": param_type,
                    "required": required,
                    "schema": {"type": "string"}
                })

        return parameters

    def _extract_request_body(self, params_str: str, content: str) -> Optional[Dict[str, Any]]:
        """Extract request body from @RequestBody parameter."""
        if '@RequestBody' not in params_str:
            return None

        # Try to extract the request type
        match = re.search(r'@RequestBody[^)]*\s+(\w+)', params_str)
        if match:
            request_type = match.group(1)

            return {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{request_type}"
                        }
                    }
                }
            }

        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"type": "object"}
                }
            }
        }

    def _extract_summary(self, content: str, method_pos: int, method_name: str) -> Optional[str]:
        """Extract summary from @Operation annotation or Javadoc."""
        # Look back for @Operation annotation
        context_before = content[max(0, method_pos - 500):method_pos]

        match = re.search(r'@Operation\s*\(\s*summary\s*=\s*["\']([^"\']+)["\']', context_before)
        if match:
            return match.group(1)

        # Try to find Javadoc
        javadoc_match = re.search(
            r'/\*\*\s*\n\s*\*\s*([^\n]+)\s*\n',
            content[max(0, method_pos - 200):method_pos]
        )
        if javadoc_match:
            return javadoc_match.group(1).strip('* ')

        return None


def print_results(endpoints: List[Endpoint], json_output: bool = False) -> None:
    """Print extracted endpoints."""
    if json_output:
        # Generate OpenAPI spec
        contract = ApiContract(
            title="API Specification",
            version="1.0.0",
            description="Extracted from Spring Boot controllers",
            endpoints=endpoints
        )
        print(json.dumps(contract.to_openapi(), indent=2))
        return

    print("\n" + "=" * 80)
    print("API CONTRACT EXTRACTION RESULTS")
    print("=" * 80)

    print(f"\n📊 Total endpoints found: {len(endpoints)}")

    # Group by tag
    by_tag: Dict[str, List[Endpoint]] = {}
    for endpoint in endpoints:
        for tag in endpoint.tags:
            if tag not in by_tag:
                by_tag[tag] = []
            by_tag[tag].append(endpoint)

    for tag, tag_endpoints in sorted(by_tag.items()):
        print(f"\n{'─' * 40}")
        print(f"📁 {tag} ({len(tag_endpoints)} endpoints)")
        print(f"{'─' * 40}")

        for endpoint in sorted(tag_endpoints, key=lambda e: e.path):
            method_emoji = {
                "get": "🟢",
                "post": "🔵",
                "put": "🟡",
                "delete": "🔴",
                "patch": "🟠"
            }.get(endpoint.method, "⚪")

            print(f"\n{method_emoji} {endpoint.method.upper():6} {endpoint.path}")
            print(f"   └─ {endpoint.summary}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Extract OpenAPI specification from Spring Boot controllers"
    )
    parser.add_argument("path", help="Path to controller file or directory")
    parser.add_argument("--output", "-o", metavar="file.yaml",
                        help="Output file (YAML or JSON based on extension)")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    args = parser.parse_args()

    extractor = ApiContractExtractor()
    endpoints = extractor.extract_from_directory(args.path)

    print_results(endpoints, json_output=args.json)

    # Write to file if specified
    if args.output:
        contract = ApiContract(
            title="API Specification",
            version="1.0.0",
            description="Extracted from Spring Boot controllers",
            endpoints=endpoints
        )

        output_path = Path(args.output)

        if output_path.suffix in ['.yaml', '.yml']:
            # Would need pyyaml for this, just output JSON for now
            print(f"\nNote: YAML output requires pyyaml. Writing JSON instead.")
            with open(output_path.with_suffix('.json'), 'w') as f:
                json.dump(contract.to_openapi(), f, indent=2)
            print(f"📄 Wrote: {output_path.with_suffix('.json')}")
        else:
            with open(output_path, 'w') as f:
                json.dump(contract.to_openapi(), f, indent=2)
            print(f"\n📄 Wrote: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
