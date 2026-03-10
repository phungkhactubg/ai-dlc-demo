# Redis Keyspace Conventions — VNPT AV Platform
## WP-001 T05

All Redis keys are namespaced to prevent cross-tenant collisions. Every key
begins with a **logical category** followed by **tenant isolation** identifiers.

---

## Keyspace Catalogue

| Key Pattern | TTL | Owner Service | Description |
|---|---|---|---|
| `idempotency:{service}:{tenantId}:{operationId}` | **86400 s** (24 h) | All services | Stores operation result; prevents duplicate processing of the same client request |
| `quota:{tenantId}:{resourceType}:{YYYY-MM}` | Until end of billing period | BMS | Tracks monthly resource consumption per tenant per resource type |
| `session:{tenantId}:{userId}` | **3600 s** (1 h) | TMS / Auth | User session data; refresh on activity |
| `fare:estimate:{tenantId}:{pickupHash}:{dropoffHash}:{vehicleType}` | **60 s** | FPE | Cached fare estimate (hash = geohash of coordinates) |
| `surge:{tenantId}:{gridCellId}` | **60 s** | FPE | Surge multiplier for a geohash grid cell |
| `tenant:context:{tenantId}` | **300 s** | TMS | Cached tenant configuration & feature flags |
| `rate-limit:{tenantId}:{userId}:{endpoint}:{window}` | **1 s** (sliding) | Kong / Gateway | API rate-limiting counter |
| `lock:trip:{tenantId}:{tripId}` | **30 s** | RHS | Distributed lock for trip state machine transitions |
| `lock:payment:{tenantId}:{transactionId}` | **60 s** | PAY | Distributed lock for payment processing |

---

## Key Construction Guidelines

1. **Always include `tenantId`** as the second segment (after the category).
2. Use **lowercase with colons** as separators: `category:tenantId:...`.
3. Avoid very long keys — hash large identifiers with geohash or SHA-256 prefix.
4. Set TTL **at write time** — never leave keys without expiry except for
   persistent config (e.g. `tenant:context`).

---

## Idempotency Pattern

```java
String key = "idempotency:" + serviceId + ":" + tenantId + ":" + operationId;
Boolean exists = redisTemplate.hasKey(key);
if (Boolean.TRUE.equals(exists)) {
    return cachedResult(key);
}
// ... execute operation ...
redisTemplate.opsForValue().set(key, result, 86400, TimeUnit.SECONDS);
```

---

## Production Cluster

- **6 nodes**: 3 masters + 3 replicas (deployed via `redis-cluster` Helm chart)
- **Slot assignment**: automatic via `redis-cli --cluster create`
- **Connection**: use Lettuce cluster client (`spring.data.redis.cluster.nodes`)
- **Sharding**: Redis Cluster handles key distribution across slots automatically;
  use hash tags `{tenantId}` in multi-key operations to ensure co-location.

```yaml
# Production cluster config (replace single-node config)
spring:
  data:
    redis:
      cluster:
        nodes:
          - redis-0.redis-headless:6379
          - redis-1.redis-headless:6379
          - redis-2.redis-headless:6379
        max-redirects: 3
```
