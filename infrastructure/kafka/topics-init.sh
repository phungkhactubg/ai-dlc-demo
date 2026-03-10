#!/usr/bin/env bash
# =============================================================================
# VNPT AV Platform — Kafka Topics Initialisation
# WP-001 T02
#
# Creates all required platform topics with correct partition counts and
# replication factor. Run once after the 3-broker cluster is healthy.
# =============================================================================
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-kafka1:29092,kafka2:29093,kafka3:29094}"
RF=3

echo "[kafka-init] Waiting for Kafka brokers to be ready..."
cub kafka-ready -b "${BOOTSTRAP}" 3 60
echo "[kafka-init] Brokers ready."

# Helper: create topic only if it doesn't already exist
create_topic() {
  local name="$1"
  local partitions="$2"
  local rf="$3"

  if kafka-topics --bootstrap-server "${BOOTSTRAP}" --list | grep -qx "${name}"; then
    echo "[kafka-init] Topic '${name}' already exists — skipping."
  else
    kafka-topics \
      --bootstrap-server "${BOOTSTRAP}" \
      --create \
      --topic "${name}" \
      --partitions "${partitions}" \
      --replication-factor "${rf}" \
      --config min.insync.replicas=2 \
      --config retention.ms=604800000
    echo "[kafka-init] Created topic '${name}' (partitions=${partitions}, RF=${rf})."
  fi
}

# ── Core event topics ──────────────────────────────────────────────────────
# 24 partitions: ride-events & payment-events are highest-throughput topics
create_topic "ride-events"         24 ${RF}
create_topic "payment-events"      24 ${RF}

# 12 partitions: fare, billing, metering
create_topic "fare-events"         12 ${RF}
create_topic "billing-events"      12 ${RF}
create_topic "metering-events"     12 ${RF}

# 6 partitions: lower-throughput administrative / notification topics
create_topic "tenant-events"        6 ${RF}
create_topic "notification-dlq"     6 ${RF}

echo ""
echo "[kafka-init] All topics created successfully."
kafka-topics --bootstrap-server "${BOOTSTRAP}" --list
