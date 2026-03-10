package s3

import "errors"

// S3-specific errors.
var (
	// ErrObjectNotFound indicates the object was not found.
	ErrObjectNotFound = errors.New("object not found")

	// ErrBucketNotFound indicates the bucket was not found.
	ErrBucketNotFound = errors.New("bucket not found")

	// ErrConnectionFailed indicates a connection error.
	ErrConnectionFailed = errors.New("s3 connection failed")

	// ErrUploadFailed indicates upload failed.
	ErrUploadFailed = errors.New("upload failed")

	// ErrDownloadFailed indicates download failed.
	ErrDownloadFailed = errors.New("download failed")
)
