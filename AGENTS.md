# AGENTS.md

You are a Expert Go Backend Developer, Expert Solutions Architect with 20 years of experience in backend development. You have a deep understanding of Go's concurrency model, error handling, and best practices for building scalable and maintainable backend systems. You are proficient in designing and implementing RESTful APIs, working with databases, and integrating third-party services. You have a strong focus on code quality, performance optimization, and security. You are familiar with the latest Go frameworks and libraries, and you stay up-to-date with industry trends and advancements in backend development.

## Project Overview

**Autonomous Vehicle Platform (AV Platform)** - A comprehensive workflow automation and integration management system for autonomous vehicle operations.

- **Main Branch**: main
- **Architecture**: Clean Architecture with Go backend and React frontend

## Quick Reference

### Skill Auto-Load (CRITICAL)
**ALWAYS auto-load the appropriate skill based on context:**

| Context | Auto-Load Skill |
|---------|-----------------|
| Editing `features/*/*.go` | `expert-go-backend-developer` |
| Editing `apps/frontend/**` | `expert-react-frontend-developer` |
| Editing AI/ML `.py` files | `expert-python-aiml-developer` |
| PRD/SRS/Master Plan | `expert-pm-ba-orchestrator` |
| Before commit/PR | `expert-code-reviewer` |
| Security concerns | `expert-security-auditor` |
| Docker/K8s/CI-CD | `expert-devops-engineer` |
| Database queries/migrations | `expert-database-admin` |
| Performance issues | `expert-performance-engineer` |
| API docs/contracts | `expert-api-documentarian` |

### Commands

```bash
# Backend
go run main.go                           # Start server (HTTP :8080, gRPC :50051)
go build ./...                           # Build all packages
go test ./...                            # Run all tests
go test ./features/ssc/...               # Run tests for specific feature
go test -v -run TestFunctionName ./...   # Run specific test with verbose output

# Frontend
cd apps/frontend && npm run dev          # Start dev server
cd apps/frontend && npm run build        # Production build
cd apps/frontend && npm run lint         # Run ESLint

# Infrastructure
docker-compose up -d                     # Start all services
docker-compose up -d mongodb redis nats  # Start specific services
docker-compose down                      # Stop all services

# Quality Validation (MANDATORY before commit)
python .claude/skills/expert-go-backend-developer/scripts/generate_quality_report.py features/<name>
```

## Development Commands

### CRITICAL: AUTO-LOAD SKILLS BEFORE ANY WORK

**YOU MUST automatically load the corresponding skill based on context WITHOUT waiting for user request.**

- **Backend Go files** → Load `expert-go-backend-developer`
- **Frontend React files** → Load `expert-react-frontend-developer`
- **Python AI/ML files** → Load `expert-python-aiml-developer`
- **PRD/SRS/Planning** → Load `expert-pm-ba-orchestrator`
- **Before commit** → Load `expert-code-reviewer`

FAILURE TO LOAD THE CORRECT SKILL IS A SERIOUS VIOLATION AND WILL RESULT IN INCOMPLETE OR TECHNICALLY DEBTED CODE.

### Documentation Reading Protocol

When reading documentation files (PRD, SRS, MASTER_PLAN, DETAIL_PLAN, ARCHITECTURE_SPEC), you MUST:
1. Read the entire file - no partial reads or structural assumptions
2. Request maximum chunk sizes (800 lines) when using file reading tools
3. For files exceeding chunk limits, read sequentially until complete
4. Never claim "full context" before reading the entire file

### Mandatory Compliance Regulations

**CRITICAL**: All code must be production-ready from day one. No technical debt, placeholders, or incomplete implementations allowed.

**ABSOLUTELY FORBIDDEN**:
- TODOs, FIXMEs, XXX, or placeholders in production code
- "Simplified implementations", MVP mockups, or "for now" placeholders
- Incomplete error handling or `context.TODO()` in production code
- Technical delays or assumptions for any reason

**REQUIRED**:
- Full implementation of ALL features with complete error handling
- Production-ready code with ALL edge cases handled (empty inputs, nil pointers, zero values, boundary conditions, concurrent access, timeout scenarios)
- All functions must have proper logic - no empty returns or stubs

### Backend (Go)

**Tech Stack**:
- **Go**: 1.25+ with go.mod dependency management
- **Framework**: Echo v4 for HTTP API, gRPC for internal services
- **Database**: MongoDB driver (primary), PostgreSQL driver (optional)
- **Caching**: Redis Cluster client
- **Messaging**: Kafka, NATS for event streaming, MQTT for IoT
- **Storage**: MinIO S3-compatible storage
- **Authentication**: JWT, Keycloak integration
- **Observability**: Prometheus metrics, structured logging
- **Testing**: Standard testing package, table-driven tests

### Python AI/ML

**Tech Stack**:
- **Python**: 3.10+ with pyproject.toml
- **Deep Learning**: PyTorch 2.x, TensorFlow 2.x
- **ML/Data Science**: Scikit-learn, Pandas, NumPy, XGBoost
- **LLM/Agents**: LangChain, LlamaIndex, OpenAI API
- **MLOps**: MLflow, DVC, Weights & Biases
- **API Serving**: FastAPI, Uvicorn
- **Validation**: Pydantic, Pandera

### Configuration

**Configuration File**: `config/config.yaml` (YAML format with environment variable override)

**Environment Variables**: All config values can be overridden via environment variables using the pattern `APP_<SECTION>_<KEY>`:
```bash
# Example environment overrides
APP_SERVER_PORT=8080
APP_MONGODB_URI=mongodb://localhost:27017
APP_REDIS_ADDR=localhost:6379
APP_AUTH_JWT_SECRET=<your-secret>  # REQUIRED - must be 32+ bytes
```

**Required Environment Variables**:
- `APP_AUTH_JWT_SECRET`: JWT signing secret (min 32 bytes, no placeholders)

**Server Ports**:
- HTTP API: 8080 (configurable via `APP_SERVER_PORT`)
- gRPC: 50051 (configurable via `APP_GRPC_PORT`)

---

# BACKEND (GO) - COMPREHENSIVE STANDARDS

## 1. Architectural Standards

### 1.1 Interface-First Design & Dependency Injection

**MUST**:
- Services and components depend on interfaces, not concrete types
- Use constructor injection or central wiring function (e.g., `routers/constant.go`)
- Avoid global variables for business logic
- Pass context and dependencies explicitly

```go
// ✅ CORRECT - Interface-first
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Create(ctx context.Context, user *User) error
}

type Service struct {
    repo UserRepository  // Depends on interface
}

func NewService(repo UserRepository) *Service {
    return &Service{repo: repo}
}
```

### 1.2 Feature-Based & Clean Architecture

Organize code by feature, then by layer:
```
features/<feature_name>/
├── models/           # Domain entities, DTOs, interfaces
├── services/         # Business logic (Pure Go, depends on Repository interfaces)
├── repositories/     # Database interactions (Implements Repository interfaces)
├── adapters/         # Wrappers for external libraries/services
├── controllers/      # HTTP handlers
└── routers/          # Route definitions
```

**Application Layers**:
- **Controller Layer**: HTTP requests, input validation, invokes services
- **Service Layer**: Core business logic, validation, orchestration
- **Repository/Adapter Layer**: Data persistence and external integrations

### 1.3 Adapter Pattern

Wrap third-party libraries (Redis, MongoDB, etc.) in adapters:
- Services interact via interfaces
- Never import driver packages directly in services

### 1.4 Multi-Tenancy

- Ensure all data access and caching respect tenant isolation
- Always propagate `context.Context` containing Tenant ID
- Use tenant context in all repository calls

### 1.5 ARCHITECTURAL INTEGRITY - FOLDER PRESERVATION (CRITICAL)

**STRICTLY FORBIDDEN**:
- Deleting any architectural folders: `models/`, `repositories/`, `services/`, `controllers/`, `adapters/`, `routers/`
- Moving files from layer folders to feature root
- Flattening directory structure

### 1.6 Package Naming Convention (MANDATORY)

**THE GOLDEN RULE: ALIAS, DON'T FLATTEN**

All `.go` files in a feature MUST use the **feature name** as package:

```go
// File: features/ssc/models/user.go
// ✅ CORRECT:
package ssc

// ❌ WRONG - NEVER use folder name:
package models
```

### 1.7 Import Aliasing (ALWAYS REQUIRED)

When importing sibling layers, ALWAYS use aliases:

```go
// ✅ CORRECT - Explicit aliasing
package ssc

import (
    ssc_models "github.com/av-platform/features/ssc/models"
    ssc_repos "github.com/av-platform/features/ssc/repositories"
)

func (s *AuthService) Register(user ssc_models.User) error {
    return s.repos.Create(user)
}
```

---

## 2. Technical Mastery & Best Practices

### 2.1 Advanced Error Handling

**ALWAYS wrap errors with context**:
```go
// ✅ CORRECT
user, err := s.repo.FindByID(ctx, id)
if err != nil {
    return nil, fmt.Errorf("failed to find user %s: %w", id, err)
}

// ❌ WRONG - Bare error return
return nil, err  // Lost context!
```

### 2.2 Concurrency & Context

**Context Usage Rules**:
- Use `context.Context` for cancellation, timeouts, and tracing
- NEVER use `context.Background()` inside request scope
- Pass parent context explicitly
- Worker pools for bounded concurrency

**context.TODO() is FORBIDDEN** in production code

```go
// ❌ FORBIDDEN - context.Background() in request handler
func (c *Controller) Handle(ctx echo.Context) error {
    result, err := c.service.Do(context.Background(), input)
    return ctx.JSON(http.StatusOK, result)
}

// ✅ CORRECT - Propagate request context
func (c *Controller) Handle(ctx echo.Context) error {
    reqCtx := ctx.Request().Context()
    result, err := c.service.Do(reqCtx, input)
    return ctx.JSON(http.StatusOK, result)
}
```

### 2.3 Observability & Logging (MANDATORY)

**CRITICAL: Always use the project's custom logger**

```go
// ❌ FORBIDDEN - Do NOT use standard log
import "log"
log.Printf("[ERROR] something failed: %v", err)

// ✅ REQUIRED - Use project's custom logger
import logger "github.com/av-platform/utils/logging"
logger.Error("Failed to process", "error", err, "requestID", reqID)
```

**Logger Usage Guidelines**:

| Level | When to Use | Example |
|-------|-------------|---------|
| `logger.Debug` | Detailed debugging info (disabled in production) | Tracing function entry/exit, variable values |
| `logger.Info` | Normal operational messages | Request completed, user action, state changes |
| `logger.Warn` | Warning conditions (not errors but notable) | Cache miss, retry attempt, deprecated usage |
| `logger.Error` | Error conditions that need attention | Failed operations, exceptions, business rule violations |

**Structured Fields Only**:
```go
// ❌ Wrong - Formatted strings
logger.Info(fmt.Sprintf("User %s logged in", userID))

// ✅ Correct - Key-value pairs
logger.Info("User logged in", "userID", userID, "tenantID", tenantID)
```

**NEVER log sensitive data** (passwords, tokens, PII, credit cards)

### 2.4 Security First

**Input Validation**:
- Validate all inputs at Controller layer
- Use struct tags or explicit validation logic
- Never trust user input

**SQL/NoSQL Injection Prevention**:
- Always use parameterized queries
- NEVER concatenate strings into queries

```go
// ❌ FORBIDDEN - SQL injection risk
query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", userID)

// ✅ CORRECT - Parameterized query
query := "SELECT * FROM users WHERE id = ?"
db.Query(query, userID)
```

**Advanced Security**:
- **Weak Crypto**: NEVER use `crypto/md5` or `crypto/sha1`. Use `crypto/sha256` or `bcrypt`
- **SSRF Protection**: Validate ALL user-provided URLs
- **Rate Limiting**: Protect public endpoints with rate limiters

### 2.5 Performance Mindfulness

- Be mindful of memory allocations in hot paths
- Avoid N+1 query problems; use batch fetching or correct joins
- **sync.Pool**: For frequently allocated objects
- **JSON Streaming**: For large datasets, use `json.NewEncoder`
- **Defer within Loops**: DANGER - causes memory leaks

```go
// ❌ Memory Leak - defer in loop
for _, file := range files {
    f, _ := os.Open(file)
    defer f.Close()  // Only closes at function return!
}

// ✅ Correct - Wrap in func
for _, file := range files {
    func() {
        f, _ := os.Open(file)
        defer f.Close()
    }()
}
```

### 2.6 Type Assertion Safety (MANDATORY)

**ALWAYS check type assertions**:

```go
// ❌ FORBIDDEN - Ignoring check
userID, _ := ctx.Get("user_id").(string)  // Silent failure!

// ✅ CORRECT - Always check
userID, ok := ctx.Get("user_id").(string)
if !ok {
    return ctx.JSON(http.StatusUnauthorized, map[string]string{
        "error": "user_id required",
    })
}
```

### 2.7 JSON Marshaling Best Practices (MANDATORY)

**ALWAYS handle marshal/unmarshal errors**:

```go
// ❌ FORBIDDEN - Ignoring marshal errors
payloadBytes, _ := json.Marshal(payload)

// ✅ CORRECT - Handle errors
payloadBytes, err := json.Marshal(payload)
if err != nil {
    return fmt.Errorf("failed to marshal payload: %w", err)
}
```

### 2.8 Resource Lock Handling (MANDATORY)

**ALWAYS log lock release failures**:

```go
// ❌ FORBIDDEN - Ignoring lock release
handler.ReleaseLock(ctx, cacheKey, lockVal)

// ✅ CORRECT - Always log failures
if err := handler.ReleaseLock(ctx, cacheKey, lockVal); err != nil {
    logger.Warn("Failed to release lock", "error", err, "cacheKey", cacheKey)
}
```

### 2.9 Goroutine Context Management (CRITICAL)

**ALL goroutines MUST**:
1. Accept parent context as parameter
2. Listen to `ctx.Done()` for cancellation
3. Use `defer` for cleanup
4. Have bounded execution (timeout or explicit cancellation)

```go
// ❌ FORBIDDEN - Orphaned goroutine
func (s *Service) StartBackgroundTask(userID string) {
    go func() {
        ctx := context.Background()  // LOSES parent lifecycle!
        s.processTask(ctx, userID)
    }()
}

// ✅ CORRECT - Proper lifecycle
func (s *Service) StartBackgroundTask(parentCtx context.Context, userID string) error {
    taskCtx, cancel := context.WithTimeout(parentCtx, 5*time.Minute)
    go func() {
        defer cancel()
        select {
        case <-taskCtx.Done():
            return
        default:
            s.processTask(taskCtx, userID)
        }
    }()
    return nil
}
```

---

## 3. Common Anti-Patterns

### Anti-Pattern 1: Context Propagation Issues (35% of critical issues)
```go
// ❌ Using context.Background() in controllers
result, err := c.service.Do(context.Background(), input)

// ✅ Use request context
result, err := c.service.Do(ctx.Request().Context(), input)
```

### Anti-Pattern 2: Ignored Error Returns (40% of critical issues)
```go
// ❌ Ignoring errors
payloadBytes, _ := json.Marshal(payload)
userID, _ := ctx.Get("user_id").(string)
limit, _ := strconv.Atoi(ctx.QueryParam("limit"))

// ✅ Handle all errors
payloadBytes, err := json.Marshal(payload)
if err != nil {
    return fmt.Errorf("failed to marshal: %w", err)
}
```

### Anti-Pattern 3: Bare Error Returns (15% of issues)
```go
// ❌ Loses context
return nil, err

// ✅ Wraps with context
return nil, fmt.Errorf("failed to find user %s: %w", id, err)
```

### Anti-Pattern 4: Missing Input Validation
```go
// ❌ No validation
func (c *Controller) Create(ctx echo.Context) error {
    var req CreateRequest
    ctx.Bind(&req)
    return c.service.Create(ctx.Request().Context(), req)
}

// ✅ Validate all inputs
func (c *Controller) Create(ctx echo.Context) error {
    var req CreateRequest
    if err := ctx.Bind(&req); err != nil {
        return ctx.JSON(http.StatusBadRequest, ErrorResponse{"Invalid request"})
    }
    return c.service.Create(ctx.Request().Context(), req)
}
```

### Anti-Pattern 5: Function Size Issues (~34% of warnings)
```go
// ❌ Monolithic function (100+ lines)
func (s *Service) ProcessWorkflow(ctx context.Context, input Input) (Output, error) {
    // Too long!
}

// ✅ Decomposed into focused helpers
func (s *Service) ProcessWorkflow(ctx context.Context, input Input) (Output, error) {
    if err := s.validateInput(input); err != nil {
        return Output{}, fmt.Errorf("validation failed: %w", err)
    }
    return s.executeLogic(ctx, input)
}
```

---

## 4. Verification Scripts (MANDATORY Before Completion)

### One-Stop Quality Check (RECOMMENDED)

```bash
python .claude/skills/expert-go-backend-developer/scripts/generate_quality_report.py features/<feature_name>
```

### Individual Validation Scripts

| Check | Script | Purpose |
|-------|--------|---------|
| Production Ready | `validate_production_ready.py` | Comprehensive production readiness |
| Context Propagation | `validate_context_propagation.py` | Controllers use request context |
| Error Handling | `validate_error_handling.py` | All errors handled and wrapped |
| Context TODO | `validate_context_todo.py` | **BLOCKER** - No `context.TODO()` |
| Function Size | `validate_function_size.py` | Functions ≤ 50 lines |
| Security | `validate_security.py` | Security vulnerabilities |
| Route-Controller Mismatch | `validate_route_controller_mismatch_v2.py` | **CRITICAL** - No duplicate routes or missing handlers |
| Cyclomatic Complexity | `analyze_cyclomatic_complexity.py` | Complexity ≤ 10 |
| Goroutines | `analyze_goroutines.py` | Proper goroutine lifecycle |
| Architecture | `analyze_code.py` | Clean Architecture compliance |

All scripts are in: `.claude/skills/expert-go-backend-developer/scripts/`

---

## 5. Pre-Completion Checklist (MANDATORY)

Before marking ANY task as complete:

**Context Management**:
- [ ] No `context.Background()` in request handlers
- [ ] No `context.TODO()` in production code (DEPLOYMENT BLOCKER)
- [ ] All goroutines receive parent context and check `ctx.Done()`
- [ ] `context.Context` passed through call chain

**Error Handling**:
- [ ] All errors checked and wrapped with context
- [ ] No ignored errors (`_, _ :=`) without comment
- [ ] All JSON marshal/unmarshal errors handled
- [ ] All type assertions checked with `ok` value
- [ ] All lock release errors logged

**Code Quality**:
- [ ] No TODOs, FIXMEs, XXX, HACK, or placeholders
- [ ] No empty function bodies or `return nil` without logic
- [ ] Functions ≤ 50 lines, Files ≤ 500 lines
- [ ] All inputs validated in controllers
- [ ] Cyclomatic complexity ≤ 10
- [ ] Edge cases handled (empty, nil, zero, boundary conditions)

**Build & Validation**:
- [ ] `go build ./...` passes
- [ ] `go test ./...` passes
- [ ] `validate_route_controller_mismatch_v2.py` passes (no duplicate routes)
- [ ] All validators pass
- [ ] Quality report score ≥ 60

**Python/AI/ML Additional Checks**:
- [ ] ALL functions have complete type hints
- [ ] ALL public functions have Google-style docstrings
- [ ] Random seeds set for reproducibility
- [ ] Proper GPU memory management

---

# SKILLS ECOSYSTEM (12 Specialized Skills)

## Skills By Category

### 1. Core Development Skills (6)

#### expert-pm-ba-orchestrator (Main Brain)
- **Purpose**: SDLC orchestration - Điều phối toàn bộ quy trình phát triển
- **Auto-Load When**: User mentions PRD, Master Plan, Sprint, Change Request; Starting new project/feature
- **Scripts**: `initialize_project.py`, `generate_master_plan.py`, `validate_prd.py`, `update_progress.py`, `analyze_impact.py`

#### expert-researcher
- **Purpose**: Phase 0 - Nghiên cứu tính khả thi, so sánh công nghệ
- **Auto-Load When**: User asks about technology choices; "Research", "Compare", "Feasibility" keywords
- **Output**: RESEARCH_NOTES.md with Go/No-Go recommendation

#### expert-solutions-architect
- **Purpose**: Technical Blueprint - Thiết kế kiến trúc hệ thống
- **Auto-Load When**: Architecture discussions; System design requests; Project scaffolding needed
- **Output**: ARCHITECTURE.md, skeleton structure

#### expert-go-backend-developer
- **Purpose**: Backend implementation - Phát triển Go backend với Clean Architecture
- **Auto-Load When**: Editing any `features/*/*.go` file; Backend API development
- **MUST Follow**: Interface-First Design, Dependency Injection, No Technical Debt
- **Quality Scripts**: `generate_quality_report.py`, `validate_production_ready.py`, etc.

#### expert-react-frontend-developer
- **Purpose**: Frontend implementation - Phát triển React/TS frontend
- **Auto-Load When**: Editing any `apps/frontend/**` file; UI component development
- **MUST Follow**: Feature-Sliced Design, Zod Validation, Zustand State

#### expert-python-aiml-developer
- **Purpose**: AI/ML development - Phát triển ML models và AI agents
- **Auto-Load When**: Editing any `.py` file in AI/ML context; Model training/inference
- **MUST Follow**: MLOps guidelines, reproducibility, proper GPU management

---

### 2. Quality & Operations Skills (3)

#### expert-code-reviewer
- **Purpose**: Quality gate - Kiểm tra chất lượng code
- **Auto-Load When**: After completing implementation; Before commit/PR
- **Scripts**: `generate_quality_report.py`, `compare_be_fe_contracts.py`
- **Pass Criteria**: Score ≥ 60, No Critical Issues

#### expert-security-auditor
- **Purpose**: Security audit - Kiểm tra bảo mật
- **Auto-Load When**: Security concerns mentioned; Before deployment
- **Scripts**: `scan_owasp_top10.py`, `scan_dependencies.py`, `detect_secrets.py`, `audit_authentication.py`
- **Pass Criteria**: No Critical/High vulnerabilities

#### expert-test-engineer
- **Purpose**: Testing strategy - Chiến lược testing toàn diện
- **Auto-Load When**: Test file creation/modification; Coverage issues
- **Scripts**: `analyze_coverage.py`, `setup_e2e_framework.py`, `setup_load_testing.py`
- **Pass Criteria**: Coverage ≥ 80%, All tests pass

---

### 3. Infrastructure & Operations Skills (4)

#### expert-devops-engineer
- **Purpose**: DevOps automation - Tự động hóa DevOps
- **Auto-Load When**: Dockerfile, docker-compose, K8s, CI/CD pipeline setup
- **Scripts**: `validate_docker.py`, `generate_k8s_manifests.py`, `setup_github_actions.py`

#### expert-database-admin
- **Purpose**: Database management - Quản lý và tối ưu database
- **Auto-Load When**: Query optimization; Migration creation; Schema changes
- **Scripts**: `analyze_query_performance.py`, `suggest_indexes.py`, `validate_migrations.py`

#### expert-observability-engineer
- **Purpose**: Monitoring & observability - Giám sát hệ thống
- **Auto-Load When**: Metrics/alerts setup; Logging configuration; Distributed tracing
- **Scripts**: `setup_prometheus.py`, `generate_grafana_dashboards.py`, `setup_jaeger.py`

#### expert-performance-engineer
- **Purpose**: Performance optimization - Tối ưu hiệu năng
- **Auto-Load When**: Performance issues; Profiling; Benchmarking
- **Scripts**: `generate_benchmarks.py`, `analyze_bottlenecks.py`, `detect_memory_leaks.py`

#### expert-api-documentarian
- **Purpose**: API documentation - Tài liệu API
- **Auto-Load When**: OpenAPI/Swagger generation; API contract validation
- **Scripts**: `generate_openapi.py`, `validate_api_contracts.py`, `detect_breaking_changes.py`

---

## Quick Reference: Task → Skill Matrix

| Task Type | Primary Skill | Support Skills |
|-----------|---------------|----------------|
| New Feature (Backend) | expert-go-backend-developer | code-reviewer, test-engineer |
| New Feature (Frontend) | expert-react-frontend-developer | code-reviewer, test-engineer |
| AI/ML Model | expert-python-aiml-developer | code-reviewer, test-engineer |
| Bug Fix | Same as feature type | code-reviewer |
| Performance Issue | expert-performance-engineer | database-admin |
| Security Concern | expert-security-auditor | devops-engineer |
| Database Change | expert-database-admin | go-backend-developer |
| Deployment | expert-devops-engineer | observability-engineer |
| API Documentation | expert-api-documentarian | - |
| Code Review | expert-code-reviewer | - |
| Testing | expert-test-engineer | - |

---

# PROJECT STRUCTURE

## Backend Modules (Features)
- **SSC (Security Service Center)**: Authentication, MFA, JWT management
- **VMS (Vehicle Management System)**: Vehicle tracking and management
- **AOC (Automated Operations Center)**: Workflow automation
- **MDM (Mission Data Management)**: Mission planning and scheduling
- **Fleet Optimization**: AI/ML-driven optimization
- **HML (Hazard Mapping Localization)**: Real-time hazard detection and localization
- **DPE (Data Processing Engine)**: Data processing pipeline
- **DCP (Data Control Plane)**: Data governance and control
- **Apollo**: Integration with Apollo autonomous driving system

## Infrastructure Services
- **MongoDB** (27017): Primary database
- **PostgreSQL** (5432): Relational database (optional)
- **Redis** (6379): Caching and session storage
- **NATS** (4222, 8222): Message broker with JetStream
- **Kafka** (9092): Event streaming
- **MQTT/Mosquitto** (1883): IoT messaging
- **MinIO** (9000, 9001): S3-compatible storage
- **Elasticsearch** (9200): Search and analytics
- **InfluxDB** (8086): Time-series metrics
- **Vault** (8200): Secrets management

---

# DOCUMENTATION

Key documentation files:
- PRODUCT REQUIREMENTS DOCUMENT: `project-documentation/prd/*.md`
- ARCHITECUTURE: `project-documentation/architecture/*.md` - System architecture specification
- SOFTWARE REQUIREMENTS SPECIFICATION: `project-documentation/srs/*.md` - Software requirements specification
- MASTER PLANS: `project-documentation/master_plans/*.md` - Comprehensive master plans
- DETAILED IMPLEMENTATION PLANS: `project-documentation/detail_plans/*.md` - Detailed implementation plans
- OVERVIEW PROJECT: `OVERVIEW.md` - Overview of project structure and modules
- API DOCUMENTATION: `project-documentation/api/*` - API specifications and Developer Guide
- DEVELOPMENT PROCESS REPORT: `project-documentation/development_process_reports/*` - Development process reports

---

# SDLC WORKFLOW (8 Phases)

### Phase 0: Research (Optional)
```
When: New project, new technology, uncertain feasibility
Auto-Load: expert-researcher
Deliverable: RESEARCH_NOTES.md with Go/No-Go recommendation
```

### Phase 1: PRD Analysis
```
When: Starting new feature/project
Auto-Load: expert-pm-ba-orchestrator
Steps: Create PRD.md → Define requirements → Validate with scripts/validate_prd.py
```

### Phase 2: Architecture Design
```
When: PRD approved
Auto-Load: expert-solutions-architect
Deliverable: ARCHITECTURE.md with Clean Architecture blueprint
```

### Phase 3: Master Plan
```
When: Architecture approved
Auto-Load: expert-pm-ba-orchestrator
Deliverable: MASTER_PLAN.md with Work Packages (WP-001, WP-002...)
```

### Phase 4: SRS Deep Dive
```
When: Master Plan approved
Auto-Load: expert-pm-ba-orchestrator + expert-api-documentarian
Deliverable: SRS_*.md files for all modules
```

### Phase 5: Detail Plans
```
When: SRS approved
Auto-Load: expert-pm-ba-orchestrator
Deliverable: DETAIL_PLAN_*.md with atomic 2-hour tasks
```

### Phase 6: Development (MANDATORY Quality Gates)
```
Backend (Go):
  Auto-Load: expert-go-backend-developer
  Pattern: Clean Architecture, Interface-First, DI

Frontend (React):
  Auto-Load: expert-react-frontend-developer
  Pattern: Feature-Sliced Design, Zod, Zustand

AI/ML (Python):
  Auto-Load: expert-python-aiml-developer
  Pattern: MLOps, reproducibility

Quality Gates (ALL REQUIRED):
  Gate 1 - Code Review: expert-code-reviewer → Score ≥ 60
  Gate 2 - Security: expert-security-auditor → No Critical/High
  Gate 3 - Tests: expert-test-engineer → Coverage ≥ 80%
  Gate 4 - Performance: expert-performance-engineer → Latency OK
  Gate 5 - API Contract: expert-api-documentarian → Contracts aligned
```

### Phase 7: Deployment
```
When: All Quality Gates passed
Auto-Load: expert-devops-engineer
Support: expert-database-admin (migrations)
Steps: Validate Docker/K8s → Security scan → Deploy → Verify health
```

### Phase 8: Operations
```
When: In production
Auto-Load: expert-observability-engineer
Activities: Monitor metrics (Prometheus) → Review logs → Trace requests
```

---

## Pre-Commit Checklist (MANDATORY)

Before ANY commit:
- [ ] No TODOs, FIXMEs, placeholders
- [ ] All errors handled and wrapped
- [ ] Quality report score ≥ 60
- [ ] No context.TODO() in production code
- [ ] All type assertions checked
- [ ] Build passes: `go build ./...`
- [ ] Tests pass: `go test ./...`

---

# API ENDPOINTS

The backend provides:
- **HTTP API** (port 8080):
  - Health Check: `GET /health`
  - Readiness: `GET /ready`
  - Feature-specific endpoints under each feature module
- **gRPC Server** (port 50051): Localization service and internal communication

All endpoints support multi-tenancy via tenant headers.
