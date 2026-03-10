#!/usr/bin/env python3
"""
API Contract Generator
======================

Generate OpenAPI-style REST API contract documentation.

Usage:
    python generate_api_contract.py --name "Users API" --resource users
    python generate_api_contract.py -i  # Interactive mode
    python generate_api_contract.py --json endpoints.json -o api_contract.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def generate_endpoint_docs(resource: str, methods: list = None) -> str:
    """Generate endpoint documentation for a resource."""
    if methods is None:
        methods = ["POST", "GET", "GET_ID", "PUT", "DELETE"]
    
    resource_singular = resource.rstrip("s")
    resource_pascal = "".join(word.capitalize() for word in resource_singular.split("_"))
    
    docs = []
    
    if "POST" in methods:
        docs.append(f"""### POST /{resource}

**Description:** Create a new {resource_singular}

**Request:**
```http
POST /api/v1/{resource}
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
Content-Type: application/json

{{
  "name": "string (required, 1-100 chars)",
  "description": "string (optional, max 500 chars)"
}}
```

**Go Request Struct:**
```go
type Create{resource_pascal}Request struct {{
    Name        string `json:"name" validate:"required,min=1,max=100"`
    Description string `json:"description,omitempty" validate:"max=500"`
}}
```

**Responses:**
| Code | Description |
|------|-------------|
| 201 | Created successfully |
| 400 | Validation error |
| 401 | Unauthorized |
| 409 | Duplicate name |

---
""")
    
    if "GET" in methods:
        docs.append(f"""### GET /{resource}

**Description:** List {resource} with pagination

**Request:**
```http
GET /api/v1/{resource}?page=1&limit=20&status=active
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page (max 100) |
| `status` | string | - | Filter by status |
| `search` | string | - | Search term |

**Responses:**
| Code | Description |
|------|-------------|
| 200 | Success with paginated list |
| 401 | Unauthorized |

**Response Body:**
```json
{{
  "success": true,
  "data": [...],
  "meta": {{
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }}
}}
```

---
""")
    
    if "GET_ID" in methods:
        docs.append(f"""### GET /{resource}/:id

**Description:** Get {resource_singular} by ID

**Request:**
```http
GET /api/v1/{resource}/{{id}}
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
```

**Responses:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized |
| 404 | Not found |

---
""")
    
    if "PUT" in methods:
        docs.append(f"""### PUT /{resource}/:id

**Description:** Update {resource_singular}

**Request:**
```http
PUT /api/v1/{resource}/{{id}}
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
Content-Type: application/json

{{
  "name": "string (optional)",
  "description": "string (optional)",
  "status": "string (optional, enum: active|inactive)"
}}
```

**Responses:**
| Code | Description |
|------|-------------|
| 200 | Updated successfully |
| 400 | Validation error |
| 401 | Unauthorized |
| 404 | Not found |

---
""")
    
    if "DELETE" in methods:
        docs.append(f"""### DELETE /{resource}/:id

**Description:** Delete {resource_singular} (soft delete)

**Request:**
```http
DELETE /api/v1/{resource}/{{id}}
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
```

**Responses:**
| Code | Description |
|------|-------------|
| 204 | Deleted successfully |
| 401 | Unauthorized |
| 404 | Not found |
""")
    
    return "\n".join(docs)


def generate_contract(name: str, resources: list) -> str:
    """Generate full API contract document."""
    doc = f"""# {name} - API Contract

**Version:** 1.0.0
**Base URL:** `/api/v1`
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## Authentication

All endpoints require:
- `Authorization: Bearer <jwt_token>`
- `X-Tenant-ID: <tenant_id>`

---

## Standard Response Format

### Success
```json
{{
  "success": true,
  "data": {{ ... }},
  "meta": {{ ... }}
}}
```

### Error
```json
{{
  "success": false,
  "error": {{
    "code": "ERROR_CODE",
    "message": "Description"
  }}
}}
```

---

## Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | BAD_REQUEST | Invalid input |
| 401 | UNAUTHORIZED | Missing/invalid token |
| 403 | FORBIDDEN | Access denied |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Duplicate |
| 500 | INTERNAL_ERROR | Server error |

---

## Endpoints

"""
    
    for resource in resources:
        doc += f"## {resource.replace('_', ' ').title()}\n\n"
        doc += generate_endpoint_docs(resource)
        doc += "\n---\n\n"
    
    return doc


def interactive_mode():
    """Run interactive mode to build API contract."""
    print("\n📝 API Contract Generator - Interactive Mode\n")
    
    name = input("API Name [My API]: ").strip() or "My API"
    
    resources = []
    print("\nEnter resources (one per line, empty to finish):")
    while True:
        resource = input("  Resource: ").strip().lower().replace(" ", "_")
        if not resource:
            break
        resources.append(resource)
    
    if not resources:
        resources = ["items"]
    
    output = input(f"\nOutput file [api_contract.md]: ").strip() or "api_contract.md"
    
    doc = generate_contract(name, resources)
    
    Path(output).write_text(doc, encoding="utf-8")
    print(f"\n✅ Generated: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate REST API contract documentation"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode"
    )
    parser.add_argument(
        "--name", "-n",
        default="API",
        help="API name"
    )
    parser.add_argument(
        "--resource", "-r",
        action="append",
        dest="resources",
        help="Resource name (can repeat)"
    )
    parser.add_argument(
        "--json", "-j",
        help="JSON file with endpoint definitions"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    resources = args.resources or ["items"]
    
    if args.json:
        try:
            with open(args.json, "r") as f:
                data = json.load(f)
            resources = data.get("resources", resources)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error reading JSON: {e}")
            sys.exit(1)
    
    doc = generate_contract(args.name, resources)
    
    if args.output:
        Path(args.output).write_text(doc, encoding="utf-8")
        print(f"✅ Generated: {args.output}")
    else:
        print(doc)


if __name__ == "__main__":
    main()
