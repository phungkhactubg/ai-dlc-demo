package com.vnpt.avplatform.bms.config;

import com.vnpt.avplatform.shared.kafka.TenantIdPartitioner;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.listener.CommonErrorHandler;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.util.backoff.FixedBackOff;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Kafka configuration for the BMS service.
 *
 * <p>Producer is configured with {@link TenantIdPartitioner} to route all messages
 * for the same tenant to the same partition, guaranteeing per-tenant ordering.</p>
 *
 * <p>Consumer error handling uses {@link DefaultErrorHandler} with a {@link FixedBackOff}
 * of 3 retry attempts. On exhaustion, messages are forwarded to the Dead-Letter Topic
 * (DLT) via {@link DeadLetterPublishingRecoverer}. DLT topic name is derived automatically
 * by Spring Kafka: {@code <original-topic>.DLT}.</p>
 */
@Slf4j
@Configuration
public class KafkaConfig {

    private static final int DLQ_MAX_RETRIES = 3;
    private static final long DLQ_RETRY_INTERVAL_MS = 1_000L;

    private final ProducerFactory<String, Object> producerFactory;
    private final ConsumerFactory<String, Object> consumerFactory;

    public KafkaConfig(
            ProducerFactory<String, Object> producerFactory,
            ConsumerFactory<String, Object> consumerFactory) {
        this.producerFactory = Objects.requireNonNull(producerFactory, "producerFactory must not be null");
        this.consumerFactory = Objects.requireNonNull(consumerFactory, "consumerFactory must not be null");
    }

    /**
     * KafkaTemplate with TenantIdPartitioner configured so all BMS events for the
     * same tenant land in the same partition (for ordering guarantees).
     *
     * @return configured {@link KafkaTemplate}
     */
    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        Map<String, Object> overrides = new HashMap<>();
        overrides.put(
                ProducerConfig.PARTITIONER_CLASS_CONFIG,
                TenantIdPartitioner.class.getName());

        return new KafkaTemplate<>(producerFactory, overrides);
    }

    /**
     * Concurrent listener container factory with DLQ error handling.
     *
     * <p>On 3 consecutive failures the message is published to the Dead-Letter Topic
     * ({@code <original>.DLT}) and the original message is acknowledged to prevent
     * an infinite consumer loop.</p>
     *
     * @return configured {@link ConcurrentKafkaListenerContainerFactory}
     */
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, Object> factory =
                new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory);
        factory.setCommonErrorHandler(deadLetterErrorHandler());
        return factory;
    }

    private CommonErrorHandler deadLetterErrorHandler() {
        DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(kafkaTemplate());
        FixedBackOff backOff = new FixedBackOff(DLQ_RETRY_INTERVAL_MS, DLQ_MAX_RETRIES);
        DefaultErrorHandler handler = new DefaultErrorHandler(recoverer, backOff);

        handler.setRetryListeners((record, ex, deliveryAttempt) ->
                log.warn("BMS Kafka retry attempt={} for topic={} partition={} offset={}: {}",
                        deliveryAttempt,
                        record.topic(),
                        record.partition(),
                        record.offset(),
                        ex.getMessage()));

        return handler;
    }
}
