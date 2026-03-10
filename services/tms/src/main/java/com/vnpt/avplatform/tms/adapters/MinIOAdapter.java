package com.vnpt.avplatform.tms.adapters;

public interface MinIOAdapter {
    String uploadLogo(String tenantId, byte[] data, String contentType);
    void deleteLogo(String tenantId);
}
