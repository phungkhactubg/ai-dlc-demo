#!/usr/bin/env python3
"""
API Contract Generator
Generate OpenAPI 3.0 YAML stubs from a simple definition format.
Useful for quickly scaffolding API specs for new features.
"""
import argparse
import json
from datetime import datetime

def generate_openapi(feature_name, endpoints):
    """
    Generate OpenAPI spec from endpoint definitions.
    
    endpoints format: 
    [
        {"method": "GET", "path": "/users", "summary": "List users"},
        {"method": "POST", "path": "/users", "summary": "Create user", "body": {"name": "string", "email": "string"}},
    ]
    """
    spec = f"""openapi: 3.0.3
info:
  title: {feature_name} API
  description: Auto-generated API specification for {feature_name}
  version: 1.0.0
  contact:
    name: API Team

servers:
  - url: http://localhost:8080/api/v1
    description: Development server

paths:
"""
    
    # Group endpoints by path
    paths = {}
    for ep in endpoints:
        path = ep["path"]
        if path not in paths:
            paths[path] = {}
        paths[path][ep["method"].lower()] = ep
    
    for path, methods in paths.items():
        spec += f"  {path}:\n"
        for method, ep in methods.items():
            spec += f"    {method}:\n"
            spec += f"      summary: {ep.get('summary', 'No summary')}\n"
            spec += f"      operationId: {method}{path.replace('/', '_').replace('{', '').replace('}', '')}\n"
            spec += f"      tags:\n        - {feature_name}\n"
            
            # Path parameters
            path_params = [p.strip("{}") for p in path.split("/") if p.startswith("{")]
            if path_params:
                spec += "      parameters:\n"
                for param in path_params:
                    spec += f"""        - name: {param}
          in: path
          required: true
          schema:
            type: string
"""
            
            # Request body
            if method in ["post", "put", "patch"] and ep.get("body"):
                spec += """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
"""
                for field, ftype in ep["body"].items():
                    spec += f"                {field}:\n"
                    spec += f"                  type: {ftype}\n"
            
            # Responses
            spec += """      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
        '400':
          description: Bad request
        '401':
          description: Unauthorized
        '500':
          description: Internal server error
"""
    
    return spec

def interactive_mode():
    """Interactive mode to build endpoints."""
    print("=== API Contract Generator ===")
    feature_name = input("Feature name: ").strip() or "NewFeature"
    
    endpoints = []
    print("\nDefine endpoints (empty path to finish):")
    
    while True:
        path = input("\nPath (e.g., /users/{id}): ").strip()
        if not path:
            break
        
        method = input("Method [GET/POST/PUT/DELETE]: ").upper().strip() or "GET"
        summary = input("Summary: ").strip() or f"{method} {path}"
        
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body_fields = input("Body fields (comma-separated, e.g., name:string,age:integer): ").strip()
            if body_fields:
                body = {}
                for field in body_fields.split(","):
                    parts = field.strip().split(":")
                    if len(parts) == 2:
                        body[parts[0]] = parts[1]
        
        endpoints.append({
            "method": method,
            "path": path,
            "summary": summary,
            "body": body
        })
        print(f"  ✓ Added: {method} {path}")
    
    if endpoints:
        spec = generate_openapi(feature_name, endpoints)
        print("\n" + "=" * 50)
        print(spec)
        
        # Optionally save
        save = input("\nSave to file? (y/n): ").lower().strip()
        if save == "y":
            filename = f"{feature_name.lower().replace(' ', '_')}_api.yaml"
            with open(filename, "w") as f:
                f.write(spec)
            print(f"Saved to: {filename}")

def from_json(json_file, feature_name):
    """Generate from JSON definition file."""
    with open(json_file, "r") as f:
        endpoints = json.load(f)
    
    spec = generate_openapi(feature_name, endpoints)
    print(spec)

def main():
    parser = argparse.ArgumentParser(description="Generate OpenAPI specs from definitions")
    parser.add_argument("--json", help="JSON file with endpoint definitions")
    parser.add_argument("--name", default="NewFeature", help="Feature name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.json:
        from_json(args.json, args.name)
    elif args.interactive:
        interactive_mode()
    else:
        # Demo output
        print("Usage:")
        print("  Interactive: python generate_api_contract.py -i")
        print("  From JSON:   python generate_api_contract.py --json endpoints.json --name MyFeature")
        print("\nJSON format example:")
        print(json.dumps([
            {"method": "GET", "path": "/users", "summary": "List all users"},
            {"method": "POST", "path": "/users", "summary": "Create user", "body": {"name": "string", "email": "string"}},
            {"method": "GET", "path": "/users/{id}", "summary": "Get user by ID"},
        ], indent=2))

if __name__ == "__main__":
    main()
