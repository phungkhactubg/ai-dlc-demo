#!/usr/bin/env python3
"""
Search Index Builder - Creates a full-text searchable index for AI Agents.
Enables quick lookup of relevant files/modules without loading entire documentation.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
import argparse


class SearchIndexBuilder:
    """Builds searchable index for AI navigation."""
    
    def __init__(self, root_dir: Path, output_dir: Path, verbose: bool = False):
        self.root_dir = Path(root_dir).absolute()
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        
        # Index structures
        self.file_index: Dict[str, Dict] = {}
        self.symbol_index: Dict[str, List[Dict]] = {}  # symbol -> [locations]
        self.keyword_index: Dict[str, List[str]] = {}  # keyword -> [file paths]
        self.module_summaries: Dict[str, str] = {}
    
    def log(self, msg: str):
        if self.verbose:
            print(f"   [index] {msg}")
    
    def build(self):
        """Build all indexes."""
        print("\n📇 Building Search Index...")
        
        self._index_files()
        self._extract_symbols()
        self._build_keyword_index()
        self._generate_summaries()
        self._save_indexes()
        
        print(f"✅ Index built: {len(self.file_index)} files, {len(self.symbol_index)} symbols")
    
    def _index_files(self):
        """Index all source files with metadata."""
        source_exts = {".go", ".py", ".ts", ".tsx", ".js", ".jsx"}
        exclude_dirs = {"node_modules", "vendor", ".git", "dist", "build", "static"}
        
        for path in self.root_dir.rglob("*"):
            if path.is_file() and path.suffix in source_exts:
                parts = path.relative_to(self.root_dir).parts
                if any(ex in parts for ex in exclude_dirs):
                    continue
                
                rel_path = str(path.relative_to(self.root_dir))
                
                # Get file info
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.count('\n')
                    
                    # Detect module/domain
                    domain = parts[1] if len(parts) > 2 and parts[0] in ["features", "apps"] else parts[0]
                    
                    # Extract first doc comment
                    doc_match = re.search(r'(?://|#|/\*\*?)\s*(.{10,100})', content)
                    description = doc_match.group(1).strip() if doc_match else ""
                    
                    self.file_index[rel_path] = {
                        "path": rel_path,
                        "domain": domain,
                        "language": path.suffix[1:],
                        "lines": lines,
                        "description": description[:100],
                    }
                except:
                    pass
    
    def _extract_symbols(self):
        """Extract public symbols (functions, classes, interfaces)."""
        patterns = {
            ".go": [
                (r'func\s+(\w+)\s*\(', 'function'),
                (r'type\s+(\w+)\s+struct', 'struct'),
                (r'type\s+(\w+)\s+interface', 'interface'),
            ],
            ".ts": [
                (r'export\s+(?:async\s+)?function\s+(\w+)', 'function'),
                (r'export\s+class\s+(\w+)', 'class'),
                (r'export\s+interface\s+(\w+)', 'interface'),
                (r'export\s+const\s+(\w+)', 'constant'),
            ],
            ".tsx": [
                (r'export\s+(?:async\s+)?function\s+(\w+)', 'function'),
                (r'export\s+const\s+(\w+)', 'component'),
            ],
            ".py": [
                (r'^class\s+(\w+)', 'class'),
                (r'^def\s+(\w+)', 'function'),
            ],
            ".java": [
                (r'public\s+(?:abstract\s+)?class\s+(\w+)', 'class'),
                (r'public\s+interface\s+(\w+)', 'interface'),
                (r'(?:public|protected|private)\s+[\w<>]+\s+(\w+)\s*\([^;{]*\)\s*(?:throws\s+[\w,\s]+)?\{', 'method'),
                (r'@(RestController|Controller|Service|Repository|Component|Bean|RequestMapping|GetMapping|PostMapping)', 'annotation'),
            ],
            ".cs": [
                (r'(?:public|internal|private|protected)\s+(?:abstract\s+|partial\s+|static\s+)?class\s+(\w+)', 'class'),
                (r'(?:public|internal|private|protected)\s+interface\s+(\w+)', 'interface'),
                (r'(?:public|private|protected|internal)\s+(?:static\s+|async\s+|virtual\s+|override\s+)?[\w<>]+\s+(\w+)\s*\([^;{]*\)\s*\{', 'method'),
                (r'\[(HttpGet|HttpPost|HttpPut|HttpDelete|Route|Authorize|AllowAnonymous)\]', 'attribute'),
            ],
            ".cpp": [
                (r'class\s+(\w+)', 'class'),
                (r'struct\s+(\w+)', 'struct'),
                (r'(?:\w+::)?(\w+)\s*\([^;{]*\)\s*(?:const\s+)?\{', 'function'),
            ],
            ".hpp": [
                (r'class\s+(\w+)', 'class'),
                (r'struct\s+(\w+)', 'struct'),
            ],
            ".c": [
                (r'struct\s+(\w+)', 'struct'),
                (r'^(\w+)\s*\([^;{]*\)\s*\{', 'function'),
            ],
            ".h": [
                (r'struct\s+(\w+)', 'struct'),
                (r'(\w+)\s*\([^;{]*\);', 'prototype'),
            ],
        }
        
        for rel_path, info in self.file_index.items():
            full_path = self.root_dir / rel_path
            lang_patterns = patterns.get(f".{info['language']}", [])
            
            if not lang_patterns:
                continue
            
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                
                for pattern, symbol_type in lang_patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        symbol_name = match.group(1)
                        line_num = content[:match.start()].count('\n') + 1
                        
                        if symbol_name not in self.symbol_index:
                            self.symbol_index[symbol_name] = []
                        
                        self.symbol_index[symbol_name].append({
                            "file": rel_path,
                            "line": line_num,
                            "type": symbol_type,
                            "domain": info["domain"],
                        })
            except:
                pass
    
    def _build_keyword_index(self):
        """Build keyword to file mapping."""
        # Common architecture keywords
        keywords = [
            "controller", "service", "repository", "model", "handler",
            "middleware", "router", "config", "util", "helper",
            "executor", "adapter", "interface", "factory", "builder",
            "store", "slice", "hook", "component", "page",
            "auth", "login", "user", "admin", "permission",
            "workflow", "block", "trigger", "schedule", "webhook",
            "api", "http", "grpc", "graphql", "rest",
            "database", "mongo", "postgres", "mysql", "redis",
            "test", "spec", "mock", "fixture",
        ]
        
        for rel_path, info in self.file_index.items():
            path_lower = rel_path.lower()
            for kw in keywords:
                if kw in path_lower:
                    if kw not in self.keyword_index:
                        self.keyword_index[kw] = []
                    self.keyword_index[kw].append(rel_path)
    
    def _generate_summaries(self):
        """Generate per-domain summaries."""
        domains: Dict[str, List[str]] = {}
        
        for rel_path, info in self.file_index.items():
            domain = info["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(rel_path)
        
        for domain, files in domains.items():
            total_lines = sum(self.file_index[f]["lines"] for f in files)
            
            # Get key file types
            file_types = {}
            for f in files:
                lang = self.file_index[f]["language"]
                file_types[lang] = file_types.get(lang, 0) + 1
            
            self.module_summaries[domain] = {
                "name": domain,
                "file_count": len(files),
                "total_lines": total_lines,
                "languages": file_types,
                "sample_files": files[:5],
            }
    
    def _save_indexes(self):
        """Save all indexes to files."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Main search index
        search_index = {
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "total_files": len(self.file_index),
                "total_symbols": len(self.symbol_index),
                "total_keywords": len(self.keyword_index),
            },
            "files": self.file_index,
            "symbols": self.symbol_index,
            "keywords": self.keyword_index,
            "domains": self.module_summaries,
        }
        
        with open(self.output_dir / "SEARCH_INDEX.json", "w", encoding="utf-8") as f:
            json.dump(search_index, f, indent=2, ensure_ascii=False)
        
        # Generate human-readable quick reference
        self._generate_quick_reference()
    
    def _generate_quick_reference(self):
        """Generate markdown quick reference for AI."""
        content = f"""# 🔍 Quick Reference Index

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **Total Files**: {len(self.file_index)} | **Symbols**: {len(self.symbol_index)}

## How AI Agents Should Use This

### Navigation Strategy

1. **Start Here** → Read `L0_EXECUTIVE_SUMMARY.md` (~500 tokens)
2. **Need Architecture?** → Read `L1_ARCHITECTURE/OVERVIEW.md` (~1500 tokens)
3. **Working on Feature?** → Read `L2_DOMAINS/<domain>/OVERVIEW.md` (~1000 tokens)
4. **Need Code Details?** → Read `L3_MODULES/<module>/OVERVIEW.md` (~2000 tokens)
5. **Looking for Symbol?** → Search in `SEARCH_INDEX.json`, then read specific file

### ⚠️ NEVER load all L3 docs at once! Use targeted reading.

---

## Domain Quick Lookup

| Domain | Files | Lines | Main Language |
|--------|-------|-------|---------------|
"""
        for domain, info in sorted(self.module_summaries.items(), key=lambda x: -x[1]["file_count"]):
            main_lang = max(info["languages"].items(), key=lambda x: x[1])[0] if info["languages"] else "-"
            content += f"| {domain} | {info['file_count']} | {info['total_lines']:,} | {main_lang} |\n"
        
        content += """
---

## Common Symbol Lookup

### Controllers/Handlers
"""
        for sym, locs in sorted(self.symbol_index.items()):
            if "Controller" in sym or "Handler" in sym:
                loc = locs[0]
                content += f"- `{sym}` → `{loc['file']}:{loc['line']}`\n"
                if len([s for s in self.symbol_index if "Controller" in s or "Handler" in s]) > 20:
                    break
        
        content += "\n### Services\n"
        count = 0
        for sym, locs in sorted(self.symbol_index.items()):
            if "Service" in sym:
                loc = locs[0]
                content += f"- `{sym}` → `{loc['file']}:{loc['line']}`\n"
                count += 1
                if count > 15:
                    break
        
        content += f"""
---

## Keyword Search Guide

| Looking For | Keyword | Sample Files |
|-------------|---------|--------------|
"""
        important_kw = ["auth", "workflow", "api", "database", "config", "service", "controller"]
        for kw in important_kw:
            if kw in self.keyword_index:
                files = self.keyword_index[kw][:3]
                content += f"| {kw.title()} | `{kw}` | {len(self.keyword_index[kw])} files |\n"
        
        content += """
---

## Reading Strategy for AI

```
For ANY task:
1. Read L0 → Understand project (mandatory, ~30 sec)
2. Identify domain → Read L2/<domain> (~30 sec)
3. Find specific file → Use SEARCH_INDEX.json
4. Read ONLY that file → Not entire module!

DO NOT:
- Load all L3 docs
- Read entire SEARCH_INDEX.json into context
- Try to understand everything at once
```
"""
        
        with open(self.output_dir / "QUICK_REFERENCE.md", "w", encoding="utf-8") as f:
            f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Build search index")
    parser.add_argument("--output", "-o", default=".github/codebase-docs", help="Output dir")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    
    args = parser.parse_args()
    
    builder = SearchIndexBuilder(Path.cwd(), Path(args.output), args.verbose)
    builder.build()
    return 0


if __name__ == "__main__":
    exit(main())
