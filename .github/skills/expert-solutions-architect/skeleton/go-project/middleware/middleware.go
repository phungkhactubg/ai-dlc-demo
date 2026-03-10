package middleware

import (
	"strings"
	"time"

	"github.com/labstack/echo/v4"

	"{{.ModuleName}}/utils/logging"
)

// Logger returns a middleware that logs requests.
func Logger(logger *logging.Logger) echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			start := time.Now()

			// Process request
			err := next(c)

			// Log details
			req := c.Request()
			res := c.Response()

			latency := time.Since(start)

			fields := []interface{}{
				"method", req.Method,
				"path", req.URL.Path,
				"status", res.Status,
				"latency", latency.String(),
				"ip", c.RealIP(),
				"request_id", c.Response().Header().Get(echo.HeaderXRequestID),
			}

			// Add tenant if present
			if tenantID := c.Get("tenant_id"); tenantID != nil {
				fields = append(fields, "tenant_id", tenantID)
			}

			// Log based on status code
			if res.Status >= 500 {
				logger.Error("Request failed", fields...)
			} else if res.Status >= 400 {
				logger.Warn("Request error", fields...)
			} else {
				logger.Info("Request completed", fields...)
			}

			return err
		}
	}
}

// CORS returns a CORS middleware.
func CORS() echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			origin := c.Request().Header.Get("Origin")

			// Allow all origins in development
			// TODO: Configure allowed origins for production
			if origin != "" {
				c.Response().Header().Set("Access-Control-Allow-Origin", origin)
			}

			c.Response().Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
			c.Response().Header().Set("Access-Control-Allow-Headers", "Accept, Content-Type, Content-Length, Accept-Encoding, Authorization, X-Tenant-ID, X-Request-ID")
			c.Response().Header().Set("Access-Control-Allow-Credentials", "true")
			c.Response().Header().Set("Access-Control-Max-Age", "86400")

			// Handle preflight
			if c.Request().Method == "OPTIONS" {
				return c.NoContent(204)
			}

			return next(c)
		}
	}
}

// Auth returns a JWT authentication middleware.
func Auth(jwtSecret string) echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			authHeader := c.Request().Header.Get("Authorization")
			if authHeader == "" {
				return echo.NewHTTPError(401, "missing authorization header")
			}

			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || parts[0] != "Bearer" {
				return echo.NewHTTPError(401, "invalid authorization format")
			}

			token := parts[1]

			// TODO: Validate JWT token
			// claims, err := ValidateJWT(token, jwtSecret)
			// if err != nil {
			//     return echo.NewHTTPError(401, "invalid token")
			// }

			// For now, just store the token
			c.Set("token", token)

			return next(c)
		}
	}
}

// Tenant returns a multi-tenancy middleware.
func Tenant(headerName string) echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			tenantID := c.Request().Header.Get(headerName)
			if tenantID == "" {
				return echo.NewHTTPError(400, "missing tenant ID")
			}

			// Store in context
			c.Set("tenant_id", tenantID)

			// Also add to request context for downstream services
			ctx := c.Request().Context()
			// ctx = context.WithValue(ctx, "tenant_id", tenantID)
			c.SetRequest(c.Request().WithContext(ctx))

			return next(c)
		}
	}
}

// RateLimit returns a simple rate limiting middleware.
// For production, use a distributed rate limiter with Redis.
func RateLimit(requestsPerSecond int) echo.MiddlewareFunc {
	// TODO: Implement token bucket or use go.uber.org/ratelimit
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			return next(c)
		}
	}
}
