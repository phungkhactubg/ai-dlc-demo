# GitHub Copilot Custom Instructions

> This file provides context and guidelines for GitHub Copilot in this repository.


## The Exhaustive Reading Mandate (NO EXCUSES - HARD LOCK)
**CRITICAL**: You are FORBIDDEN from relying on "partial reads" or "structural assumptions" for ANY documentation file (PRD, SRS, MASTER_PLAN, DETAIL_PLAN, ARCHITECTURE_SPEC).

1.  **100% Ingestion Required**: You MUST read every single line of a requested file. 
2.  **No Arbitrary Truncation**: When using `view_file`, you are FORBIDDEN from requesting small ranges (like 1-100) for files that are larger. You MUST request the maximum allowed chunk (800 lines).
3.  **Sequential Chunking**: If a file exceeds 800 lines, you MUST call `view_file` sequentially (1-800, 801-1600, etc.) until the tool reports the final line.
4.  **"Full Context" Verification**: Claiming "I have full context" before reading the entire file is **Technical Fraud**. 
5.  **Diligence Check**: In your final response after loading context, you MUST state: "Verified Total Lines: [Count] | Reading Status: 100% Complete".

## Project Overview

**System Integration Management Platform** - A comprehensive workflow automation and integration management system.

- **Backend**: Go 1.25+ (Echo Framework, Clean Architecture)
- **Frontend**: React 18+ (Vite, MUI v6, Zustand, TypeScript)
- **Database**: MongoDB
- **Multi-tenancy**: Yes, tenant isolation required

## Architecture Guidelines

### Backend (Go)
- Follow Clean Architecture: `features/<name>/{models,services,repositories,controllers,routers}/`
- All services/repositories MUST have interfaces
- Use dependency injection
- Wrap all errors with context: `fmt.Errorf("service.Method: %w", err)`
- NEVER use `context.TODO()` in production code
- Functions should not exceed 50 lines
- Reference: `.github/skills/expert-go-backend-developer/SKILL.md`

### Frontend (React) 
- Follow Feature-Sliced Design: `src/<feature>/{core,infrastructure,shared,features}/`
- Use Zustand for state management
- Validate all API responses with Zod schemas
- NEVER use `any` type - use `unknown` with type guards
- Reference: `.github/skills/expert-react-frontend-developer/SKILL.md`

### API Integration
- **Contract-First**: Backend Go structs are source of truth
- Frontend Zod schemas MUST match backend exactly
- Use `extract_go_api.py` to generate frontend types from Go

## Coding Standards

### Go
- Use `ctx context.Context` as first parameter 
- Return `error` as last return value
- Document all public functions
- Use table-driven tests

### TypeScript/React
- Strict TypeScript mode
- Use functional components with hooks
- Prefer composition over inheritance
- Use MUI v6 components



## Available Skills

Copilot should reference these skill files for specialized tasks:

| Skill | File | Use When |
|-------|------|----------|
| **Lead Orchestrator (PM/BA)** | `.github/skills/expert-pm-ba-orchestrator/SKILL.md` | **Main SDLC lead, PRDs, Master Plans & Change Mgmt** |
| | `.github/skills/expert-pm-ba-orchestrator/copilot-instructions.md` | *Detailed operational behavior & workflows* |

| Researcher | `.github/skills/expert-researcher/SKILL.md` | Phase 0 Technical Feasibility & Comparative Research |
| Solutions Architect | `.github/skills/expert-solutions-architect/SKILL.md` | Technical Blueprinting & Project Scaffolding |
| Go Backend | `.github/skills/expert-go-backend-developer/SKILL.md` | Feature implementation (Go) |
| React Frontend | `.github/skills/expert-react-frontend-developer/SKILL.md` | Feature implementation (React/TS) |
| **Python AI/ML** | `.github/skills/expert-python-aiml-developer/SKILL.md` | **Specialized AI/ML models & Python microservices** |
| Code Review | `.github/skills/expert-code-reviewer/SKILL.md` | Verification gate & quality enforcement |
| Codebase Scanner | `.github/skills/codebase-scanner/SKILL.md` | Codebase documentation & component mapping |

## Architecture & Project Commands

Use these commands for solution design and project scaffolding:

### Architecture Design
| Command | Description |
|---------|-------------|
| `/design <feature>` | Start architecture design workflow |
| `/research <topic>` | Research technologies and patterns |
| `/adr <title>` | Create Architecture Decision Record |

### Project Scaffolding
| Command | Description |
|---------|-------------|
| `/new-go-project <name>` | Generate new Go project skeleton with lib drivers |
| `/add-feature <name>` | Add feature module to existing project |
| `/validate-project` | Validate project structure |

### Execution
```bash
# Generate new Go project
python .github/skills/expert-solutions-architect/scripts/generate_project.py my_api

# Generate feature module
python .github/skills/expert-solutions-architect/scripts/generate_feature.py users

# Research technologies
python .github/skills/expert-solutions-architect/scripts/research_tech.py search "workflow engine" --lang go

# Generate architecture diagram
python .github/skills/expert-solutions-architect/scripts/generate_architecture.py --type clean --feature orders
```

### Project Management & Orchestration
| `/full-cycle <file>` | **Start Autonomous SDLC from a Req File** |
| `/analyze-req <msg>` | Start PRD & Project Initialization |
| `/link-arch` | Start Phase 2 (Call Solutions Architect) |
| `/plan-master` | Generate Master Implementation Plan |
| `/orchestrate-exec` | Begin SDLC loop (Design -> Dev -> Review) |
| `/change-request <msg>` | Handle New Change Requests |

```bash
# Initialize new project documentation
python .github/skills/expert-pm-ba-orchestrator/scripts/initialize_project.py "My System"

# Validate PRD logic
python .github/skills/expert-pm-ba-orchestrator/scripts/validate_prd.py PRD.md

# Generate atomic task specs
python .github/skills/expert-pm-ba-orchestrator/scripts/generate_task_spec.py TASK-001 "API Draft"

# Analyze impact of a Change Request
python .github/skills/expert-pm-ba-orchestrator/scripts/analyze_impact.py "Add priority field to workflows"
```


## Codebase Scanner Commands (v2.0)

Use these commands to scan and understand any codebase (including 10M+ LOC):

### Basic Scanning

| Command | Description |
|---------|-------------|
| `/scan-project` | Full scan with L0-L3 hierarchical docs + semantic analysis |
| `/scan-quick` | Quick scan - L0 + L1 only (faster) |
| `/scan-component <path>` | Deep dive into specific module |

### Incremental Scanning (Fast Updates)

| Command | Description |
|---------|-------------|
| `/scan-diff` | Only files changed since last scan |
| `/scan-git-diff [branch]` | Files changed vs branch (for PR reviews) |
| `/scan-since <date>` | Files changed since date |
| `/update-codebase` | **Automatic scan & index update** |

### Automation Command

When asked to update the codebase index, run:
```bash
python .github/skills/codebase-scanner/scripts/scan_codebase.py --incremental --output-dir .github/codebase-docs && python .github/skills/codebase-scanner/scripts/build_search_index.py --output .github/codebase-docs
```

### Semantic Analysis

| Command | Description |
|---------|-------------|
| `/scan-business-rules` | Extract business logic patterns |
| `/scan-security` | Security vulnerability analysis |
| `/scan-tech-debt` | Find TODOs, FIXMEs, long functions |
| `/scan-data-flow` | Trace data transformations |
| `/scan-complexity` | Code complexity metrics |

### Output Structure

```
.github/codebase-docs/
├── L0_EXECUTIVE_SUMMARY.md   # 1-page overview (~500 tokens)
├── L1_ARCHITECTURE/          # High-level architecture
├── L2_DOMAINS/               # Domain docs
├── L3_MODULES/               # Detailed module docs
├── SEMANTIC/                 # Semantic analysis
├── QUICK_REFERENCE.md        # Fast symbol lookup
├── SEARCH_INDEX.json         # Full index (grep, don't load!)
├── AI_NAVIGATION_GUIDE.md    # How to navigate large codebases
└── INDEX.md                  # Master navigation
```

### Execution

```bash
# Full scan
python .github/skills/codebase-scanner/scripts/scan_codebase.py --full

# Incremental
python .github/skills/codebase-scanner/scripts/scan_codebase.py --incremental

# Build search index
python .github/skills/codebase-scanner/scripts/build_search_index.py
```

### AI Navigation (Important!)

For large codebases, **always read `AI_NAVIGATION_GUIDE.md`** first to understand how to manage context windows.

## Agent Interactive Commands

Use these commands to instruct the UI Agent to load specific documentation layers and perform tasks:

### `/load-overview`
Instructs the agent to load the high-level context.
**Action**: Agent reads `L0_EXECUTIVE_SUMMARY.md` and `L1_ARCHITECTURE/OVERVIEW.md`.

### `/load-domain <name>`
Focuses the agent on a specific domain/feature.
**Action**: Agent reads `L2_DOMAINS/<name>/OVERVIEW.md` and `QUICK_REFERENCE.md`.

### `/load-module <domain>/<module>`
Deep dive into a specific implementation.
**Action**: Agent reads `L3_MODULES/<domain>/<module>/OVERVIEW.md`.

### `/load-semantic <type>`
Loads specific semantic analysis (security, rules, debt, flow).
**Action**: Agent reads `SEMANTIC/<TYPE>_ANALYSIS.md` (e.g., `SEMANTIC/SECURITY_ANALYSIS.md`).

### `/find-logic <query>`
Find specific logic or symbols across the codebase.
**Action**: Agent uses `grep_search` on `SEARCH_INDEX.json` and loads matching file headers.

### `/fix-bug <description>`
Streamlined workflow for debugging.
**Action**: Agent performs:
1. Greps `SEARCH_INDEX.json` to find relevant files.
2. Loads `L2_DOMAINS` overview for identified domains.
3. Checks `SEMANTIC/DATA_FLOW.md` and `TECH_DEBT.md`.
4. Proposes a diagnosis and plan.

### `/review <module>`
Triggers an automated code review for a specific module using the `expert-code-reviewer` skill.
**Action**: Agent uses `.github/skills/expert-code-reviewer/SKILL.md` to run validation scripts and generates a report in `report-review/<module>`.

### `/verify-arch <task>`
Verify if a task aligns with existing architecture.
**Action**: Agent loads L0, L1, and relevant L2 docs before proposing changes.

---

## Important Files
- `docs/FE_DESIGN_PATTERN.md` - Frontend architecture guide

