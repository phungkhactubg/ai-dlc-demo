package com.vnpt.avplatform.shared;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.interceptor.TenantInterceptor;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Collections;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for {@link TenantInterceptor}.
 *
 * <p>Uses Spring's {@link MockHttpServletRequest} and {@link MockHttpServletResponse}
 * to exercise the interceptor without starting a full application context.</p>
 */
@DisplayName("TenantInterceptor")
class TenantInterceptorTest {

    private TenantInterceptor interceptor;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        interceptor = new TenantInterceptor(objectMapper);
        TenantContext.clear();
        SecurityContextHolder.clearContext();
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
        SecurityContextHolder.clearContext();
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    /** Sets an authenticated user in the Spring Security context. */
    private void setAuthenticatedUser(String username) {
        UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(username, null, Collections.emptyList());
        SecurityContextHolder.getContext().setAuthentication(auth);
    }

    /** Builds a mock request with or without the X-Tenant-ID header. */
    private MockHttpServletRequest requestWithTenant(String tenantId) {
        MockHttpServletRequest request = new MockHttpServletRequest();
        if (tenantId != null) {
            request.addHeader(TenantInterceptor.TENANT_HEADER, tenantId);
        }
        return request;
    }

    // -------------------------------------------------------------------------
    // preHandle — tenant header present
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("preHandle — with X-Tenant-ID header")
    class WithTenantHeader {

        @Test
        @DisplayName("returns true when header is present (unauthenticated request)")
        void returnsTrue_whenHeaderPresent_unauthenticated() throws Exception {
            MockHttpServletRequest request = requestWithTenant("tenant-abc");
            MockHttpServletResponse response = new MockHttpServletResponse();
            boolean result = interceptor.preHandle(request, response, new Object());
            assertThat(result).isTrue();
        }

        @Test
        @DisplayName("sets TenantContext when header is present")
        void setsTenantContext_whenHeaderPresent() throws Exception {
            MockHttpServletRequest request = requestWithTenant("tenant-xyz");
            interceptor.preHandle(request, new MockHttpServletResponse(), new Object());
            assertThat(TenantContext.getTenantId()).isEqualTo("tenant-xyz");
        }

        @Test
        @DisplayName("trims whitespace from header value before storing")
        void trimsTenantIdFromHeader() throws Exception {
            MockHttpServletRequest request = new MockHttpServletRequest();
            request.addHeader(TenantInterceptor.TENANT_HEADER, "  tenant-padded  ");
            interceptor.preHandle(request, new MockHttpServletResponse(), new Object());
            assertThat(TenantContext.getTenantId()).isEqualTo("tenant-padded");
        }

        @Test
        @DisplayName("returns true and sets context even for authenticated request with header")
        void returnsTrue_authenticated_withHeader() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletRequest request = requestWithTenant("tenant-auth");
            MockHttpServletResponse response = new MockHttpServletResponse();
            boolean result = interceptor.preHandle(request, response, new Object());
            assertThat(result).isTrue();
            assertThat(TenantContext.getTenantId()).isEqualTo("tenant-auth");
        }

        @Test
        @DisplayName("does not set error status when header is present")
        void noErrorStatus_whenHeaderPresent() throws Exception {
            MockHttpServletRequest request = requestWithTenant("t-1");
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(request, response, new Object());
            assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());
        }
    }

    // -------------------------------------------------------------------------
    // preHandle — authenticated, no tenant header → 400
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("preHandle — authenticated request without X-Tenant-ID header")
    class AuthenticatedWithoutTenantHeader {

        @Test
        @DisplayName("returns false when authenticated and header is missing")
        void returnsFalse_whenAuthenticated_noHeader() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletRequest request = requestWithTenant(null);
            MockHttpServletResponse response = new MockHttpServletResponse();
            boolean result = interceptor.preHandle(request, response, new Object());
            assertThat(result).isFalse();
        }

        @Test
        @DisplayName("writes HTTP 400 status when authenticated and header is missing")
        void writes400Status_whenAuthenticated_noHeader() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletRequest request = requestWithTenant(null);
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(request, response, new Object());
            assertThat(response.getStatus()).isEqualTo(HttpStatus.BAD_REQUEST.value());
        }

        @Test
        @DisplayName("writes application/json content-type when rejecting request")
        void writesJsonContentType_onRejection() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletRequest request = requestWithTenant(null);
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(request, response, new Object());
            assertThat(response.getContentType()).contains("application/json");
        }

        @Test
        @DisplayName("response body contains MISSING_TENANT_HEADER error code")
        void responseBody_containsErrorCode() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletRequest request = requestWithTenant(null);
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(request, response, new Object());
            String body = response.getContentAsString();
            assertThat(body).contains("MISSING_TENANT_HEADER");
        }

        @Test
        @DisplayName("TenantContext remains null after rejection")
        void tenantContextNull_afterRejection() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            interceptor.preHandle(requestWithTenant(null), new MockHttpServletResponse(), new Object());
            assertThat(TenantContext.getTenantId()).isNull();
        }

        @Test
        @DisplayName("response body contains traceId field")
        void responseBody_containsTraceId() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(requestWithTenant(null), response, new Object());
            assertThat(response.getContentAsString()).contains("traceId");
        }

        @Test
        @DisplayName("response body has success=false")
        void responseBody_hasSuccessFalse() throws Exception {
            setAuthenticatedUser("user@vnpt.vn");
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(requestWithTenant(null), response, new Object());
            assertThat(response.getContentAsString()).contains("\"success\":false");
        }
    }

    // -------------------------------------------------------------------------
    // preHandle — unauthenticated, no header → allow through
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("preHandle — unauthenticated request without X-Tenant-ID header")
    class UnauthenticatedWithoutTenantHeader {

        @Test
        @DisplayName("returns true for unauthenticated request without header")
        void returnsTrue_unauthenticated_noHeader() throws Exception {
            MockHttpServletRequest request = requestWithTenant(null);
            MockHttpServletResponse response = new MockHttpServletResponse();
            boolean result = interceptor.preHandle(request, response, new Object());
            assertThat(result).isTrue();
        }

        @Test
        @DisplayName("does not write error response for unauthenticated request")
        void noErrorResponse_unauthenticated_noHeader() throws Exception {
            MockHttpServletResponse response = new MockHttpServletResponse();
            interceptor.preHandle(requestWithTenant(null), response, new Object());
            assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());
        }

        @Test
        @DisplayName("TenantContext remains null for unauthenticated request without header")
        void tenantContextNull_unauthenticated_noHeader() throws Exception {
            interceptor.preHandle(requestWithTenant(null), new MockHttpServletResponse(), new Object());
            assertThat(TenantContext.getTenantId()).isNull();
        }
    }

    // -------------------------------------------------------------------------
    // afterCompletion — always clears context
    // -------------------------------------------------------------------------

    @Nested
    @DisplayName("afterCompletion — always clears TenantContext")
    class AfterCompletionTests {

        @Test
        @DisplayName("clears TenantContext on successful request completion")
        void clearsTenantContext_onSuccess() throws Exception {
            TenantContext.setTenantId("pre-set-tenant");
            interceptor.afterCompletion(
                    new MockHttpServletRequest(),
                    new MockHttpServletResponse(),
                    new Object(),
                    null
            );
            assertThat(TenantContext.getTenantId()).isNull();
        }

        @Test
        @DisplayName("clears TenantContext even when an exception occurred")
        void clearsTenantContext_onException() throws Exception {
            TenantContext.setTenantId("pre-set-tenant");
            interceptor.afterCompletion(
                    new MockHttpServletRequest(),
                    new MockHttpServletResponse(),
                    new Object(),
                    new RuntimeException("simulated error")
            );
            assertThat(TenantContext.getTenantId()).isNull();
        }

        @Test
        @DisplayName("clears TenantContext when context was never set")
        void clearsTenantContext_whenContextNeverSet() throws Exception {
            // No setTenantId call — must not throw
            interceptor.afterCompletion(
                    new MockHttpServletRequest(),
                    new MockHttpServletResponse(),
                    new Object(),
                    null
            );
            assertThat(TenantContext.getTenantId()).isNull();
        }

        @Test
        @DisplayName("preHandle then afterCompletion leaves context null")
        void fullCycle_preHandleThenAfterCompletion_leavesNull() throws Exception {
            MockHttpServletRequest request = requestWithTenant("cycle-tenant");
            interceptor.preHandle(request, new MockHttpServletResponse(), new Object());
            assertThat(TenantContext.getTenantId()).isEqualTo("cycle-tenant");

            interceptor.afterCompletion(request, new MockHttpServletResponse(), new Object(), null);
            assertThat(TenantContext.getTenantId()).isNull();
        }
    }

    // -------------------------------------------------------------------------
    // Constructor validation
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("constructor throws IllegalArgumentException when objectMapper is null")
    void constructor_throwsOnNullObjectMapper() {
        org.junit.jupiter.api.Assertions.assertThrows(
                IllegalArgumentException.class,
                () -> new TenantInterceptor(null)
        );
    }
}
