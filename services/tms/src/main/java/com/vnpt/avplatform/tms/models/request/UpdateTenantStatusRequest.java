package com.vnpt.avplatform.tms.models.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdateTenantStatusRequest {

    @NotBlank(message = "Action is required")
    private String action; // "suspend" or "reactivate"

    private String reason;
}
