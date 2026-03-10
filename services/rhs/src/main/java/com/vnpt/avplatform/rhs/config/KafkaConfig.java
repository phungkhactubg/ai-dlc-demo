package com.vnpt.avplatform.rhs.config;

import com.vnpt.avplatform.shared.kafka.TenantIdPartitioner;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.support.serializer.JsonDeserializer;
import org.springframework.kafka.support.serializer.JsonSerializer;
import org.springframework.util.backoff.FixedBackOff;

import java.util.HashMap;
import java.util.Map;

/**
 * Kafka producer/consumer configuration for the RHS service.
 *
 * <p>Producers use {@link TenantIdPartitioner} to route messages deterministically
 * by tenant, ensuring per-tenant ordering. Consumers operate in read-committed
 * isolation and retry failed records up to {@value #MAX_RETRY_ATTEMPTS} times before
 * forwarding them to a DLQ topic ({@code <original-topic>.dlq}).
 */
@Slf4j
@Configuration
@EnableKafka
public class KafkaConfig {

    private static final int MAX_RETRY_ATTEMPTS = 3;
    private static final long RETRY_INTERVAL_MS = 1_000L;

    @Value("${spring.kafka.bootstrap-servers:localhost:9092}")
    private String bootstrapServers;

    @Value("${spring.application.name:rhs-service}")
    private String applicationName;

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        props.put(ProducerConfig.PARTITIONER_CLASS_CONFIG, TenantIdPartitioner.class.getName());
        props.put(JsonSerializer.ADD_TYPE_INFO_HEADERS, false);
        return new DefaultKafkaProducerFactory<>(props);
    }

    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate(ProducerFactory<String, Object> producerFactory) {
        return new KafkaTemplate<>(producerFactory);
    }

    @Bean
    public ConsumerFactory<String, Object> consumerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, applicationName);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");
        props.put(JsonDeserializer.TRUSTED_PACKAGES, "com.vnpt.avplatform.*");
        props.put(JsonDeserializer.USE_TYPE_INFO_HEADERS, false);
        return new DefaultKafkaConsumerFactory<>(props);
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory(
            ConsumerFactory<String, Object> consumerFactory,
            KafkaTemplate<String, Object> kafkaTemplate) {

        ConcurrentKafkaListenerContainerFactory<String, Object> factory =
                new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory);
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.RECORD);
        factory.setCommonErrorHandler(buildErrorHandler(kafkaTemplate));
        return factory;
    }

    private DefaultErrorHandler buildErrorHandler(KafkaTemplate<String, Object> kafkaTemplate) {
        DefaultErrorHandler handler = new DefaultErrorHandler(
                (record, exception) -> {
                    String dlqTopic = record.topic() + ".dlq";
                    log.error(
                            "Record failed after {} retries — routing to DLQ. "
                                    + "topic={} partition={} offset={} key={}",
                            MAX_RETRY_ATTEMPTS,
                            record.topic(), record.partition(), record.offset(), record.key(),
                            exception);
                    kafkaTemplate.send(dlqTopic, String.valueOf(record.key()), record.value());
                },
                new FixedBackOff(RETRY_INTERVAL_MS, MAX_RETRY_ATTEMPTS));

        handler.addNotRetryableExceptions(IllegalArgumentException.class);
        return handler;
    }
}
