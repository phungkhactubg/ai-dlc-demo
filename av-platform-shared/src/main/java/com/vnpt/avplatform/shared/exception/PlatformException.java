package com.vnpt.avplatform.shared.exception;

import org.springframework.http.HttpStatus;

/**
 * Root runtime exception for the AV Platform.
 *
 * <p>All business-rule and infrastructure violations thrown by platform services
 * should extend or use this class. It carries an {@code errorCode} (machine-readable
 * string for client error handling), an {@code httpStatus} (used by the global
 * exception handler to set the HTTP response status), and a {@code userMessage}
 * (human-readable description suitable for API responses).</p>
 *
 * <p>Prefer the static factory methods for the most common error scenarios:</p>
 * <pre>{@code
 * throw PlatformException.notFound("Vehicle", vehicleId);
 * throw PlatformException.forbidden("Insufficient permissions to access resource");
 * throw PlatformException.badRequest("startDate must be before endDate");
 * throw PlatformException.conflict("A vehicle with this plate already exists");
 * }</pre>
 */
public class PlatformException extends RuntimeException {

    /** Machine-readable error code sent to clients (e.g., {@code TENANT_CONTEXT_MISSING}). */
    private final String errorCode;

    /** HTTP status code that should be returned to the client. */
    private final int httpStatus;

    /** Human-readable description of the error, safe to expose in API responses. */
    private final String userMessage;

    /**
     * Full constructor.
     *
     * @param errorCode   machine-readable code identifying the error category
     * @param httpStatus  HTTP status code for the response
     * @param userMessage human-readable description of the error
     * @param cause       the underlying cause, or {@code null} if none
     */
    public PlatformException(String errorCode, int httpStatus, String userMessage, Throwable cause) {
        super(userMessage, cause);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
        this.userMessage = userMessage;
    }

    /**
     * Constructor without a root cause.
     *
     * @param errorCode   machine-readable code identifying the error category
     * @param httpStatus  HTTP status code for the response
     * @param userMessage human-readable description of the error
     */
    public PlatformException(String errorCode, int httpStatus, String userMessage) {
        this(errorCode, httpStatus, userMessage, null);
    }

    /**
     * Returns the machine-readable error code.
     *
     * @return non-null error code string
     */
    public String getErrorCode() {
        return errorCode;
    }

    /**
     * Returns the HTTP status code to send to the client.
     *
     * @return HTTP status code (e.g., 400, 403, 404, 409)
     */
    public int getHttpStatus() {
        return httpStatus;
    }

    /**
     * Returns the human-readable error message suitable for inclusion in API responses.
     *
     * @return user-facing message
     */
    public String getUserMessage() {
        return userMessage;
    }

    // -------------------------------------------------------------------------
    // Static factory methods
    // -------------------------------------------------------------------------

    /**
     * Creates a {@code 404 Not Found} exception indicating that a named resource
     * with the given identifier does not exist.
     *
     * @param resource the resource type (e.g., "Vehicle", "Trip")
     * @param id       the requested identifier
     * @return a {@link PlatformException} with code {@code RESOURCE_NOT_FOUND}
     */
    public static PlatformException notFound(String resource, String id) {
        return new PlatformException(
                "RESOURCE_NOT_FOUND",
                HttpStatus.NOT_FOUND.value(),
                resource + " not found with id: " + id
        );
    }

    /**
     * Creates a {@code 403 Forbidden} exception for authorization failures.
     *
     * @param message human-readable description of why access is denied
     * @return a {@link PlatformException} with code {@code FORBIDDEN}
     */
    public static PlatformException forbidden(String message) {
        return new PlatformException(
                "FORBIDDEN",
                HttpStatus.FORBIDDEN.value(),
                message
        );
    }

    /**
     * Creates a {@code 403 Forbidden} exception indicating that the tenant context
     * has not been established for the current request thread. This is used by
     * {@link com.vnpt.avplatform.shared.repository.BaseMongoRepository} to enforce
     * business rule BL-001 (every MongoDB query must include {@code tenant_id}).
     *
     * @return a {@link PlatformException} with code {@code TENANT_CONTEXT_MISSING}
     */
    public static PlatformException tenantContextMissing() {
        return new PlatformException(
                "TENANT_CONTEXT_MISSING",
                HttpStatus.FORBIDDEN.value(),
                "Tenant context is not set. All data access requires an active tenant."
        );
    }

    /**
     * Creates a {@code 400 Bad Request} exception for client input errors.
     *
     * @param message human-readable description of the validation failure
     * @return a {@link PlatformException} with code {@code BAD_REQUEST}
     */
    public static PlatformException badRequest(String message) {
        return new PlatformException(
                "BAD_REQUEST",
                HttpStatus.BAD_REQUEST.value(),
                message
        );
    }

    /**
     * Creates a {@code 409 Conflict} exception when a request conflicts with the
     * current state of the server (e.g., duplicate record).
     *
     * @param message human-readable description of the conflict
     * @return a {@link PlatformException} with code {@code CONFLICT}
     */
    public static PlatformException conflict(String message) {
        return new PlatformException(
                "CONFLICT",
                HttpStatus.CONFLICT.value(),
                message
        );
    }
}
