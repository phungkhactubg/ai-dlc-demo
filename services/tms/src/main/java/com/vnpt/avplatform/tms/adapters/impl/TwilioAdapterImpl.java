package com.vnpt.avplatform.tms.adapters.impl;

import com.vnpt.avplatform.tms.adapters.TwilioAdapter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Objects;

@Slf4j
@Component
public class TwilioAdapterImpl implements TwilioAdapter {

    private final RestTemplate restTemplate;
    private final String accountSid;
    private final String authToken;
    private final String fromNumber;

    public TwilioAdapterImpl(
            RestTemplate restTemplate,
            @Value("${twilio.account-sid}") String accountSid,
            @Value("${twilio.auth-token}") String authToken,
            @Value("${twilio.from-number}") String fromNumber) {
        this.restTemplate = Objects.requireNonNull(restTemplate, "restTemplate must not be null");
        this.accountSid = Objects.requireNonNull(accountSid, "accountSid must not be null");
        this.authToken = Objects.requireNonNull(authToken, "authToken must not be null");
        this.fromNumber = Objects.requireNonNull(fromNumber, "fromNumber must not be null");
    }

    @Override
    public void sendOtp(String toPhoneNumber, String otpCode, String tenantName) {
        String url = "https://api.twilio.com/2010-04-01/Accounts/" + accountSid + "/Messages.json";
        String messageBody = String.format("[%s] Your verification code is: %s. Valid for 5 minutes.", tenantName, otpCode);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        headers.setBasicAuth(accountSid, authToken);

        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("From", fromNumber);
        formData.add("To", toPhoneNumber);
        formData.add("Body", messageBody);

        try {
            restTemplate.exchange(url, HttpMethod.POST, new HttpEntity<>(formData, headers), String.class);
            log.info("OTP sent successfully to: {}", maskPhone(toPhoneNumber));
        } catch (Exception e) {
            log.error("Failed to send OTP to {}: {}", maskPhone(toPhoneNumber), e.getMessage(), e);
            throw new RuntimeException("Failed to send OTP: " + e.getMessage(), e);
        }
    }

    private String maskPhone(String phone) {
        if (phone == null || phone.length() < 4) {
            return "***";
        }
        return "***" + phone.substring(phone.length() - 4);
    }
}
