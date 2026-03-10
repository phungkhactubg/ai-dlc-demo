package com.vnpt.avplatform.tms.config;

import com.vnpt.avplatform.shared.exception.PlatformException;
import com.vnpt.avplatform.shared.model.ApiResponse;
import com.vnpt.avplatform.tms.exception.AccessDeniedException;
import com.vnpt.avplatform.tms.exception.DomainAlreadyExistsException;
import com.vnpt.avplatform.tms.exception.FileSizeExceededException;
import com.vnpt.avplatform.tms.exception.InvalidFileTypeException;
import com.vnpt.avplatform.tms.exception.InvalidStatusTransitionException;
import com.vnpt.avplatform.tms.exception.OtpExpiredException;
import com.vnpt.avplatform.tms.exception.OtpInvalidException;
import com.vnpt.avplatform.tms.exception.OtpLockedException;
import com.vnpt.avplatform.tms.exception.OtpResendLimitException;
import com.vnpt.avplatform.tms.exception.RiderAlreadyExistsException;
import com.vnpt.avplatform.tms.exception.RiderNotFoundException;
import com.vnpt.avplatform.tms.exception.SagaCompensationException;
import com.vnpt.avplatform.tms.exception.SagaStepException;
import com.vnpt.avplatform.tms.exception.TenantContextMissingException;
import com.vnpt.avplatform.tms.exception.TenantNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(TenantNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleTenantNotFound(TenantNotFoundException ex, HttpServletRequest request) {
        log.warn("Tenant not found on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.error("TENANT_NOT_FOUND", ex.getMessage(), 404, resolveTraceId(request)));
    }

    @ExceptionHandler(RiderNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleRiderNotFound(RiderNotFoundException ex, HttpServletRequest request) {
        log.warn("Rider not found on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.error("RIDER_NOT_FOUND", ex.getMessage(), 404, resolveTraceId(request)));
    }

    @ExceptionHandler(DomainAlreadyExistsException.class)
    public ResponseEntity<ApiResponse<Void>> handleDomainAlreadyExists(DomainAlreadyExistsException ex, HttpServletRequest request) {
        log.warn("Domain conflict on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error("DOMAIN_ALREADY_EXISTS", ex.getMessage(), 409, resolveTraceId(request)));
    }

    @ExceptionHandler(RiderAlreadyExistsException.class)
    public ResponseEntity<ApiResponse<Void>> handleRiderAlreadyExists(RiderAlreadyExistsException ex, HttpServletRequest request) {
        log.warn("Rider conflict on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error("RIDER_ALREADY_EXISTS", ex.getMessage(), 409, resolveTraceId(request)));
    }

    @ExceptionHandler(InvalidStatusTransitionException.class)
    public ResponseEntity<ApiResponse<Void>> handleInvalidStatusTransition(InvalidStatusTransitionException ex, HttpServletRequest request) {
        log.warn("Invalid status transition on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error("INVALID_STATUS_TRANSITION", ex.getMessage(), 409, resolveTraceId(request)));
    }

    @ExceptionHandler(OtpLockedException.class)
    public ResponseEntity<ApiResponse<Void>> handleOtpLocked(OtpLockedException ex, HttpServletRequest request, HttpServletResponse response) {
        log.warn("OTP locked on [{}]: {}", request.getRequestURI(), ex.getMessage());
        response.setHeader("Retry-After", "1800");
        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body(ApiResponse.error("OTP_LOCKED", ex.getMessage(), 429, resolveTraceId(request)));
    }

    @ExceptionHandler(OtpResendLimitException.class)
    public ResponseEntity<ApiResponse<Void>> handleOtpResendLimit(OtpResendLimitException ex, HttpServletRequest request, HttpServletResponse response) {
        log.warn("OTP resend limit on [{}]: {}", request.getRequestURI(), ex.getMessage());
        response.setHeader("Retry-After", "3600");
        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body(ApiResponse.error("OTP_RESEND_LIMIT", ex.getMessage(), 429, resolveTraceId(request)));
    }

    @ExceptionHandler(OtpExpiredException.class)
    public ResponseEntity<ApiResponse<Void>> handleOtpExpired(OtpExpiredException ex, HttpServletRequest request) {
        log.warn("OTP expired on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("OTP_EXPIRED", ex.getMessage(), 400, resolveTraceId(request)));
    }

    @ExceptionHandler(OtpInvalidException.class)
    public ResponseEntity<ApiResponse<Map<String, Integer>>> handleOtpInvalid(OtpInvalidException ex, HttpServletRequest request) {
        log.warn("OTP invalid on [{}]: {}", request.getRequestURI(), ex.getMessage());
        ApiResponse<Map<String, Integer>> body = ApiResponse.<Map<String, Integer>>builder()
                .success(false)
                .data(null)
                .error(ApiResponse.ErrorDetail.builder()
                        .code("OTP_INVALID")
                        .message(ex.getMessage())
                        .httpStatus(400)
                        .build())
                .timestamp(DateTimeFormatter.ISO_INSTANT.format(Instant.now()))
                .traceId(resolveTraceId(request))
                .build();
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiResponse<Void>> handleAccessDenied(AccessDeniedException ex, HttpServletRequest request) {
        log.warn("Access denied on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(ApiResponse.error("ACCESS_DENIED", ex.getMessage(), 403, resolveTraceId(request)));
    }

    @ExceptionHandler(TenantContextMissingException.class)
    public ResponseEntity<ApiResponse<Void>> handleTenantContextMissing(TenantContextMissingException ex, HttpServletRequest request) {
        log.warn("Tenant context missing on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(ApiResponse.error("TENANT_CONTEXT_MISSING", ex.getMessage(), 403, resolveTraceId(request)));
    }

    @ExceptionHandler(SagaStepException.class)
    public ResponseEntity<ApiResponse<Void>> handleSagaStep(SagaStepException ex, HttpServletRequest request) {
        log.error("Saga step error on [{}]: {}", request.getRequestURI(), ex.getMessage(), ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error("SAGA_STEP_ERROR", ex.getMessage(), 500, resolveTraceId(request)));
    }

    @ExceptionHandler(SagaCompensationException.class)
    public ResponseEntity<ApiResponse<Void>> handleSagaCompensation(SagaCompensationException ex, HttpServletRequest request) {
        log.error("Saga compensation error on [{}]: {}", request.getRequestURI(), ex.getMessage(), ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error("SAGA_COMPENSATION_ERROR", ex.getMessage(), 500, resolveTraceId(request)));
    }

    @ExceptionHandler(InvalidFileTypeException.class)
    public ResponseEntity<ApiResponse<Void>> handleInvalidFileType(InvalidFileTypeException ex, HttpServletRequest request) {
        log.warn("Invalid file type on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("INVALID_FILE_TYPE", ex.getMessage(), 400, resolveTraceId(request)));
    }

    @ExceptionHandler(FileSizeExceededException.class)
    public ResponseEntity<ApiResponse<Void>> handleFileSizeExceeded(FileSizeExceededException ex, HttpServletRequest request) {
        log.warn("File size exceeded on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("FILE_SIZE_EXCEEDED", ex.getMessage(), 400, resolveTraceId(request)));
    }

    @ExceptionHandler(PlatformException.class)
    public ResponseEntity<ApiResponse<Void>> handlePlatformException(PlatformException ex, HttpServletRequest request) {
        log.warn("PlatformException on [{}]: code={} message={}", request.getRequestURI(), ex.getErrorCode(), ex.getUserMessage());
        return ResponseEntity.status(ex.getHttpStatus())
                .body(ApiResponse.error(ex.getErrorCode(), ex.getUserMessage(), ex.getHttpStatus(), resolveTraceId(request)));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Map<String, List<String>>>> handleValidation(MethodArgumentNotValidException ex, HttpServletRequest request) {
        Map<String, List<String>> fieldErrors = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .collect(Collectors.groupingBy(
                        FieldError::getField,
                        Collectors.mapping(FieldError::getDefaultMessage, Collectors.toList())));
        log.warn("Validation failed on [{}]: {}", request.getRequestURI(), fieldErrors);
        ApiResponse<Map<String, List<String>>> body = ApiResponse.<Map<String, List<String>>>builder()
                .success(false)
                .data(fieldErrors)
                .error(ApiResponse.ErrorDetail.builder()
                        .code("VALIDATION_FAILED")
                        .message("Request validation failed — see data for field-level details")
                        .httpStatus(HttpStatus.BAD_REQUEST.value())
                        .build())
                .timestamp(DateTimeFormatter.ISO_INSTANT.format(Instant.now()))
                .traceId(resolveTraceId(request))
                .build();
        return ResponseEntity.badRequest().body(body);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> handleMessageNotReadable(HttpMessageNotReadableException ex, HttpServletRequest request) {
        log.warn("Unreadable HTTP message on [{}]: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.badRequest()
                .body(ApiResponse.error("MALFORMED_REQUEST", "Request body is missing or cannot be parsed as valid JSON", 400, resolveTraceId(request)));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnexpected(Exception ex, HttpServletRequest request) {
        String traceId = resolveTraceId(request);
        log.error("Unexpected error [traceId={}] on [{}]", traceId, request.getRequestURI(), ex);
        return ResponseEntity.internalServerError()
                .body(ApiResponse.error("INTERNAL_SERVER_ERROR",
                        "An unexpected error occurred. Please contact support with traceId: " + traceId,
                        500, traceId));
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
