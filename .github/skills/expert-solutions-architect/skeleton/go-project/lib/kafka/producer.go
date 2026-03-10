package kafka

import (
	"context"
	"fmt"
	"time"

	"github.com/segmentio/kafka-go"
)

// Config holds Kafka connection settings.
type Config struct {
	Brokers       []string      `mapstructure:"brokers"`
	Topic         string        `mapstructure:"topic"`
	ConsumerGroup string        `mapstructure:"consumer_group"`
	MinBytes      int           `mapstructure:"min_bytes"`
	MaxBytes      int           `mapstructure:"max_bytes"`
	MaxWait       time.Duration `mapstructure:"max_wait"`
	ReadTimeout   time.Duration `mapstructure:"read_timeout"`
	WriteTimeout  time.Duration `mapstructure:"write_timeout"`
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		Brokers:      []string{"localhost:9092"},
		MinBytes:     10e3, // 10KB
		MaxBytes:     10e6, // 10MB
		MaxWait:      1 * time.Second,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
}

// Producer provides Kafka message production.
type Producer struct {
	writer *kafka.Writer
}

// NewProducer creates a new Kafka producer.
func NewProducer(cfg Config) *Producer {
	writer := &kafka.Writer{
		Addr:         kafka.TCP(cfg.Brokers...),
		Topic:        cfg.Topic,
		Balancer:     &kafka.LeastBytes{},
		WriteTimeout: cfg.WriteTimeout,
		RequiredAcks: kafka.RequireAll,
		Async:        false,
	}
	return &Producer{writer: writer}
}

// NewAsyncProducer creates an async producer for high throughput.
func NewAsyncProducer(cfg Config) *Producer {
	writer := &kafka.Writer{
		Addr:         kafka.TCP(cfg.Brokers...),
		Topic:        cfg.Topic,
		Balancer:     &kafka.LeastBytes{},
		WriteTimeout: cfg.WriteTimeout,
		RequiredAcks: kafka.RequireOne,
		Async:        true,
		BatchSize:    100,
		BatchTimeout: 10 * time.Millisecond,
	}
	return &Producer{writer: writer}
}

// Produce sends a message to Kafka.
func (p *Producer) Produce(ctx context.Context, key, value []byte) error {
	msg := kafka.Message{
		Key:   key,
		Value: value,
		Time:  time.Now(),
	}
	if err := p.writer.WriteMessages(ctx, msg); err != nil {
		return fmt.Errorf("produce failed: %w", err)
	}
	return nil
}

// ProduceWithTopic sends a message to a specific topic.
func (p *Producer) ProduceWithTopic(ctx context.Context, topic string, key, value []byte) error {
	msg := kafka.Message{
		Topic: topic,
		Key:   key,
		Value: value,
		Time:  time.Now(),
	}
	if err := p.writer.WriteMessages(ctx, msg); err != nil {
		return fmt.Errorf("produce to topic %s failed: %w", topic, err)
	}
	return nil
}

// ProduceBatch sends multiple messages.
func (p *Producer) ProduceBatch(ctx context.Context, messages []kafka.Message) error {
	if err := p.writer.WriteMessages(ctx, messages...); err != nil {
		return fmt.Errorf("produce batch failed: %w", err)
	}
	return nil
}

// Close closes the producer.
func (p *Producer) Close() error {
	return p.writer.Close()
}

// Stats returns writer statistics.
func (p *Producer) Stats() kafka.WriterStats {
	return p.writer.Stats()
}
