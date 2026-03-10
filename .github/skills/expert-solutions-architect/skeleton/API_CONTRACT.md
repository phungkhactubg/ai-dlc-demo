# API Contract Template

> REST API contract specification following OpenAPI principles

# [Feature Name] - API Contract

**Version:** 1.0.0
**Base URL:** `/api/v1`
**Format:** JSON
**Authentication:** Bearer JWT

---

## Common Headers

### Request Headers
| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer <jwt_token>` |
| `X-Tenant-ID` | Yes | Tenant identifier |
| `X-Request-ID` | No | Request tracking ID |
| `Content-Type` | Yes* | `application/json` (* for POST/PUT/PATCH) |

### Response Headers
| Header | Description |
|--------|-------------|
| `X-Request-ID` | Echo of request ID |
| `X-Response-Time` | Processing time in ms |

---

## Standard Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

---

## Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `BAD_REQUEST` | Invalid request syntax |
| 400 | `VALIDATION_ERROR` | Input validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 401 | `TOKEN_EXPIRED` | JWT token expired |
| 403 | `FORBIDDEN` | Access denied |
| 403 | `TENANT_MISMATCH` | Resource belongs to different tenant |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource conflict (duplicate) |
| 422 | `UNPROCESSABLE` | Business rule violation |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## Endpoints

### POST /<resource>

**Description:** Create a new resource

**Request:**
```http
POST /api/v1/<resource>
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
Content-Type: application/json

{
  "name": "string (required, 1-100 chars)",
  "description": "string (optional, max 500 chars)",
  "type": "string (required, enum: typeA|typeB)",
  "settings": {
    "key": "value"
  }
}
```

**Go Request Struct:**
```go
type CreateResourceRequest struct {
    Name        string         `json:"name" validate:"required,min=1,max=100"`
    Description string         `json:"description,omitempty" validate:"max=500"`
    Type        string         `json:"type" validate:"required,oneof=typeA typeB"`
    Settings    map[string]any `json:"settings,omitempty"`
}
```

**Zod Schema:**
```typescript
const CreateResourceRequestSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  type: z.enum(['typeA', 'typeB']),
  settings: z.record(z.string(), z.unknown()).optional(),
});
```

**Responses:**

| Code | Description | Body |
|------|-------------|------|
| 201 | Created | Resource object |
| 400 | Validation error | Error object |
| 401 | Unauthorized | Error object |
| 409 | Duplicate | Error object |

**Example Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-123",
    "name": "My Resource",
    "description": "Description here",
    "type": "typeA",
    "status": "active",
    "settings": { "key": "value" },
    "tenant_id": "tenant-456",
    "created_by": "user-789",
    "created_at": "2026-01-23T12:00:00Z",
    "updated_at": "2026-01-23T12:00:00Z"
  }
}
```

---

### GET /<resource>

**Description:** List resources with pagination and filtering

**Request:**
```http
GET /api/v1/<resource>?page=1&limit=20&status=active&search=keyword
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `limit` | integer | 20 | Items per page (max 100) |
| `status` | string | - | Filter by status |
| `search` | string | - | Search in name/description |
| `sort` | string | `-created_at` | Sort field (- for desc) |

**Responses:**

| Code | Description | Body |
|------|-------------|------|
| 200 | Success | Paginated list |
| 401 | Unauthorized | Error object |

**Example Response (200):**
```json
{
  "success": true,
  "data": [
    { "id": "uuid-1", "name": "Resource 1", ... },
    { "id": "uuid-2", "name": "Resource 2", ... }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 42,
    "total_pages": 3
  }
}
```

---

### GET /<resource>/:id

**Description:** Get single resource by ID

**Request:**
```http
GET /api/v1/<resource>/uuid-123
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
```

**Responses:**

| Code | Description | Body |
|------|-------------|------|
| 200 | Success | Resource object |
| 401 | Unauthorized | Error object |
| 404 | Not found | Error object |

---

### PUT /<resource>/:id

**Description:** Update resource (full update)

**Request:**
```http
PUT /api/v1/<resource>/uuid-123
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "status": "inactive"
}
```

**Go Request Struct:**
```go
type UpdateResourceRequest struct {
    Name        *string `json:"name,omitempty" validate:"omitempty,min=1,max=100"`
    Description *string `json:"description,omitempty" validate:"omitempty,max=500"`
    Status      *string `json:"status,omitempty" validate:"omitempty,oneof=active inactive"`
}
```

**Responses:**

| Code | Description | Body |
|------|-------------|------|
| 200 | Updated | Resource object |
| 400 | Validation error | Error object |
| 401 | Unauthorized | Error object |
| 404 | Not found | Error object |

---

### DELETE /<resource>/:id

**Description:** Delete resource (soft delete)

**Request:**
```http
DELETE /api/v1/<resource>/uuid-123
Authorization: Bearer <token>
X-Tenant-ID: <tenant_id>
```

**Responses:**

| Code | Description | Body |
|------|-------------|------|
| 204 | Deleted | (empty) |
| 401 | Unauthorized | Error object |
| 404 | Not found | Error object |

---

## Data Types Reference

### Go to JSON Type Mapping
| Go Type | JSON Type | Notes |
|---------|-----------|-------|
| `string` | `string` | |
| `int`, `int64` | `number` | |
| `float64` | `number` | |
| `bool` | `boolean` | |
| `time.Time` | `string` | ISO 8601 format |
| `[]T` | `array` | |
| `map[string]any` | `object` | |
| `*T` | `T \| null` | Nullable |

### Validation Rules
| Rule | Go Tag | Zod |
|------|--------|-----|
| Required | `validate:"required"` | `.min(1)` |
| Min length | `validate:"min=N"` | `.min(N)` |
| Max length | `validate:"max=N"` | `.max(N)` |
| Enum | `validate:"oneof=a b c"` | `.enum(['a','b','c'])` |
| Email | `validate:"email"` | `.email()` |
| URL | `validate:"url"` | `.url()` |
| UUID | `validate:"uuid"` | `.uuid()` |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Create | 100 req | per minute |
| List | 1000 req | per minute |
| Get | 1000 req | per minute |
| Update | 100 req | per minute |
| Delete | 50 req | per minute |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | YYYY-MM-DD | Initial release |
