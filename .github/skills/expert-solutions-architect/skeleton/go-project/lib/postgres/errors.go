package postgres

import "errors"

// PostgreSQL-specific errors.
var (
	// ErrNotFound indicates the row was not found.
	ErrNotFound = errors.New("row not found")

	// ErrDuplicateKey indicates a unique constraint violation.
	ErrDuplicateKey = errors.New("duplicate key error")

	// ErrConnectionFailed indicates a connection error.
	ErrConnectionFailed = errors.New("connection failed")

	// ErrTransactionFailed indicates transaction failed.
	ErrTransactionFailed = errors.New("transaction failed")
)
