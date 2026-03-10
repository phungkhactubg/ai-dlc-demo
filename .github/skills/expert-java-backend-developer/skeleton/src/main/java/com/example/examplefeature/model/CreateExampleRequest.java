package com.example.examplefeature.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * CreateExampleRequest represents the DTO for creating a new ExampleEntity.
 *
 * Architectural Notes:
 * - Uses Java 17+ record for immutability
 * - Uses Jakarta Bean Validation annotations for input validation
 * - Validation is enforced at the Controller layer with @Valid
 *
 * Common validation annotations:
 * - @NotBlank: Field must not be null and must contain at least one non-whitespace character
 * - @NotNull: Field must not be null
 * - @Size: Validates string length or collection size
 * - @Email: Validates email format
 * - @Min/@Max: Validates numeric ranges
 * - @Pattern: Validates against a regex pattern
 * - @Positive/@Negative: Validates positive/negative numbers
 */
public record CreateExampleRequest(
    @NotBlank(message = "Name is required")
    @Size(min = 3, max = 255, message = "Name must be between 3 and 255 characters")
    String name,

    @Size(max = 1000, message = "Description must not exceed 1000 characters")
    String description
) {
    /**
     * Additional validation logic can be added here.
     * This is called after standard Bean Validation passes.
     */
    public CreateExampleRequest {
        // Normalize the name (trim whitespace)
        if (name != null) {
            name = name.trim();
        }
    }
}

/**
 * UpdateExampleRequest represents the DTO for updating an existing ExampleEntity.
 * All fields are optional to support partial updates.
 */
public record UpdateExampleRequest(
    @Size(min = 3, max = 255, message = "Name must be between 3 and 255 characters")
    String name,

    @Size(max = 1000, message = "Description must not exceed 1000 characters")
    String description,

    @Size(max = 50, message = "Status must not exceed 50 characters")
    String status
) {
    /**
     * Check if the request has any data to update.
     */
    public boolean hasData() {
        return name != null || description != null || status != null;
    }
}

/**
 * ExampleDTO represents the response DTO for ExampleEntity.
 * This is what gets returned to clients via the API.
 *
 * Note: Using @Value from Lombok would be similar to this record.
 */
public record ExampleDTO(
    String id,
    String name,
    String description,
    String status,
    String tenantId,
    String createdAt,
    String updatedAt
) {
    /**
     * Factory method to create a DTO from an entity.
     * This centralizes the conversion logic.
     */
    public static ExampleDTO from(ExampleEntity entity) {
        return new ExampleDTO(
            entity.getId().toString(),
            entity.getName(),
            entity.getDescription(),
            entity.getStatus(),
            entity.getTenantId(),
            entity.getCreatedAt().toString(),
            entity.getUpdatedAt().toString()
        );
    }
}

/**
 * ExampleFilter represents query parameters for searching/filtering entities.
 * This is typically used in controller methods for complex queries.
 */
public record ExampleFilter(
    String status,
    String search,
    Integer page,
    Integer size,
    String sortBy,
    String sortDirection
) {
    /**
     * Provides default values for pagination.
     */
    public ExampleFilter {
        if (page == null || page < 0) {
            page = 0;
        }
        if (size == null || size <= 0) {
            size = 20;
        }
        if (size > 100) {
            size = 100;  // Max page size
        }
        if (sortBy == null || sortBy.isBlank()) {
            sortBy = "createdAt";
        }
        if (sortDirection == null || sortDirection.isBlank()) {
            sortDirection = "DESC";
        }
    }

    public static ExampleFilter defaults() {
        return new ExampleFilter(null, null, 0, 20, "createdAt", "DESC");
    }
}
