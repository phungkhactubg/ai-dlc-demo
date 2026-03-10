package com.vnpt.avplatform.shared;

import com.vnpt.avplatform.shared.exception.PlatformException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Unit tests for {@link PlatformException}.
 *
 * <p>Validates all constructors and static factory methods, error codes,
 * HTTP statuses, and exception hierarchy.</p>
 */
@DisplayName("PlatformException")
class PlatformExceptionTest {

    // -------------------------------------------------------------------------
    // notFound()
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("notFound factory method")
    class NotFoundTests {

        @Test
        @DisplayName("returns exception with RESOURCE_NOT_FOUND error code")
        void notFound_hasCorrectErrorCode() {
            PlatformException ex = PlatformException.notFound("Vehicle", "v-123");
            assertThat(ex.getErrorCode()).isEqualTo("RESOURCE_NOT_FOUND");
        }

        @Test
        @DisplayName("returns exception with HTTP 404 status")
        void notFound_hasHttp404Status() {
            PlatformException ex = PlatformException.notFound("Trip", "t-456");
            assertThat(ex.getHttpStatus()).isEqualTo(HttpStatus.NOT_FOUND.value());
        }

        @Test
        @DisplayName("user message contains resource name and id")
        void notFound_userMessageContainsResourceAndId() {
            PlatformException ex = PlatformException.notFound("Driver", "d-789");
            assertThat(ex.getUserMessage()).contains("Driver").contains("d-789");
        }

        @Test
        @DisplayName("getMessage() equals userMessage")
        void notFound_getMessageEqualsUserMessage() {
            PlatformException ex = PlatformException.notFound("Order", "o-001");
            assertThat(ex.getMessage()).isEqualTo(ex.getUserMessage());
        }

        @Test
        @DisplayName("is a RuntimeException subtype")
        void notFound_isRuntimeException() {
            PlatformException ex = PlatformException.notFound("Zone", "z-1");
            assertThat(ex).isInstanceOf(RuntimeException.class);
        }

        @Test
        @DisplayName("cause is null when no cause is provided")
        void notFound_causeIsNull() {
            PlatformException ex = PlatformException.notFound("Sensor", "s-1");
            assertThat(ex.getCause()).isNull();
        }
    }

    // -------------------------------------------------------------------------
    // forbidden()
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("forbidden factory method")
    class ForbiddenTests {

        @Test
        @DisplayName("returns exception with FORBIDDEN error code")
        void forbidden_hasCorrectErrorCode() {
            PlatformException ex = PlatformException.forbidden("Access denied");
            assertThat(ex.getErrorCode()).isEqualTo("FORBIDDEN");
        }

        @Test
        @DisplayName("returns exception with HTTP 403 status")
        void forbidden_hasHttp403Status() {
            PlatformException ex = PlatformException.forbidden("Unauthorized tenant access");
            assertThat(ex.getHttpStatus()).isEqualTo(HttpStatus.FORBIDDEN.value());
        }

        @Test
        @DisplayName("user message matches the provided message")
        void forbidden_userMessageMatchesInput() {
            String msg = "You do not have access to this resource";
            PlatformException ex = PlatformException.forbidden(msg);
            assertThat(ex.getUserMessage()).isEqualTo(msg);
        }
    }

    // -------------------------------------------------------------------------
    // tenantContextMissing()
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("tenantContextMissing factory method")
    class TenantContextMissingTests {

        @Test
        @DisplayName("returns exception with TENANT_CONTEXT_MISSING error code")
        void tenantContextMissing_hasCorrectErrorCode() {
            PlatformException ex = PlatformException.tenantContextMissing();
            assertThat(ex.getErrorCode()).isEqualTo("TENANT_CONTEXT_MISSING");
        }

        @Test
        @DisplayName("returns exception with HTTP 403 status")
        void tenantContextMissing_hasHttp403Status() {
            PlatformException ex = PlatformException.tenantContextMissing();
            assertThat(ex.getHttpStatus()).isEqualTo(HttpStatus.FORBIDDEN.value());
        }

        @Test
        @DisplayName("user message mentions tenant context")
        void tenantContextMissing_userMessageMentionsTenant() {
            PlatformException ex = PlatformException.tenantContextMissing();
            assertThat(ex.getUserMessage().toLowerCase()).contains("tenant");
        }
    }

    // -------------------------------------------------------------------------
    // badRequest()
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("badRequest factory method")
    class BadRequestTests {

        @Test
        @DisplayName("returns exception with BAD_REQUEST error code")
        void badRequest_hasCorrectErrorCode() {
            PlatformException ex = PlatformException.badRequest("Invalid input");
            assertThat(ex.getErrorCode()).isEqualTo("BAD_REQUEST");
        }

        @Test
        @DisplayName("returns exception with HTTP 400 status")
        void badRequest_hasHttp400Status() {
            PlatformException ex = PlatformException.badRequest("Date range is invalid");
            assertThat(ex.getHttpStatus()).isEqualTo(HttpStatus.BAD_REQUEST.value());
        }

        @Test
        @DisplayName("user message matches the provided message")
        void badRequest_userMessageMatchesInput() {
            String msg = "startDate must be before endDate";
            PlatformException ex = PlatformException.badRequest(msg);
            assertThat(ex.getUserMessage()).isEqualTo(msg);
        }
    }

    // -------------------------------------------------------------------------
    // conflict()
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("conflict factory method")
    class ConflictTests {

        @Test
        @DisplayName("returns exception with CONFLICT error code")
        void conflict_hasCorrectErrorCode() {
            PlatformException ex = PlatformException.conflict("Duplicate vehicle plate");
            assertThat(ex.getErrorCode()).isEqualTo("CONFLICT");
        }

        @Test
        @DisplayName("returns exception with HTTP 409 status")
        void conflict_hasHttp409Status() {
            PlatformException ex = PlatformException.conflict("Email already registered");
            assertThat(ex.getHttpStatus()).isEqualTo(HttpStatus.CONFLICT.value());
        }

        @Test
        @DisplayName("user message matches the provided message")
        void conflict_userMessageMatchesInput() {
            String msg = "A vehicle with plate 51A-123.45 already exists";
            PlatformException ex = PlatformException.conflict(msg);
            assertThat(ex.getUserMessage()).isEqualTo(msg);
        }
    }

    // -------------------------------------------------------------------------
    // Full constructor (with cause)
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("full constructor (with cause)")
    class FullConstructorTests {

        @Test
        @DisplayName("wraps root cause correctly")
        void fullConstructor_wrapsRootCause() {
            RuntimeException root = new RuntimeException("db error");
            PlatformException ex = new PlatformException("DB_ERROR", 500, "Database error", root);
            assertThat(ex.getCause()).isSameAs(root);
        }

        @Test
        @DisplayName("stores all fields correctly")
        void fullConstructor_storesAllFields() {
            PlatformException ex = new PlatformException("MY_CODE", 422, "Unprocessable", null);
            assertThat(ex.getErrorCode()).isEqualTo("MY_CODE");
            assertThat(ex.getHttpStatus()).isEqualTo(422);
            assertThat(ex.getUserMessage()).isEqualTo("Unprocessable");
        }
    }

    // -------------------------------------------------------------------------
    // General exception properties
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("can be caught as RuntimeException")
    void canBeCaughtAsRuntimeException() {
        assertThatThrownBy(() -> {
            throw PlatformException.notFound("Resource", "id-1");
        }).isInstanceOf(RuntimeException.class)
          .isInstanceOf(PlatformException.class);
    }

    @Test
    @DisplayName("every factory method returns non-null exception")
    void allFactories_returnNonNull() {
        assertThat(PlatformException.notFound("R", "1")).isNotNull();
        assertThat(PlatformException.forbidden("msg")).isNotNull();
        assertThat(PlatformException.tenantContextMissing()).isNotNull();
        assertThat(PlatformException.badRequest("msg")).isNotNull();
        assertThat(PlatformException.conflict("msg")).isNotNull();
    }
}
