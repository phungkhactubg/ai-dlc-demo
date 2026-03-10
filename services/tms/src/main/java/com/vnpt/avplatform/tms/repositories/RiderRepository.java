package com.vnpt.avplatform.tms.repositories;

import com.vnpt.avplatform.tms.models.entity.Rider;
import com.vnpt.avplatform.tms.models.entity.RiderStatus;

import java.util.Optional;

public interface RiderRepository {
    Rider save(Rider rider);
    Optional<Rider> findByRiderId(String riderId);
    Optional<Rider> findByEmailAndTenantId(String email, String tenantId);
    Optional<Rider> findByPhoneNumberAndTenantId(String phone, String tenantId);
    Optional<Rider> findByKeycloakSub(String sub);
    Rider updateStatus(String riderId, RiderStatus status);
    boolean existsByEmailAndTenantId(String email, String tenantId);
}
