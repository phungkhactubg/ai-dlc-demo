#!/usr/bin/env python3
"""
Architecture Diagram Generator
==============================

Generate Mermaid diagrams for common architecture patterns.

Usage:
    python generate_architecture.py --type component --name UserManagement
    python generate_architecture.py --type sequence --name CreateUser
    python generate_architecture.py --type clean --feature orders
"""

import argparse
import os
import sys
import io
from datetime import datetime

# Fix for Windows console encoding issues
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def generate_component_diagram(name: str, components: list = None) -> str:
    """Generate a component diagram."""
    components = components or ["Service", "Repository", "Controller"]
    
    diagram = f"""```mermaid
graph TB
    subgraph "{name} Module"
        subgraph "Presentation Layer"
            CTRL[Controller]
        end
        
        subgraph "Business Layer"
            SVC[Service]
            VAL[Validator]
        end
        
        subgraph "Data Layer"
            REPO[Repository]
            CACHE[Cache Adapter]
        end
    end
    
    subgraph "External"
        DB[(MongoDB)]
        REDIS[(Redis)]
    end
    
    CTRL --> SVC
    SVC --> VAL
    SVC --> REPO
    SVC --> CACHE
    REPO --> DB
    CACHE --> REDIS
```"""
    return diagram


def generate_sequence_diagram(operation: str) -> str:
    """Generate a sequence diagram for CRUD operation."""
    diagram = f"""```mermaid
sequenceDiagram
    participant Client
    participant Controller
    participant Service
    participant Repository
    participant MongoDB
    
    Client->>Controller: POST /api/v1/{operation.lower()}
    Controller->>Controller: Validate Request
    Controller->>Service: Create(ctx, request)
    Service->>Service: Business Validation
    Service->>Repository: Save(ctx, entity)
    Repository->>MongoDB: InsertOne()
    MongoDB-->>Repository: Result
    Repository-->>Service: Entity
    Service-->>Controller: Entity
    Controller-->>Client: 201 Created
```"""
    return diagram


def generate_clean_architecture(feature: str) -> str:
    """Generate Clean Architecture diagram."""
    diagram = f"""```mermaid
graph TB
    subgraph "features/{feature}"
        subgraph "Controllers"
            HTTP[HTTP Controller]
        end
        
        subgraph "Services"
            IF_SVC[["I{feature.title()}Service"]]
            SVC_IMPL[{feature}ServiceImpl]
        end
        
        subgraph "Repositories"
            IF_REPO[["I{feature.title()}Repository"]]
            REPO_IMPL[MongoRepository]
        end
        
        subgraph "Models"
            ENT[Entity]
            DTO_REQ[Request DTOs]
            DTO_RES[Response DTOs]
            ERR[Domain Errors]
        end
    end
    
    HTTP --> IF_SVC
    IF_SVC -.-> SVC_IMPL
    SVC_IMPL --> IF_REPO
    IF_REPO -.-> REPO_IMPL
    SVC_IMPL --> ENT
    HTTP --> DTO_REQ
    HTTP --> DTO_RES
    SVC_IMPL --> ERR
```

### Key Principles:

1. **Dependency Rule**: Dependencies point inward only
2. **Interface First**: Services depend on repository *interfaces*
3. **DTOs at Boundary**: Request/Response DTOs at controller layer
4. **Domain Errors**: Custom errors defined in models"""
    return diagram


def generate_hexagonal_architecture(feature: str) -> str:
    """Generate Hexagonal Architecture diagram."""
    diagram = f"""```mermaid
graph LR
    subgraph "Primary Adapters (Driving)"
        HTTP[HTTP API]
        GRPC[gRPC API]
        CLI[CLI]
    end
    
    subgraph "Application Core"
        subgraph "Ports"
            PIN[Input Port]
            POUT[Output Port]
        end
        
        subgraph "Domain"
            SVC[{feature.title()} Service]
            ENT[Domain Entities]
        end
    end
    
    subgraph "Secondary Adapters (Driven)"
        MONGO[MongoDB Adapter]
        REDIS[Redis Adapter]
        NATS[NATS Adapter]
    end
    
    HTTP --> PIN
    GRPC --> PIN
    CLI --> PIN
    PIN --> SVC
    SVC --> ENT
    SVC --> POUT
    POUT --> MONGO
    POUT --> REDIS
    POUT --> NATS
```"""
    return diagram


def generate_event_driven_diagram(feature: str) -> str:
    """Generate Event-Driven Architecture diagram."""
    diagram = f"""```mermaid
graph LR
    subgraph "Command Side"
        CMD[Command Handler]
        AGG[Aggregate]
        ES[(Event Store)]
    end
    
    subgraph "Event Bus"
        NATS{{NATS JetStream}}
    end
    
    subgraph "Query Side"
        PROJ[Projection Handler]
        READ[(Read Model)]
    end
    
    subgraph "Subscribers"
        NOTIF[Notification Service]
        AUDIT[Audit Logger]
    end
    
    CMD --> AGG
    AGG --> ES
    ES --> NATS
    NATS --> PROJ
    NATS --> NOTIF
    NATS --> AUDIT
    PROJ --> READ
```

### Events for {feature.title()}:

| Event | Trigger | Data |
|-------|---------|------|
| `{feature.title()}Created` | Create operation | Entity ID, Tenant ID |
| `{feature.title()}Updated` | Update operation | Entity ID, Changes |
| `{feature.title()}Deleted` | Delete operation | Entity ID |"""
    return diagram


def generate_data_flow_diagram(feature: str) -> str:
    """Generate data flow diagram."""
    diagram = f"""```mermaid
flowchart TD
    A[Client Request] --> B{{Auth Middleware}}
    B -->|Invalid| C[401 Unauthorized]
    B -->|Valid| D{{Tenant Middleware}}
    D --> E[Controller]
    E --> F{{Validate Input}}
    F -->|Invalid| G[400 Bad Request]
    F -->|Valid| H[Service Layer]
    H --> I{{Business Rules}}
    I -->|Violation| J[422 Unprocessable]
    I -->|Pass| K[Repository]
    K --> L[(Database)]
    L -->|Success| M[Transform Response]
    L -->|Error| N[500 Internal Error]
    M --> O[200 OK Response]
```"""
    return diagram


def generate_deployment_diagram() -> str:
    """Generate deployment diagram."""
    diagram = """```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress"
            NG[NGINX Ingress]
        end
        
        subgraph "Services"
            API1[API Pod 1]
            API2[API Pod 2]
            API3[API Pod 3]
        end
        
        subgraph "Data Layer"
            MONGO[(MongoDB)]
            REDIS[(Redis Cluster)]
        end
        
        subgraph "Messaging"
            NATS[NATS Cluster]
        end
    end
    
    subgraph "External"
        CDN[CDN / Load Balancer]
        S3[(S3 / MinIO)]
    end
    
    CDN --> NG
    NG --> API1
    NG --> API2
    NG --> API3
    API1 --> MONGO
    API2 --> REDIS
    API3 --> NATS
    API1 --> S3
```"""
    return diagram


def save_diagram(content: str, output_path: str):
    """Save diagram to file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Architecture Diagram\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(content)
    print(f"✅ Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid architecture diagrams"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["component", "sequence", "clean", "hexagonal", "event", "dataflow", "deployment"],
        required=True,
        help="Type of diagram to generate"
    )
    parser.add_argument(
        "--name", "-n",
        default="Feature",
        help="Name of the feature/operation"
    )
    parser.add_argument(
        "--feature", "-f",
        default="example",
        help="Feature name for architecture diagrams"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (optional, prints to stdout if not specified)"
    )
    
    args = parser.parse_args()
    
    # Generate diagram based on type
    if args.type == "component":
        diagram = generate_component_diagram(args.name)
    elif args.type == "sequence":
        diagram = generate_sequence_diagram(args.name)
    elif args.type == "clean":
        diagram = generate_clean_architecture(args.feature)
    elif args.type == "hexagonal":
        diagram = generate_hexagonal_architecture(args.feature)
    elif args.type == "event":
        diagram = generate_event_driven_diagram(args.feature)
    elif args.type == "dataflow":
        diagram = generate_data_flow_diagram(args.feature)
    elif args.type == "deployment":
        diagram = generate_deployment_diagram()
    else:
        print(f"Unknown diagram type: {args.type}")
        return
    
    # Output
    output_path = args.output
    if not output_path:
        # Standardized Output Path
        safe_name = args.name.lower().replace(" ", "_")
        if args.feature and args.feature != "example":
            safe_name = args.feature.lower().replace(" ", "_")
        
        output_dir = Path("project-documentation/architecture")
        output_path = output_dir / f"{safe_name}_{args.type}.md"

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        save_diagram(diagram, str(output_path))
    else:
        print(diagram)


if __name__ == "__main__":
    main()
