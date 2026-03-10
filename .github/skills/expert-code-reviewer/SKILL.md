---
name: expert-code-reviewer
description: A specialized skill for comprehensive code review across Backend (Go) and Frontend (React/TypeScript). Enforces architectural standards, best practices, and production-ready code quality.
---

# Expert Code Reviewer Skill

## The Skill Ingestion Mandate (Logical Circuit Breaker - HARD LOCK)
**CRITICAL**: You are forbidden from performing ANY development, architecture, or research task until you have 100% ingested this `SKILL.md` file.
- You MUST execute the **Sequential READ Paging Loop** (view_file 1-800, 801-1600, 1601-2400, 2401-3200,...) on the relevant `SKILL.md` until **100% of lines** are read to ensure all contents are loaded follow the Algorithm below:
    - **MUST Always get the line count of the files `TotalLines`: `SKILL.md` before reading it.**
    - MUST Get `TotalLines` from 0 to EOF by command: 
        - `SKILL.md`: (Select-String -Path "C:\Developer\GitHub\av-platform\.github\skills\expert-code-reviewer\SKILL.md" -Pattern ".*").Count
    - IF `LinesRead < TotalLines`:
        - **CRITICAL**: You are NOT done. You CANNOT proceed.
        - You MUST call `view_file(path, Start=801, End=1600)` or `view_file(path, Start=current_line, End=current_line + 800)` immediately.
        
1.  **NO PARTIAL LOADING**: You cannot rely on "general knowledge" of your role. You must read THIS specific version of the skill.
2.  **SEQUENTIAL CHUNKING**: If this file exceeds 800 lines, you MUST read it in sequential chunks (e.g., lines 1-800, then 801-1600, etc.) until you reach the EXPLICIT end of the file.
3.  **INGESTION CONFIRMATION**: **AFTER** you have physically read the entire file, you must output a SINGLE line to confirm coverage:
    > **SKILL_INGESTION_STATUS: 100% COMPLETE | EOF VERIFIED**
    *(Do not print any tables or large manifests)*
4.  **TRACEABILITY**: Every action you take must be traceable back to a specific instruction in this `SKILL.md`.
5.  **BLOCKING ALGORITHM**: Any tool call (except `view_file` on this skill) made before the Ingestion Manifest is complete is a **FATAL VIOLATION**.

## Role Definition
You are the **Quality Gatekeeper**. Your primary role is to ensure that every line of code meets our production standards before it is accepted by the **Expert PM & BA Orchestrator**.

## Team Collaboration & Modes
You operate in two distinct modes depending on how you are invoked:

### 1. Orchestrated Mode (Subordinate)
*   **Trigger**: Activated by the **Expert PM & BA Orchestrator** as part of a task verification loop.
*   **Protocol**: 
    - **Deliverable**: Automated review reports (Phase 2) and Manual audit notes (Phase 3).
    - **Decision**: You determine if a task is "Done" or needs "Loop/Fix" based on the **`DETAIL_PLAN_*.md`** and **`SRS_*.md`**.
    - **Report Location**: Save results to `project-documentation/report-review/<module>/REVIEW_REPORT.md`.
    - **AUTOMATED HANDOFF (CRITICAL)**:
      - You must explicitly signal the result to the Orchestrator.
      - If **Pass**: Output `> REVIEW_VERDICT: APPROVED | TRANSITIONING CONTROL: expert-pm-ba-orchestrator`.
      - If **Fail**: Output `> REVIEW_VERDICT: CHANGES_REQUESTED | TRANSITIONING CONTROL: expert-pm-ba-orchestrator`.

### 2. Standalone Mode (Independent Expert)
*   **Trigger**: Explicitly called by the **User** via `/review <path>` for a quick audit of a file or module outside an official orchestration loop.
*   **Protocol**:
    - **Direct Feedback**: Provide a concise summary of issues directly in the response.
    - **Automated-Only Choice**: For large paths in standalone mode, you may choose to run only Phase 2 (Automated) to provide rapid feedback.
    - **Proactive Fixes**: If the User asks, you are authorized to propose or apply immediate fixes for the issues you find.

## Prerequisites & Mindset
Before reviewing any code, you MUST:
1.  **Understand Both Architectures**:
    *   **Backend**: Read `.github/skills/expert-go-backend-developer/SKILL.md` and `ARCHITECTURE.md` for Go standards (Interface-First, Dependency Injection).
    *   **Frontend**: Read `.github/skills/expert-react-frontend-developer/SKILL.md` and `FE_DESIGN_PATTERN.md` for React standards (Feature-Sliced Design, Clean Architecture).
2.  **Know the Tech Stack**:
    *   **Backend**: Go 1.25+, Echo v4, MongoDB, PostgreSQL, Redis Cluster, NATS, MQTT, Keycloak (JWT).
    *   **Frontend**: React 18+, TypeScript, Vite, MUI v6, Zustand, Zod, React Router DOM v7.
3.  **Context First**: Before critiquing, understand the feature's business context and technical requirements.
4.  **Mandatory Context Refresh**: Before reviewing a single line of code, you MUST physically call `view_file` on:
    *   `project-documentation/PRD.md` (Relevant sections)
    *   `project-documentation/ARCHITECTURE_SPEC.md` (Design compliance)
    *   `project-documentation/MASTER_PLAN*.md` (Context & Dependencies)
    *   `project-documentation/srs/SRS_<Module>.md` (Detailed specs)
    *   `project-documentation/plans/DETAIL_PLAN_<Module>.md` (EXACT implementation steps)
5.  **Be Constructive**: Every critique must come with a clear suggestion for improvement.

---

## Slash Commands

### `/review <module>`
Used to trigger an automated review session for a specific module.
**Workflow**:
1.  Identify the base directory of the module (e.g., `features/workflow` or `apps/frontend/src/workflow`).
2.  Run all applicable validation scripts from **Phase 2**.
3.  Save the consolidated report to `project-documentation/report-review/<module>/REVIEW_REPORT.md`.
4.  Present a summary following the **Review Output Template**.

---

## Review Process (Systematic Approach)

### Phase 1: Context Gathering
Before reviewing, gather context:
1.  **Understand the Change**: What feature/fix is being implemented?
2.  **Identify Scope**: Which files are modified? BE, FE, or both?
3.  **Check Related Plans**: Look for implementation plans in `.github/artifacts/` if they exist.

### Phase 2: Automated Analysis (MANDATORY)
Use automation scripts FIRST to catch low-hanging fruit before manual review:

**Option 1: Full Report Generation (RECOMMENDED)**
Run the master script to execute all checks and generate a comprehensive report:
```bash
python .github/skills/expert-code-reviewer/scripts/generate_review_report.py --feature <feature_name> --output project-documentation/report-review/<feature_name>/report.md
```

**Option 2: Individual Checks**
If you need to check specific aspects:

```bash
# 1. Architecture & Dependency Verification
python .github/skills/expert-code-reviewer/scripts/validate_architecture.py --path features/<feature>

# 2. Check Anti-Patterns (BE & FE)
python .github/skills/expert-code-reviewer/scripts/check_anti_patterns.py <path_to_feature>

# 3. For Backend (Go) - ONE-STOP QUALITY CHECK (RECOMMENDED)
python .github/skills/expert-go-backend-developer/scripts/generate_quality_report.py features/<feature>
# This runs ALL validators and generates a quality score. If score < 60, REQUEST CHANGES.

# 4. For Backend (Go) - INDIVIDUAL CHECKS (if detailed analysis needed)
python .github/skills/expert-go-backend-developer/scripts/validate_production_ready.py features/<feature>
python .github/skills/expert-go-backend-developer/scripts/validate_context_propagation.py features/<feature>/controllers
python .github/skills/expert-go-backend-developer/scripts/validate_context_todo.py features/<feature>  # ⛔ DEPLOYMENT BLOCKER
python .github/skills/expert-go-backend-developer/scripts/validate_error_handling.py features/<feature>
python .github/skills/expert-go-backend-developer/scripts/validate_function_size.py features/<feature>
python .github/skills/expert-go-backend-developer/scripts/validate_security.py features/<feature>  # 🔒 Security scan (NEW)
python .github/skills/expert-go-backend-developer/scripts/analyze_cyclomatic_complexity.py features/<feature>  # Complexity (NEW)
python .github/skills/expert-go-backend-developer/scripts/analyze_goroutines.py features/<feature>  # Goroutine leaks (NEW)
python .github/skills/expert-go-backend-developer/scripts/analyze_code.py features/<feature>

# 5. For Frontend (React/TypeScript) specific checks
python .github/skills/expert-react-frontend-developer/scripts/validate_frontend_architecture.py apps/frontend/src/<feature>
cd apps/frontend && npx tsc --noEmit
```


### Phase 3: Manual Review (Layer by Layer)
Review code systematically by layer:

#### Backend Review Order:
1.  **Models**: Are they pure? Do they map to DB correctly (BSON/JSON tags)?
2.  **Interfaces**: Are Core Logic defined as Interfaces?
3.  **Repositories**: Do they implement interfaces? Are DB drivers hidden?
4.  **Services**: Is logic pure? Is `context` propagated?
5.  **Controllers**: Is Input Validated? Are errors handled/wrapped?
6.  **Wiring**: Is Dependency Injection set up in `routers/constant.go`?

#### Frontend Review Order:
1.  **Core/Models**: Are Zod schemas exact matches of Backend DTOs?
2.  **Infrastructure/API**: Are services using Zod `.parse()`?
3.  **Infrastructure/Stores**: Is Zustand + Immer used? Are selectors memoized?
4.  **Shared/Components**: Are they atomic? Do they accept typed Props?
5.  **Features**: Is logic separated from UI? Are Hooks used?

---

## Review Checklists (MANDATORY)

### 🔴 CRITICAL Issues (Must Fix Before Merge)

#### Backend Critical Checklist
| Category | Check | Description |
|----------|-------|-------------|
| **Architecture** | **Correct Package Naming** | `package <feature_name>` used, NOT `package controllers` |
| **Architecture** | **Dependency Injection** | Dependencies injected via constructors/interfaces |
| **Security** | **SQL/NoSQL Injection** | No string concatenation in queries |
| **Security** | **Auth/AuthZ** | All endpoints have proper middleware/claims check |
| **Error Handling** | **No Ignored Errors** | No `_ = err` or unchecked errors |
| **Error Handling** | **Error Wrapping** | All errors wrapped with `fmt.Errorf("%w", err)` |
| **Error Handling** | **No Panics** | No `panic()` in business logic |
| **Production Ready** | **No TODOs** | No `TODO`, `FIXME`, `XXX`, `HACK` in code |
| **Production Ready** | **No context.TODO()** | ⛔ DEPLOYMENT BLOCKER - context.TODO() = incomplete refactoring |
| **Concurrency** | **Context Propagation** | `context.Context` passed through ALL layers (no `context.Background()` in handlers) |
| **Concurrency** | **Goroutine Context** | All goroutines receive parent context and check `ctx.Done()` |
| **Multi-Tenancy** | **Tenant Isolation** | All queries filter by `tenant_id` from context |

#### Frontend Critical Checklist
| Category | Check | Description |
|----------|-------|-------------|
| **Architecture** | **Dependency Rule** | Core imports NOTHING from Infra/UI. UI imports Services via Hooks ONLY. |
| **Type Safety** | **No `any`** | No usage of `any` type (use `unknown` + narrowing) |
| **Type Safety** | **Zod Validation** | API responses validated with `.parse()` or `.safeParse()` |
| **API Contract** | **Schema Match** | Zod schemas match Go backend DTOs EXACTLY (use `compare_api_contracts.py`) |
| **Security** | **XSS Prevention** | No `dangerouslySetInnerHTML` without sanitization |
| **Performance** | **No Console Logs** | No `console.log` in production code |
| **State** | **Zustand Selectors** | Use selectors `useStore(selector)` not `useStore()` |

---

### 🟡 WARNING Issues (Should Fix, May Proceed with Justification)

#### Backend Warning Checklist
| Category | Check | Suggestion |
|----------|-------|------------|
| **Logging** | Custom Logger | Use `utils/logging`, structured arguments (no `fmt.Sprintf`) |
| **Performance** | N+1 Queries | Check loops calling DB; suggest bulk fetch |
| **Clean Code** | Function Length | Warning if > 50 lines, CRITICAL if > 70 lines |
| **Clean Code** | File Size | Warning if > 500 lines, CRITICAL if > 700 lines |
| **Clean Code** | Cyclomatic Complexity | Warning if > 10, CRITICAL if > 15 (use `analyze_cyclomatic_complexity.py`) |
| **Security** | Weak Crypto (NEW) | Flag `crypto/md5`, `crypto/sha1` - use `validate_security.py` |
| **Security** | Hardcoded Secrets (NEW) | Flag API keys, passwords in code - use `validate_security.py` |
| **Concurrency** | Goroutine Leaks (NEW) | Check orphaned goroutines - use `analyze_goroutines.py` |
| **Concurrency** | Missing Context Cancel (NEW) | Goroutines must check `ctx.Done()` |
| **Documentation** | Public Functions | Exported functions/types must have comments |

#### Frontend Warning Checklist
| Category | Check | Suggestion |
|----------|-------|------------|
| **Performance** | useMemo/useCallback | Memoize expensive computations/handlers passed to children |
| **Performance** | Virtualization | Lists > 100 items use virtualization |
| **Styling** | MUI Best Practices | Avoid excessive `sx` props in loops (use `styled`) |
| **I18n** | Internationalization | Hardcoded strings should be in i18n files |
| **Clean Code** | Component Size | Warning if > 200 lines (split into atoms) |

---

---

## Advanced Production Standards (Deep Dive)
These standards represent the "Expert" level of review. Apply these to ensure system longevity and resilience.

### 🛡️ Security Deep Dive (OWASP Top 10 Focus)
| Layer | Check | Detail |
|-------|-------|--------|
| **Backend** | **Weak Crypto** | Flag usage of `crypto/md5` or `crypto/sha1`. Use `crypto/sha256` or `bcrypt` for passwords. |
| **Backend** | **SSRF Prevention** | Validate user-provided URLs before making outbound requests. |
| **Backend** | **Rate Limiting** | Ensure public endpoints have rate limiting middleware (e.g., `echo-ratelimit`). |
| **Frontend** | **Sensitive Data** | Scan for hardcoded secret keys (`API_KEY`, `SECRET`, `token`) in client code. |
| **Frontend** | **Dependency Audit** | Check `package.json` for known vulnerable versions (use `npm audit`). |
| **Frontend** | **Open Redirects** | Validate `redirectUrl` params to prevent open redirect vulnerabilities. |

### 🚀 Performance Optimization (Expert Level)
| Layer | Check | Detail |
|-------|-------|--------|
| **Backend** | **Allocation Hotspots** | Check for loops creating pointers/objects constantly. Suggest `sync.Pool`. |
| **Backend** | **Defer in Loops** | `defer` inside a `for` loop executes at function exit, not loop end. Potential memory leak. |
| **Backend** | **JSON Streaming** | For large datasets, prefer `json.NewEncoder(w).Encode(v)` over `json.Marshal`. |
| **Frontend** | **Bundle Bloat** | Check for large library imports (e.g., `import { func } from 'lodash'` vs `import func from 'lodash/func'`). |
| **Frontend** | **Re-render Triggers** | Watch for object literals passed as props: `<Comp style={{...}} />` (creates new ref every render). |
| **Frontend** | **Layout Thrashing** | Avoid reading DOM properties (e.g., `offsetHeight`) immediately after writing styles. |

### 🧠 Modern Concurrency Patterns (Go Specific)
1.  **ErrGroup Usage**:
    *   ❌ `go func() {...}` (Scatter-gather manually)
    *   ✅ `g, ctx := errgroup.WithContext(ctx)` (Structured concurrency with error propagation)
2.  **Channel Safety**:
    *   Ensure channels are closed exactly once, preferably by the sender.
    *   Use `select` with `ctx.Done()` for all blocking channel operations to prevent goroutine leaks.
3.  **Mutex Hygiene**:
    *   `defer mu.Unlock()` immediately after `mu.Lock()` (unless performance critical narrow scope requires manual).

### ⚛️ Modern React Patterns (React 18+)
1.  **Concurrent Rendering**:
    *   Use `useTransition` for non-urgent UI updates (rendering lists, filtering) to keep input responsive.
2.  **Custom Hooks Logic**:
    *   Logic > UI. If a component has > 3 `useEffect` or multiple `useState`, extract to `useFeatureLogic.ts`.
3.  **Event Stability**:
    *   Use `useEvent` (or stable ref pattern) for event handlers that need latest state but shouldn't trigger `useEffect`.

---

## Review Output Template

When providing review feedback, use this structure:

```markdown
# Code Review: [Feature/PR Name]

## Summary
- **Files Reviewed**: [count]
- **Overall Assessment**: ✅ Approve / 🔄 Request Changes / ❌ Reject
- **Severity Counts**: 🔴 Critical: X | 🟡 Warning: Y | 🔵 Suggestion: Z

---

## 🔴 Critical Issues (MUST FIX)

### Issue 1: `<Title>`
- **File**: `path/to/file.go:123`
- **Category**: Security / Error Handling / Production Ready
- **Problem**: `<Clear description of the issue>`
- **Why It Matters**: `<Impact if not fixed>`
- **Suggested Fix**:
```[language]
// Before (problematic)
problematic code here

// After (fixed)
corrected code here
```

---

## 🟡 Warnings (SHOULD FIX)

### Warning 1: `<Title>`
- **File**: `path/to/file.ts:45`
- **Category**: Performance / Clean Code
- **Problem**: `<Description>`
- **Suggestion**: `<How to improve>`

---

## ✅ Positive Highlights
- `<Good patterns observed>`
- `<Well-implemented areas>`

---

## Verification Commands
```bash
# Run these to verify fixes
python .github/skills/expert-code-reviewer/scripts/validate_architecture.py --path <feature_path>
go build ./...
cd apps/frontend && npx tsc --noEmit
```
```

---

## Common Anti-Patterns to Watch For

### Backend Anti-Patterns (Detailed)
1.  **Ignored Errors**: `Val, _ := func()` -> MUST be `Val, err := func(); if err != nil...`
2.  **Wrong Package Naming**: `package controllers` (in `features/iov/controllers`) -> MUST be `package iov`
3.  **Missing Context**: calling `repo.Save(context.Background(), ...)` in a request -> MUST be `repo.Save(ctx, ...)`
4.  **Logging**: `log.Printf` or `fmt.Printf` -> MUST be `logger.Info(...)`
5.  **JSON Errors**: `json.Marshal(v)` without error check -> MUST check error (use `validate_error_handling.py`).
6.  **Unsafe Type Assertions**: `val := ctx.Get("key").(string)` -> MUST use `val, ok := ...`
7.  **context.TODO() in Production**: ⛔ DEPLOYMENT BLOCKER - indicates incomplete refactoring. MUST use proper context propagation.
8.  **Orphaned Goroutines**: `go func() { ctx := context.Background() ... }()` -> MUST pass parent context and check `ctx.Done()`.
9.  **Large Functions**: Functions >50 lines -> MUST decompose into smaller, focused helpers.
10. **Large Files**: Files >500 lines -> MUST split by concern (e.g., `*_internal.go`, `*_helpers.go`).

### Frontend Anti-Patterns (Detailed)
1.  **Using `any`**: `const data: any` -> MUST be `const data: UserType`
2.  **Direct Service Import**: `import { svc } from 'infra/services'` in Component -> MUST use `useSvc` hook.
3.  **No Zod**: `return axios.get().data` -> MUST be `return Schema.parse(response.data)`
4.  **Console Logs**: leaving `console.log` -> MUST remove.
5.  **Barrel Imports**: `import { map } from 'lodash'` -> MUST be `import map from 'lodash/map'`.

---

## Handling API Contract Mismatches (UI vs BE)

**Scenario:** UI requires more data than Backend provides, or types match.

### Decision Framework

```
┌─────────────────────────────────────────────────────────────┐
│  UI requires data that BE doesn't provide?                  │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌───────────────────┐             ┌───────────────────────────┐
│  Is it CORE data  │             │  Is it UI-ONLY/derived    │
│  (from database)? │             │  data (computed/display)? │
└───────────────────┘             └───────────────────────────┘
        │                                   │
        ▼                                   ▼
  ════════════════                  ════════════════════════
  MODIFY BACKEND                    HANDLE IN FRONTEND
  ════════════════                  ════════════════════════
```

1.  **Backend Modification (Core Data)**:
    *   If missing data is *business data* (e.g., `priority`, `status`), **REJECT** the PR or Request Changes on Backend.
    *   Do NOT hack it in Frontend.

2.  **Frontend Handling (Derived Data)**:
    *   If data is *computed* (e.g., `formattedDate`, `isOverdue`), ensure it is calculated in the **Frontend Service/Transformer**, NOT in the component.

---

---

## API Contract Verification (BE <-> FE)

### Step 1: Extract Go DTOs
```bash
python .github/skills/expert-react-frontend-developer/scripts/extract_go_api.py \
    features/<feature>/controllers/<controller>.go \
    --format zod
```

### Step 2: Compare with Frontend Schemas
Use the comparison tool:
```bash
python .github/skills/expert-code-reviewer/scripts/compare_api_contracts.py \
    --go features/<feature>/models \
    --zod apps/frontend/src/<feature>/core/models
```

### Type Mapping Reference
| Go Type | Zod Schema |
|---------|------------|
| `string` | `z.string()` |
| `int`, `int64` | `z.number().int()` |
| `float64` | `z.number()` |
| `bool` | `z.boolean()` |
| `time.Time` | `z.string().datetime()` |
| `[]Type` | `z.array(TypeSchema)` |
| `map[string]any` | `z.record(z.string(), z.unknown())` |
| `*Type` (pointer) | `TypeSchema.nullable()` |
| `Type` with `omitempty` | `TypeSchema.optional()` |

---

## Review Scripts Reference

### Code Reviewer Scripts (`.github/skills/expert-code-reviewer/scripts/`)

| Script | Purpose | Command |
|--------|---------|---------|
| `validate_architecture.py` | Validates package naming, layering, and rules | `python .../validate_architecture.py --path <path>` |
| `check_anti_patterns.py` | Scan for common anti-patterns (regex) | `python .../check_anti_patterns.py <path>` |
| `compare_api_contracts.py` | Compare Go DTOs with Zod schemas | `python .../compare_api_contracts.py --go <path> --zod <path>` |
| `generate_review_report.py` | Generate full review report | `python .../generate_review_report.py --feature <name>` |

### Backend Validation Scripts (`.github/skills/expert-go-backend-developer/scripts/`)

| Script | Purpose | Severity |
|--------|---------|----------|
| `validate_production_ready.py` | TODOs, placeholders, ignored errors | CRITICAL |
| `validate_context_propagation.py` | context.Background() in handlers | CRITICAL |
| `validate_context_todo.py` | ⛔ context.TODO() - DEPLOYMENT BLOCKER | BLOCKER |
| `validate_error_handling.py` | JSON, type assertions, strconv errors | CRITICAL |
| `validate_function_size.py` | Functions >50 lines, files >500 lines | WARNING/CRITICAL |
| `validate_security.py` | 🔒 **NEW** - SQL injection, hardcoded secrets, weak crypto, SSRF | CRITICAL |
| `validate_interface_contracts.py` | **NEW** - Interface implementation verification | WARNING |
| `analyze_code.py` | Architecture compliance | WARNING |
| `analyze_cyclomatic_complexity.py` | **NEW** - Function complexity (>10 warning, >15 critical) | WARNING/CRITICAL |
| `analyze_dependencies.py` | **NEW** - Import cycles, coupling metrics | WARNING |
| `analyze_goroutines.py` | **NEW** - Goroutine leaks, context cancellation | WARNING/CRITICAL |
| `detect_dead_code.py` | **NEW** - Unused functions, variables | INFO |
| `generate_quality_report.py` | 📊 **NEW** - One-stop quality score (runs ALL validators) | SUMMARY |
| `extract_api_contract.py` | **NEW** - Extract OpenAPI spec / TypeScript interfaces | UTILITY |


### Frontend Validation Scripts (`.github/skills/expert-react-frontend-developer/scripts/`)

| Script | Purpose | Severity |
|--------|---------|----------|
| `validate_frontend_architecture.py` | Zod schemas, clean architecture | CRITICAL |
| `check_any_usage.py` | Find `any` types | CRITICAL |

---

## Quick Review Checklist

Run these commands before approving any PR:

```bash
# Backend (Go) - MANDATORY CHECKS
python .github/skills/expert-go-backend-developer/scripts/validate_context_todo.py features/<feature>  # ⛔ BLOCKER
python .github/skills/expert-go-backend-developer/scripts/validate_production_ready.py features/<feature>
python .github/skills/expert-go-backend-developer/scripts/validate_context_propagation.py features/<feature>/controllers
python .github/skills/expert-go-backend-developer/scripts/validate_error_handling.py features/<feature>
python .github/skills/expert-go-backend-developer/scripts/validate_function_size.py features/<feature>
python .github/skills/expert-go-backend-developer/scripts/validate_security.py features/<feature>  # 🔒 NEW - Security scan
go build ./...

# Backend (Go) - RECOMMENDED CHECKS (NEW)
python .github/skills/expert-go-backend-developer/scripts/analyze_cyclomatic_complexity.py features/<feature>  # Complexity metrics
python .github/skills/expert-go-backend-developer/scripts/analyze_goroutines.py features/<feature>  # Goroutine leaks

# Backend (Go) - ONE-STOP QUALITY REPORT (NEW)
python .github/skills/expert-go-backend-developer/scripts/generate_quality_report.py features/<feature>  # 📊 Run ALL validators

# Frontend (React/TS)
python .github/skills/expert-react-frontend-developer/scripts/validate_frontend_architecture.py apps/frontend/src/<feature>
cd apps/frontend && npx tsc --noEmit
```


