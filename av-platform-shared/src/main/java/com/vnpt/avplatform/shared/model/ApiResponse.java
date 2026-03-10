package com.vnpt.avplatform.shared.model;

import lombok.Builder;
import lombok.Getter;

import java.time.Instant;
import java.time.format.DateTimeFormatter;

/**
 * Generic, uniform API response envelope for all AV Platform REST endpoints.
 *
 * <p>Every HTTP response body follows this structure, allowing clients to rely on a
 * consistent contract regardless of the service they call:</p>
 * <ul>
 *   <li>{@code success} — {@code true} for 2xx responses, {@code false} on errors.</li>
 *   <li>{@code data} — the response payload; {@code null} on error responses.</li>
 *   <li>{@code error} — error detail; {@code null} on success responses.</li>
 *   <li>{@code timestamp} — ISO-8601 UTC timestamp of when the response was generated.</li>
 *   <li>{@code traceId} — distributed trace ID for log correlation.</li>
 * </ul>
 *
 * <p>Use the static factory methods rather than the builder directly:</p>
 * <pre>{@code
 * // Success
 * return ResponseEntity.ok(ApiResponse.success(vehicle, traceId));
 *
 * // Error
 * return ResponseEntity
 *     .status(HttpStatus.NOT_FOUND)
 *     .body(ApiResponse.error("RESOURCE_NOT_FOUND", "Vehicle not found", 404, traceId));
 * }</pre>
 *
 * @param <T> the type of the {@code data} payload
 */
@Getter
@Builder
public class ApiResponse<T> {

    /** {@code true} if the request was processed successfully. */
    private final boolean success;

    /** The response payload; {@code null} when {@code success} is {@code false}. */
    private final T data;

    /** Error details; {@code null} when {@code success} is {@code true}. */
    private final ErrorDetail error;

    /** ISO-8601 UTC timestamp of response generation (e.g., {@code 2024-06-01T12:00:00Z}). */
    private final String timestamp;

    /** Distributed trace ID for correlating logs across services. */
    private final String traceId;

    // -------------------------------------------------------------------------
    // Static factory methods
    // -------------------------------------------------------------------------

    /**
     * Creates a successful response envelope wrapping the given data payload.
     *
     * @param data    the response payload; may be {@code null} for empty-body successes
     * @param traceId the distributed trace ID for log correlation
     * @param <T>     the type of the data payload
     * @return a new {@link ApiResponse} with {@code success = true}
     */
    public static <T> ApiResponse<T> success(T data, String traceId) {
        return ApiResponse.<T>builder()
                .success(true)
                .data(data)
                .error(null)
                .timestamp(nowIso8601())
                .traceId(traceId)
                .build();
    }

    /**
     * Creates an error response envelope with structured error details.
     *
     * @param errorCode  machine-readable error code (e.g., {@code RESOURCE_NOT_FOUND})
     * @param message    human-readable description of the error
     * @param httpStatus the HTTP status code that will be set on the response
     * @param traceId    the distributed trace ID for log correlation
     * @param <T>        the (unused) payload type; always {@code null} on error
     * @return a new {@link ApiResponse} with {@code success = false}
     */
    public static <T> ApiResponse<T> error(String errorCode, String message, int httpStatus, String traceId) {
        return ApiResponse.<T>builder()
                .success(false)
                .data(null)
                .error(ErrorDetail.builder()
                        .code(errorCode)
                        .message(message)
                        .httpStatus(httpStatus)
                        .build())
                .timestamp(nowIso8601())
                .traceId(traceId)
                .build();
    }

    /**
     * Returns the current UTC instant formatted as ISO-8601.
     *
     * @return ISO-8601 timestamp string, e.g., {@code 2024-06-01T12:00:00Z}
     */
    private static String nowIso8601() {
        return DateTimeFormatter.ISO_INSTANT.format(Instant.now());
    }

    // -------------------------------------------------------------------------
    // Nested ErrorDetail
    // -------------------------------------------------------------------------

    /**
     * Structured error information included in non-success API responses.
     */
    @Getter
    @Builder
    public static class ErrorDetail {

        /** Machine-readable error code (e.g., {@code RESOURCE_NOT_FOUND}). */
        private final String code;

        /** Human-readable description of the error. */
        private final String message;

        /** The HTTP status code associated with this error. */
        private final int httpStatus;
    }
}
