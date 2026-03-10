package com.vnpt.avplatform.tms.models.request;

import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class UpdateBrandingRequest {

    @Pattern(regexp = "^#[0-9A-Fa-f]{6}$", message = "Primary color must be in #RRGGBB format")
    private String primaryColor;

    @Pattern(regexp = "^#[0-9A-Fa-f]{6}$", message = "Secondary color must be in #RRGGBB format")
    private String secondaryColor;

    private String emailTemplateId;
}
