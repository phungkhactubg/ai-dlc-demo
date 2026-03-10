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

import java.math.BigDecimal;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "tenants")
public class Tenant {

    @Id
    private String id;

    @Indexed(unique = true)
    @Field("tenant_id")
    private String tenantId;

    @Field("company_name")
    private String companyName;

    @Indexed(unique = true)
    @Field("company_domain")
    private String companyDomain;

    @Field("country_code")
    private String countryCode;

    @Field("timezone")
    private String timezone;

    @Builder.Default
    @Field("status")
    private TenantStatus status = TenantStatus.ONBOARDING;

    @Field("plan_id")
    private String planId;

    @Field("subscription_id")
    private String subscriptionId;

    @Field("admin_user_id")
    private String adminUserId;

    @Field("api_key_reference")
    private String apiKeyReference;

    @Field("vehicle_quota")
    private Integer vehicleQuota;

    @Field("branding")
    private TenantBranding branding;

    @Builder.Default
    @Field("surge_cap")
    private BigDecimal surgeCap = new BigDecimal("3.0");

    @Builder.Default
    @Field("feature_flags")
    private Map<String, Boolean> featureFlags = new HashMap<>();

    @Builder.Default
    @Field("config")
    private Map<String, Object> config = new HashMap<>();

    @Field("cancellation_policy")
    private CancellationPolicy cancellationPolicy;

    @Field("monthly_budget_alert_threshold")
    private BigDecimal monthlyBudgetAlertThreshold;

    @Field("created_at")
    private Instant createdAt;

    @Field("updated_at")
    private Instant updatedAt;

    @Version
    @Field("version")
    private Long version;
}
