package com.vnpt.avplatform.tms.models.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SagaStep {

    @Field("step_name")
    private String stepName;

    @Builder.Default
    @Field("status")
    private String status = "PENDING";

    @Field("external_ref")
    private String externalRef;

    @Field("completed_at")
    private Instant completedAt;

    @Field("error_message")
    private String errorMessage;
}
