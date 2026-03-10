# DETAIL PLAN — TMS: Tenant Management Service

**Work Package**: WP-002 | **SRS**: SRS_TMS_Tenant_Organization.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.tms`  
**Database**: MongoDB (`tms_db`) + Redis + Kafka  
**External**: Keycloak v26+, Twilio, MinIO  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-TMS-001 | Tenant domain model + MongoDB document | Domain Models | 1.5h |
| TASK-TMS-002 | Rider domain model + MongoDB document | Domain Models | 1h |
| TASK-TMS-003 | OnboardingSaga domain model | Domain Models | 1h |
| TASK-TMS-004 | TenantBranding embedded document | Domain Models | 1h |
| TASK-TMS-005 | TenantRepository interface + BaseMongoImpl | Repository Layer | 2h |
| TASK-TMS-006 | RiderRepository interface + impl | Repository Layer | 1.5h |
| TASK-TMS-007 | OnboardingSagaRepository interface + impl | Repository Layer | 1.5h |
| TASK-TMS-008 | TenantContextFilter (OncePerRequestFilter) | Security | 2h |
| TASK-TMS-009 | TenantContextHolder (ThreadLocal) | Security | 1h |
| TASK-TMS-010 | KeycloakAdapter (realm management) | Adapters | 2h |
| TASK-TMS-011 | TwilioAdapter (OTP SMS dispatch) | Adapters | 1.5h |
| TASK-TMS-012 | MinIOAdapter (logo upload) | Adapters | 1.5h |
| TASK-TMS-013 | SagaStepAdapter interfaces (SSC, BMS, DPE, VMS) | Adapters | 2h |
| TASK-TMS-014 | TenantService interface + impl (CRUD) | Service Layer | 2h |
| TASK-TMS-015 | OnboardingSagaService (orchestrator) | Service Layer | 2h |
| TASK-TMS-016 | OnboardingSagaCompensation (rollback chain) | Service Layer | 2h |
| TASK-TMS-017 | FeatureFlagService (Redis-backed) | Service Layer | 1.5h |
| TASK-TMS-018 | BrandingService (logo upload + CDN URL) | Service Layer | 1.5h |
| TASK-TMS-019 | RiderIdentityService (register + OAuth) | Service Layer | 2h |
| TASK-TMS-020 | OTPService (generate, verify, lock) | Service Layer | 2h |
| TASK-TMS-021 | TenantKafkaProducer (tenant-events topic) | Kafka | 1.5h |
| TASK-TMS-022 | TenantController (CRUD REST API) | Controllers | 2h |
| TASK-TMS-023 | TenantBrandingController | Controllers | 1.5h |
| TASK-TMS-024 | TenantConfigController (feature flags) | Controllers | 1h |
| TASK-TMS-025 | RiderController (register, verify, profile) | Controllers | 2h |
| TASK-TMS-026 | GlobalExceptionHandler | Controllers | 1h |
| TASK-TMS-027 | MongoConfig (indexes, validators) | Config | 1h |
| TASK-TMS-028 | RedisConfig (TTL defaults) | Config | 1h |
| TASK-TMS-029 | SecurityConfig (Spring Security + Keycloak JWT) | Config | 2h |
| TASK-TMS-030 | KafkaProducerConfig | Config | 1h |
| TASK-TMS-031 | Unit tests: TenantService | Tests | 2h |
| TASK-TMS-032 | Unit tests: OnboardingSagaService (happy path + rollback) | Tests | 2h |
| TASK-TMS-033 | Unit tests: OTPService (lock, expiry, resend limits) | Tests | 1.5h |
| TASK-TMS-034 | Integration tests: Tenant CRUD APIs | Tests | 2h |
| TASK-TMS-035 | Integration tests: Rider registration + OTP flow | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-TMS-001: Tenant Domain Model

**Parent WP Task**: WP-002-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/models/Tenant.java`
- `src/main/java/com/vnpt/avplatform/tms/models/TenantStatus.java`

**Specification**:
```java
// TenantStatus.java
package com.vnpt.avplatform.tms.models;

public enum TenantStatus {
    ONBOARDING, ACTIVE, SUSPENDED, TERMINATED
}

// Tenant.java
package com.vnpt.avplatform.tms.models;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Version;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import jakarta.validation.constraints.*;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Document(collection = "tenants")
public class Tenant {
    @Id
    private String id;

    @Field("tenant_id")
    @Indexed(unique = true)
    private String tenantId = UUID.randomUUID().toString();

    @Field("company_name")
    @NotBlank
    @Size(min = 2, max = 200)
    private String companyName;

    @Field("company_domain")
    @NotBlank
    @Pattern(regexp = "^[a-z0-9][a-z0-9\\-]{0,61}[a-z0-9]\\.[a-z]{2,}$")
    @Indexed(unique = true)
    private String companyDomain;

    @Field("country_code")
    @NotBlank
    @Pattern(regexp = "^[A-Z]{2}$")
    private String countryCode;

    @Field("timezone")
    @NotBlank
    private String timezone; // IANA: e.g., "Asia/Ho_Chi_Minh"

    @Field("status")
    private TenantStatus status = TenantStatus.ONBOARDING;

    @Field("plan_id")
    private String planId;

    @Field("subscription_id")
    private String subscriptionId;

    @Field("admin_user_id")
    private String adminUserId;

    @Field("branding")
    private TenantBranding branding = new TenantBranding();

    @Field("surge_cap")
    @DecimalMin("1.0")
    @DecimalMax("3.0")
    private Double surgeCap = 3.0;

    @Field("feature_flags")
    private Map<String, Boolean> featureFlags = new java.util.HashMap<>();

    @Field("config")
    private Map<String, Object> config = new java.util.HashMap<>();

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Field("updated_at")
    private Instant updatedAt = Instant.now();

    @Version
    private Long version;

    // Getters and setters (all fields)
}
```

**Definition of Done**:
- [ ] `Tenant.java` compiles without errors with all annotations applied
- [ ] `TenantStatus.java` has exactly 4 values: ONBOARDING, ACTIVE, SUSPENDED, TERMINATED
- [ ] `@Indexed(unique = true)` on both `tenantId` and `companyDomain`
- [ ] `@Version` field present for optimistic locking
- [ ] All fields have matching getters/setters

---

### TASK-TMS-002: Rider Domain Model

**Parent WP Task**: WP-002-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/models/Rider.java`
- `src/main/java/com/vnpt/avplatform/tms/models/AuthProvider.java`
- `src/main/java/com/vnpt/avplatform/tms/models/RiderStatus.java`

**Specification**:
```java
// AuthProvider.java
public enum AuthProvider { EMAIL, GOOGLE, APPLE }

// RiderStatus.java
public enum RiderStatus { PENDING_VERIFICATION, ACTIVE, SUSPENDED }

// Rider.java
@Document(collection = "riders")
public class Rider {
    @Id private String id;

    @Field("rider_id")
    @Indexed(unique = true)
    private String riderId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001: mandatory

    @Field("keycloak_sub")
    @Indexed(unique = true, sparse = true)
    private String keycloakSub;

    @Field("email")
    @Email
    @Indexed
    private String email;

    @Field("phone_number")
    @Pattern(regexp = "^\\+[1-9]\\d{7,14}$") // E.164
    private String phoneNumber;

    @Field("auth_provider")
    private AuthProvider authProvider;

    @Field("wallet_id")
    private String walletId;

    @Field("status")
    private RiderStatus status = RiderStatus.PENDING_VERIFICATION;

    @Field("phone_verified")
    private boolean phoneVerified = false;

    @Field("email_verified")
    private boolean emailVerified = false;

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Field("updated_at")
    private Instant updatedAt = Instant.now();
}
```

**Definition of Done**:
- [ ] `Rider.java` compiles with `@Document(collection = "riders")`
- [ ] `tenantId` field has `@Indexed` annotation (BL-001)
- [ ] Phone regex `^\\+[1-9]\\d{7,14}$` applied via `@Pattern`
- [ ] `@Email` on email field
- [ ] `keycloakSub` has `sparse = true` index (null for non-Keycloak riders)

---

### TASK-TMS-003: OnboardingSaga Domain Model

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/models/OnboardingSaga.java`
- `src/main/java/com/vnpt/avplatform/tms/models/SagaStep.java`
- `src/main/java/com/vnpt/avplatform/tms/models/SagaStatus.java`

**Specification**:
```java
// SagaStatus.java
public enum SagaStatus { PENDING, IN_PROGRESS, COMPLETED, FAILED, COMPENSATING, COMPENSATED }

// SagaStep.java — embedded document
public class SagaStep {
    private String stepName;     // "SSC" | "BMS" | "DPE" | "VMS"
    private String status;       // "PENDING" | "COMPLETED" | "FAILED" | "COMPENSATED"
    private String externalRef;  // ID returned by external service
    private Instant completedAt;
    private String errorMessage;
}

// OnboardingSaga.java
@Document(collection = "onboarding_sagas")
public class OnboardingSaga {
    @Id private String id;

    @Field("saga_id")
    @Indexed(unique = true)
    private String sagaId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed(unique = true) // one saga per tenant
    @NotBlank
    private String tenantId;

    @Field("status")
    private SagaStatus status = SagaStatus.PENDING;

    @Field("steps")
    private List<SagaStep> steps = new ArrayList<>();
    // steps ordered: index 0=SSC, 1=BMS, 2=DPE, 3=VMS

    @Field("current_step_index")
    private int currentStepIndex = 0;

    @Field("compensation_log")
    private List<String> compensationLog = new ArrayList<>();

    @Field("started_at")
    private Instant startedAt = Instant.now();

    @Field("completed_at")
    private Instant completedAt;

    @Field("failed_at")
    private Instant failedAt;

    @Field("total_timeout_seconds")
    private int totalTimeoutSeconds = 120; // BL-011: 120s total

    @Field("per_step_timeout_seconds")
    private int perStepTimeoutSeconds = 30; // 30s per step
}
```

**Definition of Done**:
- [ ] `OnboardingSaga.java` compiles with `@Document(collection = "onboarding_sagas")`
- [ ] `steps` list contains exactly 4 SagaStep entries when initialized
- [ ] `tenantId` has `@Indexed(unique = true)` — one saga per tenant
- [ ] Timeout constants: 120s total, 30s per step

---

### TASK-TMS-004: TenantBranding Embedded Document

**Parent WP Task**: WP-002-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/models/TenantBranding.java`

**Specification**:
```java
// TenantBranding.java
public class TenantBranding {
    @Field("logo_url")
    private String logoUrl; // MinIO CDN URL

    @Field("primary_color")
    @Pattern(regexp = "^#[0-9A-Fa-f]{6}$") // #RRGGBB
    private String primaryColor = "#1976D2";

    @Field("secondary_color")
    @Pattern(regexp = "^#[0-9A-Fa-f]{6}$")
    private String secondaryColor = "#424242";

    @Field("custom_domain")
    private String customDomain; // e.g., "app.customer.com"

    @Field("custom_domain_verified")
    private boolean customDomainVerified = false;

    @Field("custom_domain_txt_record")
    private String customDomainTxtRecord; // generated TXT record for DNS verification
}
```

**Definition of Done**:
- [ ] Color fields have `^#[0-9A-Fa-f]{6}$` regex validation
- [ ] Default primary color `#1976D2` (Material Blue)
- [ ] `customDomainVerified` defaults to `false`

---

## Task Group 2: Repository Layer

### TASK-TMS-005: TenantRepository (interface + implementation)

**Parent WP Task**: WP-002-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/repositories/TenantRepository.java`
- `src/main/java/com/vnpt/avplatform/tms/repositories/impl/TenantRepositoryImpl.java`

**Specification**:
```java
// TenantRepository.java
package com.vnpt.avplatform.tms.repositories;

import java.util.Optional;
import java.util.List;

public interface TenantRepository {
    Tenant save(Tenant tenant);
    Optional<Tenant> findByTenantId(String tenantId);
    Optional<Tenant> findByCompanyDomain(String companyDomain);
    List<Tenant> findAll(int page, int size); // paginated
    long count();
    boolean existsByTenantId(String tenantId);
    boolean existsByCompanyDomain(String companyDomain);
    Tenant updateStatus(String tenantId, TenantStatus status);
    Tenant updateBranding(String tenantId, TenantBranding branding);
    Tenant updateFeatureFlags(String tenantId, Map<String, Boolean> flags);
}

// TenantRepositoryImpl.java — uses MongoTemplate (NOT MongoRepository)
// REASON: Need explicit tenant_id filter in all queries (BL-001)
@Repository
public class TenantRepositoryImpl implements TenantRepository {
    private final MongoTemplate mongoTemplate;

    // findByTenantId uses:
    // Query query = Query.query(Criteria.where("tenant_id").is(tenantId));
    // return Optional.ofNullable(mongoTemplate.findOne(query, Tenant.class));

    // save uses:
    // return mongoTemplate.save(tenant); // creates or updates by _id

    // updateStatus uses:
    // Update update = new Update()
    //     .set("status", status)
    //     .set("updated_at", Instant.now());
    // mongoTemplate.updateFirst(
    //     Query.query(Criteria.where("tenant_id").is(tenantId)),
    //     update, Tenant.class
    // );
    // Then fetch and return updated document

    // findAll uses:
    // Query query = new Query().skip((long) page * size).limit(size);
    // return mongoTemplate.find(query, Tenant.class);
}
```

**Definition of Done**:
- [ ] `TenantRepository` interface has all 9 method signatures
- [ ] `TenantRepositoryImpl` uses `MongoTemplate` (not Spring Data auto-repository)
- [ ] All queries use `Criteria.where("tenant_id").is(tenantId)` pattern
- [ ] `updateStatus` sets `updated_at = Instant.now()`
- [ ] `TenantRepositoryImplTest` mocks MongoTemplate and tests all methods

---

### TASK-TMS-006: RiderRepository (interface + implementation)

**Parent WP Task**: WP-002-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/repositories/RiderRepository.java`
- `src/main/java/com/vnpt/avplatform/tms/repositories/impl/RiderRepositoryImpl.java`

**Specification**:
```java
// RiderRepository.java
public interface RiderRepository {
    Rider save(Rider rider);
    Optional<Rider> findByRiderId(String riderId);
    Optional<Rider> findByEmailAndTenantId(String email, String tenantId);
    Optional<Rider> findByPhoneNumberAndTenantId(String phone, String tenantId);
    Optional<Rider> findByKeycloakSub(String keycloakSub);
    Rider updateStatus(String riderId, RiderStatus status);
    boolean existsByEmailAndTenantId(String email, String tenantId);
}

// RiderRepositoryImpl.java — ALL queries include tenant_id in Criteria (BL-001)
// findByEmailAndTenantId:
//   Criteria.where("email").is(email).and("tenant_id").is(tenantId)
// findByRiderId: always use rider_id field
```

**Definition of Done**:
- [ ] `findByEmailAndTenantId` includes `tenant_id` in query criteria
- [ ] `findByPhoneNumberAndTenantId` includes `tenant_id` in query criteria
- [ ] `findByKeycloakSub` uses `sparse = true` indexed field
- [ ] Unit test verifies tenant_id is always included in MongoDB query Criteria

---

### TASK-TMS-007: OnboardingSagaRepository

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/repositories/OnboardingSagaRepository.java`
- `src/main/java/com/vnpt/avplatform/tms/repositories/impl/OnboardingSagaRepositoryImpl.java`

**Specification**:
```java
public interface OnboardingSagaRepository {
    OnboardingSaga save(OnboardingSaga saga);
    Optional<OnboardingSaga> findBySagaId(String sagaId);
    Optional<OnboardingSaga> findByTenantId(String tenantId);
    OnboardingSaga updateStatus(String sagaId, SagaStatus status);
    OnboardingSaga updateStepStatus(String sagaId, int stepIndex, String stepStatus, String externalRef);
    OnboardingSaga appendCompensationLog(String sagaId, String logEntry);
    OnboardingSaga markCompleted(String sagaId);
    OnboardingSaga markFailed(String sagaId, String reason);
}
```

**Definition of Done**:
- [ ] `updateStepStatus` uses `$set steps.{stepIndex}.status` MongoDB array positional update
- [ ] `appendCompensationLog` uses `$push compensation_log` MongoDB operator
- [ ] All methods handle `OptimisticLockingFailureException` from `@Version` field

---

## Task Group 3: Security

### TASK-TMS-008: TenantContextFilter (Spring Security OncePerRequestFilter)

**Parent WP Task**: WP-002-T04 (cross-cutting)  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/security/TenantContextFilter.java`

**Specification**:
```java
@Component
@Order(1) // Must run before other filters
public class TenantContextFilter extends OncePerRequestFilter {

    private static final String TENANT_ID_HEADER = "X-Tenant-ID";

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        try {
            // 1. Extract tenant_id from JWT claim (primary) or X-Tenant-ID header (fallback)
            String tenantId = extractFromJwt(request);
            if (tenantId == null) {
                tenantId = request.getHeader(TENANT_ID_HEADER);
            }

            // 2. Validate tenant_id is not blank
            if (tenantId != null && !tenantId.isBlank()) {
                TenantContextHolder.setTenantId(tenantId);
            }

            filterChain.doFilter(request, response);
        } finally {
            // CRITICAL: Always clear ThreadLocal to prevent memory leak
            TenantContextHolder.clear();
        }
    }

    private String extractFromJwt(HttpServletRequest request) {
        // Extract "tenant_id" claim from JWT bearer token
        // Use Spring Security's SecurityContextHolder.getContext().getAuthentication()
        // Cast to JwtAuthenticationToken, get claim "tenant_id"
        // Return null if not JWT or claim not present
    }
}
```

**Definition of Done**:
- [ ] `TenantContextHolder.clear()` called in `finally` block (MANDATORY — prevents thread pool leaks)
- [ ] Filter order 1 (runs first)
- [ ] JWT claim "tenant_id" extracted from Spring Security JwtAuthenticationToken
- [ ] Header `X-Tenant-ID` fallback used when JWT claim absent
- [ ] `TenantContextFilterTest` verifies `clear()` called even when exception thrown

---

### TASK-TMS-009: TenantContextHolder (ThreadLocal)

**Parent WP Task**: WP-002-T04 (cross-cutting)  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/security/TenantContextHolder.java`

**Specification**:
```java
public final class TenantContextHolder {
    private static final ThreadLocal<String> CONTEXT = new ThreadLocal<>();

    private TenantContextHolder() {} // prevent instantiation

    public static void setTenantId(String tenantId) {
        if (tenantId == null || tenantId.isBlank()) {
            throw new IllegalArgumentException("tenantId cannot be null or blank");
        }
        CONTEXT.set(tenantId);
    }

    public static String getTenantId() {
        return CONTEXT.get();
    }

    public static String requireTenantId() {
        String tenantId = CONTEXT.get();
        if (tenantId == null) {
            throw new TenantContextMissingException("Tenant context not set");
        }
        return tenantId;
    }

    public static void clear() {
        CONTEXT.remove(); // use remove(), NOT set(null)
    }
}

// TenantContextMissingException.java
public class TenantContextMissingException extends RuntimeException {
    public TenantContextMissingException(String message) {
        super(message);
    }
}
```

**Definition of Done**:
- [ ] `clear()` calls `CONTEXT.remove()` (not `set(null)`)
- [ ] `requireTenantId()` throws `TenantContextMissingException` when null
- [ ] Constructor is private to prevent instantiation
- [ ] Unit test: set → get → clear → get returns null

---

## Task Group 4: Adapters

### TASK-TMS-010: KeycloakAdapter (Realm Management)

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/adapters/KeycloakAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/KeycloakAdapterImpl.java`

**Specification**:
```java
public interface KeycloakAdapter {
    String createRiderUser(String tenantId, String email, String authProvider);
    void assignRiderRole(String keycloakUserId);
    void suspendUser(String keycloakUserId);
    void reactivateUser(String keycloakUserId);
    void deleteUser(String keycloakUserId); // used in saga compensation
}

// KeycloakAdapterImpl:
// Base URL: ${keycloak.admin.url} (e.g., http://keycloak:8080)
// Realm: "av-platform-riders"
// Auth: Admin client credentials (client_credentials grant)
// Keycloak Admin Client: org.keycloak:keycloak-admin-client:23.0.3

// createRiderUser:
//   UserRepresentation user = new UserRepresentation();
//   user.setUsername(email);
//   user.setEmail(email);
//   user.setEnabled(true);
//   user.getAttributes().put("tenant_id", List.of(tenantId));
//   user.getAttributes().put("auth_provider", List.of(authProvider));
//   Response response = keycloakClient.realm("av-platform-riders").users().create(user);
//   return extractUserId(response); // parse Location header UUID

// assignRiderRole: GET role "rider" → assign to user
// suspendUser: update user enabled=false
```

**Definition of Done**:
- [ ] `KeycloakAdapterImpl` uses Keycloak Admin Client (not REST directly)
- [ ] Realm `av-platform-riders` hardcoded as constant
- [ ] `deleteUser` available for saga compensation rollback
- [ ] `KeycloakAdapterTest` uses Wiremock to mock Keycloak admin endpoints
- [ ] `tenant_id` attribute set on Keycloak user

---

### TASK-TMS-011: TwilioAdapter (OTP SMS)

**Parent WP Task**: WP-002-T07 (rider OTP)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/adapters/TwilioAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/TwilioAdapterImpl.java`

**Specification**:
```java
public interface TwilioAdapter {
    void sendOtp(String toPhoneNumber, String otp, String tenantName);
}

// TwilioAdapterImpl:
// Config: ${twilio.account-sid}, ${twilio.auth-token}, ${twilio.from-number}
// Use Twilio Java SDK: com.twilio.sdk:twilio:9.x
// Message template: "Your {tenantName} verification code: {otp}. Valid 5 minutes."
// On TwilioException → throw OtpDeliveryException("SMS delivery failed: " + e.getMessage())

// sendOtp:
//   Message.creator(
//       new PhoneNumber(toPhoneNumber),
//       new PhoneNumber(twilioFromNumber),
//       "Your " + tenantName + " verification code: " + otp + ". Valid 5 minutes."
//   ).create();
```

**Definition of Done**:
- [ ] Twilio SDK used (not raw HTTP)
- [ ] `OtpDeliveryException` thrown on Twilio failure (not RuntimeException)
- [ ] SMS message mentions "Valid 5 minutes" to match OTP TTL
- [ ] `TwilioAdapterTest` uses mock Twilio client

---

### TASK-TMS-012: MinIOAdapter (Logo Upload)

**Parent WP Task**: WP-002-T05 (branding)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/adapters/MinIOAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/MinIOAdapterImpl.java`

**Specification**:
```java
public interface MinIOAdapter {
    String uploadLogo(String tenantId, byte[] logoBytes, String contentType);
    void deleteLogo(String objectKey);
}

// MinIOAdapterImpl:
// Bucket: "tenant-assets"
// Object key pattern: "tenants/{tenantId}/logo.{extension}"
// Extension derived from contentType: "image/png" → "png", "image/jpeg" → "jpg", "image/webp" → "webp"
// Max file size: 5MB (enforced in service layer)
// Return CDN URL: "${minio.cdn-base-url}/tenant-assets/tenants/{tenantId}/logo.{extension}"

// uploadLogo:
//   MinioClient.putObject(
//       PutObjectArgs.builder()
//           .bucket("tenant-assets")
//           .object("tenants/" + tenantId + "/logo." + ext)
//           .stream(new ByteArrayInputStream(logoBytes), logoBytes.length, -1)
//           .contentType(contentType)
//           .build()
//   );
//   return cdnBaseUrl + "/tenant-assets/tenants/" + tenantId + "/logo." + ext;
```

**Definition of Done**:
- [ ] Object key pattern: `tenants/{tenantId}/logo.{ext}`
- [ ] Supported content types: `image/png`, `image/jpeg`, `image/webp` only
- [ ] CDN URL returned (not MinIO internal URL)
- [ ] `MinIOAdapterTest` uses `MinioClient` mock

---

### TASK-TMS-013: SagaStepAdapter Interfaces (SSC, BMS, DPE, VMS)

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/adapters/saga/SagaStepAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/saga/SscSagaStepAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/saga/BmsSagaStepAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/saga/DpeSagaStepAdapter.java`
- `src/main/java/com/vnpt/avplatform/tms/adapters/saga/VmsSagaStepAdapter.java`

**Specification**:
```java
// SagaStepAdapter.java — generic interface
public interface SagaStepAdapter {
    String execute(String tenantId, Map<String, Object> context) throws SagaStepException;
    void compensate(String tenantId, String externalRef) throws SagaCompensationException;
    String getStepName();
}

// SscSagaStepAdapter.java — calls SSC service via REST
// POST ${ssc.service.url}/internal/tenants with timeout 30s
// Returns: tenant record ID from SSC
// compensate: DELETE ${ssc.service.url}/internal/tenants/{externalRef}

// BmsSagaStepAdapter.java — calls BMS service via REST
// POST ${bms.service.url}/internal/subscriptions {tenant_id, plan_id: "trial"}
// Returns: subscription_id
// compensate: DELETE ${bms.service.url}/internal/subscriptions/{externalRef}

// DpeSagaStepAdapter.java — calls DPE service (driver platform enrollment)
// POST ${dpe.service.url}/internal/tenants {tenant_id}
// compensate: DELETE ${dpe.service.url}/internal/tenants/{tenantId}

// VmsSagaStepAdapter.java — calls VMS service (vehicle management setup)
// POST ${vms.service.url}/internal/fleets {tenant_id}
// compensate: DELETE ${vms.service.url}/internal/fleets/{tenantId}

// HTTP client: RestTemplate with 30s connect timeout, 30s read timeout
// On timeout: throw SagaStepException("TIMEOUT", stepName)
// On 4xx/5xx: throw SagaStepException("HTTP_" + statusCode, stepName)
```

**Definition of Done**:
- [ ] 4 adapter implementations: SSC, BMS, DPE, VMS (one per file)
- [ ] `execute()` throws `SagaStepException` on timeout or HTTP error
- [ ] `compensate()` is idempotent (safe to call multiple times)
- [ ] RestTemplate timeout: 30000ms connect + 30000ms read
- [ ] Each `getStepName()` returns: `"SSC"`, `"BMS"`, `"DPE"`, `"VMS"`

---

## Task Group 5: Service Layer

### TASK-TMS-014: TenantService (CRUD)

**Parent WP Task**: WP-002-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/TenantService.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/TenantServiceImpl.java`

**Specification**:
```java
// TenantService.java interface
public interface TenantService {
    TenantDTO createTenant(CreateTenantRequest request);
    TenantDTO getTenant(String tenantId);
    TenantDTO getTenantByDomain(String domain);
    PageResult<TenantDTO> listTenants(int page, int size);
    TenantDTO suspendTenant(String tenantId, String reason);
    TenantDTO reactivateTenant(String tenantId);
}

// TenantServiceImpl.java
// createTenant:
//   1. Validate companyDomain uniqueness: if existsByCompanyDomain → throw DomainAlreadyExistsException (HTTP 409)
//   2. Create Tenant entity with status=ONBOARDING
//   3. Save to MongoDB
//   4. Trigger OnboardingSagaService.startSaga(tenantId, request.getPlanId())
//   5. Return TenantDTO (mapToDTO)

// suspendTenant:
//   1. Load tenant or throw TenantNotFoundException (HTTP 404)
//   2. if status != ACTIVE → throw InvalidStatusTransitionException (HTTP 409)
//   3. updateStatus(SUSPENDED)
//   4. kafkaProducer.publish("tenant.suspended", { tenantId, reason, suspendedAt })
//   5. Return updated TenantDTO

// reactivateTenant:
//   1. Load tenant or throw TenantNotFoundException (HTTP 404)
//   2. if status != SUSPENDED → throw InvalidStatusTransitionException (HTTP 409)
//   3. updateStatus(ACTIVE)
//   4. kafkaProducer.publish("tenant.reactivated", { tenantId, reactivatedAt })
//   5. Return updated TenantDTO
```

**Definition of Done**:
- [ ] `createTenant` throws HTTP 409 `DomainAlreadyExistsException` on duplicate domain
- [ ] `suspendTenant` publishes `tenant.suspended` Kafka event
- [ ] `reactivateTenant` publishes `tenant.reactivated` Kafka event
- [ ] `TenantNotFoundException` returns HTTP 404
- [ ] `InvalidStatusTransitionException` returns HTTP 409

---

### TASK-TMS-015: OnboardingSagaService (Orchestrator)

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/OnboardingSagaService.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/OnboardingSagaServiceImpl.java`

**Specification**:
```java
public interface OnboardingSagaService {
    void startSaga(String tenantId, String planId);
}

// OnboardingSagaServiceImpl — executes saga steps sequentially
// Step order: SSC → BMS → DPE → VMS

// startSaga():
//   1. Create OnboardingSaga in MongoDB (status=IN_PROGRESS)
//   2. Execute steps in order with 30s per-step timeout:
//      for (SagaStepAdapter step : [sscAdapter, bmsAdapter, dpeAdapter, vmsAdapter]):
//          try:
//              String ref = step.execute(tenantId, context); // timeout enforced
//              sagaRepo.updateStepStatus(sagaId, idx, "COMPLETED", ref);
//              idx++;
//          catch (SagaStepException e):
//              sagaRepo.updateStepStatus(sagaId, idx, "FAILED", null);
//              sagaRepo.markFailed(sagaId, e.getMessage());
//              compensationService.compensate(sagaId, tenantId, idx - 1); // rollback completed steps
//              tenantRepo.updateStatus(tenantId, TenantStatus.TERMINATED);
//              return;
//   3. On all 4 steps COMPLETED:
//      sagaRepo.markCompleted(sagaId)
//      tenantRepo.updateStatus(tenantId, TenantStatus.ACTIVE)
//      kafkaProducer.publish("tenant.created", { tenantId, planId, activatedAt })

// Total saga timeout enforcement: @Async with CompletableFuture + 120s overall timeout
// Use @Async to run saga in background (non-blocking HTTP response)
```

**Definition of Done**:
- [ ] Saga runs `@Async` — does NOT block HTTP response
- [ ] Each step has 30s timeout enforced via `CompletableFuture.get(30, TimeUnit.SECONDS)`
- [ ] Total saga timeout 120s via outer `CompletableFuture.get(120, TimeUnit.SECONDS)`
- [ ] On step failure: immediately starts compensation for completed steps
- [ ] `tenant.created` Kafka event published ONLY when all 4 steps complete

---

### TASK-TMS-016: OnboardingSagaCompensation (Rollback Chain)

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/OnboardingSagaCompensation.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/OnboardingSagaCompensationImpl.java`

**Specification**:
```java
public interface OnboardingSagaCompensation {
    void compensate(String sagaId, String tenantId, int lastCompletedStepIndex);
}

// OnboardingSagaCompensationImpl:
// Rollback order is REVERSE of execution: VMS → DPE → BMS → SSC
// For each step from lastCompletedStepIndex down to 0:
//   SagaStep step = saga.getSteps().get(i);
//   if (step.getStatus().equals("COMPLETED")):
//       SagaStepAdapter adapter = getAdapterForStep(step.getStepName()); // [vmsAdapter, dpeAdapter, bmsAdapter, sscAdapter]
//       try:
//           adapter.compensate(tenantId, step.getExternalRef());
//           sagaRepo.updateStepStatus(sagaId, i, "COMPENSATED", step.getExternalRef());
//           sagaRepo.appendCompensationLog(sagaId, "Compensated " + step.getStepName() + " at " + Instant.now());
//       catch (SagaCompensationException e):
//           sagaRepo.appendCompensationLog(sagaId, "FAILED compensation for " + step.getStepName() + ": " + e.getMessage());
//           // log and continue — best-effort compensation
//           log.error("Saga {} compensation failed for step {}: {}", sagaId, step.getStepName(), e.getMessage());
// After all steps: sagaRepo.updateStatus(sagaId, SagaStatus.COMPENSATED)
// Finally: delete Tenant record from MongoDB
```

**Definition of Done**:
- [ ] Rollback order: VMS → DPE → BMS → SSC (reverse of execution)
- [ ] Each step's `externalRef` used in compensation call
- [ ] Compensation is best-effort (individual failures logged, not rethrown)
- [ ] `compensationLog` updated after each step compensation attempt
- [ ] Tenant record deleted after compensation complete

---

### TASK-TMS-017: FeatureFlagService (Redis-backed)

**Parent WP Task**: WP-002-T04  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/FeatureFlagService.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/FeatureFlagServiceImpl.java`

**Specification**:
```java
public interface FeatureFlagService {
    boolean isEnabled(String tenantId, String flagKey);
    Map<String, Boolean> getAllFlags(String tenantId);
    Map<String, Boolean> updateFlags(String tenantId, Map<String, Boolean> flags);
}

// Redis cache key: "tenant_config:{tenantId}" (TTL 300 seconds = 5 minutes)
// Cache stores: Map<String, Boolean> serialized as JSON

// isEnabled():
//   1. Try Redis: GET "tenant_config:{tenantId}" → parse JSON → get flagKey
//   2. On miss: load from MongoDB tenants collection, cache result, return flagKey value
//   3. If flagKey not in tenant's flags → return platform default flag (load from config)

// updateFlags():
//   1. Merge new flags with existing flags (partial update supported)
//   2. Save to MongoDB
//   3. Invalidate Redis: DEL "tenant_config:{tenantId}"
//   4. Return updated flags

// Redis serialization: Jackson ObjectMapper → write as Map JSON
// RedisTemplate<String, String> used (String value type for JSON)
```

**Definition of Done**:
- [ ] Redis key: `tenant_config:{tenantId}` with TTL 300s
- [ ] Cache miss: load from MongoDB, store in Redis
- [ ] `updateFlags` invalidates cache (DEL, not TTL wait)
- [ ] Platform default flags loaded from Spring config properties
- [ ] `FeatureFlagServiceTest` tests cache hit/miss/invalidation

---

### TASK-TMS-018: BrandingService (Logo upload)

**Parent WP Task**: WP-002-T05  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/BrandingService.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/BrandingServiceImpl.java`

**Specification**:
```java
public interface BrandingService {
    TenantBranding updateBranding(String tenantId, UpdateBrandingRequest request);
    String uploadLogo(String tenantId, MultipartFile logo);
    TenantBranding initiateDomainVerification(String tenantId, String customDomain);
    boolean verifyDomain(String tenantId);
}

// uploadLogo():
//   1. Validate file: content type must be "image/png"|"image/jpeg"|"image/webp"
//      → else: throw InvalidFileTypeException (HTTP 400 "INVALID_LOGO_TYPE")
//   2. Validate size: max 5MB (5 * 1024 * 1024 bytes)
//      → else: throw FileSizeExceededException (HTTP 400 "LOGO_TOO_LARGE")
//   3. Call minIOAdapter.uploadLogo(tenantId, logo.getBytes(), logo.getContentType())
//   4. Update tenant.branding.logoUrl in MongoDB
//   5. Invalidate Redis: DEL "tenant_config:{tenantId}"
//   6. Return CDN URL

// initiateDomainVerification():
//   1. Generate TXT record value: "vnpt-av-verify=" + UUID.randomUUID()
//   2. Store in tenant.branding.customDomainTxtRecord
//   3. tenant.branding.customDomain = customDomain
//   4. tenant.branding.customDomainVerified = false
//   5. Save to MongoDB
//   6. Return branding (caller displays TXT record to tenant admin)

// verifyDomain():
//   DNS TXT record lookup for tenant.branding.customDomain
//   Compare TXT record value with tenant.branding.customDomainTxtRecord
//   If match: set customDomainVerified = true, save to MongoDB, return true
//   Else: return false
```

**Definition of Done**:
- [ ] Logo max 5MB enforced with HTTP 400 error
- [ ] Allowed content types: png, jpeg, webp only
- [ ] TXT record generated as `"vnpt-av-verify=" + UUID`
- [ ] Domain verification uses actual DNS TXT lookup (using `dnsjava` or `InetAddress`)
- [ ] Redis cache invalidated after logo update

---

### TASK-TMS-019: RiderIdentityService (Register + OAuth)

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/RiderIdentityService.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/RiderIdentityServiceImpl.java`

**Specification**:
```java
public interface RiderIdentityService {
    RiderDTO registerRider(String tenantId, RegisterRiderRequest request);
    RiderDTO handleOAuthCallback(String tenantId, String provider, String idToken);
    RiderDTO getRider(String riderId);
    RiderDTO updateRider(String riderId, UpdateRiderRequest request);
}

// registerRider() — email/password registration:
//   1. Validate email uniqueness within tenantId
//      → existsByEmailAndTenantId → throw RiderAlreadyExistsException (HTTP 409 "RIDER_EMAIL_ALREADY_EXISTS")
//   2. Create Rider entity (status=PENDING_VERIFICATION, authProvider=EMAIL)
//   3. Call keycloakAdapter.createRiderUser(tenantId, email, "email")
//   4. Set rider.keycloakSub from Keycloak response
//   5. Save rider to MongoDB
//   6. Return RiderDTO with status=PENDING_VERIFICATION

// handleOAuthCallback() — Google/Apple:
//   1. Verify idToken with Keycloak (token introspection endpoint)
//   2. Extract email, sub from token claims
//   3. Check if rider exists by keycloakSub → if yes, update and return
//   4. If new: create Rider (status=ACTIVE, authProvider=GOOGLE|APPLE, emailVerified=true)
//   5. Save rider
//   6. Return RiderDTO with JWT from Keycloak token exchange

// getRider():
//   Load by riderId and verify tenant_id matches TenantContextHolder.requireTenantId() (BL-001)
//   → if tenant mismatch: throw AccessDeniedException (HTTP 403 "CROSS_TENANT_ACCESS")
```

**Definition of Done**:
- [ ] Email uniqueness checked within `tenantId` (not globally)
- [ ] Keycloak user created on registration
- [ ] OAuth callback handles both Google and Apple (same endpoint, different `provider` param)
- [ ] `getRider` enforces tenant isolation (BL-001 — HTTP 403 on cross-tenant access)
- [ ] `RiderIdentityServiceTest` covers: duplicate email, successful register, OAuth callback

---

### TASK-TMS-020: OTPService (Generate, Verify, Lock)

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/services/OTPService.java`
- `src/main/java/com/vnpt/avplatform/tms/services/impl/OTPServiceImpl.java`

**Specification**:
```java
public interface OTPService {
    void sendOtp(String riderId, String tenantId, String phoneNumber);
    void verifyOtp(String riderId, String tenantId, String phoneNumber, String otp);
    int getRemainingAttempts(String riderId, String tenantId, String phoneNumber);
}

// Redis keys:
// OTP value:   "otp:{riderId}:{phoneNumber}"         TTL 300s (5 minutes)
// Attempts:    "otp_attempts:{riderId}:{phoneNumber}" TTL 1800s (30 min lock window)
// Resend count: "otp_resend:{phone}:hourly"            TTL 3600s (1 hour)

// sendOtp():
//   1. Check resend count: GET "otp_resend:{phoneNumber}:hourly"
//      if count >= 3: throw OtpResendLimitException (HTTP 429 "OTP_RESEND_LIMIT_REACHED")
//   2. Check lock: GET "otp_attempts:{riderId}:{phoneNumber}"
//      if value == "LOCKED": throw OtpLockedExcption (HTTP 429 "OTP_LOCKED")
//   3. Generate OTP: String.format("%06d", random.nextInt(1000000)) // 6 digits, zero-padded
//   4. Store: SET "otp:{riderId}:{phoneNumber}" {otp} EX 300
//   5. Increment resend: INCR "otp_resend:{phoneNumber}:hourly" + EXPIRE 3600 (only if first increment)
//   6. Call twilioAdapter.sendOtp(phoneNumber, otp, tenantName)

// verifyOtp():
//   1. Check lock: GET "otp_attempts:{riderId}:{phoneNumber}"
//      if == "LOCKED": throw OtpLockedException (HTTP 429 "OTP_LOCKED", retryAfter=1800)
//   2. Stored = GET "otp:{riderId}:{phoneNumber}"
//      if stored == null: throw OtpExpiredException (HTTP 400 "OTP_EXPIRED")
//   3. if stored != submitted: 
//      attempts = INCR "otp_attempts:{riderId}:{phoneNumber}"
//      EXPIRE "otp_attempts:{riderId}:{phoneNumber}" 1800
//      if attempts >= 5: SET "otp_attempts:{riderId}:{phoneNumber}" "LOCKED" EX 1800
//                        throw OtpLockedException (HTTP 429 "OTP_LOCKED")
//      else: throw OtpInvalidException (HTTP 400 "OTP_INVALID", remaining=5-attempts)
//   4. if match:
//      DEL "otp:{riderId}:{phoneNumber}"
//      DEL "otp_attempts:{riderId}:{phoneNumber}"
//      Update rider: phone_verified=true, status=ACTIVE
```

**Definition of Done**:
- [ ] OTP: 6 digits, zero-padded via `%06d`
- [ ] OTP TTL: 300s
- [ ] Max attempts: 5 before lock; lock TTL: 1800s (30 minutes)
- [ ] Resend limit: 3 per hour per phone number
- [ ] Correct attempts counted via Redis INCR (atomic)
- [ ] `OTPServiceTest` covers: expired OTP, 5-attempt lockout, resend limit, success

---

## Task Group 6: Kafka Integration

### TASK-TMS-021: TenantKafkaProducer

**Parent WP Task**: WP-002-T06  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/events/TenantKafkaProducer.java`
- `src/main/java/com/vnpt/avplatform/tms/events/TenantEvent.java`

**Specification**:
```java
// TenantEvent.java
public class TenantEvent {
    private String eventId = UUID.randomUUID().toString();
    private String eventType; // "tenant.created"|"tenant.suspended"|"tenant.reactivated"|"tenant.quota_updated"
    private String tenantId;
    private Instant timestamp = Instant.now();
    private Map<String, Object> payload;
}

// TenantKafkaProducer.java
@Component
public class TenantKafkaProducer {
    private final KafkaTemplate<String, TenantEvent> kafkaTemplate;
    private static final String TOPIC = "tenant-events";

    public void publish(String eventType, String tenantId, Map<String, Object> payload) {
        TenantEvent event = new TenantEvent();
        event.setEventType(eventType);
        event.setTenantId(tenantId);
        event.setPayload(payload);

        // Partition key = tenantId (ensures ordering per tenant)
        kafkaTemplate.send(TOPIC, tenantId, event)
            .addCallback(
                result -> log.info("Published {} for tenant {}", eventType, tenantId),
                ex -> log.error("Failed to publish {} for tenant {}: {}", eventType, tenantId, ex.getMessage())
            );
    }
}
```

**Definition of Done**:
- [ ] Topic: `tenant-events` (constant)
- [ ] Partition key: `tenantId`
- [ ] `eventId` = UUID v4 (auto-generated)
- [ ] `timestamp` = `Instant.now()` (UTC)
- [ ] Kafka send failure: logged as ERROR, not rethrown (non-blocking)
- [ ] Events: `tenant.created`, `tenant.suspended`, `tenant.reactivated`, `tenant.quota_updated`

---

## Task Group 7: REST Controllers

### TASK-TMS-022: TenantController

**Parent WP Task**: WP-002-T05  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/controllers/TenantController.java`
- `src/main/java/com/vnpt/avplatform/tms/controllers/dto/CreateTenantRequest.java`
- `src/main/java/com/vnpt/avplatform/tms/controllers/dto/TenantDTO.java`

**Specification**:
```java
// TenantController.java
@RestController
@RequestMapping("/api/v1/tenants")
@PreAuthorize("hasRole('PLATFORM_ADMIN')") // All tenant management: platform admin only
public class TenantController {

    // POST /api/v1/tenants
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public TenantDTO createTenant(@Valid @RequestBody CreateTenantRequest request) {
        return tenantService.createTenant(request);
    }

    // GET /api/v1/tenants/{tenantId}
    @GetMapping("/{tenantId}")
    public TenantDTO getTenant(@PathVariable String tenantId) {
        return tenantService.getTenant(tenantId);
    }

    // GET /api/v1/tenants?page=0&size=20
    @GetMapping
    public PageResult<TenantDTO> listTenants(
        @RequestParam(defaultValue = "0") @Min(0) int page,
        @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size
    ) {
        return tenantService.listTenants(page, size);
    }

    // PUT /api/v1/tenants/{tenantId}/status
    @PutMapping("/{tenantId}/status")
    public TenantDTO updateStatus(
        @PathVariable String tenantId,
        @Valid @RequestBody UpdateStatusRequest request  // { "action": "suspend"|"reactivate", "reason": "..." }
    ) {
        if ("suspend".equals(request.getAction())) {
            return tenantService.suspendTenant(tenantId, request.getReason());
        } else if ("reactivate".equals(request.getAction())) {
            return tenantService.reactivateTenant(tenantId);
        }
        throw new InvalidRequestException("INVALID_ACTION", "action must be 'suspend' or 'reactivate'");
    }
}

// CreateTenantRequest.java — validation annotations:
//   companyName: @NotBlank @Size(min=2, max=200)
//   companyDomain: @NotBlank @Pattern(regexp="^[a-z0-9][a-z0-9\\-]{0,61}[a-z0-9]\\.[a-z]{2,}$")
//   countryCode: @NotBlank @Pattern(regexp="^[A-Z]{2}$")
//   timezone: @NotBlank (must be valid IANA timezone)
//   planId: @NotBlank
//   adminEmail: @NotBlank @Email
```

**Definition of Done**:
- [ ] All endpoints require `PLATFORM_ADMIN` role via `@PreAuthorize`
- [ ] `@Valid` on all request bodies
- [ ] HTTP 201 on POST /tenants
- [ ] HTTP 404 on unknown tenantId
- [ ] HTTP 409 on duplicate domain or invalid status transition
- [ ] Pagination: `page` (0-based) + `size` (1-100 default 20)

---

### TASK-TMS-023: TenantBrandingController

**Parent WP Task**: WP-002-T05  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/controllers/TenantBrandingController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/tenants/{tenantId}/branding")
@PreAuthorize("hasRole('TENANT_ADMIN')")
public class TenantBrandingController {

    // PUT /api/v1/tenants/{tenantId}/branding
    @PutMapping
    public TenantBranding updateBranding(
        @PathVariable String tenantId,
        @Valid @RequestBody UpdateBrandingRequest request
    ) { return brandingService.updateBranding(tenantId, request); }

    // POST /api/v1/tenants/{tenantId}/branding/logo
    @PostMapping("/logo")
    public Map<String, String> uploadLogo(
        @PathVariable String tenantId,
        @RequestParam("file") MultipartFile file
    ) {
        String url = brandingService.uploadLogo(tenantId, file);
        return Map.of("logo_url", url);
    }

    // POST /api/v1/tenants/{tenantId}/branding/domain-verification
    @PostMapping("/domain-verification")
    public TenantBranding initiateDomainVerification(
        @PathVariable String tenantId,
        @RequestBody Map<String, String> request  // { "custom_domain": "app.customer.com" }
    ) { return brandingService.initiateDomainVerification(tenantId, request.get("custom_domain")); }

    // GET /api/v1/tenants/{tenantId}/branding/domain-verification
    @GetMapping("/domain-verification")
    public Map<String, Object> checkDomainVerification(@PathVariable String tenantId) {
        boolean verified = brandingService.verifyDomain(tenantId);
        return Map.of("verified", verified);
    }
}
```

**Definition of Done**:
- [ ] Logo upload: `multipart/form-data` with `file` param
- [ ] HTTP 400 on invalid file type or size > 5MB
- [ ] Domain verification returns `{ "verified": true|false }`
- [ ] `TENANT_ADMIN` role required (not PLATFORM_ADMIN)

---

### TASK-TMS-024: TenantConfigController (Feature Flags)

**Parent WP Task**: WP-002-T04  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/controllers/TenantConfigController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/tenants/{tenantId}/config")
public class TenantConfigController {

    // GET /api/v1/tenants/{tenantId}/config
    @GetMapping
    @PreAuthorize("hasAnyRole('PLATFORM_ADMIN', 'TENANT_ADMIN')")
    public Map<String, Boolean> getFeatureFlags(@PathVariable String tenantId) {
        return featureFlagService.getAllFlags(tenantId);
    }

    // PUT /api/v1/tenants/{tenantId}/config
    @PutMapping
    @PreAuthorize("hasRole('PLATFORM_ADMIN')") // Only platform admin can change flags
    public Map<String, Boolean> updateFeatureFlags(
        @PathVariable String tenantId,
        @RequestBody Map<String, Boolean> flags // partial update supported
    ) {
        return featureFlagService.updateFlags(tenantId, flags);
    }
}
```

**Definition of Done**:
- [ ] GET: `TENANT_ADMIN` or `PLATFORM_ADMIN` can read flags
- [ ] PUT: Only `PLATFORM_ADMIN` can update flags
- [ ] Supports partial update (merge, not replace)
- [ ] HTTP 200 on success

---

### TASK-TMS-025: RiderController

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/controllers/RiderController.java`
- `src/main/java/com/vnpt/avplatform/tms/controllers/dto/RegisterRiderRequest.java`
- `src/main/java/com/vnpt/avplatform/tms/controllers/dto/RiderDTO.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/riders")
public class RiderController {

    // POST /api/v1/riders/register (PUBLIC — no auth required)
    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public RiderDTO register(@Valid @RequestBody RegisterRiderRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        return riderIdentityService.registerRider(tenantId, request);
    }

    // POST /api/v1/riders/{riderId}/verify-phone
    @PostMapping("/{riderId}/verify-phone")
    public Map<String, String> sendOtp(@PathVariable String riderId) {
        Rider rider = riderIdentityService.getRider(riderId); // validates tenant
        otpService.sendOtp(riderId, rider.getTenantId(), rider.getPhoneNumber());
        return Map.of("message", "OTP sent to " + maskPhone(rider.getPhoneNumber()));
    }

    // POST /api/v1/riders/{riderId}/confirm-otp
    @PostMapping("/{riderId}/confirm-otp")
    public Map<String, Object> confirmOtp(
        @PathVariable String riderId,
        @RequestBody Map<String, String> body  // { "otp": "123456" }
    ) {
        Rider rider = riderIdentityService.getRider(riderId);
        otpService.verifyOtp(riderId, rider.getTenantId(), rider.getPhoneNumber(), body.get("otp"));
        return Map.of("verified", true, "rider_status", "ACTIVE");
    }

    // GET /api/v1/riders/{riderId}
    @GetMapping("/{riderId}")
    @PreAuthorize("hasAnyRole('RIDER', 'TENANT_ADMIN', 'PLATFORM_ADMIN')")
    public RiderDTO getRider(@PathVariable String riderId) {
        return RiderDTO.from(riderIdentityService.getRider(riderId));
    }

    private String maskPhone(String phone) {
        // Show only last 4 digits: +84*******1234
        return phone.substring(0, 3) + "*".repeat(phone.length() - 7) + phone.substring(phone.length() - 4);
    }
}

// RegisterRiderRequest:
//   email: @NotBlank @Email
//   phoneNumber: @Pattern(regexp="^\\+[1-9]\\d{7,14}$")
//   authProvider: @NotNull (EMAIL)
```

**Definition of Done**:
- [ ] `/register` is public (no auth required)
- [ ] Phone number masked in OTP confirmation response
- [ ] `TenantContextHolder.requireTenantId()` used to enforce tenant scope
- [ ] HTTP 409 on duplicate email within tenant
- [ ] HTTP 429 with `Retry-After` header on OTP lock

---

### TASK-TMS-026: GlobalExceptionHandler

**Parent WP Task**: WP-002-T05  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/controllers/GlobalExceptionHandler.java`

**Specification**:
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    // Standard error response format:
    // { "error_code": "DOMAIN_ALREADY_EXISTS", "message": "...", "timestamp": "ISO8601" }

    @ExceptionHandler(TenantNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleTenantNotFound(TenantNotFoundException ex) { ... }

    @ExceptionHandler(DomainAlreadyExistsException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleDomainConflict(DomainAlreadyExistsException ex) { ... }

    @ExceptionHandler(InvalidStatusTransitionException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleInvalidTransition(InvalidStatusTransitionException ex) { ... }

    @ExceptionHandler(OtpLockedException.class)
    public ResponseEntity<ErrorResponse> handleOtpLocked(OtpLockedException ex) {
        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
            .header("Retry-After", "1800")
            .body(ErrorResponse.of("OTP_LOCKED", ex.getMessage()));
    }

    @ExceptionHandler(OtpInvalidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleOtpInvalid(OtpInvalidException ex) { ... }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        // Collect all field errors into a single message
    }

    @ExceptionHandler(AccessDeniedException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public ErrorResponse handleAccessDenied(AccessDeniedException ex) { ... }
}
```

**Definition of Done**:
- [ ] `OtpLockedException` returns HTTP 429 with `Retry-After: 1800` header
- [ ] All custom exceptions mapped to correct HTTP status codes
- [ ] `MethodArgumentNotValidException` collects all field validation errors
- [ ] Error response format: `{ error_code, message, timestamp }`
- [ ] No internal exception details leaked to client

---

## Task Group 8: Configuration

### TASK-TMS-027: MongoConfig (Indexes + Validators)

**Parent WP Task**: WP-002-T03  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/config/MongoConfig.java`

**Specification**:
```java
@Configuration
public class MongoConfig {

    @Bean
    public MongoCustomConversions mongoCustomConversions() {
        // Register converters if needed
        return new MongoCustomConversions(List.of());
    }

    @EventListener(ContextRefreshedEvent.class)
    public void initIndexes() {
        // tenants collection indexes
        mongoTemplate.indexOps("tenants").ensureIndex(
            new Index().on("tenant_id", Sort.Direction.ASC).unique()
        );
        mongoTemplate.indexOps("tenants").ensureIndex(
            new Index().on("company_domain", Sort.Direction.ASC).unique()
        );
        mongoTemplate.indexOps("tenants").ensureIndex(
            new Index().on("status", Sort.Direction.ASC)
        );

        // riders collection indexes
        mongoTemplate.indexOps("riders").ensureIndex(
            new Index().on("rider_id", Sort.Direction.ASC).unique()
        );
        mongoTemplate.indexOps("riders").ensureIndex(
            new Index().on("tenant_id", Sort.Direction.ASC) // BL-001
        );
        mongoTemplate.indexOps("riders").ensureIndex(
            new Index().on("keycloak_sub", Sort.Direction.ASC).unique().sparse()
        );
        mongoTemplate.indexOps("riders").ensureIndex(
            new Index().on("email", Sort.Direction.ASC).sparse()
        );

        // onboarding_sagas collection indexes
        mongoTemplate.indexOps("onboarding_sagas").ensureIndex(
            new Index().on("tenant_id", Sort.Direction.ASC).unique()
        );
    }
}
```

**Definition of Done**:
- [ ] All unique indexes created at startup (not relying on `@Indexed` annotation)
- [ ] `keycloak_sub` index is sparse
- [ ] `tenant_id` index on riders collection (BL-001 query performance)
- [ ] No application startup failure if indexes already exist

---

### TASK-TMS-028: RedisConfig

**Parent WP Task**: WP-002-T04  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/config/RedisConfig.java`

**Specification**:
```java
@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, String> redisTemplate(RedisConnectionFactory factory) {
        RedisTemplate<String, String> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new StringRedisSerializer());
        return template;
    }

    // No default TTL configured here — TTL set per key in service implementations
}
```

**Definition of Done**:
- [ ] `RedisTemplate<String, String>` bean configured
- [ ] String serializers for key and value
- [ ] No GenericJackson serializer (use manual JSON in service layer)

---

### TASK-TMS-029: SecurityConfig (Spring Security + Keycloak JWT)

**Parent WP Task**: WP-002-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/config/SecurityConfig.java`

**Specification**:
```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity // for @PreAuthorize
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session -> session.sessionCreationPolicy(STATELESS))
            .addFilterBefore(tenantContextFilter, UsernamePasswordAuthenticationFilter.class)
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/riders/register").permitAll()         // public registration
                .requestMatchers("/api/v1/riders/*/confirm-otp").permitAll()    // OTP verification
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt
                    .jwkSetUri("${spring.security.oauth2.resourceserver.jwt.jwk-set-uri}")
                    .jwtAuthenticationConverter(keycloakJwtConverter())
                )
            );
        return http.build();
    }

    @Bean
    public JwtAuthenticationConverter keycloakJwtConverter() {
        // Extract roles from "realm_access.roles" claim in Keycloak JWT
        JwtGrantedAuthoritiesConverter grantedAuthoritiesConverter = new JwtGrantedAuthoritiesConverter();
        grantedAuthoritiesConverter.setAuthoritiesClaimName("realm_access.roles");
        grantedAuthoritiesConverter.setAuthorityPrefix("ROLE_");
        // ...
    }
}
```

**Definition of Done**:
- [ ] `/api/v1/riders/register` and confirm-otp endpoints are public
- [ ] JWT validated against Keycloak JWK endpoint
- [ ] Roles extracted from `realm_access.roles` claim
- [ ] `STATELESS` session management
- [ ] `TenantContextFilter` added before `UsernamePasswordAuthenticationFilter`

---

### TASK-TMS-030: KafkaProducerConfig

**Parent WP Task**: WP-002-T06  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/tms/config/KafkaProducerConfig.java`

**Specification**:
```java
@Configuration
public class KafkaProducerConfig {

    @Bean
    public ProducerFactory<String, TenantEvent> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        config.put(ProducerConfig.ACKS_CONFIG, "all"); // required for durability
        config.put(ProducerConfig.RETRIES_CONFIG, 3);
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        return new DefaultKafkaProducerFactory<>(config);
    }

    @Bean
    public KafkaTemplate<String, TenantEvent> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }
}
```

**Definition of Done**:
- [ ] `acks=all` for durability
- [ ] Idempotent producer enabled
- [ ] JSON serializer for `TenantEvent` value
- [ ] Retries = 3 for transient failures

---

## Task Group 9: Tests

### TASK-TMS-031: Unit Tests — TenantService

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/tms/services/TenantServiceTest.java`

**Test Cases**:
```
1. createTenant_success: given valid request, saves tenant with status=ONBOARDING, triggers saga
2. createTenant_duplicateDomain: given existing domain, throws DomainAlreadyExistsException (409)
3. getTenant_found: returns TenantDTO
4. getTenant_notFound: throws TenantNotFoundException (404)
5. suspendTenant_fromActive: updates status, publishes Kafka event tenant.suspended
6. suspendTenant_notActive: throws InvalidStatusTransitionException (409)
7. reactivateTenant_fromSuspended: updates status, publishes Kafka event tenant.reactivated
8. reactivateTenant_notSuspended: throws InvalidStatusTransitionException (409)
```

**Definition of Done**:
- [ ] 8 test cases all passing with `@ExtendWith(MockitoExtension.class)`
- [ ] `TenantRepository` and `TenantKafkaProducer` mocked with `@Mock`
- [ ] Kafka event published with correct `eventType` in suspend/reactivate tests
- [ ] Coverage for `TenantServiceImpl` ≥ 85%

---

### TASK-TMS-032: Unit Tests — OnboardingSagaService (Happy Path + Rollback)

**Parent WP Task**: WP-002-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/tms/services/OnboardingSagaServiceTest.java`

**Test Cases**:
```
1. startSaga_happyPath: all 4 steps succeed → tenant status=ACTIVE, tenant.created event published
2. startSaga_sscFails: SSC step fails → rollback called for 0 steps, tenant status=TERMINATED
3. startSaga_bmsFailsAfterSsc: BMS fails after SSC succeeds → SSC compensated, tenant=TERMINATED
4. startSaga_vmsFailsAfterThreeSteps: VMS fails after SSC+BMS+DPE → all 3 compensated in reverse
5. startSaga_stepTimeout: step takes > 30s → treated as failure, compensation starts
```

**Definition of Done**:
- [ ] 5 test cases covering happy path and all failure scenarios
- [ ] Compensation called in reverse order verified by InOrder mock verification
- [ ] `tenant.created` event only published in test case 1
- [ ] `@Async` tested with `ThreadPoolTaskExecutor` synchronous mock

---

### TASK-TMS-033: Unit Tests — OTPService

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/tms/services/OTPServiceTest.java`

**Test Cases**:
```
1. sendOtp_success: Redis set, Twilio called
2. sendOtp_locked: "LOCKED" in Redis → OtpLockedException
3. sendOtp_resendLimitReached: resend count >= 3 → OtpResendLimitException
4. verifyOtp_success: matching OTP → rider phone_verified=true
5. verifyOtp_expired: no OTP in Redis → OtpExpiredException
6. verifyOtp_invalid_3rdAttempt: wrong OTP 3 times → remaining=2 shown
7. verifyOtp_invalid_5thAttempt: wrong OTP 5 times → OtpLockedException
8. verifyOtp_afterLock: already "LOCKED" → OtpLockedException immediately
```

**Definition of Done**:
- [ ] 8 test cases all passing
- [ ] Redis operations verified using `@Mock RedisTemplate`
- [ ] OTP format validated: 6 digits numeric
- [ ] Resend counter verified via INCR mock

---

### TASK-TMS-034: Integration Tests — Tenant CRUD APIs

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/tms/integration/TenantControllerIT.java`

**Specification**:
```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@AutoConfigureMockMvc
@TestcontainersTest // MongoDB + Redis via Testcontainers
public class TenantControllerIT {
    // Test 1: POST /api/v1/tenants → 201 Created
    // Test 2: POST /api/v1/tenants (duplicate domain) → 409 Conflict
    // Test 3: GET /api/v1/tenants/{tenantId} → 200 OK with correct data
    // Test 4: GET /api/v1/tenants/{unknownId} → 404
    // Test 5: PUT /api/v1/tenants/{id}/status { action: "suspend" } → 200
    // Test 6: PUT /api/v1/tenants/{id}/status (not active) → 409
}
```

**Definition of Done**:
- [ ] Uses Testcontainers (MongoDB + Redis), not H2
- [ ] JWT mock for `PLATFORM_ADMIN` role
- [ ] All 6 test scenarios pass
- [ ] Kafka producer mocked (not real Kafka needed for controller tests)

---

### TASK-TMS-035: Integration Tests — Rider Registration + OTP Flow

**Parent WP Task**: WP-002-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/tms/integration/RiderControllerIT.java`

**Specification**:
```java
// Test 1: POST /api/v1/riders/register (email) → 201 Created, status=PENDING_VERIFICATION
// Test 2: POST /api/v1/riders/register (duplicate email) → 409
// Test 3: POST /api/v1/riders/{id}/verify-phone → 200, "OTP sent to +84****1234"
// Test 4: POST /api/v1/riders/{id}/confirm-otp (correct OTP) → 200, rider.status=ACTIVE
// Test 5: POST /api/v1/riders/{id}/confirm-otp (wrong OTP) → 400, remaining attempts shown
// Test 6: POST /api/v1/riders/{id}/confirm-otp (5th wrong) → 429, Retry-After: 1800
```

**Definition of Done**:
- [ ] Twilio adapter mocked (no real SMS sent)
- [ ] Keycloak adapter mocked (no real Keycloak)
- [ ] OTP stored in Redis Testcontainer (real Redis)
- [ ] 6 test scenarios all pass
- [ ] Response body `Retry-After: 1800` header verified in test 6

---

## Dependency Summary

```
WP-001 (Foundation) must be complete before starting WP-002.

Internal task dependencies:
TASK-TMS-001 → TASK-TMS-005 (Repo)
TASK-TMS-002 → TASK-TMS-006 (Repo)
TASK-TMS-003 → TASK-TMS-007 (Repo)
TASK-TMS-009 → TASK-TMS-008 (Filter needs Holder)
TASK-TMS-010 → TASK-TMS-019 (Keycloak Adapter needs before Rider Service)
TASK-TMS-011 → TASK-TMS-020 (Twilio Adapter before OTP Service)
TASK-TMS-012 → TASK-TMS-018 (MinIO Adapter before Branding Service)
TASK-TMS-013 → TASK-TMS-015 (Saga Step Adapters before Saga Service)
TASK-TMS-014,015,016 → TASK-TMS-022 (Services before Controllers)
TASK-TMS-021 → TASK-TMS-015 (Kafka Producer before Saga Service)
TASK-TMS-027,028,029,030 → All (Config first)
TASK-TMS-031–035 (Tests last)
```

---

*DETAIL_PLAN_TMS v1.0.0 — TMS Tenant Management Service | VNPT AV Platform Services Provider Group*
