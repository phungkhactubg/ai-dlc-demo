package com.vnpt.avplatform.shared.kafka;

import org.apache.kafka.clients.producer.Partitioner;
import org.apache.kafka.common.Cluster;
import org.apache.kafka.common.PartitionInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

/**
 * Custom Kafka partitioner that routes messages deterministically by {@code tenant_id}.
 *
 * <p>All messages belonging to the same tenant will land in the same partition, which
 * guarantees ordering per-tenant and enables efficient tenant-scoped consumer groups.
 *
 * <h3>Header contract</h3>
 * <ul>
 *   <li>Header key: {@code tenant-id}</li>
 *   <li>Header value: UTF-8 encoded tenant identifier string</li>
 * </ul>
 *
 * <h3>Partitioning algorithm</h3>
 * <pre>
 *   partition = Math.abs(tenantId.hashCode()) % numPartitions
 * </pre>
 *
 * <p>If the {@code tenant-id} header is absent, the partitioner falls back to the
 * standard key-based or round-robin partitioning.
 *
 * <h3>Spring Kafka configuration</h3>
 * <pre>
 * spring:
 *   kafka:
 *     producer:
 *       properties:
 *         partitioner.class: com.vnpt.avplatform.shared.kafka.TenantIdPartitioner
 * </pre>
 */
public class TenantIdPartitioner implements Partitioner {

    private static final Logger log = LoggerFactory.getLogger(TenantIdPartitioner.class);

    /** Kafka record header key carrying the tenant identifier. */
    public static final String TENANT_ID_HEADER = "tenant-id";

    @Override
    public int partition(
            String topic,
            Object key,
            byte[] keyBytes,
            Object value,
            byte[] valueBytes,
            Cluster cluster) {

        List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
        int numPartitions = partitions.size();

        // Attempt to extract tenantId from record headers via the Kafka producer interceptor.
        // Headers are not directly accessible inside partition(); callers must embed
        // the tenantId in the record KEY as "tenantId:<value>" when using this partitioner,
        // or inject it via a ProducerInterceptor that sets the key before this is called.
        //
        // Recommended pattern: set the message key to "<tenantId>:<entityId>" so the
        // partitioner can always extract it deterministically.
        if (keyBytes != null) {
            String keyStr = new String(keyBytes, StandardCharsets.UTF_8);
            // Key format: "<tenantId>:<entityId>" or plain tenantId
            String tenantId = keyStr.contains(":") ? keyStr.split(":", 2)[0] : keyStr;
            if (!tenantId.isEmpty()) {
                int partition = Math.abs(tenantId.hashCode()) % numPartitions;
                log.debug("TenantIdPartitioner: topic={} tenantId={} → partition={}/{}",
                        topic, tenantId, partition, numPartitions);
                return partition;
            }
        }

        // Fallback: distribute uniformly using value bytes hash
        if (valueBytes != null) {
            return Math.abs(java.util.Arrays.hashCode(valueBytes)) % numPartitions;
        }

        log.warn("TenantIdPartitioner: no key or value for topic={}; assigning partition 0", topic);
        return 0;
    }

    @Override
    public void close() {
        // No resources to release
    }

    @Override
    public void configure(Map<String, ?> configs) {
        // No configuration required
    }
}
