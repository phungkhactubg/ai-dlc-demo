package redis

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

// Lock provides distributed locking.
type Lock struct {
	client redis.Cmdable
	prefix string
}

// NewLock creates a new lock instance.
func NewLock(client *Client) *Lock {
	return &Lock{
		client: client.rdb,
		prefix: "lock:",
	}
}

// NewClusterLock creates a lock for Redis Cluster.
func NewClusterLock(client *ClusterClient) *Lock {
	return &Lock{
		client: client.rdb,
		prefix: "lock:",
	}
}

func (l *Lock) key(k string) string {
	return l.prefix + k
}

// Acquire attempts to acquire a lock.
// Returns the lock value (needed for release) and whether it was acquired.
func (l *Lock) Acquire(ctx context.Context, key string, ttl time.Duration) (string, bool, error) {
	lockValue := uuid.New().String()
	acquired, err := l.client.SetNX(ctx, l.key(key), lockValue, ttl).Result()
	if err != nil {
		return "", false, fmt.Errorf("acquire lock failed: %w", err)
	}
	if !acquired {
		return "", false, nil
	}
	return lockValue, true, nil
}

// Release releases a lock.
// Only releases if the lock value matches (owner verification).
func (l *Lock) Release(ctx context.Context, key, lockValue string) error {
	// Lua script for atomic check-and-delete
	script := `
		if redis.call("get", KEYS[1]) == ARGV[1] then
			return redis.call("del", KEYS[1])
		else
			return 0
		end
	`
	_, err := l.client.Eval(ctx, script, []string{l.key(key)}, lockValue).Result()
	if err != nil {
		return fmt.Errorf("release lock failed: %w", err)
	}
	return nil
}

// Extend extends the TTL of a held lock.
func (l *Lock) Extend(ctx context.Context, key, lockValue string, ttl time.Duration) (bool, error) {
	// Lua script for atomic check-and-extend
	script := `
		if redis.call("get", KEYS[1]) == ARGV[1] then
			return redis.call("pexpire", KEYS[1], ARGV[2])
		else
			return 0
		end
	`
	result, err := l.client.Eval(ctx, script, []string{l.key(key)}, lockValue, ttl.Milliseconds()).Result()
	if err != nil {
		return false, fmt.Errorf("extend lock failed: %w", err)
	}
	return result.(int64) == 1, nil
}

// WithLock executes a function while holding a lock.
// Automatically releases the lock when done.
func (l *Lock) WithLock(ctx context.Context, key string, ttl time.Duration, fn func() error) error {
	lockValue, acquired, err := l.Acquire(ctx, key, ttl)
	if err != nil {
		return err
	}
	if !acquired {
		return ErrLockNotAcquired
	}

	defer func() {
		// Use background context for cleanup
		releaseCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = l.Release(releaseCtx, key, lockValue)
	}()

	return fn()
}

// TryWithLock attempts to acquire a lock with retries.
func (l *Lock) TryWithLock(ctx context.Context, key string, ttl time.Duration, maxRetries int, retryDelay time.Duration, fn func() error) error {
	var lastErr error

	for i := 0; i <= maxRetries; i++ {
		lockValue, acquired, err := l.Acquire(ctx, key, ttl)
		if err != nil {
			return err
		}

		if acquired {
			defer func() {
				releaseCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				defer cancel()
				_ = l.Release(releaseCtx, key, lockValue)
			}()
			return fn()
		}

		lastErr = ErrLockNotAcquired

		// Wait before retry
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(retryDelay):
		}
	}

	return fmt.Errorf("failed after %d retries: %w", maxRetries, lastErr)
}

// IsLocked checks if a lock is held.
func (l *Lock) IsLocked(ctx context.Context, key string) (bool, error) {
	result, err := l.client.Exists(ctx, l.key(key)).Result()
	if err != nil {
		return false, fmt.Errorf("check lock failed: %w", err)
	}
	return result > 0, nil
}
