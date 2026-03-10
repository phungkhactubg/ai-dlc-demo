package com.vnpt.avplatform.tms.models.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "riders")
public class Rider {

    @Id
    private String id;

    @Indexed(unique = true)
    @Field("rider_id")
    private String riderId;

    @Indexed
    @Field("tenant_id")
    private String tenantId;

    @Indexed(unique = true, sparse = true)
    @Field("keycloak_sub")
    private String keycloakSub;

    @Indexed
    @Field("email")
    private String email;

    @Field("email_verified")
    private boolean emailVerified;

    @Field("phone_number")
    private String phoneNumber;

    @Field("phone_verified")
    private boolean phoneVerified;

    @Field("full_name")
    private String fullName;

    @Field("preferred_language")
    private String preferredLanguage;

    @Field("auth_provider")
    private AuthProvider authProvider;

    @Field("google_sub")
    private String googleSub;

    @Field("apple_sub")
    private String appleSub;

    @Field("profile_photo_url")
    private String profilePhotoUrl;

    @Field("wallet_id")
    private String walletId;

    @Field("default_payment_method")
    private PaymentMethod defaultPaymentMethod;

    @Builder.Default
    @Field("status")
    private RiderStatus status = RiderStatus.PENDING_VERIFICATION;

    @Field("created_at")
    private Instant createdAt;

    @Field("updated_at")
    private Instant updatedAt;
}
