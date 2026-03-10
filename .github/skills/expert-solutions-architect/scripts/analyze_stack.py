#!/usr/bin/env python3
"""
Stack Analyzer
==============

Analyze project tech stack from go.mod, package.json, etc.

Usage:
    python analyze_stack.py .
    python analyze_stack.py --file go.mod
    python analyze_stack.py --file package.json --format json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Any


def analyze_go_mod(content: str) -> Dict[str, Any]:
    """Analyze go.mod file."""
    result = {
        "type": "go",
        "module": "",
        "go_version": "",
        "dependencies": [],
        "categories": {}
    }
    
    # Extract module name
    mod_match = re.search(r"^module\s+(.+)$", content, re.MULTILINE)
    if mod_match:
        result["module"] = mod_match.group(1).strip()
    
    # Extract Go version
    ver_match = re.search(r"^go\s+([\d.]+)", content, re.MULTILINE)
    if ver_match:
        result["go_version"] = ver_match.group(1)
    
    # Extract dependencies
    require_block = re.search(r"require\s*\((.*?)\)", content, re.DOTALL)
    if require_block:
        deps = re.findall(r"^\s*([\w./\-]+)\s+v?([\d.]+)", require_block.group(1), re.MULTILINE)
        for name, version in deps:
            result["dependencies"].append({"name": name, "version": version})
    
    # Single-line requires
    single_deps = re.findall(r"^require\s+([\w./\-]+)\s+v?([\d.]+)", content, re.MULTILINE)
    for name, version in single_deps:
        result["dependencies"].append({"name": name, "version": version})
    
    # Categorize dependencies
    categories = {
        "web_framework": ["echo", "gin", "fiber", "chi", "gorilla/mux"],
        "database": ["mongo-driver", "pgx", "gorm", "sqlx", "mysql"],
        "cache": ["go-redis", "redigo", "bigcache"],
        "messaging": ["nats", "kafka-go", "rabbitmq", "paho.mqtt"],
        "validation": ["validator", "ozzo-validation"],
        "config": ["viper", "envconfig", "godotenv"],
        "logging": ["zap", "logrus", "zerolog"],
        "testing": ["testify", "gomock", "mockery"],
        "auth": ["jwt", "oauth", "keycloak"],
        "storage": ["minio", "aws-sdk"],
    }
    
    for dep in result["dependencies"]:
        for category, keywords in categories.items():
            if any(kw in dep["name"].lower() for kw in keywords):
                if category not in result["categories"]:
                    result["categories"][category] = []
                result["categories"][category].append(dep["name"])
    
    return result


def analyze_package_json(content: str) -> Dict[str, Any]:
    """Analyze package.json file."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}
    
    result = {
        "type": "node",
        "name": data.get("name", ""),
        "version": data.get("version", ""),
        "dependencies": [],
        "dev_dependencies": [],
        "categories": {}
    }
    
    # Extract dependencies
    for name, version in data.get("dependencies", {}).items():
        result["dependencies"].append({"name": name, "version": version})
    
    for name, version in data.get("devDependencies", {}).items():
        result["dev_dependencies"].append({"name": name, "version": version})
    
    # Categorize
    categories = {
        "framework": ["react", "vue", "angular", "next", "svelte"],
        "state": ["zustand", "redux", "mobx", "recoil", "jotai"],
        "ui": ["mui", "antd", "chakra", "tailwind", "bootstrap"],
        "forms": ["formik", "react-hook-form", "yup", "zod"],
        "routing": ["react-router", "vue-router", "next"],
        "http": ["axios", "fetch", "ky", "got"],
        "testing": ["jest", "vitest", "testing-library", "cypress"],
        "bundler": ["vite", "webpack", "esbuild", "rollup"],
        "typescript": ["typescript", "@types/"],
    }
    
    all_deps = result["dependencies"] + result["dev_dependencies"]
    for dep in all_deps:
        for category, keywords in categories.items():
            if any(kw in dep["name"].lower() for kw in keywords):
                if category not in result["categories"]:
                    result["categories"][category] = []
                result["categories"][category].append(dep["name"])
    
    return result


def print_analysis(result: Dict[str, Any], format_type: str = "text"):
    """Print analysis result."""
    if format_type == "json":
        print(json.dumps(result, indent=2))
        return
    
    print("\n" + "=" * 60)
    print("STACK ANALYSIS")
    print("=" * 60 + "\n")
    
    if result.get("type") == "go":
        print(f"📦 Module: {result.get('module', 'N/A')}")
        print(f"🔧 Go Version: {result.get('go_version', 'N/A')}")
        print(f"📚 Dependencies: {len(result.get('dependencies', []))}")
    else:
        print(f"📦 Package: {result.get('name', 'N/A')}")
        print(f"🔧 Version: {result.get('version', 'N/A')}")
        print(f"📚 Dependencies: {len(result.get('dependencies', []))}")
        print(f"🔧 Dev Dependencies: {len(result.get('dev_dependencies', []))}")
    
    print("\n📂 Categories:")
    for category, deps in result.get("categories", {}).items():
        print(f"  {category.replace('_', ' ').title()}: {', '.join(deps[:3])}")
    
    if result.get("dependencies"):
        print("\n📋 Top Dependencies:")
        for dep in result.get("dependencies", [])[:10]:
            print(f"  - {dep['name']} @ {dep['version']}")
    
    print()


def analyze_directory(path: Path) -> List[Dict[str, Any]]:
    """Analyze a directory for dependency files."""
    results = []
    
    # Check for go.mod
    go_mod = path / "go.mod"
    if go_mod.exists():
        content = go_mod.read_text(encoding="utf-8")
        result = analyze_go_mod(content)
        result["file"] = str(go_mod)
        results.append(result)
    
    # Check for package.json (root and apps/)
    for pj_path in [path / "package.json"] + list(path.glob("apps/*/package.json")):
        if pj_path.exists():
            content = pj_path.read_text(encoding="utf-8")
            result = analyze_package_json(content)
            result["file"] = str(pj_path)
            results.append(result)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Analyze project tech stack"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or file to analyze"
    )
    parser.add_argument(
        "--file", "-f",
        help="Specific file to analyze"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {args.file}")
            return
        
        content = file_path.read_text(encoding="utf-8")
        
        if file_path.name == "go.mod":
            result = analyze_go_mod(content)
        elif file_path.name == "package.json":
            result = analyze_package_json(content)
        else:
            print(f"❌ Unknown file type: {file_path.name}")
            return
        
        result["file"] = str(file_path)
        print_analysis(result, args.format)
    else:
        dir_path = Path(args.path)
        if not dir_path.is_dir():
            print(f"❌ Not a directory: {args.path}")
            return
        
        results = analyze_directory(dir_path)
        
        if not results:
            print("❌ No dependency files found (go.mod, package.json)")
            return
        
        for result in results:
            if args.format == "json":
                print(json.dumps(result, indent=2))
            else:
                print(f"\n📁 File: {result.get('file', 'N/A')}")
                print_analysis(result, args.format)


if __name__ == "__main__":
    main()
