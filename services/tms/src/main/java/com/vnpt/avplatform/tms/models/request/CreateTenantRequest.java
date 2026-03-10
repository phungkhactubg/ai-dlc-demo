package com.vnpt.avplatform.tms.models.request;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class CreateTenantRequest {

    @NotBlank(message = "Company name is required")
    @Size(min = 2, max = 200, message = "Company name must be between 2 and 200 characters")
    private String companyName;

    @NotBlank(message = "Company domain is required")
    @Pattern(regexp = "^[a-z0-9]([a-z0-9\\-]{0,61}[a-z0-9])?(\\.[a-z]{2,})+$", message = "Invalid domain format")
    private String companyDomain;

    @NotBlank(message = "Country code is required")
    @Pattern(regexp = "^[A-Z]{2}$", message = "Country code must be 2 uppercase letters (ISO-2)")
    private String countryCode;

    @NotBlank(message = "Timezone is required")
    private String timezone;

    @NotBlank(message = "Plan ID is required")
    private String planId;

    @NotBlank(message = "Admin email is required")
    @Email(message = "Admin email must be a valid email address")
    private String adminEmail;

    @NotBlank(message = "Admin name is required")
    @Size(min = 2, max = 100, message = "Admin name must be between 2 and 100 characters")
    private String adminName;

    @Min(value = 0, message = "Vehicle quota must be non-negative")
    private Integer vehicleQuota;

    @DecimalMin(value = "1.0", message = "Surge cap override must be at least 1.0")
    @DecimalMax(value = "3.0", message = "Surge cap override must be at most 3.0")
    private BigDecimal surgeCapOverride;
}
