package com.vnpt.avplatform.tms.exception;

public class TenantNotFoundException extends RuntimeException {
    public TenantNotFoundException(String message) {
        super(message);
    }
}
