package com.vnpt.avplatform.shared;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for {@link TenantContext}.
 *
 * <p>Covers basic get/set/clear behaviour, thread isolation semantics,
 * and multi-cycle usage patterns — 20+ test cases in total.</p>
 */
@DisplayName("TenantContext")
class TenantContextTest {

    @BeforeEach
    void clearBefore() {
        TenantContext.clear();
    }

    @AfterEach
    void clearAfter() {
        TenantContext.clear();
    }

    // -------------------------------------------------------------------------
    // 1. Basic set / get
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("getTenantId returns null when no tenant has been set")
    void getTenantId_returnsNull_whenNotSet() {
        assertThat(TenantContext.getTenantId()).isNull();
    }

    @Test
    @DisplayName("setTenantId persists the value for the current thread")
    void setTenantId_persistsValue() {
        TenantContext.setTenantId("tenant-001");
        assertThat(TenantContext.getTenantId()).isEqualTo("tenant-001");
    }

    @Test
    @DisplayName("setTenantId accepts any non-null string, including empty string")
    void setTenantId_acceptsEmptyString() {
        TenantContext.setTenantId("");
        assertThat(TenantContext.getTenantId()).isEqualTo("");
    }

    @Test
    @DisplayName("setTenantId with UUID-format tenant ID is stored correctly")
    void setTenantId_withUuidFormat() {
        String uuid = "550e8400-e29b-41d4-a716-446655440000";
        TenantContext.setTenantId(uuid);
        assertThat(TenantContext.getTenantId()).isEqualTo(uuid);
    }

    @Test
    @DisplayName("setTenantId with special characters is stored correctly")
    void setTenantId_withSpecialCharacters() {
        String specialId = "tenant@vnpt.vn/2024";
        TenantContext.setTenantId(specialId);
        assertThat(TenantContext.getTenantId()).isEqualTo(specialId);
    }

    // -------------------------------------------------------------------------
    // 2. clear() behaviour
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("clear() removes a previously set tenant ID")
    void clear_removesPreviouslySetValue() {
        TenantContext.setTenantId("tenant-abc");
        TenantContext.clear();
        assertThat(TenantContext.getTenantId()).isNull();
    }

    @Test
    @DisplayName("clear() on an empty context does not throw")
    void clear_onEmptyContext_doesNotThrow() {
        // Should be a no-op when nothing is set
        TenantContext.clear();
        assertThat(TenantContext.getTenantId()).isNull();
    }

    @Test
    @DisplayName("getTenantId returns null after clear()")
    void getTenantId_returnsNull_afterClear() {
        TenantContext.setTenantId("some-tenant");
        TenantContext.clear();
        assertThat(TenantContext.getTenantId()).isNull();
    }

    // -------------------------------------------------------------------------
    // 3. Override / update behaviour
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("setTenantId overrides a previously set value")
    void setTenantId_overridesPreviousValue() {
        TenantContext.setTenantId("first-tenant");
        TenantContext.setTenantId("second-tenant");
        assertThat(TenantContext.getTenantId()).isEqualTo("second-tenant");
    }

    @Test
    @DisplayName("setTenantId called multiple times always reflects last value")
    void setTenantId_multipleCallsReflectsLastValue() {
        for (int i = 1; i <= 5; i++) {
            TenantContext.setTenantId("tenant-" + i);
        }
        assertThat(TenantContext.getTenantId()).isEqualTo("tenant-5");
    }

    // -------------------------------------------------------------------------
    // 4. Multi-cycle set / clear / set
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("set → clear → set cycle works correctly")
    void setClearSet_cycle() {
        TenantContext.setTenantId("first");
        TenantContext.clear();
        assertThat(TenantContext.getTenantId()).isNull();

        TenantContext.setTenantId("second");
        assertThat(TenantContext.getTenantId()).isEqualTo("second");
    }

    @Test
    @DisplayName("multiple set/clear cycles maintain isolation")
    void multipleCycles_maintainCorrectState() {
        for (int i = 0; i < 10; i++) {
            String expected = "cycle-tenant-" + i;
            TenantContext.setTenantId(expected);
            assertThat(TenantContext.getTenantId()).isEqualTo(expected);
            TenantContext.clear();
            assertThat(TenantContext.getTenantId()).isNull();
        }
    }

    @Test
    @DisplayName("clear() twice in a row does not throw and leaves context null")
    void doubleClear_doesNotThrow() {
        TenantContext.setTenantId("tenant-x");
        TenantContext.clear();
        TenantContext.clear(); // second clear — must be safe
        assertThat(TenantContext.getTenantId()).isNull();
    }

    // -------------------------------------------------------------------------
    // 5. Thread isolation
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("different threads have independent tenant contexts")
    void differentThreads_haveIndependentContexts() throws InterruptedException {
        int threadCount = 5;
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        CountDownLatch allSet = new CountDownLatch(threadCount);
        CountDownLatch allRead = new CountDownLatch(threadCount);
        List<String> capturedValues = new ArrayList<>(threadCount);

        for (int i = 0; i < threadCount; i++) {
            final String tenantId = "thread-tenant-" + i;
            executor.submit(() -> {
                try {
                    TenantContext.setTenantId(tenantId);
                    allSet.countDown();
                    allSet.await(5, TimeUnit.SECONDS); // wait for all threads to set their own
                    synchronized (capturedValues) {
                        capturedValues.add(TenantContext.getTenantId());
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    TenantContext.clear();
                    allRead.countDown();
                }
            });
        }

        allRead.await(10, TimeUnit.SECONDS);
        executor.shutdown();

        // Every thread must have seen its own tenant ID
        assertThat(capturedValues).hasSize(threadCount);
        for (int i = 0; i < threadCount; i++) {
            String expected = "thread-tenant-" + i;
            assertThat(capturedValues).contains(expected);
        }
    }

    @Test
    @DisplayName("child thread does not inherit parent thread's tenant context")
    void childThread_doesNotInheritParentContext() throws Exception {
        TenantContext.setTenantId("parent-tenant");

        AtomicReference<String> childValue = new AtomicReference<>();
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<?> future = executor.submit(() -> {
            childValue.set(TenantContext.getTenantId());
        });
        future.get(5, TimeUnit.SECONDS);
        executor.shutdown();

        // ThreadLocal does NOT propagate to child threads
        assertThat(childValue.get()).isNull();
        // Parent context is unchanged
        assertThat(TenantContext.getTenantId()).isEqualTo("parent-tenant");
    }

    @Test
    @DisplayName("clear() in one thread does not affect another thread's context")
    void clearInOneThread_doesNotAffectOtherThread() throws Exception {
        CountDownLatch parentSet = new CountDownLatch(1);
        CountDownLatch childCleared = new CountDownLatch(1);
        AtomicReference<String> parentValueAfterChildClear = new AtomicReference<>();

        TenantContext.setTenantId("stable-tenant");
        parentSet.countDown();

        ExecutorService executor = Executors.newSingleThreadExecutor();
        executor.submit(() -> {
            TenantContext.setTenantId("child-tenant");
            TenantContext.clear();
            childCleared.countDown();
        });

        childCleared.await(5, TimeUnit.SECONDS);
        parentValueAfterChildClear.set(TenantContext.getTenantId());
        executor.shutdown();

        assertThat(parentValueAfterChildClear.get()).isEqualTo("stable-tenant");
    }

    @Test
    @DisplayName("concurrent threads maintain per-thread isolation under high load")
    void concurrentThreads_maintainIsolation_underHighLoad() throws Exception {
        int taskCount = 20;
        ExecutorService executor = Executors.newFixedThreadPool(taskCount);
        CountDownLatch latch = new CountDownLatch(taskCount);
        List<Boolean> results = new ArrayList<>();

        for (int i = 0; i < taskCount; i++) {
            final String expectedId = "concurrent-tenant-" + i;
            executor.submit(() -> {
                TenantContext.setTenantId(expectedId);
                try {
                    Thread.sleep(10); // small delay to create interleaving
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                boolean correct = expectedId.equals(TenantContext.getTenantId());
                synchronized (results) {
                    results.add(correct);
                }
                TenantContext.clear();
                latch.countDown();
            });
        }

        latch.await(15, TimeUnit.SECONDS);
        executor.shutdown();

        assertThat(results).hasSize(taskCount);
        assertThat(results).doesNotContain(false);
    }

    // -------------------------------------------------------------------------
    // 6. Edge cases
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("setTenantId with null stores null (ThreadLocal behaviour)")
    void setTenantId_withNull_storesNull() {
        TenantContext.setTenantId("tenant-x");
        TenantContext.setTenantId(null);
        assertThat(TenantContext.getTenantId()).isNull();
    }

    @Test
    @DisplayName("getTenantId is idempotent — multiple reads return same value")
    void getTenantId_isIdempotent() {
        TenantContext.setTenantId("idempotent-tenant");
        String first  = TenantContext.getTenantId();
        String second = TenantContext.getTenantId();
        String third  = TenantContext.getTenantId();
        assertThat(first).isEqualTo(second).isEqualTo(third).isEqualTo("idempotent-tenant");
    }

    @Test
    @DisplayName("very long tenant ID is stored and retrieved correctly")
    void setTenantId_withVeryLongValue() {
        String longId = "t".repeat(1024);
        TenantContext.setTenantId(longId);
        assertThat(TenantContext.getTenantId()).isEqualTo(longId);
    }
}
