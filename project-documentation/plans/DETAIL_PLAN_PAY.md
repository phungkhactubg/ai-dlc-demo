# DETAIL PLAN — PAY: Payment Processing Service

**Work Package**: WP-003 | **SRS**: SRS_PAY_Payment_Processing.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.pay`  
**Database**: MongoDB (`pay_db`, INSERT-ONLY collection `payment_transactions`) + Redis  
**Events**: Kafka producer (payment-events, 24 partitions)  
**Security**: PCI-DSS compliant — `pay-namespace` K8s namespace with NetworkPolicy  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-PAY-001 | PaymentTransaction domain model (INSERT-ONLY) | Domain Models | 1.5h |
| TASK-PAY-002 | Wallet domain model | Domain Models | 1h |
| TASK-PAY-003 | EscrowRecord domain model | Domain Models | 1h |
| TASK-PAY-004 | RefundRecord domain model | Domain Models | 1h |
| TASK-PAY-005 | FraudScore domain model | Domain Models | 1h |
| TASK-PAY-006 | PaymentTransactionRepository (INSERT-ONLY enforcement) | Repository | 2h |
| TASK-PAY-007 | WalletRepository (atomic balance operations) | Repository | 1.5h |
| TASK-PAY-008 | EscrowRepository | Repository | 1h |
| TASK-PAY-009 | RefundRepository | Repository | 1h |
| TASK-PAY-010 | TenantContextFilter + TenantContextHolder | Security | 1.5h |
| TASK-PAY-011 | PaymentGatewayPort interface | Adapters | 1h |
| TASK-PAY-012 | StripeGatewayAdapter | Adapters | 2h |
| TASK-PAY-013 | VNPayGatewayAdapter | Adapters | 2h |
| TASK-PAY-014 | MoMoGatewayAdapter (simulated escrow) | Adapters | 2h |
| TASK-PAY-015 | VNPTMoneyGatewayAdapter | Adapters | 1.5h |
| TASK-PAY-016 | ViettelMoneyGatewayAdapter (simulated escrow) | Adapters | 1.5h |
| TASK-PAY-017 | IdempotencyService (Redis NX) | Services | 1.5h |
| TASK-PAY-018 | FraudDetectionService (rule-based + ML async) | Services | 2h |
| TASK-PAY-019 | WalletService (balance + hold) | Services | 2h |
| TASK-PAY-020 | EscrowService (authorize → capture / release) | Services | 2h |
| TASK-PAY-021 | PaymentOrchestrationService (main flow) | Services | 2h |
| TASK-PAY-022 | RefundService | Services | 1.5h |
| TASK-PAY-023 | PaymentKafkaProducer (payment-events) | Kafka | 1.5h |
| TASK-PAY-024 | PaymentController | Controllers | 2h |
| TASK-PAY-025 | WalletController | Controllers | 1.5h |
| TASK-PAY-026 | RefundController | Controllers | 1h |
| TASK-PAY-027 | WebhookController (gateway callbacks) | Controllers | 2h |
| TASK-PAY-028 | GlobalExceptionHandler | Controllers | 1h |
| TASK-PAY-029 | MongoConfig (INSERT-ONLY validator + indexes) | Config | 2h |
| TASK-PAY-030 | RedisConfig + KafkaProducerConfig | Config | 1h |
| TASK-PAY-031 | SecurityConfig (PCI-DSS headers) | Config | 1h |
| TASK-PAY-032 | Unit tests: IdempotencyService | Tests | 1.5h |
| TASK-PAY-033 | Unit tests: FraudDetectionService | Tests | 2h |
| TASK-PAY-034 | Unit tests: EscrowService | Tests | 2h |
| TASK-PAY-035 | Unit tests: PaymentOrchestrationService | Tests | 2h |
| TASK-PAY-036 | Integration tests: Payment API flow | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-PAY-001: PaymentTransaction Domain Model (INSERT-ONLY)

**Parent WP Task**: WP-003-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/models/PaymentTransaction.java`
- `src/main/java/com/vnpt/avplatform/pay/models/PaymentStatus.java`
- `src/main/java/com/vnpt/avplatform/pay/models/PaymentMethod.java`

**Specification**:
```java
// PaymentStatus.java
public enum PaymentStatus {
    PENDING, AUTHORIZED, CAPTURED, FAILED, REFUNDED, CANCELLED
}

// PaymentMethod.java
public enum PaymentMethod {
    STRIPE, VNPAY, MOMO, VNPT_MONEY, VIETTEL_MONEY, WALLET
}

// PaymentTransaction.java — INSERT-ONLY via MongoDB validator (NO updates allowed)
@Document(collection = "payment_transactions")
public class PaymentTransaction {
    @Id private String id;

    @Field("transaction_id")
    @Indexed(unique = true)
    private String transactionId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001

    @Field("trip_id")
    @Indexed
    private String tripId;

    @Field("rider_id")
    private String riderId;

    @Field("payment_method")
    @NotNull
    private PaymentMethod paymentMethod;

    @Field("status")
    @NotNull
    private PaymentStatus status; // each status change = new INSERT document

    @Field("amount_vnd")
    @NotNull
    private Long amountVnd; // stored as Long (VND is whole number) — NOT Decimal128 for index efficiency

    @Field("currency")
    private String currency = "VND";

    @Field("idempotency_key")
    @Indexed(unique = true)
    private String idempotencyKey; // prevents duplicate payments

    @Field("gateway_transaction_id")
    private String gatewayTransactionId; // returned by payment gateway

    @Field("gateway_response_code")
    private String gatewayResponseCode;

    @Field("gateway_response_msg")
    private String gatewayResponseMsg;

    @Field("fraud_score")
    private Double fraudScore; // 0.0 – 1.0; >0.8 = rejected

    @Field("escrow_id")
    private String escrowId; // linked escrow record

    @Field("prev_transaction_id")
    private String prevTransactionId; // chain: PENDING → AUTHORIZED → CAPTURED

    @Field("created_at")
    @Indexed
    private Instant createdAt = Instant.now();

    // NOTE: NO @Version — INSERT-ONLY. No optimistic locking needed.
    // To track status history: each status change creates a NEW document with same trip_id
}
```

**Definition of Done**:
- [ ] `amountVnd` is `Long` (whole VND, not Decimal128 — for Redis INCR compatibility)
- [ ] `idempotencyKey` has `@Indexed(unique = true)` — enforces uniqueness at DB level
- [ ] `prevTransactionId` chains transactions (status history = chain of documents)
- [ ] MongoDB collection validator registered in MongoConfig to reject `update` operations

---

### TASK-PAY-002: Wallet Domain Model

**Parent WP Task**: WP-003-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/models/Wallet.java`

**Specification**:
```java
@Document(collection = "wallets")
public class Wallet {
    @Id private String id;

    @Field("wallet_id")
    @Indexed(unique = true)
    private String walletId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("owner_id")
    @Indexed
    private String ownerId; // riderId or tenantId

    @Field("owner_type")
    private String ownerType; // "RIDER" or "TENANT"

    @Field("balance_vnd")
    private Long balanceVnd = 0L; // atomic: only updated via WalletRepository with $inc

    @Field("held_balance_vnd")
    private Long heldBalanceVnd = 0L; // escrow hold: unavailable to rider

    @Field("available_balance_vnd")
    private Long availableBalanceVnd = 0L; // = balance - held

    @Field("currency")
    private String currency = "VND";

    @Field("is_active")
    private boolean isActive = true;

    @Field("last_updated_at")
    private Instant lastUpdatedAt;

    @Version
    private Long version; // optimistic locking for balance updates
}
```

**Definition of Done**:
- [ ] `balanceVnd`, `heldBalanceVnd`, `availableBalanceVnd` all `Long` (VND whole number)
- [ ] `@Version` for optimistic locking on balance updates
- [ ] `availableBalanceVnd` kept consistent: `balance - held` (maintained by WalletService)

---

### TASK-PAY-003: EscrowRecord Domain Model

**Parent WP Task**: WP-003-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/models/EscrowRecord.java`
- `src/main/java/com/vnpt/avplatform/pay/models/EscrowStatus.java`

**Specification**:
```java
// EscrowStatus.java
public enum EscrowStatus { AUTHORIZED, CAPTURED, RELEASED, FAILED }

// EscrowRecord.java
@Document(collection = "escrow_records")
public class EscrowRecord {
    @Id private String id;

    @Field("escrow_id")
    @Indexed(unique = true)
    private String escrowId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("trip_id")
    @Indexed
    private String tripId;

    @Field("rider_id")
    private String riderId;

    @Field("payment_method")
    private PaymentMethod paymentMethod;

    @Field("authorized_amount_vnd")
    private Long authorizedAmountVnd; // max amount authorized at booking

    @Field("captured_amount_vnd")
    private Long capturedAmountVnd; // final amount captured on ride.completed

    @Field("status")
    private EscrowStatus status;

    @Field("gateway_auth_code")
    private String gatewayAuthCode; // for real pre-auth (Stripe)

    @Field("is_simulated")
    private boolean isSimulated; // true for MoMo/ViettelMoney (no real pre-auth)

    @Field("authorized_at")
    private Instant authorizedAt;

    @Field("captured_at")
    private Instant capturedAt;

    @Field("expires_at")
    private Instant expiresAt; // authorized_at + 7 days (capture must happen within 7d)
}
```

**Definition of Done**:
- [ ] `expiresAt` = `authorizedAt + 7 days` (set by EscrowService.authorize())
- [ ] `isSimulated = true` for MoMo and ViettelMoney (no gateway pre-auth)
- [ ] `EscrowStatus.AUTHORIZED` on booking, `CAPTURED` on `ride.completed`

---

### TASK-PAY-004: RefundRecord Domain Model

**Parent WP Task**: WP-003-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/models/RefundRecord.java`
- `src/main/java/com/vnpt/avplatform/pay/models/RefundReason.java`
- `src/main/java/com/vnpt/avplatform/pay/models/RefundStatus.java`

**Specification**:
```java
// RefundReason.java
public enum RefundReason { TRIP_CANCELLED, ETA_LATE, DRIVER_NO_SHOW, OVERCHARGE, SYSTEM_ERROR, CUSTOMER_REQUEST }

// RefundStatus.java
public enum RefundStatus { PENDING, PROCESSED, FAILED }

// RefundRecord.java
@Document(collection = "refund_records")
public class RefundRecord {
    @Id private String id;

    @Field("refund_id")
    @Indexed(unique = true)
    private String refundId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("original_transaction_id")
    @NotBlank
    private String originalTransactionId;

    @Field("trip_id")
    private String tripId;

    @Field("rider_id")
    private String riderId;

    @Field("amount_vnd")
    @Positive
    private Long amountVnd;

    @Field("reason")
    @NotNull
    private RefundReason reason;

    @Field("status")
    private RefundStatus status = RefundStatus.PENDING;

    @Field("gateway_refund_id")
    private String gatewayRefundId; // from gateway on success

    @Field("auto_triggered")
    private boolean autoTriggered; // true if triggered by ETA >10min event (BL-005)

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Field("processed_at")
    private Instant processedAt;
}
```

**Definition of Done**:
- [ ] `autoTriggered = true` for BL-005 (ETA late > 10 min automatic refund)
- [ ] `RefundReason.ETA_LATE` is the reason code for BL-005 auto-refund
- [ ] INSERT-ONLY behavior (no status updates — refund history preserved)

---

### TASK-PAY-005: FraudScore Domain Model

**Parent WP Task**: WP-003-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/models/FraudScore.java`

**Specification**:
```java
@Document(collection = "fraud_scores")
public class FraudScore {
    @Id private String id;

    @Field("transaction_id")
    @Indexed
    private String transactionId;

    @Field("rider_id")
    @Indexed
    private String riderId;

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("rule_score")
    private double ruleScore; // 0.0–1.0, computed < 5ms

    @Field("ml_score")
    private double mlScore; // 0.0–1.0, async, < 500ms timeout; default 0.5 on timeout

    @Field("final_score")
    private double finalScore; // max(ruleScore, mlScore) or weighted combination

    @Field("rules_triggered")
    private List<String> rulesTriggered; // e.g., ["UNUSUAL_AMOUNT", "RAPID_SUCCESSIVE_PAYMENTS"]

    @Field("decision")
    private String decision; // "ALLOW", "REJECT", "REVIEW"

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Definition of Done**:
- [ ] `mlScore` defaults to `0.5` on ML timeout (neutral score)
- [ ] `finalScore > 0.8` → `decision = "REJECT"` (enforced by FraudDetectionService)
- [ ] `rulesTriggered` lists human-readable rule names

---

## Task Group 2: Repository Layer

### TASK-PAY-006: PaymentTransactionRepository (INSERT-ONLY Enforcement)

**Parent WP Task**: WP-003-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/repositories/PaymentTransactionRepository.java`
- `src/main/java/com/vnpt/avplatform/pay/repositories/impl/PaymentTransactionRepositoryImpl.java`

**Specification**:
```java
public interface PaymentTransactionRepository {
    PaymentTransaction insert(PaymentTransaction tx); // ONLY insert — NO update/replace
    Optional<PaymentTransaction> findByTransactionId(String transactionId);
    Optional<PaymentTransaction> findByIdempotencyKey(String idempotencyKey);
    List<PaymentTransaction> findByTripId(String tripId, String tenantId);
    List<PaymentTransaction> findByRiderId(String riderId, String tenantId, int page, int size);
}

// INSERT-ONLY enforcement strategy:
// 1. MongoDB Collection Validator (see TASK-PAY-029) rejects any $set/$update on the collection
// 2. Repository method named `insert()` NOT `save()` — save() would allow upsert behavior
// 3. Implementation uses mongoTemplate.insert() NOT mongoTemplate.save()

// insert() implementation:
//   try {
//       return mongoTemplate.insert(tx);
//   } catch (DuplicateKeyException e) {
//       // idempotencyKey collision
//       throw new DuplicatePaymentException("Duplicate idempotency key: " + tx.getIdempotencyKey());
//   }
```

**Definition of Done**:
- [ ] Method named `insert()` NOT `save()` — enforces semantics
- [ ] `DuplicatePaymentException` thrown on idempotency key collision
- [ ] All queries include `tenant_id` filter (BL-001)
- [ ] Test verifies that calling update on PaymentTransaction throws exception from MongoDB validator

---

### TASK-PAY-007: WalletRepository (Atomic Balance Operations)

**Parent WP Task**: WP-003-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/repositories/WalletRepository.java`
- `src/main/java/com/vnpt/avplatform/pay/repositories/impl/WalletRepositoryImpl.java`

**Specification**:
```java
public interface WalletRepository {
    Wallet save(Wallet wallet);
    Optional<Wallet> findByOwnerId(String ownerId, String tenantId);
    Optional<Wallet> findByWalletId(String walletId);
    // Atomic debit: fails if insufficient balance
    boolean debit(String walletId, Long amountVnd, Long expectedVersion);
    // Atomic credit: always succeeds if wallet exists
    boolean credit(String walletId, Long amountVnd);
    // Hold funds for escrow (moves from balance to held)
    boolean holdFunds(String walletId, Long amountVnd);
    // Release held funds (cancellation)
    boolean releaseFunds(String walletId, Long amountVnd);
}

// debit() — atomic with optimistic locking:
// Query: { wallet_id: walletId, version: expectedVersion, balance_vnd: { $gte: amountVnd } }
// Update: { $inc: { balance_vnd: -amountVnd, available_balance_vnd: -amountVnd }, $inc version: 1, $set: last_updated_at }
// Returns: updateResult.getMatchedCount() == 1

// holdFunds():
// Query: { wallet_id: walletId, available_balance_vnd: { $gte: amountVnd } }
// Update: { $inc: { held_balance_vnd: amountVnd, available_balance_vnd: -amountVnd } }
// balance_vnd unchanged — only available decreases, held increases

// releaseFunds():
// Query: { wallet_id: walletId, held_balance_vnd: { $gte: amountVnd } }
// Update: { $inc: { held_balance_vnd: -amountVnd, available_balance_vnd: amountVnd } }
```

**Definition of Done**:
- [ ] `debit` is atomic (single `updateFirst` with version check)
- [ ] `holdFunds` reduces `availableBalanceVnd` not `balanceVnd`
- [ ] Optimistic locking via `@Version` — `debit` returns false on version conflict
- [ ] `WalletRepositoryTest`: concurrent debit test — only one succeeds when insufficient balance

---

### TASK-PAY-008: EscrowRepository

**Parent WP Task**: WP-003-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/repositories/EscrowRepository.java`
- `src/main/java/com/vnpt/avplatform/pay/repositories/impl/EscrowRepositoryImpl.java`

**Specification**:
```java
public interface EscrowRepository {
    EscrowRecord save(EscrowRecord record);
    Optional<EscrowRecord> findByEscrowId(String escrowId);
    Optional<EscrowRecord> findByTripId(String tripId, String tenantId);
    EscrowRecord updateStatus(String escrowId, EscrowStatus status, Long capturedAmountVnd);
}
// updateStatus uses $set on status and captured_amount_vnd and captured_at
// tenant_id filter applied to all queries
```

**Definition of Done**:
- [ ] `findByTripId` includes `tenantId` filter (BL-001)
- [ ] `updateStatus` sets `capturedAt = Instant.now()` when status = CAPTURED

---

### TASK-PAY-009: RefundRepository

**Parent WP Task**: WP-003-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/repositories/RefundRepository.java`
- `src/main/java/com/vnpt/avplatform/pay/repositories/impl/RefundRepositoryImpl.java`

**Specification**:
```java
public interface RefundRepository {
    RefundRecord insert(RefundRecord refund); // INSERT-ONLY
    Optional<RefundRecord> findByRefundId(String refundId);
    List<RefundRecord> findByOriginalTransactionId(String originalTransactionId);
    RefundRecord updateStatus(String refundId, RefundStatus status, String gatewayRefundId);
}
```

**Definition of Done**:
- [ ] `insert()` used (not `save()`) — refund records are immutable except status update
- [ ] `updateStatus` is the ONLY allowed update (for recording gateway response)

---

## Task Group 3: Security

### TASK-PAY-010: TenantContextFilter + TenantContextHolder

**Parent WP Task**: WP-003-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/pay/security/TenantContextHolder.java`

**Specification**: Identical pattern to TMS (TASK-TMS-008/009).
```java
// TenantContextFilter: OncePerRequestFilter
// Extract from JWT "tenant_id" claim OR "X-Tenant-ID" header
// TenantContextHolder.setTenantId(tenantId)
// finally: TenantContextHolder.clear()

// TenantContextHolder: ThreadLocal<String> CONTEXT
// requireTenantId(): throws TenantContextMissingException (HTTP 400) if null
// clear(): CONTEXT.remove()
```

**Definition of Done**:
- [ ] `clear()` in `finally` block — prevents ThreadLocal leak between requests
- [ ] `@Order(1)` filter priority

---

## Task Group 4: Payment Gateway Adapters

### TASK-PAY-011: PaymentGatewayPort Interface

**Parent WP Task**: WP-003-T03  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/adapters/PaymentGatewayPort.java`
- `src/main/java/com/vnpt/avplatform/pay/adapters/PaymentGatewayRequest.java`
- `src/main/java/com/vnpt/avplatform/pay/adapters/PaymentGatewayResponse.java`

**Specification**:
```java
public interface PaymentGatewayPort {
    PaymentGatewayResponse authorize(PaymentGatewayRequest request); // pre-authorization (escrow)
    PaymentGatewayResponse capture(String authorizationCode, Long amountVnd); // finalize payment
    PaymentGatewayResponse refund(String transactionId, Long amountVnd, RefundReason reason);
    boolean supportsPreAuthorization(); // true for Stripe/VNPay; false for MoMo/ViettelMoney
    PaymentMethod getMethod(); // returns the enum for this adapter
}

// PaymentGatewayRequest:
public class PaymentGatewayRequest {
    private String idempotencyKey;    // idempotent key for dedup
    private Long amountVnd;
    private String riderId;
    private String tenantId;
    private String tripId;
    private String paymentToken;      // tokenized card/account from client
    private Map<String, String> metadata;
}

// PaymentGatewayResponse:
public class PaymentGatewayResponse {
    private boolean success;
    private String gatewayTransactionId;
    private String authorizationCode;  // for pre-auth
    private String responseCode;
    private String responseMessage;
    private String errorCode;          // null on success
}
```

**Definition of Done**:
- [ ] `supportsPreAuthorization()` returns `true` for Stripe, VNPay only
- [ ] All 5 adapters implement this interface
- [ ] `PaymentGatewayPort` is discoverable via `PaymentMethod` enum key

---

### TASK-PAY-012: StripeGatewayAdapter

**Parent WP Task**: WP-003-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/adapters/impl/StripeGatewayAdapter.java`

**Specification**:
```java
@Component
public class StripeGatewayAdapter implements PaymentGatewayPort {
    // Stripe Java SDK: com.stripe:stripe-java:24.x
    // API key loaded from: spring.stripe.api-key (environment variable, NOT in code)
    // Timeout: 30s connect, 60s read

    @Override
    public PaymentGatewayResponse authorize(PaymentGatewayRequest request) {
        // Create PaymentIntent with capture_method = "manual" (for escrow/pre-auth)
        // PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
        //     .setAmount(request.getAmountVnd())
        //     .setCurrency("vnd")
        //     .setCaptureMethod(PaymentIntentCreateParams.CaptureMethod.MANUAL)
        //     .setConfirm(true)
        //     .setPaymentMethod(request.getPaymentToken())
        //     .setIdempotencyKey(request.getIdempotencyKey())
        //     .putMetadata("trip_id", request.getTripId())
        //     .putMetadata("tenant_id", request.getTenantId())
        //     .build();
        // PaymentIntent intent = PaymentIntent.create(params, requestOptions);
        // return map intent to PaymentGatewayResponse
    }

    @Override
    public PaymentGatewayResponse capture(String authorizationCode, Long amountVnd) {
        // PaymentIntent.retrieve(authorizationCode).capture()
        // Capture with final amount (may differ from authorized)
    }

    @Override
    public PaymentGatewayResponse refund(String transactionId, Long amountVnd, RefundReason reason) {
        // RefundCreateParams.builder().setPaymentIntent(transactionId).setAmount(amountVnd)
    }

    @Override
    public boolean supportsPreAuthorization() { return true; }

    @Override
    public PaymentMethod getMethod() { return PaymentMethod.STRIPE; }
}
```

**Definition of Done**:
- [ ] API key from environment variable (NOT hardcoded)
- [ ] Idempotency key passed to Stripe `RequestOptions`
- [ ] `capture_method = MANUAL` for pre-authorization (escrow model)
- [ ] Stripe `StripeException` caught → `PaymentGatewayResponse { success: false, errorCode }`
- [ ] StripeGatewayAdapterTest: mock Stripe SDK, verify idempotency key sent

---

### TASK-PAY-013: VNPayGatewayAdapter

**Parent WP Task**: WP-003-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/adapters/impl/VNPayGatewayAdapter.java`

**Specification**:
```java
@Component
public class VNPayGatewayAdapter implements PaymentGatewayPort {
    // VNPay uses HMAC-SHA512 for request signing
    // Base URL: https://sandbox.vnpayment.vn/paymentv2/vpcpay.html (test)
    //           https://pay.vnpay.vn/vpcpay.html (prod)
    // Config: spring.vnpay.tmn-code, spring.vnpay.hash-secret, spring.vnpay.base-url

    // authorize() — VNPay pre-auth (creates a payment link/request):
    //   Build vnp_Params sorted map
    //   Required: vnp_TmnCode, vnp_Amount (amountVnd * 100 for VND), vnp_CreateDate, vnp_IpAddr, vnp_OrderInfo, vnp_ReturnUrl
    //   Sign: HMAC-SHA512 of sorted query string with hash-secret
    //   NOTE: VNPay pre-auth is "request-based" — returns redirect URL
    //         For API integration: use VNPay Token-based payment if available

    // capture() — VNPay QueryDR API to confirm transaction
    // refund() — VNPay Refund API

    @Override
    public boolean supportsPreAuthorization() { return true; }

    @Override
    public PaymentMethod getMethod() { return PaymentMethod.VNPAY; }
}
```

**Definition of Done**:
- [ ] HMAC-SHA512 signing implemented correctly
- [ ] `vnp_Amount` = amountVnd × 100 (VNPay uses cents/piastres)
- [ ] Config loaded from environment (no hardcoded credentials)
- [ ] VNPayGatewayAdapterTest: verify HMAC signature logic

---

### TASK-PAY-014: MoMoGatewayAdapter (Simulated Escrow)

**Parent WP Task**: WP-003-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/adapters/impl/MoMoGatewayAdapter.java`

**Specification**:
```java
@Component
public class MoMoGatewayAdapter implements PaymentGatewayPort {
    // MoMo: NO real pre-authorization available in their API
    // Strategy: simulated escrow via wallet hold
    //   1. authorize(): calls MoMo pay API immediately (full charge)
    //      stores amount in rider's MoMo wallet "hold" state internally
    //      sets EscrowRecord.isSimulated = true
    //   2. capture(): no-op for real gateway — just update EscrowRecord status
    //      or: if trip cancelled, trigger MoMo refund API

    // MoMo API (v2): HMAC-SHA256 signature
    // Config: spring.momo.partner-code, spring.momo.access-key, spring.momo.secret-key

    // authorize() implementation:
    //   request_type = "captureWallet" (immediate, not pre-auth)
    //   Build JSON body with HMAC-SHA256 signature
    //   POST to https://test-payment.momo.vn/v2/gateway/api/create
    //   On success: store gatewayTransactionId in EscrowRecord

    // capture() — for MoMo: NO-OP (already captured in authorize)
    //   return PaymentGatewayResponse { success: true, gatewayTransactionId: escrowRecord.getGatewayTransactionId() }

    @Override
    public boolean supportsPreAuthorization() { return false; } // KEY DIFFERENCE

    @Override
    public PaymentMethod getMethod() { return PaymentMethod.MOMO; }
}
```

**Definition of Done**:
- [ ] `supportsPreAuthorization()` returns `false`
- [ ] `authorize()` immediately captures (full charge via MoMo captureWallet)
- [ ] `capture()` is no-op (returns success with existing gatewayTransactionId)
- [ ] HMAC-SHA256 signing verified in test

---

### TASK-PAY-015: VNPTMoneyGatewayAdapter

**Parent WP Task**: WP-003-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/adapters/impl/VNPTMoneyGatewayAdapter.java`

**Specification**:
```java
@Component
public class VNPTMoneyGatewayAdapter implements PaymentGatewayPort {
    // VNPT Money internal payment system — assume REST API with Bearer token
    // Config: spring.vnpt-money.base-url, spring.vnpt-money.client-id, spring.vnpt-money.client-secret
    // Auth: OAuth2 client credentials → Bearer token (cached in Redis 25min, TTL 30min)

    // authorize(): POST /api/payment/create with escrow flag
    // capture(): POST /api/payment/{txId}/capture
    // refund(): POST /api/payment/{txId}/refund

    @Override
    public boolean supportsPreAuthorization() { return true; }

    @Override
    public PaymentMethod getMethod() { return PaymentMethod.VNPT_MONEY; }
}
```

**Definition of Done**:
- [ ] OAuth2 token cached in Redis (key: `vnpt_money_token:{clientId}` TTL 25min)
- [ ] Token refresh before expiry (25min cache for 30min token)
- [ ] All requests include idempotency key in header `X-Idempotency-Key`

---

### TASK-PAY-016: ViettelMoneyGatewayAdapter (Simulated Escrow)

**Parent WP Task**: WP-003-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/adapters/impl/ViettelMoneyGatewayAdapter.java`

**Specification**:
```java
@Component
public class ViettelMoneyGatewayAdapter implements PaymentGatewayPort {
    // Same pattern as MoMoGatewayAdapter — NO real pre-authorization
    // Config: spring.viettel-money.merchant-code, spring.viettel-money.secret-key

    @Override
    public boolean supportsPreAuthorization() { return false; }

    @Override
    public PaymentMethod getMethod() { return PaymentMethod.VIETTEL_MONEY; }
}
```

**Definition of Done**:
- [ ] `supportsPreAuthorization()` returns `false`
- [ ] `capture()` is no-op (same as MoMo pattern)
- [ ] Adapter registered in gateway router factory

---

## Task Group 5: Core Services

### TASK-PAY-017: IdempotencyService (Redis NX)

**Parent WP Task**: WP-003-T04  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/services/IdempotencyService.java`
- `src/main/java/com/vnpt/avplatform/pay/services/impl/IdempotencyServiceImpl.java`

**Specification**:
```java
public interface IdempotencyService {
    // Returns Optional.empty() if key is new (first time seen)
    // Returns Optional.of("processing") if currently being processed
    // Returns Optional.of(cachedResult) if already completed
    Optional<String> checkAndLock(String idempotencyKey);
    void completeWithResult(String idempotencyKey, String resultJson);
    void releaseLock(String idempotencyKey); // on failure, so retry is possible
}

// Redis key: "idempotency:{idempotencyKey}"
// TTL: 86400 seconds (24 hours)

// checkAndLock():
//   result = redis.execute(connection -> {
//       byte[] key = ("idempotency:" + idempotencyKey).getBytes();
//       byte[] existing = connection.stringCommands().get(key);
//       if (existing != null) return new String(existing); // already processed or processing
//       // SET NX EX 86400 with value "processing"
//       connection.stringCommands().set(key, "processing".getBytes(), Expiration.seconds(86400), SetOption.SET_IF_ABSENT);
//       return null; // means it's new
//   });
//   if result == "processing": retry up to 3x with 500ms delay, then return Optional.of("processing")
//   if result is a cached JSON response: return Optional.of(result)
//   return Optional.empty() (new request, proceed normally)

// completeWithResult(): SET key to resultJson with TTL 86400
// releaseLock(): SET key to "" (empty, but don't delete — preserve 24h window)
//   Actually: delete key so next attempt starts fresh
```

**Definition of Done**:
- [ ] Redis `SET NX EX 86400` for atomic lock acquisition
- [ ] On "processing" status: retry 3× with 500ms delay → HTTP 429 with `Retry-After: 2` header
- [ ] `completeWithResult` stores JSON response — exact same response returned for duplicate calls
- [ ] `IdempotencyServiceTest`: concurrent calls with same key → exactly one proceeds

---

### TASK-PAY-018: FraudDetectionService (Rule-Based + ML Async)

**Parent WP Task**: WP-003-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/services/FraudDetectionService.java`
- `src/main/java/com/vnpt/avplatform/pay/services/impl/FraudDetectionServiceImpl.java`
- `src/main/java/com/vnpt/avplatform/pay/services/FraudRule.java`

**Specification**:
```java
public interface FraudDetectionService {
    FraudScore evaluate(PaymentTransaction tx); // called before processing payment
}

// FraudDetectionServiceImpl — two-phase evaluation:
// Phase 1: Rule-based (< 5ms, synchronous)
//   Rules (FraudRule enum):
//     AMOUNT_EXCEEDS_THRESHOLD: amountVnd > tenant.maxSinglePaymentVnd → score += 0.5
//     RAPID_SUCCESSIVE_PAYMENTS: rider made >3 payments in last 5 min → score += 0.4
//       Check via Redis: INCR "fraud:rapid:{riderId}" EX 300 → if count > 3 → flag
//     UNUSUAL_AMOUNT: amountVnd not in rider's typical range (±3σ from mean) → score += 0.3
//       Rider mean/std from MongoDB aggregation (cached 1h in Redis)
//     MISMATCHED_LOCATION: payment geolocation ≠ trip pickup zone → score += 0.2
//   Rule score = min(1.0, sum of flagged scores)

// Phase 2: ML service (async, < 500ms timeout)
//   CompletableFuture<Double> mlFuture = CompletableFuture.supplyAsync(() -> mlFraudClient.predict(tx), mlExecutor)
//       .completeOnTimeout(0.5, 500, TimeUnit.MILLISECONDS); // default 0.5 on timeout
//   mlScore = mlFuture.get();

// Final score: max(ruleScore, mlScore)
// Decision: score > 0.8 → "REJECT"; score 0.5-0.8 → "REVIEW"; < 0.5 → "ALLOW"
// Log FraudScore document to MongoDB
```

**Definition of Done**:
- [ ] Rule-based evaluation < 5ms (Redis-only, no DB queries on hot path)
- [ ] ML timeout: 500ms → default score 0.5
- [ ] `CompletableFuture.completeOnTimeout(0.5, 500, MILLISECONDS)` used
- [ ] `score > 0.8` → payment rejected with HTTP 402 `FRAUD_DETECTED`
- [ ] `FraudDetectionServiceTest` covers: rapid payments rule, ML timeout, score combination

---

### TASK-PAY-019: WalletService (Balance + Hold)

**Parent WP Task**: WP-003-T05  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/services/WalletService.java`
- `src/main/java/com/vnpt/avplatform/pay/services/impl/WalletServiceImpl.java`

**Specification**:
```java
public interface WalletService {
    WalletDTO getWallet(String ownerId, String tenantId);
    WalletDTO topUp(String walletId, Long amountVnd, String idempotencyKey);
    boolean holdFunds(String walletId, Long amountVnd);   // for escrow
    boolean releaseFunds(String walletId, Long amountVnd); // escrow cancel
    boolean capture(String walletId, Long amountVnd);      // finalize escrow
    WalletDTO refund(String walletId, Long amountVnd);     // credit back
}

// holdFunds():
//   walletRepository.holdFunds(walletId, amountVnd)
//   If returns false: throw InsufficientBalanceException (HTTP 402 "INSUFFICIENT_WALLET_BALANCE")

// capture():
//   walletRepository.debit(walletId, amountVnd, wallet.getVersion())
//   If returns false (version conflict or insufficient): retry up to 3x, then throw
//   Publishes "wallet.debited" Kafka event

// topUp():
//   Idempotency check first
//   walletRepository.credit(walletId, amountVnd)
//   Insert PaymentTransaction (status=CAPTURED, paymentMethod=WALLET)
//   Publish "wallet.credited" Kafka event
```

**Definition of Done**:
- [ ] `holdFunds` throws `InsufficientBalanceException` (HTTP 402) on insufficient balance
- [ ] `capture` retries 3× on optimistic lock conflict before failing
- [ ] `topUp` is idempotent via `IdempotencyService`
- [ ] All balance operations logged as PaymentTransaction records (INSERT-ONLY)

---

### TASK-PAY-020: EscrowService (Authorize → Capture / Release)

**Parent WP Task**: WP-003-T06  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/services/EscrowService.java`
- `src/main/java/com/vnpt/avplatform/pay/services/impl/EscrowServiceImpl.java`

**Specification**:
```java
public interface EscrowService {
    EscrowRecord authorize(AuthorizeEscrowRequest request); // called at booking
    EscrowRecord capture(String tripId, Long finalAmountVnd); // called on ride.completed
    EscrowRecord release(String tripId); // called on trip cancellation
}

// authorize() — called by PaymentOrchestrationService at booking:
//   1. Get gateway for paymentMethod
//   2. If gateway.supportsPreAuthorization():
//       gatewayResp = gateway.authorize(request)
//       Create EscrowRecord { isSimulated: false, gatewayAuthCode: gatewayResp.authorizationCode }
//   3. Else (MoMo/ViettelMoney):
//       gatewayResp = gateway.authorize(request) // immediate charge
//       walletService.holdFunds(riderId, amountVnd) // soft hold in our wallet
//       Create EscrowRecord { isSimulated: true }
//   4. escrow.expiresAt = Instant.now().plus(7, ChronoUnit.DAYS)
//   5. Save EscrowRecord, return

// capture() — triggered by ride.completed Kafka event:
//   1. Load EscrowRecord by tripId
//   2. If !isSimulated: gateway.capture(authCode, finalAmountVnd)
//   3. If isSimulated: wallet already charged, just update EscrowRecord status
//   4. Update EscrowRecord.status = CAPTURED, capturedAmountVnd = finalAmountVnd
//   5. Insert PaymentTransaction with status=CAPTURED
//   6. Publish payment.captured event

// release() — on trip cancellation:
//   1. Load EscrowRecord by tripId
//   2. If !isSimulated: gateway.refund(gatewayAuthCode, authorizedAmount)
//   3. If isSimulated: walletService.releaseFunds(riderId, authorizedAmount)
//   4. Update EscrowRecord.status = RELEASED
//   5. Insert PaymentTransaction with status=REFUNDED (if refund applies)
```

**Definition of Done**:
- [ ] `authorize` sets `expiresAt = now + 7 days`
- [ ] `capture` uses `finalAmountVnd` (actual fare, may differ from authorized)
- [ ] `release` triggers gateway refund for real pre-auth OR wallet release for simulated
- [ ] `EscrowServiceTest`: happy path capture, cancellation release, expiry check

---

### TASK-PAY-021: PaymentOrchestrationService (Main Flow)

**Parent WP Task**: WP-003-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/services/PaymentOrchestrationService.java`
- `src/main/java/com/vnpt/avplatform/pay/services/impl/PaymentOrchestrationServiceImpl.java`

**Specification**:
```java
public interface PaymentOrchestrationService {
    PaymentResult initiatePayment(InitiatePaymentRequest request);
}

// initiatePayment() — the main entry point:
//   1. IdempotencyService.checkAndLock(idempotencyKey)
//      If result present: return cached result (HTTP 200 with same response)
//      If "processing": return HTTP 429 with Retry-After: 2
//   2. FraudDetectionService.evaluate(tx)
//      If score > 0.8: throw FraudDetectedException (HTTP 402 "FRAUD_DETECTED")
//      If "REVIEW": flag for manual review but proceed (BL: score 0.5-0.8)
//   3. EscrowService.authorize(request) — pre-auth or immediate charge
//   4. Insert PaymentTransaction { status: AUTHORIZED }
//   5. IdempotencyService.completeWithResult(key, resultJson)
//   6. Publish Kafka: payment.authorized
//   7. Return PaymentResult { transactionId, escrowId, status: AUTHORIZED }

// On any step failure:
//   Insert PaymentTransaction { status: FAILED }
//   IdempotencyService.releaseLock(key) — allow retry
//   Throw appropriate exception
```

**Definition of Done**:
- [ ] Idempotency check is FIRST operation (before fraud check)
- [ ] On fraud > 0.8: HTTP 402 with body `{ error: "FRAUD_DETECTED", fraud_score: X.XX }`
- [ ] On success: inserts AUTHORIZED transaction (INSERT-ONLY)
- [ ] `completeWithResult` called on success (cached for future duplicate calls)
- [ ] `PaymentOrchestrationServiceTest`: idempotent duplicate call returns same result

---

### TASK-PAY-022: RefundService

**Parent WP Task**: WP-003-T07  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/services/RefundService.java`
- `src/main/java/com/vnpt/avplatform/pay/services/impl/RefundServiceImpl.java`

**Specification**:
```java
public interface RefundService {
    RefundRecord initiateRefund(InitiateRefundRequest request);
    void processAutoRefund(String tripId, Long refundAmountVnd, RefundReason reason); // BL-005 ETA trigger
}

// initiateRefund():
//   1. Load original PaymentTransaction by transactionId
//   2. Check: status == CAPTURED (only captured payments can be refunded)
//   3. Get gateway for paymentMethod
//   4. gateway.refund(gatewayTransactionId, amountVnd, reason)
//   5. Insert RefundRecord { status: PROCESSED or FAILED }
//   6. Publish Kafka: payment.refunded

// processAutoRefund() — BL-005: triggered by ETA_LATE event from RHS:
//   autoTriggered = true, reason = RefundReason.ETA_LATE
//   Proceeds with same flow as initiateRefund
```

**Definition of Done**:
- [ ] `processAutoRefund` sets `autoTriggered = true`
- [ ] Refund requires original transaction status = CAPTURED
- [ ] HTTP 409 if refund already exists for this transactionId (prevent double refund)
- [ ] Kafka `payment.refunded` event published on success

---

## Task Group 6: Kafka Integration

### TASK-PAY-023: PaymentKafkaProducer

**Parent WP Task**: WP-003-T08  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/events/PaymentKafkaProducer.java`
- `src/main/java/com/vnpt/avplatform/pay/events/PaymentEvent.java`

**Specification**:
```java
// Topic: "payment-events" — 24 partitions (high volume)
// Partition key: tenantId

// PaymentEvent types:
//   "payment.authorized" — on escrow authorize
//   "payment.captured"   — on ride.completed capture
//   "payment.refunded"   — on refund processed
//   "payment.failed"     — on gateway failure

public class PaymentEvent {
    private String eventId = UUID.randomUUID().toString();
    private String eventType;
    private String tenantId;
    private String transactionId;
    private String tripId;
    private String riderId;
    private Long amountVnd;
    private String paymentMethod;
    private String status;
    private Instant timestamp = Instant.now();
}

// KafkaTemplate config: acks=all, retries=3, enable.idempotence=true
```

**Definition of Done**:
- [ ] Topic `payment-events` with 24 partitions
- [ ] Partition key = `tenantId`
- [ ] Producer idempotence enabled (`enable.idempotence=true`, `acks=all`)
- [ ] `PaymentKafkaProducerTest`: event type and partition key verified

---

## Task Group 7: REST Controllers

### TASK-PAY-024: PaymentController

**Parent WP Task**: WP-003-T09  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/controllers/PaymentController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    // POST /api/v1/payments/initiate
    @PostMapping("/initiate")
    public ResponseEntity<PaymentResult> initiatePayment(
        @Valid @RequestBody InitiatePaymentRequest request,
        @RequestHeader("X-Idempotency-Key") @NotBlank String idempotencyKey
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        request.setIdempotencyKey(idempotencyKey);
        request.setTenantId(tenantId);
        return ResponseEntity.ok(paymentOrchestrationService.initiatePayment(request));
    }

    // GET /api/v1/payments/{transactionId}
    @GetMapping("/{transactionId}")
    public PaymentTransactionDTO getPayment(@PathVariable String transactionId) { ... }

    // GET /api/v1/payments?trip_id=xxx
    @GetMapping
    public List<PaymentTransactionDTO> getPaymentsByTrip(@RequestParam String tripId) { ... }
}

// InitiatePaymentRequest validation:
//   paymentMethod: @NotNull
//   amountVnd: @Positive @Min(1000) // min 1,000 VND
//   riderId: @NotBlank
//   tripId: @NotBlank
//   paymentToken: @NotBlank (tokenized payment credentials)
```

**Definition of Done**:
- [ ] `X-Idempotency-Key` header is mandatory (HTTP 400 if missing)
- [ ] `amountVnd` minimum 1,000 VND validated
- [ ] Tenant isolated: GET endpoints include `tenantId` filter
- [ ] HTTP 429 returned when idempotency key shows "processing"

---

### TASK-PAY-025: WalletController

**Parent WP Task**: WP-003-T09  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/controllers/WalletController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/wallets")
public class WalletController {

    // GET /api/v1/wallets/me
    @GetMapping("/me")
    public WalletDTO getMyWallet(
        @RequestHeader("X-Rider-ID") String riderId
    ) { ... }

    // POST /api/v1/wallets/top-up
    @PostMapping("/top-up")
    public WalletDTO topUp(
        @Valid @RequestBody TopUpRequest request,
        @RequestHeader("X-Idempotency-Key") @NotBlank String idempotencyKey
    ) { ... }

    // GET /api/v1/wallets/{walletId}/transactions
    @GetMapping("/{walletId}/transactions")
    public List<PaymentTransactionDTO> getTransactions(
        @PathVariable String walletId,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) { ... }
}
// TopUpRequest: amountVnd @Positive @Min(10000) (min 10,000 VND top-up)
```

**Definition of Done**:
- [ ] `GET /me` uses `riderId` from header (not path — privacy)
- [ ] `top-up` idempotent via `X-Idempotency-Key`
- [ ] Transaction list scoped to wallet owner (tenant isolation)

---

### TASK-PAY-027: WebhookController (Gateway Callbacks)

**Parent WP Task**: WP-003-T09  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/controllers/WebhookController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/webhooks/payment")
public class WebhookController {

    // POST /api/v1/webhooks/payment/stripe
    @PostMapping("/stripe")
    public ResponseEntity<String> stripeWebhook(
        @RequestBody String payload,
        @RequestHeader("Stripe-Signature") String signature
    ) {
        // Verify Stripe signature: Stripe.constructEvent(payload, signature, endpointSecret)
        // Parse event type: payment_intent.succeeded, payment_intent.payment_failed
        // Update EscrowRecord and PaymentTransaction accordingly
        return ResponseEntity.ok("received");
    }

    // POST /api/v1/webhooks/payment/vnpay
    @PostMapping("/vnpay")
    public String vnpayWebhook(@RequestParam Map<String, String> params) {
        // Verify VNPay HMAC-SHA512 signature
        // Parse vnp_ResponseCode: "00" = success
        return "RspCode=00&Message=Confirm Success";
    }

    // POST /api/v1/webhooks/payment/momo
    @PostMapping("/momo")
    public ResponseEntity<Map<String, String>> momoWebhook(@RequestBody MoMoCallbackBody body) {
        // Verify MoMo HMAC-SHA256 signature
        // resultCode: 0 = success
        return ResponseEntity.ok(Map.of("message", "ok"));
    }
}
// All webhook endpoints are PUBLIC (no JWT auth) but signature-verified
// Each webhook: if signature invalid → return HTTP 400 IMMEDIATELY (no processing)
```

**Definition of Done**:
- [ ] Each webhook verifies its gateway-specific signature FIRST before processing
- [ ] Invalid signature → HTTP 400 immediately (no processing, no logging of sensitive data)
- [ ] Webhook endpoints exempt from `TenantContextFilter` (`/api/v1/webhooks/**` excluded)
- [ ] Idempotent: duplicate webhook events for same transaction → idempotent update

---

## Task Group 8: Configuration

### TASK-PAY-029: MongoConfig (INSERT-ONLY Validator + Indexes)

**Parent WP Task**: WP-003-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/config/MongoConfig.java`

**Specification**:
```java
@Configuration
public class MongoConfig implements ApplicationListener<ContextRefreshedEvent> {

    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        // INSERT-ONLY validator for payment_transactions:
        Document validator = new Document("$jsonSchema", new Document()
            .append("bsonType", "object")
        );
        // MongoDB collection validator to reject updates:
        // Use command:
        // db.runCommand({ collMod: "payment_transactions", validator: {}, validationAction: "error" })
        // Then apply an application-level check in the repository layer as primary enforcement
        //
        // PRIMARY enforcement: Repository only calls mongoTemplate.insert() never .save()
        // SECONDARY enforcement: MongoDB validator that rejects any document where created_at is changed

        // Indexes for payment_transactions:
        mongoTemplate.indexOps("payment_transactions").ensureIndex(
            new Index().on("transaction_id", ASC).unique()
        );
        mongoTemplate.indexOps("payment_transactions").ensureIndex(
            new Index().on("idempotency_key", ASC).unique()
        );
        mongoTemplate.indexOps("payment_transactions").ensureIndex(
            new Index().on("trip_id", ASC)
        );
        mongoTemplate.indexOps("payment_transactions").ensureIndex(
            new CompoundIndexDefinition(new Document("tenant_id", 1).append("rider_id", 1))
        );

        // Wallets indexes
        mongoTemplate.indexOps("wallets").ensureIndex(
            new CompoundIndexDefinition(new Document("owner_id", 1).append("tenant_id", 1)).unique()
        );

        // Escrow records indexes
        mongoTemplate.indexOps("escrow_records").ensureIndex(
            new CompoundIndexDefinition(new Document("trip_id", 1).append("tenant_id", 1)).unique()
        );
    }
}
```

**Definition of Done**:
- [ ] `transaction_id` unique index
- [ ] `idempotency_key` unique index (DB-level dedup backup)
- [ ] Compound unique index `{ owner_id, tenant_id }` on wallets
- [ ] Compound unique index `{ trip_id, tenant_id }` on escrow_records (one escrow per trip)

---

### TASK-PAY-031: SecurityConfig (PCI-DSS Headers)

**Parent WP Task**: WP-003-T01 (security)  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/pay/config/SecurityConfig.java`

**Specification**:
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .headers(headers -> headers
                .contentSecurityPolicy(csp -> csp.policyDirectives("default-src 'self'"))
                .frameOptions(fo -> fo.deny())
                .httpStrictTransportSecurity(hsts -> hsts
                    .includeSubDomains(true)
                    .maxAgeInSeconds(31536000) // 1 year
                )
            )
            .csrf(csrf -> csrf.disable()) // API-only service
            .sessionManagement(session -> session.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/webhooks/**").permitAll() // signature-verified externally
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            // JWT resource server
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .addFilterBefore(tenantContextFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
// PCI-DSS requirements:
// - TLS 1.2+ only (configured in K8s NetworkPolicy)
// - No sensitive data in logs (mask card numbers, CVV)
// - HSTS header mandatory
```

**Definition of Done**:
- [ ] HSTS header: `max-age=31536000; includeSubDomains`
- [ ] Webhook endpoints permitted without JWT
- [ ] Health check endpoint permitted without auth
- [ ] JWT OAuth2 resource server configured

---

## Task Group 9: Tests

### TASK-PAY-032: Unit Tests — IdempotencyService

**Parent WP Task**: WP-003-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/pay/services/IdempotencyServiceTest.java`

**Test Cases**:
```
1. newKey_returnsEmpty: first call returns Optional.empty()
2. processingKey_returns429: "processing" value → HTTP 429
3. completedKey_returnsCached: completed result returned unchanged
4. concurrentCalls_onlyOneProceeds: mock Redis NX, verify exactly one acquires lock
5. releaseLock_allowsRetry: after release, next call returns Optional.empty()
```

**Definition of Done**:
- [ ] 5 test cases passing
- [ ] Test 4: `RedisTemplate` mock verifies `SET NX` called
- [ ] Test 3: serialized JSON response returned verbatim

---

### TASK-PAY-033: Unit Tests — FraudDetectionService

**Parent WP Task**: WP-003-T10  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/pay/services/FraudDetectionServiceTest.java`

**Test Cases**:
```
1. noRulesTriggered_score_0.0 → ALLOW
2. amountExceedsThreshold_score_0.5
3. rapidSuccessivePayments_score_0.4
4. multipleRules_combined_score_capped_1.0
5. mlTimeout_defaultScore_0.5
6. mlScore_0.9_overridesRuleScore: final = max(rule, ml) → REJECT
7. score_above_0.8 → REJECT
8. score_0.6 → REVIEW but proceed
9. score_0.3 → ALLOW
10. fraudScore_savedToMongoDB: verify FraudScore document inserted
```

**Definition of Done**:
- [ ] 10 test cases passing
- [ ] Test 5: `CompletableFuture.completeOnTimeout` triggers in 500ms
- [ ] Test 6: `max(ruleScore, mlScore)` is the final score
- [ ] Test 10: `FraudScore` document saved to MongoDB

---

### TASK-PAY-034: Unit Tests — EscrowService

**Parent WP Task**: WP-003-T10  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/pay/services/EscrowServiceTest.java`

**Test Cases**:
```
1. authorize_realPreAuth_stripe: gateway.authorize() called, isSimulated=false
2. authorize_simulated_momo: gateway.authorize() called, walletService.holdFunds() called, isSimulated=true
3. capture_realGateway: gateway.capture() called with finalAmount
4. capture_simulated: gateway.capture() NOT called, EscrowRecord.status=CAPTURED
5. release_realGateway: gateway.refund() called
6. release_simulated: walletService.releaseFunds() called
7. authorize_expiresAt_7days: expiresAt = authorizedAt + 7 days
8. capture_publishesKafkaEvent: payment.captured published
```

**Definition of Done**:
- [ ] Test 2: `walletService.holdFunds()` called AND `isSimulated=true`
- [ ] Test 7: exact `expiresAt` verified with `Instant.plus(7, DAYS)`
- [ ] All 8 tests passing

---

### TASK-PAY-035: Unit Tests — PaymentOrchestrationService

**Parent WP Task**: WP-003-T10  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/pay/services/PaymentOrchestrationServiceTest.java`

**Test Cases**:
```
1. initiatePayment_happyPath: idempotency check → fraud check → escrow → INSERT tx → cache result
2. idempotent_duplicateCall_returnsCached: same idempotency key → same PaymentResult
3. idempotent_processingKey_returns429: processing → PaymentProcessingException (HTTP 429)
4. fraudDetected_rejects_payment: score > 0.8 → FraudDetectedException (HTTP 402)
5. gatewayFailure_insertsFailedTx: escrow.authorize fails → FAILED transaction inserted
6. gatewayFailure_releasesIdempotencyKey: failed payment → idempotency key released for retry
```

**Definition of Done**:
- [ ] All 6 tests passing
- [ ] Test 2: exact same `PaymentResult` object returned (not newly created)
- [ ] Test 5: `PaymentTransaction { status: FAILED }` inserted on gateway failure
- [ ] Test 6: `IdempotencyService.releaseLock()` called on failure

---

### TASK-PAY-036: Integration Tests — Payment API Flow

**Parent WP Task**: WP-003-T10  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/pay/integration/PaymentControllerIT.java`

**Test Cases**:
```
1. POST /api/v1/payments/initiate (Stripe, with valid idempotency key) → 200 OK
2. POST /api/v1/payments/initiate (duplicate idempotency key) → 200 OK with same response
3. POST /api/v1/payments/initiate (missing X-Idempotency-Key header) → 400
4. POST /api/v1/payments/initiate (fraud score > 0.8, mocked) → 402
5. GET /api/v1/payments/{transactionId} → 200 with transaction details
6. GET /api/v1/wallets/me → 200 with wallet balance
7. POST /api/v1/wallets/top-up → 200, wallet balance updated
```

**Setup**: Testcontainers MongoDB + Redis + Kafka. Mock Stripe SDK (WireMock).  
**Definition of Done**:
- [ ] 7 scenarios passing
- [ ] WireMock mocks Stripe API responses
- [ ] Kafka event captured and verified in tests 1 and 7

---

*DETAIL_PLAN_PAY v1.0.0 — PAY Payment Processing | VNPT AV Platform Services Provider Group*
