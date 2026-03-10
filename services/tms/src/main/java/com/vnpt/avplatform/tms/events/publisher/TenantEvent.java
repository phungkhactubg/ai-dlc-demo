package com.vnpt.avplatform.tms.events.publisher;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Data
@Builder
public class TenantEvent {

    @Builder.Default
    private String eventId = UUID.randomUUID().toString();

    private String eventType;
    private String tenantId;

    @Builder.Default
    private Instant timestamp = Instant.now();

    private Map<String, Object> payload;
}
