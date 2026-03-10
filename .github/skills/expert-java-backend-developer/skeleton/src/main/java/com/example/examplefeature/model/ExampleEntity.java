package com.example.examplefeature.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * ExampleEntity represents a core domain entity.
 * This is a JPA entity that maps to a database table.
 *
 * Architectural Notes:
 * - Uses @Data from Lombok for getters/setters/equals/hashCode/toString
 * - Uses @Builder for convenient object creation
 * - Uses @NoArgsConstructor and @AllArgsConstructor for JPA and Builder
 * - Supports multi-tenancy via tenantId
 * - Uses EntityListener for automatic audit fields
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "example_entities", indexes = {
    @Index(name = "idx_example_tenant_id", columnList = "tenant_id"),
    @Index(name = "idx_example_status", columnList = "status")
})
@EntityListeners(AuditingEntityListener.class)
public class ExampleEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "name", nullable = false, length = 255)
    private String name;

    @Column(name = "description", length = 1000)
    private String description;

    @Column(name = "status", nullable = false, length = 50)
    @Builder.Default
    private String status = "PENDING";

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * Business logic method to update the entity.
     * This is preferred over direct field access for encapsulation.
     */
    public void markAsCompleted() {
        this.status = "COMPLETED";
    }

    /**
     * Business logic method to check if entity is in a specific status.
     */
    public boolean isStatus(String status) {
        return this.status != null && this.status.equals(status);
    }

    /**
     * Factory method for creating a new entity from a request.
     * This ensures consistent entity creation across the application.
     */
    public static ExampleEntity from(CreateExampleRequest request, String tenantId) {
        return ExampleEntity.builder()
            .name(request.name())
            .description(request.description())
            .tenantId(tenantId)
            .status("PENDING")
            .build();
    }
}
