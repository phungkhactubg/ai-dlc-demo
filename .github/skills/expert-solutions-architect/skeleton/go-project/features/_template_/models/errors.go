package _template_

import "errors"

// Domain-specific errors.
var (
	// ErrEntityNotFound indicates the entity was not found.
	ErrEntityNotFound = errors.New("entity not found")

	// ErrDuplicateName indicates a name already exists.
	ErrDuplicateName = errors.New("entity name already exists")

	// ErrInvalidInput indicates invalid input data.
	ErrInvalidInput = errors.New("invalid input")

	// ErrUnauthorized indicates unauthorized access.
	ErrUnauthorized = errors.New("unauthorized")

	// ErrForbidden indicates forbidden access.
	ErrForbidden = errors.New("forbidden")
)
