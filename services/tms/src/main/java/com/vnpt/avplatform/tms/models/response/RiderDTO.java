package com.vnpt.avplatform.tms.models.response;

import com.vnpt.avplatform.tms.models.entity.AuthProvider;
import com.vnpt.avplatform.tms.models.entity.RiderStatus;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class RiderDTO {
    private String riderId;
    private String tenantId;
    private String email;
    private boolean emailVerified;
    private String phoneNumber;
    private boolean phoneVerified;
    private String fullName;
    private String preferredLanguage;
    private AuthProvider authProvider;
    private String profilePhotoUrl;
    private RiderStatus status;
    private Instant createdAt;
}
