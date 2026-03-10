package com.vnpt.avplatform.tms;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * TMS (Tenant Management Service) — Spring Boot entry point.
 *
 * <p>Manages tenant lifecycle, onboarding sagas (ADR-005, BL-011), and
 * tenant configuration for the VNPT AV Platform.</p>
 */
@SpringBootApplication
@EnableKafka
public class TmsApplication {

    public static void main(String[] args) {
        SpringApplication.run(TmsApplication.class, args);
    }
}
