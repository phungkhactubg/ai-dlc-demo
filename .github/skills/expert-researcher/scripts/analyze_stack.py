#!/usr/bin/env python3
"""
Tech Stack Analyzer
Analyzes package.json and go.mod to understand project dependencies.
Outputs a summary useful for architectural planning.
"""
import argparse
import json
import os
import re
from pathlib import Path

def analyze_package_json(filepath):
    """Analyze a package.json file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error reading {filepath}: {e}")
        return
    
    print(f"\n=== Frontend Analysis: {filepath} ===\n")
    print(f"Project: {data.get('name', 'N/A')}")
    print(f"Version: {data.get('version', 'N/A')}")
    
    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    
    print(f"\nProduction Dependencies: {len(deps)}")
    print(f"Dev Dependencies: {len(dev_deps)}")
    
    # Categorize common packages
    categories = {
        "Framework": ["react", "vue", "angular", "svelte", "next", "nuxt"],
        "UI Library": ["@mui/material", "@chakra-ui", "antd", "tailwindcss", "@radix-ui"],
        "State Management": ["zustand", "redux", "mobx", "jotai", "recoil", "@tanstack/react-query"],
        "Build Tool": ["vite", "webpack", "esbuild", "rollup", "parcel"],
        "Testing": ["jest", "vitest", "cypress", "@testing-library", "playwright"],
        "TypeScript": ["typescript"],
        "Validation": ["zod", "yup", "joi"],
        "HTTP Client": ["axios", "ky", "got", "node-fetch"],
        "Routing": ["react-router", "react-router-dom", "@tanstack/router"],
        "Animation": ["framer-motion", "gsap", "react-spring"],
    }
    
    all_deps = {**deps, **dev_deps}
    
    print("\n--- Detected Technologies ---")
    for category, packages in categories.items():
        found = [p for p in packages if any(p in dep for dep in all_deps.keys())]
        if found:
            versions = [f"{p}@{all_deps.get(p, all_deps.get(f'@types/{p}', '?'))}" for p in found if p in all_deps]
            print(f"  {category}: {', '.join(versions) if versions else ', '.join(found)}")
    
    # Scripts
    scripts = data.get("scripts", {})
    if scripts:
        print("\n--- Available Scripts ---")
        for name, cmd in list(scripts.items())[:10]:
            print(f"  npm run {name}: {cmd[:60]}...")

def analyze_go_mod(filepath):
    """Analyze a go.mod file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[!] Error reading {filepath}: {e}")
        return
    
    print(f"\n=== Backend Analysis: {filepath} ===\n")
    
    # Module name
    module_match = re.search(r'^module\s+(.+)$', content, re.MULTILINE)
    if module_match:
        print(f"Module: {module_match.group(1)}")
    
    # Go version
    go_match = re.search(r'^go\s+(.+)$', content, re.MULTILINE)
    if go_match:
        print(f"Go Version: {go_match.group(1)}")
    
    # Dependencies
    require_block = re.search(r'require\s*\((.*?)\)', content, re.DOTALL)
    deps = []
    if require_block:
        deps = re.findall(r'^\s*([^\s]+)\s+([^\s]+)', require_block.group(1), re.MULTILINE)
    
    # Single-line requires
    single_requires = re.findall(r'^require\s+([^\s]+)\s+([^\s]+)', content, re.MULTILINE)
    deps.extend(single_requires)
    
    print(f"\nTotal Dependencies: {len(deps)}")
    
    # Categorize
    categories = {
        "Web Framework": ["echo", "gin", "fiber", "chi", "gorilla/mux"],
        "Database": ["mongo-driver", "gorm", "sqlx", "pgx", "redis"],
        "Auth/JWT": ["jwt", "golang-jwt", "oauth"],
        "Messaging": ["nats", "rabbitmq", "kafka", "mqtt"],
        "Testing": ["testify", "gomock", "ginkgo"],
        "Logging": ["zap", "logrus", "zerolog"],
        "Config": ["viper", "envconfig", "godotenv"],
        "Validation": ["validator", "ozzo-validation"],
        "HTTP Client": ["resty", "req"],
    }
    
    print("\n--- Detected Technologies ---")
    for category, keywords in categories.items():
        found = [(d, v) for d, v in deps if any(k in d.lower() for k in keywords)]
        if found:
            print(f"  {category}: {', '.join([f'{d}@{v}' for d, v in found[:3]])}")
    
    # List all deps
    print("\n--- All Dependencies (first 15) ---")
    for dep, version in deps[:15]:
        short_dep = dep.split("/")[-1] if "/" in dep else dep
        print(f"  {short_dep}: {version}")
    if len(deps) > 15:
        print(f"  ... and {len(deps) - 15} more")

def find_and_analyze(directory):
    """Find and analyze all package.json and go.mod files."""
    path = Path(directory)
    
    # Find package.json files
    for pj in path.rglob("package.json"):
        if "node_modules" not in str(pj):
            analyze_package_json(str(pj))
    
    # Find go.mod files
    for gm in path.rglob("go.mod"):
        analyze_go_mod(str(gm))

def main():
    parser = argparse.ArgumentParser(description="Analyze project tech stack")
    parser.add_argument("path", nargs="?", default=".", help="Path to project directory")
    parser.add_argument("--file", help="Specific file to analyze (package.json or go.mod)")
    
    args = parser.parse_args()
    
    if args.file:
        if "package.json" in args.file:
            analyze_package_json(args.file)
        elif "go.mod" in args.file:
            analyze_go_mod(args.file)
        else:
            print("[!] Unsupported file. Use package.json or go.mod")
    else:
        find_and_analyze(args.path)

if __name__ == "__main__":
    main()
