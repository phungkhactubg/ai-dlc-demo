package response

import (
	"net/http"

	"github.com/labstack/echo/v4"
)

// Response represents a standard API response.
type Response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   *ErrorInfo  `json:"error,omitempty"`
	Meta    *Meta       `json:"meta,omitempty"`
}

// ErrorInfo represents error details.
type ErrorInfo struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// Meta represents pagination metadata.
type Meta struct {
	Page       int   `json:"page,omitempty"`
	Limit      int   `json:"limit,omitempty"`
	Total      int64 `json:"total,omitempty"`
	TotalPages int   `json:"total_pages,omitempty"`
}

// OK returns a successful response.
func OK(c echo.Context, data interface{}) error {
	return c.JSON(http.StatusOK, Response{
		Success: true,
		Data:    data,
	})
}

// Created returns a 201 response.
func Created(c echo.Context, data interface{}) error {
	return c.JSON(http.StatusCreated, Response{
		Success: true,
		Data:    data,
	})
}

// NoContent returns a 204 response.
func NoContent(c echo.Context) error {
	return c.NoContent(http.StatusNoContent)
}

// Paginated returns a paginated response.
func Paginated(c echo.Context, data interface{}, page, limit int, total int64) error {
	totalPages := int(total) / limit
	if int(total)%limit > 0 {
		totalPages++
	}

	return c.JSON(http.StatusOK, Response{
		Success: true,
		Data:    data,
		Meta: &Meta{
			Page:       page,
			Limit:      limit,
			Total:      total,
			TotalPages: totalPages,
		},
	})
}

// BadRequest returns a 400 error.
func BadRequest(c echo.Context, message string) error {
	return c.JSON(http.StatusBadRequest, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "BAD_REQUEST",
			Message: message,
		},
	})
}

// Unauthorized returns a 401 error.
func Unauthorized(c echo.Context, message string) error {
	if message == "" {
		message = "Unauthorized"
	}
	return c.JSON(http.StatusUnauthorized, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "UNAUTHORIZED",
			Message: message,
		},
	})
}

// Forbidden returns a 403 error.
func Forbidden(c echo.Context, message string) error {
	if message == "" {
		message = "Forbidden"
	}
	return c.JSON(http.StatusForbidden, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "FORBIDDEN",
			Message: message,
		},
	})
}

// NotFound returns a 404 error.
func NotFound(c echo.Context, message string) error {
	if message == "" {
		message = "Resource not found"
	}
	return c.JSON(http.StatusNotFound, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "NOT_FOUND",
			Message: message,
		},
	})
}

// Conflict returns a 409 error.
func Conflict(c echo.Context, message string) error {
	return c.JSON(http.StatusConflict, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "CONFLICT",
			Message: message,
		},
	})
}

// ValidationError returns a 422 error.
func ValidationError(c echo.Context, message string) error {
	return c.JSON(http.StatusUnprocessableEntity, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "VALIDATION_ERROR",
			Message: message,
		},
	})
}

// InternalError returns a 500 error.
func InternalError(c echo.Context, message string) error {
	if message == "" {
		message = "Internal server error"
	}
	return c.JSON(http.StatusInternalServerError, Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    "INTERNAL_ERROR",
			Message: message,
		},
	})
}
