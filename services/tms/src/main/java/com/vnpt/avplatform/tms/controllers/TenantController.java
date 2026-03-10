package com.vnpt.avplatform.tms.controllers;

import com.vnpt.avplatform.shared.model.ApiResponse;
import com.vnpt.avplatform.tms.models.request.CreateTenantRequest;
import com.vnpt.avplatform.tms.models.request.UpdateTenantStatusRequest;
import com.vnpt.avplatform.tms.models.response.PageResult;
import com.vnpt.avplatform.tms.models.response.TenantDTO;
import com.vnpt.avplatform.tms.services.TenantService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/tenants")
public class TenantController {

    private final TenantService tenantService;

    public TenantController(TenantService tenantService) {
        this.tenantService = Objects.requireNonNull(tenantService, "tenantService must not be null");
    }

    @PostMapping
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public ResponseEntity<ApiResponse<TenantDTO>> createTenant(
            @Valid @RequestBody CreateTenantRequest request,
            HttpServletRequest httpRequest) {
        log.info("Create tenant request: domain={}", request.getCompanyDomain());
        TenantDTO tenant = tenantService.createTenant(request);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.success(tenant, resolveTraceId(httpRequest)));
    }

    @GetMapping("/{tenantId}")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public ResponseEntity<ApiResponse<TenantDTO>> getTenant(
            @PathVariable String tenantId,
            HttpServletRequest httpRequest) {
        TenantDTO tenant = tenantService.getTenant(tenantId);
        return ResponseEntity.ok(ApiResponse.success(tenant, resolveTraceId(httpRequest)));
    }

    @GetMapping
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public ResponseEntity<ApiResponse<PageResult<TenantDTO>>> listTenants(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            HttpServletRequest httpRequest) {
        PageResult<TenantDTO> result = tenantService.listTenants(page, size);
        return ResponseEntity.ok(ApiResponse.success(result, resolveTraceId(httpRequest)));
    }

    @PutMapping("/{tenantId}/status")
    @PreAuthorize("hasRole('PLATFORM_ADMIN')")
    public ResponseEntity<ApiResponse<TenantDTO>> updateStatus(
            @PathVariable String tenantId,
            @Valid @RequestBody UpdateTenantStatusRequest request,
            HttpServletRequest httpRequest) {
        TenantDTO tenant;
        if ("suspend".equalsIgnoreCase(request.getAction())) {
            tenant = tenantService.suspendTenant(tenantId, request.getReason());
        } else if ("reactivate".equalsIgnoreCase(request.getAction())) {
            tenant = tenantService.reactivateTenant(tenantId);
        } else {
            return ResponseEntity
                    .badRequest()
                    .body(ApiResponse.error("INVALID_ACTION",
                            "Action must be 'suspend' or 'reactivate'",
                            400, resolveTraceId(httpRequest)));
        }
        return ResponseEntity.ok(ApiResponse.success(tenant, resolveTraceId(httpRequest)));
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
