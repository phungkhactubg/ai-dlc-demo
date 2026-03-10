package com.vnpt.avplatform.tms.models.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Version;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "onboarding_sagas")
public class OnboardingSaga {

    @Id
    private String id;

    @Indexed(unique = true)
    @Field("saga_id")
    private String sagaId;

    @Indexed(unique = true)
    @Field("tenant_id")
    private String tenantId;

    @Builder.Default
    @Field("status")
    private SagaStatus status = SagaStatus.PENDING;

    @Builder.Default
    @Field("steps")
    private List<SagaStep> steps = new ArrayList<>();

    @Builder.Default
    @Field("current_step_index")
    private int currentStepIndex = 0;

    @Builder.Default
    @Field("compensation_log")
    private List<String> compensationLog = new ArrayList<>();

    @Field("started_at")
    private Instant startedAt;

    @Field("completed_at")
    private Instant completedAt;

    @Field("failed_at")
    private Instant failedAt;

    @Builder.Default
    @Field("total_timeout_seconds")
    private int totalTimeoutSeconds = 120;

    @Builder.Default
    @Field("per_step_timeout_seconds")
    private int perStepTimeoutSeconds = 30;

    @Version
    @Field("version")
    private Long version;
}
