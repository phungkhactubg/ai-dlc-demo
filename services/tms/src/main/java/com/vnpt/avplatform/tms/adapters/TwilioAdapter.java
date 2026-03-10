package com.vnpt.avplatform.tms.adapters;

public interface TwilioAdapter {
    void sendOtp(String toPhoneNumber, String otpCode, String tenantName);
}
