# Security Review Checklist

> Comprehensive security review checklist for [Feature Name]

# Security Review: [Feature Name]

**Date:** YYYY-MM-DD
**Reviewer:** [Name]
**Status:** Pending | In Review | Approved | Requires Changes

---

## 1. Authentication & Authorization

### 1.1 Authentication
- [ ] **JWT Validation**: All endpoints require valid JWT tokens
- [ ] **Token Expiry**: Token expiration is enforced (default: 24h)
- [ ] **Token Refresh**: Refresh token flow is implemented
- [ ] **Logout**: Token invalidation on logout

### 1.2 Authorization
- [ ] **Role-Based Access**: RBAC is implemented where needed
- [ ] **Permission Checks**: Each endpoint verifies user permissions
- [ ] **Resource Ownership**: Users can only access their own resources
- [ ] **Admin Override**: Admin access is properly controlled

### 1.3 Multi-Tenancy
- [ ] **Tenant Isolation**: Data is isolated by tenant_id
- [ ] **Cross-Tenant Prevention**: Cannot access other tenant's data
- [ ] **Tenant Header**: X-Tenant-ID is validated on all requests
- [ ] **Query Filtering**: All queries include tenant_id filter

---

## 2. Input Validation

### 2.1 Request Validation
- [ ] **Required Fields**: All required fields are validated
- [ ] **Type Checking**: Types are strictly enforced
- [ ] **Length Limits**: Min/max lengths are enforced
- [ ] **Format Validation**: Email, URL, UUID formats validated
- [ ] **Enum Validation**: Enums are restricted to allowed values

### 2.2 Sanitization
- [ ] **HTML Escaping**: HTML special chars are escaped in output
- [ ] **SQL/NoSQL Injection**: Parameterized queries used
- [ ] **Command Injection**: No shell commands with user input
- [ ] **Path Traversal**: File paths are validated
- [ ] **XSS Prevention**: User content is sanitized

### 2.3 File Upload (if applicable)
- [ ] **File Type Validation**: Only allowed MIME types accepted
- [ ] **File Size Limit**: Maximum file size enforced
- [ ] **Malware Scanning**: Files scanned before storage
- [ ] **Safe Storage**: Files stored outside web root

---

## 3. Data Protection

### 3.1 Sensitive Data
- [ ] **Password Hashing**: Passwords hashed with bcrypt/argon2
- [ ] **PII Encryption**: Personal data encrypted at rest
- [ ] **Key Management**: Encryption keys properly managed
- [ ] **Secrets**: No secrets in code or logs

### 3.2 Data Exposure
- [ ] **Response Filtering**: Sensitive fields excluded from responses
- [ ] **Error Messages**: Errors don't leak internal details
- [ ] **Logs**: No sensitive data in logs
- [ ] **Debug Mode**: Debug disabled in production

### 3.3 Data Retention
- [ ] **Retention Policy**: Data retention limits defined
- [ ] **Soft Delete**: Deleted data properly handled
- [ ] **Backup Security**: Backups are encrypted

---

## 4. API Security

### 4.1 Rate Limiting
- [ ] **Request Limits**: Rate limits applied to all endpoints
- [ ] **Per-User Limits**: Limits are per-user, not global
- [ ] **Burst Handling**: Burst limits configured
- [ ] **Response Headers**: Rate limit headers included

### 4.2 Request/Response
- [ ] **HTTPS Only**: HTTP redirects to HTTPS
- [ ] **CORS**: CORS properly configured for allowed origins
- [ ] **CSP**: Content Security Policy headers set
- [ ] **HSTS**: Strict-Transport-Security enabled

### 4.3 Error Handling
- [ ] **Consistent Errors**: Error format is consistent
- [ ] **No Stack Traces**: Stack traces not exposed to users
- [ ] **Error Logging**: All errors are logged server-side
- [ ] **Graceful Degradation**: Errors handled gracefully

---

## 5. Infrastructure Security

### 5.1 Network
- [ ] **Firewall Rules**: Only required ports open
- [ ] **VPC**: Services in private subnet
- [ ] **TLS**: TLS 1.2+ enforced
- [ ] **Certificate**: Valid SSL certificates

### 5.2 Database
- [ ] **Access Control**: DB credentials not in code
- [ ] **Network Access**: DB not publicly accessible
- [ ] **Encryption**: Encryption at rest enabled
- [ ] **Backup**: Automated backups configured

### 5.3 Container/Deployment
- [ ] **Base Images**: Official, minimal base images
- [ ] **Non-Root**: Containers run as non-root
- [ ] **Resource Limits**: CPU/memory limits set
- [ ] **Secrets Management**: Kubernetes secrets or vault used

---

## 6. Logging & Monitoring

### 6.1 Audit Logging
- [ ] **Create Events**: All creations logged
- [ ] **Update Events**: All updates logged with diff
- [ ] **Delete Events**: All deletions logged
- [ ] **Access Events**: Sensitive access logged
- [ ] **Auth Events**: Login/logout logged

### 6.2 Security Monitoring
- [ ] **Failed Auth**: Failed login attempts monitored
- [ ] **Rate Limit Hits**: Rate limit violations alerted
- [ ] **Error Spikes**: Error rate anomalies detected
- [ ] **Suspicious Patterns**: Unusual access patterns flagged

---

## 7. Third-Party & Dependencies

### 7.1 Dependencies
- [ ] **Vulnerability Scan**: Dependencies scanned for CVEs
- [ ] **Version Pinning**: Dependency versions locked
- [ ] **License Compliance**: Licenses are compatible
- [ ] **Update Policy**: Regular update schedule defined

### 7.2 External Services
- [ ] **API Keys**: External API keys secured
- [ ] **Timeout Handling**: Timeouts configured
- [ ] **Fallback**: Graceful fallback on failure
- [ ] **Data Sharing**: Minimal data sent to third parties

---

## 8. Business Logic Security

### 8.1 Authorization Logic
- [ ] **Privilege Escalation**: Cannot gain unauthorized access
- [ ] **Bypass Prevention**: Cannot bypass business rules
- [ ] **Race Conditions**: Concurrent requests handled safely

### 8.2 Financial/Critical Operations (if applicable)
- [ ] **Double Verification**: Critical actions require confirmation
- [ ] **Audit Trail**: Complete audit trail for transactions
- [ ] **Rollback**: Ability to reverse operations
- [ ] **Limits**: Transaction limits enforced

---

## 9. Testing & Verification

### 9.1 Security Testing
- [ ] **Unit Tests**: Security logic unit tested
- [ ] **Integration Tests**: Auth/authz integration tested
- [ ] **Penetration Test**: Pen test scheduled/completed
- [ ] **SAST**: Static analysis run on code

### 9.2 Verification Steps
| Test Case | Status | Notes |
|-----------|--------|-------|
| Access with no token | ☐ Passed | Returns 401 |
| Access with invalid token | ☐ Passed | Returns 401 |
| Access wrong tenant data | ☐ Passed | Returns 403 |
| SQL injection in search | ☐ Passed | Rejected/sanitized |
| XSS in name field | ☐ Passed | Escaped in output |

---

## 10. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Security Lead | | | |
| Tech Lead | | | |

---

## Notes & Exceptions

[Document any security exceptions with justification]
