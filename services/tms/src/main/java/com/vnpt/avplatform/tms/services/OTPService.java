package com.vnpt.avplatform.tms.services;

public interface OTPService {
    void sendOtp(String riderId, String tenantId, String phoneNumber);
    void verifyOtp(String riderId, String tenantId, String phoneNumber, String otp);
    int getRemainingAttempts(String riderId, String tenantId, String phoneNumber);
}
