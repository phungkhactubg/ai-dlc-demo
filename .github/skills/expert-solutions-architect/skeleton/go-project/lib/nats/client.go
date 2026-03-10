package nats

import (
	"context"
	"fmt"
	"time"

	"github.com/nats-io/nats.go"
)

// Client wraps NATS connection.
type Client struct {
	conn *nats.Conn
	js   nats.JetStreamContext
}

// Config holds NATS connection settings.
type Config struct {
	URL             string        `mapstructure:"url"`
	Name            string        `mapstructure:"name"`
	Token           string        `mapstructure:"token"`
	Username        string        `mapstructure:"username"`
	Password        string        `mapstructure:"password"`
	ConnectTimeout  time.Duration `mapstructure:"connect_timeout"`
	ReconnectWait   time.Duration `mapstructure:"reconnect_wait"`
	MaxReconnect    int           `mapstructure:"max_reconnect"`
	EnableJetStream bool          `mapstructure:"enable_jetstream"`
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		URL:             nats.DefaultURL,
		Name:            "app-client",
		ConnectTimeout:  10 * time.Second,
		ReconnectWait:   2 * time.Second,
		MaxReconnect:    60,
		EnableJetStream: true,
	}
}

// NewClient creates a new NATS connection.
func NewClient(ctx context.Context, cfg Config) (*Client, error) {
	opts := []nats.Option{
		nats.Name(cfg.Name),
		nats.Timeout(cfg.ConnectTimeout),
		nats.ReconnectWait(cfg.ReconnectWait),
		nats.MaxReconnects(cfg.MaxReconnect),
		nats.DisconnectErrHandler(func(_ *nats.Conn, err error) {
			if err != nil {
				fmt.Printf("NATS disconnected: %v\n", err)
			}
		}),
		nats.ReconnectHandler(func(nc *nats.Conn) {
			fmt.Printf("NATS reconnected to %s\n", nc.ConnectedUrl())
		}),
	}

	if cfg.Token != "" {
		opts = append(opts, nats.Token(cfg.Token))
	}
	if cfg.Username != "" && cfg.Password != "" {
		opts = append(opts, nats.UserInfo(cfg.Username, cfg.Password))
	}

	conn, err := nats.Connect(cfg.URL, opts...)
	if err != nil {
		return nil, fmt.Errorf("nats connect failed: %w", err)
	}

	client := &Client{conn: conn}

	// Initialize JetStream if enabled
	if cfg.EnableJetStream {
		js, err := conn.JetStream()
		if err != nil {
			conn.Close()
			return nil, fmt.Errorf("jetstream init failed: %w", err)
		}
		client.js = js
	}

	return client, nil
}

// Close closes the NATS connection.
func (c *Client) Close() {
	if c.conn != nil {
		c.conn.Drain()
		c.conn.Close()
	}
}

// Conn returns the underlying NATS connection.
func (c *Client) Conn() *nats.Conn {
	return c.conn
}

// JetStream returns the JetStream context.
func (c *Client) JetStream() nats.JetStreamContext {
	return c.js
}

// Health checks if the connection is alive.
func (c *Client) Health(ctx context.Context) error {
	if !c.conn.IsConnected() {
		return ErrNotConnected
	}
	return nil
}

// CreateStream creates a JetStream stream.
func (c *Client) CreateStream(ctx context.Context, name string, subjects []string) (*nats.StreamInfo, error) {
	if c.js == nil {
		return nil, ErrJetStreamNotEnabled
	}

	streamCfg := &nats.StreamConfig{
		Name:     name,
		Subjects: subjects,
		Storage:  nats.FileStorage,
		Replicas: 1,
	}

	info, err := c.js.AddStream(streamCfg)
	if err != nil {
		// Check if stream already exists
		if existingInfo, _ := c.js.StreamInfo(name); existingInfo != nil {
			return existingInfo, nil
		}
		return nil, fmt.Errorf("create stream failed: %w", err)
	}
	return info, nil
}

// DeleteStream deletes a JetStream stream.
func (c *Client) DeleteStream(ctx context.Context, name string) error {
	if c.js == nil {
		return ErrJetStreamNotEnabled
	}
	return c.js.DeleteStream(name)
}
