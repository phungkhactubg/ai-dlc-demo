package com.vnpt.avplatform.abi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * ABI (Analytics & Business Intelligence) Service main application class.
 *
 * <p>This service is responsible for:
 * <ul>
 *   <li>Consuming ride, fare, payment, billing, metering, and tenant events from Kafka</li>
 *   <li>Running ETL pipelines to transform events into analytics facts</li>
 *   <li>Storing aggregated KPIs in Elasticsearch, InfluxDB, and MongoDB</li>
 *   <li>Generating reports and exporting them to MinIO (S3-compatible)</li>
 * </ul>
 *
 * <p>BL-010: ALL queries must include tenantId filter. No cross-tenant data is allowed.</p>
 */
@SpringBootApplication
@EnableKafka
@EnableScheduling
public class AbiApplication {

    public static void main(String[] args) {
        SpringApplication.run(AbiApplication.class, args);
    }
}
