package com.vnpt.avplatform.mkp.config;

import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.support.serializer.JsonSerializer;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Kafka configuration for the MKP (Marketplace) service.
 *
 * <p>MKP does <strong>not consume</strong> Kafka events in v1.0. This configuration
 * provides a producer-only setup for emitting marketplace domain events
 * (e.g., plugin published, partner approved) that other services may consume.</p>
 */
@Configuration
public class KafkaConfig {

    /** Topic for marketplace plugin lifecycle events. */
    public static final String TOPIC_PLUGIN_EVENTS = "plugin-events";

    /** Topic for partner status change events. */
    public static final String TOPIC_PARTNER_EVENTS = "partner-events";

    private final String bootstrapServers;

    public KafkaConfig(@Value("${spring.kafka.bootstrap-servers}") String bootstrapServers) {
        this.bootstrapServers = Objects.requireNonNull(bootstrapServers,
            "spring.kafka.bootstrap-servers must not be null");
    }

    /**
     * Creates the Kafka producer factory with idempotent, exactly-once producer settings.
     *
     * @return configured {@link ProducerFactory}
     */
    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        props.put(ProducerConfig.RETRIES_CONFIG, 3);
        props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 1);
        return new DefaultKafkaProducerFactory<>(props);
    }

    /**
     * Creates a {@link KafkaTemplate} for publishing marketplace events.
     *
     * @return configured {@link KafkaTemplate}
     */
    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }
}
