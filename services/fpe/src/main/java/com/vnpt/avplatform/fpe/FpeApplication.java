package com.vnpt.avplatform.fpe;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Entry point for the Fare Pricing Engine (FPE).
 *
 * <p>Computes upfront fares (FR-FPE-001, FR-FPE-002), applies surge multipliers
 * within tenant-configured caps (BL-002), and caches results in Redis to meet the
 * &lt;200 ms response target (FR-FPE-003).</p>
 */
@SpringBootApplication
@EnableKafka
public class FpeApplication {

    public static void main(String[] args) {
        SpringApplication.run(FpeApplication.class, args);
    }
}
