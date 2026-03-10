package com.vnpt.avplatform.abi.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * ABI ETL Pipeline Configuration (FR-ABI-030 through FR-ABI-033).
 *
 * <p>Defines the ETL pipeline topology and scheduling constants:</p>
 * <pre>
 * Kafka events → ETL Transformer → Elasticsearch + InfluxDB + MongoDB
 * </pre>
 *
 * <p>Consumed topics (consumer group: {@value #CONSUMER_GROUP}):</p>
 * <ul>
 *   <li>{@value KafkaConfig#TOPIC_RIDE_EVENTS} — from RHS</li>
 *   <li>{@value KafkaConfig#TOPIC_FARE_EVENTS} — from FPE</li>
 *   <li>{@value KafkaConfig#TOPIC_PAYMENT_EVENTS} — from PAY</li>
 *   <li>{@value KafkaConfig#TOPIC_BILLING_EVENTS} — from BMS</li>
 *   <li>{@value KafkaConfig#TOPIC_METERING_EVENTS} — from BMS</li>
 *   <li>{@value KafkaConfig#TOPIC_TENANT_EVENTS} — from TMS</li>
 * </ul>
 *
 * <p><strong>BL-010</strong>: ABI reports must NOT expose cross-tenant data.
 * Every query MUST include {@code {tenantId: requestingTenantId}} as a mandatory filter.</p>
 *
 * <p>KPI computation is triggered by a {@code @Scheduled} task every
 * {@value #KPI_COMPUTATION_INTERVAL_MS} milliseconds (5 minutes).</p>
 */
@Configuration
@EnableScheduling
public class EtlPipelineConfig {

    /** Kafka consumer group for all ABI analytics consumers. */
    public static final String CONSUMER_GROUP = "abi-analytics-consumer-group";

    /** KPI computation schedule interval: 5 minutes in milliseconds. */
    public static final long KPI_COMPUTATION_INTERVAL_MS = 300_000L;

    /** Cron expression equivalent of the 5-minute KPI computation interval. */
    public static final String KPI_COMPUTATION_CRON = "0 */5 * * * *";
}
