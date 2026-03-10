package com.vnpt.avplatform.tms.services.impl;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.tms.exception.TenantNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Tenant;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.FeatureFlagService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

@Slf4j
@Service
public class FeatureFlagServiceImpl implements FeatureFlagService {

    private static final String CACHE_KEY_PREFIX = "tenant_config:";
    private static final long CACHE_TTL_SECONDS = 300L;

    private final TenantRepository tenantRepository;
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper;

    public FeatureFlagServiceImpl(
            TenantRepository tenantRepository,
            RedisTemplate<String, String> redisTemplate,
            ObjectMapper objectMapper) {
        this.tenantRepository = Objects.requireNonNull(tenantRepository, "tenantRepository must not be null");
        this.redisTemplate = Objects.requireNonNull(redisTemplate, "redisTemplate must not be null");
        this.objectMapper = Objects.requireNonNull(objectMapper, "objectMapper must not be null");
    }

    @Override
    public boolean isEnabled(String tenantId, String flagKey) {
        Map<String, Boolean> flags = getAllFlags(tenantId);
        return Boolean.TRUE.equals(flags.getOrDefault(flagKey, false));
    }

    @Override
    public Map<String, Boolean> getAllFlags(String tenantId) {
        String cacheKey = CACHE_KEY_PREFIX + tenantId;
        try {
            String cached = redisTemplate.opsForValue().get(cacheKey);
            if (cached != null) {
                log.debug("Cache hit for tenant flags: tenantId={}", tenantId);
                return objectMapper.readValue(cached, new TypeReference<Map<String, Boolean>>() {});
            }
        } catch (Exception e) {
            log.warn("Failed to read feature flags from cache for tenantId={}: {}", tenantId, e.getMessage());
        }

        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        Map<String, Boolean> flags = tenant.getFeatureFlags() != null
                ? new HashMap<>(tenant.getFeatureFlags())
                : new HashMap<>();

        try {
            String serialized = objectMapper.writeValueAsString(flags);
            redisTemplate.opsForValue().set(cacheKey, serialized, Duration.ofSeconds(CACHE_TTL_SECONDS));
            log.debug("Cached tenant flags: tenantId={}", tenantId);
        } catch (Exception e) {
            log.warn("Failed to cache feature flags for tenantId={}: {}", tenantId, e.getMessage());
        }

        return flags;
    }

    @Override
    public Map<String, Boolean> updateFlags(String tenantId, Map<String, Boolean> flags) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        Map<String, Boolean> mergedFlags = tenant.getFeatureFlags() != null
                ? new HashMap<>(tenant.getFeatureFlags())
                : new HashMap<>();
        mergedFlags.putAll(flags);

        tenantRepository.updateFeatureFlags(tenantId, mergedFlags);
        log.info("Feature flags updated: tenantId={}, flags={}", tenantId, flags.keySet());

        String cacheKey = CACHE_KEY_PREFIX + tenantId;
        try {
            redisTemplate.delete(cacheKey);
        } catch (Exception e) {
            log.warn("Failed to evict feature flags cache for tenantId={}: {}", tenantId, e.getMessage());
        }

        return mergedFlags;
    }
}
