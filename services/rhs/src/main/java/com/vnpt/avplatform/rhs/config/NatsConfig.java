package com.vnpt.avplatform.rhs.config;

import com.vnpt.avplatform.shared.exception.PlatformException;
import io.nats.client.Connection;
import io.nats.client.Nats;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.IOException;

/**
 * NATS connection configuration for the RHS service.
 *
 * <p>Provides a shared {@link Connection} bean used by publishers and consumers
 * throughout the service. Subject patterns follow the hierarchy defined in
 * ARCHITECTURE_SPEC §15.2:
 *
 * <pre>
 *   rhs.{tenant_id}.trips.{trip_id}.state      — trip FSM state transitions
 *   rhs.{tenant_id}.trips.{trip_id}.eta        — ETA updates for passengers/drivers
 *   rhs.{tenant_id}.vehicles.{vehicle_id}.location — real-time vehicle GPS telemetry
 * </pre>
 *
 * <p>All subjects are parameterised by {@code tenant_id} to enforce per-tenant
 * isolation at the messaging layer (BL-001).
 */
@Slf4j
@Configuration
public class NatsConfig {

    /** Subject pattern for trip state-machine transitions (FR-RHS-002). */
    public static final String SUBJECT_TRIP_STATE = "rhs.%s.trips.%s.state";

    /** Subject pattern for ETA update broadcasts (BL-005: auto-refund if ETA late > 10 min). */
    public static final String SUBJECT_TRIP_ETA = "rhs.%s.trips.%s.eta";

    /** Subject pattern for real-time vehicle GPS location telemetry. */
    public static final String SUBJECT_VEHICLE_LOC = "rhs.%s.vehicles.%s.location";

    @Bean
    public Connection natsConnection(
            @Value("${nats.server-url:nats://localhost:4222}") String serverUrl) {
        log.info("Connecting to NATS server at {}", serverUrl);
        try {
            Connection connection = Nats.connect(serverUrl);
            log.info("NATS connection established — status={}", connection.getStatus());
            return connection;
        } catch (IOException e) {
            log.error("Failed to connect to NATS server at {}: {}", serverUrl, e.getMessage(), e);
            throw new PlatformException(
                "NATS_CONNECTION_FAILED",
                503,  // Service Unavailable
                "Unable to establish NATS connection. Please ensure NATS server is running at: " + serverUrl
            );
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("NATS connection interrupted: {}", e.getMessage(), e);
            throw new PlatformException(
                "NATS_CONNECTION_INTERRUPTED",
                503,  // Service Unavailable
                "NATS connection was interrupted: " + e.getMessage()
            );
        }
    }
}
