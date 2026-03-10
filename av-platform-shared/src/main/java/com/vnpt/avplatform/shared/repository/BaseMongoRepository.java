package com.vnpt.avplatform.shared.repository;

import com.vnpt.avplatform.shared.TenantContext;
import com.vnpt.avplatform.shared.exception.PlatformException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;

/**
 * Abstract base class for all MongoDB repositories in the AV Platform.
 *
 * <p><strong>Business Rule BL-001 (CRITICAL):</strong> Every MongoDB query MUST include
 * a {@code tenant_id} filter to guarantee strict tenant data isolation. This class
 * enforces that rule by providing {@link #withTenant(Criteria)} and
 * {@link #withTenantQuery(Query)} helper methods. All repository subclasses MUST
 * call one of these methods before executing any query against MongoDB.</p>
 *
 * <p>Both methods throw a {@link PlatformException} with error code
 * {@code TENANT_CONTEXT_MISSING} (HTTP 403) if {@link TenantContext#getTenantId()}
 * returns {@code null}, preventing any cross-tenant data leakage.</p>
 *
 * <p>Usage example in a subclass:</p>
 * <pre>{@code
 * @Repository
 * public class VehicleRepositoryImpl extends BaseMongoRepository implements VehicleCustomRepository {
 *
 *     public VehicleRepositoryImpl(MongoTemplate mongoTemplate) {
 *         super(mongoTemplate);
 *     }
 *
 *     public List<Vehicle> findActiveVehicles() {
 *         Query query = withTenantQuery(new Query())
 *                 .addCriteria(Criteria.where("status").is("ACTIVE"));
 *         return mongoTemplate.find(query, Vehicle.class);
 *     }
 *
 *     public List<Vehicle> findByType(String vehicleType) {
 *         Criteria criteria = withTenant(Criteria.where("type").is(vehicleType));
 *         return mongoTemplate.find(new Query(criteria), Vehicle.class);
 *     }
 * }
 * }</pre>
 */
@Slf4j
public abstract class BaseMongoRepository {

    /** MongoDB operation template; available to all subclasses. */
    protected final MongoTemplate mongoTemplate;

    /**
     * Constructs the repository with the required {@link MongoTemplate}.
     *
     * @param mongoTemplate Spring Data MongoDB template; must not be {@code null}
     */
    protected BaseMongoRepository(MongoTemplate mongoTemplate) {
        if (mongoTemplate == null) {
            throw new IllegalArgumentException("mongoTemplate must not be null");
        }
        this.mongoTemplate = mongoTemplate;
    }

    /**
     * Appends a {@code tenant_id} equality filter to an existing {@link Criteria}.
     *
     * <p>Use this method when you are building a compound {@link Criteria} from
     * scratch. Example:</p>
     * <pre>{@code
     * Criteria criteria = withTenant(Criteria.where("status").is("ACTIVE"))
     *         .and("type").is("ELECTRIC");
     * mongoTemplate.find(new Query(criteria), Vehicle.class);
     * }</pre>
     *
     * @param criteria the base criteria to augment; must not be {@code null}
     * @return the same {@link Criteria} instance with an added {@code tenant_id} condition
     * @throws PlatformException with code {@code TENANT_CONTEXT_MISSING} (HTTP 403)
     *                           if {@link TenantContext#getTenantId()} is {@code null}
     * @throws IllegalArgumentException if {@code criteria} is {@code null}
     */
    protected Criteria withTenant(Criteria criteria) {
        if (criteria == null) {
            throw new IllegalArgumentException("criteria must not be null");
        }
        String tenantId = requireTenantId();
        log.debug("Applying tenant filter: tenant_id={}", tenantId);
        return criteria.and("tenant_id").is(tenantId);
    }

    /**
     * Adds a {@code tenant_id} equality filter to an existing {@link Query}.
     *
     * <p>Use this method when you already have a {@link Query} and want to add
     * the mandatory tenant filter without rebuilding the entire criteria. Example:</p>
     * <pre>{@code
     * Query query = withTenantQuery(new Query(Criteria.where("driverId").is(driverId)));
     * mongoTemplate.find(query, Trip.class);
     * }</pre>
     *
     * @param query the base query to augment; must not be {@code null}
     * @return the same {@link Query} instance with an added {@code tenant_id} filter
     * @throws PlatformException with code {@code TENANT_CONTEXT_MISSING} (HTTP 403)
     *                           if {@link TenantContext#getTenantId()} is {@code null}
     * @throws IllegalArgumentException if {@code query} is {@code null}
     */
    protected Query withTenantQuery(Query query) {
        if (query == null) {
            throw new IllegalArgumentException("query must not be null");
        }
        String tenantId = requireTenantId();
        log.debug("Applying tenant filter to query: tenant_id={}", tenantId);
        query.addCriteria(Criteria.where("tenant_id").is(tenantId));
        return query;
    }

    /**
     * Resolves the current tenant ID from {@link TenantContext}, throwing a
     * {@link PlatformException} if the context is not set.
     *
     * @return non-null, non-blank tenant ID string
     * @throws PlatformException with code {@code TENANT_CONTEXT_MISSING} if tenant ID is absent
     */
    private String requireTenantId() {
        String tenantId = TenantContext.getTenantId();
        if (tenantId == null || tenantId.isBlank()) {
            log.error("Attempted MongoDB query without tenant context — BL-001 violation");
            throw PlatformException.tenantContextMissing();
        }
        return tenantId;
    }
}
