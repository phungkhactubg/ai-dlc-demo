import sys
import io
from datetime import datetime
import argparse

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

TEMPLATE = """# [{FEATURE_NAME}] - Implementation Plan & Architecture Spec

## 1. Executive Summary
*   **Objective**: {OBJECTIVE}
*   **Scope**: {SCOPE}
*   **Date**: {DATE}

## 2. Technical Architecture

### 2.1 Backend Design (Go)
*   **Module**: `features/{FEATURE_SLUG}`
*   **Directory Structure**:
    ```
    features/{FEATURE_SLUG}/
    ├── models/           # Domain entities + DTOs
    ├── services/         # Business logic (interface + impl)
    ├── repositories/     # Data access (interface + impl)
    ├── controllers/      # HTTP handlers
    ├── routers/          # Route registration
    └── adapters/         # External service wrappers
    ```

*   **Core Interfaces**:
    ```go
    // features/{FEATURE_SLUG}/services/service.go
    type IService interface {{
        Create(ctx context.Context, req CreateRequest) (*{FEATURE_CAMEL}, error)
        GetByID(ctx context.Context, id string) (*{FEATURE_CAMEL}, error)
        // Add methods...
    }}
    ```

### 2.2 Frontend Design (React)
*   **Feature Slice**: `apps/frontend/src/{FEATURE_SLUG}/`
*   **Directory Structure**:
    ```
    apps/frontend/src/{FEATURE_SLUG}/
    ├── core/
    │   ├── models/       # Zod schemas (MUST match BE exactly)
    │   ├── interfaces/   # Service contracts
    │   └── constants/    # Feature constants
    ├── infrastructure/
    │   ├── api/          # Axios API functions
    │   ├── stores/       # Zustand stores
    │   └── services/     # Service implementations
    ├── shared/
    │   ├── components/   # Shared UI components
    │   └── hooks/        # Custom hooks
    └── features/         # Sub-features
    ```

## 3. Data Dictionary (Source of Truth)

### 3.1 Database Models (MongoDB)
*   **Collection**: `{FEATURE_SLUG}`
*   **Schema**:
    ```go
    // features/{FEATURE_SLUG}/models/entity.go
    type {FEATURE_CAMEL} struct {{
        ID        string    `bson:"_id" json:"id"`
        TenantID  string    `bson:"tenant_id" json:"tenant_id"`
        Name      string    `bson:"name" json:"name"`
        CreatedAt time.Time `bson:"created_at" json:"created_at"`
        // Add fields...
    }}
    ```

### 3.2 API Contracts (Contract-First)
*   **Endpoint**: `POST /api/v1/{FEATURE_SLUG}`
*   **Go Request Struct**:
    ```go
    type CreateRequest struct {{
        Name string `json:"name" validate:"required,min=1"`
    }}
    ```
*   **Zod Schema (Frontend)**:
    ```typescript
    export const CreateRequestSchema = z.object({{
        name: z.string().min(1)
    }});
    ```

## 4. Implementation Steps (Mandatory Scripts)

### Phase 1: Backend Core (Go Developer)
1. [ ] **Scaffold Feature**
   - **Command**: `python .github/skills/expert-go-backend-developer/scripts/scaffold_feature.py {FEATURE_SLUG}`
   - Result: Created feature directory structure.

2. [ ] **Create Domain Models** (`models/`)
   - Define `Entity` struct with BSON/JSON tags
   - Define DTOs (Request/Response)

3. [ ] **Create Repository** (`repositories/`)
   - Implement MongoDB repository with TenantID filtering

4. [ ] **Create Service** (`services/`)
   - Implement business logic and error handling

5. [ ] **Create Controller** (`controllers/`)
   - Implement HTTP handlers and input validation

6. [ ] **Wire DI**
   - **Command**: `python .github/skills/expert-go-backend-developer/scripts/generate_di_wiring.py {FEATURE_SLUG}`
   - Action: Update `routers/constant.go`

7. [ ] **Verify**
   - **Command**: `python .github/skills/expert-go-backend-developer/scripts/validate_production_ready.py features/{FEATURE_SLUG}`
   - **Command**: `go build ./...`

### Phase 2: Frontend Foundation (React Developer)
1. [ ] **Scaffold Feature**
   - **Command**: `python .github/skills/expert-react-frontend-developer/scripts/scaffold_feature.py {FEATURE_SLUG} --path apps/frontend/src`

2. [ ] **Generate Zod Schemas**
   - **Command**: `python .github/skills/expert-react-frontend-developer/scripts/extract_go_api.py features/{FEATURE_SLUG}/controllers --format zod`
   - Action: Verify field names match exactly.

3. [ ] **Create API Functions** (`infrastructure/api/`)
   - Implement Axios wrappers

4. [ ] **Create Zustand Store** (`infrastructure/stores/`)
   - Implement state management using slices

5. [ ] **Verify**
   - **Command**: `python .github/skills/expert-react-frontend-developer/scripts/validate_frontend_architecture.py apps/frontend/src/{FEATURE_SLUG}`
   - **Command**: `npx tsc --noEmit`

### Phase 3: Integration
1. [ ] **Build Components** (`shared/components/`)
2. [ ] **Connect UI to Store**
3. [ ] **Manual Verification**
    - [ ] Happy Patch
    - [ ] Error Cases

## 5. Verification Checklist
- [ ] Backend: `validate_production_ready.py` passed?
- [ ] Backend: Code builds without errors?
- [ ] Frontend: `validate_frontend_architecture.py` passed?
- [ ] Frontend: `tsc` passed?
- [ ] Integration: UI handles all API fields correctly?
"""

def to_camel_case(snake_str):
    components = snake_str.split('-')
    return ''.join(x.title() for x in components)

def main():
    parser = argparse.ArgumentParser(description="Generate an Implementation Plan Template")
    parser.add_argument("feature_name", help="Name of the feature")
    parser.add_argument("--objective", default="[Objective]", help="Objective of the feature")
    parser.add_argument("--scope", default="[Scope]", help="Scope of the feature")
    
    args = parser.parse_args()
    
    slug = args.feature_name.lower().replace(" ", "-")
    camel = to_camel_case(slug)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(TEMPLATE.format(
        FEATURE_NAME=args.feature_name,
        FEATURE_SLUG=slug,
        FEATURE_CAMEL=camel,
        OBJECTIVE=args.objective,
        SCOPE=args.scope,
        DATE=date_str
    ))

if __name__ == "__main__":
    main()
