package com.example.examplefeature.service.impl;

import com.example.examplefeature.exception.*;
import com.example.examplefeature.model.*;
import com.example.examplefeature.repository.ExampleRepository;
import com.example.examplefeature.service.ExampleService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

/**
 * ExampleServiceImpl implements the business logic for example entities.
 *
 * Architectural Notes:
 * - Uses @RequiredArgsConstructor for constructor injection (Lombok)
 * - All dependencies are final for immutability
 * - Uses @Transactional for transaction management
 * - Uses @Transactional(readOnly = true) for read operations
 * - Logs important operations with SLF4J
 * - Wraps low-level exceptions with domain-specific exceptions
 * - Validates business rules before persistence
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ExampleServiceImpl implements ExampleService {

    private final ExampleRepository repository;

    @Override
    @Transactional
    public ExampleDTO create(CreateExampleRequest request, String tenantId) {
        log.info("Creating example entity for tenant: {}, name: {}", tenantId, request.name());

        // Business validation: Check for duplicate
        if (repository.existsByNameAndTenantId(request.name(), tenantId)) {
            log.warn("Duplicate entity name detected: {} for tenant: {}", request.name(), tenantId);
            throw new DuplicateResourceException("ExampleEntity", request.name());
        }

        // Create entity from request
        ExampleEntity entity = ExampleEntity.from(request, tenantId);

        // Save entity
        ExampleEntity savedEntity = repository.save(entity);

        log.info("Example entity created successfully: id={}, tenantId={}", savedEntity.getId(), tenantId);

        return ExampleDTO.from(savedEntity);
    }

    @Override
    @Transactional
    public ExampleDTO update(String id, UpdateExampleRequest request, String tenantId) {
        log.info("Updating example entity: id={}, tenantId={}", id, tenantId);

        // Validate input
        if (!request.hasData()) {
            throw new InvalidInputException("request", "empty", "No fields to update");
        }

        // Find entity
        ExampleEntity entity = findByIdAndValidate(id, tenantId);

        // Apply updates
        if (request.name() != null) {
            // Check for duplicate if name is being changed
            if (!entity.getName().equals(request.name()) &&
                repository.existsByNameAndTenantId(request.name(), tenantId)) {
                throw new DuplicateResourceException("ExampleEntity", request.name());
            }
            entity.setName(request.name());
        }

        if (request.description() != null) {
            entity.setDescription(request.description());
        }

        if (request.status() != null) {
            validateStatusTransition(entity.getStatus(), request.status());
            entity.setStatus(request.status());
        }

        // Save updated entity
        ExampleEntity savedEntity = repository.save(entity);

        log.info("Example entity updated successfully: id={}", id);

        return ExampleDTO.from(savedEntity);
    }

    @Override
    @Transactional
    public void delete(String id, String tenantId) {
        log.info("Deleting example entity: id={}, tenantId={}", id, tenantId);

        ExampleEntity entity = findByIdAndValidate(id, tenantId);

        // Additional business rule: Cannot delete completed entities
        if ("COMPLETED".equals(entity.getStatus())) {
            throw new InvalidStateException(entity.getStatus(), "Cannot delete COMPLETED entities");
        }

        repository.delete(entity);

        log.info("Example entity deleted successfully: id={}", id);
    }

    @Override
    @Transactional(readOnly = true)
    public ExampleDTO getById(String id, String tenantId) {
        log.debug("Getting example entity: id={}, tenantId={}", id, tenantId);

        ExampleEntity entity = findByIdAndValidate(id, tenantId);

        return ExampleDTO.from(entity);
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<ExampleDTO> findById(String id, String tenantId) {
        log.debug("Finding example entity: id={}, tenantId={}", id, tenantId);

        try {
            UUID uuid = UUID.fromString(id);
            return repository.findByIdAndTenantId(uuid, tenantId)
                .map(ExampleDTO::from);
        } catch (IllegalArgumentException e) {
            log.warn("Invalid UUID format: {}", id);
            return Optional.empty();
        }
    }

    @Override
    @Transactional(readOnly = true)
    public List<ExampleDTO> getAllByTenant(String tenantId) {
        log.debug("Getting all example entities for tenant: {}", tenantId);

        return repository.findByTenantId(tenantId).stream()
            .map(ExampleDTO::from)
            .collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public Page<ExampleDTO> getAllByTenant(String tenantId, Pageable pageable) {
        log.debug("Getting example entities for tenant: {} with pagination: {}", tenantId, pageable);

        return repository.findByTenantId(tenantId, pageable)
            .map(ExampleDTO::from);
    }

    @Override
    @Transactional(readOnly = true)
    public List<ExampleDTO> getByStatus(String status, String tenantId) {
        log.debug("Getting example entities by status: {} for tenant: {}", status, tenantId);

        return repository.findByStatusAndTenantId(status, tenantId).stream()
            .map(ExampleDTO::from)
            .collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public Page<ExampleDTO> search(String search, String tenantId, Pageable pageable) {
        log.debug("Searching example entities: query={}, tenant={}", search, tenantId);

        if (search == null || search.isBlank()) {
            return getAllByTenant(tenantId, pageable);
        }

        return repository.searchByTenantAndName(tenantId, search.trim(), pageable)
            .map(ExampleDTO::from);
    }

    @Override
    @Transactional
    public ExampleDTO markAsCompleted(String id, String tenantId) {
        log.info("Marking example entity as completed: id={}, tenantId={}", id, tenantId);

        ExampleEntity entity = findByIdAndValidate(id, tenantId);

        // Validate state transition
        validateStatusTransition(entity.getStatus(), "COMPLETED");

        entity.markAsCompleted();

        ExampleEntity savedEntity = repository.save(entity);

        log.info("Example entity marked as completed: id={}", id);

        return ExampleDTO.from(savedEntity);
    }

    @Override
    @Transactional(readOnly = true)
    public ExampleStatistics getStatistics(String tenantId) {
        log.debug("Getting statistics for tenant: {}", tenantId);

        long totalCount = repository.countByTenantIdAndStatus(tenantId, null);

        long pendingCount = repository.countByTenantIdAndStatus(tenantId, "PENDING");
        long completedCount = repository.countByTenantIdAndStatus(tenantId, "COMPLETED");
        long failedCount = repository.countByTenantIdAndStatus(tenantId, "FAILED");

        return new ExampleStatistics(totalCount, pendingCount, completedCount, failedCount);
    }

    @Override
    @Transactional
    public long deleteByStatus(String status, String tenantId) {
        log.info("Deleting example entities by status: {} for tenant: {}", status, tenantId);

        // Business rule: Cannot delete COMPLETED entities in bulk
        if ("COMPLETED".equals(status)) {
            throw new InvalidStateException("COMPLETED", "Cannot delete COMPLETED entities in bulk");
        }

        long count = repository.countByTenantIdAndStatus(tenantId, status);

        if (count > 0) {
            repository.deleteByTenantIdAndStatus(tenantId, status);
            log.info("Deleted {} example entities with status: {} for tenant: {}", count, status, tenantId);
        }

        return count;
    }

    /**
     * Helper method to find entity by ID and validate tenant access.
     * Throws ResourceNotFoundException if entity not found or doesn't belong to tenant.
     */
    private ExampleEntity findByIdAndValidate(String id, String tenantId) {
        try {
            UUID uuid = UUID.fromString(id);
            return repository.findByIdAndTenantId(uuid, tenantId)
                .orElseThrow(() -> new ResourceNotFoundException("ExampleEntity", id));
        } catch (IllegalArgumentException e) {
            throw new InvalidInputException("id", id, "Invalid UUID format");
        }
    }

    /**
     * Validate that a status transition is allowed.
     * This enforces business rules for state transitions.
     */
    private void validateStatusTransition(String currentStatus, String newStatus) {
        if (Objects.equals(currentStatus, newStatus)) {
            return;  // No change
        }

        // Define allowed state transitions
        Map<String, Set<String>> allowedTransitions = Map.of(
            "PENDING", Set.of("IN_PROGRESS", "FAILED", "COMPLETED"),
            "IN_PROGRESS", Set.of("COMPLETED", "FAILED"),
            "FAILED", Set.of("PENDING", "IN_PROGRESS"),
            "COMPLETED", Set.of()  // Terminal state - no transitions allowed
        );

        Set<String> allowedNewStates = allowedTransitions.getOrDefault(currentStatus, Set.of());

        if (!allowedNewStates.contains(newStatus)) {
            throw new InvalidStateException(currentStatus, newStatus);
        }
    }
}
