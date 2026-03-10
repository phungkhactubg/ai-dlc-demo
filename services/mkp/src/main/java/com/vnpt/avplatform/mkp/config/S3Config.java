package com.vnpt.avplatform.mkp.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

import java.net.URI;
import java.util.Objects;

/**
 * AWS S3 / MinIO-compatible client configuration for the MKP service.
 *
 * <p>MKP uses the S3 client to store and retrieve plugin package artifacts
 * uploaded by marketplace partners. Plugin binaries are stored in MinIO and
 * referenced by the marketplace catalog entries.</p>
 *
 * <p>Configuration properties:</p>
 * <ul>
 *   <li>{@code minio.endpoint} — MinIO server URL</li>
 *   <li>{@code minio.access-key} — access key ID</li>
 *   <li>{@code minio.secret-key} — secret access key</li>
 *   <li>{@code minio.bucket} — target bucket for plugin packages</li>
 * </ul>
 */
@Configuration
public class S3Config {

    /**
     * Creates an {@link S3Client} configured to connect to a MinIO-compatible endpoint.
     *
     * @param endpoint  the MinIO server URL
     * @param accessKey the access key ID for authentication
     * @param secretKey the secret access key for authentication
     * @return a configured {@link S3Client} instance
     */
    @Bean
    public S3Client s3Client(
            @Value("${minio.endpoint}") String endpoint,
            @Value("${minio.access-key}") String accessKey,
            @Value("${minio.secret-key}") String secretKey) {
        Objects.requireNonNull(endpoint, "minio.endpoint must not be null");
        Objects.requireNonNull(accessKey, "minio.access-key must not be null");
        Objects.requireNonNull(secretKey, "minio.secret-key must not be null");
        return S3Client.builder()
            .endpointOverride(URI.create(endpoint))
            .credentialsProvider(StaticCredentialsProvider.create(
                AwsBasicCredentials.create(accessKey, secretKey)))
            .region(Region.US_EAST_1)
            .build();
    }
}
