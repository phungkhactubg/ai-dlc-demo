package com.vnpt.avplatform.abi.config;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Objects;

/**
 * InfluxDB time-series database configuration for the ABI service.
 *
 * <p>InfluxDB is used to store high-frequency time-series metrics such as
 * real-time ride throughput, fare accumulation rates, and per-tenant KPI trends.
 * Data written to InfluxDB is complementary to the Elasticsearch aggregation store
 * and MongoDB operational store.</p>
 *
 * <p>Configuration properties are externalized via environment variables:</p>
 * <ul>
 *   <li>{@code INFLUXDB_URL} — InfluxDB server URL</li>
 *   <li>{@code INFLUXDB_TOKEN} — authentication token</li>
 *   <li>{@code INFLUXDB_ORG} — organization name</li>
 *   <li>{@code INFLUXDB_BUCKET} — default write/query bucket</li>
 * </ul>
 */
@Configuration
public class InfluxDbConfig {

    /**
     * Creates and configures an {@link InfluxDBClient} connected to the configured
     * InfluxDB instance.
     *
     * @param url   InfluxDB server URL (e.g., {@code http://localhost:8086})
     * @param token authentication token for write/read access
     * @param org   InfluxDB organization name
     * @return a configured {@link InfluxDBClient} instance
     */
    @Bean
    public InfluxDBClient influxDBClient(
            @Value("${influxdb.url}") String url,
            @Value("${influxdb.token}") String token,
            @Value("${influxdb.org}") String org) {
        Objects.requireNonNull(url, "influxdb.url must not be null");
        Objects.requireNonNull(token, "influxdb.token must not be null");
        Objects.requireNonNull(org, "influxdb.org must not be null");
        return InfluxDBClientFactory.create(url, token.toCharArray(), org);
    }
}
