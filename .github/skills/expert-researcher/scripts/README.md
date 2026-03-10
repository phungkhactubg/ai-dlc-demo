# Expert Researcher Script Toolkit

This directory contains specialized Python scripts to support complex technical research, feasibility studies, and architectural planning.

## 🔄 Core Research Workflow

### 1. `research_iterative.py`
**The Primary Tracker.** Manages the state of a recursive research task. 
- **Usage**: `python scripts/research_iterative.py "Task Name" --query "initial search"`
- **Key Flags**:
  - `--query`: Log a search query.
  - `--finding`: Log a specific technical finding.
  - `--source`: source for the finding.
  - `--eval`: `Positive`, `Neutral`, or `Negative` (Mandatory for friction audit).
  - `--deduction`: **(NEW)** Log a strategic insight connecting multiple findings.
  - `--status`: Display the expert-grade sufficiency report.

### 2. `generate_reasoning.py`
**Thinking Log Generator.** Scaffolds the `RESEARCH_THINKING.md` file.
- **Usage**: `python scripts/research_reasoning.py "Finalizing Auth Strategy"`
- **Purpose**: Forces the researcher to document hypotheses, skepticism, and pivot logic.

### 3. `generate_dossier.py`
**Research Dossier Scaffolder.** Creates a multi-file directory structure for complex topics.
- **Usage**: `python scripts/generate_dossier.py "Baidu Apollo"`
- **Purpose**: Automates the creation of `INDEX.md`, `ARCHITECTURE.md`, `ECOSYSTEM.md`, etc., to ensure A-Z coverage.

---

## 🏗️ Architectural & Technical Analysis

### `analyze_impact.py`
Generates a structured Architectural Impact Analysis to evaluate how a new technology fits the current system.

### `compare_candidates.py`
Generates a 3-column Decision Matrix comparing multiple technical options.

### `verify_external_repo.py`
Performs a health check on external GitHub repositories (Bus factor, activity, issues).

### `research_github.py`
Directly search GitHub for libraries, models, or documentation.

---

## 📝 Planning & Validation

### `generate_plan.py`
Scaffolds a detailed Implementation Plan based on research findings.

### `validate_plan.py`
Checks an implementation plan for completeness, contract satisfaction, and atomic steps.

### `generate_api_contract.py`
Interactive tool to create OpenAPI/JSON contracts between Backend and Frontend.

### `generate_security_checklist.py`
Generates targeted security review checklists based on the feature type (API, UI, Data).
