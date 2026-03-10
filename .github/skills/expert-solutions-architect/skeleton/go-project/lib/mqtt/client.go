package mqtt

import (
	"context"
	"fmt"
	"sync"
	"time"

	paho "github.com/eclipse/paho.mqtt.golang"
)

// QoS levels.
const (
	QoS0 byte = 0 // At most once
	QoS1 byte = 1 // At least once
	QoS2 byte = 2 // Exactly once
)

// Client wraps MQTT connection.
type Client struct {
	client paho.Client
	mu     sync.RWMutex
}

// Config holds MQTT connection settings.
type Config struct {
	Broker           string        `mapstructure:"broker"`
	ClientID         string        `mapstructure:"client_id"`
	Username         string        `mapstructure:"username"`
	Password         string        `mapstructure:"password"`
	CleanSession     bool          `mapstructure:"clean_session"`
	AutoReconnect    bool          `mapstructure:"auto_reconnect"`
	ConnectTimeout   time.Duration `mapstructure:"connect_timeout"`
	KeepAlive        time.Duration `mapstructure:"keep_alive"`
	PingTimeout      time.Duration `mapstructure:"ping_timeout"`
	MaxReconnectWait time.Duration `mapstructure:"max_reconnect_wait"`
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		Broker:           "tcp://localhost:1883",
		ClientID:         "go-mqtt-client",
		CleanSession:     false,
		AutoReconnect:    true,
		ConnectTimeout:   30 * time.Second,
		KeepAlive:        60 * time.Second,
		PingTimeout:      10 * time.Second,
		MaxReconnectWait: 5 * time.Minute,
	}
}

// NewClient creates a new MQTT client.
func NewClient(ctx context.Context, cfg Config) (*Client, error) {
	opts := paho.NewClientOptions()
	opts.AddBroker(cfg.Broker)
	opts.SetClientID(cfg.ClientID)
	opts.SetCleanSession(cfg.CleanSession)
	opts.SetAutoReconnect(cfg.AutoReconnect)
	opts.SetConnectTimeout(cfg.ConnectTimeout)
	opts.SetKeepAlive(cfg.KeepAlive)
	opts.SetPingTimeout(cfg.PingTimeout)
	opts.SetMaxReconnectInterval(cfg.MaxReconnectWait)

	if cfg.Username != "" {
		opts.SetUsername(cfg.Username)
		opts.SetPassword(cfg.Password)
	}

	opts.SetConnectionLostHandler(func(_ paho.Client, err error) {
		fmt.Printf("MQTT connection lost: %v\n", err)
	})

	opts.SetOnConnectHandler(func(_ paho.Client) {
		fmt.Println("MQTT connected")
	})

	opts.SetReconnectingHandler(func(_ paho.Client, opts *paho.ClientOptions) {
		fmt.Println("MQTT reconnecting...")
	})

	client := paho.NewClient(opts)

	token := client.Connect()
	if !token.WaitTimeout(cfg.ConnectTimeout) {
		return nil, ErrConnectionTimeout
	}
	if err := token.Error(); err != nil {
		return nil, fmt.Errorf("mqtt connect failed: %w", err)
	}

	return &Client{client: client}, nil
}

// Close disconnects the client.
func (c *Client) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.client.Disconnect(1000)
}

// IsConnected returns connection status.
func (c *Client) IsConnected() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.client.IsConnected()
}

// Health checks if the client is connected.
func (c *Client) Health(ctx context.Context) error {
	if !c.IsConnected() {
		return ErrNotConnected
	}
	return nil
}

// Publish publishes a message.
func (c *Client) Publish(ctx context.Context, topic string, payload []byte, qos byte) error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	token := c.client.Publish(topic, qos, false, payload)
	if !token.WaitTimeout(10 * time.Second) {
		return ErrPublishTimeout
	}
	if err := token.Error(); err != nil {
		return fmt.Errorf("publish failed: %w", err)
	}
	return nil
}

// PublishRetained publishes a retained message.
func (c *Client) PublishRetained(ctx context.Context, topic string, payload []byte, qos byte) error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	token := c.client.Publish(topic, qos, true, payload)
	if !token.WaitTimeout(10 * time.Second) {
		return ErrPublishTimeout
	}
	if err := token.Error(); err != nil {
		return fmt.Errorf("publish retained failed: %w", err)
	}
	return nil
}

// MessageHandler handles incoming MQTT messages.
type MessageHandler func(topic string, payload []byte)

// Subscribe subscribes to a topic.
func (c *Client) Subscribe(ctx context.Context, topic string, qos byte, handler MessageHandler) error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	token := c.client.Subscribe(topic, qos, func(_ paho.Client, msg paho.Message) {
		handler(msg.Topic(), msg.Payload())
	})
	if !token.WaitTimeout(10 * time.Second) {
		return ErrSubscribeTimeout
	}
	if err := token.Error(); err != nil {
		return fmt.Errorf("subscribe failed: %w", err)
	}
	return nil
}

// SubscribeMultiple subscribes to multiple topics.
func (c *Client) SubscribeMultiple(ctx context.Context, topics map[string]byte, handler MessageHandler) error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	token := c.client.SubscribeMultiple(topics, func(_ paho.Client, msg paho.Message) {
		handler(msg.Topic(), msg.Payload())
	})
	if !token.WaitTimeout(10 * time.Second) {
		return ErrSubscribeTimeout
	}
	if err := token.Error(); err != nil {
		return fmt.Errorf("subscribe multiple failed: %w", err)
	}
	return nil
}

// Unsubscribe unsubscribes from topics.
func (c *Client) Unsubscribe(ctx context.Context, topics ...string) error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	token := c.client.Unsubscribe(topics...)
	if !token.WaitTimeout(10 * time.Second) {
		return ErrUnsubscribeTimeout
	}
	if err := token.Error(); err != nil {
		return fmt.Errorf("unsubscribe failed: %w", err)
	}
	return nil
}
