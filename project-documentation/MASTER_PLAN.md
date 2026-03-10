# MASTER IMPLEMENTATION PLAN
## VNPT AV Platform — Services Provider Group

---

## 1. Execution Status Overview

- **Project Name**: VNPT AV Platform — Services Provider Microservices Group
- **Current Phase**: Phase 2 — Core Transaction Services (WP-001 ✅ COMPLETE)
- **Overall Progress**: 8% (1/13 Work Packages — WP-001 DONE)
- **Last Sync**: 2026-03-06 (WP-001 completed)
- **Blocked By**: None
- **Technology Stack**: Java 17+ / Spring Boot 3.x, MongoDB, Apache Kafka, Redis, NATS, Kong API Gateway
- **Architecture Pattern**: Microservices / Clean Architecture per service
- **Multi-tenancy**: TenantContext ThreadLocal + BaseMongoRepository.withTenant() — mandatory on ALL queries

---

## 2. Project Context & Architecture Summary

### 2.1 Platform Overview
The VNPT AV Platform Services Provider group consists of **8 independent Java/Spring Boot 3.x microservices** that collectively power the ride-hailing and platform management ecosystem for autonomous vehicles. All services share a common multi-tenancy model, event-driven architecture via Apache Kafka, and a unified observability stack.

### 2.2 Service Inventory

| Service ID | Name | Description | SRS Reference |
|------------|------|-------------|---------------|
| TMS | Tenant Management Service | Multi-tenant onboarding, white-label, feature flags, Saga orchestration | SRS_TMS_Tenant_Organization.md |
| PAY | Payment Processing Service | 5-gateway routing, escrow, idempotency, fraud detection | SRS_PAY_Payment_Processing.md |
| RHS | Ride Hailing Service | Trip lifecycle, AV matching, ETA, pooling, rating | SRS_RHS_Ride_Hailing_Service.md |
| FPE | Fare Pricing Engine | Fare formula, surge pricing, rate cards, promotions | SRS_FPE_Fare_Pricing_Engine.md |
| BMS | Billing & Subscription Management | Subscription lifecycle, metering, quota, invoicing | SRS_BMS_Billing_Subscription.md |
| NCS | Notification & Communication Service | Multi-channel, DLQ, HMAC webhooks, BL-007 <5s SLA | SRS_NCS_Notification_Communication.md |
| ABI | Analytics & BI | ETL pipeline, KPI dashboards, regulatory reports | SRS_ABI_Analytics_BI.md |
| MKP | Marketplace | Partner lifecycle, BL-009 audit gate, revenue share | SRS_MKP_Marketplace.md |

### 2.3 Cross-Cutting Architecture Decisions (ADRs)

| ADR | Decision | Impact |
|-----|----------|--------|
| ADR-001 | Separate MongoDB namespaces per tenant | All repository queries MUST include `tenant_id` filter |
| ADR-002 | Kafka + NATS dual messaging | Kafka for async events; NATS only for RHS real-time push |
| ADR-003 | Escrow payment model | PAY must hold funds before RHS trip completes |
| ADR-004 | Redis idempotency keys (24h TTL) | All PAY operations check Redis before DB write |
| ADR-005 | Saga orchestration for TMS onboarding | SSC → BMS → DPE → VMS with full rollback |
| ADR-006 | tenant_id enforced at every layer | Controller, Service, Repository — no exceptions |
| ADR-007 | Kong API Gateway | All ingress via Kong; per-tenant rate limiting |
| ADR-008 | Java 17 / Spring Boot 3.x | All 8 services — NOT Go |

### 2.4 Critical Business Rules

| Rule ID | Description | Enforcing Service |
|---------|-------------|-------------------|
| BL-001 | tenant_id mandatory in every MongoDB query | ALL services |
| BL-002 | Trip fare calculated by FPE — RHS must not hardcode fare | RHS, FPE |
| BL-003 | PAY escrow must be confirmed before driver payout | PAY, RHS |
| BL-004 | Redis idempotency check (24h TTL) before any payment write | PAY |
| BL-005 | PCI-DSS: payment_transactions collection is INSERT-only (MongoDB validator) | PAY |
| BL-006 | Subscription quota enforced before trip/API call | BMS, RHS |
| BL-007 | Notification delivery SLA: <5 seconds end-to-end | NCS |
| BL-008 | Kafka partition key MUST be tenant_id for all topics | ALL services |
| BL-009 | Marketplace partner changes require admin audit gate | MKP |
| BL-010 | ABI reports must not expose cross-tenant data | ABI |
| BL-011 | TMS onboarding uses Saga — full rollback on any step failure | TMS |

### 2.5 Infrastructure Components

| Component | Technology | Configuration |
|-----------|------------|---------------|
| Message Broker | Apache Kafka | 7 topics, RF=3, tenant_id as partition key |
| Real-time Push | NATS | RHS only; subjects: `rhs.{tenant_id}.trips.{trip_id}.{state\|eta}` |
| Cache / Idempotency | Redis Cluster | 24h TTL for PAY idempotency keys |
| Database | MongoDB Replica Set | Separate namespaces per tenant (ADR-001) |
| API Gateway | Kong | Per-tenant rate limiting, JWT auth |
| Payment Namespace | Kubernetes `pay-namespace` | PCI-DSS isolation (dedicated namespace) |

### 2.6 Kafka Topic Inventory

| Topic | Partitions | Producer | Consumers |
|-------|-----------|----------|-----------|
| `ride-events` | 24 | RHS | FPE, BMS, ABI, NCS |
| `fare-events` | 12 | FPE | RHS, ABI |
| `payment-events` | 24 | PAY | RHS, BMS, NCS, ABI |
| `billing-events` | 12 | BMS | NCS, ABI |
| `metering-events` | 12 | BMS | ABI |
| `tenant-events` | 6 | TMS | ALL services |
| `notification-dlq` | 6 | NCS | NCS (retry consumer) |

### 2.7 NFR Targets

| Category | Target |
|----------|--------|
| Read Latency | P95 < 200ms |
| Write Latency | P95 < 500ms |
| Concurrent Trips | ≥ 10,000 |
| API Throughput | ≥ 50,000 req/s |
| Kafka Throughput | ≥ 100,000 events/s |
| Availability | 99.9% uptime |
| RTO | < 30 minutes |
| RPO | < 5 minutes |
| Notification SLA | < 5 seconds (BL-007) |

---

## 3. Work Package Phases

### Phase Overview & Dependency Order

```
Phase 1: Foundation Infrastructure  (WP-001) ✅ COMPLETE — 2026-03-06
         ↓
Phase 2: Core Transaction Services
         TMS (WP-002) → PAY (WP-003) → RHS (WP-004) → FPE (WP-005)
         ↓
Phase 3: Supporting Services
         BMS (WP-006) → NCS (WP-007)
         ↓
Phase 4: Intelligence & Ecosystem
         ABI (WP-008) → MKP (WP-009)
         ↓
Phase 5: Cross-Cutting Hardening
         Observability (WP-010) → Integration Testing (WP-011) → Performance (WP-012) → PCI-DSS Audit (WP-013)
```

---

## 4. Phase 1: Foundation Infrastructure

### WP-001: Foundation Infrastructure & Shared Libraries
**Goal**: Establish all infrastructure components and shared Java libraries that ALL 8 services depend on. Nothing from Phase 2+ can start until WP-001 is COMPLETE.

**Depends On**: None (starting point)

**Assigned Agent**: DevOps Engineer + Solutions Architect

**Key Deliverables**:
- [x] **WP-001-T01**: Create shared Maven/Gradle module `av-platform-shared` with: ✅ DONE (62 tests passing)
  - `TenantContext` class — ThreadLocal storage, `setTenantId(String)`, `getTenantId()`, `clear()`
  - `BaseMongoRepository<T>` — abstract class wrapping all queries with `withTenant()` filter enforcing BL-001
  - `ApiResponse<T>` — standard response wrapper `{success, data, error, timestamp, traceId}`
  - `PlatformException` — base exception with `errorCode`, `httpStatus`, `userMessage`
  - `TenantInterceptor` — Spring `HandlerInterceptor` extracting `X-Tenant-ID` header → `TenantContext`
- [x] **WP-001-T02**: Configure Apache Kafka cluster: ✅ DONE
  - Create all 7 topics with specified partition counts and RF=3
  - Configure `tenant_id` as default partition key via custom `Partitioner` implementation
  - Configure producer: `acks=all`, `enable.idempotence=true`, `max.in.flight.requests.per.connection=5`
  - Configure consumer: `auto.offset.reset=earliest`, `isolation.level=read_committed`
- [x] **WP-001-T03**: Configure NATS cluster: ✅ DONE
  - Subject pattern: `rhs.{tenant_id}.trips.{trip_id}.{state|eta}`
  - Configure TLS + NKey authentication
  - Maximum message size: 1MB
- [x] **WP-001-T04**: Configure MongoDB Replica Set: ✅ DONE
  - Enable replica set with 3 nodes (PRIMARY + 2 SECONDARY)
  - Configure `writeConcern: majority`, `readPreference: primaryPreferred`
  - Create `av_platform_prod` database with per-tenant collection namespacing
  - Enable `PAY` MongoDB collection validator for INSERT-only enforcement on `payment_transactions`
- [x] **WP-001-T05**: Configure Redis Cluster: ✅ DONE
  - 6-node cluster (3 primary + 3 replica)
  - Default TTL: 24 hours for PAY idempotency keys
  - Keyspace: `idempotency:{service}:{operationId}`, `session:{tenantId}:{userId}`
- [x] **WP-001-T06**: Configure Kong API Gateway: ✅ DONE
  - Install plugins: JWT auth, Rate Limiting, Request Transformer, Prometheus
  - Per-tenant rate limiting: 1000 req/min (configurable per TMS feature flags)
  - Routes: `/api/v1/rides/*` → RHS, `/api/v1/fares/*` → FPE, `/api/v1/payments/*` → PAY, etc.
  - JWT validation: RS256, JWKS endpoint from TMS auth service
- [x] **WP-001-T07**: Create Kubernetes namespace structure: ✅ DONE
  - `av-platform` namespace: RHS, FPE, BMS, TMS, NCS, ABI, MKP
  - `pay-namespace`: PAY only (PCI-DSS isolation, NetworkPolicy denying all non-PAY ingress)
  - Apply ResourceQuota and LimitRange per namespace
  - Configure HorizontalPodAutoscaler for each service
- [x] **WP-001-T08**: Spring Boot 3.x project skeleton per service: ✅ DONE (154 Java files, BUILD SUCCESS)
  - Package structure: `com.vnpt.avplatform.{service}/{controllers,services,repositories,models,events,adapters,config}/`
  - Common `application.yml` structure with profiles: `dev`, `staging`, `prod`
  - `SecurityConfig.java` — Spring Security 6 with JWT filter
  - `KafkaConfig.java` — producer/consumer factory with tenant-aware serializer
  - `MongoConfig.java` — MongoTemplate with `TenantAwareMongoTemplate` override
  - `OpenApiConfig.java` — Springdoc OpenAPI 3.0 with `X-Tenant-ID` header global parameter

**Definition of Done**: All 8 services compile against `av-platform-shared`; Kafka, MongoDB, Redis, NATS, Kong all health-check green; `TenantContext` passes unit test suite (20+ test cases).

---

## 5. Phase 2: Core Transaction Services

### WP-002: TMS — Tenant Management Service
**Goal**: Implement complete tenant lifecycle management including Saga-based onboarding (BL-011), white-label configuration, and feature flag management. TMS must be the FIRST service live because ALL other services consume `tenant-events` from Kafka.

**Depends On**: WP-001

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_TMS_Tenant_Organization.md`

**Functional Requirements**: FR-TMS-001 through FR-TMS-021

**Key Deliverables**:
- [ ] **WP-002-T01**: Implement `Tenant` domain model:
  - Fields: `tenantId` (UUID), `name`, `slug` (unique, regex `^[a-z0-9-]{3,63}$`), `status` (PENDING/ACTIVE/SUSPENDED/TERMINATED), `plan` (STARTER/PROFESSIONAL/ENTERPRISE), `whiteLabel` (embedded doc), `featureFlags` (Map<String, Boolean>), `createdAt`, `updatedAt`
  - MongoDB collection: `tenants` with unique index on `slug`
  - `@Document(collection = "tenants")` with optimistic locking `@Version`
- [ ] **WP-002-T02**: Implement TMS Onboarding Saga (ADR-005, BL-011):
  - `TenantOnboardingSagaOrchestrator` — step sequence: SSC → BMS → DPE → VMS
  - Each step publishes compensating event on failure
  - Saga state stored in `saga_instances` MongoDB collection with `sagaId`, `currentStep`, `status`, `compensationLog`
  - Full rollback chain: VMS rollback → DPE rollback → BMS rollback → SSC rollback
  - Timeout: 30 seconds per step; saga-level timeout: 120 seconds
- [ ] **WP-002-T03**: Implement `TenantRepository extends BaseMongoRepository<Tenant>`:
  - `findBySlug(String slug, String tenantId)`
  - `findAllByStatus(TenantStatus status, String tenantId, Pageable pageable)`
  - All queries MUST call `withTenant()` — BL-001 enforcement
- [ ] **WP-002-T04**: Implement `TenantService` interface + `TenantServiceImpl`:
  - `createTenant(CreateTenantRequest, String adminUserId)` — triggers Saga
  - `updateTenant(String tenantId, UpdateTenantRequest, String requestingTenantId)` — validates tenant owns the update
  - `suspendTenant(String tenantId, String reason)` — publishes `TenantSuspendedEvent` to `tenant-events`
  - `getFeatureFlag(String tenantId, String flagKey)` → Boolean
  - `updateWhiteLabel(String tenantId, WhiteLabelConfig config)` — updates branding assets URL, colors, logo
- [ ] **WP-002-T05**: Implement REST controllers:
  - `POST /api/v1/tenants` — create (admin-only)
  - `GET /api/v1/tenants/{tenantId}` — get by ID
  - `PATCH /api/v1/tenants/{tenantId}` — update
  - `POST /api/v1/tenants/{tenantId}/suspend` — suspend
  - `GET /api/v1/tenants/{tenantId}/features` — feature flags
  - `PUT /api/v1/tenants/{tenantId}/features/{flagKey}` — toggle feature
  - `GET /api/v1/tenants/{tenantId}/white-label` — get white-label config
  - All endpoints validate `X-Tenant-ID` header matches path `tenantId` (unless super-admin)
- [ ] **WP-002-T06**: Implement Kafka producer for `tenant-events`:
  - `TenantCreatedEvent`, `TenantActivatedEvent`, `TenantSuspendedEvent`, `TenantTerminatedEvent`
  - Event schema: `{eventId, eventType, tenantId, timestamp, payload}`
  - Partition key: `tenantId`
- [ ] **WP-002-T07**: Unit tests (≥ 80% coverage):
  - Saga happy path test
  - Saga rollback test (failure at each step)
  - TenantContext injection test
  - Feature flag toggle test

**Definition of Done**: TMS passes all unit tests; `tenant-events` topic receives events verifiable via Kafka console consumer; Saga rollback verified via failure injection test.

---

### WP-003: PAY — Payment Processing Service
**Goal**: Implement PCI-DSS compliant payment processing with 5-gateway routing, escrow model (ADR-003), Redis idempotency (ADR-004), and immutable audit log (BL-005). PAY must be live before RHS can complete trips.

**Depends On**: WP-001, WP-002

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_PAY_Payment_Processing.md`

**Functional Requirements**: FR-PAY-001 through FR-PAY-028

**Key Deliverables**:
- [ ] **WP-003-T01**: Implement `PaymentTransaction` domain model:
  - Fields: `transactionId` (UUID), `tenantId`, `tripId`, `riderId`, `driverId`, `amount` (BigDecimal), `currency` (ISO 4217), `status` (PENDING/ESCROW_HELD/COMPLETED/FAILED/REFUNDED), `gateway` (VNPAY/MOMO/ZALOPAY/VISA/MASTERCARD), `idempotencyKey`, `auditLog` (List<AuditEntry>), `createdAt`
  - MongoDB collection: `payment_transactions` with INSERT-only validator (BL-005):
    ```json
    { "$jsonSchema": { "additionalProperties": false, "required": ["transactionId","tenantId","createdAt"] } }
    ```
  - Unique compound index: `{tenantId, idempotencyKey}`
- [ ] **WP-003-T02**: Implement Redis idempotency guard (ADR-004, BL-004):
  - `IdempotencyService.checkAndSet(String idempotencyKey, String tenantId)` → Optional<PaymentResponse>
  - Key format: `idempotency:pay:{tenantId}:{idempotencyKey}`
  - TTL: 24 hours (86400 seconds)
  - If key exists → return cached response (HTTP 200, no duplicate charge)
  - If key absent → proceed with payment, store result in Redis
- [ ] **WP-003-T03**: Implement 5-gateway routing strategy:
  - `PaymentGatewayRouter` — selects gateway based on: currency, amount threshold, tenant preference, gateway availability
  - `VNPayGatewayAdapter`, `MoMoGatewayAdapter`, `ZaloPayGatewayAdapter`, `VisaGatewayAdapter`, `MastercardGatewayAdapter` — all implement `PaymentGatewayPort`
  - Circuit breaker (Resilience4j) per gateway: failureRateThreshold=50%, waitDurationInOpenState=30s
  - Fallback order: primary gateway → secondary → tertiary → return `GATEWAY_UNAVAILABLE` error
- [ ] **WP-003-T04**: Implement escrow model (ADR-003, BL-003):
  - `escrowPayment(EscrowRequest)` → holds funds from rider wallet
  - `releaseEscrow(String transactionId, String tripId)` → releases to driver after trip COMPLETED
  - `cancelEscrow(String transactionId, String reason)` → returns funds to rider on trip CANCELLED
  - Escrow state machine: PENDING → ESCROW_HELD → [COMPLETED | REFUNDED]
- [ ] **WP-003-T05**: Implement REST controllers (in `pay-namespace`):
  - `POST /api/v1/payments/initiate` — initiate payment (requires `Idempotency-Key` header)
  - `POST /api/v1/payments/{transactionId}/escrow` — hold escrow
  - `POST /api/v1/payments/{transactionId}/release` — release escrow
  - `POST /api/v1/payments/{transactionId}/refund` — refund
  - `GET /api/v1/payments/{transactionId}` — get transaction
  - `GET /api/v1/payments?tripId={tripId}` — list by trip
  - All endpoints enforce `X-Tenant-ID` header; `pay-namespace` NetworkPolicy blocks all external access except Kong
- [ ] **WP-003-T06**: Implement Kafka producer for `payment-events`:
  - `PaymentInitiatedEvent`, `EscrowHeldEvent`, `PaymentCompletedEvent`, `PaymentFailedEvent`, `RefundInitiatedEvent`
  - Partition key: `tenantId`
- [ ] **WP-003-T07**: Implement fraud detection rules:
  - Velocity check: > 10 transactions per minute per `riderId+tenantId` → flag as suspicious → require 3DS
  - Amount threshold: > 10,000,000 VND → require additional OTP verification
  - Blacklist check against `fraud_blacklist` MongoDB collection
- [ ] **WP-003-T08**: Unit + integration tests:
  - Idempotency test (same key twice → same response, no duplicate DB record)
  - Escrow state machine test
  - Circuit breaker fallback test
  - PCI-DSS validator test (attempt UPDATE on payment_transactions → should fail)

**Definition of Done**: PAY deployed in `pay-namespace`; idempotency verified via duplicate request test; escrow state machine transitions verified; MongoDB INSERT-only validator blocks UPDATE/DELETE operations.

---

### WP-004: RHS — Ride Hailing Service
**Goal**: Implement complete trip lifecycle from booking through completion, AV matching algorithm, ETA calculation via NATS, and trip pooling. RHS is the core orchestrator that coordinates FPE (fare) and PAY (payment).

**Depends On**: WP-001, WP-002, WP-003, WP-005 (FPE must be live for fare calculation)

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_RHS_Ride_Hailing_Service.md`

**Functional Requirements**: FR-RHS-001 through FR-RHS-041

**Key Deliverables**:
- [ ] **WP-004-T01**: Implement `Trip` domain model:
  - Fields: `tripId` (UUID), `tenantId`, `riderId`, `driverId`, `vehicleId`, `status` (REQUESTED/MATCHING/CONFIRMED/DRIVER_ENROUTE/STARTED/COMPLETED/CANCELLED), `pickupLocation` (GeoJSON Point), `dropoffLocation` (GeoJSON Point), `estimatedFare` (from FPE), `actualFare`, `escrowTransactionId`, `poolingGroupId`, `rating` (embedded), `timestamps` (map of status→timestamp), `cancelReason`
  - MongoDB collection: `trips` with 2dsphere index on `pickupLocation`
  - TTL index on `createdAt` (90 days)
- [ ] **WP-004-T02**: Implement AV matching algorithm:
  - `AVMatchingService.findNearestAvailableAV(GeoPoint pickup, String tenantId, VehicleType type)` → Optional<Vehicle>
  - Query `vehicles` collection: status=AVAILABLE, location within 5km radius, sorted by distance
  - Apply tenant feature flag `POOLING_ENABLED` to filter poolable vs. exclusive vehicles
  - Lock selected vehicle (optimistic locking) to prevent double-booking
  - Timeout: 30 seconds for match; if no match → return `NO_AVAILABLE_VEHICLE` (HTTP 404)
- [ ] **WP-004-T03**: Implement ETA via NATS:
  - `ETAService.publishETAUpdate(String tripId, String tenantId, ETAUpdate update)` → publishes to `rhs.{tenantId}.trips.{tripId}.eta`
  - ETA recalculated every 15 seconds while trip is DRIVER_ENROUTE or STARTED
  - `ETAUpdate` payload: `{etaSeconds, currentLocation, distanceRemaining}`
  - NATS subscriber in mobile gateway service consumes updates and pushes to client
- [ ] **WP-004-T04**: Implement trip lifecycle state machine:
  - REQUESTED → MATCHING (AV search started) → CONFIRMED (AV assigned) → DRIVER_ENROUTE (AV moving to pickup) → STARTED (rider picked up) → COMPLETED (dropoff confirmed) / CANCELLED
  - Each transition publishes event to `ride-events` Kafka topic
  - `COMPLETED` transition: calls FPE to finalize fare → calls PAY to release escrow (BL-003)
  - `CANCELLED` transition: calls PAY to cancel escrow; cancellation fee applied if after 3 minutes
- [ ] **WP-004-T05**: Implement trip pooling (FR-RHS-020 through FR-RHS-025):
  - `PoolingService.findCompatiblePool(Trip trip, String tenantId)` → Optional<PoolingGroup>
  - Compatibility rules: same direction (< 30° bearing difference), pickup within 500m, dropoff within 800m
  - Maximum 3 riders per pooled vehicle
  - Fare split: each rider pays 65% of solo fare (configurable per tenant)
- [ ] **WP-004-T06**: Implement fare estimation (calls FPE synchronously):
  - `FareEstimationAdapter` — REST call to FPE `/api/v1/fares/estimate`
  - Timeout: 2 seconds; on timeout → return cached fare estimate from Redis
  - Cache key: `fare:estimate:{tenantId}:{pickup_hash}:{dropoff_hash}:{vehicle_type}`
  - Cache TTL: 60 seconds
- [ ] **WP-004-T07**: Implement REST controllers:
  - `POST /api/v1/rides/request` — request trip (triggers AV matching)
  - `GET /api/v1/rides/{tripId}` — get trip status
  - `POST /api/v1/rides/{tripId}/cancel` — cancel trip
  - `POST /api/v1/rides/{tripId}/complete` — driver marks completion
  - `POST /api/v1/rides/{tripId}/rate` — submit rating (1-5 stars + comment)
  - `GET /api/v1/rides?riderId={riderId}&status={status}` — list rider's trips (paginated)
  - `GET /api/v1/rides/estimate` — fare estimate (query params: pickup, dropoff, vehicleType)
- [ ] **WP-004-T08**: Implement Kafka producer for `ride-events`:
  - `TripRequestedEvent`, `TripMatchedEvent`, `TripStartedEvent`, `TripCompletedEvent`, `TripCancelledEvent`
  - Partition key: `tenantId`
- [ ] **WP-004-T09**: Unit + integration tests:
  - AV matching test (happy path + no vehicle available)
  - Trip state machine transition tests
  - Pooling compatibility algorithm test
  - FPE adapter timeout + cache fallback test

**Definition of Done**: Trip lifecycle end-to-end test passes (request → match → start → complete → escrow released); NATS ETA updates verified; Kafka `ride-events` events verified.

---

### WP-005: FPE — Fare Pricing Engine
**Goal**: Implement dynamic fare calculation with surge pricing, multi-tier rate cards, promotional discounts, and cancellation fee logic. FPE must be live before RHS (WP-004) since RHS calls FPE for fare estimation.

**Depends On**: WP-001, WP-002

**NOTE**: WP-005 is developed in parallel with WP-004 (FPE must reach API-ready state before WP-004's T06 fare estimation feature is implemented)

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_FPE_Fare_Pricing_Engine.md`

**Functional Requirements**: FR-FPE-001 through FR-FPE-032

**Key Deliverables**:
- [ ] **WP-005-T01**: Implement `RateCard` domain model:
  - Fields: `rateCardId` (UUID), `tenantId`, `vehicleType` (SEDAN/SUV/VAN/MICRO), `basefare` (BigDecimal), `perKmRate`, `perMinuteRate`, `minimumFare`, `cancellationFee`, `surgeMultiplierCap` (default 3.0x), `effectiveFrom`, `effectiveTo`, `status` (ACTIVE/DRAFT/ARCHIVED)
  - MongoDB collection: `rate_cards` with compound unique index: `{tenantId, vehicleType, effectiveFrom}`
- [ ] **WP-005-T02**: Implement fare calculation engine:
  - `FareCalculationService.calculateFare(FareRequest)` → `FareResult`
  - Formula: `fare = basefare + (distanceKm * perKmRate) + (durationMin * perMinuteRate)`
  - Apply surge: `fareWithSurge = fare * min(surgeMultiplier, surgeMultiplierCap)`
  - Apply promotions: `finalFare = max(fareWithSurge - discountAmount, minimumFare)`
  - Round to nearest 500 VND
  - Return: `{estimatedFare, breakdown: {baseFare, distanceFare, timeFare, surgeFee, discount, total}, currency: "VND"}`
- [ ] **WP-005-T03**: Implement surge pricing algorithm:
  - `SurgeService.calculateSurgeMultiplier(GeoPoint area, String tenantId)` → Double
  - Input factors: demand/supply ratio in 1km grid cell, time of day, weather (from external API)
  - Surge tiers: 1.0x (ratio < 1.5), 1.5x (1.5-2.5), 2.0x (2.5-4.0), 2.5x (4.0-6.0), 3.0x (> 6.0)
  - Surge multiplier cached in Redis: key `surge:{tenantId}:{gridCellId}`, TTL 60 seconds
  - Broadcast surge change events to `fare-events` Kafka topic when multiplier changes > 0.5x
- [ ] **WP-005-T04**: Implement promotions & discount system:
  - `Promotion` model: `{promotionId, tenantId, code, discountType (PERCENT/FIXED), discountValue, maxDiscount, minFare, usageLimit, perUserLimit, validFrom, validTo, status}`
  - `PromotionService.applyPromotion(String code, String riderId, String tenantId, BigDecimal fare)` → `DiscountResult`
  - Validate: code exists, not expired, usage limit not exceeded, per-user limit not exceeded, minFare satisfied
  - Atomically increment `usageCount` using MongoDB `findAndModify`
- [ ] **WP-005-T05**: Implement rate card management API:
  - `POST /api/v1/fares/rate-cards` — create rate card (tenant admin)
  - `GET /api/v1/fares/rate-cards` — list all rate cards for tenant
  - `PUT /api/v1/fares/rate-cards/{rateCardId}` — update (creates new DRAFT version)
  - `POST /api/v1/fares/rate-cards/{rateCardId}/activate` — activate DRAFT
  - `GET /api/v1/fares/estimate` — fare estimate (public; called by RHS)
  - `POST /api/v1/fares/calculate` — final fare calculation (internal; called by RHS on COMPLETED)
  - `POST /api/v1/fares/promotions` — create promotion
  - `POST /api/v1/fares/promotions/validate` — validate & reserve promotion
- [ ] **WP-005-T06**: Implement Kafka producer for `fare-events`:
  - `FareCalculatedEvent`, `SurgeActivatedEvent`, `SurgeDeactivatedEvent`, `PromotionAppliedEvent`
  - Partition key: `tenantId`
- [ ] **WP-005-T07**: Kafka consumer for `ride-events`:
  - Consume `TripCompletedEvent` → trigger final fare calculation → publish `FareCalculatedEvent`
  - Consumer group: `fpe-ride-consumer-group`
- [ ] **WP-005-T08**: Unit tests:
  - Fare formula test (base + distance + time)
  - Surge tier boundary tests (exact boundary values)
  - Promotion validation test (expired, usage exceeded, per-user limit)
  - Cap enforcement test (surge cap at 3.0x)

**Definition of Done**: Fare estimate API returns correct result within 200ms P95; surge multiplier updates reflected within 60 seconds; promotion code validates and applies correctly end-to-end.

---

## 6. Phase 3: Supporting Services

### WP-006: BMS — Billing & Subscription Management
**Goal**: Implement subscription lifecycle management, API/trip quota metering, and automated invoice generation. BMS consumes events from TMS, RHS, and PAY to maintain accurate metering records.

**Depends On**: WP-001, WP-002, WP-003, WP-004

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_BMS_Billing_Subscription.md`

**Functional Requirements**: FR-BMS-001 through FR-BMS-036

**Key Deliverables**:
- [ ] **WP-006-T01**: Implement `Subscription` domain model:
  - Fields: `subscriptionId` (UUID), `tenantId`, `plan` (STARTER/PROFESSIONAL/ENTERPRISE), `status` (ACTIVE/SUSPENDED/CANCELLED/PAST_DUE), `billingCycle` (MONTHLY/ANNUAL), `quota` (embedded: `tripsPerMonth`, `apiCallsPerMonth`, `activeVehicles`), `usage` (embedded: `tripsUsed`, `apiCallsUsed`), `currentPeriodStart`, `currentPeriodEnd`, `nextBillingDate`, `stripeCustomerId`
  - MongoDB collection: `subscriptions` with index on `{tenantId, status}`
- [ ] **WP-006-T02**: Implement quota enforcement (BL-006):
  - `QuotaService.checkAndIncrementQuota(String tenantId, QuotaType type)` → QuotaCheckResult
  - `QuotaType`: TRIP, API_CALL, VEHICLE_REGISTRATION
  - Redis counter: key `quota:{tenantId}:{type}:{periodYearMonth}`, TTL until end of billing period
  - If `usedCount >= limit` → return `QUOTA_EXCEEDED` (HTTP 429)
  - Atomic increment using Redis `INCR` command
  - Sync Redis counter to MongoDB every 5 minutes (scheduled task)
- [ ] **WP-006-T03**: Implement metering event consumer:
  - Consume `ride-events` (TripCompletedEvent → increment trip quota)
  - Consume `payment-events` (PaymentCompletedEvent → record revenue metering)
  - Consume `tenant-events` (TenantCreatedEvent → initialize subscription + quota counters)
  - Consumer group: `bms-event-consumer-group`
- [ ] **WP-006-T04**: Implement invoice generation:
  - `InvoiceService.generateMonthlyInvoice(String tenantId, YearMonth period)` → Invoice
  - Invoice items: subscription fee + overage charges (trips beyond quota @ 5000 VND/trip)
  - PDF generation via iText or Apache PDFBox
  - Invoice stored in MongoDB `invoices` collection + S3-compatible object storage
  - Trigger: scheduled task runs on 1st of each month at 00:00 UTC
- [ ] **WP-006-T05**: Implement subscription lifecycle API:
  - `POST /api/v1/billing/subscriptions` — create subscription (triggered by TMS Saga)
  - `GET /api/v1/billing/subscriptions/{tenantId}` — get current subscription
  - `POST /api/v1/billing/subscriptions/{tenantId}/upgrade` — upgrade plan
  - `POST /api/v1/billing/subscriptions/{tenantId}/cancel` — cancel at period end
  - `GET /api/v1/billing/subscriptions/{tenantId}/usage` — current usage vs quota
  - `GET /api/v1/billing/invoices?tenantId={tenantId}` — list invoices (paginated)
  - `GET /api/v1/billing/invoices/{invoiceId}/pdf` — download invoice PDF
- [ ] **WP-006-T06**: Implement Kafka producer for `billing-events` and `metering-events`:
  - `SubscriptionCreatedEvent`, `SubscriptionUpgradedEvent`, `QuotaExceededEvent`, `InvoiceGeneratedEvent`
  - `MeteringRecordedEvent` (to `metering-events` for ABI consumption)
  - Partition key: `tenantId`
- [ ] **WP-006-T07**: Unit + integration tests:
  - Quota enforcement test (at limit, beyond limit, reset on new period)
  - Invoice calculation test (base + overage)
  - Redis counter atomic increment test (concurrent requests)

**Definition of Done**: Quota enforcement blocks requests when exceeded; invoice PDF generated correctly; metering events published to Kafka and verifiable.

---

### WP-007: NCS — Notification & Communication Service
**Goal**: Implement multi-channel notification delivery (push, SMS, email, webhook) with strict <5-second SLA (BL-007), Dead Letter Queue (DLQ) handling, and HMAC webhook security. NCS is a pure consumer — it receives events from all other services.

**Depends On**: WP-001, WP-002, WP-004, WP-006 (needs events from all services)

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_NCS_Notification_Communication.md`

**Functional Requirements**: FR-NCS-001 through FR-NCS-031

**Key Deliverables**:
- [ ] **WP-007-T01**: Implement `NotificationTemplate` domain model:
  - Fields: `templateId` (UUID), `tenantId`, `channel` (PUSH/SMS/EMAIL/WEBHOOK), `eventType`, `language` (vi/en), `subject`, `bodyTemplate` (Mustache template string), `status` (ACTIVE/DRAFT)
  - MongoDB collection: `notification_templates`
  - Multi-language support: same `eventType` may have multiple templates (one per language)
- [ ] **WP-007-T02**: Implement multi-channel dispatcher:
  - `NotificationDispatcher.dispatch(NotificationRequest)` — routes to correct channel adapter
  - Adapters: `FCMAdapter` (push), `TwilioSMSAdapter` (SMS), `SendGridAdapter` (email), `WebhookAdapter` (HMAC-signed HTTP POST)
  - SLA enforcement: total dispatch time < 5 seconds (BL-007); circuit breaker per adapter
  - Timeout per adapter: FCM 2s, Twilio 3s, SendGrid 3s, Webhook 4s
- [ ] **WP-007-T03**: Implement DLQ handling:
  - On delivery failure (3 retries, exponential backoff: 1s, 2s, 4s) → publish to `notification-dlq` Kafka topic
  - DLQ consumer: retry failed notifications every 15 minutes (max 3 DLQ retries)
  - After 3 DLQ retries → mark notification as `PERMANENTLY_FAILED`, alert ops via PagerDuty webhook
  - DLQ monitoring dashboard query: `db.notification_logs.countDocuments({status:"PERMANENTLY_FAILED", tenantId: X})`
- [ ] **WP-007-T04**: Implement HMAC webhook security:
  - `WebhookAdapter.sign(String payload, String secretKey)` → HMAC-SHA256 signature
  - Add header: `X-Webhook-Signature: sha256={hex(HMAC-SHA256(secretKey, payload))}`
  - Per-tenant webhook secret stored in TMS, fetched via internal API call with caching (TTL 300s)
  - Tenant can rotate webhook secret via TMS API; old secret valid for 30 minutes after rotation
- [ ] **WP-007-T05**: Implement Kafka consumers (consumer group: `ncs-event-consumer-group`):
  - `ride-events` → `TripMatchedEvent` (notify rider of driver ETA), `TripCompletedEvent` (receipt notification), `TripCancelledEvent` (cancellation notice)
  - `payment-events` → `PaymentCompletedEvent` (payment receipt), `RefundInitiatedEvent` (refund status)
  - `billing-events` → `QuotaExceededEvent` (quota warning to tenant admin), `InvoiceGeneratedEvent` (invoice email)
  - `tenant-events` → `TenantActivatedEvent` (welcome email to tenant admin)
- [ ] **WP-007-T06**: Implement notification management API:
  - `POST /api/v1/notifications/templates` — create template
  - `GET /api/v1/notifications/templates?channel={channel}&eventType={type}` — list templates
  - `POST /api/v1/notifications/send` — send ad-hoc notification (admin use)
  - `GET /api/v1/notifications/logs?tenantId={tenantId}&status={status}` — delivery logs (paginated)
  - `POST /api/v1/notifications/webhooks` — register webhook endpoint
  - `POST /api/v1/notifications/webhooks/{webhookId}/rotate-secret` — rotate HMAC secret
- [ ] **WP-007-T07**: Unit + integration tests:
  - SLA test: mock slow adapter → verify dispatch completes within 5s or times out gracefully
  - DLQ flow test: simulate FCM failure → verify DLQ publication → verify retry
  - HMAC signature verification test
  - Multi-language template rendering test

**Definition of Done**: Notification delivered within 5 seconds in load test (P95); DLQ consumer correctly retries and marks permanently failed; HMAC signature verified by webhook endpoint.

---

## 7. Phase 4: Intelligence & Ecosystem

### WP-008: ABI — Analytics & Business Intelligence
**Goal**: Implement ETL pipeline consuming all Kafka event streams, KPI dashboard data APIs, and regulatory reporting with strict cross-tenant data isolation (BL-010).

**Depends On**: WP-001, WP-002, WP-004, WP-005, WP-006, WP-007 (needs all event producers live)

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_ABI_Analytics_BI.md`

**Functional Requirements**: FR-ABI-001 through FR-ABI-029

**Key Deliverables**:
- [ ] **WP-008-T01**: Implement ETL pipeline (Kafka Streams or Spring Kafka consumer):
  - Consume all 7 Kafka topics with consumer group `abi-analytics-consumer-group`
  - Transform raw events → `AnalyticsRecord` (normalized schema)
  - Write to `analytics_facts` MongoDB collection (append-only, indexed by `tenantId + eventType + timestamp`)
  - Deduplication: use `eventId` as idempotency key; skip duplicates
- [ ] **WP-008-T02**: Implement KPI computation (scheduled, every 5 minutes):
  - `KPIComputationJob` — Spring `@Scheduled` task
  - KPIs per tenant: `totalTrips`, `completedTrips`, `cancelledTrips`, `totalRevenue`, `averageFare`, `activeDrivers`, `activeRiders`, `averageRating`, `p95TripDuration`
  - Store computed KPIs in `kpi_snapshots` collection: `{tenantId, computedAt, kpis: {}}`
  - MUST enforce BL-010: `db.kpi_snapshots.find({tenantId: {$eq: requestingTenantId}})` — no cross-tenant query allowed
- [ ] **WP-008-T03**: Implement regulatory reporting:
  - `RegulatoryReportService.generateReport(String tenantId, ReportType type, DateRange range)` → Report
  - Report types: TRIP_SUMMARY, REVENUE_SUMMARY, DRIVER_ACTIVITY, RIDER_ACTIVITY, PAYMENT_RECONCILIATION
  - Format: JSON (API) + CSV (download)
  - BL-010 enforcement: every report query MUST include `{tenantId: requestingTenantId}` filter — audited
- [ ] **WP-008-T04**: Implement analytics API:
  - `GET /api/v1/analytics/kpis?tenantId={tenantId}&period={DAILY|WEEKLY|MONTHLY}` — KPI dashboard data
  - `GET /api/v1/analytics/trips/trends?tenantId={tenantId}&from={date}&to={date}` — trip trend (hourly buckets)
  - `GET /api/v1/analytics/revenue/breakdown?tenantId={tenantId}&period={period}` — revenue by vehicle type / zone
  - `POST /api/v1/analytics/reports` — generate regulatory report
  - `GET /api/v1/analytics/reports/{reportId}/download` — download as CSV
  - All endpoints: `X-Tenant-ID` header mandatory; response limited to requesting tenant's data only
- [ ] **WP-008-T05**: Unit + integration tests:
  - KPI computation test (feed mock events → verify KPI values)
  - Cross-tenant isolation test (verify tenant A cannot see tenant B data via API)
  - Report generation test (verify CSV output correctness)

**Definition of Done**: KPI dashboard API returns correct aggregates within 200ms P95; regulatory report CSV matches expected values from test dataset; cross-tenant isolation verified by security test.

---

### WP-009: MKP — Marketplace Service
**Goal**: Implement third-party partner/plugin marketplace with partner lifecycle management, admin audit gate (BL-009), and revenue share tracking.

**Depends On**: WP-001, WP-002, WP-003 (revenue share via PAY), WP-008 (analytics for partner performance)

**Assigned Agent**: Java Backend Developer

**SRS Reference**: `project-documentation/srs/SRS_MKP_Marketplace.md`

**Functional Requirements**: FR-MKP-001 through FR-MKP-032

**Key Deliverables**:
- [ ] **WP-009-T01**: Implement `Partner` domain model:
  - Fields: `partnerId` (UUID), `tenantId`, `name`, `type` (FLEET_PROVIDER/INSURANCE/PAYMENT_GATEWAY/ANALYTICS/OTHER), `status` (PENDING_REVIEW/APPROVED/SUSPENDED/REJECTED), `apiKey` (hashed SHA-256), `webhookUrl`, `revenueSharePercent` (BigDecimal 0-100), `auditLog` (List<AuditEntry>), `createdAt`, `approvedAt`, `approvedBy`
  - MongoDB collection: `partners` with index `{tenantId, status}`
- [ ] **WP-009-T02**: Implement admin audit gate (BL-009):
  - `PartnerAuditService.submitForReview(String partnerId, String tenantId)` → triggers review workflow
  - Review workflow: partner submits documents → admin reviews → APPROVED or REJECTED with reason
  - ALL status changes recorded in immutable `auditLog` array (append-only via `$push`)
  - Approval requires admin JWT token with `ROLE_MARKETPLACE_ADMIN` claim
  - Rejection reason mandatory (min 10 characters)
- [ ] **WP-009-T03**: Implement partner lifecycle API:
  - `POST /api/v1/marketplace/partners` — register partner (returns PENDING_REVIEW status)
  - `GET /api/v1/marketplace/partners/{partnerId}` — get partner details
  - `POST /api/v1/marketplace/partners/{partnerId}/submit-review` — submit docs for admin review
  - `POST /api/v1/marketplace/partners/{partnerId}/approve` — admin approves (ROLE_MARKETPLACE_ADMIN)
  - `POST /api/v1/marketplace/partners/{partnerId}/reject` — admin rejects with reason
  - `POST /api/v1/marketplace/partners/{partnerId}/suspend` — suspend active partner
  - `GET /api/v1/marketplace/partners?tenantId={tenantId}&status={status}` — list partners
  - `GET /api/v1/marketplace/partners/{partnerId}/audit-log` — get full audit trail
- [ ] **WP-009-T04**: Implement revenue share tracking:
  - `RevenueShareService.calculateShare(String partnerId, BigDecimal transactionAmount)` → BigDecimal
  - Consume `payment-events` (PaymentCompletedEvent) → calculate partner revenue share → create `revenue_share_records` document
  - Monthly reconciliation job: aggregate `revenue_share_records` → generate payout request via PAY
  - `GET /api/v1/marketplace/partners/{partnerId}/revenue?period={YYYY-MM}` — revenue share report
- [ ] **WP-009-T05**: Implement partner API key management:
  - API key generation: UUID v4 → SHA-256 hash stored in DB; plain key returned once at creation
  - `PartnerAuthFilter` — validates `X-Partner-API-Key` header for partner-facing endpoints
  - Rate limiting: 100 req/min per API key (Kong plugin)
- [ ] **WP-009-T06**: Unit + integration tests:
  - Audit gate test: partner cannot self-approve; only admin can approve
  - Revenue share calculation test
  - API key validation test
  - Status machine transitions test (PENDING_REVIEW → APPROVED, PENDING_REVIEW → REJECTED)

**Definition of Done**: Partner audit trail complete and immutable; revenue share calculated correctly; admin audit gate prevents unauthorized status changes.

---

## 8. Phase 5: Cross-Cutting Hardening & Validation

### WP-010: Observability Stack
**Goal**: Implement full observability (distributed tracing, metrics, logging) across all 8 services.

**Depends On**: WP-002 through WP-009 (all services must be running)

**Assigned Agent**: DevOps Engineer

**Key Deliverables**:
- [ ] **WP-010-T01**: Implement distributed tracing with OpenTelemetry:
  - Add `spring-boot-starter-actuator` + `opentelemetry-spring-boot-starter` to all services
  - Configure OTLP exporter → Jaeger collector at `http://jaeger-collector:4317`
  - Trace context propagation: inject `traceId` + `spanId` into all Kafka message headers
  - Inject `traceId` into all API response headers (`X-Trace-ID`)
  - Inject `traceId` + `tenantId` into all log entries (MDC)
- [ ] **WP-010-T02**: Implement Prometheus metrics:
  - Expose `/actuator/prometheus` on all services (internal port 9090)
  - Custom metrics per service:
    - RHS: `rhs_trips_total`, `rhs_matching_duration_seconds`, `rhs_active_trips_gauge`
    - PAY: `pay_transactions_total`, `pay_gateway_errors_total`, `pay_escrow_amount_gauge`
    - FPE: `fpe_fare_calculations_total`, `fpe_surge_multiplier_gauge` (per tenant)
    - NCS: `ncs_notifications_sent_total`, `ncs_delivery_sla_breach_total`, `ncs_dlq_size_gauge`
  - Configure Prometheus scrape intervals: 15s for all services
- [ ] **WP-010-T03**: Configure Grafana dashboards:
  - Platform Overview dashboard: total trips/min, revenue/hr, active tenants, error rate
  - Per-service dashboards: RED metrics (Rate, Errors, Duration)
  - SLA breach alerting: NCS delivery > 5s → PagerDuty alert (BL-007)
  - Kafka consumer lag alerting: lag > 10,000 → alert
- [ ] **WP-010-T04**: Centralized logging:
  - JSON structured log format: `{timestamp, level, service, tenantId, traceId, spanId, message, context}`
  - Configure Logback → Fluent Bit → Elasticsearch
  - Log retention: 30 days (hot), 90 days (warm), 365 days (cold/S3)
  - Alert on ERROR rate > 5/min per service per tenant

**Definition of Done**: Jaeger shows cross-service trace for trip lifecycle; Prometheus metrics confirmed for all 8 services; SLA breach alert fires correctly in test.

---

### WP-011: Integration Testing Suite
**Goal**: End-to-end integration tests covering complete business workflows across all 8 services.

**Depends On**: WP-002 through WP-010

**Assigned Agent**: Java Backend Developer + DevOps

**Key Deliverables**:
- [ ] **WP-011-T01**: Complete trip lifecycle E2E test:
  - Request trip → AV match → confirm → start → complete → fare finalized (FPE) → escrow released (PAY) → notification sent (NCS) → billing metered (BMS) → analytics recorded (ABI)
  - Assert each step via API calls; verify Kafka events via consumer assertions
- [ ] **WP-011-T02**: TMS onboarding Saga E2E test:
  - Happy path: create tenant → Saga completes → all 4 steps confirmed
  - Failure path: simulate DPE failure → verify rollback chain → tenant in FAILED state → no orphaned records
- [ ] **WP-011-T03**: Quota enforcement E2E test:
  - Create tenant with STARTER plan (100 trips/month quota)
  - Complete 100 trips → verify 101st trip blocked by BMS with HTTP 429
- [ ] **WP-011-T04**: Cross-tenant isolation test:
  - Create 2 tenants with trips and data
  - Verify tenant A cannot query tenant B data via any API
  - Verify ABI reports for tenant A contain no tenant B records
- [ ] **WP-011-T05**: Payment failure + retry test:
  - Simulate gateway failure → verify circuit breaker opens → verify fallback gateway used
  - Verify idempotency: duplicate payment request with same `Idempotency-Key` → no duplicate charge

**Definition of Done**: All 5 integration test scenarios pass in CI pipeline; no cross-tenant data leakage detected.

---

### WP-012: Performance & Load Testing
**Goal**: Validate all NFR targets under simulated production load.

**Depends On**: WP-011

**Assigned Agent**: DevOps Engineer + Performance Engineer

**NFR Targets to Validate**:
- P95 Read < 200ms
- P95 Write < 500ms
- ≥ 10,000 concurrent trips
- ≥ 50,000 req/s
- ≥ 100,000 Kafka events/s

**Key Deliverables**:
- [ ] **WP-012-T01**: Load test RHS with k6/Gatling:
  - Ramp: 0 → 10,000 concurrent trip requests over 10 minutes
  - Assert: P95 response < 500ms, error rate < 0.1%
  - Record: Kafka `ride-events` throughput during peak load
- [ ] **WP-012-T02**: Load test PAY with k6:
  - 5,000 concurrent payment initiations with unique idempotency keys
  - Assert: P95 < 500ms; no duplicate charges (verify via DB count)
- [ ] **WP-012-T03**: Kafka throughput test:
  - Produce 100,000 events/second across all topics for 5 minutes
  - Assert: consumer lag < 30 seconds for all consumer groups
- [ ] **WP-012-T04**: NCS SLA validation:
  - Trigger 1,000 notifications simultaneously
  - Assert: 99% delivered within 5 seconds (BL-007)
- [ ] **WP-012-T05**: MongoDB query performance:
  - Assert: P95 < 200ms for all read queries with explain plan showing `IXSCAN`
  - Assert: no COLLSCAN in any production query path

**Definition of Done**: All NFR targets met; load test reports archived as artifacts.

---

### WP-013: PCI-DSS Compliance Audit & Security Hardening
**Goal**: Validate PCI-DSS compliance for PAY service, security hardening for all services.

**Depends On**: WP-011

**Assigned Agent**: Security Auditor + DevOps

**Key Deliverables**:
- [ ] **WP-013-T01**: PAY PCI-DSS validation:
  - Verify `payment_transactions` MongoDB INSERT-only validator is active (attempt UPDATE → must fail)
  - Verify `pay-namespace` NetworkPolicy blocks all ingress except Kong
  - Verify no PAN (card number) data stored in plain text (all hashed/tokenized)
  - Verify audit log is append-only and includes `userId`, `action`, `timestamp`, `ipAddress`
- [ ] **WP-013-T02**: OWASP Top 10 security validation:
  - SQL/NoSQL injection test on all API endpoints
  - JWT token validation test (expired, invalid signature, missing claims)
  - Rate limiting test (exceed Kong rate limit → HTTP 429)
  - HMAC signature bypass test (NCS webhooks)
- [ ] **WP-013-T03**: Dependency vulnerability scan:
  - Run OWASP Dependency Check on all 8 service `pom.xml`
  - Assert: no HIGH or CRITICAL CVEs in production dependencies
  - Generate vulnerability report as CI artifact
- [ ] **WP-013-T04**: Secrets management audit:
  - Verify no secrets in `application.yml` files (all via Kubernetes Secrets or Vault)
  - Verify all DB passwords, API keys, JWT secrets are in K8s Secret objects
  - Verify Kong JWT secrets are not logged

**Definition of Done**: PCI-DSS checklist 100% passed; OWASP Top 10 test clean; no HIGH/CRITICAL CVEs; secrets audit passed.

---

## 9. Dependency & Risk Map

| WP ID | Name | Depends On | Risk | Mitigation |
|-------|------|------------|------|------------|
| WP-001 | Foundation Infrastructure | None | Kafka/MongoDB misconfiguration blocks all services | Use Terraform IaC; validate with integration smoke tests before Phase 2 |
| WP-002 | TMS | WP-001 | Saga Saga rollback failure leaves orphaned records | Implement saga state recovery job; unit test all rollback paths |
| WP-003 | PAY | WP-001, WP-002 | PCI-DSS compliance gap | Engage security auditor early; implement INSERT-only validator in WP-001 |
| WP-004 | RHS | WP-001, WP-002, WP-003, WP-005 | AV matching latency spikes | Index 2dsphere on pickupLocation; cache surge in Redis |
| WP-005 | FPE | WP-001, WP-002 | Fare calculation divergence from rider expectations | Implement fare breakdown in response; A/B test surge thresholds |
| WP-006 | BMS | WP-001, WP-002, WP-003, WP-004 | Quota counter drift (Redis vs MongoDB) | 5-minute sync job + reconciliation alert if drift > 5% |
| WP-007 | NCS | WP-001, WP-002, WP-004, WP-006 | BL-007 SLA breach (>5s delivery) | Circuit breaker per adapter; DLQ retry mechanism; SLA monitoring alert |
| WP-008 | ABI | WP-001 through WP-007 | Cross-tenant data leakage (BL-010) | Mandatory tenantId filter in all queries; automated cross-tenant isolation test |
| WP-009 | MKP | WP-001, WP-002, WP-003, WP-008 | Unauthorized partner approval (BL-009) | Audit gate enforced at service layer; admin-only RBAC role; immutable audit log |
| WP-010 | Observability | WP-002–WP-009 | Missing SLA breach alerts | Alert rules tested in staging before production |
| WP-011 | Integration Tests | WP-002–WP-010 | Test environment drift from production | Use Docker Compose for test infra; mirror production Kafka topic config |
| WP-012 | Performance | WP-011 | NFR targets not met under real load | Load test per WP as it's delivered; don't wait for Phase 5 |
| WP-013 | PCI-DSS Audit | WP-011 | Security vulnerabilities discovered late | Run OWASP scan in CI from WP-003 onwards |

---

## 10. Execution Sequence (Gantt Summary)

```
Week 1-2:   WP-001 (Foundation Infrastructure — ALL services blocked until complete)
Week 3-4:   WP-002 (TMS) + WP-005 (FPE) [parallel — independent]
Week 5-6:   WP-003 (PAY) [requires WP-002]
Week 7-9:   WP-004 (RHS) [requires WP-002, WP-003, WP-005]
Week 10-11: WP-006 (BMS) [requires WP-004]
Week 12-13: WP-007 (NCS) [requires WP-006]
Week 14-15: WP-008 (ABI) [requires WP-007]
Week 16-17: WP-009 (MKP) [requires WP-003, WP-008]
Week 18:    WP-010 (Observability)
Week 19:    WP-011 (Integration Tests)
Week 20:    WP-012 (Performance Tests)
Week 21:    WP-013 (PCI-DSS Audit)
```

---

## 11. Resource Allocation

| Role | Assigned WPs | Skills Required |
|------|-------------|----------------|
| **Lead Orchestrator (PM/BA)** | All WPs — oversight & sync | Project management, SDLC orchestration |
| **Solutions Architect** | WP-001, WP-010 (design review for all WPs) | Java/Spring Boot 3, MongoDB, Kafka, K8s |
| **Java Backend Developer #1** | WP-002 (TMS), WP-006 (BMS) | Spring Boot 3, MongoDB, Kafka, Saga patterns |
| **Java Backend Developer #2** | WP-003 (PAY), WP-009 (MKP) | Spring Boot 3, PCI-DSS, Redis, Circuit Breaker |
| **Java Backend Developer #3** | WP-004 (RHS), WP-007 (NCS) | Spring Boot 3, NATS, geospatial queries, DLQ |
| **Java Backend Developer #4** | WP-005 (FPE), WP-008 (ABI) | Spring Boot 3, Kafka Streams, surge algorithms |
| **DevOps Engineer** | WP-001, WP-010, WP-011, WP-012 | K8s, Kafka, MongoDB ops, Prometheus, Grafana |
| **Security Auditor** | WP-013 (+ review WP-003) | PCI-DSS, OWASP, penetration testing |
| **Expert Code Reviewer** | All WPs — gate before MASTER_PLAN sync | Java best practices, Clean Architecture |

---

## 12. Definition of Done (Global)

A Work Package is considered **DONE** only when ALL of the following are true:
1. ✅ All tasks in the corresponding `DETAIL_PLAN_<Service>.md` are marked `[x]`
2. ✅ Unit test coverage ≥ 80% (verified by JaCoCo report)
3. ✅ Expert Code Reviewer has approved (`APPROVED` status in review log)
4. ✅ Service passes health check in staging Kubernetes namespace
5. ✅ Kafka events published and consumed correctly (verified by consumer assertion test)
6. ✅ All BL rules specific to the service are enforced (verified by targeted tests)
7. ✅ API documentation (OpenAPI 3.0) is published at `/api/v1/swagger-ui.html`

---

## 13. Phase 5 Deliverable Index (Detail Plans)

The following `DETAIL_PLAN_*.md` files will be generated in Phase 5 (`/plan-detail`):

| File | Work Package | Service |
|------|-------------|---------|
| `project-documentation/plans/DETAIL_PLAN_TMS.md` | WP-002 | Tenant Management Service |
| `project-documentation/plans/DETAIL_PLAN_PAY.md` | WP-003 | Payment Processing Service |
| `project-documentation/plans/DETAIL_PLAN_RHS.md` | WP-004 | Ride Hailing Service |
| `project-documentation/plans/DETAIL_PLAN_FPE.md` | WP-005 | Fare Pricing Engine |
| `project-documentation/plans/DETAIL_PLAN_BMS.md` | WP-006 | Billing & Subscription |
| `project-documentation/plans/DETAIL_PLAN_NCS.md` | WP-007 | Notification & Communication |
| `project-documentation/plans/DETAIL_PLAN_ABI.md` | WP-008 | Analytics & BI |
| `project-documentation/plans/DETAIL_PLAN_MKP.md` | WP-009 | Marketplace |

---

## 14. Change Management Protocol

All changes to scope MUST follow this cascade:
1. **Update PRD.md** — add/modify functional requirement
2. **Update ARCHITECTURE_SPEC.md** — modify affected components
3. **Update MASTER_PLAN.md** — add new WP or modify existing tasks
4. **Update/Create DETAIL_PLAN_*.md** — add atomic tasks
5. **Run** `python .github/skills/expert-pm-ba-orchestrator/scripts/analyze_impact.py "<CR description>"` — impact analysis
6. **Document** change in `OVERVIEW.md` Decision Log

---

*Generated by: Expert PM/BA Orchestrator | VNPT AV Platform — Services Provider Group*
*Next Phase: `/plan-detail` — Generate DETAIL_PLAN_*.md for each of the 8 services*
