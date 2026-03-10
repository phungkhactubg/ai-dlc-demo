package com.vnpt.avplatform.tms.services;

import com.vnpt.avplatform.tms.models.request.RegisterRiderRequest;
import com.vnpt.avplatform.tms.models.request.UpdateRiderRequest;
import com.vnpt.avplatform.tms.models.response.RiderDTO;

public interface RiderIdentityService {
    RiderDTO registerRider(String tenantId, RegisterRiderRequest request);
    RiderDTO handleOAuthCallback(String tenantId, String provider, String idToken);
    RiderDTO getRider(String riderId);
    RiderDTO updateRider(String riderId, UpdateRiderRequest request);
}
