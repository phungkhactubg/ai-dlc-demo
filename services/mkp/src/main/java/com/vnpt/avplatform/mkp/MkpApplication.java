package com.vnpt.avplatform.mkp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * MKP (Marketplace) Service main application class.
 *
 * <p>This service is responsible for:
 * <ul>
 *   <li>Managing plugin/partner listings on the AV Platform Marketplace</li>
 *   <li>Enforcing the partner security audit and performance test workflow (BL-009)</li>
 *   <li>Caching the marketplace catalog in Redis for fast retrieval</li>
 *   <li>Storing plugin packages in MinIO (S3-compatible)</li>
 * </ul>
 *
 * <p>BL-009: Plugins only appear on the Marketplace after passing security audit AND performance test.</p>
 */
@SpringBootApplication
@EnableKafka
public class MkpApplication {

    public static void main(String[] args) {
        SpringApplication.run(MkpApplication.class, args);
    }
}
