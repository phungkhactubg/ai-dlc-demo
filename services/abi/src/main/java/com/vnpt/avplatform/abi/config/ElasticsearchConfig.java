package com.vnpt.avplatform.abi.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.elasticsearch.repository.config.EnableElasticsearchRepositories;

/**
 * Elasticsearch configuration for the ABI service (FR-ABI-001, FR-ABI-032).
 *
 * <p>ABI uses Elasticsearch for high-performance aggregation queries on analytics facts.
 * Spring Data Elasticsearch auto-configuration handles the {@code ElasticsearchClient}
 * bean, wiring it from the {@code spring.elasticsearch.uris} property.</p>
 *
 * <p>Managed indices:</p>
 * <ul>
 *   <li>{@code analytics_facts} — raw ETL-transformed ride, fare, payment, metering facts</li>
 *   <li>{@code kpi_snapshots} — pre-aggregated KPI snapshots computed every 5 minutes</li>
 * </ul>
 *
 * <p><strong>BL-010 enforcement</strong>: ALL queries dispatched to Elasticsearch MUST
 * include a {@code tenantId} filter term. No cross-tenant data is allowed under any
 * circumstance. Repositories extending
 * {@link org.springframework.data.elasticsearch.repository.ElasticsearchRepository}
 * must always receive the tenantId from {@code TenantContext}
 * and include it as a mandatory query predicate.</p>
 */
@Configuration
@EnableElasticsearchRepositories(basePackages = "com.vnpt.avplatform.abi.repositories")
public class ElasticsearchConfig {

    /** Index name for raw analytics facts ingested from the ETL pipeline. */
    public static final String INDEX_ANALYTICS_FACTS = "analytics_facts";

    /** Index name for pre-aggregated KPI snapshots. */
    public static final String INDEX_KPI_SNAPSHOTS = "kpi_snapshots";
}
