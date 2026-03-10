# Expert Project Manager & Business Analyst (Main Orchestrator)

This skill provides a professional framework for Product Management, Business Analysis, and Multi-Agent Orchestration. It is designed to manage complex software projects from the first requirement to the final production-ready code.

## 🌟 CORE PHILOSOPHY
- **Overview Layer**: `OVERVIEW.md` for project monitoring.
- **Execution Layer**: `tasks/*.md` for detailed instructions.
- **Orchestration**: A strict "Direct -> Verify" loop across all roles: **Researcher**, Architect, Backend, Frontend, and **AI/ML**.

---

## 🚀 USAGE GUIDE

### 1. Starting a New Project/Feature
Initialize the workspace and call the **Expert Researcher** if the domain is complex:
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/initialize_project.py "My Project Name"
```
*Note: Phase 0 (Research) is recommended before freezing the PRD.*
This creates:
- `OVERVIEW.md`: Your management dashboard.
- `PRD.md`: Your detailed requirements blueprint.
- `tasks/`: Directory for atomic task specifications.

### 2. Deep Requirement Analysis
Fill in the `PRD.md` template. Focus on the **Logic Validation Checklist** and **Edge Case Matrix**. Once done, validate it:
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/validate_prd.py PRD.md
```

### 3. Setting the Roadmap
Generate a Master Plan after the Solutions Architect has finished the `ARCHITECTURE_SPEC.md`:
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/generate_master_plan.py "My Project Name"
```

### 4. Directing Development
Generate atomic tasks for specific agents (Go, React, or **Python AI/ML**):
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/generate_task_spec.py "AI-001" "Train Sentiment Model"
```
Assign tasks and monitor the execution loop.

### 5. Tracking Progress
Update the project status in real-time as tasks are verified:
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/update_progress.py MASTER_PLAN.md "Login Form" --status x
```
*Note: This script will also sync the progress percentage to `OVERVIEW.md`.*

### 6. Managing Change Requests (CR)
If the user changes their mind or adds a new requirement:
```bash
python .github/skills/expert-pm-ba-orchestrator/scripts/analyze_impact.py "Add OAuth2 support"
```
Follow the "Document Cascade" rule: Update PRD -> Update Architecture -> Update Master Plan -> Create/Update Tasks.

---

## 🛠️ SCRIPTS REFERENCE
| Script | Description |
|--------|-------------|
| `initialize_project.py` | Sets up the Two-Layer documentation structure. |
| `validate_prd.py` | Rigorous check for PRD logic and completeness. |
| `generate_master_plan.py` | Creates a synchronized roadmap for multi-agent execution. |
| `generate_task_spec.py` | Creates atomic, unambiguous tasks for Developer Agents. |
| `update_progress.py` | Updates progress across both Overview and Master Plan. |
| `analyze_impact.py` | Identifies affected files/docs during a Change Request. |

## 🕹️ SLASH COMMANDS
- `/analyze-req <msg>`: Kickstart the SDLC (Phase 1).
- `/link-arch`: Initiate Technical Design (Phase 2).
- `/plan-master`: Build the Roadmap (Phase 3).
- `/orchestrate-exec`: Run the implementation loop (Phase 4).
- `/change-request <msg>`: Handle requirement shifts (Phase 5).

---
*Created with ❤️ for professional Multi-Agent Orchestration.*
