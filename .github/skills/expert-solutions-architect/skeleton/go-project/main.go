package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"

	"{{.ModuleName}}/config"
	appMiddleware "{{.ModuleName}}/middleware"
	"{{.ModuleName}}/routers"
	"{{.ModuleName}}/utils/logging"
)

func main() {
	// Initialize logger
	logger := logging.NewLogger()
	logger.Info("Starting application...")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		logger.Error("Failed to load config", "error", err)
		os.Exit(1)
	}

	// Create Echo instance
	e := echo.New()
	e.HideBanner = true
	e.HidePort = true

	// Apply global middleware
	e.Use(middleware.Recover())
	e.Use(middleware.RequestID())
	e.Use(appMiddleware.Logger(logger))
	e.Use(appMiddleware.CORS())

	// Initialize dependencies
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	deps, err := routers.InitializeDependencies(ctx, cfg)
	if err != nil {
		logger.Error("Failed to initialize dependencies", "error", err)
		os.Exit(1)
	}
	defer deps.Close()

	// Register routes
	routers.RegisterRoutes(e, deps, cfg)

	// Start server
	go func() {
		addr := fmt.Sprintf(":%d", cfg.Server.Port)
		logger.Info("Server starting", "address", addr)
		if err := e.Start(addr); err != nil && err != http.ErrServerClosed {
			logger.Error("Server error", "error", err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := e.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server shutdown error", "error", err)
	}

	logger.Info("Server stopped")
}
