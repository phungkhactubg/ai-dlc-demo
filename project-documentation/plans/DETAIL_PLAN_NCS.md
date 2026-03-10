# DETAIL PLAN — NCS: Notification & Communication Service

**Work Package**: WP-007 | **SRS**: SRS_NCS_Notification_Communication.md  
**Technology**: Java 17+ / Spring Boot 3.x  
**Base Package**: `com.vnpt.avplatform.ncs`  
**Database**: MongoDB (`ncs_db`) + Redis (dedup)  
**Events**: Kafka consumer (all topics) + producer (notification-events)  
**Critical SLA**: < 5 seconds for CRITICAL alerts (safety_stop, emergency) — BL-007  
**Channels**: FCM (push), APNs (iOS), SendGrid (email), Twilio (SMS), Webhook (tenant)  
**Version**: 1.0.0 | **Author**: PM/BA Orchestrator  

---

## Task Index

| Task ID | Title | Group | Est. Time |
|---------|-------|-------|-----------|
| TASK-NCS-001 | NotificationLog domain model | Domain Models | 1h |
| TASK-NCS-002 | NotificationTemplate domain model | Domain Models | 1h |
| TASK-NCS-003 | WebhookEndpoint domain model | Domain Models | 1h |
| TASK-NCS-004 | NotificationLogRepository | Repository | 1h |
| TASK-NCS-005 | TemplateRepository | Repository | 1h |
| TASK-NCS-006 | WebhookEndpointRepository | Repository | 1h |
| TASK-NCS-007 | TenantContextFilter + TenantContextHolder | Security | 1.5h |
| TASK-NCS-008 | FCMChannelAdapter | Adapters | 2h |
| TASK-NCS-009 | APNsChannelAdapter | Adapters | 2h |
| TASK-NCS-010 | SendGridEmailAdapter | Adapters | 1.5h |
| TASK-NCS-011 | TwilioSMSAdapter | Adapters | 1.5h |
| TASK-NCS-012 | WebhookChannelAdapter (HMAC + SSRF prevention) | Adapters | 2h |
| TASK-NCS-013 | CriticalAlertService (fast path < 5s SLA) | Services | 2h |
| TASK-NCS-014 | HandlebarsTemplateService | Services | 1.5h |
| TASK-NCS-015 | DeduplicationService (Redis SHA256) | Services | 1.5h |
| TASK-NCS-016 | QuietHoursService | Services | 1h |
| TASK-NCS-017 | NotificationDispatchService (standard path) | Services | 2h |
| TASK-NCS-018 | DLQRetryScheduler | Services | 1.5h |
| TASK-NCS-019 | KafkaEventConsumer (all topics) | Kafka | 2h |
| TASK-NCS-020 | NotificationKafkaProducer | Kafka | 1h |
| TASK-NCS-021 | NotificationController | Controllers | 1.5h |
| TASK-NCS-022 | WebhookEndpointController | Controllers | 1.5h |
| TASK-NCS-023 | GlobalExceptionHandler | Controllers | 1h |
| TASK-NCS-024 | MongoConfig + RedisConfig | Config | 1h |
| TASK-NCS-025 | Unit tests: CriticalAlertService (< 5s SLA) | Tests | 2h |
| TASK-NCS-026 | Unit tests: DeduplicationService | Tests | 1.5h |
| TASK-NCS-027 | Unit tests: HandlebarsTemplateService | Tests | 1h |
| TASK-NCS-028 | Unit tests: WebhookChannelAdapter (HMAC) | Tests | 1.5h |
| TASK-NCS-029 | Integration tests: Notification API | Tests | 2h |

---

## Task Group 1: Domain Models

### TASK-NCS-001: NotificationLog Domain Model

**Parent WP Task**: WP-007-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/models/NotificationLog.java`
- `src/main/java/com/vnpt/avplatform/ncs/models/NotificationChannel.java`
- `src/main/java/com/vnpt/avplatform/ncs/models/NotificationStatus.java`
- `src/main/java/com/vnpt/avplatform/ncs/models/NotificationPriority.java`

**Specification**:
```java
// NotificationChannel.java
public enum NotificationChannel { FCM, APNS, EMAIL, SMS, WEBHOOK }

// NotificationStatus.java
public enum NotificationStatus { PENDING, SENT, DELIVERED, FAILED, DEDUPED }

// NotificationPriority.java
public enum NotificationPriority {
    CRITICAL,  // safety_stop, emergency — bypass queue, < 5s SLA
    HIGH,      // booking confirmed, payment processed
    NORMAL,    // promotional, weekly summary
    LOW        // system maintenance notices
}

// NotificationLog.java
@Document(collection = "notification_logs")
public class NotificationLog {
    @Id private String id;

    @Field("notification_id")
    @Indexed(unique = true)
    private String notificationId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("event_id")
    @Indexed
    private String eventId; // source Kafka event ID (for dedup tracking)

    @Field("recipient_id")
    private String recipientId; // riderId or userId

    @Field("channel")
    private NotificationChannel channel;

    @Field("priority")
    private NotificationPriority priority;

    @Field("template_id")
    private String templateId;

    @Field("rendered_subject")
    private String renderedSubject;

    @Field("rendered_body")
    private String renderedBody; // rendered Handlebars output

    @Field("status")
    private NotificationStatus status;

    @Field("retry_count")
    private int retryCount = 0; // max 3

    @Field("dedup_key")
    private String dedupKey; // SHA256(eventId:recipientId:channel)

    @Field("gateway_message_id")
    private String gatewayMessageId; // FCM/APNs/SendGrid/Twilio message ID

    @Field("error_message")
    private String errorMessage;

    @Field("sent_at")
    private Instant sentAt;

    @Field("created_at")
    @Indexed
    private Instant createdAt = Instant.now();
}
```

**Definition of Done**:
- [ ] `dedupKey` stored for audit trail (SHA256 hash)
- [ ] `retryCount` max 3 (enforced by DLQRetryScheduler)
- [ ] `priority = CRITICAL` records bypass dedup service (always send)
- [ ] TTL index on `created_at`: auto-delete after 90 days

---

### TASK-NCS-002: NotificationTemplate Domain Model

**Parent WP Task**: WP-007-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/models/NotificationTemplate.java`

**Specification**:
```java
@Document(collection = "notification_templates")
public class NotificationTemplate {
    @Id private String id;

    @Field("template_id")
    @Indexed
    private String templateId; // e.g., "ride.completed", "payment.failed"

    @Field("tenant_id")
    @Indexed
    private String tenantId; // null = platform default template

    @Field("channel")
    private NotificationChannel channel;

    @Field("locale")
    private String locale = "vi"; // default Vietnamese; also "en"

    @Field("subject_template")
    private String subjectTemplate; // Handlebars template for email subject

    @Field("body_template")
    private String bodyTemplate; // Handlebars template for body

    @Field("is_active")
    private boolean isActive = true;

    @Field("version")
    private int version = 1;

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Pre-loaded templates** (at startup — loaded into `ConcurrentHashMap` for critical path):
- `ride.safety_stop` — FCM + SMS
- `emergency` — FCM + SMS
- `ride.completed` — FCM + EMAIL
- `payment.failed` — FCM + SMS + EMAIL
- `billing.subscription_suspended` — EMAIL
- `billing.quota_warning` — EMAIL
- `ride.cancelled` — FCM + SMS
- `booking.confirmed` — FCM + SMS

**Definition of Done**:
- [ ] `tenantId = null` means platform default (fallback if tenant has no custom template)
- [ ] Lookup order: tenant-specific → platform default
- [ ] CRITICAL templates (`ride.safety_stop`, `emergency`) pre-loaded in `ConcurrentHashMap` at startup

---

### TASK-NCS-003: WebhookEndpoint Domain Model

**Parent WP Task**: WP-007-T01  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/models/WebhookEndpoint.java`

**Specification**:
```java
@Document(collection = "webhook_endpoints")
public class WebhookEndpoint {
    @Id private String id;

    @Field("endpoint_id")
    @Indexed(unique = true)
    private String endpointId = UUID.randomUUID().toString();

    @Field("tenant_id")
    @Indexed
    private String tenantId; // BL-001

    @Field("url")
    @NotBlank
    private String url; // SSRF-checked on save

    @Field("events_subscribed")
    private List<String> eventsSubscribed; // e.g., ["ride.completed", "payment.captured"]

    @Field("hmac_secret")
    private String hmacSecret; // AES-256-GCM encrypted at rest (key from KMS)

    @Field("is_active")
    private boolean isActive = true;

    @Field("failure_count")
    private int failureCount = 0; // auto-disable after 50 consecutive failures

    @Field("last_success_at")
    private Instant lastSuccessAt;

    @Field("created_at")
    private Instant createdAt = Instant.now();
}
```

**Definition of Done**:
- [ ] `hmacSecret` encrypted at rest (AES-256-GCM, decrypted only in WebhookChannelAdapter)
- [ ] `failureCount >= 50` → `isActive = false` (auto-disabled by WebhookChannelAdapter)
- [ ] `url` SSRF-validated on registration (rejects private IP ranges)

---

## Task Group 2: Repository Layer

### TASK-NCS-004: NotificationLogRepository

**Parent WP Task**: WP-007-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/repositories/NotificationLogRepository.java`
- `src/main/java/com/vnpt/avplatform/ncs/repositories/impl/NotificationLogRepositoryImpl.java`

**Specification**:
```java
public interface NotificationLogRepository {
    NotificationLog insert(NotificationLog log); // INSERT-ONLY
    Optional<NotificationLog> findByNotificationId(String notificationId);
    List<NotificationLog> findFailedByTenantId(String tenantId, int page, int size);
    NotificationLog updateStatus(String notificationId, NotificationStatus status,
        String gatewayMessageId, String errorMessage, int retryCount);
}
// findFailedByTenantId: status=FAILED AND retryCount < 3 (ready for DLQ retry)
// TTL index: created_at expires after 90 days (configured in MongoConfig)
```

**Definition of Done**:
- [ ] `insert()` not `save()` (audit immutability)
- [ ] `findFailedByTenantId` filters `retryCount < 3`
- [ ] 90-day TTL index on `created_at`

---

### TASK-NCS-005: TemplateRepository

**Parent WP Task**: WP-007-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/repositories/TemplateRepository.java`
- `src/main/java/com/vnpt/avplatform/ncs/repositories/impl/TemplateRepositoryImpl.java`

**Specification**:
```java
public interface TemplateRepository {
    List<NotificationTemplate> findAllActive(); // loaded at startup
    Optional<NotificationTemplate> findByTemplateIdAndChannel(
        String templateId, NotificationChannel channel, String tenantId, String locale);
}
// findByTemplateIdAndChannel: try tenantId first, then null tenantId (platform default)
// For locale: try specific locale, then fallback to "vi" (Vietnamese default)
```

**Definition of Done**:
- [ ] Lookup order: tenant-specific → platform default → fallback locale
- [ ] `findAllActive()` used at startup to populate `ConcurrentHashMap`

---

### TASK-NCS-006: WebhookEndpointRepository

**Parent WP Task**: WP-007-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/repositories/WebhookEndpointRepository.java`
- `src/main/java/com/vnpt/avplatform/ncs/repositories/impl/WebhookEndpointRepositoryImpl.java`

**Specification**:
```java
public interface WebhookEndpointRepository {
    WebhookEndpoint save(WebhookEndpoint endpoint);
    Optional<WebhookEndpoint> findByEndpointId(String endpointId);
    List<WebhookEndpoint> findActiveByTenantId(String tenantId);
    List<WebhookEndpoint> findByEventSubscription(String tenantId, String eventType);
    boolean incrementFailureCount(String endpointId); // returns true if auto-disabled (>= 50)
    boolean resetFailureCount(String endpointId);     // on success
}
// findByEventSubscription: events_subscribed contains eventType AND is_active=true AND tenant_id=tenantId
// incrementFailureCount: $inc failure_count; if result >= 50: $set is_active=false
```

**Definition of Done**:
- [ ] `findByEventSubscription` uses MongoDB `$elemMatch` on `events_subscribed` array
- [ ] `incrementFailureCount` auto-disables endpoint at 50 consecutive failures
- [ ] `resetFailureCount` resets to 0 on successful delivery

---

## Task Group 3: Security

### TASK-NCS-007: TenantContextFilter + TenantContextHolder

**Parent WP Task**: WP-007-T01 (cross-cutting)  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/security/TenantContextFilter.java`
- `src/main/java/com/vnpt/avplatform/ncs/security/TenantContextHolder.java`

**Specification**: Same pattern as TMS (TASK-TMS-008/009).
```java
// OncePerRequestFilter, @Order(1)
// Extract from JWT "tenant_id" OR "X-Tenant-ID" header
// finally: TenantContextHolder.clear()
```

**Definition of Done**:
- [ ] `clear()` in `finally` block
- [ ] `@Order(1)` priority

---

## Task Group 4: Channel Adapters

### TASK-NCS-008: FCMChannelAdapter

**Parent WP Task**: WP-007-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/adapters/FCMChannelAdapter.java`

**Specification**:
```java
@Component
public class FCMChannelAdapter {
    // Library: com.google.firebase:firebase-admin:9.x
    // Config: GOOGLE_APPLICATION_CREDENTIALS environment variable (service account JSON)

    public String send(String deviceToken, String title, String body,
        Map<String, String> data, NotificationPriority priority) {
        // Build FCM message:
        Message message = Message.builder()
            .setToken(deviceToken)
            .setNotification(Notification.builder()
                .setTitle(title)
                .setBody(body)
                .build())
            .putAllData(data)
            .setAndroidConfig(AndroidConfig.builder()
                .setPriority(priority == CRITICAL ? AndroidConfig.Priority.HIGH : AndroidConfig.Priority.NORMAL)
                .build())
            .build();
        // FirebaseMessaging.getInstance().send(message);
        // Returns: FCM message ID (e.g., "projects/my-project/messages/0:1498893000615989%2fd966fd31fd966fd3")
        // On error: FirebaseMessagingException → log and rethrow as NotificationDeliveryException
    }

    // Batch send (for non-critical): up to 500 messages per batch
    public BatchResponse sendBatch(List<Message> messages) { ... }
}
// CRITICAL priority: AndroidConfig.Priority.HIGH (wakes device immediately)
// NORMAL priority: AndroidConfig.Priority.NORMAL
```

**Definition of Done**:
- [ ] `CRITICAL` → `AndroidConfig.Priority.HIGH` (device wakelock)
- [ ] `FirebaseMessagingException` → `NotificationDeliveryException` (service-level exception)
- [ ] Credentials from `GOOGLE_APPLICATION_CREDENTIALS` environment variable (not hardcoded)
- [ ] `FCMChannelAdapterTest`: mock `FirebaseMessaging`, verify HIGH priority for CRITICAL

---

### TASK-NCS-009: APNsChannelAdapter

**Parent WP Task**: WP-007-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/adapters/APNsChannelAdapter.java`

**Specification**:
```java
@Component
public class APNsChannelAdapter {
    // Library: com.eatthepath:pushy:0.15.x (APNs HTTP/2 client)
    // Auth: APNs JWT (key ID + team ID + private key) OR APNs certificate
    // Config: spring.apns.team-id, spring.apns.key-id, spring.apns.private-key-path

    public String send(String deviceToken, String title, String body,
        Map<String, String> payload, NotificationPriority priority) {
        // Build APNs payload:
        // { aps: { alert: { title, body }, sound: "default", badge: 1,
        //          "content-available": 1 (for CRITICAL — background wake) } }
        // apns-priority header: 10 for CRITICAL, 5 for NORMAL
        // apns-push-type: "alert" for CRITICAL, "background" for silent
        // Returns: APNs apns-id (UUID string)
    }

    // Connection pool: Pushy manages HTTP/2 multiplexing automatically
    // CRITICAL priority header: apns-priority = 10
}
```

**Definition of Done**:
- [ ] APNs priority `10` for CRITICAL, `5` for NORMAL
- [ ] Private key loaded from file path (not hardcoded)
- [ ] `APNsChannelAdapterTest`: mock Pushy client, verify priority header

---

### TASK-NCS-010: SendGridEmailAdapter

**Parent WP Task**: WP-007-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/adapters/SendGridEmailAdapter.java`

**Specification**:
```java
@Component
public class SendGridEmailAdapter {
    // Library: com.sendgrid:sendgrid-java:4.x
    // Config: spring.sendgrid.api-key (environment variable)
    // From address: spring.sendgrid.from-email, spring.sendgrid.from-name

    @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 2000, multiplier = 2))
    public String send(String toEmail, String toName, String subject, String htmlBody) {
        // Build SendGrid request:
        // Mail mail = new Mail(new Email(fromEmail, fromName), subject,
        //     new Email(toEmail, toName), new Content("text/html", htmlBody));
        // Request request = new Request(); request.setMethod(Method.POST);
        // request.setEndpoint("mail/send");
        // Response response = sendGrid.api(request);
        // If statusCode != 202: throw NotificationDeliveryException
        // Returns: response.getHeaders().get("X-Message-Id")
    }
}
// @Retryable: 3 attempts, exponential backoff: 2s → 4s → 8s
```

**Definition of Done**:
- [ ] `@Retryable` with 3 attempts, 2s/4s/8s backoff
- [ ] HTTP 202 = success; any other → `NotificationDeliveryException`
- [ ] SendGrid API key from environment variable
- [ ] HTML content type for email body

---

### TASK-NCS-011: TwilioSMSAdapter

**Parent WP Task**: WP-007-T03  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/adapters/TwilioSMSAdapter.java`

**Specification**:
```java
@Component
public class TwilioSMSAdapter {
    // Library: com.twilio.sdk:twilio:10.x
    // Config: spring.twilio.account-sid, spring.twilio.auth-token, spring.twilio.from-number

    @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 2000, multiplier = 2))
    public String send(String toPhoneNumber, String messageBody) {
        // Twilio.init(accountSid, authToken);
        // Message message = Message.creator(
        //     new PhoneNumber(toPhoneNumber),
        //     new PhoneNumber(fromPhoneNumber),
        //     messageBody
        // ).create();
        // Returns: message.getSid() — Twilio message SID
        // Validate toPhoneNumber format: must match E.164 format: ^\+[1-9]\d{1,14}$
    }

    // CRITICAL path: called via CompletableFuture in CriticalAlertService (parallel with FCM)
    // SMS body max length: 160 chars for standard SMS; truncate if needed
}
// Phone number E.164 validation: @Pattern(regexp = "^\\+[1-9]\\d{1,14}$")
```

**Definition of Done**:
- [ ] Phone number validated as E.164 format before sending
- [ ] SMS body truncated to 160 chars if exceeded
- [ ] Twilio credentials from environment variables
- [ ] `@Retryable`: 3 attempts, 2s/4s/8s backoff

---

### TASK-NCS-012: WebhookChannelAdapter (HMAC + SSRF Prevention)

**Parent WP Task**: WP-007-T03  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/adapters/WebhookChannelAdapter.java`
- `src/main/java/com/vnpt/avplatform/ncs/adapters/SSRFValidator.java`

**Specification**:
```java
// SSRFValidator.java — SSRF prevention (BL-009 cross-reference from MKP)
public class SSRFValidator {
    private static final List<String> BLOCKED_RANGES = List.of(
        "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.",
        "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
        "172.31.", "192.168.", "127.", "::1", "localhost"
    );

    public static void validateUrl(String url) {
        URI uri = URI.create(url);
        InetAddress address = InetAddress.getByName(uri.getHost());
        String ip = address.getHostAddress();
        for (String blocked : BLOCKED_RANGES) {
            if (ip.startsWith(blocked)) {
                throw new SSRFBlockedException("Webhook URL targets private IP range: " + ip);
            }
        }
        if (!url.startsWith("https://")) {
            throw new InvalidWebhookUrlException("Webhook URL must use HTTPS");
        }
    }
}

// WebhookChannelAdapter.java
@Component
public class WebhookChannelAdapter {

    @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 2000, multiplier = 2))
    public void send(WebhookEndpoint endpoint, String eventType, Object payload) {
        // 1. SSRF check (also done on registration, but re-check on send for IP change attacks)
        SSRFValidator.validateUrl(endpoint.getUrl());
        // 2. Serialize payload to JSON
        String body = objectMapper.writeValueAsString(payload);
        // 3. HMAC signature: "sha256=" + HMAC-SHA256(timestamp + "." + body, endpoint.hmacSecret)
        long timestamp = Instant.now().getEpochSecond();
        String signature = "sha256=" + computeHmacSha256(timestamp + "." + body, decryptedSecret);
        // 4. HTTP POST with headers:
        //    X-NCS-Signature: {signature}
        //    X-NCS-Timestamp: {timestamp}
        //    X-NCS-Event: {eventType}
        //    Content-Type: application/json
        // 5. On success (2xx): webhookEndpointRepository.resetFailureCount(endpointId)
        // 6. On failure: webhookEndpointRepository.incrementFailureCount(endpointId)
        //    If returns true (>= 50): publish "webhook.auto_disabled" event
    }

    // HMAC-SHA256: javax.crypto.Mac with "HmacSHA256"
    private String computeHmacSha256(String data, String secret) {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return Hex.encodeHexString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
    }
}
```

**Definition of Done**:
- [ ] HMAC format: `sha256=HMAC-SHA256(timestamp.body)` — dot separator
- [ ] SSRF check on every send (not just registration)
- [ ] HTTPS required for webhook URLs
- [ ] Auto-disable at 50 consecutive failures
- [ ] `hmacSecret` decrypted from AES-256-GCM before use

---

## Task Group 5: Core Services

### TASK-NCS-013: CriticalAlertService (Fast Path < 5s SLA)

**Parent WP Task**: WP-007-T04  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/services/CriticalAlertService.java`
- `src/main/java/com/vnpt/avplatform/ncs/services/impl/CriticalAlertServiceImpl.java`

**Specification**:
```java
public interface CriticalAlertService {
    void sendCriticalAlert(String tenantId, String recipientId, String eventType,
        Map<String, String> payload); // must complete < 5 seconds (BL-007)
}

// CRITICAL PATH — PRE-LOADED resources only (NO DB lookups):
// - Templates: ConcurrentHashMap<String, NotificationTemplate> criticalTemplates
//   Populated at @PostConstruct from templateRepository.findAllActive()
//   Keys: "ride.safety_stop:FCM", "ride.safety_stop:SMS", "emergency:FCM", "emergency:SMS"
// - Recipient device tokens: fetched from Redis (maintained by TMS): "rider:devices:{riderId}"
// - Recipient phone: fetched from Redis: "rider:phone:{riderId}"

// sendCriticalAlert():
//   1. Get template from criticalTemplates ConcurrentHashMap (NO DB query)
//   2. Render template with Handlebars (pre-compiled at startup)
//   3. Get deviceToken from Redis "rider:devices:{riderId}" (NO DB query)
//   4. Get phoneNumber from Redis "rider:phone:{riderId}" (NO DB query)
//   5. Send FCM AND Twilio SMS SIMULTANEOUSLY (CompletableFuture.allOf):
//      CompletableFuture<String> fcmFuture = CompletableFuture.supplyAsync(
//          () -> fcmAdapter.send(deviceToken, title, body, payload, CRITICAL)
//      );
//      CompletableFuture<String> smsFuture = CompletableFuture.supplyAsync(
//          () -> twilioAdapter.send(phoneNumber, body)
//      );
//      CompletableFuture.allOf(fcmFuture, smsFuture).get(4, TimeUnit.SECONDS); // 4s timeout < 5s SLA
//   6. Log NotificationLog ASYNC (non-blocking — does NOT delay delivery):
//      CompletableFuture.runAsync(() -> notificationLogRepository.insert(log));

// CRITICAL: NO deduplication for CRITICAL alerts (always send)
// CRITICAL: NO quiet hours check for CRITICAL alerts (always send)
// CRITICAL: NO MongoDB DB lookup in the critical path (Redis only)
```

**Definition of Done**:
- [ ] ZERO MongoDB reads in critical path (Redis + ConcurrentHashMap only)
- [ ] FCM + SMS launched simultaneously via `CompletableFuture.allOf`
- [ ] 4-second timeout on `allOf.get()` (within 5s SLA)
- [ ] No deduplication for CRITICAL alerts
- [ ] No quiet hours check for CRITICAL alerts
- [ ] `CriticalAlertServiceTest`: measure end-to-end time < 5s with mock adapters

---

### TASK-NCS-014: HandlebarsTemplateService

**Parent WP Task**: WP-007-T05  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/services/HandlebarsTemplateService.java`
- `src/main/java/com/vnpt/avplatform/ncs/services/impl/HandlebarsTemplateServiceImpl.java`

**Specification**:
```java
public interface HandlebarsTemplateService {
    String render(String templateBody, Map<String, Object> variables);
    NotificationTemplate resolveTemplate(String eventType, NotificationChannel channel,
        String tenantId, String locale);
}

// Library: com.github.jknack:handlebars:4.3.x

// @PostConstruct preCompileTemplates():
//   1. Load ALL active templates from DB
//   2. For each: compile with Handlebars.compile(template.getBodyTemplate())
//   3. Store compiled template in ConcurrentHashMap<String, Template> compiledTemplates
//   Key: "{templateId}:{channelName}:{tenantId}:{locale}"

// render():
//   1. Compile on-demand if not pre-compiled (fallback)
//   2. context = Context.newBuilder(variables).build()
//   3. return compiledTemplate.apply(context)
//   4. On error: throw TemplateRenderException (HTTP 500)

// resolveTemplate():
//   1. Try: tenantId + eventType + channel + locale
//   2. Try: tenantId + eventType + channel + "vi" (default locale)
//   3. Try: null (platform default) + eventType + channel + locale
//   4. Try: null + eventType + channel + "vi"
//   5. If none found: throw TemplateNotFoundException

// Template variable examples:
//   ride.completed: { rider_name, trip_id, pickup_address, dropoff_address, fare_vnd, duration_min }
//   payment.failed: { rider_name, amount_vnd, invoice_id, retry_date }
```

**Definition of Done**:
- [ ] Templates pre-compiled at startup into `ConcurrentHashMap`
- [ ] Template lookup: 4-step fallback chain (tenant→platform, locale→default)
- [ ] Handlebars `{{variable}}` syntax for all variables
- [ ] `HandlebarsTemplateServiceTest`: render with missing variable → empty string (not exception)

---

### TASK-NCS-015: DeduplicationService (Redis SHA256)

**Parent WP Task**: WP-007-T06  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/services/DeduplicationService.java`
- `src/main/java/com/vnpt/avplatform/ncs/services/impl/DeduplicationServiceImpl.java`

**Specification**:
```java
public interface DeduplicationService {
    boolean isDuplicate(String eventId, String recipientId, NotificationChannel channel);
    void markSent(String eventId, String recipientId, NotificationChannel channel);
}

// Redis key: SHA256(eventId + ":" + recipientId + ":" + channel.name())
// TTL: 3600 seconds (1 hour)

// isDuplicate():
//   String rawKey = eventId + ":" + recipientId + ":" + channel.name();
//   String dedupKey = DigestUtils.sha256Hex(rawKey); // Apache Commons Codec
//   String redisKey = "notif_dedup:" + dedupKey;
//   return Boolean.TRUE.equals(redisTemplate.hasKey(redisKey));

// markSent():
//   String redisKey = "notif_dedup:" + DigestUtils.sha256Hex(rawKey);
//   redisTemplate.opsForValue().set(redisKey, "1", Duration.ofSeconds(3600));

// CRITICAL alerts bypass deduplication entirely (not checked here — enforced in CriticalAlertService)
```

**Definition of Done**:
- [ ] SHA256 hash key: `SHA256(eventId:recipientId:channel)`
- [ ] Redis TTL: 3600 seconds
- [ ] `isDuplicate` and `markSent` are separate operations (not atomic — idempotent by design)
- [ ] `DeduplicationServiceTest`: duplicate event returns true, unique event returns false

---

### TASK-NCS-016: QuietHoursService

**Parent WP Task**: WP-007-T06  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/services/QuietHoursService.java`
- `src/main/java/com/vnpt/avplatform/ncs/services/impl/QuietHoursServiceImpl.java`

**Specification**:
```java
public interface QuietHoursService {
    boolean isQuietHour(String tenantId, String recipientId, NotificationChannel channel);
    boolean shouldDefer(NotificationPriority priority, String tenantId, String recipientId);
}

// Quiet hours: 22:00 – 07:00 local time (tenant timezone from TenantConfig)
// Applied to: LOW and NORMAL priority only
// NOT applied to: HIGH and CRITICAL (always send)

// isQuietHour():
//   String timezone = tenantConfigService.getTimezone(tenantId); // cached in Redis
//   ZonedDateTime now = ZonedDateTime.now(ZoneId.of(timezone));
//   int hour = now.getHour();
//   return hour >= 22 || hour < 7; // 22:00–07:00

// shouldDefer():
//   if (priority == CRITICAL || priority == HIGH) return false;
//   return isQuietHour(tenantId, recipientId, channel);

// If deferred: schedule for 07:00 next day local time
//   long delaySeconds = computeDelayUntil7AM(timezone);
//   taskScheduler.schedule(() -> dispatchNotification(log), Instant.now().plusSeconds(delaySeconds));
```

**Definition of Done**:
- [ ] CRITICAL and HIGH bypass quiet hours entirely
- [ ] LOW and NORMAL deferred to 07:00 local time during quiet hours
- [ ] Timezone from tenant config (Redis cached)
- [ ] `QuietHoursServiceTest`: 23:00 returns true, 08:00 returns false

---

### TASK-NCS-017: NotificationDispatchService (Standard Path)

**Parent WP Task**: WP-007-T07  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/services/NotificationDispatchService.java`
- `src/main/java/com/vnpt/avplatform/ncs/services/impl/NotificationDispatchServiceImpl.java`

**Specification**:
```java
public interface NotificationDispatchService {
    void dispatch(DispatchRequest request); // standard (non-critical) notification path
}

// DispatchRequest: { tenantId, recipientId, eventType, channels[], priority, variables }

// dispatch() — standard path (CRITICAL goes to CriticalAlertService):
//   For each channel in request.channels:
//     1. DeduplicationService.isDuplicate() → if true: skip (status=DEDUPED)
//     2. QuietHoursService.shouldDefer() → if true: defer (schedule for 07:00)
//     3. HandlebarsTemplateService.resolveTemplate(eventType, channel, tenantId, locale)
//     4. HandlebarsTemplateService.render(template.bodyTemplate, variables)
//     5. Get recipient contact (from Redis cache or TMS API):
//        FCM: "rider:devices:{recipientId}" → deviceToken
//        EMAIL: "rider:email:{recipientId}" → email
//        SMS: "rider:phone:{recipientId}" → phone
//     6. Send via appropriate adapter:
//        @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 2000, multiplier = 2))
//     7. DeduplicationService.markSent() on success
//     8. NotificationLogRepository.insert(NotificationLog { status: SENT })
//     9. On all retry failures: NotificationLogRepository.insert(NotificationLog { status: FAILED })
//        → Kafka: "notification-dlq" topic for DLQ retry
```

**Definition of Done**:
- [ ] Dedup check BEFORE template render (no wasted work on duplicates)
- [ ] Quiet hours check BEFORE adapter call
- [ ] Retry: 3 attempts, 2s/4s/8s exponential backoff via `@Retryable`
- [ ] All failures published to `notification-dlq` topic
- [ ] `NotificationLogRepository.insert()` on every outcome (SENT, FAILED, DEDUPED)

---

### TASK-NCS-018: DLQRetryScheduler

**Parent WP Task**: WP-007-T08  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/services/DLQRetryScheduler.java`
- `src/main/java/com/vnpt/avplatform/ncs/services/impl/DLQRetrySchedulerImpl.java`

**Specification**:
```java
// DLQ consumer + retry scheduler

// Consumes: "notification-dlq" topic (DLQ for failed notifications)
// @KafkaListener(topics = "notification-dlq", groupId = "ncs-dlq")
// Retry every 1 hour (initial delay on DLQ)
// Max DLQ retries: 3 (after 3 DLQ retries → PagerDuty alert)

// handleDLQMessage():
//   1. Load NotificationLog by notificationId
//   2. If retryCount >= 3: publish PagerDuty alert via PagerDuty Events API
//      POST https://events.pagerduty.com/v2/enqueue { routing_key, payload }
//      Mark log status: FAILED (permanent)
//      return
//   3. Increment retryCount
//   4. Retry: notificationDispatchService.dispatch(reconstructedRequest)
//   5. On success: update log status to SENT
//   6. On failure: re-publish to "notification-dlq" with incremented retryCount header

// PagerDuty alert payload:
// { routing_key: env.PAGERDUTY_ROUTING_KEY, event_action: "trigger",
//   payload: { summary: "Notification DLQ max retries exceeded", severity: "critical",
//              custom_details: { notificationId, tenantId, channel } } }

// Retry delay: handled by Kafka consumer — messages have header "retry_after_epoch"
// Consumer skips messages where retry_after_epoch > now (poll every 5 minutes)
```

**Definition of Done**:
- [ ] Max 3 DLQ retries before PagerDuty alert
- [ ] PagerDuty routing key from environment variable (`PAGERDUTY_ROUTING_KEY`)
- [ ] DLQ consumer polls every 5 minutes (not continuously)
- [ ] Failed notifications marked status=FAILED (permanent) after 3 DLQ retries

---

## Task Group 6: Kafka Integration

### TASK-NCS-019: KafkaEventConsumer (All Topics)

**Parent WP Task**: WP-007-T09  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/events/KafkaEventConsumer.java`

**Specification**:
```java
@Component
public class KafkaEventConsumer {
    // Consumer group: ncs-consumer
    // Consumes ALL event topics:

    // ride-events: ride.completed, ride.cancelled, ride.safety_stop, ride.matched
    @KafkaListener(topics = "ride-events", groupId = "ncs-consumer")
    public void handleRideEvent(ConsumerRecord<String, String> record) {
        Map<String, Object> event = objectMapper.readValue(record.value(), Map.class);
        String eventType = (String) event.get("eventType");
        String tenantId = (String) event.get("tenantId");
        String riderId = (String) event.get("riderId");

        switch (eventType) {
            case "ride.safety_stop":
                // CRITICAL path — bypass standard dispatch
                criticalAlertService.sendCriticalAlert(tenantId, riderId, "ride.safety_stop",
                    Map.of("trip_id", (String) event.get("tripId")));
                break;
            case "ride.completed":
                notificationDispatchService.dispatch(DispatchRequest.of(tenantId, riderId,
                    "ride.completed", List.of(FCM, EMAIL), HIGH, extractVariables(event)));
                break;
            case "ride.cancelled":
                notificationDispatchService.dispatch(DispatchRequest.of(tenantId, riderId,
                    "ride.cancelled", List.of(FCM, SMS), NORMAL, extractVariables(event)));
                break;
        }
    }

    // payment-events: payment.captured, payment.failed, payment.refunded
    @KafkaListener(topics = "payment-events", groupId = "ncs-consumer")
    public void handlePaymentEvent(ConsumerRecord<String, String> record) { ... }

    // billing-events: billing.subscription_suspended, billing.quota_warning, billing.invoice_generated
    @KafkaListener(topics = "billing-events", groupId = "ncs-consumer")
    public void handleBillingEvent(ConsumerRecord<String, String> record) { ... }
}
// Manual offset commit after successful processing
// DLQ: on processing failure → publish to "notification-dlq"
```

**Definition of Done**:
- [ ] `ride.safety_stop` → `CriticalAlertService` (NOT standard dispatch)
- [ ] Consumer group: `ncs-consumer`
- [ ] Manual offset commit (not auto-commit)
- [ ] Failed processing → publish to `notification-dlq`

---

### TASK-NCS-020: NotificationKafkaProducer

**Parent WP Task**: WP-007-T09  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/events/NotificationKafkaProducer.java`

**Specification**:
```java
// Topics published:
// "notification-events": notification.sent, notification.failed, notification.deduped
// "notification-dlq": failed notifications for retry

public class NotificationEvent {
    private String notificationId;
    private String eventType; // "notification.sent" | "notification.failed"
    private String tenantId;
    private String recipientId;
    private String channel;
    private String originalEventType; // source event that triggered notification
    private Instant timestamp = Instant.now();
}
// Partition key: tenantId
// "notification-dlq" topic: include retryCount and retryAfterEpoch headers
```

**Definition of Done**:
- [ ] `notification-dlq` messages include `retryCount` and `retry_after_epoch` Kafka headers
- [ ] `notification-events` published after every send attempt (success or failure)

---

## Task Group 7: REST Controllers

### TASK-NCS-021: NotificationController

**Parent WP Task**: WP-007-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/controllers/NotificationController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/notifications")
public class NotificationController {

    // POST /api/v1/notifications/send (internal — direct send by other services)
    @PostMapping("/send")
    @PreAuthorize("hasRole('INTERNAL_SERVICE')")
    @ResponseStatus(HttpStatus.ACCEPTED) // 202 — async processing
    public void sendNotification(@Valid @RequestBody SendNotificationRequest request) {
        String tenantId = TenantContextHolder.requireTenantId();
        notificationDispatchService.dispatch(DispatchRequest.of(tenantId, ...));
    }

    // GET /api/v1/notifications?recipient_id=xxx&page=0&size=20
    @GetMapping
    @PreAuthorize("hasAnyRole('TENANT_ADMIN', 'PLATFORM_ADMIN')")
    public List<NotificationLogDTO> listNotifications(
        @RequestParam(required = false) String recipientId,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) { ... }
}
// POST /send returns 202 Accepted (not 200 — async processing)
// SendNotificationRequest validation:
//   recipientId: @NotBlank
//   eventType: @NotBlank
//   channels: @NotEmpty
//   priority: @NotNull
```

**Definition of Done**:
- [ ] POST returns HTTP 202 (async — notification may not be delivered yet)
- [ ] `INTERNAL_SERVICE` role for direct send
- [ ] List endpoint scoped to tenant

---

### TASK-NCS-022: WebhookEndpointController

**Parent WP Task**: WP-007-T10  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/controllers/WebhookEndpointController.java`

**Specification**:
```java
@RestController
@RequestMapping("/api/v1/webhooks")
@PreAuthorize("hasRole('TENANT_ADMIN')")
public class WebhookEndpointController {

    // POST /api/v1/webhooks (register endpoint)
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public WebhookEndpointDTO register(@Valid @RequestBody RegisterWebhookRequest request) {
        // 1. SSRF validate URL
        SSRFValidator.validateUrl(request.getUrl());
        // 2. Generate HMAC secret (UUID → AES-256-GCM encrypt)
        // 3. Save WebhookEndpoint
        // Return: { endpointId, url, eventsSubscribed, hmacSecretPreview: "sk_live_****" }
    }

    // GET /api/v1/webhooks
    @GetMapping
    public List<WebhookEndpointDTO> list() { ... }

    // DELETE /api/v1/webhooks/{endpointId}
    @DeleteMapping("/{endpointId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable String endpointId) { ... }
}
// RegisterWebhookRequest validation:
//   url: @NotBlank @Pattern(regexp = "^https://.*") — must be HTTPS
//   eventsSubscribed: @NotEmpty — at least one event
```

**Definition of Done**:
- [ ] URL must start with `https://` (validated by regex + SSRFValidator)
- [ ] HMAC secret returned once on creation (never exposed again — only preview shown)
- [ ] DELETE is soft delete (`isActive = false`)

---

## Task Group 8: Configuration

### TASK-NCS-024: MongoConfig + RedisConfig

**Parent WP Task**: WP-007-T02  
**Estimated Time**: 1 hour  
**Files to Create**:
- `src/main/java/com/vnpt/avplatform/ncs/config/MongoConfig.java`
- `src/main/java/com/vnpt/avplatform/ncs/config/RedisConfig.java`

**Specification**:
```java
// MongoConfig indexes + TTL:
// notification_logs: notification_id (unique), tenant_id, event_id
// TTL index: { created_at: 1 } expireAfterSeconds: 7776000 (90 days)
// notification_templates: compound { template_id, channel, tenant_id, locale }
// webhook_endpoints: endpoint_id (unique), tenant_id

// RedisConfig: Lettuce connection pool, maxTotal=50
```

**Definition of Done**:
- [ ] TTL index on `notification_logs.created_at` (90 days = 7776000 seconds)
- [ ] Compound index on templates for fast lookup
- [ ] Redis connection pool configured

---

## Task Group 9: Tests

### TASK-NCS-025: Unit Tests — CriticalAlertService (< 5s SLA)

**Parent WP Task**: WP-007-T11  
**Estimated Time**: 2 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/ncs/services/CriticalAlertServiceTest.java`

**Test Cases**:
```
1. criticalAlert_sendsSimultaneously: FCM + SMS via CompletableFuture.allOf
2. criticalAlert_completesUnder5Seconds: measure wall clock time < 5s
3. criticalAlert_noDbLookup: verify NO MongoDB calls (mock verify)
4. criticalAlert_noDedup: even if dedup Redis key exists, sends anyway
5. criticalAlert_noQuietHours: sends at 23:00 (quiet hours) without deferral
6. criticalAlert_fcmFails_smsStillSent: FCM failure does not block SMS
7. criticalAlert_logsAsync: log insert called AFTER send returns (async)
```

**Definition of Done**:
- [ ] Test 2: wall clock assertion `< 5000ms` with mock adapters
- [ ] Test 3: `verify(notificationLogRepository, never()).insert(...)` before send completes
- [ ] Test 6: `allOf` continues even if one future fails

---

### TASK-NCS-026: Unit Tests — DeduplicationService

**Parent WP Task**: WP-007-T11  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/ncs/services/DeduplicationServiceTest.java`

**Test Cases**:
```
1. firstSend_notDuplicate: fresh eventId → isDuplicate=false
2. secondSend_isDuplicate: after markSent → isDuplicate=true
3. ttlExpiry_notDuplicate: after 3600s TTL → isDuplicate=false (mock Redis expiry)
4. differentChannel_notDuplicate: same event, different channel → not deduped
5. hashCorrectness: SHA256(eventId:recipientId:FCM) produces expected hash
```

**Definition of Done**:
- [ ] Test 5: compute expected SHA256 in test and compare
- [ ] Test 4: FCM and EMAIL have separate dedup keys

---

### TASK-NCS-028: Unit Tests — WebhookChannelAdapter (HMAC)

**Parent WP Task**: WP-007-T11  
**Estimated Time**: 1.5 hours  
**Files to Create**:
- `src/test/java/com/vnpt/avplatform/ncs/adapters/WebhookChannelAdapterTest.java`

**Test Cases**:
```
1. send_success: 200 response → resetFailureCount called
2. send_failure: 500 response → incrementFailureCount called, retried 3x
3. ssrf_privateIP_blocked: webhook URL 192.168.1.1 → SSRFBlockedException
4. ssrf_localhost_blocked: webhook URL localhost → SSRFBlockedException
5. hmacSignature_format: "sha256=" prefix + correct HMAC
6. autoDisable_at50Failures: incrementFailureCount returns true → webhook disabled
7. httpsRequired: http:// URL → InvalidWebhookUrlException
```

**Definition of Done**:
- [ ] Test 3: IP `10.0.0.1`, `172.16.x.x`, `192.168.x.x`, `127.x.x.x`, `localhost` all blocked
- [ ] Test 5: HMAC computed with `timestamp.body` format verified
- [ ] Test 6: `isActive=false` published as event

---

*DETAIL_PLAN_NCS v1.0.0 — NCS Notification & Communication | VNPT AV Platform Services Provider Group*
