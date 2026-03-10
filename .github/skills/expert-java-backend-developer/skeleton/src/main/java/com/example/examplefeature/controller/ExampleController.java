package com.example.examplefeature.controller;

import com.example.examplefeature.model.*;
import com.example.examplefeature.service.ExampleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * ExampleController handles HTTP requests for example entities.
 *
 * Architectural Notes:
 * - Uses @RestController for REST API endpoints
 * - Uses @RequiredArgsConstructor for constructor injection
 * - Uses @Valid for Bean Validation on request bodies
 * - Uses @PreAuthorize for method-level security
 * - Uses OpenAPI annotations for API documentation
 * - Returns ResponseEntity for flexible HTTP responses
 * - Handles tenant context via headers or security context
 * - Logs important operations with SLF4J
 *
 * Security:
 * - Add @PreAuthorize annotations for authorization
 * - Extract tenant ID from security context or headers
 * - Validate tenant access to resources
 */
@RestController
@RequestMapping("/api/v1/examples")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Examples", description = "Example entity management APIs")
public class ExampleController {

    private final ExampleService exampleService;

    /**
     * Create a new example entity.
     *
     * POST /api/v1/examples
     */
    @PostMapping
    @Operation(summary = "Create a new example entity")
    @PreAuthorize("hasAuthority('EXAMPLE_CREATE')")
    public ResponseEntity<ExampleDTO> create(
            @Parameter(description = "Example creation request")
            @Valid @RequestBody CreateExampleRequest request,

            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.info("POST /api/v1/examples - tenant: {}, name: {}", tenantId, request.name());

        ExampleDTO created = exampleService.create(request, tenantId);

        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(created);
    }

    /**
     * Update an existing example entity.
     *
     * PUT /api/v1/examples/{id}
     */
    @PutMapping("/{id}")
    @Operation(summary = "Update an example entity")
    @PreAuthorize("hasAuthority('EXAMPLE_UPDATE')")
    public ResponseEntity<ExampleDTO> update(
            @Parameter(description = "Example entity ID")
            @PathVariable String id,

            @Parameter(description = "Update request")
            @Valid @RequestBody UpdateExampleRequest request,

            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.info("PUT /api/v1/examples/{} - tenant: {}", id, tenantId);

        ExampleDTO updated = exampleService.update(id, request, tenantId);

        return ResponseEntity.ok(updated);
    }

    /**
     * Patch (partial update) an example entity.
     *
     * PATCH /api/v1/examples/{id}
     */
    @PatchMapping("/{id}")
    @Operation(summary = "Partially update an example entity")
    @PreAuthorize("hasAuthority('EXAMPLE_UPDATE')")
    public ResponseEntity<ExampleDTO> patch(
            @PathVariable String id,
            @RequestBody UpdateExampleRequest request,
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.info("PATCH /api/v1/examples/{} - tenant: {}", id, tenantId);

        ExampleDTO updated = exampleService.update(id, request, tenantId);

        return ResponseEntity.ok(updated);
    }

    /**
     * Delete an example entity.
     *
     * DELETE /api/v1/examples/{id}
     */
    @DeleteMapping("/{id}")
    @Operation(summary = "Delete an example entity")
    @PreAuthorize("hasAuthority('EXAMPLE_DELETE')")
    public ResponseEntity<Void> delete(
            @PathVariable String id,
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.info("DELETE /api/v1/examples/{} - tenant: {}", id, tenantId);

        exampleService.delete(id, tenantId);

        return ResponseEntity.noContent().build();
    }

    /**
     * Get an example entity by ID.
     *
     * GET /api/v1/examples/{id}
     */
    @GetMapping("/{id}")
    @Operation(summary = "Get an example entity by ID")
    @PreAuthorize("hasAuthority('EXAMPLE_READ')")
    public ResponseEntity<ExampleDTO> getById(
            @PathVariable String id,
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.debug("GET /api/v1/examples/{} - tenant: {}", id, tenantId);

        ExampleDTO entity = exampleService.getById(id, tenantId);

        return ResponseEntity.ok(entity);
    }

    /**
     * Get all example entities with pagination.
     *
     * GET /api/v1/examples?page=0&size=20&sort=createdAt,desc
     */
    @GetMapping
    @Operation(summary = "Get all example entities with pagination")
    @PreAuthorize("hasAuthority('EXAMPLE_READ')")
    public ResponseEntity<Page<ExampleDTO>> getAll(
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId,

            @Parameter(description = "Page number (0-based)")
            @RequestParam(defaultValue = "0") int page,

            @Parameter(description = "Page size")
            @RequestParam(defaultValue = "20") int size,

            @Parameter(description = "Sort field")
            @RequestParam(defaultValue = "createdAt") String sortBy,

            @Parameter(description = "Sort direction")
            @RequestParam(defaultValue = "desc") String sortDirection) {

        log.debug("GET /api/v1/examples - tenant: {}, page: {}, size: {}", tenantId, page, size);

        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<ExampleDTO> result = exampleService.getAllByTenant(tenantId, pageable);

        return ResponseEntity.ok(result);
    }

    /**
     * Search example entities by name.
     *
     * GET /api/v1/examples/search?query=text&page=0&size=20
     */
    @GetMapping("/search")
    @Operation(summary = "Search example entities by name")
    @PreAuthorize("hasAuthority('EXAMPLE_READ')")
    public ResponseEntity<Page<ExampleDTO>> search(
            @RequestParam String query,

            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId,

            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String sortDirection) {

        log.debug("GET /api/v1/examples/search - tenant: {}, query: {}", tenantId, query);

        Sort.Direction direction = Sort.Direction.fromString(sortDirection);
        Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));

        Page<ExampleDTO> result = exampleService.search(query, tenantId, pageable);

        return ResponseEntity.ok(result);
    }

    /**
     * Get example entities by status.
     *
     * GET /api/v1/examples/by-status?status=PENDING
     */
    @GetMapping("/by-status")
    @Operation(summary = "Get example entities by status")
    @PreAuthorize("hasAuthority('EXAMPLE_READ')")
    public ResponseEntity<List<ExampleDTO>> getByStatus(
            @RequestParam String status,

            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.debug("GET /api/v1/examples/by-status - tenant: {}, status: {}", tenantId, status);

        List<ExampleDTO> result = exampleService.getByStatus(status, tenantId);

        return ResponseEntity.ok(result);
    }

    /**
     * Mark an example entity as completed.
     *
     * POST /api/v1/examples/{id}/complete
     */
    @PostMapping("/{id}/complete")
    @Operation(summary = "Mark an example entity as completed")
    @PreAuthorize("hasAuthority('EXAMPLE_UPDATE')")
    public ResponseEntity<ExampleDTO> markAsCompleted(
            @PathVariable String id,
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.info("POST /api/v1/examples/{}/complete - tenant: {}", id, tenantId);

        ExampleDTO result = exampleService.markAsCompleted(id, tenantId);

        return ResponseEntity.ok(result);
    }

    /**
     * Get statistics for example entities.
     *
     * GET /api/v1/examples/statistics
     */
    @GetMapping("/statistics")
    @Operation(summary = "Get statistics for example entities")
    @PreAuthorize("hasAuthority('EXAMPLE_READ')")
    public ResponseEntity<ExampleStatistics> getStatistics(
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.debug("GET /api/v1/examples/statistics - tenant: {}", tenantId);

        ExampleStatistics statistics = exampleService.getStatistics(tenantId);

        return ResponseEntity.ok(statistics);
    }

    /**
     * Bulk delete example entities by status.
     *
     * DELETE /api/v1/examples/bulk?status=FAILED
     */
    @DeleteMapping("/bulk")
    @Operation(summary = "Bulk delete example entities by status")
    @PreAuthorize("hasAuthority('EXAMPLE_DELETE')")
    public ResponseEntity<Map<String, Object>> bulkDelete(
            @RequestParam String status,

            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default")
            String tenantId) {

        log.info("DELETE /api/v1/examples/bulk - tenant: {}, status: {}", tenantId, status);

        long deletedCount = exampleService.deleteByStatus(status, tenantId);

        return ResponseEntity.ok(Map.of(
            "deletedCount", deletedCount,
            "status", status
        ));
    }
}
