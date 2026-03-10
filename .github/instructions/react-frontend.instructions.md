---
applyTo: "apps/frontend/**/*.{ts,tsx}"
---

# React Frontend Development Rules

## Architecture
- Follow Feature-Sliced Design: `src/<feature>/{core,infrastructure,shared,features}/`
- Use Zustand for state management
- Validate ALL API responses with Zod

## Type Safety
- NEVER use `any` type
- Use `unknown` + type guards instead
- All component props must be typed

## Patterns
- Use functional components with hooks
- Prefer composition over inheritance
- Use MUI v6 components

## API Integration
- Frontend Zod schemas MUST match backend Go structs exactly
- Use `schema.parse(response.data)` for validation

## Reference
See `.github/skills/expert-react-frontend-developer/SKILL.md` for full guidelines.
