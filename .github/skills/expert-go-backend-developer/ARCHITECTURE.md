# System Integration Management - Architecture Documentation

> **Version:** v1.0.1  
> **Last Updated:** January 12, 2026  
> **Target Audience:** AI Agents, Developers, System Architects

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [High-Level Architecture](#high-level-architecture)
- [Core Architectural Principles](#core-architectural-principles)
- [Module Architecture](#module-architecture)
  - [Proxy Cache System](#1-proxy-cache-system)
  - [Workflow Engine](#2-workflow-engine)
  - [Authorization & Authentication](#3-authorization--authentication)
  - [Multi-Tenancy System](#4-multi-tenancy-system)
  - [MinIO S3 Integration](#5-minio-s3-integration)
  - [Superset Integration](#6-superset-integration)
  - [Management & Metrics](#7-management--metrics)
- [Layer Architecture](#layer-architecture)
- [Database & Storage](#database--storage)
- [API Architecture](#api-architecture)
- [Security Architecture](#security-architecture)
- [Performance & Scalability](#performance--scalability)
- [Development Guidelines](#development-guidelines)
- [References](#references)

---

## System Overview

**System Integration Management (SIM)** là một hệ thống gateway tích hợp phức tạp được xây dựng trên nền tảng Go và React, cung cấp các khả năng:

- **Intelligent Reverse Proxy** với Redis Cluster caching
- **Workflow Automation Engine** với visual designer
- **Multi-Tenancy Management** với isolation hoàn toàn
- **Authentication/Authorization** tích hợp Keycloak
- **File Storage** với MinIO S3
- **Analytics** tích hợp Apache Superset

### Key Characteristics

- **High Performance**: Go 1.25.5 với goroutine concurrency
- **Distributed**: Redis Cluster, MongoDB Replica Set
- **Scalable**: Horizontal scaling, stateless design
- **Secure**: JWT-based auth, RBAC, tenant isolation
- **Observable**: Metrics, logging, health checks

---

## Technology Stack

### Backend Stack

```yaml
Language: Go 1.25.5
Framework: Echo v4.13.4
Storage:
  - Redis Cluster (caching, session)
  - MongoDB v1.17+ (workflow, metadata)
  - PostgreSQL (optional, structured data)
  
Libraries:
  - JWT: golang-jwt/jwt v5.3.0
  - JSON: goccy/go-json v0.10.5 (high performance)
  - OpenAPI: getkin/kin-openapi v0.133.0
  - MQTT: eclipse/paho.mqtt.golang v1.5.1
  - NATS: nats-io/nats.go v1.36.0
  - Task Queue: hibiken/asynq v0.24.1
  - Scheduler: robfig/cron v3.0.1
  - Expression: expr-lang/expr v1.17.7
```

### Frontend Stack

```yaml
Framework: React 19
Language: TypeScript
Build Tool: Vite
UI Library: Material-UI (MUI)
State Management: Zustand
Workflow Designer: React Flow
HTTP Client: Axios
```

### Infrastructure

```yaml
Containerization: Docker
Orchestration: Docker Compose / Kubernetes
Message Queue: NATS
Object Storage: MinIO
Analytics: Apache Superset
SSO: Keycloak
```

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Client Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐                │
│  │ Web Browser │  │ Mobile App  │  │ External API │                │
│  └─────────────┘  └─────────────┘  └──────────────┘                │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────┼─────────────────────────────────────────┐
│                   API Gateway Layer                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Echo Framework                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │  CORS       │  │ Auth MW     │  │ Tenant MW   │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────────────┐
│                      Core Services Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐         │
│  │ Proxy Cache    │  │ Workflow       │  │ Authorization │         │
│  │ Service        │  │ Engine         │  │ Service       │         │
│  └────────────────┘  └────────────────┘  └───────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐         │
│  │ Tenant         │  │ MinIO S3       │  │ Superset      │         │
│  │ Service        │  │ Service        │  │ Service       │         │
│  └────────────────┘  └────────────────┘  └───────────────┘         │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────────────┐
│                      Adapter Layer                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐         │
│  │ Redis Adapter  │  │ MongoDB        │  │ Keycloak      │         │
│  │                │  │ Adapter        │  │ Adapter       │         │
│  └────────────────┘  └────────────────┘  └───────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐         │
│  │ MinIO Adapter  │  │ NATS Adapter   │  │ MQTT Adapter  │         │
│  └────────────────┘  └────────────────┘  └───────────────┘         │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────────────┐
│                      Storage Layer                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐         │
│  │ Redis Cluster  │  │ MongoDB        │  │ PostgreSQL    │         │
│  │ (Cache, State) │  │ (Workflow)     │  │ (Metadata)    │         │
│  └────────────────┘  └────────────────┘  └───────────────┘         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐                            │
│  │ MinIO          │  │ Keycloak       │                            │
│  │ (File Storage) │  │ (SSO/Identity) │                            │
│  └────────────────┘  └────────────────┘                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Core Architectural Principles

### 1. **Interface-First Design**

```go
// Services always depend on interfaces, not concrete types
type WorkflowService interface {
    CreateWorkflow(ctx context.Context, workflow *Workflow) error
    ExecuteWorkflow(ctx context.Context, id string) (*Execution, error)
}

// Implementation hidden behind interface
type workflowServiceImpl struct {
    repo WorkflowRepository
    engine WorkflowEngine
}
```

**Benefits:**
- Dependency Inversion (SOLID)
- Easy mocking for tests
- Swappable implementations

### 2. **Adapter Pattern**

```
┌─────────────────────────────────────────────────────┐
│           Service Layer (Domain Logic)              │
│  - No external library imports                      │
│  - Depends on interfaces only                       │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼ depends on interface
┌─────────────────────────────────────────────────────┐
│           Adapter Layer (Integration)                │
│  - Wraps external libraries                         │
│  - Implements service interfaces                    │
│  - Isolates dependencies                            │
└─────────────────────────────────────────────────────┘
    ▼ imports                ▼ imports
┌──────────────┐      ┌──────────────┐
│ go-redis     │      │ mongo-driver │
└──────────────┘      └──────────────┘
```

**Example:**
- `adapters/keycloak/` wraps `Nerzal/gocloak`
- `adapters/minio/` wraps `minio/minio-go`
- Services never import these libraries directly

### 3. **Feature-Based Structure**

```
features/
├── authorization/      # Keycloak integration
│   ├── adapters/       # Keycloak client wrapper
│   ├── controllers/    # HTTP handlers
│   ├── models/         # Domain entities
│   ├── repositories/   # Data persistence
│   ├── routers/        # Route definitions
│   └── services/       # Business logic
│
├── workflow/           # Workflow automation
│   ├── adapters/       # MongoDB, SMTP, etc.
│   ├── controllers/    # API handlers
│   ├── core/           # Workflow engine
│   ├── models/         # Workflow entities
│   └── services/       # Workflow services
│
└── proxy_cache/        # Reverse proxy with caching
    ├── controllers/    # Proxy handlers
    ├── models/         # Configuration models
    ├── repositories/   # Redis storage
    └── services/       # Cache, invalidation logic
```

**Key Points:**
- Each feature is self-contained
- Clear separation of concerns
- Independent deployment possible

### 4. **Dependency Injection**

```go
// Central DI container: routers/constant.go
func InitialConfiguration(cfgPath string) configModel.AppConfig {
    // 1. Initialize infrastructure
    redisClient = redisRepo.NewRedisClient(cfg)
    mongoClient, _ = factory.CreateMongoClient(ctx)
    
    // 2. Build adapters
    kcAdapter, _ := authorizationAdapter.NewClientPair(cfg.Keycloak.KeycloakBase)
    
    // 3. Wire services
    kcMgr := authorizationSvc.NewKeycloakManager(cfg, redisClient, kcAdapter)
    
    // 4. Create controllers
    keycloakController = authorizationCtl.NewKcController(kcMgr)
    
    // 5. Setup middleware
    authMw = authMiddleware.NewAuthMiddleware(cfg, kcMgr)
    
    return cfg
}
```

**Benefits:**
- Single source of truth for wiring
- Easy to understand dependencies
- Testable with mock injection

### 5. **Multi-Tenancy Isolation**

```
Request → Tenant Middleware → Extract Tenant ID → Inject Context
                                      ↓
                        ┌─────────────┴──────────────┐
                        │                            │
                    Tenant A                     Tenant B
                        │                            │
            ┌───────────┼────────────┐   ┌──────────┼────────────┐
            │           │            │   │          │            │
        Redis Cache  Backends   Workflows  Redis Cache Backends Workflows
        (isolated)   (scoped)   (scoped)   (isolated) (scoped)  (scoped)
```

**Isolation Layers:**
- Cache keys include tenant ID
- Backend assignment per tenant
- Workflow data filtered by tenant
- Resource versioning per tenant

---

## Module Architecture

### 1. Proxy Cache System

**Purpose:** Intelligent reverse proxy với Redis caching và automatic invalidation

**Location:** `features/proxy_cache/`

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     ProxyController                          │
│  - ProxyHandler (HTTP handler)                              │
│  - Middleware: Auth, Tenant, Rate Limit                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                  ProxyService (Orchestrator)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ CacheHandler│  │ Invalidation │  │ Versioning   │       │
│  │             │  │ Handler      │  │ Handler      │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │ SwaggerWatcher (Background)                     │       │
│  │  - Fetch OpenAPI specs                          │       │
│  │  - Generate invalidation rules                  │       │
│  │  - Store to Redis                               │       │
│  └─────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

#### Key Components

**CacheHandler:**
```go
// Get cached response (FAST PATH)
func (ch *CacheHandler) GetFromCache(cacheKey string) (bool, error)

// Cache response with TTL
func (ch *CacheHandler) SetCache(key string, data []byte, ttl int) error

// Track dependencies for invalidation
func (ch *CacheHandler) AddReverseIndexDep(collection, cacheKey string) error
```

**InvalidationHandler:**
```go
// Invalidate on write operations (POST/PUT/PATCH/DELETE)
func (ih *InvalidationHandler) InvalidateOnWrite(rules []InvalidationCfg, path string, body []byte)

// Execute invalidation in Redis
func (ih *InvalidationHandler) executeInvalidation(resourceIncs, collectionsToBump map[string]map[string]struct{})
```

**VersioningHandler:**
```go
// Determine version for cache key
func (vh *VersioningHandler) DetermineVersionPart(path string, rules []InvalidationCfg) string

// Try collection-level versioning (most specific)
func (vh *VersioningHandler) tryCollectionVersioning(path string) string

// Fallback to resource-level versioning
func (vh *VersioningHandler) tryResourceVersioning(path string) string
```

#### Cache Flow

```
GET Request
    ↓
Build Cache Key = hash(method + path + query + body + version)
    ↓
Check Redis: proxy:cache:cache:{tenant}:{hash}
    ↓
    ├─ HIT → Return cached (1-5ms) ✅ FAST PATH
    │
    └─ MISS → Forward to backend (100-500ms)
               ↓
           Cache response
               ↓
           Register reverse-index
               ↓
           Return to client

POST/PUT/PATCH/DELETE Request
    ↓
Extract affected resources from path/body
    ↓
Increment resource version: proxy:cache:resver:{tenant}:{type}:{id}
    ↓
Increment collection version: proxy:cache:colver:{tenant}:{collection}
    ↓
Delete dependency cache keys via reverse-index
    ↓
Forward to backend
```

#### Configuration

```yaml
cache_defaults:
  default_ttl_seconds: 60      # Cache TTL
  max_body_bytes: 5242880      # Max cache body size (5MB)

swagger:
  enabled: true
  poll_interval_secs: 3600     # Refetch interval
  list_keywords:               # Keywords for list endpoints
    - list
    - search
    - query
```

**References:**
- Code: `features/proxy_cache/services/`

---

### 2. Workflow Engine

**Purpose:** Visual workflow automation với drag-and-drop designer

**Location:** `features/workflow/`

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (React Flow)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ WorkflowDesigner.jsx                                   │ │
│  │  - Visual node editor                                  │ │
│  │  - Node palette (Triggers, Actions, Logic)            │ │
│  │  - Properties panel                                    │ │
│  │  - Execution monitor                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST API
┌───────────────────────────┼──────────────────────────────────┐
│                  Backend Controllers                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ WorkflowController (CRUD)                             │ │
│  │ WebhookTriggerController (Webhook endpoints)          │ │
│  │ ExecutionController (Monitoring)                      │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                  Core Workflow Engine                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ WorkflowEngine                                         │ │
│  │  - DAG-based execution                                 │ │
│  │  - Node executor registry                              │ │
│  │  - State management (Redis)                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Node Executors (core/nodes/)                          │ │
│  │  ├─ Triggers: webhook, schedule, manual               │ │
│  │  ├─ Actions: http, mongo, email, sms                  │ │
│  │  ├─ Logic: if, switch, loop                           │ │
│  │  └─ Core: set, wait, subworkflow                      │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MongoDB      │  │ Redis        │  │ NATS         │      │
│  │ (Workflows)  │  │ (State)      │  │ (Events)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

#### Core Components

**WorkflowEngine:**
```go
type WorkflowEngine interface {
    ExecuteWorkflow(ctx context.Context, workflow *Workflow, triggerData []byte) (*Execution, error)
    CancelExecution(ctx context.Context, executionID string) error
}

// Execution Flow
func (e *WorkflowEngine) ExecuteWorkflow() {
    1. Validate workflow structure
    2. Initialize execution context
    3. Find trigger node
    4. Build DAG (topological sort)
    5. Execute nodes in order
    6. Handle errors & retries
    7. Update execution status
    8. Save to MongoDB
}
```

**Node Executor Interface:**
```go
type NodeExecutor interface {
    Execute(ctx context.Context, node *Node, input json.RawMessage) (json.RawMessage, error)
    Validate(node *Node) error  // CRITICAL: Never leave empty!
    GetType() NodeType
    GetDescription() NodeDescription
}
```

**Example Executors:**

```go
// HTTP Request Executor
type HTTPExecutor struct {
    client *http.Client
}

func (e *HTTPExecutor) Execute(ctx, node, input) (output, error) {
    // 1. Parse HTTP config from node.Parameters
    config := parseHTTPConfig(node.Parameters)
    
    // 2. Build request with headers, body
    req := buildRequest(config)
    
    // 3. Execute with retry
    resp, err := executeWithRetry(req, config.Retry)
    
    // 4. Return structured output
    return json.Marshal(map[string]any{
        "status_code": resp.StatusCode,
        "body": resp.Body,
        "headers": resp.Headers,
    })
}

// MongoDB Query Executor
type MongoQueryExecutor struct {
    client *mongo.Client
}

func (e *MongoQueryExecutor) Execute(ctx, node, input) (output, error) {
    // 1. Parse MongoDB config
    config := parseMongoConfig(node.Parameters)
    
    // 2. Connect to collection
    coll := client.Database(config.Database).Collection(config.Collection)
    
    // 3. Execute query
    cursor, err := coll.Find(ctx, config.Filter)
    
    // 4. Return results
    var results []bson.M
    cursor.All(ctx, &results)
    return json.Marshal(results)
}
```

#### Workflow Models

```go
type Workflow struct {
    ID          string
    Name        string
    Status      WorkflowStatus  // draft, active, inactive
    Nodes       []*Node
    Connections []*Connection
    Settings    *WorkflowSettings
    TenantID    string
    CreatedAt   time.Time
}

type Node struct {
    ID          string
    Type        NodeType  // "trigger.webhook", "action.http", etc.
    Parameters  map[string]interface{}  // Node configuration
    Position    Position
    RetryPolicy *RetryPolicy
}

type Connection struct {
    SourceID   string
    TargetID   string
    SourcePort string  // "main", "true", "false", "error"
    TargetPort string
}

type Execution struct {
    ID          string
    WorkflowID  string
    Status      ExecutionStatus  // queued, running, completed, failed
    TriggerData []byte
    NodeStates  map[string]*NodeExecutionState
    StartTime   time.Time
    EndTime     *time.Time
}
```

#### Node Types

```
Triggers:
  - trigger.webhook      # HTTP webhook
  - trigger.schedule     # Cron schedule
  - trigger.manual       # Manual execution

Actions:
  - action.http          # HTTP request
  - action.mongo.query   # MongoDB query
  - action.mongo.insert  # MongoDB insert
  - action.email         # Send email (SMTP)
  - action.sms           # Send SMS (Twilio)
  - action.telegram      # Telegram message
  - action.fcm           # Firebase push notification
  - action.service.*     # Backend service calls

Logic:
  - logic.if             # Conditional branching
  - logic.switch         # Multi-way branching
  - logic.loop           # Iteration

Core:
  - core.set             # Variable assignment
  - core.wait            # Delay execution
  - core.subworkflow     # Call another workflow
```

#### API Endpoints

```
POST   /_admin/api/v1/workflows                Create workflow
GET    /_admin/api/v1/workflows                List workflows
GET    /_admin/api/v1/workflows/:id            Get workflow
PUT    /_admin/api/v1/workflows/:id            Update workflow
DELETE /_admin/api/v1/workflows/:id            Delete workflow
POST   /_admin/api/v1/workflows/:id/activate   Activate
POST   /_admin/api/v1/workflows/:id/execute    Execute

POST   /webhook/:path                          Trigger webhook
GET    /webhook/_debug                         Debug webhooks

GET    /_admin/api/v1/workflows/executions     List executions
GET    /_admin/api/v1/workflows/executions/:id Execution details
```

**References:**
- Code: `features/workflow/core/`, `features/workflow/controllers/`

#### Plugin Architecture

**Purpose:** Clean separation between engine core and node executors

**Architecture Layers:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│              (features/workflow/controllers/workflow/module.go)                │
│  - Wires dependencies                                       │
│  - Initializes plugin factory                               │
│  - Injects services into plugins                            │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────────────────┐
│                    Plugin Layer                             │
│           (features/workflow/core/plugin/*)                          │
│  - Plugin interfaces (ExecutorPlugin)                       │
│  - Plugin registry (auto-discovery)                         │
│  - Version manager (migrations)                             │
│  - Base adapters (auto-wrapping)                            │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────────────────┐
│                   Engine Core Layer                         │
│            (features/workflow/core/execution/*)                      │
│  - Execution engine (DAG orchestration)                     │
│  - Node orchestrator (execution flow)                       │
│  - State manager (execution state)                          │
│  - Only depends on NodeExecutorRegistry interface           │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────────────────┐
│                   Executor Layer                            │
│           (features/workflow/core/nodes/*/*)                         │
│  - Concrete executor implementations                        │
│  - HTTP, MongoDB, IF, Loop, etc.                            │
│  - Isolated from engine via plugin interface                │
└─────────────────────────────────────────────────────────────┘
```

**Key Interfaces:**

```go
type ExecutorPlugin interface {
    // Lifecycle
    Initialize(ctx context.Context, deps PluginDependencies) error
    Shutdown(ctx context.Context) error
    
    // Metadata
    GetMetadata() PluginMetadata
    
    // Execution (delegates to NodeExecutor)
    Execute(ctx context.Context, node *Node, input []byte) ([]byte, error)
    Validate(node *Node) error
    GetType() NodeType
    GetDescription() NodeDescription
}
```

**Auto-Registration:**
```go
// 1. Create plugin factory
pluginFactory := wfPluginAdapter.NewPluginAdapterFactory(
    mongoURI, evaluator, mongoClient, credService,
)

// 2. Register all built-in executors
pluginFactory.RegisterBuiltinExecutors(ctx)

// 3. Get plugin-enabled registry
registry := pluginFactory.GetRegistry()

// 4. Use registry with engine (no coupling to executors)
engine := execution.NewExecutionEngine(registry, ...)
```

**Versioning & Migration:**
```go
// Semantic versioning
type Version struct {
    Major int  // Breaking changes
    Minor int  // New features (backward compatible)
    Patch int  // Bug fixes
}

// Auto-migration between versions
vm.RegisterMigration(
    "action.http",
    Version{1, 0, 0}, // from
    Version{2, 0, 0}, // to
    func(oldConfig map[string]any) (map[string]any, error) {
        newConfig := make(map[string]any)
        newConfig["endpoint"] = oldConfig["url"]  // Rename field
        return newConfig, nil
    },
)
```

**Benefits:**
- ✅ Engine core doesn't import concrete executors
- ✅ Add new executor without modifying engine code
- ✅ Automatic version migration for workflows
- ✅ Isolated testing with mock engine

#### Pattern 4: Unified Output Format

**Purpose:** Standardized node output structure separating data from metadata

**Structure:**

```json
{
  "json": {
    "userId": 123,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "metadata": {
    "_type": "http",
    "_timestamp": 1234567890,
    "_duration_ms": 145,
    "statusCode": 200,
    "headers": {...}
  }
}
```

**Helper Functions:**

```go
// Build unified output
func BuildUnifiedOutput(data any, executorType string, metadata map[string]any) (json.RawMessage, error) {
    if metadata == nil {
        metadata = make(map[string]any)
    }
    metadata["_type"] = executorType
    metadata["_timestamp"] = time.Now().UnixMilli()
    
    output := map[string]any{
        "json":     data,
        "metadata": metadata,
    }
    return json.Marshal(output)
}

// Convert legacy formats to unified
func ConvertLegacyFormat(output json.RawMessage) json.RawMessage {
    // Pattern 1 (IF nodes): {output_port, is_true, data} → unified
    // Pattern 2 (HTTP): {statusCode, headers, body} → unified
    // Pass-through for already unified or unknown formats
    return converted
}
```

**Normalization Pipeline:**

```
┌─────────────────────────┐
│  Executor Output        │
│  (any format)           │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  ConvertLegacyFormat    │
│  (Step 1)               │
│  Legacy → Unified       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  UnwrapNodeOutput       │
│  (Step 2)               │
│  Extract json field     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Normalized Data        │
│  (consistent format)    │
└─────────────────────────┘
```

**Expression Access:**
```javascript
// Access data
{{ $json.userId }}        // 123
{{ $json.name }}          // "John Doe"

// Access metadata
{{ $metadata._type }}     // "http"
{{ $metadata.statusCode }} // 200
{{ $metadata._timestamp }} // 1234567890
```

**Benefits:**
- ✅ Clean separation: data and metadata never mixed
- ✅ Consistent expressions: always `{{ $json.field }}`
- ✅ Better debugging: metadata accessible via `{{ $metadata.* }}`
- ✅ Backward compatible: old executors work without changes
- ✅ Type safety: structure enforced at helper level

**Implementation Files:**
- `features/workflow/core/workflow/utils/normalization.go` - Pattern detection and conversion
- `features/workflow/core/workflow/utils/expressions.go` - Expression environment enhancement
- `features/workflow/core/workflow/execution/node_orchestrator.go` - Two-step normalization pipeline

---

### Node Development Workflow

**Purpose:** Standardized process for creating new nodes, enhancing existing nodes, and fixing bugs

#### 1. Creating a New Node

**Step-by-Step Process:**

```bash
# 1. Create Executor File
# Location: features/workflow/core/nodes/<category>/<node_name>_executor.go
# Categories: action, trigger, logic, data_processing, utility, core
```

**Example: Creating a Slack Node**

```go
// File: features/workflow/core/nodes/action/slack_executor.go
package workflow

import (
    "context"
    "fmt"
    json "github.com/goccy/go-json"
    models "system_integration_management/features/workflow/models/workflow"
)

// SlackExecutor sends messages to Slack
type SlackExecutor struct {
    client *http.Client
}

func NewSlackExecutor() *SlackExecutor {
    return &SlackExecutor{
        client: &http.Client{Timeout: 30 * time.Second},
    }
}

// GetType returns the node type
func (e *SlackExecutor) GetType() models.NodeType {
    return models.NodeTypeSlackSend
}

// Execute sends Slack message
func (e *SlackExecutor) Execute(ctx context.Context, node *models.Node, input json.RawMessage) (json.RawMessage, error) {
    // 1. Parse configuration
    var config models.SlackSendConfig
    if err := json.Unmarshal(node.Parameters, &config); err != nil {
        return nil, fmt.Errorf("invalid slack config: %w", err)
    }

    // 2. Build Slack API request
    payload := map[string]interface{}{
        "channel": config.Channel,
        "text":    config.Message,
    }

    // 3. Send request
    resp, err := e.sendSlackMessage(ctx, config.Token, payload)
    if err != nil {
        return nil, err
    }

    // 4. Return unified output
    return json.Marshal(map[string]interface{}{
        "json": map[string]interface{}{
            "success": true,
            "ts":      resp.Timestamp,
        },
        "metadata": map[string]interface{}{
            "_type":      "slack",
            "_timestamp": time.Now().UnixMilli(),
        },
    })
}

// Validate checks node configuration
func (e *SlackExecutor) Validate(node *models.Node) error {
    var config models.SlackSendConfig
    if err := json.Unmarshal(node.Parameters, &config); err != nil {
        return fmt.Errorf("invalid config: %w", err)
    }
    if config.Token == "" {
        return fmt.Errorf("slack token is required")
    }
    if config.Channel == "" {
        return fmt.Errorf("channel is required")
    }
    return nil
}

// GetDescription returns node metadata
func (e *SlackExecutor) GetDescription() models.NodeDescription {
    return models.NodeDescription{
        Type:        e.GetType(),
        DisplayName: "Slack Send",
        Description: "Send messages to Slack channels",
        Category:    "Communication",
        Icon:        "slack",
        Inputs: []models.ParameterDescription{
            {
                Name:        "token",
                Type:        "string",
                Required:    true,
                Description: "Slack Bot Token",
            },
            {
                Name:        "channel",
                Type:        "string",
                Required:    true,
                Description: "Channel ID or name",
            },
            {
                Name:        "message",
                Type:        "text",
                Required:    true,
                Description: "Message content",
            },
        },
        Outputs: []models.ParameterDescription{
            {
                Name:        "success",
                Type:        "boolean",
                Description: "Message sent successfully",
            },
            {
                Name:        "ts",
                Type:        "string",
                Description: "Message timestamp",
            },
        },
    }
}
```

**Step 2: Define Node Model**

```go
// File: features/workflow/models/workflow/node.go

// Add NodeType constant
const (
    // ... existing types
    NodeTypeSlackSend NodeType = "action.slack.send"
)

// Add Config struct
type SlackSendConfig struct {
    CommonInOutConfig `json:",inline"`
    Token             string `json:"token"`
    Channel           string `json:"channel"`
    Message           string `json:"message"`
    Attachments       []map[string]interface{} `json:"attachments,omitempty"`
}
```

**Step 3: Register Executor**

```go
// File: features/workflow/adapters/plugin_factory.go

func (f *PluginAdapterFactory) RegisterBuiltinExecutors(ctx context.Context) error {
    // ... existing registrations

    // Slack executor
    slackExec := actionCore.NewSlackExecutor()
    if err := f.RegisterExecutor(slackExec.GetType(), 1, slackExec); err != nil {
        logger.Warn("failed to register slack executor: %v", err)
    }

    // ... rest of registrations
    return nil
}
```

**Step 4: Create Frontend Component**

```typescript
// File: apps/frontend/src/workflow/features/properties/node-panels/SlackSendConfigPanel.tsx

import React from 'react';
import { Box, TextField, Typography } from '@mui/material';

interface SlackSendConfigPanelProps {
    nodeId: string;
    parameters: any;
    onParametersChange: (params: any) => void;
}

export const SlackSendConfigPanel: React.FC<SlackSendConfigPanelProps> = ({
    parameters,
    onParametersChange,
}) => {
    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
                Slack Configuration
            </Typography>

            <TextField
                fullWidth
                label="Bot Token"
                value={parameters.token || ''}
                onChange={(e) => onParametersChange({
                    ...parameters,
                    token: e.target.value,
                })}
                margin="normal"
                type="password"
            />

            <TextField
                fullWidth
                label="Channel"
                value={parameters.channel || ''}
                onChange={(e) => onParametersChange({
                    ...parameters,
                    channel: e.target.value,
                })}
                margin="normal"
                placeholder="#general or C1234567890"
            />

            <TextField
                fullWidth
                multiline
                rows={4}
                label="Message"
                value={parameters.message || ''}
                onChange={(e) => onParametersChange({
                    ...parameters,
                    message: e.target.value,
                })}
                margin="normal"
            />
        </Box>
    );
};

export default SlackSendConfigPanel;
```

**Step 5: Register Frontend Component**

```typescript
// File: apps/frontend/src/workflow/features/properties/node-panels/renderNodeConfig.tsx

import SlackSendConfigPanel from './SlackSendConfigPanel';

export const renderNodePanel = (nodeType: string, ...) => {
    switch (nodeType) {
        // ... existing cases
        
        case 'action.slack.send':
            return <SlackSendConfigPanel {...props} />;
        
        // ... rest of cases
    }
};
```

**Step 6: Build and Test**

```bash
# Backend
cd features/workflow/core/nodes/action
go test -v -run TestSlackExecutor

# Build
go build -o bin/server.exe .

# Frontend
cd apps/frontend
npx tsc --noEmit  # Check TypeScript errors
npm run dev       # Test in browser
```

---

#### 2. Enhancing an Existing Node

**Example: Adding n8n-style features to Code Node**

**Step 1: Analyze Current Implementation**

```bash
# View current code
cat features/workflow/core/nodes/core/code_executor.go

# Check model
cat features/workflow/models/workflow/node.go | grep -A 10 "CodeNodeConfig"
```

**Step 2: Update Model**

```go
// File: features/workflow/models/workflow/node.go

type CodeNodeConfig struct {
    CommonInOutConfig `json:",inline"`
    Language          string `json:"language"`
    Code              string `json:"code"`
    Mode              string `json:"mode"` // NEW: execution mode
    ContinueOnFail    bool   `json:"continue_on_fail,omitempty"` // NEW
    AlwaysOutputData  bool   `json:"always_output_data,omitempty"` // NEW
}
```

**Step 3: Create Helper Functions**

```go
// File: features/workflow/core/nodes/core/n8n_helpers.go

package workflow

// Built-in helper functions for n8n compatibility

func RegisterN8NHelpers(vm *goja.Runtime) {
    // Time helpers
    vm.Set("$now", func() time.Time {
        return time.Now()
    })
    
    // String helpers
    stringHelpers := map[string]interface{}{
        "toUpperCase": func(s string) string {
            return strings.ToUpper(s)
        },
        "toLowerCase": func(s string) string {
            return strings.ToLower(s)
        },
        // ... more helpers
    }
    vm.Set("$string", stringHelpers)
}
```

**Step 4: Enhance Executor**

```go
// File: features/workflow/core/nodes/core/code_executor.go

func (e *CodeExecutor) ExecuteWithData(ctx context.Context, node *models.Node, inputData *models.TaskDataConnections, execCtx *models.ExecuteData) (*models.NodeOutputData, error) {
    // Parse config
    var config models.CodeNodeConfig
    configBytes, _ := json.Marshal(node.Parameters)
    json.Unmarshal(configBytes, &config)

    // NEW: Handle execution modes
    if config.Mode == "run_once_for_all_items" {
        return e.executeAllItemsMode(ctx, config, inputData)
    }
    return e.executePerItemMode(ctx, config, inputData)
}

// NEW: Per-item execution
func (e *CodeExecutor) executePerItemMode(ctx context.Context, config models.CodeNodeConfig, inputData *models.TaskDataConnections) (*models.NodeOutputData, error) {
    // Execute code for each item
    // Inject $json variable
}

// NEW: All-items execution
func (e *CodeExecutor) executeAllItemsMode(ctx context.Context, config models.CodeNodeConfig, inputData *models.TaskDataConnections) (*models.NodeOutputData, error) {
    // Execute code once with all items
    // Inject $input.all(), $input.first(), $input.last()
}
```

**Step 5: Update Frontend**

```typescript
// File: apps/frontend/src/workflow/features/properties/node-panels/CodeNodeConfigPanel.tsx

// Add mode selector
<RadioGroup value={parameters.mode || 'run_once_for_each_item'}>
    <FormControlLabel 
        value="run_once_for_each_item"
        control={<Radio />}
        label="Run Once for Each Item"
    />
    <FormControlLabel 
        value="run_once_for_all_items"
        control={<Radio />}
        label="Run Once for All Items"
    />
</RadioGroup>
```

**Step 6: Update Plugin Version**

```go
// File: features/workflow/core/nodes/core/code_executor.go

func (e *CodeExecutor) GetMetadata() PluginMetadata {
    return PluginMetadata{
        ID:          "core.code",
        Name:        "Code Executor",
        Version:     Version{2, 0, 0}, // UPDATED from 1.0.0
        Description: "Execute JavaScript code with n8n-style helpers",
        // ...
    }
}
```

---

#### 3. Fixing Bugs in Existing Nodes

**Common Bug: Node Not Registered**

**Symptom:**
```json
{
    "error": "no executor found for node type: core.code",
    "success": false
}
```

**Solution:**

```go
// File: features/workflow/adapters/plugin_factory.go

func (f *PluginAdapterFactory) RegisterBuiltinExecutors(ctx context.Context) error {
    // ... existing code

    // ADD MISSING REGISTRATION
    codeExec := coreNodes.NewCodeExecutor()
    if err := f.RegisterExecutor(codeExec.GetType(), 1, codeExec); err != nil {
        logger.Warn("failed to register code executor: %v", err)
    }

    // ... rest of code
}
```

**Common Bug: Import Missing**

```go
// File: features/workflow/adapters/plugin_factory.go

import (
    // ... existing imports
    coreNodes "system_integration_management/features/workflow/core/nodes/core" // ADD THIS
)
```

**Common Bug: TypeScript Errors**

```bash
# Check errors
cd apps/frontend
npx tsc --noEmit

# Fix: Export component
// File: apps/frontend/src/workflow/features/properties/node-panels/index.ts
export { default as CodeNodeConfigPanel } from './CodeNodeConfigPanel';
```

---

#### 4. Testing Workflow

**Backend Tests:**

```go
// File: features/workflow/core/nodes/core/code_executor_test.go

func TestCodeExecutor_PerItemMode(t *testing.T) {
    executor := NewCodeExecutor()
    ctx := context.Background()

    node := &models.Node{
        ID:   "test-node",
        Type: models.NodeTypeCode,
        Parameters: map[string]interface{}{
            "language": "javascript",
            "mode":     "run_once_for_each_item",
            "code":     "return { result: $json.value * 2 };",
        },
    }

    inputData := &models.TaskDataConnections{
        Main: [][]models.NodeExecutionItem{
            {{JSON: map[string]any{"value": 5}, Index: 0}},
        },
    }

    result, err := executor.ExecuteWithData(ctx, node, inputData, nil)
    assert.NoError(t, err)
    assert.Equal(t, 10, result.Branches[0][0].JSON["result"])
}
```

**Run Tests:**

```bash
# Unit tests
go test -v ./features/workflow/core/nodes/core/...

# Integration test
go test -v -run TestWorkflowExecution ./features/workflow/core/execution/...

# Build
go build -o bin/server.exe .
```

**Frontend Testing:**

```bash
# TypeScript check
npx tsc --noEmit

# Run dev server
npm run dev

# Manual test in browser
# 1. Create workflow
# 2. Add node
# 3. Configure
# 4. Execute
# 5. Check output
```

---

#### 5. Deployment Checklist

**Before Deploying:**

- [ ] Backend build pass
- [ ] TypeScript compilation successful
- [ ] Node registered in plugin factory
- [ ] Frontend component exported

**Build Commands:**

```bash
# Backend
go build -o bin/server.exe .

# Frontend
cd apps/frontend
npm run build

# Restart server
./bin/server.exe
```

---

#### 6. Common Patterns

**Pattern: Credential Injection**

```go
func (e *HTTPExecutor) Execute(ctx context.Context, node *models.Node, input json.RawMessage) (json.RawMessage, error) {
    // Get credential service from context
    credService := GetCredentialService(ctx)
    
    // Resolve credential
    cred, err := credService.Get(ctx, config.CredentialID)
    if err != nil {
        return nil, err
    }
    
    // Use credential
    req.Header.Set("Authorization", "Bearer " + cred.Token)
}
```

**Pattern: Retry Logic**

```go
func (e *HTTPExecutor) executeWithRetry(req *http.Request, retryConfig *RetryConfig) (*http.Response, error) {
    var lastErr error
    for attempt := 0; attempt <= retryConfig.MaxRetries; attempt++ {
        resp, err := e.client.Do(req)
        if err == nil && resp.StatusCode < 500 {
            return resp, nil
        }
        lastErr = err
        time.Sleep(retryConfig.RetryDelay * time.Duration(attempt+1))
    }
    return nil, lastErr
}
```

**Pattern: Error Handling**

```go
func (e *NodeExecutor) Execute(ctx, node, input) (output, error) {
    // Wrap errors with context
    if err := validateConfig(node); err != nil {
        return nil, fmt.Errorf("config validation failed for node %s: %w", node.ID, err)
    }
    
    // Handle ContinueOnFail
    if config.ContinueOnFail {
        defer func() {
            if r := recover(); r != nil {
                logger.Error("Node %s panicked: %v", node.ID, r)
                output = buildErrorOutput(r)
            }
        }()
    }
}
```

---

**Reference Files:**
- Backend: `features/workflow/core/nodes/*/`
- Frontend: `apps/frontend/src/workflow/features/properties/node-panels/`
- Models: `features/workflow/models/workflow/node.go`
- Registry: `features/workflow/adapters/plugin_factory.go`

---

### 3. Authorization & Authentication

**Purpose:** SSO với Keycloak, RBAC, permission caching

**Location:** `features/authorization/`

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Auth Middleware                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Middleware()           # Full permission check         │ │
│  │ AuthOnly()             # Token validation only         │ │
│  │ CheckAuthOnlyWithout*  # Skip params check             │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                   Keycloak Service                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ KeycloakManager (Facade)                              │ │
│  │  - User management                                     │ │
│  │  - Role/permission management                          │ │
│  │  - Resource-based access control (UMA)                │ │
│  │  - Permission caching (Redis)                          │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    Adapter Layer                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ KeycloakAdapter (wraps Nerzal/gocloak)               │ │
│  │  - ClientPair pattern (shared underlying client)       │ │
│  │  - Narrow interfaces (single responsibility)           │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                      Storage Layer                           │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │ Redis        │  │ Keycloak Server                      │ │
│  │ (Cache)      │  │ (Identity Provider)                  │ │
│  └──────────────┘  └──────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

#### Permission Caching (3-Tier)

```
Request → Extract JWT → Check Expiration
                ↓
        ┌───────────────────────────────────┐
        │ TIER 1: Permission Decision Cache │
        │ Key: perm:user:{uid}:res:{res}:   │
        │      scope:{scope}                │
        │ Hit: 1-5ms ✅ FAST PATH           │
        └───────────┬───────────────────────┘
                    │ MISS
        ┌───────────┴───────────────────────┐
        │ TIER 2: Resources List Cache      │
        │ Key: resources:{clientID}         │
        │ Hit: 50-200ms                     │
        └───────────┬───────────────────────┘
                    │ MISS
        ┌───────────┴───────────────────────┐
        │ TIER 3: UMA Permission Check      │
        │ Call: GetRequestingPartyToken()   │
        │ Time: 300-500ms (most expensive)  │
        │ Cache result by name AND ID       │
        └───────────────────────────────────┘
```

#### Cache Invalidation

**Trigger Points:**
1. **NATS Event** (real-time from Keycloak SPI)
2. **Manual API** (resource/permission CRUD)

**Flow:**
```go
Keycloak Event → NATS → EventHandler
                            ↓
                  InvalidateAllRelatedCache()
                            ↓
                  ┌─────────┴──────────┐
                  │                    │
            perm:*                resources:*
                  │                    │
            deps:resource:*      deps:permission:*
```

**Key Methods:**
```go
// Cache permission decision
func (k *KeycloakManager) CachePermissionDecision(
    ctx context.Context, 
    userID, resourceName, scope string, 
    allowed bool, 
    ttlSeconds int,
) error

// Invalidate all related caches (comprehensive)
func (k *KeycloakManager) InvalidateAllRelatedCache(ctx context.Context) error

// Targeted invalidation for specific resource
func (k *KeycloakManager) InvalidatePermissionCacheForResource(
    ctx context.Context, 
    resourceName string,
) error
```

#### RBAC (Role-Based Access Control)

**Server-side Enforcement:**
```go
// Check if user has admin role
func hasAnyRealmRole(token string, roles []string) bool {
    claims := parseJWT(token)
    realmRoles := claims["realm_access"]["roles"]
    resourceAccess := claims["resource_access"]
    
    // Check both realm roles and client roles
    return hasRole(realmRoles, roles) || 
           hasRole(resourceAccess, roles)
}

// Example usage in controller
if config.Scope == "global" {
    if !hasAnyRealmRole(token, []string{"admin", "system-admin", "realm-admin"}) {
        return Forbidden("admin role required")
    }
}
```

**Client-side UI Controls:**
```javascript
// Hide features for non-admins
import { hasAnyRealmRole } from '../utils/jwt'

const isAdmin = hasAnyRealmRole(token, ['admin', 'system-admin', 'realm-admin'])

{isAdmin && (
  <Button>Create Global Integration</Button>
)}
```

**References:**
- Code: `features/authorization/services/`, `middleware/auth.go`

---

### 4. Multi-Tenancy System

**Purpose:** Tenant isolation cho backends, caching, workflows

**Location:** `features/tenant/`

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Tenant Middleware                          │
│  - Extract X-Tenant header or query param                   │
│  - Load tenant config from Redis (cached)                   │
│  - Inject tenant context                                    │
│  - Fallback to default tenant if missing                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                   Tenant Manager                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ TenantConfigProvider                                   │ │
│  │  - GetTenantConfig(tenantID)                           │ │
│  │  - CreateTenant, UpdateTenant, DeleteTenant            │ │
│  │  - ListTenants                                         │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                   Backend Manager                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ BackendConfigProvider                                  │ │
│  │  - GetBackendConfig(backendID)                         │ │
│  │  - CreateBackend, UpdateBackend, DeleteBackend         │ │
│  │  - ListBackendsByTenant(tenantID)                      │ │
│  │  - Dynamic route registration                          │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

#### Isolation Layers

**1. Cache Isolation:**
```
Cache Key Format:
  proxy:cache:cache:{tenant}:{hash}
  proxy:cache:resver:{tenant}:{type}:{id}
  proxy:cache:colver:{tenant}:{collection}
  proxy:cache:deps:collection:{tenant}:{collection}

Example:
  Tenant A: proxy:cache:cache:tenant-a:abc123
  Tenant B: proxy:cache:cache:tenant-b:abc123
  → Same hash, different keys, isolated
```

**2. Backend Scoping:**
```yaml
backends:
  - name: "api-service"
    base_url: "http://api.example.com"
    tenant_id: "tenant-a"        # Assigned to tenant A
    enabled: true

# Tenant A can access api-service
# Tenant B cannot (403 Forbidden)
```

**3. Workflow Isolation:**
```go
// All queries filter by tenant_id
func (r *WorkflowRepository) List(ctx, tenantID) {
    filter := bson.M{"tenant_id": tenantID}
    return collection.Find(ctx, filter)
}
```

#### Dynamic Route Registry

```go
type DynamicRouteRegistry interface {
    // Register routes for a backend
    RegisterBackendRoutes(ctx context.Context, backend *BackendConfig) error
    
    // Reload all routes from Redis
    ReloadRoutes(ctx context.Context) error
    
    // Unregister backend routes
    UnregisterBackendRoutes(backendName string) error
}

// Flow: Backend CRUD → ReloadRoutes() → Re-register Echo routes
```

#### Tenant Configuration Model

```go
type TenantConfig struct {
    TenantID    string            `json:"tenant_id"`
    TenantName  string            `json:"tenant_name"`
    BackendIDs  []string          `json:"backend_ids"`
    CachePrefix string            `json:"cache_prefix"`
    Status      string            `json:"status"`  // active, inactive
    Enabled     bool              `json:"enabled"`
    CreatedAt   time.Time         `json:"created_at"`
}
```

**References:**
- Code: `features/tenant/services/`, `middleware/tenant.go`

---

### 5. MinIO S3 Integration

**Purpose:** Object storage cho file uploads

**Location:** `features/s3/`

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     S3 Controller                            │
│  POST   /s3/api/v1/upload/:backend_name                     │
│  GET    /s3/api/v1/download/:backend/:object                │
│  DELETE /s3/api/v1/delete/:backend/:object                  │
│  GET    /s3/api/v1/list/:backend                            │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                     MinIO Service                            │
│  - UploadFile(backend, file) → presigned URL                │
│  - DownloadFile(backend, objectName)                        │
│  - DeleteFile(backend, objectName)                          │
│  - ListFiles(backend, prefix)                               │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    MinIO Adapter                             │
│  - Wraps minio-go/v7                                        │
│  - Per-backend bucket configuration                          │
│  - Auto-create bucket if not exists                         │
└───────────────────────────┬──────────────────────────────────┘
                            │
                     ┌──────┴───────┐
                     │ MinIO Server │
                     └──────────────┘
```

#### Configuration

```yaml
minio:
  endpoint: "minio-server:9000"
  access_key: "minioadmin"
  secret_key: "minioadmin"
  use_ssl: false
  max_file_size: 209715200        # 200MB per file
  max_files_per_upload: 30
  allowed_file_formats:
    - jpeg
    - jpg
    - png
    - pdf
    - xlsx
    - mp4
  
  bucket_configs:
    seafood:
      bucket_name: "seafood-bucket"
      access_key: "seafood-user"    # Per-backend credentials
      secret_key: "seafood-password"
    cultivation:
      bucket_name: "cultivation-bucket"
```

#### Usage

**Upload:**
```bash
curl -X POST \
  http://localhost:9000/s3/api/v1/upload/seafood \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

Response:
{
  "success": true,
  "object_name": "1732540800_document.pdf",
  "file_url": "http://minio:9000/seafood-bucket/1732540800_document.pdf?X-Amz-..."
}
```

**Download:**
```bash
curl -X GET \
  http://localhost:9000/s3/api/v1/download/seafood/1732540800_document.pdf \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded.pdf
```

**References:**
- Code: `features/s3/services/`, `adapters/minio/`

---

### 6. Superset Integration

**Purpose:** Embedded analytics dashboards

**Location:** `features/superset/`

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 Superset Controller                          │
│  GET    /superset/guest-token/:dashboard_id                 │
│  POST   /superset/embed-url                                 │
│  GET    /superset/dashboards                                │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                 Superset Service                             │
│  - GetGuestToken(dashboardID, rls) → JWT token              │
│  - GetEmbedURL(dashboardID, filters)                        │
│  - ListDashboards()                                         │
│  - Token caching (Redis)                                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                Superset Adapter                              │
│  - REST API client for Superset                             │
│  - Guest token generation                                   │
│  - Row-Level Security (RLS) injection                       │
└───────────────────────────┬──────────────────────────────────┘
                            │
                  ┌─────────┴──────────┐
                  │ Apache Superset    │
                  │ (Analytics Server) │
                  └────────────────────┘
```

#### Guest Token Flow

```
User Request → GetGuestToken(dashboardID, rls)
                    ↓
              Check Redis Cache
                    ↓
                MISS ↓
                    ↓
          Call Superset API: POST /security/guest_token/
              with RLS filters
                    ↓
          Receive JWT token (15 min expiry)
                    ↓
          Cache in Redis (TTL: 14 min)
                    ↓
          Return to frontend
                    ↓
    Frontend: Embed dashboard with token
```

**References:**
- Code: `features/superset/services/`, `adapters/superset/`

---

### 7. Management & Metrics

**Purpose:** System monitoring, metrics collection

**Location:** `features/management/`

#### Metrics Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 Metrics Middleware                           │
│  - Intercept every request                                  │
│  - Record: endpoint, tenant, status, latency                │
│  - Increment counters in Redis                              │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                 Metrics Service                              │
│  - GetMetricsSummary()                                      │
│  - GetTopEndpoints(limit)                                   │
│  - GetTenantStats()                                         │
│  - GetCacheStats()                                          │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                 Redis Storage                                │
│  Keys:                                                       │
│  - metrics:request:count:{tenant}:{endpoint}                │
│  - metrics:request:latency:{tenant}:{endpoint}              │
│  - metrics:cache:hits                                       │
│  - metrics:cache:misses                                     │
└──────────────────────────────────────────────────────────────┘
```

#### Collected Metrics

```go
type MetricsSummary struct {
    TotalRequests    int64
    TotalCacheHits   int64
    TotalCacheMisses int64
    CacheHitRate     float64
    TopEndpoints     []EndpointMetric
    TenantStats      []TenantMetric
}

type EndpointMetric struct {
    Endpoint     string
    RequestCount int64
    AvgLatency   float64
}
```

**API Endpoints:**
```
GET /_admin/api/v1/metrics/summary
GET /_admin/api/v1/metrics/top-endpoints
GET /_admin/api/v1/metrics/tenants
GET /_admin/api/v1/metrics/cache
```

**References:**
- Code: `features/management/services/`, `features/management/controllers/`

---

## Layer Architecture

### Request Flow (Top-Down)

```
┌────────────────────────────────────────────────────────────┐
│ 1. HTTP Request                                            │
│    - Method, Path, Headers, Body                           │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 2. Middleware Layer                                        │
│    ├─ CORS                                                 │
│    ├─ Auth (JWT validation)                                │
│    ├─ Tenant (extract tenant context)                      │
│    ├─ Rate Limit (per tenant/endpoint/user)                │
│    └─ Metrics (record counters)                            │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 3. Router Layer (Echo)                                     │
│    - Match route to handler                                │
│    - Execute controller method                             │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 4. Controller Layer                                        │
│    - Parse request (bind, validate)                        │
│    - Call service methods                                  │
│    - Format response                                       │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 5. Service Layer (Business Logic)                         │
│    - Implement domain logic                                │
│    - Orchestrate operations                                │
│    - Call repositories                                     │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 6. Repository Layer (Data Access)                         │
│    - Query databases                                       │
│    - Cache management                                      │
│    - Data transformation                                   │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 7. Adapter Layer (External Integration)                   │
│    - Wrap third-party libraries                            │
│    - Implement service interfaces                          │
│    - Isolate dependencies                                  │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────┐
│ 8. Storage Layer                                           │
│    - Redis, MongoDB, PostgreSQL                            │
│    - MinIO, Keycloak                                       │
└────────────────────────────────────────────────────────────┘
```

### Dependency Direction

```
Controllers → Services → Repositories → Adapters → External Systems
     ↓            ↓           ↓            ↓
  Models      Models      Models       Models
     ↓            ↓           ↓            ↓
 Interfaces  Interfaces  Interfaces   Interfaces

Rule: Upper layers depend on lower layers via INTERFACES, never concrete types
```

---

## Database & Storage

### Redis (Cluster Mode)

**Purpose:** Caching, session, state management

**Schema:**

```
# Proxy Cache
proxy:cache:cache:{tenant}:{hash} → binary (response)
proxy:cache:resver:{tenant}:{type}:{id} → int (version)
proxy:cache:colver:{tenant}:{collection} → int (version)
proxy:cache:deps:collection:{tenant}:{collection} → Set (cache keys)

# Proxy Configuration
proxy:invalidations:entries:{tenant}:{backend} → JSON (rules array)
backend:config:{backend_id} → JSON (backend config)
backend:list → Set (backend IDs)

# Tenant Configuration
tenant:config:{tenant_id} → JSON (tenant config)
tenant:list → Set (tenant IDs)

# Permission Cache
perm:user:{uid}:res:{res}:scope:{scope} → "1" or "0"
resources:{clientID} → JSON (resources array)
deps:resource:{resourceName} → Set (permission keys)

# Metrics
metrics:request:count:{tenant}:{endpoint} → int
metrics:request:latency:{tenant}:{endpoint} → float
metrics:cache:hits → int
metrics:cache:misses → int

# Workflow State
workflow:exec:{execution_id}:context → JSON (execution state)
workflow:exec:{execution_id}:node:{node_id}:output → JSON
workflow:exec:{execution_id}:variables → Hash

# Rate Limiting
rate_limit:{tenant}:{endpoint}:{user}:{ip}:{window} → int
```

### MongoDB

**Purpose:** Workflow persistence, metadata

**Collections:**

```javascript
// Workflows
{
  _id: "wf-123",
  name: "Order Processing",
  status: "active",
  nodes: [
    {
      _id: "node-1",
      type: "trigger.webhook",
      parameters: {...}
    }
  ],
  connections: [...],
  tenant_id: "tenant-a",
  created_at: ISODate(...)
}

// Executions
{
  _id: "exec-456",
  workflow_id: "wf-123",
  status: "completed",
  trigger_data: {...},
  node_states: {
    "node-1": {
      status: "completed",
      output: {...}
    }
  },
  start_time: ISODate(...),
  end_time: ISODate(...)
}

// Workspaces/Folders
{
  _id: "folder-789",
  name: "Production Workflows",
  parent_id: null,
  tenant_id: "tenant-a",
  workflows: ["wf-123", ...]
}
```

### PostgreSQL (Optional)

**Purpose:** Structured data, relational queries

**Tables:**
- Users (if not using Keycloak as primary)
- Audit logs
- Metadata entities (Phase 4)

### MinIO

**Purpose:** Object storage

**Bucket Structure:**
```
/{backend-name}/
  ├── {timestamp}_{filename1}.pdf
  ├── {timestamp}_{filename2}.jpg
  └── ...
```

---

## API Architecture

### API Versioning

```
Current: v1
Path: /_admin/api/v1/...

Future: v2 (Workflow API v2.0 in progress)
Path: /api/v2/...
```

### API Groups

```
/_admin/api/v1/
  ├── metrics/              # System metrics
  ├── proxy/                # Proxy cache management
  ├── tenants/              # Tenant CRUD
  │   └── backends/         # Backend CRUD
  ├── workflows/            # Workflow CRUD
  │   ├── executions/       # Execution monitoring
  │   ├── schedules/        # Schedule management
  │   └── webhooks/         # Webhook management
  ├── keycloak/             # Keycloak admin
  ├── superset/             # Superset integration
  └── s3/                   # File upload

/webhook/:path              # Public webhook triggers

/api/v2/                    # Workflow API v2.0
  ├── workflows/
  ├── executions/
  └── ws                    # WebSocket API
```

### Request/Response Format

**Standard Success:**
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed"
}
```

**Standard Error:**
```json
{
  "error": "Resource not found",
  "code": "ERR_NOT_FOUND",
  "details": "Workflow ID wf-123 does not exist"
}
```

### Authentication

**Bearer Token (JWT):**
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Claims:**
```json
{
  "sub": "user-id-123",
  "exp": 1736697600,
  "realm_access": {
    "roles": ["admin", "user"]
  },
  "resource_access": {
    "my-client": {
      "roles": ["workflow-admin"]
    }
  }
}
```

---

## Security Architecture

### Authentication Flow

```
User Login
    ↓
Keycloak SSO
    ↓
Generate JWT token
    ↓
Client stores token (localStorage)
    ↓
Every request includes: Authorization: Bearer {token}
    ↓
Auth Middleware:
  ├─ Parse JWT (unverified)
  ├─ Check expiration
  ├─ Extract claims (sub, roles)
  ├─ Validate signature (Keycloak public key)
  ├─ Check permissions (UMA if needed)
  └─ Inject user context
    ↓
Controller processes request
```

### Permission Layers

**Level 1: Route-level Auth**
```go
// Require authentication
route.Use(authMw.Middleware)

// Auth only (no permission check)
route.Use(authMw.AuthOnly)

// No auth
// (no middleware)
```

**Level 2: Role-based Auth (RBAC)**
```go
if !hasAnyRealmRole(token, []string{"admin"}) {
    return Forbidden
}
```

**Level 3: Resource-based Auth (UMA)**
```go
ok, err := kcMgr.CheckPermissionForResourceScope(
    ctx, 
    userToken, 
    "/api/v1/workflows", 
    "read",
)
```

### Tenant Isolation

**1. Request Level:**
- X-Tenant header → middleware → context

**2. Data Level:**
- All queries filter by tenant_id
- Cache keys include tenant

**3. Backend Level:**
- Backends assigned to tenants
- Unauthorized tenant → 403

---

## Performance & Scalability

### Caching Strategy

**L1 (In-Memory):** Not implemented (planned Phase 4.1)

**L2 (Redis):**
- Proxy cache: 60s TTL (configurable)
- Permission cache: 60s TTL
- Resource cache: 5min TTL
- Token cache: 14min TTL (Superset)

**L3 (Source):**
- Backend APIs
- Keycloak
- MongoDB

### Concurrency

**Goroutines:**
- Workflow execution per request
- Swagger fetching (parallel)
- Background workers (scheduler, queue)

**Connection Pools:**
- Redis: 50 pool size (configurable)
- MongoDB: Default driver pool
- HTTP clients: Per-integration pools

### Horizontal Scaling

**Stateless Components:**
- Controllers
- Services
- Middleware

**Stateful Components:**
- Redis (Cluster mode)
- MongoDB (Replica Set)

**Load Balancing:**
- Multiple instances behind load balancer
- Session affinity not required

---

## Development Guidelines

### Code Organization

```
features/{feature}/
  ├── adapters/       # External library wrappers
  ├── controllers/    # HTTP handlers
  ├── models/         # Domain entities
  ├── repositories/   # Data access
  ├── routers/        # Route definitions
  └── services/       # Business logic
```

### Naming Conventions

**Interfaces:**
```go
type WorkflowService interface {...}      // Service interface
type WorkflowRepository interface {...}   // Repository interface
type HTTPClient interface {...}           // Client interface
```

**Implementations:**
```go
type workflowServiceImpl struct {...}     # Private implementation
type workflowRepositoryImpl struct {...}  # Private implementation
```

**Constructors:**
```go
func NewWorkflowService(...) WorkflowService  # Returns interface
```

### Error Handling

**Service Layer:**
```go
return nil, fmt.Errorf("failed to create workflow: %w", err)
```

**Controller Layer:**
```go
if err != nil {
    return ctx.JSON(http.StatusInternalServerError, map[string]any{
        "error": "Failed to create workflow",
        "details": err.Error(),
        "code": apierrors.ErrInternal,
    })
}
```

### Testing

**Unit Tests:**
```bash
go test ./features/workflow/services/...
```

**Integration Tests:**
```bash
go test -tags=integration ./features/workflow/...
```

### Logging

```go
import logger "system_integration_management/utils/logging"

logger.Info("Workflow created: id=%s, name=%s", wf.ID, wf.Name)
logger.Error("Failed to execute workflow: %v", err)
logger.Debug("[cache] cache key: %s", cacheKey)
```

### Configuration

**Environment Variables:**
```bash
export LOCATION_CONF=config/config.yaml
```

**Config Structure:**
```yaml
listen: "0.0.0.0:9000"
redis:
  addresses: ["localhost:6379"]
mongodb:
  uri: "mongodb://localhost:27017"
keycloak:
  base_url: "http://keycloak:8080"
```

---

## References

### Documentation

- **[FE_DESIGN_PATTERN.md](./docs/FE_DESIGN_PATTERN.md)** - Frontend architecture patterns
- **[WORKFLOW_UNIFIED_FORMAT_SOLUTION.md](./docs/WORKFLOW_UNIFIED_FORMAT_SOLUTION.md)** - Workflow unified format
- **[RELEASE_NOTES.md](./RELEASE_NOTES.md)** - Version history

### Code Entry Points

- **Main:** [main.go](./main.go)
- **Router:** [routers/router.go](./routers/router.go)
- **DI Container:** [routers/constant.go](./routers/constant.go)
- **Config:** [config/config.go](./config/config.go)

### Key Directories

- **Backend:** `features/`, `lib/`, `middleware/`, `utils/`
- **Frontend:** `apps/frontend/src/`
- **Config:** `config/`
- **Docs:** `docs/`

---

**End of Architecture Documentation**

> This document serves as the primary reference for AI Agents and developers working on the System Integration Management platform. For module-specific details, refer to the linked documentation in each section.
