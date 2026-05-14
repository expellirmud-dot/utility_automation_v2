# Security Dependency Risk Register

This document tracks known security vulnerabilities in the project's dependencies that have been explicitly deferred.

## Deferred Risks

### Next.js / PostCSS Vulnerabilities
- **Component**: `frontend/operator-observatory`
- **Audit Finding**: `npm audit` reports high-severity vulnerabilities in `next` (DoS, XSS, SSRF) and moderate-severity in `postcss`.
- **Severity**: High
- **Deferred Rationale**: Fixing these vulnerabilities requires a major upgrade to Next.js 16.x, which is a breaking change. TASK 048 focus was a read-only observability UI, not a dependency migration. Upgrading now would introduce significant instability and risk of architectural regression.
- **Remediation Path**: Separate "Security/Dependency Hardening" task to migrate to Next.js 16.x, validate all routes, and update PostCSS.
- **Ownership**: Platform Security / Lead Engineer
- **Review Expectation**: Re-evaluate after every major frontend layout change or when a critical un-deferred vulnerability is found.

## Governance
All dependency upgrades must be deterministic and validated via the certification pipeline. `npm audit fix --force` is strictly forbidden.
