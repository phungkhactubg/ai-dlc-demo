# Software Requirements Specification (SRS)
# TMS — Tenant & Organization Management (Quản Lý Doanh Nghiệp)

**Module**: TMS — Tenant & Organization Management  
**Parent Work Package**: WP-TBD (to be assigned in MASTER_PLAN)  
**Source**: Derived from `PRD.md` §4.5, §4.9 and `ARCHITECTURE_SPEC.md` §9  
**Technology**: Java 17+ / Spring Boot 3.x  
**Database**: MongoDB (`tms_db`) + S3/MinIO | Cache: Redis | Events: Kafka  
**Version**: 1.0.0 | **Date**: 2026-03-06  

---

## 1. Introduction

TMS is the tenant control plane. It orchestrates enterprise tenant onboarding (via Saga pattern), manages tenant configurations, enforces data isolation (BL-001), manages white-label branding, controls feature flags per tenant, and provides rider identity management (B2C) via Keycloak integration.

### 1.1 Scope

| In Scope | Out of Scope |
|----------|-------------|
| Enterprise onboarding Saga (SSC+BMS+DPE+VMS) | Payment processing (PAY) |
| Tenant configuration & feature flags | Subscription plan management (BMS) |
| White-label branding (logo/colors/domain) | Vehicle fleet management (VMS) |
| Cross-tenant data isolation enforcement | IAM for platform operators (SSC) |
| Rider identity management (B2C) | Notification sending (NCS) |
| Keycloak v26+ SSO integration | |

---

## 2. Functional Flow Diagrams

### 2.1 Enterprise Onboarding Saga (FR-TMS-001, FR-TMS-002, BL-011)

```mermaid
sequenceDiagram
    participant Portal as Enterprise Portal
    participant TMS
    participant SSC
    participant BMS
    participant DPE
    participant VMS
    participant Kafka
    participant NCS

    Portal->>TMS: POST /api/v1/tenants { company_name, admin_email, plan_id, vehicle_quota }
    TMS->>TMS: Validate input; check uniqueness of company domain
    TMS->>TMS: Generate tenant_id (UUID v4)
    TMS->>TMS: Create tenant record { status: onboarding }
    TMS->>TMS: CREATE onboarding_saga record { saga_id, tenant_id, steps: [] }

    %% Step 1: SSC
    TMS->>SSC: POST /internal/tenants/{tenant_id}/admin-account { admin_email }
    SSC-->>TMS: { admin_user_id, rbac_role_ids } OR { error }
    alt SSC fails
        TMS->>TMS: UPDATE saga: step1=FAILED
        TMS->>TMS: DELETE tenant record
        TMS-->>Portal: HTTP 500 { error: "ONBOARDING_FAILED", step: "SSC", rollback: "complete" }
    else SSC success
        TMS->>TMS: UPDATE saga: step1=COMPLETED

        %% Step 2: BMS
        TMS->>BMS: POST /internal/subscriptions { tenant_id, plan_id }
        BMS-->>TMS: { subscription_id } OR { error }
        alt BMS fails
            TMS->>SSC: DELETE /internal/tenants/{tenant_id}/admin-account [compensate]
            TMS->>TMS: DELETE tenant record
            TMS-->>Portal: HTTP 500 { error: "ONBOARDING_FAILED", step: "BMS" }
        else BMS success
            TMS->>TMS: UPDATE saga: step2=COMPLETED

            %% Step 3: DPE
            TMS->>DPE: POST /internal/api-keys { tenant_id }
            DPE-->>TMS: { api_key, api_secret } OR { error }
            alt DPE fails
                TMS->>BMS: DELETE /internal/subscriptions/{subscription_id} [compensate]
                TMS->>SSC: DELETE /internal/tenants/{tenant_id}/admin-account [compensate]
                TMS->>TMS: DELETE tenant record
                TMS-->>Portal: HTTP 500 { error: "ONBOARDING_FAILED", step: "DPE" }
            else DPE success
                TMS->>TMS: UPDATE saga: step3=COMPLETED

                %% Step 4: VMS
                TMS->>VMS: POST /internal/fleet-allocation { tenant_id, vehicle_quota }
                VMS-->>TMS: { allocated_vehicles } OR { error }
                alt VMS fails
                    TMS->>DPE: DELETE /internal/api-keys/{tenant_id} [compensate]
                    TMS->>BMS: DELETE /internal/subscriptions/{subscription_id} [compensate]
                    TMS->>SSC: DELETE /internal/tenants/{tenant_id}/admin-account [compensate]
                    TMS->>TMS: DELETE tenant record
                    TMS-->>Portal: HTTP 500 { error: "ONBOARDING_FAILED", step: "VMS" }
                else VMS success
                    TMS->>TMS: UPDATE tenant: { status: active }
                    TMS->>TMS: UPDATE saga: step4=COMPLETED, status=SUCCESS
                    TMS->>Redis: SET tenant_config:{tenant_id} EX 300 (cache)
                    TMS->>Kafka: PUBLISH tenant-events[tenant.created] { tenant_id, plan_id }
                    TMS-->>Portal: HTTP 201 { tenant_id, admin_credentials, api_key }
                end
            end
        end
    end
```

### 2.2 White-Label Branding Update Flow

```mermaid
flowchart TD
    A[Tenant Admin: PUT /tenants/{id}/branding] --> B[Validate input: logo, colors, domain]
    B --> C{logo_file provided?}
    C -->|Yes| D[Upload logo to MinIO: tenants/{tenant_id}/logo.{ext}]
    D --> E[Generate CDN URL]
    C -->|No| F[Keep existing logo]
    E --> G[Update tenant.branding in MongoDB]
    F --> G
    G --> H[Invalidate Redis cache: tenant_config:{tenant_id}]
    H --> I[Return updated branding config]
```

### 2.3 Feature Flag Resolution (BL-010)

```mermaid
flowchart TD
    A[TenantConfigService.getEffectiveFlags] --> B[Load platform default flags from config]
    B --> C[Load tenant flags from Redis: tenant_flags:{tenant_id}]
    C --> D{Redis cache miss?}
    D -->|Yes| E[Query MongoDB: tenant.feature_flags]
    E --> F[Cache in Redis TTL 5 min]
    F --> G[Merge: tenant flags override platform defaults BL-010]
    D -->|No| G
    G --> H[Return effective_flags map]
```

---

## 3. Detailed Requirement Specifications

### 3.1 Feature: Enterprise Onboarding (FR-TMS-001, FR-TMS-002)

**User Story**: As an Enterprise Admin, I want to register my company on the platform and receive access credentials within minutes, without manual intervention.

#### 3.1.1 Inputs & Validations

| Field | Type | Required | Validation Rules | Error |
|-------|------|----------|-----------------|-------|
| `company_name` | string | Yes | 2–200 chars; unique | 400 / 409 |
| `company_domain` | string | Yes | Valid domain format `^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$`; unique in platform | 400 / 409 |
| `admin_email` | string | Yes | Valid email; regex `^[^\s@]+@[^\s@]+\.[^\s@]+$` | 400 |
| `admin_name` | string | Yes | 2–100 chars | 400 |
| `plan_id` | string | Yes | Must exist in BMS plans catalog | 400 |
| `vehicle_quota` | int | No | ≥ 0; default = plan's max_vehicles | 400 |
| `country_code` | string | Yes | ISO 3166-1 alpha-2 (e.g., "VN", "SG") | 400 |
| `timezone` | string | Yes | Valid IANA timezone (e.g., "Asia/Ho_Chi_Minh") | 400 |

#### 3.1.2 Business Logic — Saga Rules (BL-011)

1. All 4 onboarding steps (SSC, BMS, DPE, VMS) MUST succeed, or ALL are rolled back.
2. Rollback order (reverse of creation): VMS → DPE → BMS → SSC → tenant record.
3. Saga state persisted in `onboarding_sagas` collection; survives service restart.
4. If saga is `FAILED` and same company_domain registers again → allow (previous saga cleaned up).
5. Onboarding timeout: if any step takes > 30 seconds → mark step as `TIMED_OUT` → trigger rollback.
6. Publish `tenant.created` event to Kafka ONLY after saga status = `SUCCESS`.
7. NCS receives `tenant.created` via Kafka and sends welcome email with credentials.

#### 3.1.3 Tenant MongoDB Schema

```json
{
  "_id": "ObjectId",
  "tenant_id": "uuid-v4 (unique index)",
  "company_name": "string",
  "company_domain": "string (unique index)",
  "country_code": "string",
  "timezone": "string",
  "status": "enum[onboarding|active|suspended|terminated]",
  "plan_id": "string",
  "subscription_id": "string",
  "admin_user_id": "string",
  "api_key_reference": "string",
  "vehicle_quota": "int32",
  "branding": {
    "logo_url": "string (MinIO CDN URL)",
    "primary_color": "string (#RRGGBB)",
    "secondary_color": "string (#RRGGBB)",
    "email_template_id": "string",
    "custom_domain": "string",
    "custom_domain_verified": "boolean"
  },
  "surge_cap": "double (1.0–3.0, default 3.0)",
  "cancellation_policy": {
    "free_cancel_window_min": "int32",
    "fee_per_min_after_dispatch": "Decimal128"
  },
  "feature_flags": { "flag_key": "boolean" },
  "config": { "config_key": "string|int|boolean" },
  "monthly_budget_alert_threshold": "Decimal128 (null = disabled)",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

---

### 3.2 Feature: White-Label Branding (FR-TMS-010)

**Description**: Each tenant can customize their brand identity within the platform.

#### 3.2.1 Branding Customization Options

| Element | Allowed Values | Storage |
|---------|---------------|---------|
| Logo | PNG/SVG, max 5MB | MinIO: `tenants/{tenant_id}/logo.{ext}` |
| Primary color | Hex `#RRGGBB` | MongoDB `tenant.branding.primary_color` |
| Secondary color | Hex `#RRGGBB` | MongoDB `tenant.branding.secondary_color` |
| Email template | Custom HTML (sanitized) | MongoDB `notification_templates` collection |
| Custom domain | Valid FQDN | MongoDB `tenant.branding.custom_domain` |

**Color Validation**: `^#[0-9A-Fa-f]{6}$`

**Custom Domain Verification**:
1. Tenant sets `custom_domain = "rides.acmecorp.com"`.
2. TMS generates verification TXT record: `vnpt-verify={random_token}`.
3. Tenant adds TXT record to their DNS.
4. TMS scheduler checks DNS every 15 minutes (max 48h). On verification success → `custom_domain_verified = true`.

**MinIO Logo Upload**:
- `POST /api/v1/tenants/{id}/branding/logo` with `multipart/form-data`.
- Validate: MIME type in `[image/png, image/svg+xml]`; size ≤ 5MB.
- Store at `s3://av-platform-assets/tenants/{tenant_id}/logo.{ext}`.
- Return CDN URL: `https://cdn.vnpt-av.com/tenants/{tenant_id}/logo.{ext}`.

---

### 3.3 Feature: Data Isolation & Quota (FR-TMS-020, FR-TMS-021)

**Description**: BL-001 compliance — every data access is filtered by `tenant_id`.

#### 3.3.1 TenantContextFilter (Spring Filter)

```java
@Component
public class TenantContextFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, ...) {
        String tenantId = jwtDecoder.decode(bearerToken).getClaim("tenant_id");
        if (tenantId == null || tenantId.isBlank()) {
            response.sendError(403, "Missing tenant_id in JWT");
            return;
        }
        TenantContext.setTenantId(tenantId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear(); // MUST clear to prevent thread-local leak
        }
    }
}
```

**Rule**: Endpoints with `@Public` annotation bypass tenant check (e.g., rider registration, health check).

#### 3.3.2 Resource Quota Enforcement

- TMS defines quotas per tenant per plan: `{ max_vehicles, max_api_calls, max_rides, max_storage_gb }`.
- Quotas stored in MongoDB → synced to Redis on creation/update.
- BMS `QuotaEnforcementService` reads from Redis (not TMS) for speed.
- On subscription change → TMS sends `tenant.quota_updated` event → BMS refreshes Redis cache.

---

### 3.4 Feature: Tenant Configuration & Feature Flags (FR-TMS-030, FR-TMS-031, BL-010)

**Description**: Tenant-level feature flags override platform-level defaults.

#### 3.4.1 Feature Flag Operations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/tenants/{id}/config` | JWT (Tenant Admin) | Get all config + feature flags |
| `PUT` | `/api/v1/tenants/{id}/config` | JWT (Tenant Admin) | Update config values |
| `PUT` | `/api/v1/tenants/{id}/feature-flags` | JWT (Platform Admin) | Set feature flags |

**Feature Flag Examples**:
```json
{
  "ride_pooling_enabled": true,
  "surge_pricing_enabled": false,
  "wallet_topup_enabled": true,
  "scheduled_rides_enabled": true,
  "corporate_travel_plugin_enabled": false
}
```

**Cache**: `SET tenant_config:{tenant_id} {JSON} EX 300` (5-minute TTL).  
**Invalidation**: On any config update → `DEL tenant_config:{tenant_id}`.

---

### 3.5 Feature: Rider Identity Management (FR-TMS-040, FR-TMS-041, FR-TMS-042)

**Description**: B2C rider registration, social login (Google/Apple), phone OTP verification, and optional Keycloak SSO.

#### 3.5.1 Rider Registration Flow

```mermaid
flowchart TD
    A[POST /api/v1/riders/register] --> B{Auth method?}
    B -->|Email + Password| C[Create Keycloak account; send email verification]
    B -->|Google OAuth| D[Redirect to Google OAuth2; callback with id_token]
    D --> E[Validate id_token with Google JWKS; extract email + sub]
    B -->|Apple OAuth| F[Validate Apple identity token; extract email + sub]
    C --> G[Create rider profile in MongoDB]
    E --> G
    F --> G
    G --> H[POST /api/v1/riders/{id}/verify-phone (OTP)]
    H --> I[Twilio sends 6-digit OTP via SMS]
    I --> J[POST /api/v1/riders/{id}/confirm-otp { code }]
    J --> K{OTP valid and not expired?}
    K -->|Yes| L[Set phone_verified=true; issue JWT]
    K -->|No| M[HTTP 422 INVALID_OTP; max 5 attempts then lock 30 min]
```

#### 3.5.2 Rider Profile MongoDB Schema

```json
{
  "_id": "ObjectId",
  "rider_id": "uuid-v4 (unique index)",
  "tenant_id": "string (indexed)",
  "keycloak_sub": "string (indexed, from Keycloak)",
  "email": "string (indexed, lowercase)",
  "email_verified": "boolean",
  "phone_number": "string (E.164 format: +84912345678)",
  "phone_verified": "boolean",
  "full_name": "string",
  "preferred_language": "string (IETF BCP 47, e.g., vi-VN)",
  "auth_provider": "enum[email|google|apple]",
  "google_sub": "string (null if not Google auth)",
  "apple_sub": "string (null if not Apple auth)",
  "profile_photo_url": "string",
  "wallet_id": "string (created by PAY on registration)",
  "default_payment_method": "enum[wallet|gateway]",
  "status": "enum[pending_verification|active|suspended]",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### 3.5.3 OTP Validation Rules

- OTP: 6-digit numeric code.
- Expiry: 5 minutes.
- Max attempts: 5 per OTP. After 5 failed attempts → lock account for 30 minutes.
- OTP stored in Redis: `otp:{rider_id}:{phone_number}` TTL 300s.
- Resend limit: max 3 resends per hour per phone number.

#### 3.5.4 Keycloak Integration (FR-TMS-041)

- Keycloak realm: `av-platform-riders` (separate from operator realm).
- OIDC/OAuth2 PKCE flow for mobile clients.
- `KeycloakAdapter.createUser(email, name)` → Keycloak REST Admin API.
- JWT issued by Keycloak; validated at Kong API Gateway using Keycloak JWKS endpoint.
- `FR-TMS-042`: Rider JWT claims (`tenant_id`, `rider_id`, `roles: ["rider"]`) must NOT overlap with operator IAM JWT claims.

---

## 4. API Contracts

### 4.1 Tenant Management APIs

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/tenants` | JWT (Platform Admin) | Create tenant (trigger Saga) |
| `GET` | `/api/v1/tenants/{tenant_id}` | JWT (Admin) | Get tenant details |
| `GET` | `/api/v1/tenants` | JWT (Platform Admin) | List all tenants (paginated) |
| `PUT` | `/api/v1/tenants/{id}/status` | JWT (Platform Admin) | Suspend/reactivate tenant |
| `PUT` | `/api/v1/tenants/{id}/branding` | JWT (Tenant Admin) | Update branding config |
| `POST` | `/api/v1/tenants/{id}/branding/logo` | JWT (Tenant Admin) | Upload logo to MinIO |
| `GET/PUT` | `/api/v1/tenants/{id}/config` | JWT (Tenant Admin) | Get/update feature flags |

**POST /tenants Response 201**:
```json
{
  "tenant_id": "uuid-v4",
  "status": "active",
  "admin_credentials": {
    "email": "admin@acmecorp.com",
    "temporary_password": "abc123!@#"
  },
  "api_key": "vnpt_live_xxxxxxxx",
  "api_secret": "sk_live_xxxxxxxx"
}
```

### 4.2 Rider APIs

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/riders/register` | Public | Rider registration |
| `POST` | `/api/v1/riders/{id}/verify-phone` | JWT (Rider) | Send OTP to phone |
| `POST` | `/api/v1/riders/{id}/confirm-otp` | JWT (Rider) | Confirm OTP code |
| `GET` | `/api/v1/riders/{id}` | JWT (Rider own or Admin) | Get rider profile |
| `PUT` | `/api/v1/riders/{id}` | JWT (Rider own) | Update profile |

---

## 5. Kafka Events

| Topic | Event Key | Payload | Consumers |
|-------|-----------|---------|-----------|
| `tenant-events` | `tenant.created` | `tenant_id, company_name, plan_id, admin_email, timestamp` | NCS, BMS, ABI |
| `tenant-events` | `tenant.suspended` | `tenant_id, reason, suspended_by, timestamp` | NCS, BMS, ABI |
| `tenant-events` | `tenant.reactivated` | `tenant_id, timestamp` | NCS, BMS |
| `tenant-events` | `tenant.quota_updated` | `tenant_id, new_quota, timestamp` | BMS |

---

## 6. Non-Functional Requirements

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| Onboarding completion | < 30 seconds end-to-end | Saga with 10s timeout per step |
| Tenant config retrieval | < 5ms P99 | Redis cache 5-min TTL |
| Cross-tenant isolation | 100% enforced | TenantContextFilter + BaseMongoRepository.withTenant() |
| OTP delivery | < 10 seconds | Twilio priority route |
| Saga durability | Survives service restart | MongoDB persisted saga state |

---

## 7. Acceptance Criteria

| # | Criterion | Test Type |
|---|-----------|-----------|
| AC-TMS-001 | Full onboarding completes in < 30s with all 4 steps | Integration test |
| AC-TMS-002 | Onboarding rolls back completely when SSC fails (BL-011) | Integration test |
| AC-TMS-003 | Cross-tenant data access returns 403 (BL-001) | Security test |
| AC-TMS-004 | Feature flag from tenant overrides platform default (BL-010) | Unit test |
| AC-TMS-005 | Logo upload to MinIO returns correct CDN URL | Integration test |
| AC-TMS-006 | Rider Google OAuth login creates profile and issues JWT | Integration test |
| AC-TMS-007 | OTP locked after 5 failed attempts | Unit test |
| AC-TMS-008 | `tenant.created` Kafka event published after successful onboarding | Integration test |
| AC-TMS-009 | Rider JWT does not contain operator-level claims (FR-TMS-042) | Security test |
| AC-TMS-010 | Tenant suspension publishes `tenant.suspended` event | Integration test |

---

*SRS v1.0.0 — TMS Tenant & Organization Management | VNPT AV Platform Services Provider Group*
