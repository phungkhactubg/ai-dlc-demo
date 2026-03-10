package redis

import "errors"

// Redis-specific errors.
var (
	// ErrCacheMiss indicates the key was not found.
	ErrCacheMiss = errors.New("cache miss")

	// ErrLockNotAcquired indicates the lock could not be acquired.
	ErrLockNotAcquired = errors.New("lock not acquired")

	// ErrConnectionFailed indicates a connection error.
	ErrConnectionFailed = errors.New("connection failed")
)
