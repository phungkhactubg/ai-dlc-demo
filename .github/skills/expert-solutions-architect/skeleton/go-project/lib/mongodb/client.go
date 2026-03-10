package mongodb

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
)

// Client wraps MongoDB connection with helper methods.
type Client struct {
	client   *mongo.Client
	database *mongo.Database
}

// Config holds MongoDB connection settings.
type Config struct {
	URI            string        `mapstructure:"uri"`
	Database       string        `mapstructure:"database"`
	ConnectTimeout time.Duration `mapstructure:"connect_timeout"`
	PingTimeout    time.Duration `mapstructure:"ping_timeout"`
	MaxPoolSize    uint64        `mapstructure:"max_pool_size"`
	MinPoolSize    uint64        `mapstructure:"min_pool_size"`
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		URI:            "mongodb://localhost:27017",
		Database:       "app_db",
		ConnectTimeout: 10 * time.Second,
		PingTimeout:    5 * time.Second,
		MaxPoolSize:    100,
		MinPoolSize:    10,
	}
}

// NewClient creates a new MongoDB connection.
func NewClient(ctx context.Context, cfg Config) (*Client, error) {
	if cfg.URI == "" {
		cfg = DefaultConfig()
	}

	clientOpts := options.Client().
		ApplyURI(cfg.URI).
		SetMaxPoolSize(cfg.MaxPoolSize).
		SetMinPoolSize(cfg.MinPoolSize).
		SetConnectTimeout(cfg.ConnectTimeout)

	connectCtx, cancel := context.WithTimeout(ctx, cfg.ConnectTimeout)
	defer cancel()

	client, err := mongo.Connect(connectCtx, clientOpts)
	if err != nil {
		return nil, fmt.Errorf("mongodb connect failed: %w", err)
	}

	// Verify connection
	pingCtx, pingCancel := context.WithTimeout(ctx, cfg.PingTimeout)
	defer pingCancel()

	if err := client.Ping(pingCtx, readpref.Primary()); err != nil {
		return nil, fmt.Errorf("mongodb ping failed: %w", err)
	}

	return &Client{
		client:   client,
		database: client.Database(cfg.Database),
	}, nil
}

// Close disconnects from MongoDB.
func (c *Client) Close(ctx context.Context) error {
	if c.client != nil {
		return c.client.Disconnect(ctx)
	}
	return nil
}

// Database returns the default database.
func (c *Client) Database() *mongo.Database {
	return c.database
}

// Collection returns a collection from the default database.
func (c *Client) Collection(name string) *mongo.Collection {
	return c.database.Collection(name)
}

// UseDatabase switches to a different database.
func (c *Client) UseDatabase(name string) *mongo.Database {
	return c.client.Database(name)
}

// Health checks if the connection is alive.
func (c *Client) Health(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	return c.client.Ping(ctx, readpref.Primary())
}

// CreateIndex creates an index on a collection.
func (c *Client) CreateIndex(ctx context.Context, collection string, keys bson.D, unique bool) (string, error) {
	coll := c.Collection(collection)
	indexModel := mongo.IndexModel{
		Keys:    keys,
		Options: options.Index().SetUnique(unique),
	}
	return coll.Indexes().CreateOne(ctx, indexModel)
}

// CreateCompoundIndex creates a compound index.
func (c *Client) CreateCompoundIndex(ctx context.Context, collection string, keys bson.D) (string, error) {
	return c.CreateIndex(ctx, collection, keys, false)
}

// WithTransaction executes operations in a transaction.
func (c *Client) WithTransaction(ctx context.Context, fn func(sessCtx mongo.SessionContext) error) error {
	session, err := c.client.StartSession()
	if err != nil {
		return fmt.Errorf("failed to start session: %w", err)
	}
	defer session.EndSession(ctx)

	_, err = session.WithTransaction(ctx, func(sessCtx mongo.SessionContext) (interface{}, error) {
		return nil, fn(sessCtx)
	})
	if err != nil {
		return fmt.Errorf("transaction failed: %w", err)
	}
	return nil
}
