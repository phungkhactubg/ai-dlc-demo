#!/usr/bin/env python3
"""
Security Checklist Generator
=============================

Generate security review checklists for features.

Usage:
    python generate_security_checklist.py "User Authentication" --types all
    python generate_security_checklist.py "Payment API" --types api database
    python generate_security_checklist.py "Admin Panel" -o security_review.md
"""

import argparse
from datetime import datetime
from pathlib import Path


CHECKLISTS = {
    "api": """### API Security
- [ ] **Authentication**: All endpoints require valid JWT
- [ ] **Authorization**: Role/permission checks implemented
- [ ] **Input Validation**: All inputs validated and sanitized
- [ ] **Rate Limiting**: Rate limits applied to endpoints
- [ ] **CORS**: Properly configured for allowed origins
- [ ] **HTTPS**: TLS enforced, HTTP redirects to HTTPS
- [ ] **Error Handling**: Errors don't leak internal details
- [ ] **Request Size**: Maximum request body size enforced
- [ ] **Response Filtering**: Sensitive fields excluded
- [ ] **Audit Logging**: All mutations logged
""",

    "database": """### Database Security
- [ ] **Connection**: Credentials not in code, use env/vault
- [ ] **Network**: Database not publicly accessible
- [ ] **Encryption at Rest**: Enabled for sensitive data
- [ ] **Query Safety**: Parameterized queries, no injection
- [ ] **Tenant Isolation**: Multi-tenancy enforced in all queries
- [ ] **Backup Security**: Backups encrypted
- [ ] **Access Control**: Minimal privileges for app user
- [ ] **Audit Trail**: Schema changes tracked
""",

    "auth": """### Authentication & Authorization
- [ ] **JWT Validation**: Token signature verified
- [ ] **Token Expiry**: Expiration enforced (24h default)
- [ ] **Refresh Flow**: Secure refresh token mechanism
- [ ] **Password Policy**: Minimum complexity enforced
- [ ] **Password Storage**: bcrypt/argon2 hashing
- [ ] **Session Management**: Secure session handling
- [ ] **Logout**: Token invalidation on logout
- [ ] **MFA**: Multi-factor option available (if required)
- [ ] **Account Lockout**: Brute force protection
- [ ] **Password Reset**: Secure reset flow
""",

    "data": """### Data Protection
- [ ] **PII Encryption**: Personal data encrypted at rest
- [ ] **Key Management**: Encryption keys properly managed
- [ ] **Data Masking**: Sensitive data masked in logs
- [ ] **Data Retention**: Retention policies defined
- [ ] **Soft Delete**: Deleted data handled properly
- [ ] **Export Controls**: Data export restrictions
- [ ] **Consent**: User consent captured where required
""",

    "frontend": """### Frontend Security
- [ ] **XSS Prevention**: User input sanitized in output
- [ ] **CSRF Protection**: Tokens for state-changing ops
- [ ] **CSP**: Content Security Policy headers set
- [ ] **Secure Cookies**: HttpOnly, Secure, SameSite flags
- [ ] **Token Storage**: JWT in httpOnly cookies or secure storage
- [ ] **Dependency Audit**: npm audit clean
- [ ] **Form Validation**: Client-side validation (+ server)
- [ ] **Click Jacking**: X-Frame-Options set
""",

    "infrastructure": """### Infrastructure Security
- [ ] **Container Security**: Non-root user, minimal base image
- [ ] **Secrets Management**: K8s secrets or vault used
- [ ] **Network Policies**: Pod-to-pod communication restricted
- [ ] **Resource Limits**: CPU/memory limits set
- [ ] **Firewall**: Only required ports open
- [ ] **TLS Termination**: TLS 1.2+ at ingress
- [ ] **Image Scanning**: Vulnerability scanning enabled
- [ ] **Log Aggregation**: Centralized logging
""",

    "thirdparty": """### Third-Party & Dependencies
- [ ] **Vulnerability Scan**: Dependencies scanned for CVEs
- [ ] **Version Pinning**: Versions locked in requirements
- [ ] **License Check**: Licenses are compatible
- [ ] **API Keys**: External API keys secured
- [ ] **Timeout Handling**: Timeouts for external calls
- [ ] **Data Minimization**: Minimal data sent externally
""",

    "business": """### Business Logic Security
- [ ] **Privilege Escalation**: Cannot gain unauthorized access
- [ ] **Bypass Prevention**: Cannot bypass business rules
- [ ] **Race Conditions**: Concurrent requests handled safely
- [ ] **Financial Controls**: Transaction limits enforced
- [ ] **Audit Trail**: Complete trail for critical operations
- [ ] **Rollback**: Ability to reverse operations
""",
}


def generate_checklist(feature_name: str, types: list) -> str:
    """Generate security checklist document."""
    doc = f"""# Security Review Checklist

**Feature:** {feature_name}
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Reviewer:** [Name]
**Status:** ⬜ Pending | ⬜ In Review | ⬜ Approved | ⬜ Requires Changes

---

## Overview

This security checklist covers the following areas:
{", ".join(types)}

---

"""
    
    for t in types:
        if t in CHECKLISTS:
            doc += CHECKLISTS[t] + "\n"
    
    doc += """---

## Findings

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| S-001 | | | Pending |
| S-002 | | | Pending |

---

## Sign-Off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Developer | | | ⬜ |
| Security Lead | | | ⬜ |
| Tech Lead | | | ⬜ |

---

## Notes

[Additional notes and exceptions]
"""
    
    return doc


def main():
    parser = argparse.ArgumentParser(
        description="Generate security review checklists"
    )
    parser.add_argument(
        "feature",
        help="Feature name"
    )
    parser.add_argument(
        "--types", "-t",
        nargs="+",
        choices=["api", "database", "auth", "data", "frontend", "infrastructure", "thirdparty", "business", "all"],
        default=["api", "auth", "data"],
        help="Checklist types to include"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    types = args.types
    if "all" in types:
        types = list(CHECKLISTS.keys())
    
    doc = generate_checklist(args.feature, types)
    
    output_path = args.output
    if not output_path:
        # Standardized Output Path
        safe_name = args.feature.lower().replace(" ", "_")
        output_dir = Path("project-documentation/security-checklists") / safe_name
        output_path = output_dir / "SECURITY_CHECKLIST.md"

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(doc, encoding="utf-8")
        print(f"✅ Generated security checklist: {output_path}")
    else:
        print(doc)


if __name__ == "__main__":
    main()
