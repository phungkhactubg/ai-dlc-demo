package kafka

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/segmentio/kafka-go"
)

// MessageHandler handles incoming Kafka messages.
type MessageHandler func(ctx context.Context, msg Message) error

// Message wraps kafka.Message for easier handling.
type Message struct {
	Topic     string
	Partition int
	Offset    int64
	Key       []byte
	Value     []byte
	Time      time.Time
	Headers   []kafka.Header
}

// Consumer provides Kafka message consumption.
type Consumer struct {
	reader  *kafka.Reader
	handler MessageHandler
}

// NewConsumer creates a new Kafka consumer.
func NewConsumer(cfg Config) *Consumer {
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:     cfg.Brokers,
		Topic:       cfg.Topic,
		GroupID:     cfg.ConsumerGroup,
		MinBytes:    cfg.MinBytes,
		MaxBytes:    cfg.MaxBytes,
		MaxWait:     cfg.MaxWait,
		StartOffset: kafka.LastOffset,
	})
	return &Consumer{reader: reader}
}

// NewConsumerFromBeginning creates a consumer starting from the beginning.
func NewConsumerFromBeginning(cfg Config) *Consumer {
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:     cfg.Brokers,
		Topic:       cfg.Topic,
		GroupID:     cfg.ConsumerGroup,
		MinBytes:    cfg.MinBytes,
		MaxBytes:    cfg.MaxBytes,
		MaxWait:     cfg.MaxWait,
		StartOffset: kafka.FirstOffset,
	})
	return &Consumer{reader: reader}
}

// Consume starts consuming messages.
func (c *Consumer) Consume(ctx context.Context, handler MessageHandler) error {
	c.handler = handler

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			msg, err := c.reader.FetchMessage(ctx)
			if err != nil {
				if err == io.EOF || err == context.Canceled {
					return nil
				}
				return fmt.Errorf("fetch message failed: %w", err)
			}

			wrappedMsg := Message{
				Topic:     msg.Topic,
				Partition: msg.Partition,
				Offset:    msg.Offset,
				Key:       msg.Key,
				Value:     msg.Value,
				Time:      msg.Time,
				Headers:   msg.Headers,
			}

			if err := handler(ctx, wrappedMsg); err != nil {
				// Log error but continue processing
				fmt.Printf("handler error: %v\n", err)
				continue
			}

			// Commit offset after successful processing
			if err := c.reader.CommitMessages(ctx, msg); err != nil {
				fmt.Printf("commit failed: %v\n", err)
			}
		}
	}
}

// ConsumeWithRetry consumes with retry on handler failure.
func (c *Consumer) ConsumeWithRetry(ctx context.Context, handler MessageHandler, maxRetries int) error {
	return c.Consume(ctx, func(ctx context.Context, msg Message) error {
		var lastErr error
		for i := 0; i <= maxRetries; i++ {
			if err := handler(ctx, msg); err == nil {
				return nil
			} else {
				lastErr = err
				time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
			}
		}
		return fmt.Errorf("handler failed after %d retries: %w", maxRetries, lastErr)
	})
}

// Close closes the consumer.
func (c *Consumer) Close() error {
	return c.reader.Close()
}

// Stats returns reader statistics.
func (c *Consumer) Stats() kafka.ReaderStats {
	return c.reader.Stats()
}

// Lag returns the current consumer lag.
func (c *Consumer) Lag() int64 {
	return c.reader.Lag()
}

// Offset returns the current offset.
func (c *Consumer) Offset() int64 {
	return c.reader.Offset()
}
