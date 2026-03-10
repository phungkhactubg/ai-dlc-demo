# Skeleton Templates

Ready-to-use architecture document templates for Solutions Architects.

## Available Templates

| Template | Purpose | When to Use |
|----------|---------|-------------|
| [TECHNICAL_SPEC.md](./TECHNICAL_SPEC.md) | Complete technical specification | Full feature documentation |
| [API_CONTRACT.md](./API_CONTRACT.md) | REST API contract | API design and documentation |
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | Database schema design | Data modeling |
| [SECURITY_REVIEW.md](./SECURITY_REVIEW.md) | Security checklist | Security reviews |
| [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) | High-level system design | New systems/major features |

## Template Contents

### TECHNICAL_SPEC.md
Complete feature specification including:
- Executive summary with scope and success criteria
- Architecture design with diagrams
- Data models with Go structs
- API contracts with all endpoints
- Use cases and edge cases
- Implementation steps
- Security and testing considerations

### API_CONTRACT.md
REST API contract including:
- Common headers and authentication
- Standard response formats
- Error codes reference
- CRUD endpoint templates
- Request/response examples
- Go struct and Zod schema examples
- Validation rules mapping

### DATABASE_SCHEMA.md
Database schema design including:
- Schema overview with ER diagram
- Field definitions with types
- Index specifications
- Go struct definitions
- Migration scripts (MongoDB/PostgreSQL)
- Query patterns and examples
- Data integrity rules

### SECURITY_REVIEW.md
Comprehensive security checklist covering:
- Authentication & authorization
- Input validation & sanitization
- Data protection
- API security
- Infrastructure security
- Third-party dependencies
- Business logic security

### SYSTEM_DESIGN.md
High-level system architecture including:
- System context and actors
- Architecture diagrams
- Component responsibilities
- Data design and storage
- API design standards
- Security design
- Reliability & scalability
- Trade-offs and decisions
- Implementation phases

## How to Use

1. **Copy Template**: Copy the appropriate template to your project/docs directory
2. **Fill Sections**: Replace placeholders with actual content
3. **Validate**: Run validation scripts to check completeness
   ```bash
   python scripts/validate_plan.py your_spec.md --strict
   ```
4. **Review**: Share with team for feedback
5. **Update**: Keep updated as design evolves
