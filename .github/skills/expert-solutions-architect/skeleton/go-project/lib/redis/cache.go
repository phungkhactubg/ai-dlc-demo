package redis

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// Cache provides caching operations.
type Cache struct {
	client redis.Cmdable
	prefix string
}

// NewCache creates a new cache instance.
func NewCache(client *Client) *Cache {
	return &Cache{
		client: client.rdb,
		prefix: "",
	}
}

// NewClusterCache creates a cache for Redis Cluster.
func NewClusterCache(client *ClusterClient) *Cache {
	return &Cache{
		client: client.rdb,
		prefix: "",
	}
}

// WithPrefix sets a key prefix for namespacing.
func (c *Cache) WithPrefix(prefix string) *Cache {
	return &Cache{
		client: c.client,
		prefix: prefix + ":",
	}
}

func (c *Cache) key(k string) string {
	return c.prefix + k
}

// Set stores a value with TTL.
func (c *Cache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("marshal failed: %w", err)
	}
	return c.client.Set(ctx, c.key(key), data, ttl).Err()
}

// SetString stores a string value with TTL.
func (c *Cache) SetString(ctx context.Context, key, value string, ttl time.Duration) error {
	return c.client.Set(ctx, c.key(key), value, ttl).Err()
}

// Get retrieves a value and unmarshals it.
func (c *Cache) Get(ctx context.Context, key string, dest interface{}) error {
	data, err := c.client.Get(ctx, c.key(key)).Bytes()
	if err != nil {
		if err == redis.Nil {
			return ErrCacheMiss
		}
		return fmt.Errorf("get failed: %w", err)
	}
	return json.Unmarshal(data, dest)
}

// GetString retrieves a string value.
func (c *Cache) GetString(ctx context.Context, key string) (string, error) {
	val, err := c.client.Get(ctx, c.key(key)).Result()
	if err != nil {
		if err == redis.Nil {
			return "", ErrCacheMiss
		}
		return "", fmt.Errorf("get string failed: %w", err)
	}
	return val, nil
}

// Delete removes a key.
func (c *Cache) Delete(ctx context.Context, keys ...string) error {
	prefixedKeys := make([]string, len(keys))
	for i, k := range keys {
		prefixedKeys[i] = c.key(k)
	}
	return c.client.Del(ctx, prefixedKeys...).Err()
}

// Exists checks if a key exists.
func (c *Cache) Exists(ctx context.Context, key string) (bool, error) {
	result, err := c.client.Exists(ctx, c.key(key)).Result()
	if err != nil {
		return false, fmt.Errorf("exists check failed: %w", err)
	}
	return result > 0, nil
}

// Expire sets expiration on an existing key.
func (c *Cache) Expire(ctx context.Context, key string, ttl time.Duration) error {
	return c.client.Expire(ctx, c.key(key), ttl).Err()
}

// TTL returns the remaining TTL of a key.
func (c *Cache) TTL(ctx context.Context, key string) (time.Duration, error) {
	return c.client.TTL(ctx, c.key(key)).Result()
}

// Incr increments a counter.
func (c *Cache) Incr(ctx context.Context, key string) (int64, error) {
	return c.client.Incr(ctx, c.key(key)).Result()
}

// IncrBy increments a counter by a value.
func (c *Cache) IncrBy(ctx context.Context, key string, value int64) (int64, error) {
	return c.client.IncrBy(ctx, c.key(key), value).Result()
}

// SetNX sets a value only if it doesn't exist.
func (c *Cache) SetNX(ctx context.Context, key string, value interface{}, ttl time.Duration) (bool, error) {
	data, err := json.Marshal(value)
	if err != nil {
		return false, fmt.Errorf("marshal failed: %w", err)
	}
	return c.client.SetNX(ctx, c.key(key), data, ttl).Result()
}

// GetOrSet gets a value or sets it using the provider function.
func (c *Cache) GetOrSet(ctx context.Context, key string, dest interface{}, ttl time.Duration, provider func() (interface{}, error)) error {
	// Try to get from cache
	err := c.Get(ctx, key, dest)
	if err == nil {
		return nil
	}
	if err != ErrCacheMiss {
		return err
	}

	// Cache miss - get from provider
	value, err := provider()
	if err != nil {
		return fmt.Errorf("provider failed: %w", err)
	}

	// Store in cache
	if err := c.Set(ctx, key, value, ttl); err != nil {
		return fmt.Errorf("cache set failed: %w", err)
	}

	// Unmarshal to destination
	data, _ := json.Marshal(value)
	return json.Unmarshal(data, dest)
}

// HSet sets hash fields.
func (c *Cache) HSet(ctx context.Context, key string, values map[string]interface{}) error {
	args := make([]interface{}, 0, len(values)*2)
	for k, v := range values {
		data, err := json.Marshal(v)
		if err != nil {
			return fmt.Errorf("marshal field %s failed: %w", k, err)
		}
		args = append(args, k, data)
	}
	return c.client.HSet(ctx, c.key(key), args...).Err()
}

// HGet gets a hash field.
func (c *Cache) HGet(ctx context.Context, key, field string, dest interface{}) error {
	data, err := c.client.HGet(ctx, c.key(key), field).Bytes()
	if err != nil {
		if err == redis.Nil {
			return ErrCacheMiss
		}
		return fmt.Errorf("hget failed: %w", err)
	}
	return json.Unmarshal(data, dest)
}

// HGetAll gets all hash fields.
func (c *Cache) HGetAll(ctx context.Context, key string) (map[string]string, error) {
	return c.client.HGetAll(ctx, c.key(key)).Result()
}

// HDel deletes hash fields.
func (c *Cache) HDel(ctx context.Context, key string, fields ...string) error {
	return c.client.HDel(ctx, c.key(key), fields...).Err()
}
