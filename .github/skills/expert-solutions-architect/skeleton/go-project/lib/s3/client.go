package s3

import (
	"context"
	"fmt"
	"io"
	"net/url"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

// Client wraps S3/MinIO connection.
type Client struct {
	client *minio.Client
	bucket string
}

// Config holds S3 connection settings.
type Config struct {
	Endpoint        string `mapstructure:"endpoint"`
	AccessKeyID     string `mapstructure:"access_key_id"`
	SecretAccessKey string `mapstructure:"secret_access_key"`
	UseSSL          bool   `mapstructure:"use_ssl"`
	Region          string `mapstructure:"region"`
	DefaultBucket   string `mapstructure:"default_bucket"`
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		Endpoint:      "localhost:9000",
		UseSSL:        false,
		Region:        "us-east-1",
		DefaultBucket: "default",
	}
}

// NewClient creates a new S3/MinIO client.
func NewClient(ctx context.Context, cfg Config) (*Client, error) {
	client, err := minio.New(cfg.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.AccessKeyID, cfg.SecretAccessKey, ""),
		Secure: cfg.UseSSL,
		Region: cfg.Region,
	})
	if err != nil {
		return nil, fmt.Errorf("s3 client creation failed: %w", err)
	}

	// Verify connection by checking bucket
	exists, err := client.BucketExists(ctx, cfg.DefaultBucket)
	if err != nil {
		return nil, fmt.Errorf("s3 connection check failed: %w", err)
	}
	if !exists {
		// Create bucket if it doesn't exist
		if err := client.MakeBucket(ctx, cfg.DefaultBucket, minio.MakeBucketOptions{Region: cfg.Region}); err != nil {
			return nil, fmt.Errorf("s3 bucket creation failed: %w", err)
		}
	}

	return &Client{
		client: client,
		bucket: cfg.DefaultBucket,
	}, nil
}

// Health checks if the connection is alive.
func (c *Client) Health(ctx context.Context) error {
	_, err := c.client.BucketExists(ctx, c.bucket)
	return err
}

// Upload uploads a file.
func (c *Client) Upload(ctx context.Context, objectName string, reader io.Reader, size int64, contentType string) (*UploadInfo, error) {
	info, err := c.client.PutObject(ctx, c.bucket, objectName, reader, size, minio.PutObjectOptions{
		ContentType: contentType,
	})
	if err != nil {
		return nil, fmt.Errorf("upload failed: %w", err)
	}
	return &UploadInfo{
		Bucket:   info.Bucket,
		Key:      info.Key,
		ETag:     info.ETag,
		Size:     info.Size,
		Location: info.Location,
	}, nil
}

// UploadToBucket uploads to a specific bucket.
func (c *Client) UploadToBucket(ctx context.Context, bucket, objectName string, reader io.Reader, size int64, contentType string) (*UploadInfo, error) {
	info, err := c.client.PutObject(ctx, bucket, objectName, reader, size, minio.PutObjectOptions{
		ContentType: contentType,
	})
	if err != nil {
		return nil, fmt.Errorf("upload to bucket failed: %w", err)
	}
	return &UploadInfo{
		Bucket:   info.Bucket,
		Key:      info.Key,
		ETag:     info.ETag,
		Size:     info.Size,
		Location: info.Location,
	}, nil
}

// Download downloads a file.
func (c *Client) Download(ctx context.Context, objectName string) (io.ReadCloser, error) {
	obj, err := c.client.GetObject(ctx, c.bucket, objectName, minio.GetObjectOptions{})
	if err != nil {
		return nil, fmt.Errorf("download failed: %w", err)
	}
	return obj, nil
}

// DownloadFromBucket downloads from a specific bucket.
func (c *Client) DownloadFromBucket(ctx context.Context, bucket, objectName string) (io.ReadCloser, error) {
	obj, err := c.client.GetObject(ctx, bucket, objectName, minio.GetObjectOptions{})
	if err != nil {
		return nil, fmt.Errorf("download from bucket failed: %w", err)
	}
	return obj, nil
}

// Delete deletes an object.
func (c *Client) Delete(ctx context.Context, objectName string) error {
	if err := c.client.RemoveObject(ctx, c.bucket, objectName, minio.RemoveObjectOptions{}); err != nil {
		return fmt.Errorf("delete failed: %w", err)
	}
	return nil
}

// Exists checks if an object exists.
func (c *Client) Exists(ctx context.Context, objectName string) (bool, error) {
	_, err := c.client.StatObject(ctx, c.bucket, objectName, minio.StatObjectOptions{})
	if err != nil {
		errResponse := minio.ToErrorResponse(err)
		if errResponse.Code == "NoSuchKey" {
			return false, nil
		}
		return false, fmt.Errorf("stat object failed: %w", err)
	}
	return true, nil
}

// GetInfo returns object information.
func (c *Client) GetInfo(ctx context.Context, objectName string) (*ObjectInfo, error) {
	info, err := c.client.StatObject(ctx, c.bucket, objectName, minio.StatObjectOptions{})
	if err != nil {
		return nil, fmt.Errorf("get info failed: %w", err)
	}
	return &ObjectInfo{
		Key:          info.Key,
		Size:         info.Size,
		ETag:         info.ETag,
		ContentType:  info.ContentType,
		LastModified: info.LastModified,
	}, nil
}

// List lists objects with prefix.
func (c *Client) List(ctx context.Context, prefix string) ([]ObjectInfo, error) {
	var objects []ObjectInfo
	for obj := range c.client.ListObjects(ctx, c.bucket, minio.ListObjectsOptions{Prefix: prefix, Recursive: true}) {
		if obj.Err != nil {
			return nil, fmt.Errorf("list objects failed: %w", obj.Err)
		}
		objects = append(objects, ObjectInfo{
			Key:          obj.Key,
			Size:         obj.Size,
			ETag:         obj.ETag,
			LastModified: obj.LastModified,
		})
	}
	return objects, nil
}

// GetPresignedURL generates a presigned URL for download.
func (c *Client) GetPresignedURL(ctx context.Context, objectName string, expiry time.Duration) (string, error) {
	reqParams := make(url.Values)
	presignedURL, err := c.client.PresignedGetObject(ctx, c.bucket, objectName, expiry, reqParams)
	if err != nil {
		return "", fmt.Errorf("get presigned url failed: %w", err)
	}
	return presignedURL.String(), nil
}

// GetPresignedPutURL generates a presigned URL for upload.
func (c *Client) GetPresignedPutURL(ctx context.Context, objectName string, expiry time.Duration) (string, error) {
	presignedURL, err := c.client.PresignedPutObject(ctx, c.bucket, objectName, expiry)
	if err != nil {
		return "", fmt.Errorf("get presigned put url failed: %w", err)
	}
	return presignedURL.String(), nil
}

// Copy copies an object.
func (c *Client) Copy(ctx context.Context, srcObject, destObject string) (*UploadInfo, error) {
	src := minio.CopySrcOptions{Bucket: c.bucket, Object: srcObject}
	dst := minio.CopyDestOptions{Bucket: c.bucket, Object: destObject}

	info, err := c.client.CopyObject(ctx, dst, src)
	if err != nil {
		return nil, fmt.Errorf("copy failed: %w", err)
	}
	return &UploadInfo{
		Bucket: info.Bucket,
		Key:    info.Key,
		ETag:   info.ETag,
	}, nil
}

// CreateBucket creates a new bucket.
func (c *Client) CreateBucket(ctx context.Context, bucket, region string) error {
	return c.client.MakeBucket(ctx, bucket, minio.MakeBucketOptions{Region: region})
}

// UploadInfo contains upload result information.
type UploadInfo struct {
	Bucket   string
	Key      string
	ETag     string
	Size     int64
	Location string
}

// ObjectInfo contains object metadata.
type ObjectInfo struct {
	Key          string
	Size         int64
	ETag         string
	ContentType  string
	LastModified time.Time
}
