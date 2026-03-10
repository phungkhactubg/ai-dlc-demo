# NATS Subject Patterns — VNPT AV Platform
## WP-001 T03

NATS is used for **real-time, low-latency** telemetry that does not require
durable persistence. Durable domain events are published to Kafka; NATS handles
ephemeral pub/sub and live dashboards.

---

## Subject Naming Convention

```
<service>.<tenant_id>.<entity_type>.<entity_id>.<event_type>
```

All subjects are **namespaced by `tenant_id`** to ensure strict multi-tenant isolation.

---

## Subject Catalogue

### RHS — Ride Hailing Service

| Subject Pattern | Description | Publisher | Subscriber(s) |
|---|---|---|---|
| `rhs.{tenant_id}.trips.{trip_id}.state` | Trip FSM state transitions (REQUESTED→ACCEPTED→STARTED→COMPLETED) | RHS | FPE, NCS, ABI |
| `rhs.{tenant_id}.trips.{trip_id}.eta` | ETA updates (published every 30 s while trip is active) | RHS | Mobile Gateway, NCS |
| `rhs.{tenant_id}.vehicles.{vehicle_id}.location` | Raw GPS position updates (lat/lng/heading/speed) at ~1 Hz | Vehicle SDK | RHS, ABI |

### FPE — Fare & Pricing Engine

| Subject Pattern | Description | Publisher | Subscriber(s) |
|---|---|---|---|
| `fpe.{tenant_id}.surge.{grid_cell_id}` | Surge multiplier update per geohash cell | FPE | RHS, MKP |
| `fpe.{tenant_id}.fare.{trip_id}.estimate` | Real-time fare estimate as trip progresses | FPE | Mobile Gateway |

### PAY — Payment Service

| Subject Pattern | Description | Publisher | Subscriber(s) |
|---|---|---|---|
| `pay.{tenant_id}.transactions.{tx_id}.status` | Payment status change (PENDING→CAPTURED/FAILED) | PAY | NCS, BMS |

### NCS — Notification & Communication Service

| Subject Pattern | Description | Publisher | Subscriber(s) |
|---|---|---|---|
| `ncs.{tenant_id}.push.{user_id}` | Push notification delivery status | NCS | Analytics |

---

## JetStream Streams (durable)

For consumers that need at-least-once delivery guarantees, use JetStream streams:

| Stream Name | Subjects | Retention | Max Age |
|---|---|---|---|
| `VEHICLE_TELEMETRY` | `rhs.*.vehicles.*.location` | Limits | 1 hour |
| `TRIP_STATES` | `rhs.*.trips.*.state` | WorkQueue | 24 hours |

---

## Security — Subject ACLs (production)

Each service account is granted publish/subscribe permissions scoped to its subjects:

```
# RHS service account
publish:   ["rhs.>", "fpe.*.fare.*.estimate"]
subscribe: ["rhs.>"]

# FPE service account
publish:   ["fpe.>"]
subscribe: ["rhs.*.trips.*.state", "rhs.*.vehicles.*.location"]
```

---

## Local Development

```bash
# Subscribe to all trip state changes for tenant t001
nats sub "rhs.t001.trips.*.state"

# Publish a test location update
nats pub "rhs.t001.vehicles.v42.location" \
  '{"lat":21.0285,"lng":105.8542,"heading":45,"speed":30}'
```
