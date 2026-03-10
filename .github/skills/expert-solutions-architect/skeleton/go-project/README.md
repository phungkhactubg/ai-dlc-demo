# {{.ProjectName}}

## Getting Started

### Prerequisites
- Go 1.25+
- Docker & Docker Compose
- MongoDB
- Redis

### Setup

```bash
# Install dependencies
go mod tidy

# Start services
docker-compose up -d

# Run application
go run main.go
```

### API

- Health Check: `GET /health`
- Readiness: `GET /ready`

### Project Structure

```
{{.ProjectName}}/
├── config/         # Configuration
├── middleware/     # HTTP middleware
├── routers/        # Route definitions
├── utils/          # Utilities
├── lib/            # Driver libraries
│   ├── mongodb/
│   ├── redis/
│   ├── nats/
│   ├── kafka/
│   ├── mqtt/
│   ├── s3/
│   └── postgres/
├── features/       # Feature modules
└── main.go         # Entry point
```

### Development

```bash
# Run with hot reload (install air first)
air

# Build
go build -o bin/{{.ProjectName}} .
```
