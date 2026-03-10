package com.vnpt.avplatform.mkp.exception;

import com.vnpt.avplatform.shared.exception.PlatformException;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Global exception handler for the MKP (Marketplace) service.
 *
 * <p>Translates all domain and infrastructure exceptions into consistent
 * {@link ApiResponse} error envelopes. Every error response includes a
 * {@code traceId} for log correlation.</p>
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * Handles {@link PlatformException} — the root domain exception.
     * Uses the status code and error code embedded in the exception.
     */
    @ExceptionHandler(PlatformException.class)
    public ResponseEntity<ApiResponse<Void>> handlePlatformException(
            PlatformException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        log.warn("PlatformException [{}] on {} {}: {}",
            ex.getErrorCode(), request.getMethod(), request.getRequestURI(), ex.getUserMessage());
        return ResponseEntity
            .status(ex.getHttpStatus())
            .body(ApiResponse.error(ex.getErrorCode(), ex.getUserMessage(), ex.getHttpStatus(), traceId));
    }

    /**
     * Handles Spring Validation failures from {@code @Valid} annotated parameters.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        String message = ex.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining("; "));
        log.warn("Validation failed on {} {}: {}", request.getMethod(), request.getRequestURI(), message);
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponse.error("VALIDATION_FAILED", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    /**
     * Handles missing required request headers.
     */
    @ExceptionHandler(MissingRequestHeaderException.class)
    public ResponseEntity<ApiResponse<Void>> handleMissingHeader(
            MissingRequestHeaderException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        String message = "Required header '" + ex.getHeaderName() + "' is missing";
        log.warn("Missing header on {} {}: {}", request.getMethod(), request.getRequestURI(), message);
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponse.error("MISSING_HEADER", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    /**
     * Handles type mismatch errors in path variables or request parameters.
     */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ApiResponse<Void>> handleTypeMismatch(
            MethodArgumentTypeMismatchException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        String message = "Invalid value '" + ex.getValue() + "' for parameter '" + ex.getName() + "'";
        log.warn("Type mismatch on {} {}: {}", request.getMethod(), request.getRequestURI(), message);
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponse.error("INVALID_PARAMETER", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    /**
     * Handles Spring Security authentication failures.
     */
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ApiResponse<Void>> handleAuthenticationException(
            AuthenticationException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        log.warn("Authentication failed on {} {}: {}", request.getMethod(), request.getRequestURI(), ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.UNAUTHORIZED)
            .body(ApiResponse.error("UNAUTHORIZED", "Authentication required", HttpStatus.UNAUTHORIZED.value(), traceId));
    }

    /**
     * Handles Spring Security authorization failures (e.g., missing ROLE_MARKETPLACE_ADMIN).
     */
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiResponse<Void>> handleAccessDeniedException(
            AccessDeniedException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        log.warn("Access denied on {} {}: {}", request.getMethod(), request.getRequestURI(), ex.getMessage());
        return ResponseEntity
            .status(HttpStatus.FORBIDDEN)
            .body(ApiResponse.error("FORBIDDEN", "Access denied. Required role: ROLE_MARKETPLACE_ADMIN", HttpStatus.FORBIDDEN.value(), traceId));
    }

    /**
     * Catch-all handler for unexpected exceptions.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(
            Exception ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        log.error("Unexpected error on {} {}: traceId={}",
            request.getMethod(), request.getRequestURI(), traceId, ex);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponse.error(
                "INTERNAL_SERVER_ERROR",
                "An unexpected error occurred. Please contact support with traceId: " + traceId,
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                traceId));
    }

    private String generateTraceId() {
        return UUID.randomUUID().toString();
    }
}
