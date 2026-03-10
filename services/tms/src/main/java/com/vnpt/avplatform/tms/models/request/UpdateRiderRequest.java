package com.vnpt.avplatform.tms.models.request;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class UpdateRiderRequest {

    @Size(min = 2, max = 100, message = "Full name must be between 2 and 100 characters")
    private String fullName;

    private String preferredLanguage;

    private String profilePhotoUrl;
}
