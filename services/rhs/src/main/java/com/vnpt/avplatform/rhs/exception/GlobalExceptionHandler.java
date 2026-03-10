package com.vnpt.avplatform.rhs.exception;

import com.vnpt.avplatform.shared.exception.PlatformException;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Centralised exception handler for the RHS service.
 *
 * <p>Translates all domain, validation, and unexpected exceptions into the platform's
 * standard {@link ApiResponse} error envelope so that clients always receive a
 * consistent JSON error structure with a traceable {@code traceId}.
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(PlatformException.class)
    public ResponseEntity<ApiResponse<Void>> handlePlatformException(
            PlatformException ex, HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.error("PlatformException [{}] on {}: {} — traceId={}",
                ex.getErrorCode(), request.getRequestURI(), ex.getUserMessage(), traceId, ex);
        return ResponseEntity.status(ex.getHttpStatus())
                .body(ApiResponse.error(ex.getErrorCode(), ex.getUserMessage(), ex.getHttpStatus(), traceId));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        List<String> fieldErrors = ex.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.toList());
        String message = "Validation failed: " + String.join("; ", fieldErrors);
        log.warn("Validation error on {} — traceId={}: {}", request.getRequestURI(), traceId, message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("VALIDATION_ERROR", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiResponse<Void>> handleConstraintViolationException(
            ConstraintViolationException ex, HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        List<String> violations = ex.getConstraintViolations().stream()
                .map(ConstraintViolation::getMessage)
                .collect(Collectors.toList());
        String message = "Constraint violation: " + String.join("; ", violations);
        log.warn("Constraint violation on {} — traceId={}: {}", request.getRequestURI(), traceId, message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("CONSTRAINT_VIOLATION", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    @ExceptionHandler(MissingRequestHeaderException.class)
    public ResponseEntity<ApiResponse<Void>> handleMissingHeader(
            MissingRequestHeaderException ex, HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        String message = "Required header '" + ex.getHeaderName() + "' is missing";
        log.warn("Missing header on {} — traceId={}: {}", request.getRequestURI(), traceId, message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("MISSING_HEADER", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ApiResponse<Void>> handleTypeMismatch(
            MethodArgumentTypeMismatchException ex, HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        String message = String.format("Parameter '%s' has an invalid value: '%s'", ex.getName(), ex.getValue());
        log.warn("Type mismatch on {} — traceId={}: {}", request.getRequestURI(), traceId, message);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error("TYPE_MISMATCH", message, HttpStatus.BAD_REQUEST.value(), traceId));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(
            Exception ex, HttpServletRequest request) {
        String traceId = UUID.randomUUID().toString();
        log.error("Unhandled exception on {} — traceId={}", request.getRequestURI(), traceId, ex);
        String message = "An unexpected error occurred. Contact support with traceId: " + traceId;
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error("INTERNAL_SERVER_ERROR", message,
                        HttpStatus.INTERNAL_SERVER_ERROR.value(), traceId));
    }
}
