package com.vnpt.avplatform.tms.services.impl;

import com.vnpt.avplatform.tms.adapters.MinIOAdapter;
import com.vnpt.avplatform.tms.exception.FileSizeExceededException;
import com.vnpt.avplatform.tms.exception.InvalidFileTypeException;
import com.vnpt.avplatform.tms.exception.TenantNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Tenant;
import com.vnpt.avplatform.tms.models.entity.TenantBranding;
import com.vnpt.avplatform.tms.models.request.UpdateBrandingRequest;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.BrandingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import javax.naming.NamingException;
import javax.naming.directory.Attributes;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;
import java.io.IOException;
import java.util.Hashtable;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;

@Slf4j
@Service
public class BrandingServiceImpl implements BrandingService {

    private static final long MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024L;
    private static final Set<String> ALLOWED_CONTENT_TYPES = Set.of("image/png", "image/jpeg", "image/webp");
    private static final Pattern HEX_COLOR_PATTERN = Pattern.compile("^#[0-9A-Fa-f]{6}$");
    private static final String CACHE_KEY_PREFIX = "tenant_config:";

    private final TenantRepository tenantRepository;
    private final MinIOAdapter minIOAdapter;
    private final RedisTemplate<String, String> redisTemplate;

    public BrandingServiceImpl(
            TenantRepository tenantRepository,
            MinIOAdapter minIOAdapter,
            RedisTemplate<String, String> redisTemplate) {
        this.tenantRepository = Objects.requireNonNull(tenantRepository, "tenantRepository must not be null");
        this.minIOAdapter = Objects.requireNonNull(minIOAdapter, "minIOAdapter must not be null");
        this.redisTemplate = Objects.requireNonNull(redisTemplate, "redisTemplate must not be null");
    }

    @Override
    @Transactional
    public TenantBranding updateBranding(String tenantId, UpdateBrandingRequest request) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        TenantBranding existing = tenant.getBranding() != null
                ? tenant.getBranding()
                : TenantBranding.builder().build();

        if (request.getPrimaryColor() != null) {
            if (!HEX_COLOR_PATTERN.matcher(request.getPrimaryColor()).matches()) {
                throw new IllegalArgumentException("Invalid primary color format. Use #RRGGBB");
            }
            existing.setPrimaryColor(request.getPrimaryColor());
        }
        if (request.getSecondaryColor() != null) {
            if (!HEX_COLOR_PATTERN.matcher(request.getSecondaryColor()).matches()) {
                throw new IllegalArgumentException("Invalid secondary color format. Use #RRGGBB");
            }
            existing.setSecondaryColor(request.getSecondaryColor());
        }
        if (request.getEmailTemplateId() != null) {
            existing.setEmailTemplateId(request.getEmailTemplateId());
        }

        tenantRepository.updateBranding(tenantId, existing);
        evictCache(tenantId);
        log.info("Branding updated: tenantId={}", tenantId);
        return existing;
    }

    @Override
    public String uploadLogo(String tenantId, MultipartFile logo) {
        validateLogoFile(logo);

        tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        try {
            byte[] data = logo.getBytes();
            String contentType = logo.getContentType();
            String cdnUrl = minIOAdapter.uploadLogo(tenantId, data, contentType);

            Tenant tenant = tenantRepository.findByTenantId(tenantId)
                    .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));
            TenantBranding branding = tenant.getBranding() != null
                    ? tenant.getBranding()
                    : TenantBranding.builder().build();
            branding.setLogoUrl(cdnUrl);
            tenantRepository.updateBranding(tenantId, branding);
            evictCache(tenantId);

            log.info("Logo uploaded: tenantId={}, cdnUrl={}", tenantId, cdnUrl);
            return cdnUrl;
        } catch (IOException e) {
            log.error("Failed to read logo file for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new RuntimeException("Failed to read logo file: " + e.getMessage(), e);
        }
    }

    @Override
    public TenantBranding initiateDomainVerification(String tenantId, String customDomain) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        String txtRecord = "vnpt-av-verify=" + UUID.randomUUID().toString().replace("-", "");
        TenantBranding branding = tenant.getBranding() != null
                ? tenant.getBranding()
                : TenantBranding.builder().build();
        branding.setCustomDomain(customDomain);
        branding.setCustomDomainVerified(false);
        branding.setCustomDomainTxtRecord(txtRecord);

        tenantRepository.updateBranding(tenantId, branding);
        evictCache(tenantId);
        log.info("Domain verification initiated: tenantId={}, domain={}, txtRecord={}", tenantId, customDomain, txtRecord);
        return branding;
    }

    @Override
    public boolean verifyDomain(String tenantId) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        TenantBranding branding = tenant.getBranding();
        if (branding == null || branding.getCustomDomain() == null || branding.getCustomDomainTxtRecord() == null) {
            log.warn("Domain verification attempted but no domain/record set: tenantId={}", tenantId);
            return false;
        }

        String domain = branding.getCustomDomain();
        String expectedRecord = branding.getCustomDomainTxtRecord();

        try {
            Hashtable<String, String> env = new Hashtable<>();
            env.put("java.naming.factory.initial", "com.sun.jndi.dns.DnsContextFactory");
            env.put("java.naming.provider.url", "dns:");
            DirContext ctx = new InitialDirContext(env);

            Attributes attrs = ctx.getAttributes(domain, new String[]{"TXT"});
            javax.naming.directory.Attribute txtAttr = attrs.get("TXT");

            if (txtAttr != null) {
                for (int i = 0; i < txtAttr.size(); i++) {
                    String txtValue = txtAttr.get(i).toString().replace("\"", "");
                    if (expectedRecord.equals(txtValue)) {
                        branding.setCustomDomainVerified(true);
                        tenantRepository.updateBranding(tenantId, branding);
                        evictCache(tenantId);
                        log.info("Domain verified: tenantId={}, domain={}", tenantId, domain);
                        return true;
                    }
                }
            }
            log.info("Domain verification failed - TXT record not found: tenantId={}, domain={}", tenantId, domain);
            return false;
        } catch (NamingException e) {
            log.warn("DNS lookup failed for domain={}: {}", domain, e.getMessage());
            return false;
        }
    }

    private void validateLogoFile(MultipartFile logo) {
        if (logo.isEmpty()) {
            throw new InvalidFileTypeException("Logo file must not be empty");
        }
        String contentType = logo.getContentType();
        if (contentType == null || !ALLOWED_CONTENT_TYPES.contains(contentType)) {
            throw new InvalidFileTypeException("Invalid file type. Allowed types: PNG, JPEG, WebP");
        }
        if (logo.getSize() > MAX_LOGO_SIZE_BYTES) {
            throw new FileSizeExceededException("Logo file size exceeds the maximum allowed 5MB");
        }
    }

    private void evictCache(String tenantId) {
        try {
            redisTemplate.delete(CACHE_KEY_PREFIX + tenantId);
        } catch (Exception e) {
            log.warn("Failed to evict cache for tenantId={}: {}", tenantId, e.getMessage());
        }
    }
}
