package com.example.examplefeature.repository;

import com.example.examplefeature.model.ExampleEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * ExampleRepository is the data access layer for ExampleEntity.
 *
 * Architectural Notes:
 * - Extends JpaRepository for standard CRUD operations
 * - Uses Spring Data JPA query derivation for custom queries
 * - Supports pagination and sorting
 * - Includes tenant isolation for multi-tenancy
 *
 * Common Spring Data JPA features:
 * - findAll(): Get all entities
 * - findById(ID): Get entity by ID (returns Optional)
 * - save(Entity): Save or update entity
 * - deleteById(ID): Delete entity by ID
 * - existsById(ID): Check if entity exists
 * - count(): Count all entities
 */
@Repository
public interface ExampleRepository extends JpaRepository<ExampleEntity, UUID> {

    /**
     * Find all entities for a specific tenant.
     * This supports multi-tenancy by filtering on tenantId.
     */
    List<ExampleEntity> findByTenantId(String tenantId);

    /**
     * Find entities by tenant with pagination.
     */
    Page<ExampleEntity> findByTenantId(String tenantId, Pageable pageable);

    /**
     * Find entity by ID and tenant.
     * This ensures tenant isolation - a tenant can only access their own entities.
     */
    Optional<ExampleEntity> findByIdAndTenantId(UUID id, String tenantId);

    /**
     * Find entities by status and tenant.
     */
    List<ExampleEntity> findByStatusAndTenantId(String status, String tenantId);

    /**
     * Find entities by status and tenant with pagination.
     */
    Page<ExampleEntity> findByStatusAndTenantId(String status, String tenantId, Pageable pageable);

    /**
     * Check if entity exists by name and tenant.
     * Useful for duplicate detection before insertion.
     */
    boolean existsByNameAndTenantId(String name, String tenantId);

    /**
     * Count entities by tenant and status.
     */
    long countByTenantIdAndStatus(String tenantId, String status);

    /**
     * Custom query using @Query annotation.
     * This is an alternative to query derivation for complex queries.
     */
    @Query("SELECT e FROM ExampleEntity e WHERE e.tenantId = :tenantId AND " +
           "LOWER(e.name) LIKE LOWER(CONCAT('%', :search, '%'))")
    Page<ExampleEntity> searchByTenantAndName(
        @Param("tenantId") String tenantId,
        @Param("search") String search,
        Pageable pageable
    );

    /**
     * Delete entities by tenant and status.
     * Use with caution - consider soft delete instead.
     */
    void deleteByTenantIdAndStatus(String tenantId, String status);

    /**
     * Find entities created after a certain date for a tenant.
     * Useful for reporting and analytics.
     */
    @Query("SELECT e FROM ExampleEntity e WHERE e.tenantId = :tenantId AND " +
           "e.createdAt > :startDate")
    List<ExampleEntity> findByTenantIdAndCreatedAtAfter(
        @Param("tenantId") String tenantId,
        @Param("startDate") java.time.LocalDateTime startDate
    );
}
