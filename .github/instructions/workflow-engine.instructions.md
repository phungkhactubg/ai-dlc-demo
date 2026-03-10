---
applyTo: "features/workflow_engine/**/*.go"
---

# Workflow Engine Development Rules

## Context Management
- Workflow execution uses background goroutines
- Use `context.WithoutCancel()` for long-running workflows
- HTTP request cancellation should NOT cancel workflow execution

## Block Executors
- Implement `IBlockExecutor` interface
- Reference: `docs/EXECUTOR_PLUGIN_MIGRATION_TEMPLATE.md`

## Status Updates
- Workflow status must update from "queued" → "running" → "completed"
- Use proper MongoDB transactions for status updates

## Known Issues
- Issue #001: Workflows getting stuck in "queued" state
- Root cause: Context detachment / MongoDB transaction issues
