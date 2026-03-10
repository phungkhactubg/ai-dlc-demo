package com.vnpt.avplatform.ncs.config;

import com.vnpt.avplatform.shared.exception.PlatformException;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.List;
import java.util.UUID;

/**
 * Global exception handler for the NCS service.
 *
 * <p>Translates all thrown exceptions into structured {@link ApiResponse} error bodies
 * with appropriate HTTP status codes. Ensures no raw stack traces are leaked to clients.</p>
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * Handles {@link PlatformException} — domain-level business rule violations.
     *
     * @param ex      the platform exception
     * @param request the current HTTP request
     * @return structured error response with the exception's HTTP status
     */
    @ExceptionHandler(PlatformException.class)
    public ResponseEntity<ApiResponse<Void>> handlePlatformException(
            PlatformException ex,
            HttpServletRequest request) {

        String traceId = resolveTraceId(request);
        log.warn("PlatformException [{}] on {}: {}",
                ex.getErrorCode(), request.getRequestURI(), ex.getUserMessage());

        ApiResponse<Void> body = ApiResponse.error(
                ex.getErrorCode(),
                ex.getUserMessage(),
                ex.getHttpStatus(),
                traceId);

        return ResponseEntity.status(ex.getHttpStatus()).body(body);
    }

    /**
     * Handles {@link MethodArgumentNotValidException} — Bean Validation constraint failures.
     *
     * <p>Collects all field-level validation errors and returns them as a comma-separated
     * message so the client can correct all issues in a single request.</p>
     *
     * @param ex      the validation exception
     * @param request the current HTTP request
     * @return 400 Bad Request with field error details
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(
            MethodArgumentNotValidException ex,
            HttpServletRequest request) {

        String traceId = resolveTraceId(request);

        List<String> fieldErrors = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(this::formatFieldError)
                .toList();

        String message = String.join("; ", fieldErrors);
        log.warn("Validation failed on {}: {}", request.getRequestURI(), message);

        ApiResponse<Void> body = ApiResponse.error(
                "VALIDATION_FAILED",
                message,
                HttpStatus.BAD_REQUEST.value(),
                traceId);

        return ResponseEntity.badRequest().body(body);
    }

    /**
     * Handles all unhandled {@link Exception} — last-resort error handler.
     *
     * <p>Returns a generic 500 Internal Server Error without exposing internal details.</p>
     *
     * @param ex      the unhandled exception
     * @param request the current HTTP request
     * @return 500 Internal Server Error response
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(
            Exception ex,
            HttpServletRequest request) {

        String traceId = resolveTraceId(request);
        log.error("Unhandled exception on {} [traceId={}]: {}",
                request.getRequestURI(), traceId, ex.getMessage(), ex);

        ApiResponse<Void> body = ApiResponse.error(
                "INTERNAL_SERVER_ERROR",
                "An unexpected error occurred. Please try again or contact support.",
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                traceId);

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);
    }

    private String formatFieldError(FieldError fieldError) {
        return fieldError.getField() + ": " + fieldError.getDefaultMessage();
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
