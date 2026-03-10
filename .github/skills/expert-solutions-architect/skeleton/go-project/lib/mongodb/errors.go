package mongodb

import "errors"

// MongoDB-specific errors.
var (
	// ErrNotFound indicates the document was not found.
	ErrNotFound = errors.New("document not found")

	// ErrDuplicateKey indicates a unique constraint violation.
	ErrDuplicateKey = errors.New("duplicate key error")

	// ErrInvalidID indicates the provided ID is invalid.
	ErrInvalidID = errors.New("invalid document id")

	// ErrConnectionFailed indicates a connection error.
	ErrConnectionFailed = errors.New("connection failed")
)
