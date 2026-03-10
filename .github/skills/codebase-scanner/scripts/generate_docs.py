#!/usr/bin/env python3
"""
Documentation Generator - Generates markdown documentation from scan data.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class DocumentationGenerator:
    """Generates markdown documentation from scan results."""
    
    def __init__(self, output_dir: Path, verbose: bool = False):
        self.output_dir = Path(output_dir)
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(f"   [docs] {message}")
    
    def generate(self, scan_data: Dict, quick_mode: bool = False) -> List[str]:
        """Generate all documentation files."""
        generated = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate ARCHITECTURE.md
        self._generate_architecture(scan_data)
        generated.append("ARCHITECTURE.md")
        
        # Generate COMPONENT_MAP.md
        self._generate_component_map(scan_data)
        generated.append("COMPONENT_MAP.md")
        
        # Generate TECH_STACK.md
        self._generate_tech_stack(scan_data)
        generated.append("TECH_STACK.md")
        
        if not quick_mode:
            # Generate API_SURFACE.md
            if scan_data.get("apis"):
                self._generate_api_surface(scan_data)
                generated.append("API_SURFACE.md")
            
            # Generate DEPENDENCY_GRAPH.md
            if scan_data.get("dependencies"):
                self._generate_dependency_graph(scan_data)
                generated.append("DEPENDENCY_GRAPH.md")
        
        return generated
    
    def _generate_architecture(self, scan_data: Dict):
        """Generate ARCHITECTURE.md."""
        project = scan_data.get("project_info", {})
        structure = scan_data.get("structure", {})
        
        content = f"""# Project Architecture

> Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview

- **Project Type**: {project.get("type", "Unknown")}
- **Languages**: {", ".join(project.get("languages", []))}
- **Architecture Pattern**: {project.get("architecture", "Not detected")}

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
"""
        for fw in project.get("frameworks", []):
            content += f"| Framework | {fw} | - |\n"
        
        if project.get("database"):
            content += f"| Database | {project.get('database')} | - |\n"
        
        if project.get("ci_cd"):
            content += f"| CI/CD | {project.get('ci_cd')} | - |\n"

        content += f"""
## Project Statistics

- **Total Files**: {structure.get("total_files", 0)}
- **Total Directories**: {structure.get("total_dirs", 0)}
- **Total Lines of Code**: {structure.get("total_lines", 0):,}

## Entry Points

| File | Type | Purpose |
|------|------|---------|
"""
        for entry in structure.get("entry_points", [])[:10]:
            content += f"| `{entry.get('file', '')}` | {entry.get('type', '')} | {entry.get('language', '')} entry |\n"

        content += """
## Module Overview

| Module | Path | Files |
|--------|------|-------|
"""
        for module in structure.get("modules", [])[:15]:
            content += f"| {module.get('name', '')} | `{module.get('path', '')}` | {module.get('file_count', 0)} |\n"

        content += """
## File Categories

| Category | Count |
|----------|-------|
"""
        categories = structure.get("categories", {})
        for cat, files in categories.items():
            content += f"| {cat.capitalize()} | {len(files)} |\n"

        content += """
## Important Files

| File | Purpose |
|------|---------|
"""
        for imp in structure.get("important_files", [])[:10]:
            content += f"| `{imp.get('file', '')}` | {imp.get('purpose', '')} |\n"

        self._write_file("ARCHITECTURE.md", content)
    
    def _generate_component_map(self, scan_data: Dict):
        """Generate COMPONENT_MAP.md."""
        structure = scan_data.get("structure", {})
        
        content = f"""# Component Map

> Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Directory Structure

```
{structure.get("root", ".")}
"""
        # Add top-level directories
        for name, info in structure.get("by_directory", {}).items():
            content += f"├── {name}/ ({info.get('file_count', 0)} files) - {info.get('purpose', 'Unknown')}\n"
        
        content += "```\n\n## Components\n\n"
        
        for module in structure.get("modules", []):
            content += f"""### {module.get("name", "Unknown")}

- **Path**: `{module.get("path", "")}`
- **Type**: {module.get("type", "module")}
- **Files**: {module.get("file_count", 0)}

---

"""
        
        content += """## Largest Files

| File | Size | Lines |
|------|------|-------|
"""
        for f in structure.get("largest_files", [])[:10]:
            size_kb = f.get("size", 0) / 1024
            content += f"| `{f.get('path', '')}` | {size_kb:.1f} KB | {f.get('lines', 0)} |\n"

        self._write_file("COMPONENT_MAP.md", content)
    
    def _generate_tech_stack(self, scan_data: Dict):
        """Generate TECH_STACK.md."""
        project = scan_data.get("project_info", {})
        
        content = f"""# Technology Stack

> Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Languages

"""
        for lang in project.get("languages", []):
            content += f"- **{lang}**\n"
        
        content += "\n## Frameworks & Libraries\n\n"
        for fw in project.get("frameworks", []):
            content += f"- {fw}\n"
        
        content += f"""
## Build & Development

- **Build System**: {project.get("build_system", "Not detected")}
- **Package Manager**: {project.get("package_manager", "Not detected")}
- **Test Framework**: {project.get("test_framework", "Not detected")}

## Infrastructure

- **CI/CD**: {project.get("ci_cd", "Not detected")}
- **Database**: {project.get("database", "Not detected")}

## Configuration Files

| File | Language | Framework |
|------|----------|-----------|
"""
        for cfg in project.get("config_files", [])[:15]:
            content += f"| `{cfg.get('file', '')}` | {cfg.get('language', '-')} | {cfg.get('framework', '-')} |\n"

        self._write_file("TECH_STACK.md", content)
    
    def _generate_api_surface(self, scan_data: Dict):
        """Generate API_SURFACE.md."""
        apis = scan_data.get("apis", {})
        
        content = f"""# API Surface

> Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## HTTP Endpoints

| Method | Path | Handler | File |
|--------|------|---------|------|
"""
        for ep in apis.get("endpoints", [])[:50]:
            content += f"| {ep.get('method', '')} | `{ep.get('path', '')}` | {ep.get('handler', '')} | `{ep.get('file', '')}` |\n"

        content += "\n## Interfaces\n\n"
        for iface in apis.get("interfaces", [])[:20]:
            content += f"### {iface.get('name', '')}\n\n"
            content += f"- **File**: `{iface.get('file', '')}`\n"
            content += f"- **Language**: {iface.get('language', '')}\n\n"

        self._write_file("API_SURFACE.md", content)
    
    def _generate_dependency_graph(self, scan_data: Dict):
        """Generate DEPENDENCY_GRAPH.md."""
        deps = scan_data.get("dependencies", {})
        
        content = f"""# Dependency Graph

> Auto-generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Most Imported Modules

| Module | Imported By |
|--------|-------------|
"""
        for m in deps.get("most_imported", [])[:10]:
            content += f"| `{m.get('module', '')}` | {m.get('imported_by_count', 0)} modules |\n"

        content += "\n## Most Dependencies\n\n| Module | Import Count |\n|--------|-------------|\n"
        for m in deps.get("most_dependent", [])[:10]:
            content += f"| `{m.get('module', '')}` | {m.get('import_count', 0)} |\n"

        if deps.get("circular_deps"):
            content += "\n## ⚠️ Circular Dependencies\n\n"
            for c in deps.get("circular_deps", []):
                content += f"- {' → '.join(c.get('cycle', []))}\n"

        self._write_file("DEPENDENCY_GRAPH.md", content)
    
    def generate_component_doc(self, component_data: Dict, output_file: Path):
        """Generate documentation for a single component."""
        content = f"""# Component: {component_data.get("name", "Unknown")}

> Path: `{component_data.get("path", "")}`

## Structure

- **Total Files**: {component_data.get("structure", {}).get("total_files", 0)}
- **Total Lines**: {component_data.get("structure", {}).get("total_lines", 0)}

## Files

| File | Lines |
|------|-------|
"""
        for f in component_data.get("structure", {}).get("largest_files", [])[:20]:
            content += f"| `{f.get('path', '')}` | {f.get('lines', 0)} |\n"

        content += "\n## APIs\n\n"
        for ep in component_data.get("apis", {}).get("endpoints", []):
            content += f"- `{ep.get('method', '')} {ep.get('path', '')}`\n"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _write_file(self, filename: str, content: str):
        """Write content to file."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"Generated: {filepath}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Input directory with JSON files")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    scan_data = {}
    
    for json_file in ["project_info.json", "structure.json", "dependencies.json", "apis.json"]:
        path = input_dir / json_file
        if path.exists():
            with open(path) as f:
                key = json_file.replace(".json", "")
                scan_data[key] = json.load(f)
    
    gen = DocumentationGenerator(Path(args.output), args.verbose)
    gen.generate(scan_data)
