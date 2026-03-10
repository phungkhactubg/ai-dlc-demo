package com.vnpt.avplatform.rhs;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Entry point for the Ride Hailing Service (RHS).
 *
 * <p>Manages the full trip lifecycle: request → match → vehicle-enroute → arrived →
 * boarding → in-progress → alighting → completed, including exception states
 * (remote-intervention, safety-stop, cancelled) as defined in FR-RHS-002.</p>
 */
@SpringBootApplication
@EnableKafka
public class RhsApplication {

    public static void main(String[] args) {
        SpringApplication.run(RhsApplication.class, args);
    }
}
