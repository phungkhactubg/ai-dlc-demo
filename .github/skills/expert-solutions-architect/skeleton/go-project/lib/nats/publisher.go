package nats

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/nats-io/nats.go"
)

// Publisher provides message publishing.
type Publisher struct {
	client *Client
}

// NewPublisher creates a new publisher.
func NewPublisher(client *Client) *Publisher {
	return &Publisher{client: client}
}

// Publish publishes a message to a subject.
func (p *Publisher) Publish(ctx context.Context, subject string, data interface{}) error {
	payload, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("marshal failed: %w", err)
	}
	return p.client.conn.Publish(subject, payload)
}

// PublishRaw publishes raw bytes to a subject.
func (p *Publisher) PublishRaw(ctx context.Context, subject string, data []byte) error {
	return p.client.conn.Publish(subject, data)
}

// PublishWithReply publishes and waits for a reply.
func (p *Publisher) PublishWithReply(ctx context.Context, subject string, data interface{}, dest interface{}) error {
	payload, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("marshal failed: %w", err)
	}

	msg, err := p.client.conn.RequestWithContext(ctx, subject, payload)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}

	if dest != nil {
		if err := json.Unmarshal(msg.Data, dest); err != nil {
			return fmt.Errorf("unmarshal response failed: %w", err)
		}
	}
	return nil
}

// JetStreamPublisher provides JetStream publishing.
type JetStreamPublisher struct {
	client *Client
}

// NewJetStreamPublisher creates a JetStream publisher.
func NewJetStreamPublisher(client *Client) (*JetStreamPublisher, error) {
	if client.js == nil {
		return nil, ErrJetStreamNotEnabled
	}
	return &JetStreamPublisher{client: client}, nil
}

// Publish publishes to JetStream.
func (p *JetStreamPublisher) Publish(ctx context.Context, subject string, data interface{}) (*nats.PubAck, error) {
	payload, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("marshal failed: %w", err)
	}
	ack, err := p.client.js.Publish(subject, payload)
	if err != nil {
		return nil, fmt.Errorf("jetstream publish failed: %w", err)
	}
	return ack, nil
}

// PublishAsync publishes asynchronously to JetStream.
func (p *JetStreamPublisher) PublishAsync(ctx context.Context, subject string, data interface{}) (nats.PubAckFuture, error) {
	payload, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("marshal failed: %w", err)
	}
	future, err := p.client.js.PublishAsync(subject, payload)
	if err != nil {
		return nil, fmt.Errorf("jetstream publish async failed: %w", err)
	}
	return future, nil
}
