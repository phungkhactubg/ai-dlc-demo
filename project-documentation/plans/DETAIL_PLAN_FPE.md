# DETAIL PLAN — FPE: Fare Pricing Engine

**Work Package**: WP-005 | **SRS**: SRS_FPE_Fare_Pricing_Engine.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.fpe`  
**Database**: MongoDB (`fpe_db`) + Redis  
**Events**: Kafka producer (fare-events topic)  
**Critical**: ALL monetary values MUST use `org.bson.types.Decimal128` (NO double/float for money)  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-FPE-001 | RateCard domain model | Domain Models | 1.5h |
| TASK-FPE-002 | Promotion domain model | Domain Models | 1.5h |
| TASK-FPE-003 | FareEstimate + FareLock domain models | Domain Models | 1h |
| TASK-FPE-004 | FareSplit domain model (pooled trips) | Domain Models | 1h |
| TASK-FPE-005 | RateCardRepository interface + impl | Repository | 1.5h |
| TASK-FPE-006 | PromotionRepository interface + impl | Repository | 1.5h |
| TASK-FPE-007 | FareLockRepository interface + impl | Repository | 1h |
| TASK-FPE-008 | TenantContextFilter (copy from TMS pattern) | Security | 1.5h |
| TASK-FPE-009 | GeoHashService (zone hash computation) | Services | 1.5h |
| TASK-FPE-010 | SurgeComputationService (5-tier algorithm) | Services | 2h |
| TASK-FPE-011 | RateCardService (CRUD + active lookup) | Services | 1.5h |
| TASK-FPE-012 | PromotionService (validate + apply) | Services | 2h |
| TASK-FPE-013 | FareCalculationEngine (core formula) | Services | 2h |
| TASK-FPE-014 | FareLockService (lock + finalize) | Services | 2h |
| TASK-FPE-015 | PoolFareSplitService | Services | 1.5h |
| TASK-FPE-016 | RedisCacheService (fare + surge cache) | Services | 1.5h |
| TASK-FPE-017 | FareKafkaProducer (fare-events topic) | Kafka | 1.5h |
| TASK-FPE-018 | FareController (estimate + lock + finalize) | Controllers | 2h |
| TASK-FPE-019 | RateCardController | Controllers | 1.5h |
| TASK-FPE-020 | PromotionController | Controllers | 1.5h |
| TASK-FPE-021 | SurgeStatusController | Controllers | 1h |
| TASK-FPE-022 | GlobalExceptionHandler | Controllers | 1h |
| TASK-FPE-023 | MongoConfig (Decimal128 converters + indexes) | Config | 1.5h |
| TASK-FPE-024 | RedisConfig | Config | 1h |
| TASK-FPE-025 | KafkaProducerConfig | Config | 1h |
| TASK-FPE-026 | Unit tests: FareCalculationEngine | Tests | 2h |
| TASK-FPE-027 | Unit tests: SurgeComputationService | Tests | 1.5h |
| TASK-FPE-028 | Unit tests: PromotionService | Tests | 1.5h |
| TASK-FPE-029 | Unit tests: FareLockService (anti-fraud override) | Tests | 2h |
| TASK-FPE-030 | Integration tests: Fare estimate + lock API | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-FPE-001: RateCard Domain Model

**Parent WP Task**: WP-005-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/models/RateCard.java`
- `src/main/java/com/vnpt/avplatform/fpe/models/VehicleType.java`

**Specification**:
```java
// VehicleType.java
public enum VehicleType { SEDAN, SUV, VAN }

// RateCard.java
@Document(collection = "rate_cards")
public class RateCard {
    @Id private String id;

    @Field("rate_card_id")
    @Indexed(unique = true)
    private String rateCardId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001

    @Field("vehicle_type")
    @NotNull
    private VehicleType vehicleType;

    @Field("effective_from")
    @NotNull
    private Instant effectiveFrom;

    @Field("effective_to")
    private Instant effectiveTo; // null = currently active

    @Field("base_fare_vnd")
    @NotNull
    private Decimal128 baseFareVnd; // NEVER double or BigDecimal in MongoDB — use Decimal128

    @Field("per_km_rate_vnd")
    @NotNull
    private Decimal128 perKmRateVnd;

    @Field("per_minute_rate_vnd")
    @NotNull
    private Decimal128 perMinuteRateVnd;

    @Field("minimum_fare_vnd")
    @NotNull
    private Decimal128 minimumFareVnd;

    @Field("platform_fee_pct")
    private double platformFeePct = 5.0; // default 5% — percentage, not monetary

    @Field("is_active")
    private boolean isActive = true;

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Version
    private Long version;
}
```

**Definition of Done**:
- [ ] All monetary fields use `org.bson.types.Decimal128` (NOT `double`, NOT `BigDecimal`)
- [ ] `@Indexed` on `tenantId` (BL-001)
- [ ] `@Indexed(unique = true)` on `rateCardId`
- [ ] `effectiveTo` is nullable (null = currently active)
- [ ] `platformFeePct` is `double` (it's a percentage, not a money value)
- [ ] `@Version` for optimistic locking

---

### TASK-FPE-002: Promotion Domain Model

**Parent WP Task**: WP-005-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/models/Promotion.java`
- `src/main/java/com/vnpt/avplatform/fpe/models/PromotionType.java`

**Specification**:
```java
// PromotionType.java
public enum PromotionType { PERCENTAGE, FIXED_AMOUNT, FREE_RIDE }

// Promotion.java
@Document(collection = "promotions")
public class Promotion {
    @Id private String id;

    @Field("promo_id")
    @Indexed(unique = true)
    private String promoId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001

    @Field("code")
    @NotBlank
    @Size(min = 3, max = 50)
    @Pattern(regexp = "^[A-Z0-9_-]+$") // uppercase alphanumeric + _ -
    private String code; // unique per tenant (enforced via compound index)

    @Field("type")
    @NotNull
    private PromotionType type;

    @Field("discount_pct")
    private Double discountPct; // used when type=PERCENTAGE (0.01–100.0)

    @Field("discount_vnd")
    private Decimal128 discountVnd; // used when type=FIXED_AMOUNT

    @Field("max_discount_vnd")
    private Decimal128 maxDiscountVnd; // cap for PERCENTAGE type

    @Field("min_fare_vnd")
    private Decimal128 minFareVnd; // minimum fare to qualify

    @Field("valid_from")
    @NotNull
    private Instant validFrom;

    @Field("valid_to")
    @NotNull
    private Instant validTo;

    @Field("usage_limit")
    private Integer usageLimit; // null = unlimited

    @Field("usage_count")
    private int usageCount = 0; // atomically incremented

    @Field("eligible_rider_ids")
    private List<String> eligibleRiderIds; // null = all riders

    @Field("is_active")
    private boolean isActive = true;
}
```

**Compound MongoDB index**: `{ tenant_id: 1, code: 1 }` unique (code unique per tenant)

**Definition of Done**:
- [ ] `discountVnd` and `maxDiscountVnd` and `minFareVnd` use `Decimal128`
- [ ] `code` pattern: uppercase alphanumeric + `_-` (prevents injection)
- [ ] Compound unique index `{ tenant_id, code }` defined in MongoConfig
- [ ] `usageCount` is `int` (incremented via `$inc` operator, not direct set)
- [ ] `discountPct` is `Double` (nullable, only present for PERCENTAGE type)

---

### TASK-FPE-003: FareEstimate and FareLock Domain Models

**Parent WP Task**: WP-005-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/models/FareLock.java`
- `src/main/java/com/vnpt/avplatform/fpe/models/FareBreakdown.java`

**Specification**:
```java
// FareBreakdown.java — embedded (also returned in API responses)
public class FareBreakdown {
    private Decimal128 baseFareVnd;
    private Decimal128 distanceFareVnd;    // distance_km × per_km_rate
    private Decimal128 durationFareVnd;    // duration_min × per_minute_rate
    private Decimal128 rawFareVnd;         // base + distance + duration
    private double tierMultiplier;          // 1.0 (sedan), 1.3 (SUV), 1.5 (Van)
    private Decimal128 tieredFareVnd;      // raw × tier_multiplier
    private double surgeMultiplier;         // 1.0 – 3.0
    private Decimal128 surgedFareVnd;      // tiered × surge
    private Decimal128 promotionDiscountVnd; // applied after surge
    private Decimal128 platformFeeVnd;     // (surged - promotion) × platformFeePct%
    private Decimal128 finalFareVnd;       // surged - promotion + platform_fee
    private Decimal128 minimumFareApplied; // if final < minimum, this overrides
}

// FareLock.java
@Document(collection = "fare_locks")
public class FareLock {
    @Id private String id;

    @Field("fare_id")
    @Indexed(unique = true)
    private String fareId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("trip_id")
    @Indexed
    private String tripId; // set when trip is booked

    @Field("rider_id")
    private String riderId;

    @Field("estimated_distance_km")
    private double estimatedDistanceKm;

    @Field("estimated_duration_min")
    private int estimatedDurationMin;

    @Field("vehicle_type")
    private VehicleType vehicleType;

    @Field("breakdown")
    private FareBreakdown breakdown;

    @Field("locked_fare_vnd")
    private Decimal128 lockedFareVnd; // = breakdown.finalFareVnd at lock time

    @Field("locked")
    private boolean locked = false;

    @Field("locked_at")
    private Instant lockedAt;

    @Field("lock_expires_at")
    private Instant lockExpiresAt; // locked_at + 30 minutes

    @Field("finalized")
    private boolean finalized = false;

    @Field("final_fare_vnd")
    private Decimal128 finalFareVnd; // may differ from lockedFare if anti-fraud override

    @Field("override_applied")
    private boolean overrideApplied = false;

    @Field("override_reason")
    private String overrideReason;

    @Field("promo_code")
    private String promoCode; // applied promotion code

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Definition of Done**:
- [ ] All monetary fields in `FareBreakdown` use `Decimal128`
- [ ] `FareLock.lockExpiresAt` = `lockedAt + 30 minutes`
- [ ] `FareLock.overrideApplied` tracks if anti-fraud override was triggered
- [ ] `tripId` field on `FareLock` with `@Indexed` for lookup by trip

---

### TASK-FPE-004: FareSplit Domain Model

**Parent WP Task**: WP-005-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/models/FareSplit.java`
- `src/main/java/com/vnpt/avplatform/fpe/models/RiderFareShare.java`

**Specification**:
```java
// RiderFareShare.java — embedded
public class RiderFareShare {
    private String riderId;
    private double exclusiveDistanceKm;    // their exclusive leg
    private double sharedDistanceKm;       // their share of shared portion
    private double totalDistanceKm;        // exclusive + shared
    private int durationMin;
    private Decimal128 fareVnd;            // their total fare share
}

// FareSplit.java
@Document(collection = "fare_splits")
public class FareSplit {
    @Id private String id;

    @Field("pool_trip_id")
    @Indexed(unique = true)
    private String poolTripId;

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("vehicle_type")
    private VehicleType vehicleType;

    @Field("riders")
    private List<RiderFareShare> riders; // 2 entries for pooled trips (v1.0)

    @Field("total_vehicle_fare_vnd")
    private Decimal128 totalVehicleFareVnd;

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Definition of Done**:
- [ ] `RiderFareShare.fareVnd` uses `Decimal128`
- [ ] `riders` list has exactly 2 entries for v1.0 pooled trips
- [ ] Sum of all `fareVnd` = `totalVehicleFareVnd` (verified in PoolFareSplitService)

---

## Task Group 2: Repository Layer

### TASK-FPE-005: RateCardRepository

**Parent WP Task**: WP-005-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/repositories/RateCardRepository.java`
- `src/main/java/com/vnpt/avplatform/fpe/repositories/impl/RateCardRepositoryImpl.java`

**Specification**:
```java
public interface RateCardRepository {
    RateCard save(RateCard rateCard);
    Optional<RateCard> findByRateCardId(String rateCardId);
    // Find the ACTIVE rate card for tenant+vehicleType at a given time:
    Optional<RateCard> findActiveRateCard(String tenantId, VehicleType vehicleType, Instant at);
    List<RateCard> findAllByTenantId(String tenantId, int page, int size);
    RateCard deactivate(String rateCardId); // sets effectiveTo = now()
}

// findActiveRateCard implementation:
// Criteria: tenant_id = tenantId AND vehicle_type = vehicleType AND is_active = true
//           AND effective_from <= at AND (effective_to IS NULL OR effective_to >= at)
// Query query = Query.query(
//     Criteria.where("tenant_id").is(tenantId)
//         .and("vehicle_type").is(vehicleType.name())
//         .and("is_active").is(true)
//         .and("effective_from").lte(at)
//         .orOperator(
//             Criteria.where("effective_to").isNull(),
//             Criteria.where("effective_to").gte(at)
//         )
// );
// return Optional.ofNullable(mongoTemplate.findOne(query, RateCard.class));
```

**Definition of Done**:
- [ ] `findActiveRateCard` uses `orOperator` for null `effective_to`
- [ ] All queries include `tenant_id` filter (BL-001)
- [ ] `deactivate` sets `effective_to = Instant.now()` AND `is_active = false`
- [ ] `RateCardRepositoryTest` tests boundary conditions for date range query

---

### TASK-FPE-006: PromotionRepository

**Parent WP Task**: WP-005-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/repositories/PromotionRepository.java`
- `src/main/java/com/vnpt/avplatform/fpe/repositories/impl/PromotionRepositoryImpl.java`

**Specification**:
```java
public interface PromotionRepository {
    Promotion save(Promotion promotion);
    Optional<Promotion> findByPromoId(String promoId);
    Optional<Promotion> findByCodeAndTenantId(String code, String tenantId);
    List<Promotion> findActiveByTenantId(String tenantId, int page, int size);
    boolean incrementUsageCount(String promoId); // returns false if usageLimit reached
    Promotion deactivate(String promoId);
}

// incrementUsageCount — uses atomic $inc with conditional:
// Query: { promo_id: promoId, $expr: { $lt: ["$usage_count", "$usage_limit"] } }
//        OR usage_limit IS NULL (unlimited)
// Update: { $inc: { usage_count: 1 } }
// Use mongoTemplate.updateFirst() and check getMatchedCount() == 1

// If promotion has no usageLimit (unlimited):
//   Simple $inc: { usage_count: 1 } — always succeeds

// findActiveByTenantId:
// Criteria: tenant_id, is_active=true, valid_from <= now, valid_to >= now
```

**Definition of Done**:
- [ ] `incrementUsageCount` is atomic — no read-modify-write race condition
- [ ] Returns `false` when `usageCount >= usageLimit`
- [ ] Unlimited promotions (`usageLimit = null`) always return `true`
- [ ] `findByCodeAndTenantId` includes tenant_id filter (BL-001)

---

### TASK-FPE-007: FareLockRepository

**Parent WP Task**: WP-005-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/repositories/FareLockRepository.java`
- `src/main/java/com/vnpt/avplatform/fpe/repositories/impl/FareLockRepositoryImpl.java`

**Specification**:
```java
public interface FareLockRepository {
    FareLock save(FareLock lock);
    Optional<FareLock> findByFareId(String fareId);
    Optional<FareLock> findByTripId(String tripId);
    FareLock markLocked(String fareId, Instant lockExpiresAt);
    FareLock finalize(String fareId, Decimal128 finalFare, boolean overrideApplied, String overrideReason);
}

// finalize uses:
// Update update = new Update()
//     .set("finalized", true)
//     .set("final_fare_vnd", finalFare)
//     .set("override_applied", overrideApplied)
//     .set("override_reason", overrideReason);
// mongoTemplate.updateFirst(query, update, FareLock.class);
```

**Definition of Done**:
- [ ] `findByTripId` query uses `tenant_id` from TenantContextHolder (BL-001)
- [ ] `finalize` uses `$set` operators (not full document replacement)
- [ ] `Decimal128` used for `finalFare` parameter type

---

## Task Group 3: Security

### TASK-FPE-008: TenantContextFilter

**Parent WP Task**: WP-005-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/fpe/security/TenantContextHolder.java`

**Specification**: Same pattern as TASK-TMS-008 and TASK-TMS-009.
```java
// TenantContextFilter: extends OncePerRequestFilter
// Extract tenant_id from JWT claim "tenant_id" OR "X-Tenant-ID" header
// Store in TenantContextHolder.setTenantId()
// ALWAYS call TenantContextHolder.clear() in finally block

// TenantContextHolder: identical to TMS version
// ThreadLocal<String> CONTEXT
// requireTenantId() throws TenantContextMissingException if null
// clear() calls CONTEXT.remove()
```

**Definition of Done**:
- [ ] `clear()` in `finally` block — verified by test with exception thrown during filter
- [ ] `Filter` priority set to `@Order(1)`

---

## Task Group 4: Core Services

### TASK-FPE-009: GeoHashService (Zone Hash Computation)

**Parent WP Task**: WP-005-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/GeoHashService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/GeoHashServiceImpl.java`

**Specification**:
```java
public interface GeoHashService {
    String computeZoneHash(double latitude, double longitude);
}

// GeoHashServiceImpl:
// Library: ch.hsr:geohash:1.4.0
// Precision: 6 characters (~1.2km accuracy — sufficient for zone-level caching)
// Returns: String of 6 geohash characters (e.g., "w3gv2s")

// computeZoneHash():
//   GeoHash hash = GeoHash.withCharacterPrecision(latitude, longitude, 6);
//   return hash.toBase32();
```

**Definition of Done**:
- [ ] Uses `ch.hsr:geohash` library (not home-grown)
- [ ] Precision: 6 characters (~1.2km)
- [ ] `GeoHashServiceTest`: known coordinates produce expected geohash string
- [ ] Returns consistent results for same coordinates (deterministic)

---

### TASK-FPE-010: SurgeComputationService (5-Tier Algorithm)

**Parent WP Task**: WP-005-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/SurgeComputationService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/SurgeComputationServiceImpl.java`

**Specification**:
```java
public interface SurgeComputationService {
    double computeSurgeMultiplier(String tenantId, String zoneHash, VehicleType vehicleType);
    SurgeStatus getSurgeStatus(String tenantId, String zoneHash);
}

// SurgeComputationServiceImpl:
// Redis key: "surge:{tenantId}:{zoneHash}:{vehicleType}" TTL 30s (refreshed frequently)

// computeSurgeMultiplier():
//   1. Try Redis cache: GET "surge:{tenantId}:{zoneHash}:{vehicleType}" → parse as double
//   2. On miss: compute fresh:
//      active_requests = countActiveBookingRequests(tenantId, zoneHash)
//      available_vehicles = countAvailableVehicles(tenantId, zoneHash) // via VMS Redis Sorted Set
//      ratio = available_vehicles == 0 ? 5.0 : (double) active_requests / available_vehicles
//      raw_multiplier = computeFromRatio(ratio)
//      tenant_surge_cap = tenantConfigService.getSurgeCap(tenantId) // cached
//      multiplier = Math.min(raw_multiplier, tenant_surge_cap)
//      Redis: SET "surge:{tenantId}:{zoneHash}:{vehicleType}" {multiplier} EX 30
//   3. Return multiplier

// computeFromRatio — 5-tier table:
// private static double computeFromRatio(double ratio) {
//     if (ratio < 1.2) return 1.0;
//     if (ratio < 1.5) return 1.2;
//     if (ratio < 2.0) return 1.5;
//     if (ratio < 2.5) return 2.0;
//     if (ratio < 3.0) return 2.5;
//     return 3.0;
// }

// countActiveBookingRequests: from Redis Sorted Set "booking_requests:{tenantId}:{zoneHash}"
// countAvailableVehicles: from Redis Sorted Set "vehicles:{tenantId}:{zoneHash}" (maintained by VMS)
```

**Definition of Done**:
- [ ] Surge multiplier capped at `min(3.0, tenant.surge_cap)` — tenant cap always respected
- [ ] 5-tier boundaries: 1.2 / 1.5 / 2.0 / 2.5 / 3.0
- [ ] Redis cache TTL: 30 seconds for surge values
- [ ] `SurgeComputationServiceTest`: 6 test cases (one per tier + cap enforcement)
- [ ] Division by zero handled (0 available vehicles → max surge = 3.0 or cap)

---

### TASK-FPE-011: RateCardService (CRUD + Active Lookup)

**Parent WP Task**: WP-005-T05  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/RateCardService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/RateCardServiceImpl.java`

**Specification**:
```java
public interface RateCardService {
    RateCardDTO createRateCard(String tenantId, CreateRateCardRequest request);
    RateCardDTO getActiveRateCard(String tenantId, VehicleType vehicleType);
    List<RateCardDTO> listRateCards(String tenantId, int page, int size);
    RateCardDTO deactivateRateCard(String rateCardId);
}

// createRateCard():
//   1. Deactivate any existing active rate card for same tenantId + vehicleType
//   2. Create new RateCard with effectiveFrom = Instant.now()
//   3. Save and return DTO

// getActiveRateCard():
//   1. findActiveRateCard(tenantId, vehicleType, Instant.now())
//   2. If not found: throw RateCardNotFoundException (HTTP 404 "RATE_CARD_NOT_FOUND")

// Monetary field conversion: use BigDecimal → Decimal128:
//   request.getBaseFareVnd() (BigDecimal) → new Decimal128(request.getBaseFareVnd())
```

**Definition of Done**:
- [ ] `createRateCard` deactivates old active card before creating new one (atomically via update)
- [ ] Monetary fields stored as `Decimal128` (not as request's `BigDecimal` directly)
- [ ] `RateCardNotFoundException` returns HTTP 404

---

### TASK-FPE-012: PromotionService (Validate + Apply)

**Parent WP Task**: WP-005-T06  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/PromotionService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/PromotionServiceImpl.java`

**Specification**:
```java
public interface PromotionService {
    PromotionValidationResult validatePromo(String tenantId, String promoCode, String riderId, Decimal128 fareVnd);
    Decimal128 applyDiscount(PromotionType type, Decimal128 discountPct_or_vnd, Decimal128 maxDiscountVnd, Decimal128 fareVnd);
    PromotionDTO createPromotion(String tenantId, CreatePromotionRequest request);
    void deactivatePromotion(String promoId);
}

// validatePromo():
//   1. findByCodeAndTenantId(code, tenantId)
//   2. If not found: return { valid: false, reason: "PROMO_NOT_FOUND" }
//   3. Check is_active: false → { valid: false, reason: "PROMO_INACTIVE" }
//   4. Check valid_from <= now <= valid_to → else: { valid: false, reason: "PROMO_EXPIRED" }
//   5. If eligibleRiderIds != null: check riderId in list → else: { valid: false, reason: "RIDER_NOT_ELIGIBLE" }
//   6. Check usageLimit: usageCount >= usageLimit → { valid: false, reason: "PROMO_LIMIT_REACHED" }
//   7. Check minFareVnd: fareVnd < minFareVnd → { valid: false, reason: "FARE_BELOW_MINIMUM" }
//   8. All checks passed: return { valid: true, discountVnd: applyDiscount(...) }
//   NOTE: validatePromo does NOT increment usageCount (done only on confirmed booking)

// applyDiscount() — pure function, no side effects:
//   PERCENTAGE: discount = fare × discountPct / 100; if maxDiscount: min(discount, maxDiscountVnd); return discount
//   FIXED_AMOUNT: return min(discountVnd, fare) // never discount more than fare
//   FREE_RIDE: return fare // 100% discount
//   All arithmetic: BigDecimal operations, then convert to Decimal128

// Arithmetic pattern for PERCENTAGE:
//   BigDecimal fareBD = fareVnd.bigDecimalValue();
//   BigDecimal discountBD = fareBD.multiply(BigDecimal.valueOf(discountPct / 100.0));
//   if (maxDiscountVnd != null) discountBD = discountBD.min(maxDiscountVnd.bigDecimalValue());
//   return new Decimal128(discountBD.setScale(0, RoundingMode.HALF_UP));
```

**Definition of Done**:
- [ ] Validation order strictly: active → dates → eligibility → limit → min fare
- [ ] `validatePromo` does NOT increment usageCount (read-only validation)
- [ ] `applyDiscount` returns `Decimal128` (no double intermediate)
- [ ] `PromotionServiceTest` covers all 7 validation failure cases + success

---

### TASK-FPE-013: FareCalculationEngine (Core Formula)

**Parent WP Task**: WP-005-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/FareCalculationEngine.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/FareCalculationEngineImpl.java`

**Specification**:
```java
public interface FareCalculationEngine {
    FareBreakdown compute(FareComputationInput input);
}

// FareComputationInput:
public class FareComputationInput {
    private RateCard rateCard;
    private double distanceKm;
    private int durationMin;
    private double surgeMultiplier;      // already capped at tenant.surge_cap
    private Decimal128 promotionDiscount; // already computed by PromotionService
    private VehicleType vehicleType;
}

// FareCalculationEngineImpl.compute() — ALL arithmetic via BigDecimal:
// 1. baseFare = rateCard.getBaseFareVnd().bigDecimalValue()
// 2. distanceFare = rateCard.getPerKmRateVnd().bigDecimalValue() × BigDecimal.valueOf(distanceKm)
// 3. durationFare = rateCard.getPerMinuteRateVnd().bigDecimalValue() × BigDecimal.valueOf(durationMin)
// 4. rawFare = baseFare + distanceFare + durationFare
// 5. tierMultiplier = getTierMultiplier(vehicleType) // 1.0/1.3/1.5
// 6. tieredFare = rawFare × BigDecimal.valueOf(tierMultiplier)
// 7. surgedFare = tieredFare × BigDecimal.valueOf(surgeMultiplier)
// 8. netFare = surgedFare − promotionDiscount.bigDecimalValue()
//    if netFare < 0: netFare = BigDecimal.ZERO
// 9. platformFee = netFare × BigDecimal.valueOf(rateCard.getPlatformFeePct() / 100.0)
// 10. finalFare = netFare + platformFee
// 11. Apply minimum fare: if finalFare < rateCard.getMinimumFareVnd() → finalFare = minimum
// 12. All values rounded to HALF_UP, scale 0 (VND is whole number)
// 13. Return FareBreakdown with all Decimal128 fields populated

// getTierMultiplier():
//   SEDAN → 1.0
//   SUV → 1.3
//   VAN → 1.5

// BigDecimal arithmetic scale: use scale 2 for intermediates, round to 0 for VND (final)
```

**Definition of Done**:
- [ ] ALL arithmetic uses `BigDecimal` (ZERO `double` operations on monetary values)
- [ ] Tier multipliers: SEDAN=1.0, SUV=1.3, VAN=1.5 — hardcoded as constants
- [ ] Promotion applied AFTER surge (not before)
- [ ] Platform fee applied to `(surgedFare - promotionDiscount)` (net fare)
- [ ] Minimum fare override: final fare never below `minimumFareVnd`
- [ ] `FareCalculationEngineTest` with 10 test cases covering: surge cap, promotion, min fare, free ride promo, all vehicle types

---

### TASK-FPE-014: FareLockService (Lock + Finalize + Anti-Fraud Override)

**Parent WP Task**: WP-005-T08  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/FareLockService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/FareLockServiceImpl.java`

**Specification**:
```java
public interface FareLockService {
    FareLockDTO estimateFare(EstimateFareRequest request);
    FareLockDTO lockFare(LockFareRequest request);
    FareLockDTO finalizeFare(FinalizeFareRequest request);
}

// estimateFare():
//   1. Get active rate card for tenantId + vehicleType
//   2. Get surge multiplier: surgeComputationService.computeSurgeMultiplier(tenantId, pickupZoneHash, vehicleType)
//   3. Validate promo if promoCode provided: promotionService.validatePromo(...)
//   4. Compute fare: fareCalculationEngine.compute(input)
//   5. Create FareLock (locked=false) — temporary estimate record
//   6. Return FareLockDTO { fareId, breakdown, estimatedFare, locked: false, surgeMultiplier }

// lockFare():
//   1. Load FareLock by fareId
//   2. If already locked: throw FareAlreadyLockedException (HTTP 409 "FARE_ALREADY_LOCKED")
//   3. If estimate expired (createdAt + 5min): throw FareExpiredException (HTTP 410 "FARE_ESTIMATE_EXPIRED")
//   4. Re-compute fare (real-time) — prices may have changed
//   5. Set locked=true, lockedFareVnd=finalFare, lockExpiresAt=now()+30min
//   6. If promoCode: increment usageCount via promotionService atomically
//   7. Store in Redis: "fare_lock:{fareId}" TTL 1800s (backup cache)
//   8. Return updated FareLockDTO

// finalizeFare():
//   1. Load FareLock by tripId (or fareId)
//   2. Compute actual fare from actual distance/duration
//   3. Anti-fraud check (BL-anti-fraud):
//      if actualDistanceKm > 1.5 × lockedFare.estimatedDistanceKm:
//          actualFare = recompute with actual distance
//          overrideApplied = true
//          overrideReason = "DISTANCE_EXCEEDED_150_PCT"
//      else:
//          finalFare = lockedFare.lockedFareVnd (upfront pricing honored)
//   4. Update FareLock: finalized=true, finalFareVnd, overrideApplied
//   5. Publish Kafka event: fare.finalized
//   6. Return FareLockDTO with finalFareVnd and overrideApplied

// Anti-fraud override condition: actual_distance > 1.5 × estimated_distance (150%)
```

**Definition of Done**:
- [ ] Anti-fraud override: actual > 150% of estimated → recompute with actual distance
- [ ] Lock expiry: 30 minutes from lock time (`lockExpiresAt`)
- [ ] `lockFare` increments promo usageCount atomically (via `PromotionRepository.incrementUsageCount`)
- [ ] `finalizeFare` publishes `fare.finalized` Kafka event with `platform_revenue_vnd`
- [ ] `FareLockServiceTest` with test: actualDistance=200% of estimate → override applied

---

### TASK-FPE-015: PoolFareSplitService

**Parent WP Task**: WP-005-T09  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/PoolFareSplitService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/PoolFareSplitServiceImpl.java`

**Specification**:
```java
public interface PoolFareSplitService {
    FareSplit computeSplit(ComputeSplitRequest request);
}

// ComputeSplitRequest:
//   poolTripId: string
//   tenantId: string
//   vehicleType: VehicleType
//   riders: [
//     { riderId, exclusiveDistanceKm, sharedDistanceKm, durationMin },
//     { riderId, exclusiveDistanceKm, sharedDistanceKm, durationMin }
//   ]
//   surgeMultiplier: double

// computeSplit():
//   For each rider:
//     totalDistance = exclusiveDistance + (sharedDistance × riderDistance / totalSharedDistance)
//     Actually: each rider's shared portion = their sharedDistanceKm (already per-rider)
//     totalDistanceForRider = exclusiveDistanceKm + sharedDistanceKm
//     fareVnd = fareCalculationEngine.compute({
//         rateCard: getActiveRateCard(tenantId, vehicleType),
//         distanceKm: totalDistanceForRider,
//         durationMin: rider.durationMin,
//         surgeMultiplier: surgeMultiplier,
//         promotionDiscount: Decimal128.ZERO
//     }).getFinalFareVnd()
//
//   totalVehicleFare = SUM of all rider fares
//
//   Verify: SUM(rider fares) == totalVehicleFare (within 1 VND rounding tolerance)
//   Save FareSplit to MongoDB
//   Return FareSplit
```

**Definition of Done**:
- [ ] Sum of rider fares stored as `totalVehicleFareVnd`
- [ ] All `fareVnd` per rider computed via `FareCalculationEngine` (consistent formula)
- [ ] `PoolFareSplitServiceTest`: 2 riders → fares sum to vehicle total
- [ ] Rounding: each rider's fare rounded to 0 decimal (HALF_UP), then total summed

---

### TASK-FPE-016: RedisCacheService (Fare + Surge Cache Management)

**Parent WP Task**: WP-005-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/services/FareCacheService.java`
- `src/main/java/com/vnpt/avplatform/fpe/services/impl/FareCacheServiceImpl.java`

**Specification**:
```java
public interface FareCacheService {
    Optional<FareBreakdown> getCachedFare(String tenantId, String pickupZoneHash, String dropoffZoneHash, VehicleType vehicleType, int surgeBucket);
    void cacheFare(String tenantId, String pickupZoneHash, String dropoffZoneHash, VehicleType vehicleType, int surgeBucket, FareBreakdown breakdown);
    void invalidateFareCache(String tenantId); // on rate card update
}

// Cache key: "fare:{tenantId}:{pickupZoneHash}:{dropoffZoneHash}:{vehicleType}:{surgeBucket}"
// TTL: 60 seconds

// surgeBucket = (int)(surgeMultiplier × 10) to avoid float as key
//   1.0 → bucket=10, 1.2 → 12, 1.5 → 15, 2.0 → 20, 2.5 → 25, 3.0 → 30

// cacheFare: serialize FareBreakdown to JSON → SET key value EX 60
// getCachedFare: GET key → deserialize JSON → return Optional

// invalidateFareCache: 
//   Pattern: "fare:{tenantId}:*"
//   Use RedisTemplate.keys("fare:" + tenantId + ":*") → redisTemplate.delete(keys)
//   NOTE: keys() is O(n) — acceptable for rate card updates (infrequent)
```

**Definition of Done**:
- [ ] Cache key format: `fare:{tenantId}:{pickupZoneHash}:{dropoffZoneHash}:{vehicleType}:{surgeBucket}`
- [ ] Surge bucket: integer representation (× 10 to avoid float key)
- [ ] TTL: 60 seconds on cache write
- [ ] `invalidateFareCache` uses pattern delete (acceptable for infrequent rate card updates)
- [ ] `FareCacheServiceTest` verifies correct key construction

---

## Task Group 5: Kafka Integration

### TASK-FPE-017: FareKafkaProducer

**Parent WP Task**: WP-005-T11  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/events/FareKafkaProducer.java`
- `src/main/java/com/vnpt/avplatform/fpe/events/FareEvent.java`

**Specification**:
```java
// FareEvent.java
public class FareEvent {
    private String eventId = UUID.randomUUID().toString();
    private String eventType; // "fare.estimated"|"fare.finalized"|"fare.override_applied"
    private String tenantId;
    private String fareId;
    private String tripId;
    private Instant timestamp = Instant.now();
    private BigDecimal finalFareVnd;       // serialized as number (not Decimal128 in Kafka)
    private BigDecimal platformRevenueVnd; // = finalFare × platformFeePct%
    private boolean overrideApplied;
    private String overrideReason;
}

// FareKafkaProducer.java
@Component
public class FareKafkaProducer {
    private static final String TOPIC = "fare-events"; // 12 partitions

    // publish fare.finalized with platform_revenue_vnd:
    // platformRevenue = finalFare × platformFeePct / 100 (BigDecimal arithmetic)
    // Partition key = tenantId
    public void publishFareFinalized(String tenantId, FareLock lock, double platformFeePct) {
        BigDecimal finalFare = lock.getFinalFareVnd().bigDecimalValue();
        BigDecimal platformRevenue = finalFare.multiply(BigDecimal.valueOf(platformFeePct / 100.0))
            .setScale(0, RoundingMode.HALF_UP);

        FareEvent event = new FareEvent();
        event.setEventType("fare.finalized");
        event.setTenantId(tenantId);
        event.setFareId(lock.getFareId());
        event.setTripId(lock.getTripId());
        event.setFinalFareVnd(finalFare);
        event.setPlatformRevenueVnd(platformRevenue);
        // ...
        kafkaTemplate.send(TOPIC, tenantId, event);
    }
}
```

**Definition of Done**:
- [ ] Topic: `fare-events` (12 partitions)
- [ ] Partition key: `tenantId`
- [ ] `platformRevenueVnd` computed as `finalFare × platformFeePct%` (BigDecimal)
- [ ] Event serialized with BigDecimal (not Decimal128) for Kafka JSON

---

## Task Group 6: REST Controllers

### TASK-FPE-018: FareController

**Parent WP Task**: WP-005-T12  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/controllers/FareController.java`
- `src/main/java/com/vnpt/avplatform/fpe/controllers/dto/EstimateFareRequest.java`
- `src/main/java/com/vnpt/avplatform/fpe/controllers/dto/FareLockDTO.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/fares")
public class FareController {

    // POST /api/v1/fares/estimate
    @PostMapping("/estimate")
    public FareLockDTO estimateFare(@Valid @RequestBody EstimateFareRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        return fareLockService.estimateFare(request.withTenantId(tenantId));
    }

    // POST /api/v1/fares/lock
    @PostMapping("/lock")
    public FareLockDTO lockFare(@Valid @RequestBody LockFareRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        return fareLockService.lockFare(request.withTenantId(tenantId));
    }

    // POST /api/v1/fares/finalize  (internal — called by RHS on trip completion)
    @PostMapping("/finalize")
    @PreAuthorize("hasRole('INTERNAL_SERVICE')")
    public FareLockDTO finalizeFare(@Valid @RequestBody FinalizeFareRequest request) {
        return fareLockService.finalizeFare(request);
    }

    // POST /api/v1/fares/validate-promo
    @PostMapping("/validate-promo")
    public PromotionValidationResult validatePromo(@Valid @RequestBody ValidatePromoRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        return promotionService.validatePromo(tenantId, request.getPromoCode(),
            request.getRiderId(), request.getFareVndAsDecimal128());
    }
}

// EstimateFareRequest validation:
//   pickupLat: @DecimalMin("-90.0") @DecimalMax("90.0")
//   pickupLng: @DecimalMin("-180.0") @DecimalMax("180.0")
//   dropoffLat, dropoffLng: same
//   vehicleType: @NotNull (SEDAN|SUV|VAN)
//   estimatedDistanceKm: @Positive
//   estimatedDurationMin: @Positive
//   promoCode: optional, max 50 chars
```

**Definition of Done**:
- [ ] `estimate` endpoint: public (any authenticated user can estimate)
- [ ] `finalize` endpoint: `INTERNAL_SERVICE` role only
- [ ] `TenantContextHolder.requireTenantId()` used for tenant isolation
- [ ] `EstimateFareRequest` has lat/lng validation
- [ ] HTTP 409 on already-locked fare, HTTP 410 on expired estimate

---

### TASK-FPE-019: RateCardController

**Parent WP Task**: WP-005-T12  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/controllers/RateCardController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/rate-cards")
@PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN')")
public class RateCardController {

    // GET /api/v1/rate-cards
    @GetMapping
    public List<RateCardDTO> listRateCards(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        return rateCardService.listRateCards(tenantId, page, size);
    }

    // POST /api/v1/rate-cards
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public RateCardDTO createRateCard(@Valid @RequestBody CreateRateCardRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        return rateCardService.createRateCard(tenantId, request);
    }

    // PUT /api/v1/rate-cards/{rateCardId} — deactivates old, creates new version
    @PutMapping("/{rateCardId}")
    public RateCardDTO updateRateCard(
        @PathVariable String rateCardId,
        @Valid @RequestBody CreateRateCardRequest request
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        rateCardService.deactivateRateCard(rateCardId);
        return rateCardService.createRateCard(tenantId, request);
    }
}

// CreateRateCardRequest validation:
//   vehicleType: @NotNull
//   baseFareVnd: @NotNull @DecimalMin("0.01") (BigDecimal in request, stored as Decimal128)
//   perKmRateVnd: @NotNull @DecimalMin("0.01")
//   perMinuteRateVnd: @NotNull @DecimalMin("0.01")
//   minimumFareVnd: @NotNull @DecimalMin("0.01")
//   platformFeePct: @DecimalMin("0.0") @DecimalMax("100.0"), default 5.0
```

**Definition of Done**:
- [ ] `TENANT_ADMIN` can create/update their own rate cards
- [ ] `PLATFORM_ADMIN` can create for any tenant
- [ ] PUT creates new rate card + deactivates old (version history preserved)
- [ ] `baseFareVnd` validated as `BigDecimal` in request, stored as `Decimal128`

---

### TASK-FPE-020: PromotionController

**Parent WP Task**: WP-005-T12  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/controllers/PromotionController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/promotions")
@PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN')")
public class PromotionController {

    @GetMapping
    public List<PromotionDTO> listPromotions(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) { ... }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public PromotionDTO createPromotion(@Valid @RequestBody CreatePromotionRequest request) { ... }

    @DeleteMapping("/{promoId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deactivatePromotion(@PathVariable String promoId) { ... }
}
// CreatePromotionRequest validation:
//   code: @NotBlank @Pattern(regexp="^[A-Z0-9_-]+$") @Size(min=3, max=50)
//   type: @NotNull
//   validFrom: @NotNull @FutureOrPresent (or admin override)
//   validTo: @NotNull @Future
//   discountPct: required if type=PERCENTAGE; @DecimalMin("0.01") @DecimalMax("100.0")
//   discountVnd: required if type=FIXED_AMOUNT; @DecimalMin("1")
```

**Definition of Done**:
- [ ] DELETE sets `is_active = false` (soft delete, not hard delete)
- [ ] `code` pattern enforced: uppercase alphanumeric + `_-`
- [ ] `discountPct` required only when type=PERCENTAGE (validated in service)
- [ ] HTTP 204 on successful deactivation

---

### TASK-FPE-021: SurgeStatusController

**Parent WP Task**: WP-005-T12  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/controllers/SurgeStatusController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/surge-status")
public class SurgeStatusController {

    // GET /api/v1/surge-status?pickup_lat=10.77&pickup_lng=106.69&vehicle_type=SEDAN
    @GetMapping
    public SurgeStatusResponse getSurgeStatus(
        @RequestParam @DecimalMin("-90.0") @DecimalMax("90.0") double pickupLat,
        @RequestParam @DecimalMin("-180.0") @DecimalMax("180.0") double pickupLng,
        @RequestParam VehicleType vehicleType
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        String zoneHash = geoHashService.computeZoneHash(pickupLat, pickupLng);
        SurgeStatus status = surgeComputationService.getSurgeStatus(tenantId, zoneHash);
        return new SurgeStatusResponse(zoneHash, status.getMultiplier(), status.getRatio());
    }
}

// SurgeStatusResponse: { zone_id, surge_multiplier, demand_supply_ratio }
```

**Definition of Done**:
- [ ] Returns zone ID (geohash) for client-side caching
- [ ] Surge multiplier already capped at tenant cap (per SurgeComputationService)
- [ ] HTTP 200 with `{ zone_id, surge_multiplier, demand_supply_ratio }`

---

## Task Group 7: Configuration

### TASK-FPE-023: MongoConfig (Decimal128 Converters + Indexes)

**Parent WP Task**: WP-005-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/fpe/config/MongoConfig.java`

**Specification**:
```java
@Configuration
public class MongoConfig implements ApplicationListener<ContextRefreshedEvent> {

    @Bean
    public MongoCustomConversions mongoCustomConversions() {
        // Register Decimal128 ↔ BigDecimal converters for Spring Data MongoDB
        return new MongoCustomConversions(List.of(
            new Decimal128ToBigDecimalConverter(),
            new BigDecimalToDecimal128Converter()
        ));
    }

    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        // rate_cards indexes
        mongoTemplate.indexOps("rate_cards").ensureIndex(
            new Index().on("rate_card_id", ASC).unique()
        );
        mongoTemplate.indexOps("rate_cards").ensureIndex(
            new Index().on("tenant_id", ASC)
        );
        mongoTemplate.indexOps("rate_cards").ensureIndex(
            new CompoundIndexDefinition(new Document("tenant_id", 1).append("vehicle_type", 1).append("is_active", 1))
        );

        // promotions indexes
        mongoTemplate.indexOps("promotions").ensureIndex(
            new Index().on("promo_id", ASC).unique()
        );
        mongoTemplate.indexOps("promotions").ensureIndex(
            new CompoundIndexDefinition(new Document("tenant_id", 1).append("code", 1)).unique()
        );

        // fare_locks indexes
        mongoTemplate.indexOps("fare_locks").ensureIndex(
            new Index().on("fare_id", ASC).unique()
        );
        mongoTemplate.indexOps("fare_locks").ensureIndex(
            new Index().on("trip_id", ASC)
        );
    }
}
```

**Definition of Done**:
- [ ] Decimal128 ↔ BigDecimal converters registered for Spring Data
- [ ] Compound index `{ tenant_id, vehicle_type, is_active }` on rate_cards
- [ ] Compound unique index `{ tenant_id, code }` on promotions
- [ ] All indexes created at application startup

---

## Task Group 8: Tests

### TASK-FPE-026: Unit Tests — FareCalculationEngine

**Parent WP Task**: WP-005-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/fpe/services/FareCalculationEngineTest.java`

**Test Cases**:
```
1. compute_sedan_noSurge_noPromo: basic sedan fare (base + distance + duration)
2. compute_suv_tierMultiplier: SUV fare = sedan × 1.3
3. compute_van_tierMultiplier: Van fare = sedan × 1.5
4. compute_withSurge_2x: surgedFare = tieredFare × 2.0
5. compute_withPromoPercentage: 10% off, max 50k cap
6. compute_withFixedPromo: 30k fixed discount
7. compute_freeRidePromo: fare = minimumFare (promo discounts all, min still applies)
8. compute_minimumFareEnforced: computed fare < minimum → returns minimum
9. compute_surgeCapEnforced: surge=3.5 but tenant_cap=2.5 → multiplied by 2.5 (in input)
10. compute_allDecimal128_noDoubleArithmetic: verify no rounding error in BigDecimal chain
```

**Definition of Done**:
- [ ] 10 test cases all passing
- [ ] All monetary assertion comparisons use `BigDecimal` (not `==` on `Decimal128`)
- [ ] Test case 10: known inputs produce bitwise exact expected output (no floating point error)

---

### TASK-FPE-027: Unit Tests — SurgeComputationService

**Parent WP Task**: WP-005-T13  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/fpe/services/SurgeComputationServiceTest.java`

**Test Cases**:
```
1. ratio_below_1.2 → multiplier 1.0
2. ratio_1.3 → multiplier 1.2
3. ratio_1.7 → multiplier 1.5
4. ratio_2.2 → multiplier 2.0
5. ratio_2.7 → multiplier 2.5
6. ratio_3.5 → multiplier 3.0 (max)
7. tenantSurgeCap_2.5: ratio_3.5 → multiplier 2.5 (capped)
8. zeroAvailableVehicles → multiplier 3.0 (or cap)
9. cacheHit: returns cached value without recomputing
10. cacheMiss: computes and stores in cache
```

**Definition of Done**:
- [ ] 10 test cases all passing
- [ ] Redis mock verifies `SET NX EX 30` on cache miss
- [ ] Test 7: tenant surge cap respected

---

### TASK-FPE-028: Unit Tests — PromotionService

**Parent WP Task**: WP-005-T13  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/fpe/services/PromotionServiceTest.java`

**Test Cases**:
```
1. validatePromo_notFound → { valid: false, reason: "PROMO_NOT_FOUND" }
2. validatePromo_inactive → { valid: false, reason: "PROMO_INACTIVE" }
3. validatePromo_expired → { valid: false, reason: "PROMO_EXPIRED" }
4. validatePromo_riderNotEligible → { valid: false, reason: "RIDER_NOT_ELIGIBLE" }
5. validatePromo_limitReached → { valid: false, reason: "PROMO_LIMIT_REACHED" }
6. validatePromo_fareBelowMinimum → { valid: false, reason: "FARE_BELOW_MINIMUM" }
7. validatePromo_success_percentage → correct discount computed
8. validatePromo_success_fixed → discount = min(discountVnd, fare)
9. validatePromo_success_freeRide → discount = full fare
10. validatePromo_noUsageCount_increment_on_validate: verify repo.incrementUsageCount NOT called in validate
```

**Definition of Done**:
- [ ] 10 test cases all passing
- [ ] Test 10: `PromotionRepository.incrementUsageCount` is NEVER called during `validatePromo`
- [ ] All 7 validation failure cases produce distinct `reason` codes

---

### TASK-FPE-029: Unit Tests — FareLockService (Anti-Fraud Override)

**Parent WP Task**: WP-005-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/fpe/services/FareLockServiceTest.java`

**Test Cases**:
```
1. lockFare_success: fareEstimate locked, lockedFare stored
2. lockFare_alreadyLocked: FareAlreadyLockedException thrown
3. lockFare_expired: FareExpiredException thrown (estimate > 5min old)
4. finalizeFare_happyPath: actualDistance ≤ estimated → lockedFare honored
5. finalizeFare_antiFraudOverride: actualDistance = 200% of estimated → override applied, fare recomputed
6. finalizeFare_override_exactThreshold: actualDistance = 150% → NO override (threshold is > 150%)
7. finalizeFare_publishesKafkaEvent: fare.finalized event published with platformRevenueVnd
8. finalizeFare_promoUsageIncrement: usageCount incremented on lock (not on finalize)
```

**Definition of Done**:
- [ ] Test 5: `overrideApplied=true`, `overrideReason="DISTANCE_EXCEEDED_150_PCT"`
- [ ] Test 6: exactly 150% distance → override NOT applied (must be strictly > 150%)
- [ ] Test 7: Kafka event verified with correct `platformRevenueVnd`
- [ ] `FareLockRepository.finalize()` called with correct `Decimal128` final fare

---

### TASK-FPE-030: Integration Tests — Fare Estimate + Lock API

**Parent WP Task**: WP-005-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/fpe/integration/FareControllerIT.java`

**Test Cases**:
```
1. POST /api/v1/fares/estimate → 200 OK with breakdown
2. POST /api/v1/fares/estimate (no active rate card) → 404
3. POST /api/v1/fares/lock → 200 OK, fare locked
4. POST /api/v1/fares/lock (already locked) → 409
5. POST /api/v1/fares/validate-promo (valid promo) → { valid: true, discountVnd }
6. POST /api/v1/fares/validate-promo (invalid promo) → { valid: false, reason }
7. GET /api/v1/surge-status → 200 OK with surge multiplier
```

**Setup**: Testcontainers MongoDB + Redis + Kafka (KafkaContainer)
**Definition of Done**:
- [ ] 7 test scenarios passing
- [ ] Rate card seeded in MongoDB for test tenant
- [ ] Kafka event verified in test 3 (fare.estimated event captured)
- [ ] Redis Testcontainer used for surge cache tests

---

*DETAIL_PLAN_FPE v1.0.0 — FPE Fare Pricing Engine | VNPT AV Platform Services Provider Group*
