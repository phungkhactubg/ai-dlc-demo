package nats

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/nats-io/nats.go"
)

// MessageHandler handles incoming messages.
type MessageHandler func(subject string, data []byte) error

// Subscriber provides message subscription.
type Subscriber struct {
	client        *Client
	subscriptions []*nats.Subscription
	mu            sync.Mutex
}

// NewSubscriber creates a new subscriber.
func NewSubscriber(client *Client) *Subscriber {
	return &Subscriber{
		client:        client,
		subscriptions: make([]*nats.Subscription, 0),
	}
}

// Subscribe subscribes to a subject.
func (s *Subscriber) Subscribe(subject string, handler MessageHandler) error {
	sub, err := s.client.conn.Subscribe(subject, func(msg *nats.Msg) {
		if err := handler(msg.Subject, msg.Data); err != nil {
			fmt.Printf("handler error for %s: %v\n", msg.Subject, err)
		}
	})
	if err != nil {
		return fmt.Errorf("subscribe failed: %w", err)
	}

	s.mu.Lock()
	s.subscriptions = append(s.subscriptions, sub)
	s.mu.Unlock()

	return nil
}

// SubscribeJSON subscribes and unmarshals JSON messages.
func (s *Subscriber) SubscribeJSON(subject string, handler func(subject string, data interface{}) error) error {
	return s.Subscribe(subject, func(subj string, raw []byte) error {
		var data interface{}
		if err := json.Unmarshal(raw, &data); err != nil {
			return fmt.Errorf("unmarshal failed: %w", err)
		}
		return handler(subj, data)
	})
}

// QueueSubscribe subscribes with a queue group.
func (s *Subscriber) QueueSubscribe(subject, queue string, handler MessageHandler) error {
	sub, err := s.client.conn.QueueSubscribe(subject, queue, func(msg *nats.Msg) {
		if err := handler(msg.Subject, msg.Data); err != nil {
			fmt.Printf("handler error for %s: %v\n", msg.Subject, err)
		}
	})
	if err != nil {
		return fmt.Errorf("queue subscribe failed: %w", err)
	}

	s.mu.Lock()
	s.subscriptions = append(s.subscriptions, sub)
	s.mu.Unlock()

	return nil
}

// Unsubscribe unsubscribes from all subjects.
func (s *Subscriber) Unsubscribe() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	var lastErr error
	for _, sub := range s.subscriptions {
		if err := sub.Unsubscribe(); err != nil {
			lastErr = err
		}
	}
	s.subscriptions = make([]*nats.Subscription, 0)
	return lastErr
}

// JetStreamSubscriber provides JetStream subscription.
type JetStreamSubscriber struct {
	client        *Client
	subscriptions []*nats.Subscription
	mu            sync.Mutex
}

// NewJetStreamSubscriber creates a JetStream subscriber.
func NewJetStreamSubscriber(client *Client) (*JetStreamSubscriber, error) {
	if client.js == nil {
		return nil, ErrJetStreamNotEnabled
	}
	return &JetStreamSubscriber{
		client:        client,
		subscriptions: make([]*nats.Subscription, 0),
	}, nil
}

// Subscribe creates a pull subscription.
func (s *JetStreamSubscriber) Subscribe(ctx context.Context, stream, consumer, subject string, handler MessageHandler) error {
	// Create consumer
	_, err := s.client.js.AddConsumer(stream, &nats.ConsumerConfig{
		Durable:       consumer,
		AckPolicy:     nats.AckExplicitPolicy,
		FilterSubject: subject,
	})
	if err != nil {
		// Ignore if already exists
		fmt.Printf("consumer create note: %v\n", err)
	}

	sub, err := s.client.js.PullSubscribe(subject, consumer)
	if err != nil {
		return fmt.Errorf("jetstream subscribe failed: %w", err)
	}

	s.mu.Lock()
	s.subscriptions = append(s.subscriptions, sub)
	s.mu.Unlock()

	// Start processing
	go s.processPull(ctx, sub, handler)

	return nil
}

func (s *JetStreamSubscriber) processPull(ctx context.Context, sub *nats.Subscription, handler MessageHandler) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
			msgs, err := sub.Fetch(10, nats.MaxWait(nats.DefaultTimeout))
			if err != nil {
				continue
			}
			for _, msg := range msgs {
				if err := handler(msg.Subject, msg.Data); err != nil {
					msg.Nak()
				} else {
					msg.Ack()
				}
			}
		}
	}
}

// PushSubscribe creates a push subscription.
func (s *JetStreamSubscriber) PushSubscribe(subject string, handler MessageHandler) error {
	sub, err := s.client.js.Subscribe(subject, func(msg *nats.Msg) {
		if err := handler(msg.Subject, msg.Data); err != nil {
			msg.Nak()
		} else {
			msg.Ack()
		}
	})
	if err != nil {
		return fmt.Errorf("jetstream push subscribe failed: %w", err)
	}

	s.mu.Lock()
	s.subscriptions = append(s.subscriptions, sub)
	s.mu.Unlock()

	return nil
}

// Unsubscribe unsubscribes from all.
func (s *JetStreamSubscriber) Unsubscribe() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	var lastErr error
	for _, sub := range s.subscriptions {
		if err := sub.Unsubscribe(); err != nil {
			lastErr = err
		}
	}
	s.subscriptions = make([]*nats.Subscription, 0)
	return lastErr
}
