package com.vnpt.avplatform.tms.models.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TenantBranding {

    @Field("logo_url")
    private String logoUrl;

    @Builder.Default
    @Field("primary_color")
    private String primaryColor = "#1976D2";

    @Builder.Default
    @Field("secondary_color")
    private String secondaryColor = "#424242";

    @Field("email_template_id")
    private String emailTemplateId;

    @Field("custom_domain")
    private String customDomain;

    @Builder.Default
    @Field("custom_domain_verified")
    private boolean customDomainVerified = false;

    @Field("custom_domain_txt_record")
    private String customDomainTxtRecord;
}
