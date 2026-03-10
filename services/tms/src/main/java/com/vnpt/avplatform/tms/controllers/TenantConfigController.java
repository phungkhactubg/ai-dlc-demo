package com.vnpt.avplatform.tms.controllers;

import com.vnpt.avplatform.shared.model.ApiResponse;
import com.vnpt.avplatform.tms.services.FeatureFlagService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/tenants/{tenantId}")
public class TenantConfigController {

    private final FeatureFlagService featureFlagService;

    public TenantConfigController(FeatureFlagService featureFlagService) {
        this.featureFlagService = Objects.requireNonNull(featureFlagService, "featureFlagService must not be null");
    }

    @GetMapping("/config")
    @PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Boolean>>> getAllFlags(
            @PathVariable String tenantId,
            HttpServletRequest httpRequest) {
        Map<String, Boolean> flags = featureFlagService.getAllFlags(tenantId);
        return ResponseEntity.ok(ApiResponse.success(flags, resolveTraceId(httpRequest)));
    }

    @PutMapping("/feature-flags")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Boolean>>> updateFlags(
            @PathVariable String tenantId,
            @RequestBody Map<String, Boolean> flags,
            HttpServletRequest httpRequest) {
        Map<String, Boolean> updated = featureFlagService.updateFlags(tenantId, flags);
        return ResponseEntity.ok(ApiResponse.success(updated, resolveTraceId(httpRequest)));
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
