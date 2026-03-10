package com.vnpt.avplatform.tms.exception;

public class OtpResendLimitException extends RuntimeException {
    public OtpResendLimitException(String message) {
        super(message);
    }
}
