package com.example.examplefeature.service;

import com.example.examplefeature.exception.DuplicateResourceException;
import com.example.examplefeature.exception.InvalidStateException;
import com.example.examplefeature.exception.ResourceNotFoundException;
import com.example.examplefeature.model.*;
import com.example.examplefeature.repository.ExampleRepository;
import com.example.examplefeature.service.impl.ExampleServiceImpl;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.time.LocalDateTime;
import java.util.*;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for ExampleService.
 *
 * Architectural Notes:
 * - Uses JUnit 5 for testing framework
 * - Uses Mockito for mocking dependencies
 * - Uses AssertJ for fluent assertions
 * - Follows AAA pattern (Arrange, Act, Assert)
 * - Tests both happy path and edge cases
 * - Mocks repository to test service in isolation
 *
 * Testing Best Practices:
 * - One assertion per test (when possible)
 * - Descriptive test names that explain what is being tested
 * - Test structure: Given-When-Then comments
 * - Test naming convention: should[ExpectedBehavior]When[StateUnderTest]
 * - Reset mocks between tests
 * - Use @BeforeEach for common setup
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("ExampleService Tests")
class ExampleServiceTest {

    @Mock
    private ExampleRepository repository;

    @InjectMocks
    private ExampleServiceImpl service;

    private final String TENANT_ID = "test-tenant";
    private ExampleEntity testEntity;
    private CreateExampleRequest createRequest;
    private UpdateExampleRequest updateRequest;

    @BeforeEach
    void setUp() {
        // Given: A test entity
        testEntity = ExampleEntity.builder()
            .id(UUID.randomUUID())
            .name("Test Entity")
            .description("Test Description")
            .status("PENDING")
            .tenantId(TENANT_ID)
            .createdAt(LocalDateTime.now())
            .updatedAt(LocalDateTime.now())
            .build();

        // Given: Create and update requests
        createRequest = new CreateExampleRequest("Test Entity", "Test Description");
        updateRequest = new UpdateExampleRequest("Updated Name", "Updated Description", null);
    }

    @Nested
    @DisplayName("Create Entity")
    class CreateEntityTests {

        @Test
        @DisplayName("should create entity successfully when valid request provided")
        void shouldCreateEntitySuccessfully() {
            // Given
            when(repository.existsByNameAndTenantId(anyString(), eq(TENANT_ID))).thenReturn(false);
            when(repository.save(any(ExampleEntity.class))).thenReturn(testEntity);

            // When
            ExampleDTO result = service.create(createRequest, TENANT_ID);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.name()).isEqualTo("Test Entity");
            assertThat(result.tenantId()).isEqualTo(TENANT_ID);

            verify(repository).existsByNameAndTenantId("Test Entity", TENANT_ID);
            verify(repository).save(any(ExampleEntity.class));
        }

        @Test
        @DisplayName("should throw DuplicateResourceException when entity name already exists")
        void shouldThrowExceptionWhenDuplicateName() {
            // Given
            when(repository.existsByNameAndTenantId(anyString(), eq(TENANT_ID))).thenReturn(true);

            // When/Then
            assertThatThrownBy(() -> service.create(createRequest, TENANT_ID))
                .isInstanceOf(DuplicateResourceException.class)
                .hasMessageContaining("already exists");

            verify(repository, never()).save(any());
        }
    }

    @Nested
    @DisplayName("Update Entity")
    class UpdateEntityTests {

        @Test
        @DisplayName("should update entity successfully when entity exists")
        void shouldUpdateEntitySuccessfully() {
            // Given
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.of(testEntity));
            when(repository.existsByNameAndTenantId(anyString(), eq(TENANT_ID))).thenReturn(false);
            when(repository.save(any(ExampleEntity.class))).thenReturn(testEntity);

            // When
            ExampleDTO result = service.update(
                testEntity.getId().toString(),
                updateRequest,
                TENANT_ID
            );

            // Then
            assertThat(result).isNotNull();
            verify(repository).save(any(ExampleEntity.class));
        }

        @Test
        @DisplayName("should throw ResourceNotFoundException when entity not found")
        void shouldThrowExceptionWhenEntityNotFound() {
            // Given
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.empty());

            // When/Then
            assertThatThrownBy(() ->
                service.update(UUID.randomUUID().toString(), updateRequest, TENANT_ID)
            ).isInstanceOf(ResourceNotFoundException.class);

            verify(repository, never()).save(any());
        }
    }

    @Nested
    @DisplayName("Delete Entity")
    class DeleteEntityTests {

        @Test
        @DisplayName("should delete entity successfully when entity exists and not completed")
        void shouldDeleteEntitySuccessfully() {
            // Given
            testEntity.setStatus("PENDING");
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.of(testEntity));

            // When
            service.delete(testEntity.getId().toString(), TENANT_ID);

            // Then
            verify(repository).delete(testEntity);
        }

        @Test
        @DisplayName("should throw InvalidStateException when entity is completed")
        void shouldThrowExceptionWhenEntityCompleted() {
            // Given
            testEntity.setStatus("COMPLETED");
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.of(testEntity));

            // When/Then
            assertThatThrownBy(() ->
                service.delete(testEntity.getId().toString(), TENANT_ID)
            ).isInstanceOf(InvalidStateException.class);

            verify(repository, never()).delete(any());
        }
    }

    @Nested
    @DisplayName("Get Entity")
    class GetEntityTests {

        @Test
        @DisplayName("should return entity when entity exists")
        void shouldReturnEntityWhenExists() {
            // Given
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.of(testEntity));

            // When
            ExampleDTO result = service.getById(testEntity.getId().toString(), TENANT_ID);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.id()).isEqualTo(testEntity.getId().toString());
        }

        @Test
        @DisplayName("should throw ResourceNotFoundException when entity not found")
        void shouldThrowExceptionWhenNotFound() {
            // Given
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.empty());

            // When/Then
            assertThatThrownBy(() ->
                service.getById(UUID.randomUUID().toString(), TENANT_ID)
            ).isInstanceOf(ResourceNotFoundException.class);
        }
    }

    @Nested
    @DisplayName("Search Entities")
    class SearchEntitiesTests {

        @Test
        @DisplayName("should return paginated results when search term provided")
        void shouldReturnPaginatedResults() {
            // Given
            Pageable pageable = PageRequest.of(0, 20);
            Page<ExampleEntity> entityPage = new PageImpl<>(
                List.of(testEntity),
                pageable,
                1
            );

            when(repository.searchByTenantAndName(eq(TENANT_ID), anyString(), any(Pageable)))
                .thenReturn(entityPage);

            // When
            Page<ExampleDTO> result = service.search("test", TENANT_ID, pageable);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.getContent()).hasSize(1);
            assertThat(result.getTotalElements()).isEqualTo(1);
        }

        @Test
        @DisplayName("should return all entities when search term is blank")
        void shouldReturnAllEntitiesWhenBlankSearch() {
            // Given
            Pageable pageable = PageRequest.of(0, 20);
            Page<ExampleEntity> entityPage = new PageImpl<>(
                List.of(testEntity),
                pageable,
                1
            );

            when(repository.findByTenantId(eq(TENANT_ID), any(Pageable)))
                .thenReturn(entityPage);

            // When
            Page<ExampleDTO> result = service.search("  ", TENANT_ID, pageable);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.getContent()).hasSize(1);
        }
    }

    @Nested
    @DisplayName("Mark as Completed")
    class MarkAsCompletedTests {

        @Test
        @DisplayName("should mark entity as completed when status transition is valid")
        void shouldMarkAsCompletedSuccessfully() {
            // Given
            testEntity.setStatus("IN_PROGRESS");
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.of(testEntity));
            when(repository.save(any(ExampleEntity.class))).thenReturn(testEntity);

            // When
            ExampleDTO result = service.markAsCompleted(
                testEntity.getId().toString(),
                TENANT_ID
            );

            // Then
            assertThat(result).isNotNull();
            assertThat(testEntity.getStatus()).isEqualTo("COMPLETED");
            verify(repository).save(testEntity);
        }

        @Test
        @DisplayName("should throw InvalidStateException when transition is not allowed")
        void shouldThrowExceptionWhenInvalidTransition() {
            // Given
            testEntity.setStatus("FAILED");
            when(repository.findByIdAndTenantId(any(UUID.class), eq(TENANT_ID)))
                .thenReturn(Optional.of(testEntity));

            // When/Then
            assertThatThrownBy(() ->
                service.markAsCompleted(testEntity.getId().toString(), TENANT_ID)
            ).isInstanceOf(InvalidStateException.class);

            verify(repository, never()).save(any());
        }
    }

    @Nested
    @DisplayName("Get Statistics")
    class GetStatisticsTests {

        @Test
        @DisplayName("should return statistics with counts by status")
        void shouldReturnStatistics() {
            // Given
            when(repository.countByTenantIdAndStatus(eq(TENANT_ID), isNull()))
                .thenReturn(10L);
            when(repository.countByTenantIdAndStatus(eq(TENANT_ID), eq("PENDING")))
                .thenReturn(5L);
            when(repository.countByTenantIdAndStatus(eq(TENANT_ID), eq("COMPLETED")))
                .thenReturn(3L);
            when(repository.countByTenantIdAndStatus(eq(TENANT_ID), eq("FAILED")))
                .thenReturn(2L);

            // When
            ExampleStatistics result = service.getStatistics(TENANT_ID);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.totalCount()).isEqualTo(10L);
            assertThat(result.pendingCount()).isEqualTo(5L);
            assertThat(result.completedCount()).isEqualTo(3L);
            assertThat(result.failedCount()).isEqualTo(2L);
        }
    }
}
