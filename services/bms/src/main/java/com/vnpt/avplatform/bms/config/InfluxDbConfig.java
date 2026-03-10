package com.vnpt.avplatform.bms.config;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * InfluxDB client configuration for BMS usage metering.
 *
 * <p>InfluxDB is used to store time-series metering data (trip counts, API calls,
 * vehicle registrations, storage usage) for quota enforcement (FR-BMS-010 to FR-BMS-013)
 * and billing cycle aggregation.</p>
 */
@Slf4j
@Configuration
public class InfluxDbConfig {

    /**
     * Creates and configures the {@link InfluxDBClient} bean.
     *
     * @param url   InfluxDB server URL (default: {@code http://localhost:8086})
     * @param token InfluxDB authentication token (default: {@code dev-token})
     * @param org   InfluxDB organization name (default: {@code vnpt-av})
     * @return fully configured {@link InfluxDBClient}
     */
    @Bean
    public InfluxDBClient influxDBClient(
            @Value("${influxdb.url:http://localhost:8086}") String url,
            @Value("${influxdb.token:dev-token}") String token,
            @Value("${influxdb.org:vnpt-av}") String org) {

        log.info("Initialising InfluxDB client: url={}, org={}", url, org);
        return InfluxDBClientFactory.create(url, token.toCharArray(), org);
    }
}
