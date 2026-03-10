package com.vnpt.avplatform.tms.services.impl;

import com.vnpt.avplatform.tms.adapters.TwilioAdapter;
import com.vnpt.avplatform.tms.exception.OtpExpiredException;
import com.vnpt.avplatform.tms.exception.OtpInvalidException;
import com.vnpt.avplatform.tms.exception.OtpLockedException;
import com.vnpt.avplatform.tms.exception.OtpResendLimitException;
import com.vnpt.avplatform.tms.exception.RiderNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Rider;
import com.vnpt.avplatform.tms.models.entity.RiderStatus;
import com.vnpt.avplatform.tms.repositories.RiderRepository;
import com.vnpt.avplatform.tms.services.OTPService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;

@Slf4j
@Service
public class OTPServiceImpl implements OTPService {

    private static final int MAX_RESEND_PER_HOUR = 3;
    private static final int MAX_VERIFY_ATTEMPTS = 5;
    private static final long OTP_TTL_SECONDS = 300L;
    private static final long ATTEMPTS_TTL_SECONDS = 1800L;
    private static final long RESEND_TTL_SECONDS = 3600L;
    private static final long LOCKED_TTL_SECONDS = 1800L;

    private final RiderRepository riderRepository;
    private final TwilioAdapter twilioAdapter;
    private final RedisTemplate<String, String> redisTemplate;
    private final SecureRandom secureRandom;

    public OTPServiceImpl(
            RiderRepository riderRepository,
            TwilioAdapter twilioAdapter,
            RedisTemplate<String, String> redisTemplate) {
        this.riderRepository = Objects.requireNonNull(riderRepository, "riderRepository must not be null");
        this.twilioAdapter = Objects.requireNonNull(twilioAdapter, "twilioAdapter must not be null");
        this.redisTemplate = Objects.requireNonNull(redisTemplate, "redisTemplate must not be null");
        this.secureRandom = new SecureRandom();
    }

    @Override
    public void sendOtp(String riderId, String tenantId, String phoneNumber) {
        String resendKey = "otp_resend:" + phoneNumber + ":hourly";
        String lockedKey = "otp_locked:" + riderId + ":" + phoneNumber;

        String lockedValue = redisTemplate.opsForValue().get(lockedKey);
        if (lockedValue != null) {
            throw new OtpLockedException("Phone verification is locked due to too many failed attempts. Try again later.");
        }

        String resendCountStr = redisTemplate.opsForValue().get(resendKey);
        int resendCount = resendCountStr != null ? Integer.parseInt(resendCountStr) : 0;
        if (resendCount >= MAX_RESEND_PER_HOUR) {
            throw new OtpResendLimitException("Maximum OTP resend limit reached. Try again in 1 hour.");
        }

        String otpCode = String.format("%06d", secureRandom.nextInt(1_000_000));
        String otpKey = "otp:" + riderId + ":" + phoneNumber;

        redisTemplate.opsForValue().set(otpKey, otpCode, Duration.ofSeconds(OTP_TTL_SECONDS));

        if (resendCountStr == null) {
            redisTemplate.opsForValue().set(resendKey, "1", Duration.ofSeconds(RESEND_TTL_SECONDS));
        } else {
            redisTemplate.opsForValue().increment(resendKey);
        }

        Rider rider = riderRepository.findByRiderId(riderId)
                .orElseThrow(() -> new RiderNotFoundException("Rider not found: " + riderId));

        twilioAdapter.sendOtp(phoneNumber, otpCode, rider.getTenantId());
        log.info("OTP sent: riderId={}, phone={}", riderId, maskPhone(phoneNumber));
    }

    @Override
    public void verifyOtp(String riderId, String tenantId, String phoneNumber, String otp) {
        String lockedKey = "otp_locked:" + riderId + ":" + phoneNumber;
        String otpKey = "otp:" + riderId + ":" + phoneNumber;
        String attemptsKey = "otp_attempts:" + riderId + ":" + phoneNumber;

        String lockedValue = redisTemplate.opsForValue().get(lockedKey);
        if (lockedValue != null) {
            throw new OtpLockedException("Phone verification is locked due to too many failed attempts. Try again later.");
        }

        String storedOtp = redisTemplate.opsForValue().get(otpKey);
        if (storedOtp == null) {
            throw new OtpExpiredException("OTP has expired. Please request a new one.");
        }

        if (!storedOtp.equals(otp)) {
            Long attempts = redisTemplate.opsForValue().increment(attemptsKey);
            if (attempts == 1) {
                redisTemplate.expire(attemptsKey, Duration.ofSeconds(ATTEMPTS_TTL_SECONDS));
            }
            if (attempts != null && attempts >= MAX_VERIFY_ATTEMPTS) {
                redisTemplate.opsForValue().set(lockedKey, "LOCKED", Duration.ofSeconds(LOCKED_TTL_SECONDS));
                redisTemplate.delete(otpKey);
                redisTemplate.delete(attemptsKey);
                throw new OtpLockedException("Too many failed attempts. Phone verification locked for 30 minutes.");
            }
            int remaining = MAX_VERIFY_ATTEMPTS - (attempts != null ? attempts.intValue() : 1);
            throw new OtpInvalidException("Invalid OTP. " + remaining + " attempts remaining.");
        }

        redisTemplate.delete(otpKey);
        redisTemplate.delete(attemptsKey);

        Rider rider = riderRepository.findByRiderId(riderId)
                .orElseThrow(() -> new RiderNotFoundException("Rider not found: " + riderId));

        rider.setPhoneNumber(phoneNumber);
        rider.setPhoneVerified(true);
        rider.setStatus(RiderStatus.ACTIVE);
        rider.setUpdatedAt(Instant.now());
        riderRepository.save(rider);

        log.info("OTP verified successfully: riderId={}, phone={}", riderId, maskPhone(phoneNumber));
    }

    @Override
    public int getRemainingAttempts(String riderId, String tenantId, String phoneNumber) {
        String attemptsKey = "otp_attempts:" + riderId + ":" + phoneNumber;
        String attemptsStr = redisTemplate.opsForValue().get(attemptsKey);
        int used = attemptsStr != null ? Integer.parseInt(attemptsStr) : 0;
        return Math.max(0, MAX_VERIFY_ATTEMPTS - used);
    }

    private String maskPhone(String phone) {
        if (phone == null || phone.length() < 4) {
            return "***";
        }
        return "***" + phone.substring(phone.length() - 4);
    }
}
