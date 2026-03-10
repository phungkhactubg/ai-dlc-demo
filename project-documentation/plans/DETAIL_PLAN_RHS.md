# DETAIL PLAN — RHS: Ride Hailing Service

**Work Package**: WP-004 | **SRS**: SRS_RHS_Ride_Hailing_Service.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.rhs`  
**Database**: MongoDB (`rhs_db`) + Redis + NATS (real-time push)  
**Events**: Kafka producer (ride-events topic, 12 partitions)  
**NATS**: Publish real-time trip updates (ETA, status changes)  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-RHS-001 | Trip domain model (11-state) | Domain Models | 1.5h |
| TASK-RHS-002 | Vehicle model (for matching) | Domain Models | 1h |
| TASK-RHS-003 | CancellationFeeRecord domain model | Domain Models | 1h |
| TASK-RHS-004 | TripRating domain model | Domain Models | 1h |
| TASK-RHS-005 | TripRepository (state machine queries) | Repository | 2h |
| TASK-RHS-006 | VehicleRepository | Repository | 1h |
| TASK-RHS-007 | TenantContextFilter + TenantContextHolder | Security | 1.5h |
| TASK-RHS-008 | AVMatchingService (scoring algorithm) | Services | 2h |
| TASK-RHS-009 | ETAService (ML + fallback) | Services | 2h |
| TASK-RHS-010 | TripStateMachineService (11-state transitions) | Services | 2h |
| TASK-RHS-011 | BookingService (create + duplicate prevention) | Services | 2h |
| TASK-RHS-012 | PooledTripService (max 2 passengers) | Services | 2h |
| TASK-RHS-013 | CancellationFeeService | Services | 1.5h |
| TASK-RHS-014 | SafetyStopService | Services | 1h |
| TASK-RHS-015 | RatingService (48h window, dimensions) | Services | 1.5h |
| TASK-RHS-016 | NATSPublisher (ETA + status real-time) | NATS | 1.5h |
| TASK-RHS-017 | RideKafkaProducer (ride-events) | Kafka | 1.5h |
| TASK-RHS-018 | TripController | Controllers | 2h |
| TASK-RHS-019 | BookingController | Controllers | 1.5h |
| TASK-RHS-020 | RatingController | Controllers | 1h |
| TASK-RHS-021 | SafetyController | Controllers | 1h |
| TASK-RHS-022 | GlobalExceptionHandler | Controllers | 1h |
| TASK-RHS-023 | MongoConfig + RedisConfig | Config | 1.5h |
| TASK-RHS-024 | NATSConfig | Config | 1h |
| TASK-RHS-025 | Unit tests: AVMatchingService | Tests | 2h |
| TASK-RHS-026 | Unit tests: TripStateMachineService | Tests | 2h |
| TASK-RHS-027 | Unit tests: ETAService (fallback) | Tests | 1.5h |
| TASK-RHS-028 | Unit tests: PooledTripService | Tests | 1.5h |
| TASK-RHS-029 | Integration tests: Booking + trip flow API | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-RHS-001: Trip Domain Model (11-State)

**Parent WP Task**: WP-004-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/models/Trip.java`
- `src/main/java/com/vnpt/avplatform/rhs/models/TripStatus.java`
- `src/main/java/com/vnpt/avplatform/rhs/models/TripType.java`

**Specification**:
```java
// TripStatus.java — 11 states
public enum TripStatus {
    REQUESTED,      // rider submits booking request
    MATCHING,       // system searching for AV
    MATCHED,        // AV assigned
    AV_EN_ROUTE,    // AV heading to pickup
    ARRIVED,        // AV at pickup location
    IN_PROGRESS,    // trip ongoing
    COMPLETED,      // trip finished
    CANCELLED,      // cancelled before pickup
    FAILED_MATCH,   // no AV found within timeout
    SAFETY_STOP,    // emergency stop triggered
    DISPUTE         // rider filed dispute
}

// TripType.java
public enum TripType { STANDARD, POOLED }

// Trip.java
@Document(collection = "trips")
public class Trip {
    @Id private String id;

    @Field("trip_id")
    @Indexed(unique = true)
    private String tripId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001

    @Field("rider_id")
    @Indexed
    @NotBlank
    private String riderId;

    @Field("vehicle_id")
    private String vehicleId; // set after matching

    @Field("trip_type")
    @NotNull
    private TripType tripType = TripType.STANDARD;

    @Field("status")
    @NotNull
    private TripStatus status = TripStatus.REQUESTED;

    @Field("status_history")
    private List<TripStatusEntry> statusHistory = new ArrayList<>();

    @Field("pickup_lat")
    private double pickupLat;

    @Field("pickup_lng")
    private double pickupLng;

    @Field("dropoff_lat")
    private double dropoffLat;

    @Field("dropoff_lng")
    private double dropoffLng;

    @Field("pickup_address")
    private String pickupAddress;

    @Field("dropoff_address")
    private String dropoffAddress;

    @Field("estimated_distance_km")
    private double estimatedDistanceKm;

    @Field("estimated_duration_min")
    private int estimatedDurationMin;

    @Field("actual_distance_km")
    private Double actualDistanceKm; // null until trip COMPLETED

    @Field("actual_duration_min")
    private Integer actualDurationMin; // null until trip COMPLETED

    @Field("fare_id")
    private String fareId; // from FPE

    @Field("promo_code")
    private String promoCode;

    @Field("matching_score")
    private Double matchingScore; // AV score at assignment time

    @Field("eta_min")
    private Integer etaMin; // updated every 30s via NATS

    @Field("pool_trip_id")
    private String poolTripId; // for POOLED trips

    @Field("safety_stop_triggered")
    private boolean safetyStopTriggered = false;

    @Field("requested_at")
    @Indexed
    private Instant requestedAt = Instant.now();

    @Field("matched_at")
    private Instant matchedAt;

    @Field("started_at")
    private Instant startedAt;

    @Field("completed_at")
    private Instant completedAt;

    @Version
    private Long version;
}

// TripStatusEntry (embedded):
public class TripStatusEntry {
    private TripStatus status;
    private Instant timestamp;
    private String reason; // for cancellation, failure
}
```

**Definition of Done**:
- [ ] All 11 `TripStatus` values defined
- [ ] `statusHistory` is an embedded list of `TripStatusEntry` (audit trail)
- [ ] `@Version` for optimistic locking on state transitions
- [ ] `actualDistanceKm` is nullable (null until COMPLETED)
- [ ] Indexes: `tripId` unique, `tenantId`, `riderId`, `requestedAt`

---

### TASK-RHS-002: Vehicle Model (For Matching)

**Parent WP Task**: WP-004-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/models/Vehicle.java`
- `src/main/java/com/vnpt/avplatform/rhs/models/VehicleAvailability.java`

**Specification**:
```java
// Used for matching lookups — read-only from VMS Redis cache in RHS
// This is a local DTO for matching algorithm, not the canonical model

// VehicleAvailability.java — from VMS Redis sorted set
public class VehicleAvailability {
    private String vehicleId;
    private String tenantId;
    private double latitude;
    private double longitude;
    private double batteryPct;       // 0–100
    private boolean oddCompliant;    // Operational Design Domain compliant
    private String vehicleType;      // SEDAN, SUV, VAN
    private double distanceKm;       // computed from rider pickup location
    private double oddScore;         // 0.0–1.0; 0 = hard disqualify
    private double matchingScore;    // computed: 0.4×proximity + 0.2×battery + 0.3×ODD + 0.1×type
}
```

**Definition of Done**:
- [ ] `oddScore = 0` → hard disqualify (enforced in AVMatchingService)
- [ ] `matchingScore` computed in AVMatchingService (not stored here)
- [ ] `distanceKm` max matching radius: 5km

---

### TASK-RHS-003: CancellationFeeRecord Domain Model

**Parent WP Task**: WP-004-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/models/CancellationFeeRecord.java`

**Specification**:
```java
@Document(collection = "cancellation_fees")
public class CancellationFeeRecord {
    @Id private String id;

    @Field("trip_id")
    @Indexed
    private String tripId;

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("rider_id")
    private String riderId;

    @Field("fee_vnd")
    private Long feeVnd; // Long (whole VND), 0 if waived

    @Field("fee_policy")
    private String feePolicy; // "NO_FEE", "PARTIAL", "FULL" based on when cancelled

    @Field("cancellation_stage")
    private TripStatus stageAtCancellation; // what status was the trip in

    @Field("minutes_after_match")
    private int minutesAfterMatch; // 0–5 free, 5+ = fee applies

    @Field("waived")
    private boolean waived = false;

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Cancellation Fee Policy**:
- Status `REQUESTED`: free cancellation
- Status `MATCHING` or `MATCHED`: free (< 5 min after match) OR fee (> 5 min)
- Status `AV_EN_ROUTE` or `ARRIVED`: fee applies (30% of fare estimate)
- `fee_vnd = 0` when waived

**Definition of Done**:
- [ ] `cancellationStage` captures which status the trip was in when cancelled
- [ ] `minutesAfterMatch` computed from `matchedAt` to cancellation time
- [ ] `feeVnd = 0` when `waived = true`

---

### TASK-RHS-004: TripRating Domain Model

**Parent WP Task**: WP-004-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/models/TripRating.java`

**Specification**:
```java
@Document(collection = "trip_ratings")
public class TripRating {
    @Id private String id;

    @Field("trip_id")
    @Indexed(unique = true)  // one rating per trip
    private String tripId;

    @Field("tenant_id")
    @Indexed
    private String tenantId;

    @Field("rider_id")
    private String riderId;

    @Field("vehicle_id")
    private String vehicleId;

    // Rating dimensions (1–5 integer each)
    @Field("cleanliness")
    @Min(1) @Max(5)
    private int cleanliness;

    @Field("safety")
    @Min(1) @Max(5)
    private int safety;

    @Field("comfort")
    @Min(1) @Max(5)
    private int comfort;

    @Field("overall")
    private double overall; // computed: average of 3 dimensions

    @Field("comment")
    @Size(max = 500)
    private String comment;

    @Field("trip_completed_at")
    private Instant tripCompletedAt; // for 48h window check

    @Field("rated_at")
    private Instant ratedAt = Instant.now();
}
```

**Rating Window**: Rating only accepted if `ratedAt - tripCompletedAt <= 48 hours`  
**Overall**: `(cleanliness + safety + comfort) / 3.0` rounded to 1 decimal

**Definition of Done**:
- [ ] `@Indexed(unique = true)` on `tripId` (one rating per trip)
- [ ] 48h window enforced in `RatingService` (not in model)
- [ ] `overall` computed as average of 3 dimensions

---

## Task Group 2: Repository Layer

### TASK-RHS-005: TripRepository (State Machine Queries)

**Parent WP Task**: WP-004-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/repositories/TripRepository.java`
- `src/main/java/com/vnpt/avplatform/rhs/repositories/impl/TripRepositoryImpl.java`

**Specification**:
```java
public interface TripRepository {
    Trip save(Trip trip);
    Optional<Trip> findByTripId(String tripId);
    Optional<Trip> findActiveByRiderId(String riderId, String tenantId);
    // Atomic status transition with optimistic lock:
    boolean transitionStatus(String tripId, TripStatus expectedStatus, TripStatus newStatus, String reason, Long version);
    List<Trip> findByStatusAndTenantId(TripStatus status, String tenantId, int page, int size);
    Trip assignVehicle(String tripId, String vehicleId, double matchingScore, int etaMin);
}

// transitionStatus() — atomic with optimistic lock:
// Query: { trip_id: tripId, status: expectedStatus, version: version }
// Update: {
//   $set: { status: newStatus, last_updated_at: now },
//   $inc: { version: 1 },
//   $push: { status_history: { status: newStatus, timestamp: now, reason: reason } }
// }
// Returns: updateResult.getMatchedCount() == 1

// findActiveByRiderId():
// Criteria: rider_id = riderId AND tenant_id = tenantId
//           AND status NOT IN [COMPLETED, CANCELLED, FAILED_MATCH]
// Used to prevent duplicate bookings
```

**Definition of Done**:
- [ ] `transitionStatus` is atomic (single `updateFirst` with version check)
- [ ] `$push` to `statusHistory` on every transition
- [ ] `findActiveByRiderId` excludes terminal statuses
- [ ] All queries include `tenant_id` filter (BL-001)

---

### TASK-RHS-006: VehicleRepository

**Parent WP Task**: WP-004-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/repositories/VehicleAvailabilityRepository.java`
- `src/main/java/com/vnpt/avplatform/rhs/repositories/impl/VehicleAvailabilityRepositoryImpl.java`

**Specification**:
```java
public interface VehicleAvailabilityRepository {
    // Fetch available vehicles from VMS Redis sorted set within radius:
    List<VehicleAvailability> findAvailableWithinRadius(
        String tenantId, double pickupLat, double pickupLng,
        double radiusKm, String vehicleType
    );
}

// Implementation reads from Redis:
// Key: "vehicles:{tenantId}:{vehicleType}" — Geo sorted set (maintained by VMS)
// Command: GEORADIUS "vehicles:{tenantId}:{vehicleType}" {lng} {lat} {radiusKm} km WITHCOORD WITHDIST COUNT 20 ASC
// Then fetch vehicle details: HGETALL "vehicle_info:{vehicleId}"
// Note: radiusKm max = 5.0 (hard cap from SRS)
```

**Definition of Done**:
- [ ] Max radius capped at 5.0 km in implementation
- [ ] Fetches vehicle details from Redis hash `vehicle_info:{vehicleId}`
- [ ] Returns empty list if no vehicles found (never throws exception)

---

## Task Group 3: Security

### TASK-RHS-007: TenantContextFilter + TenantContextHolder

**Parent WP Task**: WP-004-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/rhs/security/TenantContextHolder.java`

**Specification**: Same pattern as TMS (TASK-TMS-008/009).
```java
// TenantContextFilter: OncePerRequestFilter, @Order(1)
// Extract from JWT "tenant_id" claim OR "X-Tenant-ID" header
// TenantContextHolder.setTenantId(tenantId)
// finally: TenantContextHolder.clear()
```

**Definition of Done**:
- [ ] `clear()` in `finally` block
- [ ] `@Order(1)` filter priority

---

## Task Group 4: Core Services

### TASK-RHS-008: AVMatchingService (Scoring Algorithm)

**Parent WP Task**: WP-004-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/AVMatchingService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/AVMatchingServiceImpl.java`

**Specification**:
```java
public interface AVMatchingService {
    Optional<VehicleAvailability> findBestMatch(MatchRequest request);
}

// MatchRequest: tenantId, pickupLat, pickupLng, vehicleType

// findBestMatch():
//   Attempt 1: radius = 2.0 km
//   If no results: Attempt 2: radius = 5.0 km
//   For each vehicle in radius:
//     1. If vehicle.oddScore == 0 → SKIP (hard disqualify)
//     2. If vehicle.batteryPct < 20 → SKIP (insufficient battery for trip)
//     3. Compute matching score:
//        proximityScore = 1.0 - (distanceKm / 5.0)  // normalized to 0–1
//        batteryScore = vehicle.batteryPct / 100.0
//        oddScore = vehicle.oddScore
//        typeScore = vehicleType matches requested ? 1.0 : 0.0
//        matchingScore = 0.4 × proximityScore + 0.2 × batteryScore + 0.3 × oddScore + 0.1 × typeScore
//   Sort by matchingScore descending
//   Return top vehicle (highest score)

// Redis lock for AV assignment to prevent race condition:
//   SET "match_lock:{vehicleId}" {tripId} NX EX 30
//   If lock fails (already assigned): skip to next vehicle
//   Return Optional.empty() if no vehicles available after all attempts

// Redis attempt tracking:
//   INCR "match:{tripId}:attempt" EX 300
//   For display only (used by TripStateMachineService for timeout)
```

**Definition of Done**:
- [ ] `oddScore == 0` → hard disqualify (skip immediately)
- [ ] Matching formula: `0.4×proximity + 0.2×battery + 0.3×ODD + 0.1×type` (exact weights)
- [ ] Redis `SET NX EX 30` lock prevents double-assignment
- [ ] Two-pass: 2km first, then expand to 5km on no results
- [ ] `AVMatchingServiceTest` with 5 vehicles at varying distances + ODD scores

---

### TASK-RHS-009: ETAService (ML + Fallback)

**Parent WP Task**: WP-004-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/ETAService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/ETAServiceImpl.java`

**Specification**:
```java
public interface ETAService {
    int computeETA(String vehicleId, double pickupLat, double pickupLng); // returns minutes
    void startETAUpdater(String tripId, String vehicleId); // starts 30s NATS updates
    void stopETAUpdater(String tripId); // stops on ARRIVED/COMPLETED/CANCELLED
}

// computeETA():
//   CompletableFuture<Integer> mlFuture = CompletableFuture.supplyAsync(() ->
//       mlEtaClient.predict(vehicleId, pickupLat, pickupLng)  // POST to ML service
//   ).completeOnTimeout(null, 3, TimeUnit.SECONDS); // 3s timeout
//
//   Integer mlEta = mlFuture.get();
//   if (mlEta != null) return mlEta;
//
//   // Fallback formula: ceil(distance / 30 km/h × 60 min) + 3 min buffer
//   double distance = calculateHaversineDistance(vehicleId, pickupLat, pickupLng);
//   return (int) Math.ceil(distance / 30.0 * 60) + 3;

// startETAUpdater():
//   ScheduledFuture<?> future = scheduler.scheduleAtFixedRate(() -> {
//       int eta = computeETA(vehicleId, trip.getPickupLat(), trip.getPickupLng());
//       natsPublisher.publishEtaUpdate(tripId, eta);
//   }, 0, 30, TimeUnit.SECONDS);
//   etaUpdaterMap.put(tripId, future); // ConcurrentHashMap

// stopETAUpdater():
//   ScheduledFuture<?> future = etaUpdaterMap.remove(tripId);
//   if (future != null) future.cancel(false);

// Haversine distance:
//   double R = 6371; // Earth radius km
//   double dLat = Math.toRadians(lat2 - lat1);
//   double dLon = Math.toRadians(lon2 - lon1);
//   double a = Math.sin(dLat/2) × Math.sin(dLat/2) + ...
//   double c = 2 × Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
//   return R × c;
```

**Definition of Done**:
- [ ] ML timeout: 3 seconds → fallback formula
- [ ] Fallback: `ceil(distance/30×60) + 3` minutes
- [ ] ETA updates published via NATS every 30 seconds
- [ ] `etaUpdaterMap` is `ConcurrentHashMap<String, ScheduledFuture<?>>` (thread-safe)
- [ ] `stopETAUpdater` cancels scheduled task on trip terminal state
- [ ] `ETAServiceTest`: ML timeout test → fallback formula used

---

### TASK-RHS-010: TripStateMachineService (11-State Transitions)

**Parent WP Task**: WP-004-T05  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/TripStateMachineService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/TripStateMachineServiceImpl.java`

**Specification**:
```java
public interface TripStateMachineService {
    Trip transition(String tripId, TripStatus newStatus, String reason);
    void startMatchingTimeout(String tripId); // 30s timeout → FAILED_MATCH
}

// Valid transitions map (from → allowed next states):
// REQUESTED → [MATCHING, CANCELLED]
// MATCHING → [MATCHED, FAILED_MATCH, CANCELLED]
// MATCHED → [AV_EN_ROUTE, CANCELLED]
// AV_EN_ROUTE → [ARRIVED, SAFETY_STOP, CANCELLED]
// ARRIVED → [IN_PROGRESS, SAFETY_STOP, CANCELLED]
// IN_PROGRESS → [COMPLETED, SAFETY_STOP]
// COMPLETED → [DISPUTE] (within 48h)
// CANCELLED → [] (terminal)
// FAILED_MATCH → [MATCHING] (retry allowed)
// SAFETY_STOP → [DISPUTE]
// DISPUTE → [] (terminal — handled by ops)

// transition():
//   1. Load trip by tripId
//   2. Check: newStatus in ALLOWED_TRANSITIONS.get(currentStatus)
//      → else throw InvalidTripTransitionException (HTTP 409 "INVALID_TRANSITION")
//   3. tripRepository.transitionStatus(tripId, currentStatus, newStatus, reason, version)
//   4. If false (optimistic lock conflict): reload trip and retry once
//   5. Publish ride-events Kafka event
//   6. Publish NATS status update (real-time)
//   7. Side effects per transition:
//      → MATCHED: start ETA updater, assign vehicle
//      → IN_PROGRESS: record startedAt
//      → COMPLETED: record completedAt, actual distance/duration, trigger FPE finalize
//      → CANCELLED: cancel ETA updater, trigger cancellation fee calculation
//      → SAFETY_STOP: trigger SafetyStopService

// startMatchingTimeout():
//   scheduler.schedule(() -> {
//       Trip trip = tripRepository.findByTripId(tripId).orElse(null);
//       if (trip != null && trip.getStatus() == TripStatus.MATCHING) {
//           transition(tripId, TripStatus.FAILED_MATCH, "MATCH_TIMEOUT");
//       }
//   }, 30, TimeUnit.SECONDS);
```

**Definition of Done**:
- [ ] All 11 states with valid transitions defined as immutable Map
- [ ] `InvalidTripTransitionException` on illegal transition (HTTP 409)
- [ ] `COMPLETED` transition triggers FPE finalize (Kafka event `fare.finalize`)
- [ ] `MATCHED` transition starts ETA updater
- [ ] 30s matching timeout → `FAILED_MATCH`
- [ ] `TripStateMachineServiceTest`: illegal transition test, optimistic lock retry test

---

### TASK-RHS-011: BookingService (Create + Duplicate Prevention)

**Parent WP Task**: WP-004-T06  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/BookingService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/BookingServiceImpl.java`

**Specification**:
```java
public interface BookingService {
    TripDTO createBooking(CreateBookingRequest request);
    TripDTO cancelBooking(String tripId, String riderId, String reason);
}

// createBooking():
//   1. Check Redis: "active_trip:{riderId}:{tenantId}" → if exists: throw DuplicateBookingException (HTTP 409 "ACTIVE_TRIP_EXISTS")
//   2. Validate FPE fareId: GET /api/v1/fares/{fareId} → must be locked=true and not finalized
//   3. Create Trip { status: REQUESTED }
//   4. Set Redis: "active_trip:{riderId}:{tenantId}" = tripId EX 7200 (2h max trip duration)
//   5. Transition to MATCHING: tripStateMachineService.transition(tripId, MATCHING)
//   6. Start matching: avMatchingService.findBestMatch() → async (non-blocking)
//      If match found: transition to MATCHED, assign vehicle, start ETA updater
//      If no match after 30s: transition to FAILED_MATCH
//   7. Publish Kafka: ride.requested
//   8. Return TripDTO { tripId, status: MATCHING }

// cancelBooking():
//   1. Load trip, verify riderId matches
//   2. Calculate cancellation fee
//   3. Transition to CANCELLED
//   4. Del Redis: "active_trip:{riderId}:{tenantId}"
//   5. Publish Kafka: ride.cancelled
//   6. Trigger escrow release via PAY service (Kafka event)
//   7. Return updated TripDTO
```

**Definition of Done**:
- [ ] Duplicate prevention: Redis `"active_trip:{riderId}:{tenantId}"` key check FIRST
- [ ] Redis TTL: 7200s (2 hours — max expected trip duration)
- [ ] Cancel clears Redis key `"active_trip:{riderId}:{tenantId}"`
- [ ] `BookingServiceTest`: duplicate booking test, cancel-clears-redis test

---

### TASK-RHS-012: PooledTripService (Max 2 Passengers)

**Parent WP Task**: WP-004-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/PooledTripService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/PooledTripServiceImpl.java`

**Specification**:
```java
public interface PooledTripService {
    Optional<String> findCompatiblePool(String tenantId, double pickupLat, double pickupLng,
        double dropoffLat, double dropoffLng, String vehicleType);
    String createPool(String tenantId, String tripId, TripType tripType);
    boolean joinPool(String poolTripId, String tripId);
}

// Pool constraints (v1.0):
//   Max 2 passengers per pool
//   Pickup radius: 1.5 km between riders
//   Dropoff radius: 3.0 km between riders
//   Detour allowance: ≤ 20% of original estimated distance

// findCompatiblePool():
//   Search Redis sorted set: "pool_candidates:{tenantId}" (geo-indexed)
//   GEORADIUS within 1.5km of pickupLat/pickupLng
//   For each candidate pool:
//     Check passenger count < 2
//     Check dropoff distance ≤ 3km
//     Check estimated detour ≤ 20%: detourPct = (newTotalDist - originalDist) / originalDist × 100
//     First eligible pool → return poolTripId
//   Return Optional.empty() if none found

// joinPool():
//   Atomic Redis INCR on "pool:{poolTripId}:passengers"
//   If count > 2: DECR back, return false (rejected)
//   Add tripId to "pool:{poolTripId}:trips" list
//   Call FPE /api/v1/fares/pool/compute-split for fare recalculation
//   Return true

// Pool Redis keys:
//   "pool_candidates:{tenantId}" — geo sorted set of active pool positions
//   "pool:{poolTripId}:passengers" — counter (0–2)
//   "pool:{poolTripId}:trips" — list of tripIds
```

**Definition of Done**:
- [ ] Max 2 passengers enforced atomically via Redis INCR
- [ ] Pickup radius: 1.5km (GEORADIUS)
- [ ] Dropoff radius: 3.0km
- [ ] Detour ≤ 20% calculation implemented
- [ ] `PooledTripServiceTest`: 3rd passenger rejected, detour exceeded test

---

### TASK-RHS-013: CancellationFeeService

**Parent WP Task**: WP-004-T08  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/CancellationFeeService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/CancellationFeeServiceImpl.java`

**Specification**:
```java
public interface CancellationFeeService {
    CancellationFeeRecord computeFee(Trip trip, Instant cancelledAt);
}

// Fee policy:
// Status REQUESTED: fee = 0 (free)
// Status MATCHING or MATCHED, < 5 min after match: fee = 0 (free)
// Status MATCHING or MATCHED, ≥ 5 min after match: fee = 10% of fare estimate
// Status AV_EN_ROUTE: fee = 20% of fare estimate
// Status ARRIVED: fee = 30% of fare estimate (AV already waiting)

// computeFee():
//   minutesAfterMatch = ChronoUnit.MINUTES.between(trip.getMatchedAt(), cancelledAt)
//   Fetch fare estimate from FPE service (HTTP GET /api/v1/fares/{fareId})
//   estimatedFareVnd = fareResponse.getLockedFareVnd()
//   feeVnd based on policy above
//   Create and save CancellationFeeRecord
//   If fee > 0: publish Kafka event "payment.cancellation_fee" for PAY to charge
```

**Definition of Done**:
- [ ] Fee computed from fare estimate (not a flat fee)
- [ ] ARRIVED status → 30% fee (highest — AV waiting penalty)
- [ ] Fee = 0 when status is REQUESTED (free cancellation always)
- [ ] Publishes Kafka event for fee > 0 cases

---

### TASK-RHS-014: SafetyStopService

**Parent WP Task**: WP-004-T09  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/SafetyStopService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/SafetyStopServiceImpl.java`

**Specification**:
```java
public interface SafetyStopService {
    void triggerSafetyStop(String tripId, String triggeredBy, String location);
}

// triggerSafetyStop():
//   1. Transition trip to SAFETY_STOP status
//   2. Publish Kafka: "ride.safety_stop" event (consumed by NCS for critical alert)
//   3. NCS will send CRITICAL alert to rider + operator (FCM + SMS simultaneously < 5s SLA via NCS BL-007)
//   4. No cancellation fee for SAFETY_STOP trips
//   NOTE: RHS only publishes the event. NCS handles notification delivery.
```

**Definition of Done**:
- [ ] Publishes `ride.safety_stop` Kafka event immediately (< 100ms)
- [ ] NCS handles notification (RHS does NOT call NCS directly)
- [ ] No cancellation fee for SAFETY_STOP transitions

---

### TASK-RHS-015: RatingService (48h Window, Dimensions)

**Parent WP Task**: WP-004-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/services/RatingService.java`
- `src/main/java/com/vnpt/avplatform/rhs/services/impl/RatingServiceImpl.java`

**Specification**:
```java
public interface RatingService {
    TripRating submitRating(SubmitRatingRequest request);
    Optional<TripRating> getRating(String tripId, String tenantId);
}

// submitRating():
//   1. Load trip by tripId
//   2. Verify trip.status == COMPLETED
//   3. Check 48h window: if (Instant.now().isAfter(trip.getCompletedAt().plus(48, ChronoUnit.HOURS)))
//      throw RatingWindowExpiredException (HTTP 410 "RATING_WINDOW_EXPIRED")
//   4. Check no existing rating: if exists throw DuplicateRatingException (HTTP 409)
//   5. Compute overall = (cleanliness + safety + comfort) / 3.0, round to 1 decimal
//   6. Save TripRating
//   7. Publish Kafka: "ride.rated" with vehicleId and overall score (for VMS to update vehicle rating)

// SubmitRatingRequest validation:
//   cleanliness: @Min(1) @Max(5)
//   safety: @Min(1) @Max(5)
//   comfort: @Min(1) @Max(5)
//   comment: @Size(max=500)
```

**Definition of Done**:
- [ ] 48h window enforced (HTTP 410 after expiry)
- [ ] Duplicate rating rejected (HTTP 409)
- [ ] `overall` = average of 3 dimensions, rounded to 1 decimal place
- [ ] Publishes `ride.rated` for VMS to update vehicle rating

---

## Task Group 5: NATS Integration

### TASK-RHS-016: NATSPublisher (ETA + Status Real-Time)

**Parent WP Task**: WP-004-T11  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/nats/NATSPublisher.java`
- `src/main/java/com/vnpt/avplatform/rhs/nats/TripUpdateMessage.java`

**Specification**:
```java
// Library: io.nats:jnats:2.17.x
// NATS subject pattern: "trips.{tenantId}.{tripId}.updates"

public class TripUpdateMessage {
    private String tripId;
    private String tenantId;
    private String updateType; // "ETA_UPDATE", "STATUS_CHANGE"
    private TripStatus status; // current status
    private Integer etaMin;    // for ETA_UPDATE
    private Instant timestamp;
}

@Component
public class NATSPublisher {
    private final Connection natsConnection;

    public void publishEtaUpdate(String tripId, String tenantId, int etaMin) {
        TripUpdateMessage msg = new TripUpdateMessage();
        msg.setTripId(tripId);
        msg.setTenantId(tenantId);
        msg.setUpdateType("ETA_UPDATE");
        msg.setEtaMin(etaMin);
        msg.setTimestamp(Instant.now());

        String subject = "trips." + tenantId + "." + tripId + ".updates";
        natsConnection.publish(subject, objectMapper.writeValueAsBytes(msg));
    }

    public void publishStatusChange(String tripId, String tenantId, TripStatus status) {
        TripUpdateMessage msg = new TripUpdateMessage();
        msg.setUpdateType("STATUS_CHANGE");
        msg.setStatus(status);
        // publish to same subject
    }
}
```

**Definition of Done**:
- [ ] NATS subject: `trips.{tenantId}.{tripId}.updates`
- [ ] ETA updates every 30s (scheduled by ETAService)
- [ ] Status changes published immediately on transition
- [ ] Non-blocking publish (fire-and-forget for ETA updates)

---

## Task Group 6: Kafka Integration

### TASK-RHS-017: RideKafkaProducer (ride-events)

**Parent WP Task**: WP-004-T11  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/events/RideKafkaProducer.java`
- `src/main/java/com/vnpt/avplatform/rhs/events/RideEvent.java`

**Specification**:
```java
// Topic: "ride-events" — 12 partitions
// Partition key: tenantId

// RideEvent types:
//   "ride.requested" — booking created
//   "ride.matched"   — AV assigned
//   "ride.started"   — IN_PROGRESS
//   "ride.completed" — triggers PAY capture + FPE finalize
//   "ride.cancelled" — triggers PAY escrow release
//   "ride.rated"     — rating submitted
//   "ride.safety_stop" — safety stop (critical path for NCS)
//   "ride.eta_late"  — actual ETA > 10 min late (triggers auto-refund BL-005)

public class RideEvent {
    private String eventId = UUID.randomUUID().toString();
    private String eventType;
    private String tenantId;
    private String tripId;
    private String riderId;
    private String vehicleId;
    private TripStatus status;
    private Double actualDistanceKm; // on completed
    private Integer actualDurationMin; // on completed
    private String fareId; // on completed — for FPE to finalize
    private Instant timestamp = Instant.now();
}
```

**Definition of Done**:
- [ ] `ride.completed` event includes `fareId`, `actualDistanceKm`, `actualDurationMin`
- [ ] `ride.safety_stop` published synchronously (within 100ms of trigger)
- [ ] `ride.eta_late` published when ETA > `trip.estimatedEta + 10 min` (BL-005)
- [ ] Partition key = `tenantId`

---

## Task Group 7: REST Controllers

### TASK-RHS-018: TripController

**Parent WP Task**: WP-004-T12  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/controllers/TripController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/trips")
public class TripController {

    // GET /api/v1/trips/{tripId}
    @GetMapping("/{tripId}")
    public TripDTO getTrip(@PathVariable String tripId) {
        String tenantId = TenantContextHolder.requireTenantId();
        return tripStateMachineService.getTrip(tripId, tenantId);
    }

    // GET /api/v1/trips?status=IN_PROGRESS&page=0&size=20
    @GetMapping
    @PreAuthorize("hasAnyRole('TENANT_ADMIN', 'OPERATOR')")
    public List<TripDTO> listTrips(
        @RequestParam(required = false) TripStatus status,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) { ... }

    // POST /api/v1/trips/{tripId}/status (internal — AV reports status changes)
    @PostMapping("/{tripId}/status")
    @PreAuthorize("hasRole('INTERNAL_SERVICE')")
    public TripDTO updateStatus(
        @PathVariable String tripId,
        @Valid @RequestBody UpdateStatusRequest request
    ) {
        return tripStateMachineService.transition(tripId, request.getNewStatus(), request.getReason());
    }
}
```

**Definition of Done**:
- [ ] `GET /{tripId}` tenant-scoped (rider sees only their own trips)
- [ ] `POST /{tripId}/status` is INTERNAL_SERVICE only (AV reports status)
- [ ] `listTrips` TENANT_ADMIN/OPERATOR only

---

### TASK-RHS-019: BookingController

**Parent WP Task**: WP-004-T12  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/controllers/BookingController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/bookings")
public class BookingController {

    // POST /api/v1/bookings
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public TripDTO createBooking(@Valid @RequestBody CreateBookingRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        return bookingService.createBooking(request.withTenantId(tenantId));
    }

    // DELETE /api/v1/bookings/{tripId}
    @DeleteMapping("/{tripId}")
    public TripDTO cancelBooking(
        @PathVariable String tripId,
        @RequestBody(required = false) CancelBookingRequest request
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        String reason = request != null ? request.getReason() : "RIDER_CANCELLED";
        return bookingService.cancelBooking(tripId, tenantId, reason);
    }
}

// CreateBookingRequest validation:
//   pickupLat: @DecimalMin("-90.0") @DecimalMax("90.0")
//   pickupLng: @DecimalMin("-180.0") @DecimalMax("180.0")
//   dropoffLat, dropoffLng: same
//   fareId: @NotBlank (must be locked fare from FPE)
//   tripType: default STANDARD; POOLED if pool requested
//   vehicleType: @NotNull
```

**Definition of Done**:
- [ ] HTTP 409 when active trip exists for rider (duplicate prevention)
- [ ] `fareId` validated as non-blank (fare must be pre-locked)
- [ ] DELETE → triggers cancellation fee calculation

---

### TASK-RHS-020: RatingController

**Parent WP Task**: WP-004-T12  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/controllers/RatingController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/trips/{tripId}/rating")
public class RatingController {

    // POST /api/v1/trips/{tripId}/rating
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public TripRatingDTO submitRating(
        @PathVariable String tripId,
        @Valid @RequestBody SubmitRatingRequest request
    ) { ... }

    // GET /api/v1/trips/{tripId}/rating
    @GetMapping
    public TripRatingDTO getRating(@PathVariable String tripId) { ... }
}
```

**Definition of Done**:
- [ ] POST returns HTTP 201 Created
- [ ] HTTP 410 after 48h window expires
- [ ] HTTP 409 on duplicate rating

---

## Task Group 8: Configuration

### TASK-RHS-023: MongoConfig + RedisConfig

**Parent WP Task**: WP-004-T02  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/config/MongoConfig.java`
- `src/main/java/com/vnpt/avplatform/rhs/config/RedisConfig.java`

**Specification**:
```java
// MongoConfig indexes:
// trips: trip_id (unique), tenant_id, rider_id, requested_at, status (for status queries)
// Compound: { rider_id, tenant_id, status } (for active trip lookup)

// RedisConfig:
// @Bean RedisTemplate<String, String> — for string operations
// @Bean LettuceConnectionFactory with SSL (PCI-DSS compliant Redis)
```

**Definition of Done**:
- [ ] Compound index `{ rider_id, tenant_id }` on trips (for active trip check)
- [ ] Trip index includes `status` for `findByStatusAndTenantId` queries

---

### TASK-RHS-024: NATSConfig

**Parent WP Task**: WP-004-T11  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/rhs/config/NATSConfig.java`

**Specification**:
```java
@Configuration
public class NATSConfig {

    @Bean
    public Connection natsConnection(@Value("${nats.servers}") String servers) throws IOException, InterruptedException {
        Options options = new Options.Builder()
            .servers(servers.split(","))
            .maxReconnects(-1) // infinite reconnects
            .reconnectWait(Duration.ofSeconds(2))
            .connectionTimeout(Duration.ofSeconds(10))
            .build();
        return Nats.connect(options);
    }
}
// spring.nats.servers=nats://nats-1:4222,nats://nats-2:4222
// Cluster connection for high availability
```

**Definition of Done**:
- [ ] Infinite reconnect attempts (`maxReconnects(-1)`)
- [ ] 2s reconnect wait
- [ ] Cluster URLs from configuration (not hardcoded)

---

## Task Group 9: Tests

### TASK-RHS-025: Unit Tests — AVMatchingService

**Parent WP Task**: WP-004-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/rhs/services/AVMatchingServiceTest.java`

**Test Cases**:
```
1. hardDisqualify_oddScore0: vehicle with oddScore=0 always excluded
2. batteryTooLow: vehicle with battery < 20% excluded
3. bestScoreSelected: 3 vehicles → vehicle with highest formula score returned
4. scoringFormula: verify 0.4×proximity + 0.2×battery + 0.3×ODD + 0.1×type weights
5. twoPassRadius: no vehicles at 2km → expands to 5km and finds vehicle
6. lockPreventsDoubleAssignment: Redis NX lock rejects already-assigned vehicle
7. noVehicles_returnsEmpty: all vehicles excluded → Optional.empty()
8. matchRadius5km_hardCap: vehicle at 6km never returned even if only one available
```

**Definition of Done**:
- [ ] 8 test cases passing
- [ ] Test 4: exact formula weights verified with known inputs
- [ ] Test 6: Redis mock verifies `SET NX` used for vehicle lock

---

### TASK-RHS-026: Unit Tests — TripStateMachineService

**Parent WP Task**: WP-004-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/rhs/services/TripStateMachineServiceTest.java`

**Test Cases**:
```
1. validTransition_REQUESTED_to_MATCHING: succeeds
2. validTransition_MATCHING_to_MATCHED: succeeds, ETA updater started
3. validTransition_IN_PROGRESS_to_COMPLETED: triggers FPE finalize event
4. validTransition_AV_EN_ROUTE_to_CANCELLED: cancellation fee computed
5. invalidTransition_COMPLETED_to_MATCHING: InvalidTripTransitionException (HTTP 409)
6. invalidTransition_CANCELLED_to_MATCHING: InvalidTripTransitionException
7. optimisticLock_conflict_retries: version conflict → retry once
8. statusHistory_updated_on_transition: statusHistory contains new entry
9. matchingTimeout_triggers_FAILED_MATCH: after 30s, FAILED_MATCH transition occurs
10. SAFETY_STOP_no_cancellation_fee: SafetyStop → no fee record created
```

**Definition of Done**:
- [ ] 10 test cases passing
- [ ] Test 5 and 6: exact exception type `InvalidTripTransitionException`
- [ ] Test 9: uses `TestScheduler` with 30s fast-forward

---

### TASK-RHS-027: Unit Tests — ETAService

**Parent WP Task**: WP-004-T13  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/rhs/services/ETAServiceTest.java`

**Test Cases**:
```
1. mlSuccess_returnsMLEta: ML responds in < 3s → ML ETA returned
2. mlTimeout_usesFallback: ML > 3s → fallback formula used
3. fallbackFormula_knownDistance: 10km → ceil(10/30×60)+3 = 23 minutes
4. startETAUpdater_schedulesTask: ScheduledFuture started
5. stopETAUpdater_cancelsTask: Future.cancel(false) called
6. etaLate_publishesEvent: actual ETA > estimated + 10 min → ride.eta_late event
```

**Definition of Done**:
- [ ] Test 2: `completeOnTimeout(null, 3, SECONDS)` verified
- [ ] Test 3: exact formula: `ceil(10.0/30.0×60)+3 = 23`

---

### TASK-RHS-028: Unit Tests — PooledTripService

**Parent WP Task**: WP-004-T13  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/rhs/services/PooledTripServiceTest.java`

**Test Cases**:
```
1. joinPool_success: first passenger joins pool
2. joinPool_twoPassengers: second passenger joins pool
3. joinPool_rejected_maxCapacity: third passenger → returns false
4. detourExceeded_notCompatible: 25% detour → pool rejected
5. detourWithinLimit_compatible: 15% detour → pool compatible
6. pickupRadius_exceeded: rider 2km from pickup point → not compatible (> 1.5km)
7. atomicIncr_concurrentJoin: two concurrent joins → only one succeeds when at capacity
```

**Definition of Done**:
- [ ] Test 3: Redis INCR → DECR when exceeding limit
- [ ] Test 7: concurrent join test verifies atomicity

---

### TASK-RHS-029: Integration Tests — Booking + Trip Flow API

**Parent WP Task**: WP-004-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/rhs/integration/BookingControllerIT.java`

**Test Cases**:
```
1. POST /api/v1/bookings → 201 Created, status=MATCHING
2. POST /api/v1/bookings (duplicate) → 409 Conflict
3. DELETE /api/v1/bookings/{tripId} → 200, status=CANCELLED
4. GET /api/v1/trips/{tripId} → 200 with trip details
5. POST /api/v1/trips/{tripId}/status (INTERNAL_SERVICE role) → 200 status updated
6. POST /api/v1/trips/{tripId}/rating → 201
7. POST /api/v1/trips/{tripId}/rating (after 48h) → 410
```

**Setup**: Testcontainers MongoDB + Redis + Kafka  
**Definition of Done**:
- [ ] 7 scenarios passing
- [ ] Test 2: Redis active_trip key verified as cause of 409
- [ ] Test 5: requires JWT with `INTERNAL_SERVICE` role

---

*DETAIL_PLAN_RHS v1.0.0 — RHS Ride Hailing Service | VNPT AV Platform Services Provider Group*
