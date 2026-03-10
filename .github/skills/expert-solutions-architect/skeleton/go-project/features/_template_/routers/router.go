package _template_

import (
	"github.com/labstack/echo/v4"
)

// RegisterRoutes registers routes for this feature.
// The group should have auth and tenant middleware applied.
func RegisterRoutes(g *echo.Group, controller *EntityController) {
	// Replace "entities" with your actual resource name
	entities := g.Group("/entities")

	entities.POST("", controller.Create)
	entities.GET("", controller.List)
	entities.GET("/:id", controller.GetByID)
	entities.PUT("/:id", controller.Update)
	entities.DELETE("/:id", controller.Delete)
}
