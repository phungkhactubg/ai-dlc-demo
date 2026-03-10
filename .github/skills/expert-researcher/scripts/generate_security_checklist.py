#!/usr/bin/env python3
"""
Security Checklist Generator
Generate security review checklists based on feature type.
Ensures no critical security considerations are missed during planning.
"""
import argparse
from datetime import datetime

CHECKLISTS = {
    "api": {
        "title": "API Security Checklist",
        "items": [
            ("Authentication", [
                "JWT token validation on all endpoints",
                "Token expiration properly configured",
                "Refresh token mechanism if needed",
                "API key management for service-to-service calls",
            ]),
            ("Authorization", [
                "Role-Based Access Control (RBAC) implemented",
                "Resource-level permissions checked",
                "Multi-tenancy isolation enforced",
                "Context.TenantID propagated to all queries",
            ]),
            ("Input Validation", [
                "All inputs validated at controller layer",
                "Request body size limits configured",
                "Query parameters sanitized",
                "Path parameters validated",
                "No SQL/NoSQL injection vulnerabilities",
            ]),
            ("Data Protection", [
                "Sensitive data NOT logged (passwords, tokens, PII)",
                "Response doesn't leak internal errors",
                "HTTPS enforced",
                "CORS properly configured",
            ]),
            ("Rate Limiting", [
                "Rate limiting applied to public endpoints",
                "Brute force protection on auth endpoints",
                "Per-tenant rate limits if applicable",
            ]),
        ]
    },
    "frontend": {
        "title": "Frontend Security Checklist",
        "items": [
            ("XSS Prevention", [
                "User input sanitized before rendering",
                "React's automatic escaping not bypassed (no dangerouslySetInnerHTML)",
                "Content Security Policy (CSP) headers configured",
            ]),
            ("Authentication Handling", [
                "Tokens stored securely (HttpOnly cookies preferred)",
                "Token refresh handled gracefully",
                "Logout clears all sensitive data",
                "Protected routes redirect unauthenticated users",
            ]),
            ("Data Handling", [
                "Sensitive data not stored in localStorage",
                "API responses validated with Zod schemas",
                "Error messages don't expose internal details",
            ]),
            ("Dependencies", [
                "No known vulnerabilities (npm audit)",
                "Dependencies from trusted sources",
                "Subresource Integrity (SRI) for CDN resources",
            ]),
        ]
    },
    "database": {
        "title": "Database Security Checklist",
        "items": [
            ("Access Control", [
                "Least privilege principle for DB users",
                "Separate credentials for read/write operations",
                "Connection strings not hardcoded",
            ]),
            ("Data Protection", [
                "Sensitive fields encrypted at rest",
                "PII data identified and protected",
                "Backup encryption enabled",
            ]),
            ("Query Safety", [
                "Parameterized queries only (no string concatenation)",
                "Input validation before queries",
                "Query timeout limits configured",
            ]),
            ("Auditing", [
                "Audit logs for sensitive operations",
                "CreatedAt/UpdatedAt timestamps on records",
                "Soft delete vs hard delete decision made",
            ]),
        ]
    },
    "infrastructure": {
        "title": "Infrastructure Security Checklist",
        "items": [
            ("Network", [
                "Services not exposed to public internet unnecessarily",
                "Internal communication over private network",
                "Firewall rules properly configured",
            ]),
            ("Secrets Management", [
                "Secrets NOT in source code",
                "Environment variables or secrets manager used",
                "Secrets rotation strategy defined",
            ]),
            ("Container Security", [
                "Base images from trusted sources",
                "Non-root user in containers",
                "Image vulnerability scanning enabled",
            ]),
            ("Monitoring", [
                "Security events logged",
                "Alerting for suspicious activities",
                "Regular security audits scheduled",
            ]),
        ]
    }
}

def generate_checklist(feature_name, types):
    """Generate markdown checklist."""
    output = f"""# Security Review Checklist: {feature_name}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Status:** [ ] Pending Review

---

"""
    for check_type in types:
        if check_type not in CHECKLISTS:
            continue
        
        checklist = CHECKLISTS[check_type]
        output += f"## {checklist['title']}\n\n"
        
        for category, items in checklist["items"]:
            output += f"### {category}\n\n"
            for item in items:
                output += f"- [ ] {item}\n"
            output += "\n"
    
    output += """---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | | | |
| Reviewer | | | |
| Security Lead | | | |

## Notes

_Add any additional security considerations or exceptions here._
"""
    
    return output

def main():
    parser = argparse.ArgumentParser(description="Generate security review checklists")
    parser.add_argument("feature", help="Feature name")
    parser.add_argument(
        "--types", 
        nargs="+", 
        choices=["api", "frontend", "database", "infrastructure", "all"],
        default=["all"],
        help="Types of checklists to generate"
    )
    parser.add_argument("--output", "-o", help="Output file (prints to stdout if not specified)")
    
    args = parser.parse_args()
    
    types = args.types
    if "all" in types:
        types = list(CHECKLISTS.keys())
    
    checklist = generate_checklist(args.feature, types)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(checklist)
        print(f"[✓] Checklist saved to: {args.output}")
    else:
        print(checklist)

if __name__ == "__main__":
    main()
