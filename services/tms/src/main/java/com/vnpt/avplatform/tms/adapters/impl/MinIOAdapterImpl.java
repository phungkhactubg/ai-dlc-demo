package com.vnpt.avplatform.tms.adapters.impl;

import com.vnpt.avplatform.tms.adapters.MinIOAdapter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HexFormat;
import java.util.Objects;

@Slf4j
@Component
public class MinIOAdapterImpl implements MinIOAdapter {

    private static final String SERVICE = "s3";
    private static final String AWS_ALGORITHM = "AWS4-HMAC-SHA256";
    private static final String AWS4_REQUEST = "aws4_request";
    private static final DateTimeFormatter DATE_TIME_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'");
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd");

    private final String endpoint;
    private final String accessKey;
    private final String secretKey;
    private final String bucket;
    private final String cdnUrl;
    private final String region;

    public MinIOAdapterImpl(
            @Value("${minio.endpoint}") String endpoint,
            @Value("${minio.access-key}") String accessKey,
            @Value("${minio.secret-key}") String secretKey,
            @Value("${minio.bucket}") String bucket,
            @Value("${minio.cdn-url}") String cdnUrl,
            @Value("${minio.region:us-east-1}") String region) {
        this.endpoint = Objects.requireNonNull(endpoint, "endpoint must not be null");
        this.accessKey = Objects.requireNonNull(accessKey, "accessKey must not be null");
        this.secretKey = Objects.requireNonNull(secretKey, "secretKey must not be null");
        this.bucket = Objects.requireNonNull(bucket, "bucket must not be null");
        this.cdnUrl = Objects.requireNonNull(cdnUrl, "cdnUrl must not be null");
        this.region = Objects.requireNonNull(region, "region must not be null");
    }

    @Override
    public String uploadLogo(String tenantId, byte[] data, String contentType) {
        String extension = resolveExtension(contentType);
        String objectKey = "tenants/" + tenantId + "/logo." + extension;
        String uploadUrl = endpoint + "/" + bucket + "/" + objectKey;

        ZonedDateTime now = ZonedDateTime.now(ZoneOffset.UTC);
        String dateTime = now.format(DATE_TIME_FORMAT);
        String date = now.format(DATE_FORMAT);

        try {
            String payloadHash = hexSha256(data);
            String host = URI.create(endpoint).getHost();
            int port = URI.create(endpoint).getPort();
            String hostHeader = (port != -1) ? host + ":" + port : host;

            String canonicalHeaders = "content-type:" + contentType + "\n"
                    + "host:" + hostHeader + "\n"
                    + "x-amz-content-sha256:" + payloadHash + "\n"
                    + "x-amz-date:" + dateTime + "\n";
            String signedHeaders = "content-type;host;x-amz-content-sha256;x-amz-date";

            String canonicalRequest = "PUT\n"
                    + "/" + bucket + "/" + objectKey + "\n"
                    + "\n"
                    + canonicalHeaders + "\n"
                    + signedHeaders + "\n"
                    + payloadHash;

            String credentialScope = date + "/" + region + "/" + SERVICE + "/" + AWS4_REQUEST;
            String stringToSign = AWS_ALGORITHM + "\n"
                    + dateTime + "\n"
                    + credentialScope + "\n"
                    + hexSha256(canonicalRequest.getBytes(StandardCharsets.UTF_8));

            byte[] signingKey = deriveSigningKey(secretKey, date, region, SERVICE);
            String signature = HexFormat.of().formatHex(hmacSha256(signingKey, stringToSign));

            String authHeader = AWS_ALGORITHM + " Credential=" + accessKey + "/" + credentialScope
                    + ", SignedHeaders=" + signedHeaders + ", Signature=" + signature;

            URL url = new URL(uploadUrl);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("PUT");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", contentType);
            connection.setRequestProperty("Host", hostHeader);
            connection.setRequestProperty("x-amz-content-sha256", payloadHash);
            connection.setRequestProperty("x-amz-date", dateTime);
            connection.setRequestProperty("Authorization", authHeader);
            connection.setRequestProperty("Content-Length", String.valueOf(data.length));

            try (OutputStream os = connection.getOutputStream()) {
                os.write(data);
            }

            int responseCode = connection.getResponseCode();
            if (responseCode != 200 && responseCode != 201 && responseCode != 204) {
                throw new RuntimeException("MinIO upload failed with HTTP status: " + responseCode);
            }

            String cdnPath = cdnUrl + "/tenants/" + tenantId + "/logo." + extension;
            log.info("Logo uploaded successfully: tenantId={}, cdnUrl={}", tenantId, cdnPath);
            return cdnPath;

        } catch (Exception e) {
            log.error("Failed to upload logo for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new RuntimeException("Failed to upload logo to MinIO: " + e.getMessage(), e);
        }
    }

    @Override
    public void deleteLogo(String tenantId) {
        for (String ext : new String[]{"png", "jpg", "jpeg", "webp"}) {
            String objectKey = "tenants/" + tenantId + "/logo." + ext;
            String deleteUrl = endpoint + "/" + bucket + "/" + objectKey;

            ZonedDateTime now = ZonedDateTime.now(ZoneOffset.UTC);
            String dateTime = now.format(DATE_TIME_FORMAT);
            String date = now.format(DATE_FORMAT);

            try {
                String payloadHash = hexSha256(new byte[0]);
                String host = URI.create(endpoint).getHost();
                int port = URI.create(endpoint).getPort();
                String hostHeader = (port != -1) ? host + ":" + port : host;

                String canonicalHeaders = "host:" + hostHeader + "\n"
                        + "x-amz-content-sha256:" + payloadHash + "\n"
                        + "x-amz-date:" + dateTime + "\n";
                String signedHeaders = "host;x-amz-content-sha256;x-amz-date";

                String canonicalRequest = "DELETE\n"
                        + "/" + bucket + "/" + objectKey + "\n"
                        + "\n"
                        + canonicalHeaders + "\n"
                        + signedHeaders + "\n"
                        + payloadHash;

                String credentialScope = date + "/" + region + "/" + SERVICE + "/" + AWS4_REQUEST;
                String stringToSign = AWS_ALGORITHM + "\n"
                        + dateTime + "\n"
                        + credentialScope + "\n"
                        + hexSha256(canonicalRequest.getBytes(StandardCharsets.UTF_8));

                byte[] signingKey = deriveSigningKey(secretKey, date, region, SERVICE);
                String signature = HexFormat.of().formatHex(hmacSha256(signingKey, stringToSign));

                String authHeader = AWS_ALGORITHM + " Credential=" + accessKey + "/" + credentialScope
                        + ", SignedHeaders=" + signedHeaders + ", Signature=" + signature;

                URL url = new URL(deleteUrl);
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("DELETE");
                connection.setRequestProperty("Host", hostHeader);
                connection.setRequestProperty("x-amz-content-sha256", payloadHash);
                connection.setRequestProperty("x-amz-date", dateTime);
                connection.setRequestProperty("Authorization", authHeader);

                int responseCode = connection.getResponseCode();
                if (responseCode == 200 || responseCode == 204) {
                    log.info("Logo deleted: tenantId={}, extension={}", tenantId, ext);
                    return;
                }
            } catch (Exception e) {
                log.debug("Could not delete logo with extension={} for tenantId={}: {}", ext, tenantId, e.getMessage());
            }
        }
        log.warn("No logo found to delete for tenantId={}", tenantId);
    }

    private String resolveExtension(String contentType) {
        return switch (contentType) {
            case "image/png" -> "png";
            case "image/jpeg" -> "jpg";
            case "image/webp" -> "webp";
            default -> "png";
        };
    }

    private String hexSha256(byte[] data) throws NoSuchAlgorithmException {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        return HexFormat.of().formatHex(digest.digest(data));
    }

    private String hexSha256(String data) throws NoSuchAlgorithmException {
        return hexSha256(data.getBytes(StandardCharsets.UTF_8));
    }

    private byte[] hmacSha256(byte[] key, String data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(key, "HmacSHA256"));
        return mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
    }

    private byte[] deriveSigningKey(String secret, String date, String region, String service) throws Exception {
        byte[] kSecret = ("AWS4" + secret).getBytes(StandardCharsets.UTF_8);
        byte[] kDate = hmacSha256(kSecret, date);
        byte[] kRegion = hmacSha256(kDate, region);
        byte[] kService = hmacSha256(kRegion, service);
        return hmacSha256(kService, AWS4_REQUEST);
    }
}
