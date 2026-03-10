package com.vnpt.avplatform.tms.exception;

public class TenantContextMissingException extends RuntimeException {
    public TenantContextMissingException(String message) {
        super(message);
    }
}
