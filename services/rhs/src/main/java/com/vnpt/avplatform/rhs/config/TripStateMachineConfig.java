package com.vnpt.avplatform.rhs.config;

/**
 * Documents the RHS trip state machine as defined in FR-RHS-002.
 *
 * <p><b>Happy-path transitions:</b>
 * <pre>
 *   REQUESTED → MATCHED → VEHICLE_ENROUTE → ARRIVED → BOARDING
 *             → IN_PROGRESS → ALIGHTING → COMPLETED
 * </pre>
 *
 * <p><b>Exception states (reachable from any active state):</b>
 * <ul>
 *   <li>{@link TripStatus#REMOTE_INTERVENTION} — operator remotely takes control of the AV.</li>
 *   <li>{@link TripStatus#SAFETY_STOP} — autonomous safety system halts the vehicle.</li>
 *   <li>{@link TripStatus#CANCELLED} — trip cancelled by passenger, system, or operator.</li>
 * </ul>
 *
 * <p><b>Key business rules:</b>
 * <ul>
 *   <li>BL-002: Fare is calculated by the FPE — RHS must NOT hardcode or re-derive fares.</li>
 *   <li>BL-003: PAY escrow must be confirmed before driver payout is released.</li>
 *   <li>BL-005: Auto-refund is triggered when ETA is late by more than 10 minutes.</li>
 * </ul>
 */
public class TripStateMachineConfig {

    /** All possible states in the RHS trip lifecycle (FR-RHS-002). */
    public enum TripStatus {
        /** Passenger has submitted a ride request; awaiting driver/vehicle match. */
        REQUESTED,
        /** A vehicle has been matched and assigned to the trip. */
        MATCHED,
        /** The matched vehicle is en route to the pickup location. */
        VEHICLE_ENROUTE,
        /** The vehicle has arrived at the pickup location. */
        ARRIVED,
        /** Passenger is boarding the vehicle. */
        BOARDING,
        /** Trip is active; vehicle is transporting the passenger. */
        IN_PROGRESS,
        /** Passenger is alighting at the destination. */
        ALIGHTING,
        /** Trip successfully completed; triggers fare settlement. */
        COMPLETED,
        /** Trip was cancelled before reaching COMPLETED. */
        CANCELLED,
        /** Operator remotely intervened; manual driving mode active. */
        REMOTE_INTERVENTION,
        /** Autonomous safety system halted the vehicle. */
        SAFETY_STOP
    }
}
