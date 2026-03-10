package _template_

import (
	"errors"
	"net/http"
	"strconv"

	"github.com/labstack/echo/v4"
)

// EntityController handles HTTP requests for entities.
type EntityController struct {
	service IEntityService
}

// NewEntityController creates a new controller.
func NewEntityController(service IEntityService) *EntityController {
	return &EntityController{service: service}
}

// Create handles POST requests to create an entity.
func (c *EntityController) Create(ctx echo.Context) error {
	var req CreateEntityRequest
	if err := ctx.Bind(&req); err != nil {
		return c.respondError(ctx, http.StatusBadRequest, "INVALID_REQUEST", "invalid request body")
	}

	if err := ctx.Validate(req); err != nil {
		return c.respondError(ctx, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
	}

	entity, err := c.service.Create(ctx.Request().Context(), req)
	if err != nil {
		return c.handleError(ctx, err)
	}

	return ctx.JSON(http.StatusCreated, map[string]any{
		"success": true,
		"data":    ToResponse(entity),
	})
}

// GetByID handles GET requests for a single entity.
func (c *EntityController) GetByID(ctx echo.Context) error {
	id := ctx.Param("id")

	entity, err := c.service.GetByID(ctx.Request().Context(), id)
	if err != nil {
		return c.handleError(ctx, err)
	}

	return ctx.JSON(http.StatusOK, map[string]any{
		"success": true,
		"data":    ToResponse(entity),
	})
}

// List handles GET requests for listing entities.
func (c *EntityController) List(ctx echo.Context) error {
	tenantID, _ := ctx.Get("tenant_id").(string)

	filter := EntityFilter{
		TenantID: tenantID,
		Status:   ctx.QueryParam("status"),
		Search:   ctx.QueryParam("search"),
		Page:     c.parseIntParam(ctx, "page", 1),
		Limit:    c.parseIntParam(ctx, "limit", 20),
	}

	// Limit max page size
	if filter.Limit > 100 {
		filter.Limit = 100
	}

	entities, total, err := c.service.List(ctx.Request().Context(), filter)
	if err != nil {
		return c.handleError(ctx, err)
	}

	return ctx.JSON(http.StatusOK, map[string]any{
		"success": true,
		"data":    ToListResponse(entities, filter.Page, filter.Limit, total),
	})
}

// Update handles PUT requests to update an entity.
func (c *EntityController) Update(ctx echo.Context) error {
	id := ctx.Param("id")

	var req UpdateEntityRequest
	if err := ctx.Bind(&req); err != nil {
		return c.respondError(ctx, http.StatusBadRequest, "INVALID_REQUEST", "invalid request body")
	}

	entity, err := c.service.Update(ctx.Request().Context(), id, req)
	if err != nil {
		return c.handleError(ctx, err)
	}

	return ctx.JSON(http.StatusOK, map[string]any{
		"success": true,
		"data":    ToResponse(entity),
	})
}

// Delete handles DELETE requests.
func (c *EntityController) Delete(ctx echo.Context) error {
	id := ctx.Param("id")

	if err := c.service.Delete(ctx.Request().Context(), id); err != nil {
		return c.handleError(ctx, err)
	}

	return ctx.NoContent(http.StatusNoContent)
}

// handleError maps domain errors to HTTP responses.
func (c *EntityController) handleError(ctx echo.Context, err error) error {
	switch {
	case errors.Is(err, ErrEntityNotFound):
		return c.respondError(ctx, http.StatusNotFound, "NOT_FOUND", "entity not found")
	case errors.Is(err, ErrDuplicateName):
		return c.respondError(ctx, http.StatusConflict, "CONFLICT", "entity name already exists")
	case errors.Is(err, ErrUnauthorized):
		return c.respondError(ctx, http.StatusUnauthorized, "UNAUTHORIZED", "unauthorized")
	case errors.Is(err, ErrForbidden):
		return c.respondError(ctx, http.StatusForbidden, "FORBIDDEN", "forbidden")
	case errors.Is(err, ErrInvalidInput):
		return c.respondError(ctx, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
	default:
		// Log internal error
		ctx.Logger().Error(err)
		return c.respondError(ctx, http.StatusInternalServerError, "INTERNAL_ERROR", "internal server error")
	}
}

// respondError sends a structured error response.
func (c *EntityController) respondError(ctx echo.Context, status int, code, message string) error {
	return ctx.JSON(status, map[string]any{
		"success": false,
		"error": map[string]string{
			"code":    code,
			"message": message,
		},
	})
}

// parseIntParam parses an integer query parameter with a default value.
func (c *EntityController) parseIntParam(ctx echo.Context, name string, defaultVal int) int {
	val := ctx.QueryParam(name)
	if val == "" {
		return defaultVal
	}
	intVal, err := strconv.Atoi(val)
	if err != nil {
		return defaultVal
	}
	return intVal
}
