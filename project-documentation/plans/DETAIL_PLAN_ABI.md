# DETAIL PLAN — ABI: Analytics & Business Intelligence Service

**Work Package**: WP-008 | **SRS**: SRS_ABI_Analytics_BI.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.abi`  
**Database**: MongoDB (`abi_db`, `daily_aggregates`) + Elasticsearch + InfluxDB  
**Events**: Kafka consumer group `abi-etl` (ride-events, payment-events, billing-events)  
**Object Storage**: MinIO (reports: PDF + CSV)  
**Critical**: BL-010 strict cross-tenant isolation — every ES query MUST include `must: { term: { tenant_id } }`  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-ABI-001 | DailyAggregate domain model (MongoDB) | Domain Models | 1.5h |
| TASK-ABI-002 | ReportJob domain model | Domain Models | 1h |
| TASK-ABI-003 | DailyAggregateRepository | Repository | 1h |
| TASK-ABI-004 | ReportJobRepository | Repository | 1h |
| TASK-ABI-005 | TenantContextFilter + TenantContextHolder | Security | 1.5h |
| TASK-ABI-006 | RideEventETLTransformer | ETL | 2h |
| TASK-ABI-007 | PaymentEventETLTransformer | ETL | 1.5h |
| TASK-ABI-008 | BillingEventETLTransformer | ETL | 1.5h |
| TASK-ABI-009 | ElasticsearchIndexingService (dual-write) | Services | 2h |
| TASK-ABI-010 | InfluxDBTimeSeriesService | Services | 1.5h |
| TASK-ABI-011 | DailyAggregationService (end-of-day CRON) | Services | 2h |
| TASK-ABI-012 | KPIComputationService (threshold classification) | Services | 1.5h |
| TASK-ABI-013 | HeatmapService (geotile_grid aggregation) | Services | 1.5h |
| TASK-ABI-014 | ReportGenerationService (JasperReports + CSV) | Services | 2h |
| TASK-ABI-015 | MinIOStorageService (presigned URLs) | Services | 1.5h |
| TASK-ABI-016 | ETLKafkaConsumer (abi-etl group) | Kafka | 2h |
| TASK-ABI-017 | AnalyticsController (query endpoints) | Controllers | 2h |
| TASK-ABI-018 | ReportController (generate + download) | Controllers | 1.5h |
| TASK-ABI-019 | GlobalExceptionHandler | Controllers | 1h |
| TASK-ABI-020 | MongoConfig + ElasticsearchConfig + InfluxDBConfig | Config | 2h |
| TASK-ABI-021 | MinIOConfig | Config | 1h |
| TASK-ABI-022 | Unit tests: ETL Transformers | Tests | 2h |
| TASK-ABI-023 | Unit tests: KPIComputationService + HeatmapService | Tests | 1.5h |
| TASK-ABI-024 | Unit tests: ReportGenerationService | Tests | 2h |
| TASK-ABI-025 | Integration tests: Analytics API | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-ABI-001: DailyAggregate Domain Model

**Parent WP Task**: WP-008-T01  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/models/DailyAggregate.java`
- `src/main/java/com/vnpt/avplatform/abi/models/AggregateType.java`

**Specification**:
```java
// AggregateType.java
public enum AggregateType {
    RIDE_SUMMARY,    // trip counts, distances, durations
    PAYMENT_SUMMARY, // revenue, gateway breakdown
    BILLING_SUMMARY  // subscriptions, overage
}

// DailyAggregate.java — upserted nightly by DailyAggregationService
@Document(collection = "daily_aggregates")
public class DailyAggregate {
    @Id private String id;

    @Field("aggregate_id")
    @Indexed(unique = true)
    private String aggregateId; // format: "{tenantId}:{date}:{type}" e.g. "t1:2025-01-15:RIDE_SUMMARY"

    @Field("tenant_id")
    @Indexed
    @NotBlank
    private String tenantId; // BL-001

    @Field("date")
    @Indexed
    private LocalDate date;

    @Field("type")
    private AggregateType type;

    // RIDE_SUMMARY fields:
    @Field("total_trips")
    private long totalTrips;

    @Field("completed_trips")
    private long completedTrips;

    @Field("cancelled_trips")
    private long cancelledTrips;

    @Field("failed_match_trips")
    private long failedMatchTrips;

    @Field("total_distance_km")
    private double totalDistanceKm;

    @Field("avg_trip_duration_min")
    private double avgTripDurationMin;

    @Field("avg_rating")
    private double avgRating;

    // PAYMENT_SUMMARY fields:
    @Field("gross_revenue_vnd")
    private Long grossRevenueVnd;

    @Field("platform_revenue_vnd")
    private Long platformRevenueVnd;

    @Field("refunds_vnd")
    private Long refundsVnd;

    @Field("net_revenue_vnd")
    private Long netRevenueVnd; // gross - refunds - platform fee

    @Field("gateway_breakdown")
    private Map<String, Long> gatewayBreakdown; // gateway name → revenue VND

    @Field("computed_at")
    private Instant computedAt;
}
```

**Definition of Done**:
- [ ] `aggregateId` format: `{tenantId}:{date}:{type}` — unique compound key
- [ ] Upsertable by `aggregateId` (idempotent nightly CRON)
- [ ] Both ride and payment fields on same document (type-specific fields nullable)

---

### TASK-ABI-002: ReportJob Domain Model

**Parent WP Task**: WP-008-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/models/ReportJob.java`
- `src/main/java/com/vnpt/avplatform/abi/models/ReportFormat.java`
- `src/main/java/com/vnpt/avplatform/abi/models/ReportStatus.java`

**Specification**:
```java
// ReportFormat.java
public enum ReportFormat { PDF, CSV }

// ReportStatus.java
public enum ReportStatus { PENDING, GENERATING, COMPLETED, FAILED }

// ReportJob.java
@Document(collection = "report_jobs")
public class ReportJob {
    @Id private String id;

    @Field("job_id")
    @Indexed(unique = true)
    private String jobId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("report_type")
    private String reportType; // "DAILY_SUMMARY", "TRIP_DETAIL", "REVENUE"

    @Field("format")
    private ReportFormat format;

    @Field("date_from")
    private LocalDate dateFrom;

    @Field("date_to")
    private LocalDate dateTo;

    @Field("status")
    private ReportStatus status = ReportStatus.PENDING;

    @Field("file_key")
    private String fileKey; // MinIO object key

    @Field("presigned_url")
    private String presignedUrl; // temporary download URL (expires)

    @Field("presigned_url_expires_at")
    private Instant presignedUrlExpiresAt;

    @Field("error_message")
    private String errorMessage;

    @Field("requested_by")
    private String requestedBy; // userId

    @Field("created_at")
    private Instant createdAt = Instant.now();

    @Field("completed_at")
    private Instant completedAt;
}
```

**Presigned URL TTL**: 
- Standard reports: 1 hour (`presignedUrlExpiresAt = now + 1h`)
- Scheduled exports: 7 days (`presignedUrlExpiresAt = now + 7d`)

**Definition of Done**:
- [ ] `presignedUrlExpiresAt` stored for expiry check on download
- [ ] `fileKey` format: `reports/{tenantId}/{reportType}/{jobId}.{format.toLowerCase()}`
- [ ] `status` progresses: PENDING → GENERATING → COMPLETED/FAILED

---

## Task Group 2: Repository Layer

### TASK-ABI-003: DailyAggregateRepository

**Parent WP Task**: WP-008-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/repositories/DailyAggregateRepository.java`
- `src/main/java/com/vnpt/avplatform/abi/repositories/impl/DailyAggregateRepositoryImpl.java`

**Specification**:
```java
public interface DailyAggregateRepository {
    DailyAggregate upsert(DailyAggregate aggregate); // by aggregateId
    List<DailyAggregate> findByTenantIdAndDateRange(String tenantId, LocalDate from, LocalDate to, AggregateType type);
    Optional<DailyAggregate> findByAggregateId(String aggregateId);
}
// upsert: mongoTemplate.upsert(query by aggregateId, update with $set all fields, DailyAggregate.class)
// findByTenantIdAndDateRange: tenant_id = tenantId AND type = type AND date >= from AND date <= to
```

**Definition of Done**:
- [ ] `upsert` is idempotent (safe to run multiple times for same date)
- [ ] Date range query uses `$gte` and `$lte` on `date` field
- [ ] All queries include `tenant_id` filter (BL-001)

---

### TASK-ABI-004: ReportJobRepository

**Parent WP Task**: WP-008-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/repositories/ReportJobRepository.java`
- `src/main/java/com/vnpt/avplatform/abi/repositories/impl/ReportJobRepositoryImpl.java`

**Specification**:
```java
public interface ReportJobRepository {
    ReportJob insert(ReportJob job); // INSERT for new jobs
    Optional<ReportJob> findByJobId(String jobId);
    List<ReportJob> findByTenantId(String tenantId, int page, int size);
    ReportJob updateStatus(String jobId, ReportStatus status, String fileKey,
        String presignedUrl, Instant presignedUrlExpiresAt, String errorMessage);
}
// updateStatus: $set all output fields in one atomic update
```

**Definition of Done**:
- [ ] `insert()` NOT `save()` for new jobs
- [ ] `updateStatus` is only allowed modification (for job completion)
- [ ] tenant_id filter on all find operations (BL-001)

---

## Task Group 3: Security

### TASK-ABI-005: TenantContextFilter + TenantContextHolder

**Parent WP Task**: WP-008-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/abi/security/TenantContextHolder.java`

**Specification**: Same pattern as TMS (TASK-TMS-008/009).
```java
// OncePerRequestFilter, @Order(1)
// Extract from JWT "tenant_id" OR "X-Tenant-ID" header
// finally: TenantContextHolder.clear()
```

**Definition of Done**:
- [ ] `clear()` in `finally` block
- [ ] `@Order(1)` priority

---

## Task Group 4: ETL Transformers

### TASK-ABI-006: RideEventETLTransformer

**Parent WP Task**: WP-008-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/etl/RideEventETLTransformer.java`
- `src/main/java/com/vnpt/avplatform/abi/etl/RideAnalyticsDocument.java`

**Specification**:
```java
// RideAnalyticsDocument.java — Elasticsearch document
public class RideAnalyticsDocument {
    private String tripId;
    private String tenantId;          // MANDATORY for BL-010 tenant isolation
    private String riderId;
    private String vehicleId;
    private String status;
    private String vehicleType;
    private Double pickupLat;
    private Double pickupLng;
    private Double dropoffLat;
    private Double dropoffLng;
    // geo_point for ES geo queries:
    private GeoPoint pickupLocation;  // { lat, lon }
    private GeoPoint dropoffLocation;
    private Double distanceKm;
    private Integer durationMin;
    private Long fareVnd;
    private Double rating;
    private Instant requestedAt;
    private Instant completedAt;
    private LocalDate date;           // for date-based aggregations
    private String month;             // "YYYY-MM" for monthly rollup
}

// RideEventETLTransformer.java
@Component
public class RideEventETLTransformer {
    public RideAnalyticsDocument transform(RideEvent event) {
        // Only transform ride.completed events (primary analytics event)
        if (!"ride.completed".equals(event.getEventType())) return null;

        RideAnalyticsDocument doc = new RideAnalyticsDocument();
        doc.setTripId(event.getTripId());
        doc.setTenantId(event.getTenantId()); // MUST be set — BL-010
        doc.setPickupLocation(new GeoPoint(event.getPickupLat(), event.getPickupLng()));
        doc.setDropoffLocation(new GeoPoint(event.getDropoffLat(), event.getDropoffLng()));
        doc.setDate(event.getCompletedAt().atZone(ZoneId.of("UTC")).toLocalDate());
        doc.setMonth(YearMonth.from(doc.getDate()).toString());
        // ... map all other fields
        return doc;
    }
}
```

**Definition of Done**:
- [ ] `tenantId` ALWAYS set in `RideAnalyticsDocument` (BL-010)
- [ ] `pickupLocation` and `dropoffLocation` as `GeoPoint` (for ES geo_distance queries)
- [ ] Only `ride.completed` events transformed (others return null)
- [ ] `date` computed from `completedAt` in UTC timezone

---

### TASK-ABI-007: PaymentEventETLTransformer

**Parent WP Task**: WP-008-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/etl/PaymentEventETLTransformer.java`
- `src/main/java/com/vnpt/avplatform/abi/etl/PaymentAnalyticsDocument.java`

**Specification**:
```java
// PaymentAnalyticsDocument.java
public class PaymentAnalyticsDocument {
    private String transactionId;
    private String tenantId;      // MANDATORY — BL-010
    private String tripId;
    private String riderId;
    private String paymentMethod; // STRIPE, VNPAY, MOMO, etc.
    private String status;        // CAPTURED, REFUNDED
    private Long amountVnd;
    private Long platformRevenueVnd;
    private Instant timestamp;
    private LocalDate date;
    private String month;
}

// Transformer:
// Transform: payment.captured AND payment.refunded events only
// payment.failed: NOT indexed in ES (only in MongoDB for billing audit)
```

**Definition of Done**:
- [ ] `tenantId` ALWAYS set (BL-010)
- [ ] `payment.failed` events NOT indexed (billing handles those)
- [ ] `platformRevenueVnd` from event metadata (published by FPE)

---

### TASK-ABI-008: BillingEventETLTransformer

**Parent WP Task**: WP-008-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/etl/BillingEventETLTransformer.java`
- `src/main/java/com/vnpt/avplatform/abi/etl/BillingAnalyticsDocument.java`

**Specification**:
```java
// BillingAnalyticsDocument.java
public class BillingAnalyticsDocument {
    private String invoiceId;
    private String tenantId;      // MANDATORY — BL-010
    private String subscriptionId;
    private String planTier;
    private Long totalVnd;
    private Long taxVnd;
    private Long netVnd;
    private String status;        // PAID, FAILED
    private String billingCountry;
    private LocalDate billingDate;
    private String month;
}
// Transform: billing.invoice_generated AND billing.payment_success/failure events
```

**Definition of Done**:
- [ ] `tenantId` ALWAYS set (BL-010)
- [ ] Only invoice and payment status events transformed

---

## Task Group 5: Core Services

### TASK-ABI-009: ElasticsearchIndexingService (Dual-Write)

**Parent WP Task**: WP-008-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/ElasticsearchIndexingService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/ElasticsearchIndexingServiceImpl.java`

**Specification**:
```java
public interface ElasticsearchIndexingService {
    void indexRideDocument(RideAnalyticsDocument doc);
    void indexPaymentDocument(PaymentAnalyticsDocument doc);
    SearchResult<RideAnalyticsDocument> searchRides(RideSearchQuery query);
    AggregationResult aggregateRides(String tenantId, LocalDate from, LocalDate to);
}

// Index names:
// "ride-analytics-{YYYY.MM}" — monthly index rotation (ILM policy)
// "payment-analytics-{YYYY.MM}"
// "billing-analytics-{YYYY.MM}"

// ILM policy: ride-analytics:
//   hot: 7 days (primary shards, R/W)
//   warm: 30 days (replica shrink, read-only)
//   cold: 365 days (reduced resource, read-only)

// indexRideDocument():
//   String indexName = "ride-analytics-" + doc.getMonth().replace("-", ".");
//   IndexRequest request = new IndexRequest(indexName)
//       .id(doc.getTripId())
//       .source(objectMapper.writeValueAsBytes(doc), XContentType.JSON);
//   client.index(request, RequestOptions.DEFAULT);

// searchRides() — BL-010 MANDATORY tenant isolation:
//   SearchRequest request = new SearchRequest("ride-analytics-*");
//   BoolQueryBuilder query = QueryBuilders.boolQuery()
//       .must(QueryBuilders.termQuery("tenant_id", tenantId)); // BL-010 MANDATORY
//   if (dateFrom != null) query.filter(QueryBuilders.rangeQuery("date").gte(dateFrom));
//   // ... add other filters

// DUAL-WRITE: ES + InfluxDB (called from ETLKafkaConsumer after ES index)
```

**Definition of Done**:
- [ ] EVERY ES query includes `must: { term: { tenant_id } }` (BL-010)
- [ ] Monthly index rotation: `ride-analytics-{YYYY.MM}` (e.g., `ride-analytics-2025.01`)
- [ ] ILM policy configured: hot 7d / warm 30d / cold 1yr
- [ ] `ElasticsearchIndexingServiceTest`: verify tenant_id filter present in ALL queries

---

### TASK-ABI-010: InfluxDBTimeSeriesService

**Parent WP Task**: WP-008-T05  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/InfluxDBTimeSeriesService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/InfluxDBTimeSeriesServiceImpl.java`

**Specification**:
```java
public interface InfluxDBTimeSeriesService {
    void writeRideMetric(String tenantId, Instant time, String status, double distanceKm, Long fareVnd);
    void writePaymentMetric(String tenantId, Instant time, String gateway, Long amountVnd);
    List<TimeSeriesPoint> queryRideTrend(String tenantId, Instant from, Instant to, String granularity);
}

// InfluxDB measurements:
// "ride_metrics": tags=[tenant_id, status, vehicle_type], fields=[count, distance_km, fare_vnd, duration_min]
// "payment_metrics": tags=[tenant_id, gateway, status], fields=[amount_vnd, count]

// writeRideMetric() — async Reactor:
// Point point = Point.measurement("ride_metrics")
//     .addTag("tenant_id", tenantId) // MANDATORY for tenant isolation
//     .addTag("status", status)
//     .addField("distance_km", distanceKm)
//     .addField("fare_vnd", fareVnd)
//     .addField("count", 1L)
//     .time(time, WritePrecision.S);
// Mono.fromCallable(() -> writeApi.writePoint(point))
//     .subscribeOn(Schedulers.boundedElastic())
//     .doOnError(e -> log.warn("InfluxDB write error: {}", e.getMessage()))
//     .onErrorComplete()
//     .subscribe();

// queryRideTrend() — Flux query:
// String flux = "from(bucket: \"av-platform\")" +
//     " |> range(start: " + from + ", stop: " + to + ")" +
//     " |> filter(fn: (r) => r[\"_measurement\"] == \"ride_metrics\")" +
//     " |> filter(fn: (r) => r[\"tenant_id\"] == \"" + tenantId + "\")" + // BL-010
//     " |> aggregateWindow(every: " + granularity + ", fn: sum)";
```

**Definition of Done**:
- [ ] `tenant_id` tag on EVERY InfluxDB point write (BL-010)
- [ ] Write is async non-blocking (Reactor pipeline)
- [ ] InfluxDB write failure logged WARN, NOT rethrown
- [ ] Flux query always includes `tenant_id` filter

---

### TASK-ABI-011: DailyAggregationService (End-of-Day CRON)

**Parent WP Task**: WP-008-T06  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/DailyAggregationService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/DailyAggregationServiceImpl.java`

**Specification**:
```java
public interface DailyAggregationService {
    void aggregateAllTenants(); // @Scheduled CRON — 23:55 UTC daily
    DailyAggregate aggregateForTenant(String tenantId, LocalDate date);
}

// @Scheduled(cron = "0 55 23 * * *", zone = "UTC") — 23:55 UTC daily

// aggregateForTenant():
//   Queries Elasticsearch for today's data (tenant-scoped):
//   BoolQueryBuilder query = boolQuery()
//       .must(termQuery("tenant_id", tenantId))  // BL-010
//       .filter(rangeQuery("date").gte(date).lte(date));
//
//   // ES aggregation query:
//   SearchSourceBuilder source = new SearchSourceBuilder()
//       .query(query)
//       .aggregation(AggregationBuilders.count("total_trips").field("trip_id"))
//       .aggregation(AggregationBuilders.filter("completed_trips",
//           termQuery("status", "COMPLETED")))
//       .aggregation(AggregationBuilders.sum("total_distance").field("distance_km"))
//       .aggregation(AggregationBuilders.avg("avg_rating").field("rating"))
//       .size(0); // don't return documents, only aggregations
//
//   DailyAggregate aggregate = mapAggregations(response);
//   aggregate.setAggregateId(tenantId + ":" + date + ":RIDE_SUMMARY");
//   dailyAggregateRepository.upsert(aggregate);
//   return aggregate;
```

**Definition of Done**:
- [ ] CRON: `"0 55 23 * * *"` at UTC 23:55 daily
- [ ] All ES queries include `tenant_id` filter (BL-010)
- [ ] Result upserted to MongoDB `daily_aggregates` (idempotent)
- [ ] Processes all tenants sequentially (not parallel — avoid ES overload)

---

### TASK-ABI-012: KPIComputationService (Threshold Classification)

**Parent WP Task**: WP-008-T07  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/KPIComputationService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/KPIComputationServiceImpl.java`

**Specification**:
```java
public interface KPIComputationService {
    KPIReport computeKPIs(String tenantId, LocalDate from, LocalDate to);
}

// KPIReport fields:
// completionRate: completed / total trips × 100 → GREEN (>85%), YELLOW (70-85%), RED (<70%)
// avgRating: → GREEN (>4.5), YELLOW (3.5-4.5), RED (<3.5)
// cancellationRate: cancelled / total × 100 → GREEN (<10%), YELLOW (10-20%), RED (>20%)
// matchSuccessRate: matched / (matched + failed_match) × 100 → GREEN (>90%), YELLOW (75-90%), RED (<75%)
// revenueGrowthPct: compare to previous period → GREEN (>5%), YELLOW (0-5%), RED (<0%, decline)

// computeKPIs():
//   1. Fetch DailyAggregate records for period (from MongoDB)
//   2. Sum/average across days
//   3. Classify each KPI: GREEN/YELLOW/RED based on thresholds above
//   4. Return KPIReport { tenantId, period, kpis: [...], generatedAt }

// Each KPI:
// { name, value, unit, classification: "GREEN"|"YELLOW"|"RED", threshold }
```

**Definition of Done**:
- [ ] Classification thresholds are constants (not configurable per tenant in v1.0)
- [ ] `revenueGrowthPct` computes by fetching previous equivalent period
- [ ] All 5 KPIs always present in response (nullable value if no data)
- [ ] `KPIComputationServiceTest`: 5 test cases (one per KPI classification boundary)

---

### TASK-ABI-013: HeatmapService (geotile_grid Aggregation)

**Parent WP Task**: WP-008-T08  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/HeatmapService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/HeatmapServiceImpl.java`

**Specification**:
```java
public interface HeatmapService {
    HeatmapResponse getPickupHeatmap(String tenantId, LocalDate from, LocalDate to, int zoomLevel);
    HeatmapResponse getDropoffHeatmap(String tenantId, LocalDate from, LocalDate to, int zoomLevel);
}

// ES geotile_grid aggregation for heatmap:
// SearchSourceBuilder source = new SearchSourceBuilder()
//     .query(boolQuery()
//         .must(termQuery("tenant_id", tenantId))  // BL-010 MANDATORY
//         .filter(rangeQuery("date").gte(from).lte(to))
//     )
//     .aggregation(AggregationBuilders.geotileGrid("pickup_tiles")
//         .field("pickup_location")
//         .precision(zoomLevel) // zoom 5-12 (city-level to street-level)
//         .size(10000)          // max tiles returned
//     )
//     .size(0);

// HeatmapResponse: { tiles: [{ tile_id, lat, lng, count }] }
// tile_id: "{zoom}/{x}/{y}" Mercator tile format
// lat/lng: center of tile computed from tile coordinates

// Zoom level validation: min 5 (country), max 12 (street) — reject outside range
```

**Definition of Done**:
- [ ] `tenant_id` filter MANDATORY in geotile_grid query (BL-010)
- [ ] Zoom level 5–12 (validated: HTTP 400 outside range)
- [ ] Returns max 10,000 tiles per request
- [ ] `HeatmapServiceTest`: verify tenant_id present in all ES queries

---

### TASK-ABI-014: ReportGenerationService (JasperReports + CSV)

**Parent WP Task**: WP-008-T09  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/ReportGenerationService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/ReportGenerationServiceImpl.java`

**Specification**:
```java
public interface ReportGenerationService {
    ReportJob generateReport(String tenantId, String reportType, ReportFormat format,
        LocalDate dateFrom, LocalDate dateTo, String requestedBy);
}

// generateReport() — async (returns ReportJob immediately, generates in background):
//   1. Insert ReportJob { status: PENDING }
//   2. CompletableFuture.runAsync(() -> generateAsync(jobId, ...), reportExecutor)
//   3. Return the pending ReportJob

// generateAsync() — runs in background thread pool:
//   1. Update status: GENERATING
//   2. Fetch data from MongoDB daily_aggregates
//   3. Generate file based on format:
//      PDF: JasperReports:
//           JasperReport jasperReport = JasperCompileManager.compileReport(template.jrxml);
//           JRBeanCollectionDataSource ds = new JRBeanCollectionDataSource(dataList);
//           JasperPrint print = JasperFillManager.fillReport(jasperReport, params, ds);
//           byte[] pdf = JasperExportManager.exportReportToPdf(print);
//      CSV: Apache Commons CSV:
//           StringWriter writer = new StringWriter();
//           CSVPrinter printer = new CSVPrinter(writer, CSVFormat.DEFAULT.withHeader(headers));
//           dataList.forEach(row -> printer.printRecord(row.values()));
//           byte[] csv = writer.toString().getBytes(StandardCharsets.UTF_8);
//   4. Upload to MinIO: minIOStorageService.upload(fileKey, fileBytes, contentType)
//   5. Generate presigned URL: minIOStorageService.generatePresignedUrl(fileKey, duration)
//   6. Update ReportJob { status: COMPLETED, fileKey, presignedUrl, presignedUrlExpiresAt }
//   7. On any error: Update ReportJob { status: FAILED, errorMessage }

// Report thread pool: @Bean ThreadPoolExecutor reportExecutor (10 threads, queue 100)
// JasperReports templates: stored in src/main/resources/reports/*.jrxml
```

**Definition of Done**:
- [ ] `generateReport` returns immediately (async generation)
- [ ] Thread pool: 10 threads for report generation
- [ ] JasperReports template path: `classpath:reports/{reportType}.jrxml`
- [ ] CSV uses Apache Commons CSV with proper header row
- [ ] On failure: `status=FAILED` with descriptive `errorMessage`

---

### TASK-ABI-015: MinIOStorageService (Presigned URLs)

**Parent WP Task**: WP-008-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/services/MinIOStorageService.java`
- `src/main/java/com/vnpt/avplatform/abi/services/impl/MinIOStorageServiceImpl.java`

**Specification**:
```java
public interface MinIOStorageService {
    String upload(String objectKey, byte[] content, String contentType);
    String generatePresignedUrl(String objectKey, Duration expiry);
    void delete(String objectKey);
}

// Library: io.minio:minio:8.5.x
// Config: spring.minio.endpoint, spring.minio.access-key, spring.minio.secret-key, spring.minio.bucket

// upload():
//   minioClient.putObject(PutObjectArgs.builder()
//       .bucket(bucketName)
//       .object(objectKey)
//       .stream(new ByteArrayInputStream(content), content.length, -1)
//       .contentType(contentType)
//       .build());
//   return objectKey;

// generatePresignedUrl():
//   return minioClient.getPresignedObjectUrl(GetPresignedObjectUrlArgs.builder()
//       .method(Method.GET)
//       .bucket(bucketName)
//       .object(objectKey)
//       .expiry((int) expiry.toSeconds(), TimeUnit.SECONDS)
//       .build());

// Standard expiry: Duration.ofHours(1)
// Scheduled export expiry: Duration.ofDays(7)
// Object key format: "reports/{tenantId}/{reportType}/{jobId}.pdf|csv"
```

**Definition of Done**:
- [ ] Bucket name from configuration (not hardcoded)
- [ ] Object key includes `tenantId` (cross-tenant access prevention)
- [ ] Presigned URL for GET only (not PUT/DELETE)
- [ ] MinIO credentials from environment variables

---

## Task Group 6: Kafka Consumer

### TASK-ABI-016: ETLKafkaConsumer (abi-etl Group)

**Parent WP Task**: WP-008-T11  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/events/ETLKafkaConsumer.java`

**Specification**:
```java
@Component
public class ETLKafkaConsumer {
    // Consumer group: abi-etl
    // Kafka config: max.poll.records=500, enable.auto.commit=false

    @KafkaListener(
        topics = {"ride-events", "payment-events", "billing-events"},
        groupId = "abi-etl",
        containerFactory = "abiKafkaListenerContainerFactory"
    )
    public void consumeEvents(List<ConsumerRecord<String, String>> records,
        Acknowledgment ack) {

        for (ConsumerRecord<String, String> record : records) {
            String topic = record.topic();
            try {
                if ("ride-events".equals(topic)) {
                    RideEvent event = objectMapper.readValue(record.value(), RideEvent.class);
                    RideAnalyticsDocument doc = rideEventETLTransformer.transform(event);
                    if (doc != null) {
                        // DUAL-WRITE: ES + InfluxDB
                        elasticsearchIndexingService.indexRideDocument(doc);
                        influxDBTimeSeriesService.writeRideMetric(doc.getTenantId(), ...);
                    }
                } else if ("payment-events".equals(topic)) {
                    PaymentEvent event = objectMapper.readValue(record.value(), PaymentEvent.class);
                    PaymentAnalyticsDocument doc = paymentEventETLTransformer.transform(event);
                    if (doc != null) {
                        elasticsearchIndexingService.indexPaymentDocument(doc);
                        influxDBTimeSeriesService.writePaymentMetric(...);
                    }
                }
                // billing-events handled similarly
            } catch (Exception e) {
                log.error("ETL processing failed for record: topic={}, offset={}", topic, record.offset(), e);
                // Don't rethrow — continue processing batch
            }
        }
        // Manual commit after batch processed:
        ack.acknowledge();
    }
}
// max.poll.records=500: process up to 500 records per poll
// enable.auto.commit=false: manual commit after dual-write
// On individual record failure: log error, continue batch (don't fail entire batch)
```

**Definition of Done**:
- [ ] Consumer group: `abi-etl`
- [ ] `max.poll.records=500`
- [ ] `enable.auto.commit=false` — manual offset commit with `Acknowledgment`
- [ ] DUAL-WRITE: ES AND InfluxDB for each record
- [ ] Individual record failure does NOT fail entire batch (log and continue)
- [ ] `ack.acknowledge()` called AFTER all records in batch processed

---

## Task Group 7: REST Controllers

### TASK-ABI-017: AnalyticsController (Query Endpoints)

**Parent WP Task**: WP-008-T12  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/controllers/AnalyticsController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/analytics")
@PreAuthorize("hasAnyRole('TENANT_ADMIN', 'ANALYST', 'PLATFORM_ADMIN')")
public class AnalyticsController {

    // GET /api/v1/analytics/kpis?date_from=2025-01-01&date_to=2025-01-31
    @GetMapping("/kpis")
    public KPIReport getKPIs(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        validateDateRange(dateFrom, dateTo, 90); // max 90 days
        return kpiComputationService.computeKPIs(tenantId, dateFrom, dateTo);
    }

    // GET /api/v1/analytics/heatmap/pickup?date_from=...&date_to=...&zoom=8
    @GetMapping("/heatmap/pickup")
    public HeatmapResponse getPickupHeatmap(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo,
        @RequestParam(defaultValue = "8") @Min(5) @Max(12) int zoom
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        return heatmapService.getPickupHeatmap(tenantId, dateFrom, dateTo, zoom);
    }

    // GET /api/v1/analytics/trends/rides?granularity=1d|1h|1w
    @GetMapping("/trends/rides")
    public List<TimeSeriesPoint> getRideTrends(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo,
        @RequestParam(defaultValue = "1d") String granularity
    ) {
        String tenantId = TenantContextHolder.requireTenantId();
        // granularity: "1h", "1d", "1w" (validated: only these 3)
        if (!List.of("1h", "1d", "1w").contains(granularity))
            throw new InvalidParameterException("granularity must be 1h, 1d, or 1w");
        return influxDBTimeSeriesService.queryRideTrend(tenantId, ...);
    }
}
// Date range validation: dateFrom must be before dateTo; max 90 days for KPIs, 30 days for heatmap
// All endpoints: tenant isolation via TenantContextHolder (no tenant_id param)
```

**Definition of Done**:
- [ ] All endpoints use `TenantContextHolder.requireTenantId()` (no tenant_id path param)
- [ ] Date range max 90 days for KPIs (HTTP 400 if exceeded)
- [ ] Zoom level 5–12 validated by `@Min(5) @Max(12)`
- [ ] `granularity` validated: only `1h`, `1d`, `1w` accepted

---

### TASK-ABI-018: ReportController (Generate + Download)

**Parent WP Task**: WP-008-T12  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/controllers/ReportController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/reports")
@PreAuthorize("hasAnyRole('TENANT_ADMIN', 'ANALYST')")
public class ReportController {

    // POST /api/v1/reports (request report generation)
    @PostMapping
    @ResponseStatus(HttpStatus.ACCEPTED) // 202 — async
    public ReportJobDTO requestReport(@Valid @RequestBody ReportRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        String requestedBy = getCurrentUserId(); // from JWT sub claim
        return reportGenerationService.generateReport(tenantId, request.getReportType(),
            request.getFormat(), request.getDateFrom(), request.getDateTo(), requestedBy);
    }

    // GET /api/v1/reports/{jobId} (check status + get download URL)
    @GetMapping("/{jobId}")
    public ReportJobDTO getReportStatus(@PathVariable String jobId) {
        String tenantId = TenantContextHolder.requireTenantId();
        ReportJob job = reportJobRepository.findByJobId(jobId)
            .orElseThrow(() -> new ReportNotFoundException(jobId));
        // Verify tenant ownership (BL-010):
        if (!job.getTenantId().equals(tenantId))
            throw new AccessDeniedException("Report does not belong to this tenant");
        // Check presigned URL expiry:
        if (job.getPresignedUrlExpiresAt() != null && Instant.now().isAfter(job.getPresignedUrlExpiresAt())) {
            // Regenerate presigned URL:
            String newUrl = minIOStorageService.generatePresignedUrl(job.getFileKey(), Duration.ofHours(1));
            reportJobRepository.updateStatus(jobId, COMPLETED, job.getFileKey(), newUrl, Instant.now().plus(1, HOURS), null);
        }
        return mapper.toDTO(job);
    }

    // GET /api/v1/reports (list jobs)
    @GetMapping
    public List<ReportJobDTO> listReports(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) { ... }
}
```

**Definition of Done**:
- [ ] POST returns HTTP 202 (async)
- [ ] GET checks tenant ownership (BL-010)
- [ ] Expired presigned URL automatically refreshed (1h extension)
- [ ] `ReportNotFoundException` → HTTP 404

---

## Task Group 8: Configuration

### TASK-ABI-020: MongoConfig + ElasticsearchConfig + InfluxDBConfig

**Parent WP Task**: WP-008-T02  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/config/MongoConfig.java`
- `src/main/java/com/vnpt/avplatform/abi/config/ElasticsearchConfig.java`
- `src/main/java/com/vnpt/avplatform/abi/config/InfluxDBConfig.java`

**Specification**:
```java
// MongoConfig indexes:
// daily_aggregates: aggregate_id (unique), tenant_id, date
// report_jobs: job_id (unique), tenant_id, created_at

// ElasticsearchConfig:
// @Bean RestHighLevelClient elasticsearchClient() {
//     return new RestHighLevelClient(
//         RestClient.builder(HttpHost.create(elasticsearchUrl))
//             .setHttpClientConfigCallback(httpClientBuilder ->
//                 httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider))
//     );
// }
// OR for ES 8.x: use ElasticsearchClient (new transport-based client)

// ILM policy registration at startup:
// @PostConstruct createILMPolicies() {
//     // ride-analytics ILM: hot 7d, warm 30d, cold 365d
//     // Index template: ride-analytics-* → apply ILM policy
// }

// InfluxDBConfig:
// @Bean InfluxDBClient influxDbClient() { ... } // same as BMS
```

**Definition of Done**:
- [ ] ILM policy created at startup for `ride-analytics-*`
- [ ] ES client supports both username/password and API key auth (configured via env)
- [ ] Unique index on `daily_aggregates.aggregate_id`

---

### TASK-ABI-021: MinIOConfig

**Parent WP Task**: WP-008-T10  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/abi/config/MinIOConfig.java`

**Specification**:
```java
@Configuration
public class MinIOConfig {
    @Bean
    public MinioClient minioClient(
        @Value("${spring.minio.endpoint}") String endpoint,
        @Value("${spring.minio.access-key}") String accessKey,
        @Value("${spring.minio.secret-key}") String secretKey
    ) {
        return MinioClient.builder()
            .endpoint(endpoint)
            .credentials(accessKey, secretKey)
            .build();
    }
    // Bucket creation at startup (if not exists):
    // @PostConstruct void ensureBucket() { minioClient.makeBucket(...) }
}
```

**Definition of Done**:
- [ ] Credentials from environment variables
- [ ] Bucket created at startup if not exists (`makeBucket` with `BucketExistsArgs`)

---

## Task Group 9: Tests

### TASK-ABI-022: Unit Tests — ETL Transformers

**Parent WP Task**: WP-008-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/abi/etl/RideEventETLTransformerTest.java`

**Test Cases**:
```
1. transform_rideCompleted: correct mapping of all fields
2. transform_rideRequested: returns null (not indexed)
3. transform_tenantId_alwaysPresent: BL-010 — tenant_id never null
4. transform_geoPoint_correctFormat: pickupLocation is GeoPoint { lat, lon }
5. transform_date_UTC: completedAt in "+07:00" still stored as UTC LocalDate
6. paymentTransform_captured: correct mapping
7. paymentTransform_failed_returnsNull: payment.failed not indexed
```

**Definition of Done**:
- [ ] Test 3: `assertNotNull(doc.getTenantId())` — BL-010 verified
- [ ] Test 5: timezone conversion verified explicitly

---

### TASK-ABI-023: Unit Tests — KPIComputationService + HeatmapService

**Parent WP Task**: WP-008-T13  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/abi/services/KPIComputationServiceTest.java`

**Test Cases**:
```
1. completionRate_green: 90% completed → GREEN
2. completionRate_yellow: 80% completed → YELLOW
3. completionRate_red: 65% completed → RED
4. avgRating_green: rating 4.7 → GREEN
5. avgRating_red: rating 3.2 → RED
6. heatmap_tenantIdFilterPresent: ES query always has tenant_id (BL-010)
7. heatmap_zoomOutOfRange: zoom 3 → HTTP 400
```

**Definition of Done**:
- [ ] Test 6: capture ES request, assert `must.term.tenant_id` present
- [ ] Test 7: `@Min(5)` constraint violations caught

---

### TASK-ABI-024: Unit Tests — ReportGenerationService

**Parent WP Task**: WP-008-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/abi/services/ReportGenerationServiceTest.java`

**Test Cases**:
```
1. generatePDF_success: status transitions PENDING→GENERATING→COMPLETED
2. generateCSV_success: CSV file uploaded to MinIO with correct key
3. generateReport_returns_immediately: async — job returned before file created
4. generateFailed_status_updated: exception → status=FAILED with errorMessage
5. presignedUrl_1hour_standard: standard report → 1h expiry
6. presignedUrl_7days_scheduled: scheduled export → 7d expiry
7. minioKey_includes_tenantId: objectKey format verified
```

**Definition of Done**:
- [ ] Test 3: verify job returned with `status=PENDING` before async completes
- [ ] Test 7: `reports/{tenantId}/{reportType}/{jobId}.pdf` format verified

---

### TASK-ABI-025: Integration Tests — Analytics API

**Parent WP Task**: WP-008-T13  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/abi/integration/AnalyticsControllerIT.java`

**Test Cases**:
```
1. GET /api/v1/analytics/kpis → 200 with KPI report
2. GET /api/v1/analytics/kpis (date range > 90 days) → 400
3. GET /api/v1/analytics/heatmap/pickup → 200 with tiles
4. GET /api/v1/analytics/heatmap/pickup (zoom=3) → 400
5. POST /api/v1/reports → 202 with jobId
6. GET /api/v1/reports/{jobId} → 200 with status
7. GET /api/v1/reports/{jobId} (wrong tenant) → 403
```

**Setup**: Testcontainers MongoDB + Elasticsearch + Kafka. MinIO Testcontainer.  
**Definition of Done**:
- [ ] Test 7: cross-tenant access returns HTTP 403 (BL-010)
- [ ] Elasticsearch seeded with test data for tenant
- [ ] MinIO Testcontainer configured for report upload test

---

*DETAIL_PLAN_ABI v1.0.0 — ABI Analytics & Business Intelligence | VNPT AV Platform Services Provider Group*
