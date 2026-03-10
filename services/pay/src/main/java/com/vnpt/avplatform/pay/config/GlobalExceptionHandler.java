package com.vnpt.avplatform.pay.config;

import com.vnpt.avplatform.shared.exception.PlatformException;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Global exception handler for the PAY service.
 *
 * <p>All exceptions are mapped to {@link ApiResponse} envelopes. Stack traces
 * for unexpected errors are logged at ERROR level with a traceId that is also
 * surfaced to the caller for support correlation — the actual cause is never
 * leaked to the response body.</p>
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * Handles all {@link PlatformException} subclasses with the correct HTTP status.
     */
    @ExceptionHandler(PlatformException.class)
    public ResponseEntity<ApiResponse<Void>> handlePlatformException(
            PlatformException ex, HttpServletRequest request) {
        log.warn("PlatformException on PAY [{}]: code={} message={}",
                request.getRequestURI(), ex.getErrorCode(), ex.getUserMessage());
        ApiResponse<Void> body = ApiResponse.error(
                ex.getErrorCode(),
                ex.getUserMessage(),
                ex.getHttpStatus(),
                resolveTraceId(request));
        return ResponseEntity.status(ex.getHttpStatus()).body(body);
    }

    /**
     * Handles Bean Validation failures with per-field error details.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Map<String, List<String>>>> handleValidation(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        Map<String, List<String>> fieldErrors = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .collect(Collectors.groupingBy(
                        FieldError::getField,
                        Collectors.mapping(FieldError::getDefaultMessage, Collectors.toList())));
        log.warn("Validation failed on PAY [{}]: {}", request.getRequestURI(), fieldErrors);
        ApiResponse<Map<String, List<String>>> body = ApiResponse.<Map<String, List<String>>>builder()
                .success(false)
                .data(fieldErrors)
                .error(ApiResponse.ErrorDetail.builder()
                        .code("VALIDATION_FAILED")
                        .message("Request validation failed — see data for field-level details")
                        .httpStatus(HttpStatus.BAD_REQUEST.value())
                        .build())
                .timestamp(java.time.format.DateTimeFormatter.ISO_INSTANT.format(java.time.Instant.now()))
                .traceId(resolveTraceId(request))
                .build();
        return ResponseEntity.badRequest().body(body);
    }

    /**
     * Handles malformed or unreadable JSON request bodies.
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> handleMessageNotReadable(
            HttpMessageNotReadableException ex, HttpServletRequest request) {
        log.warn("Unreadable HTTP message on PAY [{}]: {}", request.getRequestURI(), ex.getMessage());
        ApiResponse<Void> body = ApiResponse.error(
                "MALFORMED_REQUEST",
                "Request body is missing or cannot be parsed as valid JSON",
                HttpStatus.BAD_REQUEST.value(),
                resolveTraceId(request));
        return ResponseEntity.badRequest().body(body);
    }

    /**
     * Catch-all — logs full stack trace, returns sanitized 500 with traceId.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnexpected(
            Exception ex, HttpServletRequest request) {
        String traceId = resolveTraceId(request);
        log.error("Unexpected error on PAY [traceId={}] [{}]", traceId, request.getRequestURI(), ex);
        ApiResponse<Void> body = ApiResponse.error(
                "INTERNAL_SERVER_ERROR",
                "An unexpected error occurred. Please contact support with traceId: " + traceId,
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                traceId);
        return ResponseEntity.internalServerError().body(body);
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
