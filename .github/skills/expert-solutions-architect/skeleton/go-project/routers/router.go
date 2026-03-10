package routers

import (
	"context"
	"fmt"

	"github.com/labstack/echo/v4"

	"{{.ModuleName}}/config"
	"{{.ModuleName}}/lib/mongodb"
	"{{.ModuleName}}/lib/redis"
	appMiddleware "{{.ModuleName}}/middleware"
)

// Dependencies holds all application dependencies.
type Dependencies struct {
	MongoDB *mongodb.Client
	Redis   *redis.Client
	// Add more dependencies as needed
}

// InitializeDependencies creates all dependencies.
func InitializeDependencies(ctx context.Context, cfg *config.Config) (*Dependencies, error) {
	deps := &Dependencies{}

	// Initialize MongoDB
	mongoCfg := mongodb.Config{
		URI:            cfg.MongoDB.URI,
		Database:       cfg.MongoDB.Database,
		ConnectTimeout: cfg.MongoDB.ConnectTimeout,
		MaxPoolSize:    cfg.MongoDB.MaxPoolSize,
	}
	mongoClient, err := mongodb.NewClient(ctx, mongoCfg)
	if err != nil {
		return nil, fmt.Errorf("mongodb init failed: %w", err)
	}
	deps.MongoDB = mongoClient

	// Initialize Redis
	redisCfg := redis.Config{
		Addr:     cfg.Redis.Addr,
		Password: cfg.Redis.Password,
		DB:       cfg.Redis.DB,
		PoolSize: cfg.Redis.PoolSize,
	}
	redisClient, err := redis.NewClient(ctx, redisCfg)
	if err != nil {
		return nil, fmt.Errorf("redis init failed: %w", err)
	}
	deps.Redis = redisClient

	return deps, nil
}

// Close closes all dependencies.
func (d *Dependencies) Close() {
	if d.MongoDB != nil {
		_ = d.MongoDB.Close(context.Background())
	}
	if d.Redis != nil {
		_ = d.Redis.Close()
	}
}

// RegisterRoutes registers all routes.
func RegisterRoutes(e *echo.Echo, deps *Dependencies, cfg *config.Config) {
	// Health check (no auth required)
	e.GET("/health", healthCheck(deps))
	e.GET("/ready", readinessCheck(deps))

	// API v1 group
	v1 := e.Group("/api/v1")

	// Apply authentication middleware
	// NOTE: The deprecated middleware.Auth() has been removed.
	// Use one of the following patterns for authentication:
	//
	// Option 1: SSC Auth Middleware (recommended for AV Platform)
	//   import ssc_middleware "{{.ModuleName}}/features/ssc/middleware"
	//   authMW := ssc_middleware.NewAuthMiddleware(authService)
	//   v1.Use(authMW.Middleware)
	//
	// Option 2: Custom JWT Middleware
	//   Implement your own middleware that verifies JWT tokens using
	//   your preferred JWT library (e.g., golang-jwt/jwt/v5)
	//
	// See middleware/middleware.go for migration guide

	// Apply tenant middleware for multi-tenancy support
	v1.Use(appMiddleware.Tenant(cfg.Auth.TenantHeader))

	// Register feature routes
	// Example: RegisterFeatureRoutes(v1, deps)
}

func healthCheck(deps *Dependencies) echo.HandlerFunc {
	return func(c echo.Context) error {
		return c.JSON(200, map[string]string{
			"status": "healthy",
		})
	}
}

func readinessCheck(deps *Dependencies) echo.HandlerFunc {
	return func(c echo.Context) error {
		ctx := c.Request().Context()

		// Check MongoDB
		if err := deps.MongoDB.Health(ctx); err != nil {
			return c.JSON(503, map[string]string{
				"status": "not ready",
				"error":  "mongodb unavailable",
			})
		}

		// Check Redis
		if err := deps.Redis.Health(ctx); err != nil {
			return c.JSON(503, map[string]string{
				"status": "not ready",
				"error":  "redis unavailable",
			})
		}

		return c.JSON(200, map[string]string{
			"status": "ready",
		})
	}
}
