# Detailed Task Specification: [Task ID - Name]

## 0. Prerequisites (MANDATORY)
Before starting this task, you MUST read/view the following documents to ensure alignment with the latest project state:
- [ ] `project-documentation/PRD.md` (Relevant sections)
- [ ] `project-documentation/ARCHITECTURE_SPEC.md`
- [ ] `project-documentation/MASTER_PLAN.md`
- [ ] `project-documentation/srs/SRS_<Module>.md` (Target Module)
- [ ] `project-documentation/plans/DETAIL_PLAN_<Module>.md` (Target Module)

## 1. Context & Objective
- **Traceability**: [SRS_REF] | [MASTER_PLAN_WP_ID]
- **Component**: [e.g., features/workflow/services]
- **Objective**: [Precise engineering goal for this specific task]

## 2. Technical Requirements (Deep Dive)
### 2.1 Interface & Data Contracts
```go
// Required Interface change or creation
type IMyTaskService interface {
    Execute(ctx context.Context, input Data) (Result, error)
}
```

### 2.2 Logic & Business Rules
- [Rule 1]: Detail descriptions of the algorithm or logic.
- [Rule 2]: Specific validation rules for this task.

### 2.3 Success Scenarios
1. [Scenario 1]: Input -> Expected Output
2. [Scenario 2]: Input -> Expected Error

## 3. Implementation Steps
1. [ ] Create file `...`
2. [ ] Implement method `...`
3. [ ] Write unit test for `...`

## 4. Verification Checkpoints
- [ ] `go test ./path/to/module`
- [ ] Check logic against [PRD Requirement]
- [ ] No regression in [Sensitive Area]

---
*Assigned by Expert PM & BA Orchestrator*
