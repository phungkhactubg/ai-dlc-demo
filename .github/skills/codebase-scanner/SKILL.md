# codebase-scanner

## The Skill Ingestion Mandate (Logical Circuit Breaker - HARD LOCK)
**CRITICAL**: You are forbidden from performing ANY development, architecture, or research task until you have 100% ingested this `SKILL.md` file.

1.  **NO PARTIAL LOADING**: You cannot rely on "general knowledge" of your role. You must read THIS specific version of the skill.
2.  **SEQUENTIAL CHUNKING**: If this file exceeds 800 lines, you MUST read it in sequential chunks (e.g., lines 1-800, then 801-1600, etc.) until you reach the EXPLICIT end of the file.
3.  **INGESTION CONFIRMATION**: **AFTER** you have physically read the entire file, you must output a SINGLE line to confirm coverage:
    > **SKILL_INGESTION_STATUS: 100% COMPLETE | EOF VERIFIED**
    *(Do not print any tables or large manifests)*
4.  **TRACEABILITY**: Every action you take must be traceable back to a specific instruction in this `SKILL.md`.
5.  **BLOCKING ALGORITHM**: Any tool call (except `view_file` on this skill) made before the Ingestion Manifest is complete is a **FATAL VIOLATION**.

> **Purpose**: Scan any codebase (from small to 10M+ LOC), generate hierarchical documentation, and enable AI Agents to quickly understand project architecture at any depth level.

---

## 🆕 v2.0 Features

- **Incremental Scanning** - Only scan changed files, 10x faster
- **Hierarchical Documentation** - L0 to L3 depth levels for any audience
- **Semantic Analysis** - Understand business rules, data flow, security
- **Git Integration** - Scan based on git diff, commits, branches
- **Chunked Output** - Handle 10M+ LOC codebases without memory issues

---

## Team Collaboration & Modes
You operate in two distinct modes depending on how you are invoked:

### 1. Orchestrated Mode (Subordinate)
*   **Trigger**: Activated by the **Expert PM & BA Orchestrator** (Phase 1/4) or **Expert Researcher** (Phase 0) to understand the codebase before major changes.
*   **Protocol**: 
    - **Goal**: Provide the "Landscape" for planning.
    - **Execution**: Target only relevant domains specified in the task context.
    - **Deliverable**: Update docs in `project-documentation/codebase-docs/` to provide high-level context for other agents.

### 2. Standalone Mode (Independent Expert)
*   **Trigger**: Explicitly called by the **User** via `/scan-*` commands for immediate codebase insight or auditing.
*   **Protocol**:
    - **Goal**: Act as a project archaeologist. Answer specific questions about the codebase structure or technical debt.
    - **Direct Insights**: Deliver findings directly in the response.
    - **Traceability**: If requested, link specific findings to source code for the User's immediate review.

---

## Quick Start Commands

### Basic Scanning

| Command | Description | Speed |
|---------|-------------|-------|
| `/scan-project` | Full codebase scan, all 4 levels | Slow |
| `/scan-quick` | Structure only (L0 + L1) | Fast |
| `/scan-component <path>` | Deep dive into specific module | Medium |
| `/scan-refresh` | Update existing docs | Fast |

### Incremental Scanning (NEW)

| Command | Description | Use Case |
|---------|-------------|----------|
| `/scan-diff` | Only files changed since last scan | Daily updates |
| `/scan-since <date>` | Files changed since date | Weekly reviews |
| `/scan-git-diff [branch]` | Files in git diff vs branch | PR reviews |
| `/scan-commits <n>` | Files changed in last N commits | Quick catch-up |

### Semantic Analysis (NEW)

| Command | Description |
|---------|-------------|
| `/scan-business-rules` | Extract business logic patterns |
| `/scan-data-flow` | Trace data transformations |
| `/scan-security` | Security-focused analysis |
| `/scan-tech-debt` | Identify technical debt areas |
| `/scan-complexity` | Code complexity metrics |

---

## Hierarchical Documentation Structure

Documentation is organized in **4 levels** for different audiences:

```
project-documentation/codebase-docs/
├── <repo_name>/                # Repository specific documentation
│   ├── L0_EXECUTIVE_SUMMARY.md # 1-page overview (C-level, new devs)
│   ├── L1_ARCHITECTURE/        # High-level architecture
│   │   ├── OVERVIEW.md
│   │   ├── TECH_STACK.md           # Technologies used
│   │   ├── DESIGN_PATTERNS.md      # Patterns in use
│   │   └── DIAGRAMS.md             # High-level diagrams
│   │   ├── ...
│   ├── L2_DOMAINS/             # Domain-level docs
│   │   ├── INDEX.md                # Domain index
│   │   ├── workflow/               # Per-domain folder
│   │   │   ├── OVERVIEW.md
│   │   │   ├── API.md
│   │   │   └── DATA_MODELS.md
│   │   ├── authorization/
│   │   │   ├── OVERVIEW.md
│   │   │   ├── API.md
│   │   │   └── DATA_MODELS.md
│   │   ├── ...
│   ├── L3_MODULES/                 # Module deep-dives (Developers)
│   │   ├── INDEX.md                # Full module index
│   │   ├── workflow/
│   │   │   ├── executor/
│   │   │   │   ├── OVERVIEW.md
│   │   │   │   ├── INTERFACES.md
│   │   │   │   ├── FUNCTIONS.md
│   │   │   │   └── DEPENDENCIES.md
│   │   │   └── blocks/
│   │   └── ...
│   ├── SEMANTIC/                   # Semantic analysis results
│   │   ├── BUSINESS_RULES.md
│   │   ├── DATA_FLOW.md
│   │   ├── SECURITY_ANALYSIS.md
│   │   └── TECH_DEBT.md
│   ├── INDEX.md                    # Master searchable index
│   ├── SEARCH_INDEX.json           # Full-text search data
│   └── .scan_metadata.json         # Last scan info for incremental
```

---

## Level Descriptions

### L0: Executive Summary (1 page)
**Audience**: Executives, new team members, stakeholders
**Content**: 
- What does this system do?
- Key technologies
- Team/ownership info
- Quick stats (LOC, modules, APIs)

### L1: Architecture Overview
**Audience**: Architects, tech leads, senior developers
**Content**:
- System architecture diagram
- Technology decisions
- Design patterns used
- Infrastructure overview

### L2: Domain Documentation  
**Audience**: Team leads, feature developers
**Content**:
- Domain boundaries
- Public APIs per domain
- Data models
- Integration points

### L3: Module Deep-Dives
**Audience**: Developers working on specific code
**Content**:
- Every public function/class
- Internal implementation notes
- Dependencies (imports/exports)
- Test coverage info

---

## Scripts

### Main Commands

```bash
# Full scan with all levels
python .github/skills/codebase-scanner/scripts/scan_codebase.py --full

# Quick scan (L0 + L1 only)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --quick

# Incremental scan (changed files only)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --incremental

# Scan based on git diff
python .github/skills/codebase-scanner/scripts/scan_codebase.py --git-diff main

# Component deep-dive
python .github/skills/codebase-scanner/scripts/scan_codebase.py --component features/workflow

# Semantic analysis
python .github/skills/codebase-scanner/scripts/scan_semantic.py --all
python .github/skills/codebase-scanner/scripts/scan_semantic.py --business-rules
python .github/skills/codebase-scanner/scripts/scan_semantic.py --security
```

### Script Reference

| Script | Purpose |
|--------|---------|
| `scan_codebase.py` | Main orchestrator (v2) |
| `scan_incremental.py` | Incremental/diff scanning |
| `scan_semantic.py` | Semantic analysis |
| `detect_project.py` | Project type detection |
| `analyze_structure.py` | Directory/file analysis |
| `analyze_dependencies.py` | Dependency mapping |
| `extract_apis.py` | API extraction |
| `generate_hierarchical_docs.py` | L0-L3 doc generator |
| `generate_diagrams.py` | Mermaid diagrams |
| `build_search_index.py` | Full-text search index |

---

## Detailed Command Instructions

### `/scan-project` - Full Hierarchical Scan

**When to use**: First time, or major refactoring

**Execution**:
```bash
python .github/skills/codebase-scanner/scripts/scan_codebase.py --full
```
*(Note: Output will be automatically saved to `project-documentation/codebase-docs/<repo_name>/`)*

**Generates**: All L0, L1, L2, L3 documentation + semantic analysis

---

### `/scan-diff` - Incremental Scan

**When to use**: Daily updates, after small changes

**Execution**:
```bash
python .github/skills/codebase-scanner/scripts/scan_incremental.py --mode diff --output project-documentation/codebase-docs
```

**How it works**:
1. Reads `.scan_metadata.json` for last scan timestamp
2. Finds files modified since then (using file mtime)
3. Updates only affected L2/L3 docs
4. Regenerates L0/L1 summaries
5. Updates search index

---

### `/scan-git-diff [branch]` - Git-Based Scan

**When to use**: PR reviews, branch comparisons

**Execution**:
```bash
python .github/skills/codebase-scanner/scripts/scan_incremental.py --mode git-diff --branch main
```

**How it works**:
1. Runs `git diff --name-only <branch>`
2. Analyzes only changed files
3. Generates focused report

---

### `/scan-business-rules` - Business Logic Extraction

**When to use**: Understanding domain logic, onboarding

**Execution**:
```bash
python .github/skills/codebase-scanner/scripts/scan_semantic.py --business-rules
```

**Detects**:
- Validation patterns
- Business rule comments
- Decision trees (if/switch patterns)
- Domain-specific terminology
- State machines

---

### `/scan-security` - Security Analysis

**When to use**: Security audits, PR reviews

**Execution**:
```bash
python .github/skills/codebase-scanner/scripts/scan_semantic.py --security
```

**Checks**:
- SQL injection risks
- XSS vulnerabilities
- Hardcoded credentials
- Insecure dependencies
- Authentication patterns
- Authorization checks
- Input validation

---

### `/scan-tech-debt` - Technical Debt Finder

**When to use**: Sprint planning, refactoring decisions

**Execution**:
```bash
python .github/skills/codebase-scanner/scripts/scan_semantic.py --tech-debt
```

**Identifies**:
- TODO/FIXME/HACK comments
- Long functions (>50 lines)
- High cyclomatic complexity
- Duplicated code patterns
- Deprecated API usage
- Missing error handling
- Missing tests

---

## Handling Large Codebases (1M+ LOC)

### Chunked Processing

For codebases > 500K LOC, the scanner automatically:
1. Processes files in batches of 1000
2. Writes intermediate results to disk
3. Merges results at the end
4. Generates chunked L3 docs (100 files per doc)

### Memory Optimization

```bash
# Low memory mode (slower but handles any size)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --low-memory

# Parallel processing (faster on multi-core)
python .github/skills/codebase-scanner/scripts/scan_codebase.py --workers 4
```

### Recommended Workflow for Huge Codebases

1. **Initial scan**: `/scan-project` (may take 10-30 min for 10M+ LOC)
2. **Daily updates**: `/scan-diff` (seconds to minutes)
3. **PR reviews**: `/scan-git-diff` (seconds)
4. **Deep dives**: `/scan-component <path>` (as needed)

---

## AI Agent Integration

### How AI Agents Should Use This

1. **Starting a new session**:
   - Read `L0_EXECUTIVE_SUMMARY.md` first
   - Then `L1_ARCHITECTURE/OVERVIEW.md`
   - Check `INDEX.md` for navigation

2. **Working on specific feature**:
   - Read relevant `L2_DOMAINS/<domain>/OVERVIEW.md`
   - Dive into `L3_MODULES/<domain>/<module>/` as needed

3. **Code review**:
   - Run `/scan-git-diff`
   - Check `SEMANTIC/SECURITY_ANALYSIS.md`

4. **Debugging issues**:
   - Use `SEARCH_INDEX.json` to find related files
   - Check `SEMANTIC/DATA_FLOW.md` for tracing

### Quick Navigation Commands

| What needs refactoring? | `SEMANTIC/TECH_DEBT.md` |

---

## 🤖 Agent Interactive Commands

As an AI Agent, you should recognize and implement the following logic when the user uses these slash commands or requests:

### `/load-overview`
**Action**: Read `L0_EXECUTIVE_SUMMARY.md` and `L1_ARCHITECTURE/OVERVIEW.md`.
**Goal**: Get high-level project context.

### `/load-domain <name>`
**Action**: Read `L2_DOMAINS/<name>/OVERVIEW.md` and `QUICK_REFERENCE.md`.
**Goal**: Focus on a specific domain/feature.

### `/load-module <domain>/<module>`
**Action**: Read `L3_MODULES/<domain>/<module>/OVERVIEW.md`.
**Goal**: Deep dive into specific implementation.

### `/load-semantic <type>`
**Action**: Read `SEMANTIC/<TYPE>_ANALYSIS.md` (e.g., `SEMANTIC/SECURITY_ANALYSIS.md`).
**Goal**: Load specific analysis (security, rules, debt, flow).

### `/find-logic <query>`
**Action**: Use `grep_search` on `SEARCH_INDEX.json` and load matching file headers.
**Goal**: Find specific logic or symbols.

### `/fix-bug <description>`
**Action**: 
1. Use `grep_search` on `SEARCH_INDEX.json` to find relevant files.
2. Load `L2_DOMAINS` overview for identified domains.
3. Check `SEMANTIC/DATA_FLOW.md` and `TECH_DEBT.md`.
4. Propose diagnosis and fix plan.

### `/review <module>`
**Action**: Triggers an automated code review for a specific module using the `expert-code-reviewer` skill.
**Action**: Use `.github/skills/expert-code-reviewer/SKILL.md` to run validation scripts and generates a report in `report-review/<module>`.

### `/verify-arch <task>`
**Action**: Load L0, L1, and relevant L2 docs before proposing changes.
**Goal**: Ensure changes align with design patterns.

---

## Configuration

Create `.github/codebase-scanner.config.json` for project-specific settings:

```json
{
  "exclude_patterns": [
    "node_modules",
    "vendor",
    ".git",
    "dist",
    "build",
    "*.min.js"
  ],
  "include_languages": ["go", "typescript", "python", "java", "csharp", "cpp", "c"],
  "max_file_size_kb": 500,
  "max_function_lines": 50,
  "complexity_threshold": 10,
  "domains": {
    "workflow": "features/workflow",
    "auth": "features/authorization",
    "frontend": "apps/frontend"
  },
  "business_rule_patterns": [
    "// RULE:",
    "// Business:",
    "@BusinessRule"
  ],
  "security_patterns": {
    "sql_injection": ["fmt.Sprintf.*SELECT", "query\\s*\\+"],
    "hardcoded_secrets": ["password\\s*=\\s*[\"']", "api_key\\s*="]
  }
}
```

---

## 🧠 AI Navigation Strategy (CRITICAL)

### The Problem: Context Window Limits

| AI Model | Context Window | Usable for Docs |
|----------|----------------|-----------------|
| GPT-4 | 128K tokens | ~500KB text |
| Claude 3 | 200K tokens | ~800KB text |
| Gemini 1.5 | 1M tokens | ~4MB text |

A 1M+ LOC codebase generates **5-50MB of docs** - impossible to load entirely!

### The Solution: Lazy Hierarchical Loading

```
ALWAYS start with L0 (~500 tokens)
     ↓
Need more? Load L1 (~1500 tokens)
     ↓
Working on domain? Load ONE L2 (~1000 tokens)
     ↓
Need implementation? Load ONE L3 (~2000 tokens)
     ↓
Need specific code? Load ONE source file

⚠️ NEVER load: All L3 docs, entire SEARCH_INDEX.json, multiple domains
```

### Token Budget Guidelines

| Task | What to Load | Est. Tokens |
|------|--------------|-------------|
| Quick question | L0 only | ~500 |
| Feature work | L0 + L1 + 1 L2 + 3 files | ~10,000 |
| Deep debugging | L0 + L1 + L2 + L3 + 5 files | ~20,000 |
| Security audit | L0 + SEMANTIC/SECURITY | ~5,000 |
| Architecture review | L0 + L1 + all L2 headers | ~15,000 |

### Navigation Workflow

1. **Read L0_EXECUTIVE_SUMMARY.md** (MANDATORY - ~30 sec)
2. **Identify domain** from L0 module list
3. **Read L2_DOMAINS/<domain>/OVERVIEW.md** (if needed)
4. **Search symbol/file** using:
   - `QUICK_REFERENCE.md` for common lookups
   - `grep_search` on SEARCH_INDEX.json for specific symbols
5. **Read ONLY that specific file** - not entire module!

### Key Navigation Files

| File | Size | Purpose |
|------|------|---------|
| `L0_EXECUTIVE_SUMMARY.md` | ~1 KB | Start here - always |
| `QUICK_REFERENCE.md` | ~3.5 KB | Symbol/domain lookup table |
| `AI_NAVIGATION_GUIDE.md` | ~8 KB | Detailed navigation instructions |
| `SEARCH_INDEX.json` | ~1.6 MB | Full index (grep, don't load!) |

### Anti-Patterns (DON'T!)

```
❌ Load all L3 documentation at once
❌ Read entire SEARCH_INDEX.json into context
❌ Load multiple domains simultaneously
❌ Skip L0 and jump to source code
```

### Best Practices (DO!)

```
✅ Always read L0 first
✅ Load ONE domain at a time
✅ Use grep_search on SEARCH_INDEX.json
✅ Read specific files, not directories
✅ Keep total under 30K tokens
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-01-22 | AI Navigation Strategy, Search Index, Context Window Management |
| 2.0.0 | 2026-01-22 | Hierarchical docs, incremental scanning, semantic analysis |
| 1.0.0 | 2026-01-22 | Initial release |


---

## Troubleshooting

### Scan is slow
- Use `--quick` for structure only
- Use `--incremental` for updates
- Increase `--workers` on multi-core machines

### Out of memory
- Use `--low-memory` mode
- Increase `--chunk-size` value
- Exclude large binary/generated files

### Missing business rules
- Add custom patterns in config
- Ensure consistent comment format
- Use `// RULE:` prefix for auto-detection

### Git diff not working
- Ensure git is installed
- Check branch name spelling
- Verify you're in a git repository
