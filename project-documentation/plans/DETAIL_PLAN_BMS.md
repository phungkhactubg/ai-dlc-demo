# DETAIL PLAN — BMS: Billing & Subscription Management Service

**Work Package**: WP-006 | **SRS**: SRS_BMS_Billing_Subscription.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.bms`  
**Database**: MongoDB (`bms_db`) + InfluxDB (async metering) + Redis (quota hot path)  
**Events**: Kafka producer (billing-events topic, 6 partitions)  
**Critical**: Quota check MUST be < 10ms P99 — Redis INCR ONLY, NO DB on hot path  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-BMS-001 | Subscription domain model | Domain Models | 1.5h |
| TASK-BMS-002 | Invoice domain model | Domain Models | 1h |
| TASK-BMS-003 | Credit domain model (prepaid/promotional/trial) | Domain Models | 1h |
| TASK-BMS-004 | UsageRecord domain model | Domain Models | 1h |
| TASK-BMS-005 | SubscriptionRepository | Repository | 1.5h |
| TASK-BMS-006 | InvoiceRepository (INSERT-ONLY audit) | Repository | 1h |
| TASK-BMS-007 | CreditRepository | Repository | 1h |
| TASK-BMS-008 | TenantContextFilter + TenantContextHolder | Security | 1.5h |
| TASK-BMS-009 | QuotaEnforcementService (Redis INCR < 10ms P99) | Services | 2h |
| TASK-BMS-010 | SubscriptionLifecycleService (state machine) | Services | 2h |
| TASK-BMS-011 | InvoiceGenerationService (1st of month CRON) | Services | 2h |
| TASK-BMS-012 | TaxComputationService (VN/SG/EU) | Services | 2h |
| TASK-BMS-013 | CreditDeductionService (MongoDB transaction) | Services | 2h |
| TASK-BMS-014 | PaymentRetryScheduler (3x backoff) | Services | 1.5h |
| TASK-BMS-015 | InfluxDBMeteringService (async Reactor pipeline) | Services | 2h |
| TASK-BMS-016 | BillingKafkaProducer (billing-events) | Kafka | 1.5h |
| TASK-BMS-017 | BillingKafkaConsumer (consume ride + payment events) | Kafka | 1.5h |
| TASK-BMS-018 | SubscriptionController | Controllers | 1.5h |
| TASK-BMS-019 | InvoiceController | Controllers | 1h |
| TASK-BMS-020 | QuotaController | Controllers | 1h |
| TASK-BMS-021 | GlobalExceptionHandler | Controllers | 1h |
| TASK-BMS-022 | MongoConfig + InfluxDBConfig + RedisConfig | Config | 1.5h |
| TASK-BMS-023 | Unit tests: QuotaEnforcementService | Tests | 2h |
| TASK-BMS-024 | Unit tests: InvoiceGenerationService + TaxComputationService | Tests | 2h |
| TASK-BMS-025 | Unit tests: CreditDeductionService | Tests | 1.5h |
| TASK-BMS-026 | Integration tests: Billing API | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-BMS-001: Subscription Domain Model

**Parent WP Task**: WP-006-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/models/Subscription.java`
- `src/main/java/com/vnpt/avplatform/bms/models/SubscriptionStatus.java`
- `src/main/java/com/vnpt/avplatform/bms/models/PlanTier.java`

**Specification**:
```java
// SubscriptionStatus.java
public enum SubscriptionStatus { TRIAL, ACTIVE, SUSPENDED, CANCELLED, PAST_DUE }

// PlanTier.java — tenant subscription plan
public enum PlanTier { STARTER, PROFESSIONAL, ENTERPRISE }

// PlanTier quotas (monthly):
// STARTER: 1,000 trips, 10,000 events, 100 GB storage
// PROFESSIONAL: 50,000 trips, 500,000 events, 1 TB storage
// ENTERPRISE: unlimited (Long.MAX_VALUE), unlimited events, 10 TB storage

// Subscription.java
@Document(collection = "subscriptions")
public class Subscription {
    @Id private String id;

    @Field("subscription_id")
    @Indexed(unique = true)
    private String subscriptionId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed(unique = true) // one active subscription per tenant
    private String tenantId;

    @Field("plan_tier")
    @NotNull
    private PlanTier planTier;

    @Field("status")
    private SubscriptionStatus status = SubscriptionStatus.TRIAL;

    @Field("billing_cycle_day")
    private int billingCycleDay = 1; // 1st of each month

    @Field("billing_country")
    private String billingCountry; // "VN", "SG", "EU_*" — determines tax

    @Field("monthly_fee_vnd")
    private Long monthlyFeeVnd; // platform fee for this tier

    @Field("trial_ends_at")
    private Instant trialEndsAt; // TRIAL → ACTIVE/CANCELLED

    @Field("current_period_start")
    private Instant currentPeriodStart;

    @Field("current_period_end")
    private Instant currentPeriodEnd;

    @Field("cancelled_at")
    private Instant cancelledAt;

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Version
    private Long version;
}
```

**Definition of Done**:
- [ ] `@Indexed(unique = true)` on `tenantId` (one active subscription per tenant)
- [ ] `billingCountry` drives `TaxComputationService` (VN/SG/EU)
- [ ] `@Version` for optimistic locking on status transitions

---

### TASK-BMS-002: Invoice Domain Model

**Parent WP Task**: WP-006-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/models/Invoice.java`
- `src/main/java/com/vnpt/avplatform/bms/models/InvoiceStatus.java`
- `src/main/java/com/vnpt/avplatform/bms/models/InvoiceLineItem.java`

**Specification**:
```java
// InvoiceStatus.java
public enum InvoiceStatus { DRAFT, PENDING, PAID, FAILED, VOID }

// InvoiceLineItem.java (embedded)
public class InvoiceLineItem {
    private String description;     // e.g., "STARTER Plan - January 2025"
    private Long amountVnd;
    private String type;            // "SUBSCRIPTION", "USAGE_OVERAGE", "PLATFORM_FEE"
}

// Invoice.java — INSERT-ONLY (BL-008: immutable financial audit log)
@Document(collection = "invoices")
public class Invoice {
    @Id private String id;

    @Field("invoice_id")
    @Indexed(unique = true)
    private String invoiceId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("subscription_id")
    private String subscriptionId;

    @Field("billing_period_start")
    private Instant billingPeriodStart;

    @Field("billing_period_end")
    private Instant billingPeriodEnd;

    @Field("line_items")
    private List<InvoiceLineItem> lineItems;

    @Field("subtotal_vnd")
    private Long subtotalVnd;

    @Field("tax_vnd")
    private Long taxVnd;

    @Field("tax_rate")
    private double taxRate; // e.g., 0.10 for 10% VAT

    @Field("tax_type")
    private String taxType; // "VN_VAT", "SG_GST", "EU_REVERSE_CHARGE"

    @Field("total_vnd")
    private Long totalVnd; // subtotal + tax

    @Field("status")
    private InvoiceStatus status;

    @Field("credits_applied_vnd")
    private Long creditsAppliedVnd = 0L; // credits deducted before payment

    @Field("amount_due_vnd")
    private Long amountDueVnd; // total - credits_applied

    @Field("payment_transaction_id")
    private String paymentTransactionId; // from PAY service

    @Field("payment_attempts")
    private int paymentAttempts = 0; // max 3

    @Field("created_at")
    @Indexed
    private Instant createdAt = Instant.now(); // auto-created 1st of month 00:00 UTC
}
```

**Definition of Done**:
- [ ] Invoice is INSERT-ONLY (BL-008: immutable audit log)
- [ ] `amountDueVnd = totalVnd - creditsAppliedVnd`
- [ ] `paymentAttempts` tracked for retry logic (max 3)

---

### TASK-BMS-003: Credit Domain Model

**Parent WP Task**: WP-006-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/models/Credit.java`
- `src/main/java/com/vnpt/avplatform/bms/models/CreditType.java`

**Specification**:
```java
// CreditType.java — usage priority order
public enum CreditType {
    PREPAID(1),     // highest priority — use first
    PROMOTIONAL(2), // second priority
    TRIAL(3);       // lowest priority — use last

    private final int priority;
}

// Credit.java
@Document(collection = "credits")
public class Credit {
    @Id private String id;

    @Field("credit_id")
    @Indexed(unique = true)
    private String creditId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("type")
    private CreditType type;

    @Field("balance_vnd")
    private Long balanceVnd; // remaining balance

    @Field("original_amount_vnd")
    private Long originalAmountVnd; // original grant

    @Field("expires_at")
    private Instant expiresAt; // null = no expiry (PREPAID)

    @Field("is_active")
    private boolean isActive = true;

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Version
    private Long version; // optimistic locking for deduction
}
```

**Usage priority**: PREPAID → PROMOTIONAL → TRIAL  
**Transaction**: MongoDB session transaction when deducting credits from multiple credit records

**Definition of Done**:
- [ ] `CreditType` has `priority` field for ordering
- [ ] `@Version` for optimistic locking during deduction
- [ ] `expiresAt = null` for PREPAID (never expires)

---

### TASK-BMS-004: UsageRecord Domain Model

**Parent WP Task**: WP-006-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/models/UsageRecord.java`

**Specification**:
```java
@Document(collection = "usage_records")
public class UsageRecord {
    @Id private String id;

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("metric_name")
    private String metricName; // "trips", "events", "storage_gb"

    @Field("month")
    private String month; // "2025-01" format (YYYY-MM)

    @Field("count")
    private long count; // current month usage

    @Field("quota_limit")
    private long quotaLimit; // from PlanTier

    @Field("warning_threshold")
    private long warningThreshold; // 80% of quota

    @Field("last_updated_at")
    private Instant lastUpdatedAt;
}
```

**Note**: `UsageRecord` is for MongoDB persistence (end-of-day sync from Redis INCR counters).  
Real-time quota checking uses Redis counters directly.

**Definition of Done**:
- [ ] `month` in `"YYYY-MM"` format (not Instant — month is the partition key)
- [ ] `warningThreshold = quota × 0.8` (computed and stored, not dynamic)

---

## Task Group 2: Repository Layer

### TASK-BMS-005: SubscriptionRepository

**Parent WP Task**: WP-006-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/repositories/SubscriptionRepository.java`
- `src/main/java/com/vnpt/avplatform/bms/repositories/impl/SubscriptionRepositoryImpl.java`

**Specification**:
```java
public interface SubscriptionRepository {
    Subscription save(Subscription sub);
    Optional<Subscription> findByTenantId(String tenantId);
    List<Subscription> findByStatus(SubscriptionStatus status); // for billing CRON
    boolean updateStatus(String tenantId, SubscriptionStatus expectedStatus,
        SubscriptionStatus newStatus, Long version);
}
// updateStatus: atomic with optimistic lock (version check)
// findByStatus: returns all subscriptions in given status — used by InvoiceGenerationService
```

**Definition of Done**:
- [ ] `updateStatus` atomic with version check (returns false on conflict)
- [ ] `findByTenantId` uses tenant_id index (BL-001)

---

### TASK-BMS-006: InvoiceRepository (INSERT-ONLY Audit)

**Parent WP Task**: WP-006-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/repositories/InvoiceRepository.java`
- `src/main/java/com/vnpt/avplatform/bms/repositories/impl/InvoiceRepositoryImpl.java`

**Specification**:
```java
public interface InvoiceRepository {
    Invoice insert(Invoice invoice); // INSERT-ONLY (BL-008)
    Optional<Invoice> findByInvoiceId(String invoiceId);
    List<Invoice> findByTenantId(String tenantId, int page, int size);
    // Status update is the ONLY allowed modification (payment processing)
    Invoice updateStatus(String invoiceId, InvoiceStatus status, String paymentTxId, int attempts);
}
// insert() uses mongoTemplate.insert() NOT save()
// updateStatus: $set status, payment_transaction_id, payment_attempts, last_updated_at
```

**Definition of Done**:
- [ ] `insert()` NOT `save()` — enforces INSERT-ONLY semantics (BL-008)
- [ ] `updateStatus` is only allowed update (for payment result recording)

---

### TASK-BMS-007: CreditRepository

**Parent WP Task**: WP-006-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/repositories/CreditRepository.java`
- `src/main/java/com/vnpt/avplatform/bms/repositories/impl/CreditRepositoryImpl.java`

**Specification**:
```java
public interface CreditRepository {
    Credit save(Credit credit);
    List<Credit> findActiveByTenantId(String tenantId); // ordered by CreditType.priority ASC
    boolean deductFromCredit(String creditId, Long amountVnd, Long expectedVersion);
}
// findActiveByTenantId: is_active=true, expires_at > now (or null), ordered by type.priority
// deductFromCredit: atomic with version check
//   Query: { credit_id, version: expectedVersion, balance_vnd: { $gte: amountVnd } }
//   Update: { $inc: { balance_vnd: -amountVnd }, $inc: { version: 1 }, $set: last_updated_at }
//   Returns: matchedCount == 1
```

**Definition of Done**:
- [ ] Ordered by `CreditType.priority` (PREPAID=1 first, TRIAL=3 last)
- [ ] `deductFromCredit` atomic (no race condition on concurrent deductions)

---

## Task Group 3: Security

### TASK-BMS-008: TenantContextFilter + TenantContextHolder

**Parent WP Task**: WP-006-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/bms/security/TenantContextHolder.java`

**Specification**: Identical pattern to TMS (TASK-TMS-008/009).
```java
// OncePerRequestFilter, @Order(1)
// Extract from JWT "tenant_id" OR "X-Tenant-ID" header
// finally: TenantContextHolder.clear()
```

**Definition of Done**:
- [ ] `clear()` in `finally` block
- [ ] `@Order(1)` priority

---

## Task Group 4: Core Services

### TASK-BMS-009: QuotaEnforcementService (Redis INCR < 10ms P99)

**Parent WP Task**: WP-006-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/QuotaEnforcementService.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/QuotaEnforcementServiceImpl.java`

**Specification**:
```java
public interface QuotaEnforcementService {
    QuotaCheckResult checkAndIncrement(String tenantId, String metricName, long amount);
    long getUsage(String tenantId, String metricName); // for display
}

// Redis key: "quota:{tenantId}:{month}:{metricName}"
// month = YearMonth.now().toString() e.g., "2025-01"
// TTL: set once at month start = seconds until end of month

// checkAndIncrement() — MUST be < 10ms P99:
//   1. Execute Redis INCRBY key amount → newCount
//      (INCRBY is atomic, creates key if not exists)
//   2. If newCount == amount (first increment this month):
//      Set TTL: EXPIREAT key {startOfNextMonth.epochSecond}
//   3. Look up quota limit from local cache (ConcurrentHashMap, populated at startup):
//      quotaLimits.get(tenantId + ":" + metricName)
//      (loaded from MongoDB subscription at startup + on subscription change event)
//   4. If newCount > quotaLimit:
//      // Check: was it already over before? (newCount - amount >= quotaLimit)
//      If was not over before: DECRBY key amount (rollback — don't count)
//      throw QuotaExceededException (HTTP 429 "QUOTA_EXCEEDED")
//   5. If newCount >= warningThreshold (80%):
//      // Publish warning event (async, non-blocking — does NOT delay quota check)
//      CompletableFuture.runAsync(() -> kafkaProducer.publishQuotaWarning(tenantId, metricName, newCount, quotaLimit))

// CRITICAL: NO MongoDB query in this method — Redis INCR only
// CRITICAL: Quota limits loaded from local ConcurrentHashMap (not DB per request)

// Load quotaLimits at startup:
//   @PostConstruct void loadAllQuotas() {
//       subscriptionRepository.findAll().forEach(sub -> {
//           PlanTier tier = sub.getPlanTier();
//           quotaLimits.put(sub.getTenantId() + ":trips", tier.getTripQuota());
//           quotaLimits.put(sub.getTenantId() + ":events", tier.getEventQuota());
//       });
//   }
// Update quotaLimits when subscription changes via Kafka event (billing.subscription_changed)
```

**Definition of Done**:
- [ ] ZERO MongoDB reads in `checkAndIncrement` — Redis INCR only
- [ ] Quota limits in `ConcurrentHashMap` (local in-memory, updated via Kafka)
- [ ] Warning event published ASYNC (non-blocking, does not add latency)
- [ ] `QuotaServiceTest`: P99 < 10ms verified with 1000 calls (mock Redis)
- [ ] Warning threshold: 80% of quota limit
- [ ] HTTP 429 with body `{ error: "QUOTA_EXCEEDED", metric: "trips", limit: 1000, current: 1001 }`

---

### TASK-BMS-010: SubscriptionLifecycleService (State Machine)

**Parent WP Task**: WP-006-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/SubscriptionLifecycleService.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/SubscriptionLifecycleServiceImpl.java`

**Specification**:
```java
public interface SubscriptionLifecycleService {
    Subscription createSubscription(String tenantId, PlanTier tier, String billingCountry);
    Subscription upgrade(String tenantId, PlanTier newTier);
    Subscription cancel(String tenantId);
    Subscription suspend(String tenantId, String reason); // on payment failure
    Subscription reactivate(String tenantId); // on payment success
}

// Valid transitions:
// TRIAL → [ACTIVE, CANCELLED]
// ACTIVE → [SUSPENDED, CANCELLED]
// SUSPENDED → [ACTIVE (reactivate on payment), CANCELLED]
// CANCELLED → [] (terminal)
// PAST_DUE → [ACTIVE (payment success), CANCELLED (3 retry failures)]

// createSubscription():
//   1. Set status = TRIAL, trialEndsAt = now() + 14 days
//   2. Set currentPeriodStart = now(), currentPeriodEnd = now() + 30 days
//   3. monthlyFeeVnd = PlanTier.getMonthlyFee()
//   4. Load quotaLimits into QuotaEnforcementService.quotaLimits (in-memory)
//   5. Publish Kafka: billing.subscription_created

// cancel():
//   1. Transition to CANCELLED, cancelledAt = now()
//   2. Do NOT prorate — access continues until current period end
//   3. Publish Kafka: billing.subscription_cancelled (NCS will send cancellation email)

// suspend() — triggered by PaymentRetryScheduler after 3 failures:
//   1. Transition ACTIVE → SUSPENDED
//   2. Publish Kafka: billing.subscription_suspended (NCS alerts tenant admin)
```

**Definition of Done**:
- [ ] Invalid transitions throw `SubscriptionTransitionException` (HTTP 409)
- [ ] Trial period: 14 days
- [ ] Cancel: access continues until period end (no immediate cutoff)
- [ ] Kafka events published on every transition

---

### TASK-BMS-011: InvoiceGenerationService (1st of Month CRON)

**Parent WP Task**: WP-006-T05  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/InvoiceGenerationService.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/InvoiceGenerationServiceImpl.java`

**Specification**:
```java
public interface InvoiceGenerationService {
    void generateMonthlyInvoices(); // @Scheduled CRON — 1st of month 00:00 UTC
    Invoice generateForTenant(String tenantId, YearMonth billingMonth);
}

// @Scheduled(cron = "0 0 0 1 * *", zone = "UTC") — runs 1st of each month at midnight UTC

// generateMonthlyInvoices():
//   1. Find all ACTIVE subscriptions
//   2. For each subscription: generateForTenant(sub.getTenantId(), YearMonth.now().minusMonths(1))
//      NOTE: generate for PREVIOUS month (January invoice generated on Feb 1st)
//   3. Trigger payment: paymentRetryScheduler.schedulePayment(invoice)

// generateForTenant():
//   1. Get subscription for tenantId
//   2. Get usage from Redis (trips, events, storage) for the billing month
//   3. Compute overage charges if usage > planTier.quota
//   4. Build line items:
//      - "STARTER Plan - {month}": monthlyFeeVnd
//      - If trip overage: "Trip Overage: {overageCount} trips × {unitPrice}": overageVnd
//   5. subtotal = sum of line items
//   6. TaxComputationService.compute(billingCountry, subtotal) → taxVnd, taxRate, taxType
//   7. total = subtotal + taxVnd
//   8. CreditDeductionService.deductCredits(tenantId, total) → creditsApplied
//   9. amountDue = total - creditsApplied
//   10. Insert Invoice (INSERT-ONLY, BL-008)
//   11. Publish Kafka: billing.invoice_generated
```

**Definition of Done**:
- [ ] CRON: `"0 0 0 1 * *"` in UTC timezone
- [ ] Generates for PREVIOUS month (not current month)
- [ ] Credits applied before determining `amountDue`
- [ ] Invoice created via `InvoiceRepository.insert()` (INSERT-ONLY, BL-008)
- [ ] `InvoiceGenerationServiceTest`: CRON trigger test with mocked clock

---

### TASK-BMS-012: TaxComputationService (VN/SG/EU)

**Parent WP Task**: WP-006-T06  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/TaxComputationService.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/TaxComputationServiceImpl.java`

**Specification**:
```java
public interface TaxComputationService {
    TaxResult compute(String billingCountry, Long subtotalVnd);
}

// TaxResult: { taxVnd, taxRate, taxType, taxJurisdiction }

// Tax rules:
// billingCountry = "VN": VAT 10% on subtotalVnd → taxType = "VN_VAT"
//   taxVnd = subtotalVnd × 0.10, rounded HALF_UP
// billingCountry = "SG": GST 9% → taxType = "SG_GST"
//   taxVnd = subtotalVnd × 0.09, rounded HALF_UP
// billingCountry starts with "EU_": EU Reverse Charge (B2B — tenant pays VAT themselves)
//   taxVnd = 0, taxType = "EU_REVERSE_CHARGE"
//   NOTE: Tenant must provide valid VAT registration number for EU reverse charge
//   If no VAT number on file: apply EU standard VAT 20% (use maxVAT = 20% as safe default)
// billingCountry = other: no tax (international), taxVnd = 0, taxType = "NO_TAX"

// compute():
//   switch (billingCountry) {
//     case "VN": return new TaxResult(subtotalVnd × 0.10, 0.10, "VN_VAT");
//     case "SG": return new TaxResult(subtotalVnd × 0.09, 0.09, "SG_GST");
//     default:
//       if (billingCountry.startsWith("EU_")) {
//         boolean hasVatNumber = tenantService.hasValidVatNumber(billingCountry.substring(3));
//         if (hasVatNumber) return new TaxResult(0, 0.0, "EU_REVERSE_CHARGE");
//         else return new TaxResult(subtotalVnd × 0.20, 0.20, "EU_STANDARD_VAT");
//       }
//       return new TaxResult(0, 0.0, "NO_TAX");
//   }
// All multiplication: BigDecimal, then convert to Long (round HALF_UP)
```

**Definition of Done**:
- [ ] VN VAT: 10% exactly
- [ ] SG GST: 9% exactly
- [ ] EU: 0% with reverse charge (or 20% if no VAT number)
- [ ] All arithmetic via `BigDecimal`, rounded `HALF_UP` to Long (VND whole number)
- [ ] `TaxComputationServiceTest`: VN/SG/EU-with-VAT/EU-without-VAT/OTHER cases

---

### TASK-BMS-013: CreditDeductionService (MongoDB Transaction)

**Parent WP Task**: WP-006-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/CreditDeductionService.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/CreditDeductionServiceImpl.java`

**Specification**:
```java
public interface CreditDeductionService {
    Long deductCredits(String tenantId, Long amountToDeduct); // returns total deducted
}

// deductCredits() — MUST use MongoDB session transaction:
//   MongoClient client = ...;
//   return client.startSession() → session.withTransaction(() -> {
//     1. Load active credits: creditRepository.findActiveByTenantId(tenantId)
//        (ordered by priority: PREPAID=1, PROMOTIONAL=2, TRIAL=3)
//     2. Iterate credits in priority order:
//        for (Credit credit : credits) {
//          if (remainingAmount <= 0) break;
//          Long deductable = Math.min(credit.getBalanceVnd(), remainingAmount);
//          boolean success = creditRepository.deductFromCredit(credit.getCreditId(), deductable, credit.getVersion());
//          if (!success) throw new OptimisticLockException(); // transaction will retry
//          remainingAmount -= deductable;
//          totalDeducted += deductable;
//          if (credit.getBalanceVnd() - deductable == 0) {
//              credit.setIsActive(false);
//              creditRepository.save(credit);
//          }
//        }
//     3. Return totalDeducted
//   });

// If amountToDeduct > total available credits: deduct all available credits, return total available
// (remaining amountDue is charged to payment gateway by PAY service)
```

**Definition of Done**:
- [ ] MongoDB session transaction wraps all credit deductions (atomic)
- [ ] Priority order: PREPAID → PROMOTIONAL → TRIAL (never reversed)
- [ ] `OptimisticLockException` within transaction triggers automatic MongoDB retry
- [ ] Exhausted credits (`balanceVnd = 0`) marked `isActive = false`
- [ ] `CreditDeductionServiceTest`: multi-credit partial deduction test

---

### TASK-BMS-014: PaymentRetryScheduler (3× Backoff)

**Parent WP Task**: WP-006-T08  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/PaymentRetryScheduler.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/PaymentRetrySchedulerImpl.java`

**Specification**:
```java
public interface PaymentRetryScheduler {
    void schedulePayment(Invoice invoice);
    void retryFailedInvoices(); // @Scheduled — checks for due retries
}

// Retry backoff (3 attempts):
//   Attempt 1: immediate (on invoice generation)
//   Attempt 2: initial attempt + 5 minutes
//   Attempt 3: initial attempt + 15 minutes
//   Attempt 4: initial attempt + 1 hour
//   If all fail: suspend subscription, mark invoice FAILED

// retryFailedInvoices() @Scheduled(fixedRate = 60000) — runs every minute:
//   1. Find invoices with status=PENDING AND paymentAttempts < 3 AND retryAfter <= now()
//   2. For each: call PAY service to charge amountDueVnd
//      POST /api/v1/payments/initiate { amount: invoice.amountDueVnd, tenantId, invoiceId }
//   3. On success: invoiceRepository.updateStatus(PAID)
//                  subscriptionLifecycleService.reactivate() if SUSPENDED
//   4. On failure: invoiceRepository.updateStatus(PENDING, attempts++)
//                  if attempts == 3: invoiceRepository.updateStatus(FAILED)
//                                    subscriptionLifecycleService.suspend()
//   5. Publish Kafka: billing.payment_success or billing.payment_failure

// Redis key to track retry schedule: "invoice_retry:{invoiceId}:retryAfter" = epochSecond
// Backoff delays: [0, 5×60, 15×60, 60×60] seconds
```

**Definition of Done**:
- [ ] 3 retry attempts with backoff: 5min → 15min → 1h
- [ ] After 3 failures: subscription suspended, invoice marked FAILED
- [ ] Scheduler runs every minute (fixed rate)
- [ ] Idempotent: duplicate scheduler triggers for same invoice do nothing extra

---

### TASK-BMS-015: InfluxDBMeteringService (Async Reactor Pipeline)

**Parent WP Task**: WP-006-T09  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/services/MeteringService.java`
- `src/main/java/com/vnpt/avplatform/bms/services/impl/InfluxDBMeteringServiceImpl.java`

**Specification**:
```java
public interface MeteringService {
    void recordEvent(String tenantId, String metricName, long value, Map<String, String> tags);
}

// InfluxDBMeteringServiceImpl — ASYNC, NON-BLOCKING Reactor pipeline:
// Library: com.influxdb:influxdb-client-java:7.x (reactive client)
// Config: spring.influxdb.url, spring.influxdb.token, spring.influxdb.org, spring.influxdb.bucket

// recordEvent():
//   Point point = Point.measurement(metricName)
//       .addTag("tenant_id", tenantId)
//       .addField("value", value)
//       .time(Instant.now(), WritePrecision.MS);
//   tags.forEach(point::addTag);
//
//   // Non-blocking Reactor write:
//   Mono.fromCallable(() -> influxDbWriteApi.writePoint(point))
//       .subscribeOn(Schedulers.boundedElastic())
//       .doOnError(e -> log.warn("InfluxDB write failed for tenant {}: {}", tenantId, e.getMessage()))
//       .onErrorComplete() // NEVER block caller on InfluxDB failure
//       .subscribe();

// CRITICAL: recordEvent() MUST return immediately (non-blocking)
// InfluxDB failure MUST NOT affect quota enforcement or billing correctness

// Metrics tracked:
//   Measurement "trips": tenant_id, status (requested/completed/cancelled), value=1
//   Measurement "payment_amount": tenant_id, gateway, value=amountVnd
//   Measurement "quota_usage": tenant_id, metric_name, value=currentCount
```

**Definition of Done**:
- [ ] `recordEvent()` returns immediately — Reactor `Mono.subscribe()` (fire-and-forget)
- [ ] InfluxDB write failure logged as WARN, not rethrown
- [ ] `onErrorComplete()` prevents error from propagating to caller
- [ ] `MeteringServiceTest`: verify `recordEvent` returns before InfluxDB write completes

---

## Task Group 5: Kafka Integration

### TASK-BMS-016: BillingKafkaProducer

**Parent WP Task**: WP-006-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/events/BillingKafkaProducer.java`
- `src/main/java/com/vnpt/avplatform/bms/events/BillingEvent.java`

**Specification**:
```java
// Topic: "billing-events" — 6 partitions
// Partition key: tenantId

// BillingEvent types:
//   "billing.invoice_generated" — monthly invoice created
//   "billing.payment_success"   — invoice paid
//   "billing.payment_failure"   — retry attempt failed
//   "billing.subscription_created"
//   "billing.subscription_suspended" — after 3 payment failures
//   "billing.subscription_cancelled"
//   "billing.quota_warning" — at 80% of quota limit

public class BillingEvent {
    private String eventId = UUID.randomUUID().toString();
    private String eventType;
    private String tenantId;
    private String subscriptionId;
    private String invoiceId;
    private Long amountVnd;
    private String metricName;  // for quota_warning events
    private Long currentUsage;  // for quota_warning events
    private Long quotaLimit;    // for quota_warning events
    private Instant timestamp = Instant.now();
}
```

**Definition of Done**:
- [ ] `billing-events` topic, 6 partitions
- [ ] `billing.quota_warning` published async (non-blocking from QuotaEnforcementService)
- [ ] Producer idempotence: `enable.idempotence=true`, `acks=all`

---

### TASK-BMS-017: BillingKafkaConsumer (Consume Ride + Payment Events)

**Parent WP Task**: WP-006-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/events/BillingKafkaConsumer.java`

**Specification**:
```java
@Component
public class BillingKafkaConsumer {
    // Consumer group: bms-consumer

    // Consumes: "ride-events" topic (ride.completed, ride.requested)
    @KafkaListener(topics = "ride-events", groupId = "bms-consumer")
    public void handleRideEvent(ConsumerRecord<String, RideEvent> record) {
        RideEvent event = record.value();
        if ("ride.completed".equals(event.getEventType())) {
            // Increment quota counter: "trips" metric
            quotaEnforcementService.checkAndIncrement(event.getTenantId(), "trips", 1);
            // Record to InfluxDB
            meteringService.recordEvent(event.getTenantId(), "trips",
                1, Map.of("status", "completed", "vehicle_type", event.getVehicleType()));
        }
    }

    // Consumes: "payment-events" topic (payment.captured)
    @KafkaListener(topics = "payment-events", groupId = "bms-consumer")
    public void handlePaymentEvent(ConsumerRecord<String, PaymentEvent> record) {
        PaymentEvent event = record.value();
        if ("payment.captured".equals(event.getEventType())) {
            // Record payment amount to InfluxDB for revenue analytics
            meteringService.recordEvent(event.getTenantId(), "payment_amount",
                event.getAmountVnd(), Map.of("gateway", event.getPaymentMethod()));
        }
    }
}
```

**Definition of Done**:
- [ ] Consumer group: `bms-consumer`
- [ ] `ride.completed` increments trip quota counter
- [ ] `payment.captured` records to InfluxDB (async, non-blocking)
- [ ] Manual offset commit after processing (not auto-commit)

---

## Task Group 6: REST Controllers

### TASK-BMS-018: SubscriptionController

**Parent WP Task**: WP-006-T11  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/controllers/SubscriptionController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/subscriptions")
public class SubscriptionController {

    // POST /api/v1/subscriptions (PLATFORM_ADMIN creates for tenant)
    @PostMapping
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    @ResponseStatus(HttpStatus.CREATED)
    public SubscriptionDTO createSubscription(@Valid @RequestBody CreateSubscriptionRequest request) { ... }

    // GET /api/v1/subscriptions/me (tenant views their own subscription)
    @GetMapping("/me")
    public SubscriptionDTO getMySubscription() {
        String tenantId = TenantContextHolder.requireTenantId();
        return subscriptionLifecycleService.getSubscription(tenantId);
    }

    // PUT /api/v1/subscriptions/me/upgrade
    @PutMapping("/me/upgrade")
    @PreAuthorize("hasRole('TENANT_ADMIN')")
    public SubscriptionDTO upgrade(@Valid @RequestBody UpgradeRequest request) { ... }

    // DELETE /api/v1/subscriptions/me
    @DeleteMapping("/me")
    @PreAuthorize("hasRole('TENANT_ADMIN')")
    public SubscriptionDTO cancel() { ... }
}
```

**Definition of Done**:
- [ ] `GET /me` scoped to caller's tenant (no `tenantId` param)
- [ ] Cancel returns 200 with updated subscription (not 204 — includes cancellation date)
- [ ] `PLATFORM_ADMIN` can create subscription for any tenant

---

### TASK-BMS-019: InvoiceController

**Parent WP Task**: WP-006-T11  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/controllers/InvoiceController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/invoices")
@PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN')")
public class InvoiceController {

    // GET /api/v1/invoices?page=0&size=12
    @GetMapping
    public List<InvoiceDTO> listInvoices(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "12") int size
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        return invoiceRepository.findByTenantId(tenantId, page, size);
    }

    // GET /api/v1/invoices/{invoiceId}
    @GetMapping("/{invoiceId}")
    public InvoiceDTO getInvoice(@PathVariable String invoiceId) { ... }
}
```

**Definition of Done**:
- [ ] Invoice list scoped to caller's tenant
- [ ] `PLATFORM_ADMIN` sees all tenants' invoices (uses `X-Tenant-ID` override)
- [ ] Default page size: 12 (monthly invoices)

---

### TASK-BMS-020: QuotaController

**Parent WP Task**: WP-006-T11  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/controllers/QuotaController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/quota")
public class QuotaController {

    // GET /api/v1/quota/usage — current month usage for all metrics
    @GetMapping("/usage")
    public QuotaUsageResponse getUsage() {
        String tenantId = TenantContextHolder.requireTenantId();
        return new QuotaUsageResponse(
            tenantId,
            quotaEnforcementService.getUsage(tenantId, "trips"),
            quotaEnforcementService.getUsage(tenantId, "events"),
            subscriptionRepository.findByTenantId(tenantId).getPlanTier()
        );
    }

    // POST /api/v1/quota/check (internal — used by other services to check before action)
    @PostMapping("/check")
    @PreAuthorize("hasRole('INTERNAL_SERVICE')")
    public ResponseEntity<QuotaCheckResult> checkQuota(
        @Valid @RequestBody QuotaCheckRequest request
    ) {
        QuotaCheckResult result = quotaEnforcementService.checkAndIncrement(
            request.getTenantId(), request.getMetricName(), request.getAmount()
        );
        if (!result.isAllowed()) return ResponseEntity.status(429).body(result);
        return ResponseEntity.ok(result);
    }
}
```

**Definition of Done**:
- [ ] `GET /usage` returns current Redis counter values (not MongoDB)
- [ ] `POST /check` is INTERNAL_SERVICE only (called by RHS before creating trip)
- [ ] HTTP 429 body includes `{ metric, current, limit, remaining }`

---

## Task Group 7: Configuration

### TASK-BMS-022: MongoConfig + InfluxDBConfig + RedisConfig

**Parent WP Task**: WP-006-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/bms/config/MongoConfig.java`
- `src/main/java/com/vnpt/avplatform/bms/config/InfluxDBConfig.java`
- `src/main/java/com/vnpt/avplatform/bms/config/RedisConfig.java`

**Specification**:
```java
// MongoConfig indexes:
// subscriptions: tenant_id (unique)
// invoices: invoice_id (unique), tenant_id, created_at
// credits: credit_id (unique), tenant_id + is_active (compound)

// InfluxDBConfig:
// @Bean InfluxDBClient influxDbClient() {
//     return InfluxDBClientFactory.create(url, token.toCharArray(), org, bucket);
// }

// RedisConfig:
// Lettuce connection pool: maxTotal=50, maxIdle=10, minIdle=5
// SSL enabled (production)
```

**Definition of Done**:
- [ ] Unique index on `subscriptions.tenant_id` (one per tenant)
- [ ] Compound index `{ tenant_id, is_active }` on credits for fast credit lookup
- [ ] InfluxDB bean configured with token auth (not username/password)

---

## Task Group 8: Tests

### TASK-BMS-023: Unit Tests — QuotaEnforcementService

**Parent WP Task**: WP-006-T12  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/bms/services/QuotaEnforcementServiceTest.java`

**Test Cases**:
```
1. underQuota_allowed: trips < 1000 → ALLOW, counter incremented
2. atWarning_publishesEvent: count reaches 800 (80% of 1000) → quota_warning event published async
3. atQuota_rejected: count reaches 1001 → QuotaExceededException (HTTP 429)
4. counterRollback_onRejection: after rejection, counter is decremented back
5. noDbQuery_inHotPath: verify NO MongoDB calls during checkAndIncrement (mock verify)
6. quotaLimits_fromLocalCache: quotaLimits ConcurrentHashMap used, not repository
7. warningEvent_doesNotDelayResponse: warning published async, method returns immediately
8. enterprisePlan_unlimited: ENTERPRISE tier → never rejected (Long.MAX_VALUE)
```

**Definition of Done**:
- [ ] Test 5: verify `SubscriptionRepository.findByTenantId()` is NEVER called during hot path
- [ ] Test 7: use `CountDownLatch` to verify async Kafka publish
- [ ] Test 8: ENTERPRISE tier quota = `Long.MAX_VALUE` → counter can increment freely

---

### TASK-BMS-024: Unit Tests — InvoiceGenerationService + TaxComputationService

**Parent WP Task**: WP-006-T12  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/bms/services/InvoiceGenerationServiceTest.java`
- `src/test/java/com/vnpt/avplatform/bms/services/TaxComputationServiceTest.java`

**InvoiceGenerationService Test Cases**:
```
1. generateForTenant_starterPlan: correct line items and amounts
2. generateForTenant_withOverage: usage > quota → overage charge included
3. generateForTenant_withCredits: credits deducted from total
4. generateForTenant_withVatVN: VN VAT 10% applied
5. cronTrigger_generatesAllActiveSubs: all ACTIVE subscriptions get invoices
```

**TaxComputationService Test Cases**:
```
1. VN_billing → 10% VAT
2. SG_billing → 9% GST
3. EU_with_VAT_number → 0% reverse charge
4. EU_without_VAT_number → 20% standard EU VAT
5. US_billing → 0% (no tax)
6. rounding_HALF_UP: 1,500,000 × 10% = 150,000 exactly
```

**Definition of Done**:
- [ ] All 11 test cases passing
- [ ] Tax arithmetic uses BigDecimal (verify no rounding errors)
- [ ] Test 2: overage rate computed from PlanTier configuration

---

### TASK-BMS-025: Unit Tests — CreditDeductionService

**Parent WP Task**: WP-006-T12  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/bms/services/CreditDeductionServiceTest.java`

**Test Cases**:
```
1. singleCredit_fullDeduction: 100,000 VND credit, 100,000 deducted → credit exhausted
2. singleCredit_partialDeduction: 100,000 credit, 50,000 deducted → 50,000 remaining
3. multiCredit_priorityOrder: PREPAID deducted before PROMOTIONAL before TRIAL
4. multiCredit_crossBoundary: PREPAID = 30,000, need 50,000 → deducts all PREPAID + 20,000 PROMOTIONAL
5. insufficientCredits: total credits < amount → deducts all available, returns total available
6. transactionRollback_onLockConflict: optimistic lock fails → transaction retries
7. exhaustedCredit_markedInactive: credit.balanceVnd=0 → isActive=false
```

**Definition of Done**:
- [ ] Test 3: priority order verified by mock call order
- [ ] Test 6: MongoDB session transaction rollback verified
- [ ] Test 7: `isActive = false` when balance reaches zero

---

### TASK-BMS-026: Integration Tests — Billing API

**Parent WP Task**: WP-006-T12  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/bms/integration/BillingControllerIT.java`

**Test Cases**:
```
1. GET /api/v1/subscriptions/me → 200 with subscription details
2. GET /api/v1/quota/usage → 200 with current usage
3. POST /api/v1/quota/check (under quota) → 200 ALLOW
4. POST /api/v1/quota/check (over quota) → 429 QUOTA_EXCEEDED
5. GET /api/v1/invoices → 200 with invoice list
6. GET /api/v1/invoices/{invoiceId} → 200 with invoice details
```

**Setup**: Testcontainers MongoDB + Redis + Kafka  
**Definition of Done**:
- [ ] Redis Testcontainer seeded with quota counters
- [ ] Test 4: verify HTTP 429 with correct body `{ error, metric, current, limit }`

---

*DETAIL_PLAN_BMS v1.0.0 — BMS Billing & Subscription Management | VNPT AV Platform Services Provider Group*
