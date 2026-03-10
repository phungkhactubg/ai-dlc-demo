package com.vnpt.avplatform.tms.services;

import com.vnpt.avplatform.tms.adapters.TwilioAdapter;
import com.vnpt.avplatform.tms.exception.OtpExpiredException;
import com.vnpt.avplatform.tms.exception.OtpInvalidException;
import com.vnpt.avplatform.tms.exception.OtpLockedException;
import com.vnpt.avplatform.tms.exception.OtpResendLimitException;
import com.vnpt.avplatform.tms.models.entity.Rider;
import com.vnpt.avplatform.tms.models.entity.RiderStatus;
import com.vnpt.avplatform.tms.repositories.RiderRepository;
import com.vnpt.avplatform.tms.services.impl.OTPServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class OTPServiceTest {

    @Mock
    private RiderRepository riderRepository;

    @Mock
    private TwilioAdapter twilioAdapter;

    @Mock
    private RedisTemplate<String, String> redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    private OTPServiceImpl otpService;

    private static final String RIDER_ID = "rider-001";
    private static final String TENANT_ID = "tenant-001";
    private static final String PHONE = "+84912345678";

    @BeforeEach
    void setUp() {
        otpService = new OTPServiceImpl(riderRepository, twilioAdapter, redisTemplate);
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
    }

    private Rider buildRider() {
        return Rider.builder()
                .riderId(RIDER_ID)
                .tenantId(TENANT_ID)
                .email("rider@test.com")
                .status(RiderStatus.PENDING_VERIFICATION)
                .build();
    }

    @Test
    void sendOtp_success_callsTwilio() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn(null);
        when(valueOps.get("otp_resend:" + PHONE + ":hourly")).thenReturn(null);
        when(riderRepository.findByRiderId(RIDER_ID)).thenReturn(Optional.of(buildRider()));
        doNothing().when(twilioAdapter).sendOtp(anyString(), anyString(), anyString());

        otpService.sendOtp(RIDER_ID, TENANT_ID, PHONE);

        verify(valueOps).set(contains("otp:" + RIDER_ID), anyString(), any());
        verify(twilioAdapter).sendOtp(anyString(), anyString(), anyString());
    }

    @Test
    void sendOtp_locked_throwsOtpLockedException() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn("LOCKED");

        assertThatThrownBy(() -> otpService.sendOtp(RIDER_ID, TENANT_ID, PHONE))
                .isInstanceOf(OtpLockedException.class);

        verify(twilioAdapter, never()).sendOtp(anyString(), anyString(), anyString());
    }

    @Test
    void sendOtp_resendLimitReached_throwsOtpResendLimitException() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn(null);
        when(valueOps.get("otp_resend:" + PHONE + ":hourly")).thenReturn("3");

        assertThatThrownBy(() -> otpService.sendOtp(RIDER_ID, TENANT_ID, PHONE))
                .isInstanceOf(OtpResendLimitException.class);
    }

    @Test
    void verifyOtp_validOtp_succeeds() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn(null);
        when(valueOps.get("otp:" + RIDER_ID + ":" + PHONE)).thenReturn("123456");
        when(riderRepository.findByRiderId(RIDER_ID)).thenReturn(Optional.of(buildRider()));
        when(riderRepository.save(any(Rider.class))).thenAnswer(inv -> inv.getArgument(0));

        otpService.verifyOtp(RIDER_ID, TENANT_ID, PHONE, "123456");

        verify(riderRepository).save(any(Rider.class));
    }

    @Test
    void verifyOtp_expiredOtp_throwsOtpExpiredException() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn(null);
        when(valueOps.get("otp:" + RIDER_ID + ":" + PHONE)).thenReturn(null);

        assertThatThrownBy(() -> otpService.verifyOtp(RIDER_ID, TENANT_ID, PHONE, "123456"))
                .isInstanceOf(OtpExpiredException.class);
    }

    @Test
    void verifyOtp_wrongOtp_throwsOtpInvalidException() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn(null);
        when(valueOps.get("otp:" + RIDER_ID + ":" + PHONE)).thenReturn("654321");
        when(valueOps.increment("otp_attempts:" + RIDER_ID + ":" + PHONE)).thenReturn(1L);

        assertThatThrownBy(() -> otpService.verifyOtp(RIDER_ID, TENANT_ID, PHONE, "123456"))
                .isInstanceOf(OtpInvalidException.class);
    }

    @Test
    void verifyOtp_maxAttemptsReached_throwsOtpLockedException() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn(null);
        when(valueOps.get("otp:" + RIDER_ID + ":" + PHONE)).thenReturn("654321");
        when(valueOps.increment("otp_attempts:" + RIDER_ID + ":" + PHONE)).thenReturn(5L);

        assertThatThrownBy(() -> otpService.verifyOtp(RIDER_ID, TENANT_ID, PHONE, "123456"))
                .isInstanceOf(OtpLockedException.class);
    }

    @Test
    void verifyOtp_lockedAccount_throwsOtpLockedException() {
        when(valueOps.get("otp_locked:" + RIDER_ID + ":" + PHONE)).thenReturn("LOCKED");

        assertThatThrownBy(() -> otpService.verifyOtp(RIDER_ID, TENANT_ID, PHONE, "123456"))
                .isInstanceOf(OtpLockedException.class);
    }
}
