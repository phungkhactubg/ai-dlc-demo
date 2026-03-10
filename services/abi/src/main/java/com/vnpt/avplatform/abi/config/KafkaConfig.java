package com.vnpt.avplatform.abi.config;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.support.serializer.JsonDeserializer;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Kafka configuration for the ABI service.
 *
 * <p>ABI is a <strong>consumer-only</strong> service. It subscribes to the following topics
 * under the {@code abi-analytics-consumer-group}:</p>
 * <ul>
 *   <li>{@code ride-events} — from RHS (Ride Handling Service)</li>
 *   <li>{@code fare-events} — from FPE (Fare/Pricing Engine)</li>
 *   <li>{@code payment-events} — from PAY (Payment Service)</li>
 *   <li>{@code billing-events} — from BMS (Billing & Metering Service)</li>
 *   <li>{@code metering-events} — from BMS (Billing & Metering Service)</li>
 *   <li>{@code tenant-events} — from TMS (Tenant Management Service)</li>
 * </ul>
 *
 * <p>Isolation level is set to {@code read_committed} to ensure ABI only processes
 * events that have been durably committed by the producing services.</p>
 */
@Configuration
public class KafkaConfig {

    /** Kafka consumer group identifier for all ABI analytics consumers. */
    public static final String CONSUMER_GROUP = "abi-analytics-consumer-group";

    public static final String TOPIC_RIDE_EVENTS     = "ride-events";
    public static final String TOPIC_FARE_EVENTS     = "fare-events";
    public static final String TOPIC_PAYMENT_EVENTS  = "payment-events";
    public static final String TOPIC_BILLING_EVENTS  = "billing-events";
    public static final String TOPIC_METERING_EVENTS = "metering-events";
    public static final String TOPIC_TENANT_EVENTS   = "tenant-events";

    private final String bootstrapServers;

    public KafkaConfig(@Value("${spring.kafka.bootstrap-servers}") String bootstrapServers) {
        this.bootstrapServers = Objects.requireNonNull(bootstrapServers,
            "spring.kafka.bootstrap-servers must not be null");
    }

    /**
     * Creates the consumer factory configured with the ABI consumer group and
     * read_committed isolation level.
     *
     * @return configured {@link ConsumerFactory}
     */
    @Bean
    public ConsumerFactory<String, Object> consumerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, CONSUMER_GROUP);
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
        props.put(JsonDeserializer.TRUSTED_PACKAGES, "com.vnpt.avplatform.*");
        props.put(JsonDeserializer.USE_TYPE_INFO_HEADERS, true);
        return new DefaultKafkaConsumerFactory<>(props);
    }

    /**
     * Creates the Kafka listener container factory with manual acknowledgement mode.
     * Manual ack ensures that offsets are committed only after successful processing.
     *
     * @return configured {@link ConcurrentKafkaListenerContainerFactory}
     */
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, Object> factory =
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        factory.setConcurrency(3);
        return factory;
    }
}
