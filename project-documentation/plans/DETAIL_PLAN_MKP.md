# DETAIL PLAN — MKP: Marketplace & Plugin Ecosystem Service

**Work Package**: WP-009 | **SRS**: SRS_MKP_Marketplace.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.mkp`  
**Database**: MongoDB (`mkp_db`)  
**Cache**: Redis (`plugin-catalog:{tenant_id}` TTL 300s)  
**Events**: Kafka (publishes: `mkp-events`; consumes: `payment-events` for revenue tracking)  
**Object Storage**: MinIO (plugin packages, audit reports)  
**Security**: API keys SHA-256 hashed; bank accounts AES-256-GCM encrypted; SSRF prevention on webhook URLs  
**Critical**: BL-009 — ZERO plugins published without BOTH security AND performance audit `result=passed`  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-MKP-001 | Partner domain model + state machine enum | Domain Models | 1.5h |
| TASK-MKP-002 | Plugin domain model | Domain Models | 1.5h |
| TASK-MKP-003 | AuditReport domain model (security + performance) | Domain Models | 1h |
| TASK-MKP-004 | RevenueShareRecord domain model (INSERT-only) | Domain Models | 1h |
| TASK-MKP-005 | PayoutBatch domain model | Domain Models | 1h |
| TASK-MKP-006 | PartnerRepository | Repository | 1h |
| TASK-MKP-007 | PluginRepository | Repository | 1h |
| TASK-MKP-008 | AuditReportRepository | Repository | 1h |
| TASK-MKP-009 | RevenueShareRecordRepository (INSERT-only) | Repository | 1h |
| TASK-MKP-010 | PayoutBatchRepository | Repository | 1h |
| TASK-MKP-011 | TenantContextFilter + AES-256-GCM EncryptionService | Security | 2h |
| TASK-MKP-012 | ApiKeyService (SHA-256 hash + generation) | Security | 1.5h |
| TASK-MKP-013 | SsrfValidationService (private IP range blocking) | Security | 1.5h |
| TASK-MKP-014 | PartnerLifecycleService (7-state machine) | Services | 2h |
| TASK-MKP-015 | AuditGateService (BL-009 dual-audit enforcement) | Services | 2h |
| TASK-MKP-016 | PluginCatalogService (Redis TTL 300s cache) | Services | 1.5h |
| TASK-MKP-017 | RevenueShareService (INSERT-only records) | Services | 1.5h |
| TASK-MKP-018 | PayoutBatchScheduler (min 50,000 VND threshold) | Services | 2h |
| TASK-MKP-019 | ConnectorSeederService (5 pre-built connectors) | Services | 1.5h |
| TASK-MKP-020 | MkpKafkaProducer + PaymentEventConsumer | Kafka | 1.5h |
| TASK-MKP-021 | PartnerController (registration + lifecycle) | Controllers | 2h |
| TASK-MKP-022 | PluginController (publish + catalog) | Controllers | 2h |
| TASK-MKP-023 | AuditController (submit + query audit results) | Controllers | 1.5h |
| TASK-MKP-024 | RevenueController (records + payout) | Controllers | 1.5h |
| TASK-MKP-025 | GlobalExceptionHandler | Controllers | 1h |
| TASK-MKP-026 | MongoConfig + RedisConfig | Config | 1.5h |
| TASK-MKP-027 | Unit tests: AuditGateService + PartnerLifecycleService | Tests | 2h |
| TASK-MKP-028 | Unit tests: ApiKeyService + SsrfValidationService | Tests | 1.5h |
| TASK-MKP-029 | Unit tests: RevenueShareService + PayoutBatchScheduler | Tests | 2h |
| TASK-MKP-030 | Integration tests: Partner + Plugin + Audit API | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-MKP-001: Partner Domain Model + State Machine Enum

**Parent WP Task**: WP-009-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/models/Partner.java`
- `src/main/java/com/vnpt/avplatform/mkp/models/PartnerStatus.java`

**Specification**:
```java
// PartnerStatus.java — 7-state machine (BL-009)
public enum PartnerStatus {
    REGISTERED,       // Initial state after self-registration
    UNDER_REVIEW,     // Manual review by platform admin
    SECURITY_AUDIT,   // Security audit in progress
    PERFORMANCE_TEST, // Performance test in progress
    APPROVED,         // Both audits passed, ready to publish
    PUBLISHED,        // Active in marketplace (can publish plugins)
    SUSPENDED         // Deactivated (compliance/security breach)
}
// Valid state transitions:
// REGISTERED → UNDER_REVIEW (trigger: admin action)
// UNDER_REVIEW → SECURITY_AUDIT (trigger: admin submits for audit)
// SECURITY_AUDIT → PERFORMANCE_TEST (trigger: security audit passes)
// PERFORMANCE_TEST → APPROVED (trigger: performance test passes)
// SECURITY_AUDIT → UNDER_REVIEW (trigger: security audit fails — re-review)
// PERFORMANCE_TEST → UNDER_REVIEW (trigger: perf test fails — re-review)
// APPROVED → PUBLISHED (trigger: admin publishes)
// PUBLISHED → SUSPENDED (trigger: security breach or admin action)
// SUSPENDED → UNDER_REVIEW (trigger: appeal and re-entry)

// Partner.java
@Document(collection = "partners")
public class Partner {
    @Id private String id;

    @Field("partner_id")
    @Indexed(unique = true)
    private String partnerId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001

    @Field("company_name")
    @NotBlank
    @Size(max = 200)
    private String companyName;

    @Field("company_registration_number")
    @NotBlank
    private String companyRegistrationNumber;

    @Field("contact_email")
    @Email
    @NotBlank
    private String contactEmail;

    @Field("contact_phone")
    @Pattern(regexp = "^\\+?[1-9]\\d{1,14}$")
    private String contactPhone;

    @Field("status")
    @Indexed
    private PartnerStatus status = PartnerStatus.REGISTERED;

    // API key fields (SHA-256 hashed — raw key shown only at creation):
    @Field("api_key_hash")
    private String apiKeyHash; // SHA-256(rawApiKey)

    @Field("api_key_prefix")
    private String apiKeyPrefix; // first 8 chars of raw key (for display)

    // Bank account (AES-256-GCM encrypted):
    @Field("bank_account_encrypted")
    private String bankAccountEncrypted; // AES-256-GCM ciphertext

    @Field("bank_account_iv")
    private String bankAccountIv; // base64 IV for AES-GCM decryption

    @Field("bank_name")
    private String bankName; // NOT encrypted

    @Field("revenue_share_pct")
    @Min(0) @Max(100)
    private int revenueSharePct; // default 70 (partner gets 70%)

    @Field("webhook_url")
    private String webhookUrl; // validated: no private IPs (SSRF prevention)

    @Field("status_history")
    private List<StatusChange> statusHistory = new ArrayList<>();

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Field("approved_at")
    private Instant approvedAt;

    @Field("suspended_at")
    private Instant suspendedAt;
    
    // StatusChange inner class:
    // { fromStatus, toStatus, changedBy, reason, changedAt }
}
```

**Definition of Done**:
- [ ] All 7 states in `PartnerStatus`
- [ ] `apiKeyHash` stores SHA-256 hash — NEVER raw key
- [ ] `bankAccountEncrypted` + `bankAccountIv` for AES-GCM
- [ ] `statusHistory` tracks all transitions with actor and reason

---

### TASK-MKP-002: Plugin Domain Model

**Parent WP Task**: WP-009-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/models/Plugin.java`
- `src/main/java/com/vnpt/avplatform/mkp/models/PluginStatus.java`
- `src/main/java/com/vnpt/avplatform/mkp/models/PluginCategory.java`

**Specification**:
```java
// PluginStatus.java
public enum PluginStatus {
    DRAFT,            // In development, not submitted
    SUBMITTED,        // Submitted for review
    SECURITY_AUDIT,   // Under security audit
    PERFORMANCE_TEST, // Under performance test
    APPROVED,         // Audits passed, ready to activate
    PUBLISHED,        // Active in catalog
    DEACTIVATED,      // Suspended/removed
    REJECTED          // Failed audits (terminal — must re-submit as new version)
}

// PluginCategory.java
public enum PluginCategory {
    INSURANCE,      // VNPT Insurance connector
    ACCESSIBILITY,  // Accessibility features
    ERP,            // Enterprise Resource Planning (SAP Concur, TripActions)
    MAPS,           // HERE Maps, routing
    FINANCE,        // Payment, accounting
    ANALYTICS,      // Custom analytics
    COMMUNICATION,  // Chat, notifications
    OTHER
}

// Plugin.java
@Document(collection = "plugins")
public class Plugin {
    @Id private String id;

    @Field("plugin_id")
    @Indexed(unique = true)
    private String pluginId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001 — tenant that installed this plugin

    @Field("partner_id")
    @Indexed
    private String partnerId; // Publisher's partner ID

    @Field("name")
    @NotBlank @Size(max = 100)
    private String name;

    @Field("slug")
    @Indexed
    @Pattern(regexp = "^[a-z0-9-]+$")
    private String slug; // URL-friendly name (e.g., "vnpt-insurance-connector")

    @Field("version")
    @NotBlank
    private String version; // SemVer: "1.2.3"

    @Field("category")
    private PluginCategory category;

    @Field("description")
    @Size(max = 2000)
    private String description;

    @Field("pricing_model")
    private String pricingModel; // "FREE", "SUBSCRIPTION", "PAY_PER_USE"

    @Field("monthly_price_vnd")
    private Long monthlyPriceVnd; // null for FREE

    @Field("status")
    @Indexed
    private PluginStatus status = PluginStatus.DRAFT;

    @Field("is_pre_built")
    private boolean isPreBuilt = false; // true for 5 seeded connectors

    @Field("package_url")
    private String packageUrl; // MinIO object key for plugin archive

    @Field("documentation_url")
    private String documentationUrl;

    @Field("webhook_endpoint")
    private String webhookEndpoint; // partner's webhook (SSRF validated)

    @Field("security_audit_id")
    private String securityAuditId; // ref to AuditReport

    @Field("performance_audit_id")
    private String performanceAuditId; // ref to AuditReport

    @Field("installed_count")
    private long installedCount = 0;

    @Field("avg_rating")
    private double avgRating = 0.0;

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Field("published_at")
    private Instant publishedAt;
}
```

**Definition of Done**:
- [ ] Both `securityAuditId` and `performanceAuditId` must be set before PUBLISHED (enforced by AuditGateService)
- [ ] `slug` regex: `^[a-z0-9-]+$` — URL safe
- [ ] `is_pre_built=true` for 5 seeded connectors

---

### TASK-MKP-003: AuditReport Domain Model

**Parent WP Task**: WP-009-T03  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/models/AuditReport.java`
- `src/main/java/com/vnpt/avplatform/mkp/models/AuditType.java`
- `src/main/java/com/vnpt/avplatform/mkp/models/AuditResult.java`

**Specification**:
```java
// AuditType.java
public enum AuditType { SECURITY, PERFORMANCE }

// AuditResult.java — BL-009: both must be PASSED for plugin to go APPROVED
public enum AuditResult { PENDING, PASSED, FAILED }

// AuditReport.java
@Document(collection = "audit_reports")
public class AuditReport {
    @Id private String id;

    @Field("audit_id")
    @Indexed(unique = true)
    private String auditId = UUID.randomUUID().toString();

    @Field("plugin_id")
    @Indexed
    private String pluginId;

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("audit_type")
    private AuditType auditType;

    @Field("result")
    private AuditResult result = AuditResult.PENDING;

    @Field("summary")
    private String summary; // human-readable audit outcome

    @Field("findings")
    private List<AuditFinding> findings = new ArrayList<>();
    // AuditFinding: { severity: "CRITICAL|HIGH|MEDIUM|LOW", description, line_ref }

    @Field("conducted_by")
    private String conductedBy; // adminId or automated tool name

    @Field("started_at")
    private Instant startedAt;

    @Field("completed_at")
    private Instant completedAt;
}
```

**Business Rule BL-009**:
- Security `result=PASSED` AND Performance `result=PASSED` BOTH required before plugin can transition to APPROVED
- If either is FAILED: plugin status → REJECTED; partner must re-submit new version

**Definition of Done**:
- [ ] `AuditResult.PASSED` required from BOTH audits (not just one)
- [ ] `AuditFinding` severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` only

---

### TASK-MKP-004: RevenueShareRecord Domain Model (INSERT-Only)

**Parent WP Task**: WP-009-T04  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/models/RevenueShareRecord.java`

**Specification**:
```java
// INSERT-ONLY collection (BL-008 — immutable financial audit log)
// NEVER UPDATE OR DELETE revenue_share_records
@Document(collection = "revenue_share_records")
public class RevenueShareRecord {
    @Id private String id;

    @Field("record_id")
    @Indexed(unique = true)
    private String recordId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("partner_id")
    @Indexed
    private String partnerId;

    @Field("plugin_id")
    private String pluginId;

    @Field("transaction_id")
    private String transactionId; // from PAY service payment.captured event

    @Field("event_type")
    private String eventType; // "SUBSCRIPTION_FEE", "INSTALLATION_FEE", "PAY_PER_USE"

    @Field("gross_revenue_vnd")
    private Long grossRevenueVnd; // total payment amount

    @Field("partner_share_pct")
    private int partnerSharePct; // snapshot of partner.revenueSharePct at time of transaction

    @Field("partner_revenue_vnd")
    private Long partnerRevenueVnd; // gross × (partnerSharePct / 100) — stored for audit

    @Field("platform_revenue_vnd")
    private Long platformRevenueVnd; // gross - partner_revenue_vnd

    @Field("payout_batch_id")
    private String payoutBatchId; // set when included in payout (null until then)

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Definition of Done**:
- [ ] `partnerSharePct` is a SNAPSHOT at transaction time (not live partner value)
- [ ] `payout_batch_id` is the ONLY field that may be updated (null → batchId)
- [ ] Repository ONLY provides `insert()` and `findByPartnerId()` (no update/delete)

---

### TASK-MKP-005: PayoutBatch Domain Model

**Parent WP Task**: WP-009-T04  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/models/PayoutBatch.java`
- `src/main/java/com/vnpt/avplatform/mkp/models/PayoutStatus.java`

**Specification**:
```java
// PayoutStatus.java
public enum PayoutStatus { PENDING, PROCESSING, COMPLETED, FAILED }

// PayoutBatch.java
@Document(collection = "payout_batches")
public class PayoutBatch {
    @Id private String id;

    @Field("batch_id")
    @Indexed(unique = true)
    private String batchId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("partner_id")
    @Indexed
    private String partnerId;

    @Field("period_from")
    private LocalDate periodFrom; // payout period start

    @Field("period_to")
    private LocalDate periodTo;

    @Field("total_revenue_vnd")
    private Long totalRevenueVnd; // sum of all RevenueShareRecords in batch

    @Field("status")
    private PayoutStatus status = PayoutStatus.PENDING;

    @Field("transfer_reference")
    private String transferReference; // bank transfer confirmation number

    @Field("record_ids")
    private List<String> recordIds = new ArrayList<>(); // RevenueShareRecord IDs included

    @Field("scheduled_at")
    private Instant scheduledAt; // monthly scheduler timestamp

    @Field("processed_at")
    private Instant processedAt;

    @Field("error_message")
    private String errorMessage;
}
```

**Minimum payout threshold**: 50,000 VND (partners below threshold accumulate to next cycle)

**Definition of Done**:
- [ ] `totalRevenueVnd < 50000` → batch NOT created (records carry forward)
- [ ] `record_ids` links to all included `revenue_share_records` for audit trail

---

## Task Group 2: Repository Layer

### TASK-MKP-006: PartnerRepository

**Parent WP Task**: WP-009-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/repositories/PartnerRepository.java`
- `src/main/java/com/vnpt/avplatform/mkp/repositories/impl/PartnerRepositoryImpl.java`

**Specification**:
```java
public interface PartnerRepository {
    Partner insert(Partner partner); // initial registration
    Optional<Partner> findByPartnerId(String partnerId);
    Optional<Partner> findByApiKeyHash(String apiKeyHash); // API key lookup
    List<Partner> findByTenantIdAndStatus(String tenantId, PartnerStatus status, int page, int size);
    Partner updateStatus(String partnerId, PartnerStatus newStatus, StatusChange change);
    Partner updateBankAccount(String partnerId, String encryptedAccount, String iv);
}
// All queries include tenant_id filter (BL-001)
// findByApiKeyHash: used in API authentication (partner-facing endpoints)
// updateStatus: $push statusHistory, $set status atomically
```

**Definition of Done**:
- [ ] `findByApiKeyHash` indexed (SHA-256 hash is queried frequently)
- [ ] `updateStatus`: atomic `$set status` + `$push statusHistory` in single update

---

### TASK-MKP-007: PluginRepository

**Parent WP Task**: WP-009-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/repositories/PluginRepository.java`
- `src/main/java/com/vnpt/avplatform/mkp/repositories/impl/PluginRepositoryImpl.java`

**Specification**:
```java
public interface PluginRepository {
    Plugin insert(Plugin plugin);
    Optional<Plugin> findByPluginId(String pluginId);
    List<Plugin> findPublished(String tenantId, PluginCategory category, int page, int size);
    List<Plugin> findByPartnerId(String partnerId, PluginStatus status);
    Plugin updateStatus(String pluginId, PluginStatus status, String auditId, AuditType auditType);
    Plugin incrementInstalledCount(String pluginId);
}
// findPublished: tenant_id filter + status=PUBLISHED (catalog browsing)
// updateStatus: sets securityAuditId or performanceAuditId based on auditType
```

**Definition of Done**:
- [ ] `findPublished` ONLY returns `status=PUBLISHED` (BL-009 safety)
- [ ] Index on `(slug, tenant_id)` for unique slug per tenant
- [ ] `incrementInstalledCount`: `$inc { installed_count: 1 }` atomic

---

### TASK-MKP-008: AuditReportRepository

**Parent WP Task**: WP-009-T03  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/repositories/AuditReportRepository.java`
- `src/main/java/com/vnpt/avplatform/mkp/repositories/impl/AuditReportRepositoryImpl.java`

**Specification**:
```java
public interface AuditReportRepository {
    AuditReport insert(AuditReport report);
    Optional<AuditReport> findByAuditId(String auditId);
    List<AuditReport> findByPluginId(String pluginId, AuditType type);
    AuditReport updateResult(String auditId, AuditResult result, String summary,
        List<AuditFinding> findings, Instant completedAt);
    Optional<AuditReport> findLatestByPluginIdAndType(String pluginId, AuditType type);
}
// findLatestByPluginIdAndType: sort by started_at DESC, limit 1
```

**Definition of Done**:
- [ ] `findLatestByPluginIdAndType` sorts by `startedAt DESC` limit 1
- [ ] `updateResult` only updates result, summary, findings, completedAt

---

### TASK-MKP-009: RevenueShareRecordRepository (INSERT-Only)

**Parent WP Task**: WP-009-T04  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/repositories/RevenueShareRecordRepository.java`
- `src/main/java/com/vnpt/avplatform/mkp/repositories/impl/RevenueShareRecordRepositoryImpl.java`

**Specification**:
```java
public interface RevenueShareRecordRepository {
    RevenueShareRecord insert(RevenueShareRecord record); // ONLY allowed write operation
    List<RevenueShareRecord> findUnpaidByPartnerId(String partnerId, String tenantId);
    // "unpaid" = payout_batch_id is null
    Long sumUnpaidByPartnerId(String partnerId, String tenantId); // sum partner_revenue_vnd
    RevenueShareRecord assignPayoutBatch(String recordId, String payoutBatchId);
    // assignPayoutBatch: ONLY allowed update (payout_batch_id null → batchId)
}
// NO delete, NO bulk update, NO other field updates (BL-008)
```

**Definition of Done**:
- [ ] Repository interface only exposes `insert` + `findUnpaid` + `sumUnpaid` + `assignPayoutBatch`
- [ ] `assignPayoutBatch` validates payout_batch_id is currently null (no re-assignment)

---

### TASK-MKP-010: PayoutBatchRepository

**Parent WP Task**: WP-009-T04  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/repositories/PayoutBatchRepository.java`
- `src/main/java/com/vnpt/avplatform/mkp/repositories/impl/PayoutBatchRepositoryImpl.java`

**Specification**:
```java
public interface PayoutBatchRepository {
    PayoutBatch insert(PayoutBatch batch);
    Optional<PayoutBatch> findByBatchId(String batchId);
    List<PayoutBatch> findByPartnerId(String partnerId, String tenantId, int page, int size);
    PayoutBatch updateStatus(String batchId, PayoutStatus status,
        String transferReference, String errorMessage, Instant processedAt);
}
```

**Definition of Done**:
- [ ] All queries include `tenant_id` filter (BL-001)

---

## Task Group 3: Security

### TASK-MKP-011: TenantContextFilter + AES-256-GCM EncryptionService

**Parent WP Task**: WP-009-T01 (cross-cutting)  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/mkp/security/TenantContextHolder.java`
- `src/main/java/com/vnpt/avplatform/mkp/security/EncryptionService.java`
- `src/main/java/com/vnpt/avplatform/mkp/security/impl/AesGcmEncryptionService.java`

**Specification**:
```java
// TenantContextFilter — same as TMS pattern
// OncePerRequestFilter @Order(1), JWT "tenant_id" or "X-Tenant-ID" header
// finally: TenantContextHolder.clear()

// EncryptionService interface:
public interface EncryptionService {
    EncryptedData encrypt(String plaintext);
    String decrypt(EncryptedData encryptedData);
}

// EncryptedData: { ciphertext: String (base64), iv: String (base64) }

// AesGcmEncryptionService:
// - Algorithm: AES/GCM/NoPadding
// - Key size: 256-bit (32 bytes) from environment: AES_ENCRYPTION_KEY (base64-encoded)
// - IV size: 12 bytes (randomly generated per encryption)
// - Tag length: 128 bits

// encrypt():
//   byte[] iv = new byte[12];
//   new SecureRandom().nextBytes(iv);
//   Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
//   cipher.init(Cipher.ENCRYPT_MODE, secretKey, new GCMParameterSpec(128, iv));
//   byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));
//   return new EncryptedData(
//       Base64.getEncoder().encodeToString(ciphertext),
//       Base64.getEncoder().encodeToString(iv)
//   );

// decrypt():
//   byte[] iv = Base64.getDecoder().decode(encryptedData.getIv());
//   byte[] ciphertext = Base64.getDecoder().decode(encryptedData.getCiphertext());
//   Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
//   cipher.init(Cipher.DECRYPT_MODE, secretKey, new GCMParameterSpec(128, iv));
//   return new String(cipher.doFinal(ciphertext), StandardCharsets.UTF_8);
```

**Definition of Done**:
- [ ] AES key loaded from `AES_ENCRYPTION_KEY` env var (not application.properties)
- [ ] New random IV generated for EACH encryption (not reused)
- [ ] IV stored alongside ciphertext (in `bank_account_iv` field)
- [ ] `EncryptionServiceTest`: decrypt(encrypt(plaintext)) == plaintext

---

### TASK-MKP-012: ApiKeyService (SHA-256 Hash + Generation)

**Parent WP Task**: WP-009-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/security/ApiKeyService.java`
- `src/main/java/com/vnpt/avplatform/mkp/security/impl/ApiKeyServiceImpl.java`

**Specification**:
```java
public interface ApiKeyService {
    ApiKeyCreationResult generateApiKey(); // called on partner approval
    String hashApiKey(String rawApiKey);   // SHA-256 hash
    boolean verifyApiKey(String rawApiKey, String storedHash); // for auth
}

// ApiKeyCreationResult: { rawApiKey, hash, prefix }

// generateApiKey():
//   UUID prefix (first 8 chars): "mnxpqrst"
//   Raw key format: "mkp_{prefix}_{UUID.randomUUID()}"
//   Example: "mkp_mnxpqrst_550e8400-e29b-41d4-a716-446655440000"
//   hash = hashApiKey(rawKey)
//   // rawApiKey shown ONCE to partner — never stored
//   return new ApiKeyCreationResult(rawKey, hash, prefix);

// hashApiKey():
//   MessageDigest digest = MessageDigest.getInstance("SHA-256");
//   byte[] hashBytes = digest.digest(rawApiKey.getBytes(StandardCharsets.UTF_8));
//   return HexFormat.of().formatHex(hashBytes); // lowercase hex string

// verifyApiKey():
//   return storedHash.equals(hashApiKey(rawApiKey));
```

**Definition of Done**:
- [ ] Raw API key shown ONLY once (at generation) — never stored, never returned again
- [ ] SHA-256 hash stored in `partner.api_key_hash`
- [ ] `prefix` (first 8 chars) stored in `partner.api_key_prefix` for display
- [ ] `ApiKeyServiceTest`: verify hash is deterministic and verify() works

---

### TASK-MKP-013: SsrfValidationService (Private IP Range Blocking)

**Parent WP Task**: WP-009-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/security/SsrfValidationService.java`
- `src/main/java/com/vnpt/avplatform/mkp/security/impl/SsrfValidationServiceImpl.java`

**Specification**:
```java
public interface SsrfValidationService {
    void validateWebhookUrl(String url); // throws InvalidWebhookUrlException if unsafe
}

// validateWebhookUrl():
//   1. Parse URL: URI uri = new URI(url);
//   2. Schema check: must be "https" (reject http, ftp, file, etc.)
//      if (!"https".equalsIgnoreCase(uri.getScheme()))
//          throw new InvalidWebhookUrlException("Webhook URL must use HTTPS");
//   3. Resolve hostname → IP address:
//      InetAddress addr = InetAddress.getByName(uri.getHost());
//   4. Private/loopback range check:
//      if (isPrivateOrReservedIp(addr))
//          throw new InvalidWebhookUrlException("Webhook URL points to private/reserved IP");
//   5. DNS rebinding protection: resolve again and compare (if IPs differ → reject)

// isPrivateOrReservedIp(InetAddress addr):
//   return addr.isLoopbackAddress()         // 127.x.x.x
//       || addr.isSiteLocalAddress()        // 10.x, 172.16-31.x, 192.168.x
//       || addr.isLinkLocalAddress()        // 169.254.x
//       || addr.isAnyLocalAddress()         // 0.0.0.0
//       || isCloudMetadataRange(addr);      // 169.254.169.254 (AWS/GCP metadata)

// isCloudMetadataRange(addr):
//   String ip = addr.getHostAddress();
//   return ip.startsWith("169.254.169.");    // Cloud metadata service

// Custom exception:
// class InvalidWebhookUrlException extends BadRequestException { ... }
```

**Definition of Done**:
- [ ] Rejects `http://` (must be HTTPS)
- [ ] Rejects 10.x, 172.16-31.x, 192.168.x (site-local)
- [ ] Rejects 127.x.x.x (loopback)
- [ ] Rejects 169.254.169.254 (cloud metadata)
- [ ] `SsrfValidationServiceTest`: 8 test cases covering each rejected range + valid URL

---

## Task Group 4: Core Services

### TASK-MKP-014: PartnerLifecycleService (7-State Machine)

**Parent WP Task**: WP-009-T05  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/services/PartnerLifecycleService.java`
- `src/main/java/com/vnpt/avplatform/mkp/services/impl/PartnerLifecycleServiceImpl.java`

**Specification**:
```java
public interface PartnerLifecycleService {
    Partner registerPartner(PartnerRegistrationRequest request);
    Partner transitionStatus(String partnerId, PartnerStatus newStatus, String actorId, String reason);
    Partner approvePartner(String partnerId, String adminId);
    Partner suspendPartner(String partnerId, String adminId, String reason);
    ApiKeyCreationResult generatePartnerApiKey(String partnerId, String adminId);
}

// registerPartner():
//   1. Validate companyName, email, phone
//   2. ssrfValidationService.validateWebhookUrl(request.getWebhookUrl()) — if provided
//   3. Encrypt bank account: encryptionService.encrypt(request.getBankAccountNumber())
//   4. Set status = REGISTERED
//   5. partnerRepository.insert(partner)

// transitionStatus() — state machine enforcement:
//   VALID_TRANSITIONS = Map.of(
//       REGISTERED, Set.of(UNDER_REVIEW),
//       UNDER_REVIEW, Set.of(SECURITY_AUDIT, APPROVED),
//       SECURITY_AUDIT, Set.of(PERFORMANCE_TEST, UNDER_REVIEW),
//       PERFORMANCE_TEST, Set.of(APPROVED, UNDER_REVIEW),
//       APPROVED, Set.of(PUBLISHED),
//       PUBLISHED, Set.of(SUSPENDED),
//       SUSPENDED, Set.of(UNDER_REVIEW)
//   )
//   if (!VALID_TRANSITIONS.get(current).contains(newStatus))
//       throw new InvalidStateTransitionException(current + " → " + newStatus);
//   StatusChange change = new StatusChange(current, newStatus, actorId, reason, Instant.now());
//   return partnerRepository.updateStatus(partnerId, newStatus, change);

// approvePartner():
//   Validates AuditGateService.checkPartnerAudits(partnerId) — BL-009
//   Calls transitionStatus(partnerId, APPROVED, adminId, "Audits passed")
//   Calls generatePartnerApiKey() and returns key result

// generatePartnerApiKey():
//   Only callable when partner is APPROVED or PUBLISHED
//   ApiKeyCreationResult result = apiKeyService.generateApiKey()
//   partnerRepository.update(partnerId, { apiKeyHash: result.hash, apiKeyPrefix: result.prefix })
//   return result (rawApiKey visible ONE time to caller)
```

**Definition of Done**:
- [ ] Invalid state transitions throw `InvalidStateTransitionException` (HTTP 422)
- [ ] `registerPartner` calls SSRF validation on webhook URL
- [ ] `registerPartner` encrypts bank account with AES-256-GCM
- [ ] `generatePartnerApiKey` raw key returned only once (not stored)
- [ ] `PartnerLifecycleServiceTest`: all 7 state transitions tested (valid + invalid)

---

### TASK-MKP-015: AuditGateService (BL-009 Dual-Audit Enforcement)

**Parent WP Task**: WP-009-T06  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/services/AuditGateService.java`
- `src/main/java/com/vnpt/avplatform/mkp/services/impl/AuditGateServiceImpl.java`

**Specification**:
```java
public interface AuditGateService {
    // BL-009: BOTH audits must have result=PASSED
    void assertBothAuditsPassed(String pluginId); // throws AuditNotPassedException

    AuditReport submitAudit(String pluginId, AuditType auditType, String conductedBy);
    AuditReport recordAuditResult(String auditId, AuditResult result, String summary,
        List<AuditFinding> findings);
    AuditGateStatus getAuditStatus(String pluginId);
}

// AuditGateStatus: { pluginId, securityResult, performanceResult, canPublish: boolean }

// assertBothAuditsPassed() — BL-009 enforcement:
//   AuditReport security = auditReportRepository.findLatestByPluginIdAndType(pluginId, SECURITY)
//       .orElseThrow(() -> new AuditNotPassedException("Security audit not yet conducted"));
//   AuditReport perf = auditReportRepository.findLatestByPluginIdAndType(pluginId, PERFORMANCE)
//       .orElseThrow(() -> new AuditNotPassedException("Performance audit not yet conducted"));
//   if (security.getResult() != PASSED)
//       throw new AuditNotPassedException("Security audit result: " + security.getResult());
//   if (perf.getResult() != PASSED)
//       throw new AuditNotPassedException("Performance audit result: " + perf.getResult());
//   // Both passed — proceed

// recordAuditResult() — when audit completes:
//   AuditReport updated = auditReportRepository.updateResult(auditId, result, summary, findings, now);
//   if (result == FAILED) {
//       // Update plugin status to REJECTED (BL-009)
//       pluginRepository.updateStatus(pluginId, PluginStatus.REJECTED, auditId, type);
//       mkpKafkaProducer.publishEvent("mkp.plugin.rejected", { pluginId, reason: "Audit failed" });
//   } else { // PASSED
//       // Check if OTHER audit also passed → auto-transition to APPROVED
//       AuditGateStatus status = getAuditStatus(pluginId);
//       if (status.isCanPublish()) {
//           pluginRepository.updateStatus(pluginId, PluginStatus.APPROVED, auditId, type);
//           mkpKafkaProducer.publishEvent("mkp.plugin.approved", { pluginId });
//       }
//   }
```

**Definition of Done**:
- [ ] `assertBothAuditsPassed` throws if EITHER audit is missing or not PASSED
- [ ] `recordAuditResult(FAILED)` → plugin status = REJECTED (no recovery without re-submit)
- [ ] `recordAuditResult(PASSED)` → check other audit, auto-transition to APPROVED if both pass
- [ ] `AuditGateServiceTest`: BL-009 matrix tested (4 combinations: SS, SP, PS, PP where S=Security, P=Perf, first char = result)

---

### TASK-MKP-016: PluginCatalogService (Redis TTL 300s Cache)

**Parent WP Task**: WP-009-T07  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/services/PluginCatalogService.java`
- `src/main/java/com/vnpt/avplatform/mkp/services/impl/PluginCatalogServiceImpl.java`

**Specification**:
```java
public interface PluginCatalogService {
    List<PluginDTO> browsePublished(String tenantId, PluginCategory category, int page, int size);
    PluginDTO getPluginDetails(String tenantId, String pluginId);
    Plugin activatePlugin(String tenantId, String pluginId); // install for tenant
    Plugin deactivatePlugin(String tenantId, String pluginId);
}

// Cache key pattern: "plugin-catalog:{tenantId}" → TTL 300s
// Cache invalidated on: activate OR deactivate

// browsePublished():
//   String cacheKey = "plugin-catalog:" + tenantId;
//   String cached = redisTemplate.opsForValue().get(cacheKey);
//   if (cached != null) return objectMapper.readValue(cached, LIST_OF_PLUGIN_DTO);
//   List<Plugin> plugins = pluginRepository.findPublished(tenantId, category, page, size);
//   List<PluginDTO> dtos = plugins.stream().map(mapper::toDTO).collect(toList());
//   redisTemplate.opsForValue().set(cacheKey, objectMapper.writeValueAsString(dtos),
//       Duration.ofSeconds(300)); // TTL 300s
//   return dtos;

// activatePlugin():
//   auditGateService.assertBothAuditsPassed(pluginId); // BL-009 re-check
//   Plugin plugin = pluginRepository.findByPluginId(pluginId)...;
//   if (plugin.getStatus() != PluginStatus.PUBLISHED)
//       throw new PluginNotPublishedException("Plugin must be PUBLISHED to activate");
//   pluginRepository.incrementInstalledCount(pluginId);
//   // Invalidate cache:
//   redisTemplate.delete("plugin-catalog:" + tenantId);
//   mkpKafkaProducer.publishEvent("mkp.plugin.activated", { tenantId, pluginId });
//   return plugin;
```

**Definition of Done**:
- [ ] Cache key: `plugin-catalog:{tenantId}` — TTL 300s (5 minutes)
- [ ] Cache invalidated on activate AND deactivate
- [ ] `activatePlugin` re-checks `assertBothAuditsPassed` (BL-009 — defense in depth)
- [ ] Only `status=PUBLISHED` plugins returned by browse

---

### TASK-MKP-017: RevenueShareService (INSERT-Only Records)

**Parent WP Task**: WP-009-T08  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/services/RevenueShareService.java`
- `src/main/java/com/vnpt/avplatform/mkp/services/impl/RevenueShareServiceImpl.java`

**Specification**:
```java
public interface RevenueShareService {
    RevenueShareRecord recordRevenue(String tenantId, String partnerId, String pluginId,
        String transactionId, String eventType, Long grossRevenueVnd);
    RevenueShareSummary getSummary(String partnerId, String tenantId, LocalDate from, LocalDate to);
}

// recordRevenue():
//   1. Fetch partner.revenueSharePct (SNAPSHOT at time of transaction)
//   2. Compute:
//      partnerRevenueVnd = grossRevenueVnd * partnerSharePct / 100
//      platformRevenueVnd = grossRevenueVnd - partnerRevenueVnd
//   3. RevenueShareRecord record = new RevenueShareRecord();
//      record.setPartnerSharePct(partner.getRevenueSharePct()); // snapshot
//      record.setPartnerRevenueVnd(partnerRevenueVnd);
//      record.setPlatformRevenueVnd(platformRevenueVnd);
//      // ...
//   4. revenueShareRecordRepository.insert(record); // INSERT-ONLY (BL-008)
//   5. return record;

// getSummary():
//   Long totalPendingVnd = revenueShareRecordRepository.sumUnpaidByPartnerId(partnerId, tenantId);
//   List<RevenueShareRecord> records = revenueShareRecordRepository.findUnpaidByPartnerId(...);
//   return new RevenueShareSummary { partnerId, pendingPayoutVnd: totalPendingVnd, records };
```

**Definition of Done**:
- [ ] `partnerSharePct` is snapshot of partner value at transaction time (not live)
- [ ] `revenueShareRecordRepository.insert()` used (never save/update)
- [ ] Revenue computation: integer arithmetic (Long VND — no floating point rounding)
- [ ] `RevenueShareServiceTest`: verify partnerShare + platformRevenue = grossRevenue exactly

---

### TASK-MKP-018: PayoutBatchScheduler (Min 50,000 VND Threshold)

**Parent WP Task**: WP-009-T09  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/services/PayoutBatchScheduler.java`
- `src/main/java/com/vnpt/avplatform/mkp/services/impl/PayoutBatchSchedulerImpl.java`

**Specification**:
```java
public interface PayoutBatchScheduler {
    void processMonthlyPayouts(); // @Scheduled CRON — 1st of month 02:00 UTC
    PayoutBatch processBatchForPartner(String partnerId, String tenantId);
}

// @Scheduled(cron = "0 0 2 1 * *", zone = "UTC") — 2 AM UTC on 1st of each month

// processMonthlyPayouts():
//   // Get all approved/published partners with unpaid revenue
//   List<String> partnerIds = partnerRepository.findWithUnpaidRevenue(tenantId);
//   for (String partnerId : partnerIds) {
//       processBatchForPartner(partnerId, tenantId);
//   }

// processBatchForPartner():
//   Long unpaidVnd = revenueShareRecordRepository.sumUnpaidByPartnerId(partnerId, tenantId);
//   if (unpaidVnd < 50_000L) {
//       log.info("Partner {} below minimum payout threshold ({}VND < 50000VND) — carry forward", 
//           partnerId, unpaidVnd);
//       return null; // no payout this cycle — accumulates
//   }
//   List<RevenueShareRecord> records = revenueShareRecordRepository.findUnpaidByPartnerId(...);
//   PayoutBatch batch = new PayoutBatch();
//   batch.setPartnerId(partnerId);
//   batch.setTotalRevenueVnd(unpaidVnd);
//   batch.setRecordIds(records.stream().map(RevenueShareRecord::getRecordId).collect(toList()));
//   batch.setPeriodFrom(LocalDate.now().withDayOfMonth(1).minusMonths(1));
//   batch.setPeriodTo(LocalDate.now().withDayOfMonth(1).minusDays(1));
//   PayoutBatch saved = payoutBatchRepository.insert(batch);
//   // Link records to batch:
//   records.forEach(r -> revenueShareRecordRepository.assignPayoutBatch(r.getRecordId(), saved.getBatchId()));
//   // Trigger bank transfer (external integration):
//   initiateTransfer(saved, partner);
//   return saved;
```

**Definition of Done**:
- [ ] CRON: `"0 0 2 1 * *"` — 2:00 AM UTC on 1st of every month
- [ ] Partners with unpaidVnd < 50,000 VND: log + skip (carry forward to next month)
- [ ] `assignPayoutBatch` called for ALL included records (audit trail)
- [ ] `PayoutBatchSchedulerTest`: threshold edge cases (49,999 VND → skip, 50,000 VND → process)

---

### TASK-MKP-019: ConnectorSeederService (5 Pre-Built Connectors)

**Parent WP Task**: WP-009-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/services/ConnectorSeederService.java`

**Specification**:
```java
@Component
public class ConnectorSeederService {
    @PostConstruct
    public void seedPreBuiltConnectors() {
        // 5 pre-built connectors seeded at startup with status=PUBLISHED
        // Only seed if not already in DB (idempotent check by slug)
        List<PreBuiltConnector> connectors = List.of(
            new PreBuiltConnector("vnpt-insurance-connector", "VNPT Insurance Connector",
                PluginCategory.INSURANCE, "Integration with VNPT Insurance API"),
            new PreBuiltConnector("accessibility-connector", "Accessibility Features",
                PluginCategory.ACCESSIBILITY, "ADA-compliant vehicle booking features"),
            new PreBuiltConnector("sap-concur-connector", "SAP Concur ERP Connector",
                PluginCategory.ERP, "Enterprise travel and expense management"),
            new PreBuiltConnector("tripactions-connector", "TripActions Connector",
                PluginCategory.ERP, "Business travel management platform"),
            new PreBuiltConnector("here-maps-connector", "HERE Maps Connector",
                PluginCategory.MAPS, "HERE Maps routing and geocoding")
        );
        for (PreBuiltConnector connector : connectors) {
            boolean exists = pluginRepository.findBySlug(connector.getSlug()).isPresent();
            if (!exists) {
                Plugin plugin = buildPlugin(connector);
                plugin.setStatus(PluginStatus.PUBLISHED); // seeded as published
                plugin.setPreBuilt(true);
                plugin.setPublishedAt(Instant.now());
                pluginRepository.insert(plugin);
                log.info("Seeded pre-built connector: {}", connector.getSlug());
            }
        }
    }
}
```

**Definition of Done**:
- [ ] All 5 connectors seeded at startup
- [ ] Idempotent: seeder skips if slug already exists
- [ ] All 5 seeded with `status=PUBLISHED` and `is_pre_built=true`
- [ ] No audit required for pre-built connectors (VNPT-owned)

---

## Task Group 5: Kafka

### TASK-MKP-020: MkpKafkaProducer + PaymentEventConsumer

**Parent WP Task**: WP-009-T04  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/events/MkpKafkaProducer.java`
- `src/main/java/com/vnpt/avplatform/mkp/events/PaymentEventConsumer.java`

**Specification**:
```java
// MkpKafkaProducer: publishes to "mkp-events" topic
// Events published:
// - mkp.plugin.approved: { pluginId, partnerId, tenantId }
// - mkp.plugin.rejected: { pluginId, partnerId, reason }
// - mkp.plugin.activated: { pluginId, tenantId }
// - mkp.payout.processed: { batchId, partnerId, amountVnd }

// PaymentEventConsumer: listens to "payment-events" for plugin subscription payments
@KafkaListener(topics = "payment-events", groupId = "mkp-revenue")
public void onPaymentEvent(ConsumerRecord<String, String> record, Acknowledgment ack) {
    PaymentEvent event = objectMapper.readValue(record.value(), PaymentEvent.class);
    // Process only: payment.captured events with event metadata containing pluginId
    if ("payment.captured".equals(event.getEventType()) && event.getMetadata().containsKey("plugin_id")) {
        String pluginId = (String) event.getMetadata().get("plugin_id");
        String partnerId = getPartnerIdForPlugin(pluginId);
        revenueShareService.recordRevenue(event.getTenantId(), partnerId, pluginId,
            event.getTransactionId(), "SUBSCRIPTION_FEE", event.getAmountVnd());
    }
    ack.acknowledge();
}
```

**Definition of Done**:
- [ ] Consumer group: `mkp-revenue`
- [ ] Only processes `payment.captured` events with `plugin_id` in metadata
- [ ] Revenue recorded via `revenueShareService.recordRevenue()` (INSERT-only)
- [ ] Manual offset commit after processing

---

## Task Group 6: REST Controllers

### TASK-MKP-021: PartnerController (Registration + Lifecycle)

**Parent WP Task**: WP-009-T10  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/controllers/PartnerController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/partners")
public class PartnerController {

    // POST /api/v1/partners (partner self-registration)
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public PartnerDTO register(@Valid @RequestBody PartnerRegistrationRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        Partner partner = partnerLifecycleService.registerPartner(request.withTenantId(tenantId));
        return mapper.toDTO(partner); // bank account NOT returned in DTO
    }

    // GET /api/v1/partners/{partnerId}
    @GetMapping("/{partnerId}")
    @PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN') or @partnerOwnership.check(#partnerId)")
    public PartnerDTO getPartner(@PathVariable String partnerId) {
        String tenantId = TenantContextHolder.requireTenantId();
        return mapper.toDTO(partnerRepository.findByPartnerId(partnerId)
            .filter(p -> p.getTenantId().equals(tenantId))
            .orElseThrow(() -> new PartnerNotFoundException(partnerId)));
    }

    // PATCH /api/v1/partners/{partnerId}/status
    @PatchMapping("/{partnerId}/status")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public PartnerDTO updateStatus(@PathVariable String partnerId,
        @Valid @RequestBody StatusTransitionRequest request) {
        String adminId = getCurrentUserId();
        return mapper.toDTO(partnerLifecycleService.transitionStatus(
            partnerId, request.getNewStatus(), adminId, request.getReason()));
    }

    // POST /api/v1/partners/{partnerId}/api-key (generate/rotate API key)
    @PostMapping("/{partnerId}/api-key")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public ApiKeyResponse generateApiKey(@PathVariable String partnerId) {
        ApiKeyCreationResult result = partnerLifecycleService.generatePartnerApiKey(partnerId, getCurrentUserId());
        // rawApiKey shown ONCE — never available again
        return new ApiKeyResponse(result.getRawApiKey(), result.getPrefix());
    }
}
```

**Validation Rules**:
- `companyName`: 1–200 chars, not blank
- `contactEmail`: valid email format
- `contactPhone`: E.164 format (`^\\+?[1-9]\\d{1,14}$`)
- `webhookUrl`: HTTPS, SSRF validated (no private IPs)

**Definition of Done**:
- [ ] Bank account NEVER returned in `PartnerDTO` (only `apiKeyPrefix`)
- [ ] `generateApiKey` raw key shown only in response of this endpoint
- [ ] SSRF validation failure → HTTP 400 with `"Webhook URL points to private/reserved IP"`

---

### TASK-MKP-022: PluginController (Publish + Catalog)

**Parent WP Task**: WP-009-T11  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/controllers/PluginController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/plugins")
public class PluginController {

    // POST /api/v1/plugins (submit plugin for review)
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasRole('PARTNER')")
    public PluginDTO submitPlugin(@Valid @RequestBody PluginSubmissionRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        String partnerId = getPartnerIdFromJwt(); // JWT claim "partner_id"
        // Validate partner is PUBLISHED (can submit plugins):
        Partner partner = partnerRepository.findByPartnerId(partnerId)
            .filter(p -> p.getStatus() == PartnerStatus.PUBLISHED)
            .orElseThrow(() -> new PartnerNotApprovedException("Partner must be PUBLISHED to submit plugins"));
        // SSRF validate webhook:
        if (request.getWebhookEndpoint() != null)
            ssrfValidationService.validateWebhookUrl(request.getWebhookEndpoint());
        Plugin plugin = mapper.toPlugin(request, tenantId, partnerId);
        return mapper.toDTO(pluginRepository.insert(plugin));
    }

    // GET /api/v1/plugins (browse catalog)
    @GetMapping
    public List<PluginDTO> browseCatalog(
        @RequestParam(required = false) PluginCategory category,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        return pluginCatalogService.browsePublished(tenantId, category, page, size);
    }

    // POST /api/v1/plugins/{pluginId}/activate
    @PostMapping("/{pluginId}/activate")
    @PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN')")
    public PluginDTO activatePlugin(@PathVariable String pluginId) {
        String tenantId = TenantContextHolder.requireTenantId();
        return mapper.toDTO(pluginCatalogService.activatePlugin(tenantId, pluginId));
    }

    // POST /api/v1/plugins/{pluginId}/publish (admin publishes approved plugin)
    @PostMapping("/{pluginId}/publish")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public PluginDTO publishPlugin(@PathVariable String pluginId) {
        // auditGateService.assertBothAuditsPassed(pluginId) — BL-009
        auditGateService.assertBothAuditsPassed(pluginId);
        return mapper.toDTO(pluginRepository.updateStatus(pluginId, PluginStatus.PUBLISHED, null, null));
    }
}
```

**Definition of Done**:
- [ ] Catalog browse returns only `status=PUBLISHED` plugins (cache-backed)
- [ ] `publish` enforces BL-009 `assertBothAuditsPassed` before setting PUBLISHED
- [ ] `submitPlugin` validates partner is PUBLISHED (not just APPROVED)

---

### TASK-MKP-023: AuditController (Submit + Query Audit Results)

**Parent WP Task**: WP-009-T12  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/controllers/AuditController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/audits")
@PreAuthorize("hasRole('PLATFORM_ADMIN')")
public class AuditController {

    // POST /api/v1/audits (start an audit for a plugin)
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public AuditReportDTO submitAudit(@Valid @RequestBody AuditSubmissionRequest request) {
        String adminId = getCurrentUserId();
        return mapper.toDTO(auditGateService.submitAudit(
            request.getPluginId(), request.getAuditType(), adminId));
    }

    // PATCH /api/v1/audits/{auditId}/result (record audit outcome)
    @PatchMapping("/{auditId}/result")
    public AuditReportDTO recordResult(@PathVariable String auditId,
        @Valid @RequestBody AuditResultRequest request) {
        return mapper.toDTO(auditGateService.recordAuditResult(
            auditId, request.getResult(), request.getSummary(), request.getFindings()));
    }

    // GET /api/v1/audits/plugins/{pluginId}/status
    @GetMapping("/plugins/{pluginId}/status")
    public AuditGateStatus getAuditStatus(@PathVariable String pluginId) {
        return auditGateService.getAuditStatus(pluginId);
    }
}
// AuditResultRequest:
// { result: AuditResult (PASSED|FAILED), summary: String (required), findings: List<AuditFinding> }
```

**Definition of Done**:
- [ ] Only `PLATFORM_ADMIN` can record audit results
- [ ] `recordResult(FAILED)` triggers plugin → REJECTED (via AuditGateService)
- [ ] `recordResult(PASSED)` auto-checks other audit and transitions to APPROVED if both pass

---

### TASK-MKP-024: RevenueController (Records + Payout)

**Parent WP Task**: WP-009-T13  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/controllers/RevenueController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/revenue")
public class RevenueController {

    // GET /api/v1/revenue/summary (partner views own pending revenue)
    @GetMapping("/summary")
    @PreAuthorize("hasAnyRole('PARTNER', 'PLATFORM_ADMIN')")
    public RevenueShareSummary getRevenueSummary(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        String partnerId = getPartnerIdFromJwt();
        return revenueShareService.getSummary(partnerId, tenantId, dateFrom, dateTo);
    }

    // GET /api/v1/revenue/payouts (list payout batches)
    @GetMapping("/payouts")
    @PreAuthorize("hasAnyRole('PARTNER', 'PLATFORM_ADMIN')")
    public List<PayoutBatchDTO> listPayouts(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        String partnerId = getPartnerIdFromJwt();
        return payoutBatchRepository.findByPartnerId(partnerId, tenantId, page, size)
            .stream().map(mapper::toDTO).collect(toList());
    }
}
// Bank account number NEVER returned in any endpoint response
```

**Definition of Done**:
- [ ] Partner can only view own revenue (partnerId from JWT, not path param)
- [ ] Bank account number NOT returned anywhere in responses

---

## Task Group 7: Configuration

### TASK-MKP-026: MongoConfig + RedisConfig

**Parent WP Task**: WP-009-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/mkp/config/MongoConfig.java`
- `src/main/java/com/vnpt/avplatform/mkp/config/RedisConfig.java`

**Specification**:
```java
// MongoConfig indexes:
// partners: partner_id (unique), tenant_id, api_key_hash (single, for auth lookup), status
// plugins: plugin_id (unique), (slug, tenant_id) (compound unique), partner_id, status
// revenue_share_records: record_id (unique), partner_id, tenant_id, payout_batch_id
// payout_batches: batch_id (unique), partner_id, tenant_id

// RedisConfig: same as other services
// @Bean RedisTemplate<String, String> — String key/value for plugin catalog cache
// Key pattern: "plugin-catalog:{tenantId}" → TTL 300s

// application.yml:
// spring:
//   data:
//     mongodb:
//       uri: ${MONGODB_URI}
//       database: mkp_db
//     redis:
//       host: ${REDIS_HOST:localhost}
//       port: ${REDIS_PORT:6379}
// aes:
//   encryption-key: ${AES_ENCRYPTION_KEY} # base64-encoded 256-bit key
// minio:
//   endpoint: ${MINIO_ENDPOINT}
//   access-key: ${MINIO_ACCESS_KEY}
//   secret-key: ${MINIO_SECRET_KEY}
//   bucket: ${MINIO_BUCKET:mkp-plugins}
```

**Definition of Done**:
- [ ] Unique index on `(slug, tenant_id)` — slug unique per tenant
- [ ] Single index on `api_key_hash` for O(1) auth lookup
- [ ] `AES_ENCRYPTION_KEY` loaded from env var (not application.properties)

---

## Task Group 8: Tests

### TASK-MKP-027: Unit Tests — AuditGateService + PartnerLifecycleService

**Parent WP Task**: WP-009-T14  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/mkp/services/AuditGateServiceTest.java`
- `src/test/java/com/vnpt/avplatform/mkp/services/PartnerLifecycleServiceTest.java`

**Test Cases**:
```
AuditGateServiceTest:
1. assertBothAuditsPassed_bothPassed: no exception thrown
2. assertBothAuditsPassed_securityFailed: throws AuditNotPassedException
3. assertBothAuditsPassed_perfMissing: throws AuditNotPassedException
4. recordAuditResult_failed: plugin status → REJECTED
5. recordAuditResult_securityPassed_perfPending: plugin stays SECURITY_AUDIT
6. recordAuditResult_bothPassed: plugin auto-transitions to APPROVED
7. bl009_neitherAuditConducted: throws for missing security audit

PartnerLifecycleServiceTest:
8. registerPartner_ssrfWebhook: SSRF-unsafe URL → HTTP 400
9. transitionStatus_valid_registeredToReview: succeeds
10. transitionStatus_invalid_registeredToPublished: InvalidStateTransitionException
11. generateApiKey_rawKeyNotStored: stored hash ≠ raw key
12. suspendPartner_publishedToSuspended: succeeds
13. statusHistory_tracked: 3 transitions → 3 statusHistory entries
```

**Definition of Done**:
- [ ] Test 4: plugin status verified as REJECTED after audit FAILED
- [ ] Test 6: auto-approve after second audit passes
- [ ] Test 11: `assertNotEquals(rawKey, storedHash)` and `hashApiKey(rawKey).equals(storedHash)`

---

### TASK-MKP-028: Unit Tests — ApiKeyService + SsrfValidationService

**Parent WP Task**: WP-009-T14  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/mkp/security/ApiKeyServiceTest.java`
- `src/test/java/com/vnpt/avplatform/mkp/security/SsrfValidationServiceTest.java`

**Test Cases**:
```
ApiKeyServiceTest:
1. generateApiKey_format: starts with "mkp_"
2. generateApiKey_unique: two calls produce different keys
3. hashApiKey_deterministic: same input always produces same hash
4. verifyApiKey_valid: matching key → true
5. verifyApiKey_invalid: wrong key → false

SsrfValidationServiceTest:
6. validate_validHttps: passes
7. validate_http: throws InvalidWebhookUrlException
8. validate_loopback_127: throws
9. validate_siteLocal_10x: throws
10. validate_siteLocal_192168x: throws
11. validate_siteLocal_17216x: throws
12. validate_cloudMetadata_169254169254: throws
13. validate_linkLocal_169254x: throws
```

**Definition of Done**:
- [ ] 8 SSRF rejection test cases all pass
- [ ] Test 3: SHA-256 determinism verified
- [ ] Test 4: `hashApiKey(rawKey).equals(storedHash)` verified

---

### TASK-MKP-029: Unit Tests — RevenueShareService + PayoutBatchScheduler

**Parent WP Task**: WP-009-T14  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/mkp/services/RevenueShareServiceTest.java`
- `src/test/java/com/vnpt/avplatform/mkp/services/PayoutBatchSchedulerTest.java`

**Test Cases**:
```
RevenueShareServiceTest:
1. recordRevenue_computation: partnerShare + platformRevenue = grossRevenue (exact)
2. recordRevenue_snapshotPct: uses partner.revenueSharePct at time of call
3. recordRevenue_insertOnly: verify repository.insert() called (not save/update)
4. getSummary_sumUnpaid: sums records without payoutBatchId

PayoutBatchSchedulerTest:
5. processBatch_aboveThreshold_50000: batch created and records linked
6. processBatch_belowThreshold_49999: returns null, no batch created (carry forward)
7. processBatch_exactThreshold_50000: batch created (inclusive threshold)
8. assignPayoutBatch_called: all included records have payoutBatchId set
```

**Definition of Done**:
- [ ] Test 1: `partnerRevenueVnd + platformRevenueVnd == grossRevenueVnd` (Long arithmetic)
- [ ] Test 5 & 6: threshold boundary tests (49,999 → skip, 50,000 → process)
- [ ] Test 3: Mockito verify `repository.insert(any())` — NOT save

---

### TASK-MKP-030: Integration Tests — Partner + Plugin + Audit API

**Parent WP Task**: WP-009-T14  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/mkp/integration/PartnerControllerIT.java`
- `src/test/java/com/vnpt/avplatform/mkp/integration/PluginCatalogIT.java`

**Test Cases**:
```
PartnerControllerIT:
1. POST /api/v1/partners → 201 with partner (no bank account in response)
2. POST /api/v1/partners (SSRF webhook URL) → 400
3. PATCH /api/v1/partners/{id}/status (invalid transition) → 422
4. POST /api/v1/partners/{id}/api-key → 200 with rawApiKey (only once)

PluginCatalogIT:
5. GET /api/v1/plugins → 200 with published plugins only
6. POST /api/v1/plugins/{id}/publish (without both audits) → 422 (BL-009)
7. POST /api/v1/plugins/{id}/publish (both audits passed) → 200 PUBLISHED
8. POST /api/v1/plugins/{id}/activate → 200, installed_count incremented
9. Cache invalidated after activate: second browse fetches from DB
```

**Setup**: Testcontainers MongoDB + Redis.  
**Definition of Done**:
- [ ] Test 1: bank account not in response body
- [ ] Test 6: BL-009 enforced (422 when audits not passed)
- [ ] Test 9: Redis cache verified invalidated after activate

---

*DETAIL_PLAN_MKP v1.0.0 — MKP Marketplace & Plugin Ecosystem | VNPT AV Platform Services Provider Group*
