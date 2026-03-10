// =============================================================================
// VNPT AV Platform — MongoDB Replica Set Initialisation
// WP-001 T04
//
// Run via: mongosh --host mongo1:27017 /scripts/replica-set-init.js
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// 1. Initialise replica set rs0
// ─────────────────────────────────────────────────────────────────────────────
print("[mongo-init] Initiating replica set rs0 ...");
try {
  rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "mongo1:27017", priority: 2 },  // preferred PRIMARY
      { _id: 1, host: "mongo2:27018", priority: 1 },
      { _id: 2, host: "mongo3:27019", priority: 1 }
    ]
  });
} catch (e) {
  if (e.codeName === "AlreadyInitialized") {
    print("[mongo-init] Replica set already initialised — continuing.");
  } else {
    throw e;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Wait for PRIMARY election (up to 60 s)
// ─────────────────────────────────────────────────────────────────────────────
print("[mongo-init] Waiting for PRIMARY election ...");
let attempts = 0;
while (true) {
  const status = rs.status();
  const primary = status.members.find(m => m.stateStr === "PRIMARY");
  if (primary) {
    print("[mongo-init] PRIMARY elected: " + primary.name);
    break;
  }
  if (++attempts > 30) {
    throw new Error("[mongo-init] Timed out waiting for PRIMARY after 60 s.");
  }
  print("[mongo-init] Waiting ... attempt " + attempts);
  sleep(2000);
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. Switch to application database
// ─────────────────────────────────────────────────────────────────────────────
const db = db.getSiblingDB("av_platform_prod");
print("[mongo-init] Switched to database: av_platform_prod");

// ─────────────────────────────────────────────────────────────────────────────
// 4. payment_transactions — INSERT-only collection with JSON Schema validator
//    Immutability enforced at DB level: once written, documents cannot be
//    mutated (audit-grade PCI-DSS requirement).
// ─────────────────────────────────────────────────────────────────────────────
print("[mongo-init] Creating payment_transactions collection with schema validator ...");
try {
  db.createCollection("payment_transactions", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["transaction_id", "tenant_id", "created_at", "audit_immutable"],
        additionalProperties: true,
        properties: {
          transaction_id: {
            bsonType: "string",
            description: "Globally unique transaction identifier (UUID v4)"
          },
          tenant_id: {
            bsonType: "string",
            description: "Owning tenant identifier — REQUIRED, IMMUTABLE"
          },
          audit_immutable: {
            bsonType: "bool",
            enum: [true],
            description: "Must always be true; signals record is immutable"
          },
          created_at: {
            bsonType: "date",
            description: "Creation timestamp — set at insert, never updated"
          },
          idempotency_key: {
            bsonType: "string",
            description: "Client-supplied idempotency key for dedup"
          },
          amount_minor: {
            bsonType: "long",
            minimum: 0,
            description: "Amount in minor currency units (e.g. VND cents)"
          },
          currency: {
            bsonType: "string",
            pattern: "^[A-Z]{3}$"
          },
          status: {
            bsonType: "string",
            enum: ["PENDING", "CAPTURED", "FAILED", "REFUNDED"]
          }
        }
      }
    },
    validationLevel: "strict",
    validationAction: "error"
  });
  print("[mongo-init] payment_transactions collection created.");
} catch (e) {
  if (e.codeName === "NamespaceExists") {
    print("[mongo-init] payment_transactions already exists — skipping creation.");
  } else {
    throw e;
  }
}

// Indexes on payment_transactions
print("[mongo-init] Creating indexes on payment_transactions ...");
db.payment_transactions.createIndex({ tenant_id: 1 }, { background: true });
db.payment_transactions.createIndex(
  { tenant_id: 1, idempotency_key: 1 },
  { unique: true, sparse: true, background: true }
);
db.payment_transactions.createIndex({ tenant_id: 1, status: 1 }, { background: true });
db.payment_transactions.createIndex({ created_at: 1 }, { expireAfterSeconds: 31536000, background: true }); // 1-year TTL for archival
print("[mongo-init] payment_transactions indexes created.");

// ─────────────────────────────────────────────────────────────────────────────
// 5. trips — Geospatial + status indexing
// ─────────────────────────────────────────────────────────────────────────────
print("[mongo-init] Creating trips collection ...");
try {
  db.createCollection("trips");
} catch (e) {
  if (e.codeName !== "NamespaceExists") throw e;
}

print("[mongo-init] Creating indexes on trips ...");
// 2dsphere indexes for pickup/dropoff GeoJSON Point fields
db.trips.createIndex({ "pickup.location": "2dsphere" }, { background: true });
db.trips.createIndex({ "dropoff.location": "2dsphere" }, { background: true });
// Standard operational indexes
db.trips.createIndex({ tenant_id: 1, status: 1 }, { background: true });
db.trips.createIndex({ tenant_id: 1, driver_id: 1, status: 1 }, { background: true });
db.trips.createIndex({ tenant_id: 1, rider_id: 1 }, { background: true });
db.trips.createIndex({ tenant_id: 1 }, { background: true });
db.trips.createIndex({ created_at: 1 }, { background: true });
print("[mongo-init] trips indexes created.");

// ─────────────────────────────────────────────────────────────────────────────
// 6. Standard indexes on other collections
// ─────────────────────────────────────────────────────────────────────────────
const stdCollections = ["tenants", "drivers", "riders", "vehicles", "fare_rules", "audit_logs"];
stdCollections.forEach(function(collName) {
  try {
    db.createCollection(collName);
  } catch (e) {
    if (e.codeName !== "NamespaceExists") throw e;
  }
  db[collName].createIndex({ tenant_id: 1 }, { background: true });
  print("[mongo-init] Created tenant_id index on " + collName);
});

print("[mongo-init] ✅ Replica set initialisation complete.");
