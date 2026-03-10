# Codebase Scanner Scripts v2.1

> Scripts for scanning and documenting any codebase (Go, TS, Python, Java, C#, C++, C) up to 10M+ LOC.

## Quick Start

```bash
# Full scan with hierarchical docs + semantic analysis
python .github/skills/codebase-scanner/scripts/scan_codebase.py --full

# Quick scan (structure only, L0 + L1)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --quick

# Incremental scan (changed files only)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --incremental

# Git diff scan (for PR reviews)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --git-diff main

# Component deep-dive
python .github/skills/codebase-scanner/scripts/scan_codebase.py --component features/workflow

# Semantic analysis only
python .github/skills/codebase-scanner/scripts/scan_semantic.py --all

# Build search index
python .github/skills/codebase-scanner/scripts/build_search_index.py
```

## Scripts Reference

| Script | Purpose | Output |
|--------|---------|--------|
| `scan_codebase.py` | Main orchestrator (v2) | All docs |
| `scan_incremental.py` | Diff/git-based scanning | Updated docs |
| `scan_semantic.py` | Security, tech debt, business rules | SEMANTIC/*.md |
| `build_search_index.py` | Symbol/file search index | SEARCH_INDEX.json |
| `generate_hierarchical_docs.py` | L0-L3 documentation | L0/L1/L2/L3/ |
| `detect_project.py` | Project type detection | project_info.json |
| `analyze_structure.py` | Directory/file analysis | structure.json |
| `analyze_dependencies.py` | Dependency mapping | dependencies.json |
| `extract_apis.py` | API extraction | apis.json |
| `generate_docs.py` | Basic markdown docs | *.md |
| `generate_diagrams.py` | Mermaid diagrams | diagrams/*.mmd |

## Output Structure

```
.github/codebase-docs/
├── L0_EXECUTIVE_SUMMARY.md     # 1-page overview (~500 tokens)
├── L1_ARCHITECTURE/            # High-level architecture (~2000 tokens)
├── L2_DOMAINS/                 # Per-domain docs (~1000 tokens each)
├── L3_MODULES/                 # Module deep-dives (~2000 tokens each)
├── SEMANTIC/                   # Semantic analysis
│   ├── BUSINESS_RULES.md
│   ├── SECURITY_ANALYSIS.md
│   ├── TECH_DEBT.md
│   ├── DATA_FLOW.md
│   └── COMPLEXITY.md
├── QUICK_REFERENCE.md          # Fast lookup table
├── SEARCH_INDEX.json           # Full symbol index (grep, don't load!)
├── AI_NAVIGATION_GUIDE.md      # How AI should navigate
└── INDEX.md                    # Master navigation
```

## For AI Agents

### Navigation Strategy

```
1. ALWAYS read L0_EXECUTIVE_SUMMARY.md first (~500 tokens)
2. Identify the domain you need
3. Read L2_DOMAINS/<domain>/OVERVIEW.md (~1000 tokens)
4. Search for specific symbol in QUICK_REFERENCE.md
5. If not found, grep SEARCH_INDEX.json
6. Read ONLY the specific file needed

⚠️ NEVER load all L3 docs or entire SEARCH_INDEX.json!
```

### Token Budgets

| Task | Load | Tokens |
|------|------|--------|
| Quick question | L0 | ~500 |
| Feature work | L0 + L1 + 1 L2 + 3 files | ~10K |
| Deep debugging | L0 + L1 + L2 + L3 + 5 files | ~20K |

## Requirements

- Python 3.8+
- No external dependencies (uses only standard library)
- Git (for git-diff features)

## Semantic Analysis Options

```bash
# All semantic analyses
python .github/skills/codebase-scanner/scripts/scan_semantic.py --all

# Individual analyses
python .github/skills/codebase-scanner/scripts/scan_semantic.py --business-rules
python .github/skills/codebase-scanner/scripts/scan_semantic.py --security
python .github/skills/codebase-scanner/scripts/scan_semantic.py --tech-debt
python .github/skills/codebase-scanner/scripts/scan_semantic.py --data-flow
python .github/skills/codebase-scanner/scripts/scan_semantic.py --complexity
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-01-22 | AI Navigation, Search Index, Context Window Management |
| 2.0.0 | 2026-01-22 | Hierarchical docs, incremental, semantic analysis |
| 1.0.0 | 2026-01-22 | Initial release |
