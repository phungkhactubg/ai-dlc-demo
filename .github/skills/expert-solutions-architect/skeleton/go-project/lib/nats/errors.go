package nats

import "errors"

// NATS-specific errors.
var (
	// ErrNotConnected indicates the client is not connected.
	ErrNotConnected = errors.New("nats not connected")

	// ErrJetStreamNotEnabled indicates JetStream is not enabled.
	ErrJetStreamNotEnabled = errors.New("jetstream not enabled")

	// ErrSubscriptionFailed indicates subscription failed.
	ErrSubscriptionFailed = errors.New("subscription failed")

	// ErrPublishFailed indicates publish failed.
	ErrPublishFailed = errors.New("publish failed")
)
