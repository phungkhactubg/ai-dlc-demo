package com.vnpt.avplatform.tms.models.response;

import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;

@Data
@Builder
public class TenantDTO {
    private String tenantId;
    private String companyName;
    private String companyDomain;
    private TenantStatus status;
    private String planId;
    private BigDecimal surgeCap;
    private Map<String, Boolean> featureFlags;
    private Instant createdAt;
}
