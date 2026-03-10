package com.vnpt.avplatform.tms.events.publisher;

import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;

@Slf4j
@Component
public class TenantKafkaProducer {

    private static final String TOPIC = "tenant-events";

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public TenantKafkaProducer(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = Objects.requireNonNull(kafkaTemplate, "kafkaTemplate must not be null");
    }

    public void publish(String eventType, String tenantId, Map<String, Object> payload) {
        TenantEvent event = TenantEvent.builder()
                .eventType(eventType)
                .tenantId(tenantId)
                .payload(payload)
                .build();

        CompletableFuture<SendResult<String, Object>> future = kafkaTemplate.send(TOPIC, tenantId, event);
        future.whenComplete((result, ex) -> {
            if (ex != null) {
                log.error("Failed to publish event: type={}, tenantId={}, error={}", eventType, tenantId, ex.getMessage(), ex);
            } else {
                log.info("Published event: type={}, tenantId={}, partition={}, offset={}",
                        eventType, tenantId,
                        result.getRecordMetadata().partition(),
                        result.getRecordMetadata().offset());
            }
        });
    }
}
