package com.example.examplefeature.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Response DTO for ExampleEntity.
 * Demonstrates proper DTO pattern with Lombok.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ExampleResponse {

    private Long id;
    private String uuid;
    private String name;
    private String description;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /**
     * Factory method to create response from entity.
     * This demonstrates the proper conversion pattern.
     */
    public static ExampleResponse fromEntity(ExampleEntity entity) {
        return ExampleResponse.builder()
                .id(entity.getId())
                .uuid(entity.getUuid())
                .name(entity.getName())
                .description(entity.getDescription())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .build();
    }
}
