package com.vnpt.avplatform.bms;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Entry point for the Billing &amp; Subscription Management Service (BMS).
 *
 * <p>Responsibilities:</p>
 * <ul>
 *   <li>Subscription lifecycle management (STARTER / PROFESSIONAL / ENTERPRISE plans)</li>
 *   <li>Usage metering and quota enforcement (FR-BMS-010 to FR-BMS-013)</li>
 *   <li>Billing cycle automation (monthly / annual)</li>
 *   <li>InfluxDB time-series metering data storage</li>
 * </ul>
 */
@SpringBootApplication
@EnableKafka
public class BmsApplication {

    public static void main(String[] args) {
        SpringApplication.run(BmsApplication.class, args);
    }
}
