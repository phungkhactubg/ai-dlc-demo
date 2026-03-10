package mqtt

import "errors"

// MQTT-specific errors.
var (
	// ErrNotConnected indicates the client is not connected.
	ErrNotConnected = errors.New("mqtt not connected")

	// ErrConnectionTimeout indicates connection timed out.
	ErrConnectionTimeout = errors.New("mqtt connection timeout")

	// ErrPublishTimeout indicates publish timed out.
	ErrPublishTimeout = errors.New("mqtt publish timeout")

	// ErrSubscribeTimeout indicates subscribe timed out.
	ErrSubscribeTimeout = errors.New("mqtt subscribe timeout")

	// ErrUnsubscribeTimeout indicates unsubscribe timed out.
	ErrUnsubscribeTimeout = errors.New("mqtt unsubscribe timeout")
)
