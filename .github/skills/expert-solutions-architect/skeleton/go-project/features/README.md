# Features Directory

This directory contains feature modules following Clean Architecture.

## Structure

Each feature follows this structure:

```
features/<feature>/
├── models/
│   ├── entity.go       # Domain entity
│   ├── request.go      # Input DTOs
│   ├── response.go     # Output DTOs
│   └── errors.go       # Domain errors
├── services/
│   ├── interface.go    # Service interface (contract)
│   └── service_impl.go # Business logic implementation
├── repositories/
│   ├── interface.go    # Repository interface
│   └── mongo_repository.go # MongoDB implementation
├── controllers/
│   └── http_controller.go  # HTTP handlers
├── adapters/           # Optional: external service wrappers
│   └── external.go
└── routers/
    └── router.go       # Route registration
```

## Available Features

| Feature | Description | Status |
|---------|-------------|--------|
| `health` | Health check endpoints (liveness, readiness) | ✅ Ready |
| `_template_` | CRUD template for new features | 📝 Template |

## Creating a New Feature

### Option 1: Use the scaffold script

```bash
python .github/skills/go-project-generator/scripts/generate_feature.py users
```

### Option 2: Copy the template

1. Copy `_template_` directory:
   ```bash
   cp -r features/_template_ features/your_feature
   ```

2. Rename package in all files:
   - Replace `_template_` with `your_feature`

3. Customize:
   - Rename `Entity` to your domain entity (e.g., `User`)
   - Update collection name in repository
   - Update route paths in router

## Feature Layers

### Models Layer
- **Purpose**: Define domain entities and DTOs
- **Dependencies**: None (pure Go)
- **Contains**: Entities, Request DTOs, Response DTOs, Errors

### Services Layer
- **Purpose**: Business logic
- **Dependencies**: Repository interfaces (not implementations)
- **Contains**: Service interface + implementation

### Repositories Layer
- **Purpose**: Data access
- **Dependencies**: Database drivers, domain models
- **Contains**: Repository interface + implementations

### Controllers Layer
- **Purpose**: HTTP handling
- **Dependencies**: Service interfaces
- **Contains**: HTTP handlers, request validation

### Routers Layer
- **Purpose**: Route registration
- **Dependencies**: Echo, controllers
- **Contains**: Route definitions

## Dependency Flow

```
Controller → Service Interface → Repository Interface
     ↓              ↓                    ↓
  (impl)         (impl)              (impl)
     ↓              ↓                    ↓
  Echo        Business Logic        MongoDB
```

## Wiring Dependencies

In `routers/constant.go`:

```go
// Create repository
repo := yourfeature.NewMongoRepository(deps.MongoDB.Database())

// Create service
service := yourfeature.NewEntityService(repo)

// Create controller
controller := yourfeature.NewEntityController(service)

// Register routes
yourfeature.RegisterRoutes(v1, controller)
```
