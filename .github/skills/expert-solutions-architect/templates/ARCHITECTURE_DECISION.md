# Architecture Decision Record Template

> Use this template to document significant architectural decisions.

# ADR-[NUMBER]: [Short Title]

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-X
**Date:** YYYY-MM-DD
**Deciders:** [Who made/approved this decision]
**Technical Story:** [Link to issue/ticket if applicable]

---

## Context

[Describe the situation that is forcing a decision. What is the problem we are trying to solve? What constraints do we have?]

### Motivation
- [Why is this decision needed now?]
- [What happens if we don't make this decision?]

### Constraints
- [Technical constraint]
- [Business constraint]
- [Time constraint]

---

## Decision

[State the decision clearly and concisely]

```
We will [ACTION] using [TECHNOLOGY/APPROACH] because [PRIMARY REASON].
```

### Technical Details
[Provide specific implementation details]

```go
// Example code showing the pattern
type Service struct {
    repo Repository // Depends on interface
}
```

---

## Alternatives Considered

### Alternative 1: [Name]
[Brief description]
- **Why rejected:** [Reason]

### Alternative 2: [Name]
[Brief description]
- **Why rejected:** [Reason]

---

## Consequences

### Positive
- ✅ [Benefit 1]
- ✅ [Benefit 2]
- ✅ [Benefit 3]

### Negative
- ⚠️ [Drawback 1]
- ⚠️ [Drawback 2]

### Neutral
- ℹ️ [Side effect or note]

---

## Implementation Notes

### Required Changes
1. [Change to component A]
2. [Change to component B]

### Migration Strategy
[How to transition from current state to new state]

### Rollback Plan
[How to undo this decision if needed]

---

## Validation Criteria

- [ ] [How do we know this decision is successful?]
- [ ] [Metric or test to validate]

---

## Related Decisions
- ADR-[X]: [Related decision]
- ADR-[Y]: [Related decision]

---

## References
- [Link to documentation]
- [Link to research]
