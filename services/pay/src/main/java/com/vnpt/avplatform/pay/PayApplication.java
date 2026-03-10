package com.vnpt.avplatform.pay;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * PAY (Payment Service) — Spring Boot entry point.
 *
 * <p>PCI-DSS compliant payment processing service deployed in the dedicated
 * {@code pay-namespace} Kubernetes namespace (ADR-003). All payment endpoints are
 * internal-only, reachable only from RHS via service-to-service calls.</p>
 */
@SpringBootApplication
@EnableKafka
public class PayApplication {

    public static void main(String[] args) {
        SpringApplication.run(PayApplication.class, args);
    }
}
