package com.example.examplefeature.service;

import com.example.examplefeature.model.*;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

/**
 * ExampleService defines the business logic contract for example entities.
 * Services MUST depend on interfaces, not concrete implementations.
 *
 * Architectural Notes:
 * - This is an interface - the implementation is in ExampleServiceImpl
 * - Controllers depend on this interface, not the implementation
 * - Methods are organized by CRUD operations and business operations
 * - All methods that modify data should be annotated with @Transactional in implementation
 * - Read operations should be annotated with @Transactional(readOnly = true)
 */
public interface ExampleService {

    /**
     * Create a new example entity.
     *
     * @param request The creation request with validation applied
     * @param tenantId The tenant ID for multi-tenancy
     * @return The created entity as a DTO
     * @throws DuplicateResourceException if an entity with the same name exists
     */
    ExampleDTO create(CreateExampleRequest request, String tenantId);

    /**
     * Update an existing example entity.
     *
     * @param id The ID of the entity to update
     * @param request The update request (partial update supported)
     * @param tenantId The tenant ID for security (can only update own entities)
     * @return The updated entity as a DTO
     * @throws ResourceNotFoundException if entity not found
     */
    ExampleDTO update(String id, UpdateExampleRequest request, String tenantId);

    /**
     * Delete an example entity by ID.
     *
     * @param id The ID of the entity to delete
     * @param tenantId The tenant ID for security
     * @throws ResourceNotFoundException if entity not found
     */
    void delete(String id, String tenantId);

    /**
     * Get an example entity by ID.
     *
     * @param id The ID of the entity
     * @param tenantId The tenant ID for security
     * @return The entity as a DTO
     * @throws ResourceNotFoundException if entity not found
     */
    ExampleDTO getById(String id, String tenantId);

    /**
     * Get an example entity by ID, returning Optional.
     *
     * @param id The ID of the entity
     * @param tenantId The tenant ID for security
     * @return Optional containing the DTO if found
     */
    Optional<ExampleDTO> findById(String id, String tenantId);

    /**
     * Get all example entities for a tenant.
     *
     * @param tenantId The tenant ID
     * @return List of all entities as DTOs
     */
    List<ExampleDTO> getAllByTenant(String tenantId);

    /**
     * Get example entities for a tenant with pagination.
     *
     * @param tenantId The tenant ID
     * @param pageable Pagination parameters
     * @return Page of entities as DTOs
     */
    Page<ExampleDTO> getAllByTenant(String tenantId, Pageable pageable);

    /**
     * Get example entities by status for a tenant.
     *
     * @param status The status to filter by
     * @param tenantId The tenant ID
     * @return List of entities as DTOs
     */
    List<ExampleDTO> getByStatus(String status, String tenantId);

    /**
     * Search example entities by name for a tenant.
     *
     * @param search The search term (case-insensitive partial match)
     * @param tenantId The tenant ID
     * @param pageable Pagination parameters
     * @return Page of matching entities as DTOs
     */
    Page<ExampleDTO> search(String search, String tenantId, Pageable pageable);

    /**
     * Mark an entity as completed.
     * This is a business operation that changes the entity's status.
     *
     * @param id The ID of the entity
     * @param tenantId The tenant ID
     * @return The updated entity as a DTO
     * @throws ResourceNotFoundException if entity not found
     * @throws InvalidStateException if entity is not in a valid state for completion
     */
    ExampleDTO markAsCompleted(String id, String tenantId);

    /**
     * Get statistics for a tenant.
     *
     * @param tenantId The tenant ID
     * @return Statistics object with counts and aggregations
     */
    ExampleStatistics getStatistics(String tenantId);

    /**
     * Bulk delete entities by status for a tenant.
     *
     * @param status The status of entities to delete
     * @param tenantId The tenant ID
     * @return Number of entities deleted
     */
    long deleteByStatus(String status, String tenantId);
}

/**
 * ExampleStatistics represents aggregated statistics for example entities.
 */
record ExampleStatistics(
    long totalCount,
    long pendingCount,
    long completedCount,
    long failedCount
) {}
