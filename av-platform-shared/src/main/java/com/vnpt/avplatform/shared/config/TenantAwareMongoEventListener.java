package com.vnpt.avplatform.shared.config;

import com.vnpt.avplatform.shared.exception.PlatformException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.mapping.event.AbstractMongoEventListener;
import org.springframework.data.mongodb.core.mapping.event.BeforeSaveEvent;
import org.springframework.stereotype.Component;
import org.springframework.util.ReflectionUtils;

import java.lang.reflect.Field;

/**
 * MongoDB event listener that enforces multi-tenant data safety before every save.
 *
 * <p><b>Responsibility:</b> Reject any attempt to persist a document with a missing
 * {@code tenant_id}, preventing cross-tenant data leakage at the database layer.
 *
 * <h3>How it works</h3>
 * <ol>
 *   <li>Spring Data MongoDB calls {@link #onBeforeSave(BeforeSaveEvent)} before
 *       executing an insert or update.</li>
 *   <li>The listener reflectively looks for a field named {@code tenantId} or
 *       {@code tenant_id} on the entity class.</li>
 *   <li>If the field exists but its value is {@code null} or blank, a
 *       {@link PlatformException#forbidden(String)} is thrown, which is mapped to
 *       HTTP 403 by the global exception handler.</li>
 * </ol>
 *
 * <h3>Conventions</h3>
 * <ul>
 *   <li>Entity classes that participate in multi-tenancy should declare a
 *       {@code String tenantId} field (or annotate the class with a marker).</li>
 *   <li>Entities without a tenant field (e.g. audit logs written by the system)
 *       are silently skipped.</li>
 * </ul>
 */
@Slf4j
@Component
public class TenantAwareMongoEventListener extends AbstractMongoEventListener<Object> {

    private static final String[] TENANT_FIELD_NAMES = {"tenantId", "tenant_id"};

    /**
     * Called by Spring Data MongoDB immediately before a document save operation.
     *
     * @param event the before-save event containing the source entity
     * @throws PlatformException if the entity has a tenant field whose value is null/blank
     */
    @Override
    public void onBeforeSave(BeforeSaveEvent<Object> event) {
        Object entity = event.getSource();
        if (entity == null) {
            return;
        }

        for (String fieldName : TENANT_FIELD_NAMES) {
            Field field = findField(entity.getClass(), fieldName);
            if (field == null) {
                continue;   // Entity is not tenant-scoped — skip
            }

            ReflectionUtils.makeAccessible(field);
            Object value = ReflectionUtils.getField(field, entity);

            if (value == null || value.toString().isBlank()) {
                throw PlatformException.forbidden(
                        "tenant_id is required: entity "
                        + entity.getClass().getSimpleName()
                        + " must carry a non-null tenantId before saving to MongoDB.");
            }
            // Valid tenant_id found — proceed
            return;
        }
    }

    // ─── private helpers ─────────────────────────────────────────────────────

    /**
     * Walks the class hierarchy to find a field by name (including superclasses).
     */
    private static Field findField(Class<?> clazz, String fieldName) {
        Class<?> current = clazz;
        while (current != null && current != Object.class) {
            try {
                return current.getDeclaredField(fieldName);
            } catch (NoSuchFieldException e) {
                log.trace("Field '{}' not found on {}; checking superclass",
                        fieldName, current.getSimpleName());
                current = current.getSuperclass();
            }
        }
        return null;
    }
}
