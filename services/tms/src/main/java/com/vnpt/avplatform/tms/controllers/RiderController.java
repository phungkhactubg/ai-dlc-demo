package com.vnpt.avplatform.tms.controllers;

import com.vnpt.avplatform.shared.model.ApiResponse;
import com.vnpt.avplatform.tms.models.request.RegisterRiderRequest;
import com.vnpt.avplatform.tms.models.request.UpdateRiderRequest;
import com.vnpt.avplatform.tms.models.response.RiderDTO;
import com.vnpt.avplatform.tms.services.OTPService;
import com.vnpt.avplatform.tms.services.RiderIdentityService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.vnpt.avplatform.tms.exception.OtpLockedException;
import com.vnpt.avplatform.tms.exception.OtpResendLimitException;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/riders")
public class RiderController {

    private final RiderIdentityService riderIdentityService;
    private final OTPService otpService;

    public RiderController(
            RiderIdentityService riderIdentityService,
            OTPService otpService) {
        this.riderIdentityService = Objects.requireNonNull(riderIdentityService, "riderIdentityService must not be null");
        this.otpService = Objects.requireNonNull(otpService, "otpService must not be null");
    }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<RiderDTO>> registerRider(
            @Valid @RequestBody RegisterRiderRequest request,
            @RequestHeader(value = "X-Tenant-ID") String tenantId,
            HttpServletRequest httpRequest) {
        log.info("Register rider request: tenantId={}, email={}", tenantId, request.getEmail());
        RiderDTO rider = riderIdentityService.registerRider(tenantId, request);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.success(rider, resolveTraceId(httpRequest)));
    }

    @PostMapping("/{riderId}/verify-phone")
    public ResponseEntity<ApiResponse<Void>> sendOtp(
            @PathVariable String riderId,
            @RequestBody Map<String, String> body,
            @RequestHeader(value = "X-Tenant-ID", required = false) String tenantId,
            HttpServletRequest httpRequest,
            HttpServletResponse httpResponse) {
        String phoneNumber = body.get("phoneNumber");
        if (phoneNumber == null || phoneNumber.isBlank()) {
            return ResponseEntity
                    .badRequest()
                    .body(ApiResponse.error("MISSING_FIELD", "phoneNumber is required", 400, resolveTraceId(httpRequest)));
        }
        try {
            otpService.sendOtp(riderId, tenantId, phoneNumber);
            return ResponseEntity.ok(ApiResponse.success(null, resolveTraceId(httpRequest)));
        } catch (OtpResendLimitException | OtpLockedException e) {
            httpResponse.setHeader("Retry-After", "3600");
            return ResponseEntity
                    .status(429)
                    .body(ApiResponse.error("TOO_MANY_REQUESTS", e.getMessage(), 429, resolveTraceId(httpRequest)));
        }
    }

    @PostMapping("/{riderId}/confirm-otp")
    public ResponseEntity<ApiResponse<Void>> confirmOtp(
            @PathVariable String riderId,
            @RequestBody Map<String, String> body,
            @RequestHeader(value = "X-Tenant-ID", required = false) String tenantId,
            HttpServletRequest httpRequest,
            HttpServletResponse httpResponse) {
        String phoneNumber = body.get("phoneNumber");
        String code = body.get("code");

        if (phoneNumber == null || phoneNumber.isBlank() || code == null || code.isBlank()) {
            return ResponseEntity
                    .badRequest()
                    .body(ApiResponse.error("MISSING_FIELD", "phoneNumber and code are required", 400, resolveTraceId(httpRequest)));
        }

        try {
            otpService.verifyOtp(riderId, tenantId, phoneNumber, code);
            return ResponseEntity.ok(ApiResponse.success(null, resolveTraceId(httpRequest)));
        } catch (OtpLockedException e) {
            httpResponse.setHeader("Retry-After", "1800");
            return ResponseEntity
                    .status(429)
                    .body(ApiResponse.error("OTP_LOCKED", e.getMessage(), 429, resolveTraceId(httpRequest)));
        }
    }

    @GetMapping("/{riderId}")
    public ResponseEntity<ApiResponse<RiderDTO>> getRider(
            @PathVariable String riderId,
            HttpServletRequest httpRequest) {
        RiderDTO rider = riderIdentityService.getRider(riderId);
        return ResponseEntity.ok(ApiResponse.success(rider, resolveTraceId(httpRequest)));
    }

    @PutMapping("/{riderId}")
    public ResponseEntity<ApiResponse<RiderDTO>> updateRider(
            @PathVariable String riderId,
            @Valid @RequestBody UpdateRiderRequest request,
            HttpServletRequest httpRequest) {
        RiderDTO rider = riderIdentityService.updateRider(riderId, request);
        return ResponseEntity.ok(ApiResponse.success(rider, resolveTraceId(httpRequest)));
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
