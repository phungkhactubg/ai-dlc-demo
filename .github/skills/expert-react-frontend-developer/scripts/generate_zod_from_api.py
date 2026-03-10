#!/usr/bin/env python3
"""
Zod Schema Generator from API Response
=======================================
Generate Zod schemas from JSON API response samples.

Usage:
    python generate_zod_from_api.py --input sample.json --name User
    python generate_zod_from_api.py --url http://localhost:8080/api/users/1 --name User
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Union


def infer_zod_type(value: Any, key: str = "") -> str:
    """Infer Zod type from Python value."""
    if value is None:
        return "z.unknown().nullable()"
    
    if isinstance(value, bool):
        return "z.boolean()"
    
    if isinstance(value, int):
        return "z.number().int()"
    
    if isinstance(value, float):
        return "z.number()"
    
    if isinstance(value, str):
        # Detect common patterns
        if key.lower().endswith('id') and len(value) == 36 and '-' in value:
            return "z.string().uuid()"
        if key.lower() in ['email', 'mail']:
            return "z.string().email()"
        if key.lower() in ['url', 'link', 'href']:
            return "z.string().url()"
        if key.lower() in ['createdat', 'updatedat', 'created_at', 'updated_at', 'date', 'timestamp']:
            return "z.string().datetime()"
        return "z.string()"
    
    if isinstance(value, list):
        if len(value) == 0:
            return "z.array(z.unknown())"
        # Infer from first element
        elem_type = infer_zod_type(value[0])
        return f"z.array({elem_type})"
    
    if isinstance(value, dict):
        return generate_zod_object(value, inline=True)
    
    return "z.unknown()"


def generate_zod_object(data: Dict[str, Any], inline: bool = False) -> str:
    """Generate Zod object schema from dictionary."""
    if not data:
        return "z.object({})"
    
    lines = []
    indent = "    " if not inline else "  "
    
    for key, value in data.items():
        zod_type = infer_zod_type(value, key)
        
        # Check if field might be optional (heuristic: null value or camelCase with 'optional' prefix)
        is_optional = value is None
        
        if is_optional:
            lines.append(f"{indent}{key}: {zod_type}.optional(),")
        else:
            lines.append(f"{indent}{key}: {zod_type},")
    
    if inline:
        return "z.object({\n" + "\n".join(lines) + "\n  })"
    else:
        return "\n".join(lines)


def generate_schema(data: Any, name: str) -> str:
    """Generate complete Zod schema file content."""
    if isinstance(data, list):
        # If array, use first element as template
        if len(data) == 0:
            return f"// Empty array response - cannot infer schema\nexport const {name}Schema = z.array(z.unknown());\nexport type {name} = z.infer<typeof {name}Schema>;"
        data = data[0]
    
    if not isinstance(data, dict):
        zod_type = infer_zod_type(data)
        return f"import {{ z }} from 'zod';\n\nexport const {name}Schema = {zod_type};\nexport type {name} = z.infer<typeof {name}Schema>;"
    
    fields = generate_zod_object(data)
    
    return f"""import {{ z }} from 'zod';

// Auto-generated Zod schema from API response
// Review and adjust types as needed

export const {name}Schema = z.object({{
{fields}
}});

// TypeScript type inferred from schema
export type {name} = z.infer<typeof {name}Schema>;

// Optional: Create partial schema for updates
export const Update{name}Schema = {name}Schema.partial();
export type Update{name}Request = z.infer<typeof Update{name}Schema>;

// Optional: Create schema for creation (omitting auto-generated fields)
export const Create{name}Schema = {name}Schema.omit({{
  id: true,
  createdAt: true,
  updatedAt: true,
}});
export type Create{name}Request = z.infer<typeof Create{name}Schema>;
"""


def fetch_from_url(url: str) -> Any:
    """Fetch JSON from URL."""
    try:
        import urllib.request
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate Zod schemas from JSON API responses"
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Path to JSON file containing sample response"
    )
    parser.add_argument(
        "--url",
        "-u",
        help="URL to fetch sample response from"
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help="Name for the generated schema (PascalCase)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Get data
    data = None
    if args.input:
        try:
            data = json.loads(Path(args.input).read_text())
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    elif args.url:
        data = fetch_from_url(args.url)
    else:
        # Try reading from stdin
        print("Paste JSON and press Ctrl+D (Unix) or Ctrl+Z (Windows):")
        try:
            import sys
            data = json.load(sys.stdin)
        except:
            print("Error: Provide --input, --url, or pipe JSON to stdin")
            return

    if data is None:
        return

    # Generate schema
    schema = generate_schema(data, args.name)

    if args.output:
        Path(args.output).write_text(schema, encoding='utf-8')
        print(f"Schema saved to: {args.output}")
    else:
        print("=" * 60)
        print("GENERATED ZOD SCHEMA")
        print("=" * 60)
        print(schema)


if __name__ == "__main__":
    main()
