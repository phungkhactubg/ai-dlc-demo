---
applyTo: "**/*.go"
---

# Go Backend Development Rules

## Architecture
- Follow Clean Architecture in `features/<name>/{models,services,repositories,controllers,routers}/`
- All services and repositories MUST have interfaces
- Use dependency injection

## Error Handling
- ALWAYS wrap errors: `fmt.Errorf("service.Method: %w", err)`
- NEVER ignore errors - handle or return them
- Use custom domain errors where appropriate

## Context
- NEVER use `context.TODO()` in production code
- ALWAYS propagate context from HTTP handlers
- Use `context.WithTimeout()` for external calls

## Code Style
- Functions should not exceed 50 lines
- Document all public functions
- Use table-driven tests
- `ctx context.Context` as first parameter
- `error` as last return value

## Reference
See `.github/skills/expert-go-backend-developer/SKILL.md` for full guidelines.
