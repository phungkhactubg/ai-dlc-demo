# Examples Directory

This directory contains reference architecture examples demonstrating real-world system design patterns.

## Available Examples

| Example | Description | Patterns Used |
|---------|-------------|---------------|
| [workflow_engine_architecture.md](./workflow_engine_architecture.md) | Workflow/process automation engine | Clean Architecture, Event-Driven, CQRS |
| [multi_tenant_saas.md](./multi_tenant_saas.md) | Multi-tenant SaaS platform | Clean Architecture, Multi-tenancy |
| [event_sourcing.md](./event_sourcing.md) | Event sourcing with CQRS | Event Sourcing, CQRS |

## How to Use

1. **As Reference**: Use these examples as templates when designing similar systems
2. **As Learning**: Study the patterns and decisions made
3. **As Starting Point**: Copy and adapt for your specific needs

## Example Structure

Each example follows this structure:

```markdown
# [System Name] - Architecture

## Overview
- Purpose and key features

## High-Level Architecture
- System context diagram
- Component diagram

## Domain Model
- Entity relationships
- Go struct definitions

## Component Design
- Per-component breakdown
- API endpoints
- Internal structure

## Data Flow
- Sequence diagrams
- Event flows

## Security & Scalability
- Security considerations
- Scaling strategies

## Implementation Phases
- Phased rollout plan
```
