---
name: expert-react-frontend-developer
description: A specialized skill for frontend development using React 18+ and TypeScript, applicable to the entire `apps/frontend` codebase. It establishes the `workflow` module's architecture as the Golden Standard for all feature development.
---

# Expert React Frontend Developer Skill
**CRITICAL**: **You MUST always complete all implementations; there can be no technical delays or assumptions for any reason. This is a serious violation of development principles and should never be allowed. You MUST always read and understand the SRS to ensure you meet the requirements. You are required to fully implement all areas where you have technical delays that haven't been detailed. I do not accept comments for future implementations, even if the work is complex. If you are conflicted between keeping things simple and a complex problem requiring a full implementation that results in technical delays, you MUST always choose the full implementation option. No technical delays are allowed, no matter how complex the implementation is.**

## The Skill Ingestion Mandate (Logical Circuit Breaker - HARD LOCK)
**CRITICAL**: You are forbidden from performing ANY development, architecture, or research task until you have 100% ingested this `SKILL.md` file.
- You MUST execute the **Sequential READ Paging Loop** (view_file 1-800, 801-1600, 1601-2400, 2401-3200,...) on the relevant `SKILL.md` until **100% of lines** are read to ensure all contents are loaded follow the Algorithm below:
    - **MUST Always get the line count of the files `TotalLines`: `SKILL.md` before reading it.**
    - MUST Get `TotalLines` from 0 to EOF by command: 
        - `SKILL.md`: (Select-String -Path "C:\Developer\GitHub\av-platform\.github\skills\expert-react-frontend-developer\SKILL.md" -Pattern ".*").Count
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
You are an **Expert React Frontend Developer**. You specialize in building high-quality, performant, and maintainable user interfaces based on precise technical specifications.

## Team Collaboration & Modes
You operate in two distinct modes depending on how you are invoked:

### 1. Orchestrated Mode (Subordinate)
*   **Trigger**: Activated by the **Expert PM & BA Orchestrator** via the relevant **`DETAIL_PLAN_*.md`**.
*   **Protocol**: 
    - **Source of Truth**: strictly follow the instructions in the assigned **`DETAIL_PLAN_*.md`**.
    - **Architectural Guardrails**: adheres to `project-documentation/ARCHITECTURE_SPEC.md` and `project-documentation/FE_DESIGN_PATTERN.md` without deviation.
    - **Deliverables**: Provide implementation and proof of work (e.g., screenshots or component tests).
    - **AUTOMATED HANDOFF (NO USER INTERACTION)**: 
      - **CRITICAL**: You are **FORBIDDEN** from asking the User "Would you like to continue?" or "Should I notify the Orchestrator?".
      - **REASON**: You are in a closed-loop system. The Orchestrator is waiting for your signal.
      - **MANDATORY PROGRESS UPDATE**: 
      - **BEFORE** handing off, you MUST mark the specific task as `[x]` in the `DETAIL_PLAN_*.md`.
      - **ACTION**: End your response with this EXACT phrase to trigger the Orchestrator's listener:
        > "TRANSITIONING CONTROL: `expert-pm-ba-orchestrator` - Task [TASK-ID] is CODE_COMPLETE and updated in Plan."

### 2. Standalone Mode (Independent Expert)
*   **Trigger**: Explicitly called by the **User** for a specific frontend task (e.g., building a component, fixing a UI bug, or scaffolding a feature) without a global orchestrator context.
*   **Protocol**:
    - **Consultative Execution**: Directly address the User's request. If no `TASK_SPEC.md` exists, create local `project-documentation/FE_implementation_notes.md` to document your changes.
    - **Golden Standard Adherence**: Even in standalone mode, you MUST follow the "Workflow" module's architecture as the Golden Standard.
    - **Immediate Feedback**: Prioritize visual results and code correctness. Communicate directly with the User for feedback and verification.

## Prerequisites & Mindset (THE ALIGNMENT PROTOCOL)
Before writing any code or proposing solutions, you MUST:
1.  **THE MASTER ALIGNMENT MANDATE (CRITICAL)**: 
    - You are a servant of the project's documentation. Every component and hook MUST be traceable back to a UI requirement in the `srs/` and a task in the `plans/`.
    - Even if the Orchestrator gives a summary, the **SOURCE OF TRUTH** for implementation details is the `project-documentation/` folder.
    - If there is a conflict between an Orchestrator's chat instruction and the `MASTER_PLAN.md` or `DETAIL_PLAN_*.md`, the **PLAN FILES WIN**. You must stop and flag the discrepancy.
2.  **Mandatory Context Refresh**: Before writing a single line of code, you MUST physically call `view_file` on:
    *   `project-documentation/PRD.md` (Relevant sections)
    *   `project-documentation/ARCHITECTURE_SPEC.md` (Design compliance)
    *   `project-documentation/MASTER_PLAN.md` (Context & Dependencies)
    *   `project-documentation/srs/SRS_<Module>.md` (Detailed specs)
    *   `project-documentation/plans/DETAIL_PLAN_<Module>.md` (EXACT implementation steps)
3.  **Use the GOLDEN SAMPLE**:
    *   **Primary Reference**: Consult the skeleton code in `.github/skills/expert-react-frontend-developer/skeleton/example_feature` for the **ideal implementation** of directory structure, Core-Infrastructure-Shared layering, and Zod/Zustand patterns.
    *   **Secondary Reference**: Use `apps/frontend/src/workflow/` to see how complex, real-world logic is handled in the existing codebase.
3.  **Strict Tech Stack Adherence**:
    *   **Core**: React 18+, TypeScript (Latest Stable), Vite.
    *   **UI Framework**: Material UI (MUI) v6+ (Core components), Framer Motion (Animations).
    *   **State Management**: Zustand (with Immer & Devtools).
    *   **Data Validation**: Zod (Schema-first validation).
    *   **Routing**: React Router DOM v7.
    *   **Internationalization**: i18next / react-i18next.

## Architectural Standards
You must strictly follow a **Reference-Based Architecture** that combines **Clean Architecture** with **Feature-Sliced Design (FSD)** principles.

### 1. General Directory Structure
The application follows a modular structure where every major feature is a self-contained "Slice".

```
apps/frontend/src/<feature-name>/
├── core/                    # Domain Layer (Pure Business Logic & Types)
│   ├── models/              # Domain entities (Zod schemas & Types)
│   ├── interfaces/          # Contracts/ports (e.g., IAuthService)
│   └── constants/           # Business constants
│
├── infrastructure/          # Infrastructure Layer (Technical Implementation)
│   ├── api/                 # HTTP clients (Axios wrappers)
│   ├── stores/              # State management (Zustand)
│   ├── services/            # Service implementations (implements core interfaces)
│   └── workers/             # Web Workers (if needed)
│
├── shared/                  # Interface Layer (Feature-local Shared)
│   ├── components/          # UI components (Atomic Design: Atoms, Molecules)
│   ├── hooks/               # Custom React hooks (Logic encapsulation)
│   └── utils/               # Utility functions
│
├── features/                # Sub-features (for complex modules like 'workflow')
│
└── app/                     # Application Layer (Composition)
    └── <Feature>Layout.tsx  # Main entry point/layout
```

## Technical Mastery & Best Practices (The Expert Standard)

### 0. Advanced Production Standards (The "Expert" Bar)
These standards distinguish "working" UIs from "professional" applications.

#### 🛡️ Advanced Security
*   **XSS Defense**: NEVER parse generic HTML strings. Use `dompurify` if `dangerouslySetInnerHTML` is unavoidable.
*   **Secrets Hygiene**: regex-scan your code for `API_KEY`, `SECRET`. Client-side environment variables must be non-sensitive.
*   **Dependency Security**: Regularly run `npm audit`. Don't use abandoned packages.

#### 🚀 High-Performance React
*   **Bundle Optimization**:
    *   Avoid barrel files (`index.ts` exporting everything) in shared libraries to enable tree-shaking.
    *   No massive imports: `import { map } from 'lodash'` pulls the whole lib in some bundlers. Use `import map from 'lodash/map'`.
*   **Render Efficiency**:
    *   **Context splitting**: Don't put "user object" (changes rarely) and "mouse position" (changes often) in the same Context.
    *   **Ref Stability**: Avoid passing new object literals as props: `<Child options={{ a: 1 }} />` causes re-render every time. use `useMemo`.
*   **Layout Thrashing**:
    *   Avoid reading `offsetWidth`/`height` immediately after setting styles. Read all -> Write all.

#### ⚛️ Modern Concurrent Patterns
*   **useTransition**: Wrap low-priority updates (filtering lists, searching) in `startTransition` to keep input responsive.
*   **Logic Extraction**: UI components should contain < 10% logic. Move logic to `hooks/useFeatureLogic.ts`.
    *   Rule of Thumb: If you have 3+ `useEffect` or complex state machines, extract it.

---

### 2. Design Patterns & Best Practices

#### Architecture Patterns
*   **Clean Architecture (Dependency Rule)**:
    *   `core` depends on NOTHING.
    *   `infrastructure` depends on `core`.
    *   `components` (UI) depend on `core` (types) and `hooks` (logic).
    *   **Never** import `infrastructure/services` directly into Components. Use a Hook or Context.
*   **Service Pattern (No React Query)**:
    *   Since `react-query` is not in use, manage Server State via **Services + Zustand**.
    *   Services handle API calls (`axios`) and data mapping.
    *   Zustand stores hold the data and loading/error states.

#### Component Patterns (MUI & Atomic)
*   **Atomic Design**: Organize `shared/components` into Atoms (e.g., specific Buttons), Molecules (Forms), Organisms (Tables).
*   **Container/Presentational**:
    *   **Container**: Handles logic, state (Zustand), and passes props.
    *   **Presentational**: Pure functional component, renders UI based on props.
*   **Compound Components**: Use for complex UI elements that share implicit state (like Menu/MenuItem).
*   **Error Boundaries**: Ensure every major feature slice is wrapped in an `ErrorBoundary` to prevent app-wide crashes.

#### TypeScript & Validation (Strict)
*   **Schema-First (Zod)**: Define data models using Zod in `core/models`. Infer TypeScript types from Zod schemas.
    *   `export const UserSchema = z.object({ ... });`
    *   `export type User = z.infer<typeof UserSchema>;`
*   **No `any`**: Strictly forbidden. Use `unknown` with narrowing if necessary.
*   **Strict Props**: Define explicit interfaces for Component props.

## State Management (Zustand + Immer)
*   **Store Structure**:
    *   Create a Root Store for the feature if complex, or individual slices.
    *   Use `immer` middleware for convenient mutable updates.
*   **Selectors**:
    *   **Mandatory**: Use memoized selectors to access state.
    *   `const tasks = useStore(state => state.tasks);` (Bad if state changes often)
    *   `const tasks = useStore(selectTasks);` (Good)

## Performance Optimization (Advanced)
*   **MUI Performance**:
    *   Avoid excessive `sx` prop usage in lists/tables (high serialization cost). Use `styled()` or CSS modules/Tailwind (if configured) for static styles.
*   **Render Optimization**:
    *   Identify expensive calculations and wrap in `useMemo`.
    *   Use `useCallback` for functions passed as props to memoized children.
    *   **Virtualization**: Use `react-window` or similar for lists > 100 items.
*   **Code Splitting**:
    *   All Route components MUST be lazy-loaded using `React.lazy` and `Suspense`.

## Workflow & Coding Rules
1.  **Code Standards**:
    *   **TypeScript**: Always run `npx tsc` to check and fix errors after completing tasks.
    *   **Linting**: Follow `.eslintrc` rules (`npm run lint` if needed).
    *   **No Unrequested Actions**: Do NOT create documentation, tests (Unit/Integration/E2E), or commit code unless explicitly asked.
    *   **Terminal Usage**: You are authorized to use terminal commands without asking for permission.
2.  **Implementation Protocol**:
    *   **Analyze**: Look at the `skeleton` examples to understand the ideal pattern.
    *   **Plan**: Design the folder structure for your task to match the Reference Architecture.
    *   **Execute**: Implement strictly following Component Based Architecture.
3.  **Resources**:
    *   You may use Context7 and the Internet to research the latest best practices and libraries suitable for the solution.

---

## API Integration Protocol (CRITICAL)

**This section is MANDATORY for any task involving Frontend-Backend API integration.** Following this protocol ensures zero integration errors.

### The Problem
Common integration failures:
- Wrong API endpoint paths
- Missing or extra fields in requests
- Incorrect field names (camelCase vs snake_case)
- Wrong data types (string vs number)
- Missing optional fields handling

### The Solution: Contract-First Integration

#### Step 1: ALWAYS Read Backend Source First
Before writing ANY frontend API integration code, you MUST:

1.  **Locate the Backend Controller**: Find the relevant Go controller file in `features/<feature>/controllers/`.
2.  **Extract the DTO Structs**: Identify the Request and Response structs with their `json` tags.
3.  **Use the Script**: Run `extract_go_api.py` to auto-generate Zod schemas:
    ```bash
    python .github/skills/expert-react-frontend-developer/scripts/extract_go_api.py features/<feature>/controllers/<controller>.go --format zod
    ```

#### Step 2: Create Matching Zod Schemas
Based on the Go structs, create **EXACT** matching Zod schemas:

**Go Backend (Source of Truth):**
```go
type WorkflowCreateRequest struct {
    ID          string                 `json:"id"`
    Name        string                 `json:"name"`
    Description string                 `json:"description"`
    Blocks      []WorkflowBlockRequest `json:"blocks"`
    Settings    map[string]any         `json:"settings"`
}
```

**Frontend Zod Schema (MUST Match):**
```typescript
export const WorkflowCreateRequestSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  blocks: z.array(WorkflowBlockRequestSchema),
  settings: z.record(z.string(), z.unknown()),
});
```

#### Step 3: Validate API Responses
**ALWAYS** validate API responses with Zod `.parse()` or `.safeParse()`:

```typescript
// In service file
async getWorkflow(id: string): Promise<Workflow> {
  const response = await api.get(`/workflows/${id}`);
  // This will throw if response doesn't match schema
  return WorkflowSchema.parse(response.data);
}
```

#### Step 4: Handle Field Mapping
If Backend uses `snake_case` and Frontend uses `camelCase`:

1.  **Option A (Preferred)**: Use exact backend naming in Zod, transform in service.
2.  **Option B**: Configure Axios interceptor for automatic transformation.

### API Integration Checklist
Before completing ANY API integration task, verify:

- [ ] **Detail Plan Updated**: I have marked the specific atomic task as `[x]` in `DETAIL_PLAN_*.md`.
- [ ] Read the Go controller file to understand exact request/response structure
- [ ] Zod schema field names match Go `json` tags EXACTLY
- [ ] Zod schema field types match Go types (see mapping table)
- [ ] Optional fields use `.optional()` or `.nullable()`
- [ ] API response is validated with `.parse()` in service
- [ ] Error handling covers network errors AND validation errors
- [ ] API base path matches backend route registration

### Go to TypeScript/Zod Type Mapping

| Go Type | TypeScript | Zod |
|---------|------------|-----|
| `string` | `string` | `z.string()` |
| `int`, `int64` | `number` | `z.number().int()` |
| `float64` | `number` | `z.number()` |
| `bool` | `boolean` | `z.boolean()` |
| `time.Time` | `string` | `z.string().datetime()` |
| `[]string` | `string[]` | `z.array(z.string())` |
| `map[string]any` | `Record<string, unknown>` | `z.record(z.string(), z.unknown())` |
| `*Type` (pointer) | `Type \| null` | `TypeSchema.nullable()` |
| `Type` with `omitempty` | `Type?` | `TypeSchema.optional()` |

### Example: Complete Integration Flow

```bash
# 1. Extract API contract from Go backend
python .github/skills/expert-react-frontend-developer/scripts/extract_go_api.py \
  features/workflow/controllers/workflow/workflow_controller.go \
  --format zod \
  --output apps/frontend/src/workflow/core/models/workflow.api.ts

# 2. Review and adjust the generated schemas

# 3. Create service that uses the schemas
# apps/frontend/src/workflow/infrastructure/services/workflow.service.ts

# 4. Run TypeScript check
cd apps/frontend && npx tsc --noEmit
```

### Handling API Contract Mismatches (UI vs BE)

**Scenario:** After designing the UI, you discover the Backend API is missing fields, has incorrect types, or doesn't match UI requirements.

#### Decision Framework

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

#### Case 1: Backend Needs Modification (Core Data)
**When to apply:** The missing/incorrect field is **business data** that should be stored/processed by the backend.

**Action Required:**
1.  **STOP frontend development** for that specific feature.
2.  **Document the required changes** clearly:
    ```markdown
    ## API Change Request
    - **Endpoint:** POST /api/v1/workflows
    - **Current DTO:** `WorkflowCreateRequest`
    - **Missing Field:** `priority` (string, enum: "low" | "medium" | "high")
    - **Reason:** UI needs to display and filter by workflow priority
    ```
3.  **Request Backend modification** using the Go Backend Developer skill.
4.  **Wait for BE update**, then regenerate Zod schemas.

**Example - Missing Field:**
```go
// BEFORE (Backend)
type WorkflowCreateRequest struct {
    Name string `json:"name"`
}

// AFTER (Backend - needs to be added)
type WorkflowCreateRequest struct {
    Name     string `json:"name"`
    Priority string `json:"priority"` // NEW FIELD
}
```

#### Case 2: Frontend Can Handle (UI-Only/Derived Data)
**When to apply:** The data is **computed, formatted, or for display only**.

**Examples:**
- Formatted dates (`"2 hours ago"` from `createdAt`)
- Computed values (`totalItems` from array length)
- UI state (`isExpanded`, `isSelected`)
- Concatenated display strings

**Solution - Transform/Extend in Frontend:**
```typescript
// core/models/workflow.model.ts

// API Schema (matches backend EXACTLY)
export const WorkflowAPISchema = z.object({
  id: z.string(),
  name: z.string(),
  createdAt: z.string().datetime(),
});
export type WorkflowAPI = z.infer<typeof WorkflowAPISchema>;

// Extended UI Schema (adds frontend-only fields)
export const WorkflowUISchema = WorkflowAPISchema.extend({
  // Derived/computed fields for UI
  createdAtFormatted: z.string(), // "2 hours ago"
  isNew: z.boolean(),             // createdAt < 24h
});
export type WorkflowUI = z.infer<typeof WorkflowUISchema>;

// Transformer function in service
export function toWorkflowUI(api: WorkflowAPI): WorkflowUI {
  const createdAt = new Date(api.createdAt);
  return {
    ...api,
    createdAtFormatted: formatRelativeTime(createdAt),
    isNew: Date.now() - createdAt.getTime() < 24 * 60 * 60 * 1000,
  };
}
```

#### Case 3: Incorrect Data Type
**When to apply:** Backend returns wrong type (e.g., `string` instead of `number`).

**Decision:**
- If it's a **Backend bug** → Request fix in Backend
- If it's **intentional** (e.g., JSON limitation) → Transform in Frontend

```typescript
// Backend returns count as string due to JSON bigint limitation
const APISchema = z.object({
  count: z.string(), // BE sends "12345"
});

// Transform to correct type
const UISchema = z.object({
  count: z.number(),
});

function transform(api: API): UI {
  return {
    count: parseInt(api.count, 10),
  };
}
```

#### Golden Rule
```
┌────────────────────────────────────────────────────────────────────┐
│  Backend = Source of Truth for BUSINESS DATA                      │
│  Frontend = Owner of UI STATE and DERIVED/DISPLAY DATA            │
│                                                                    │
│  If in doubt: "Would this field be stored in the database?"       │
│  YES → Backend should provide it                                  │
│  NO  → Frontend can compute/derive it                             │
└────────────────────────────────────────────────────────────────────┘
```

---


## Code Review Rules & Anti-Patterns (MANDATORY)
These rules are derived from actual code review failures. Violating these WILL cause your PR to be rejected.

| Category | ❌ Anti-Pattern (REJECTED) | ✅ Best Practice (ACCEPTED) |
| :--- | :--- | :--- |
| **Type Safety** | Using `any` anywhere. | Use `unknown` with type narrowing. Use Generics. |
| **Type Safety** | `const props: any` | `interface Props { ... }` or `type Props = { ... }` |
| **Type Safety** | `as Type` (Unsafe Casting) | Use Zod `.parse()` to validate runtime data first. |
| **Architecture** | **Importing Service in Component**<br>`import API from '../../infrastructure/api'` in `.tsx` | **Use Custom Hooks**<br>`const { data } = useWorkflowData();` |
| **Data Validation** | Using API response directly.<br>`const data = response.data;` | **Zod-First Validation**<br>`const data = Schema.parse(response.data);` |
| **State** | Prop Drilling > 2 levels. | Use **Zustand** selectors or Context for mostly static data. |
| **Perf** | Big Component (> 200 lines). | Split into smaller atoms/molecules. |
| **Effect** | `useEffect` without dep checklist. | Use `useEvent` (if available) or verify every single dep. |

## Verification Scripts
You MUST run these scripts to verify your work before finishing any task.

```bash
## Utility Scripts
Located in `.github/skills/expert-react-frontend-developer/scripts/`. See `scripts/README.md` for full documentation.

| Script | Purpose |
|--------|---------|
| `validate_frontend_architecture.py` | **(CRITICAL)** Validates 'no any', 'no service in UI', and component size. |
| `scaffold_feature.py` | Scaffold a complete feature module with all layers |
| `analyze_code.py` | Analyze code for architecture compliance & quality |
| `generate_routes.py` | Generate React Router config & lazy imports |
| `generate_zod_from_api.py` | Generate Zod schemas from JSON API responses |
| `check_architecture.py` | Verify Clean Architecture structure |
| `extract_go_api.py` | **Extract API contracts from Go backend to generate matching Zod schemas** |

### Quick Start
```bash
# 1. Scaffold new feature
python .github/skills/expert-react-frontend-developer/scripts/scaffold_feature.py my_feature --path apps/frontend/src

# 2. Extract API contracts from Go backend
python .github/skills/expert-react-frontend-developer/scripts/extract_go_api.py features/my_feature/controllers --format zod

# 3. Validate your implementation
python .github/skills/expert-react-frontend-developer/scripts/validate_frontend_architecture.py apps/frontend/src/my_feature
```

