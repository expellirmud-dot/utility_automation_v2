# PRODUCT VS GOVERNANCE SCOPE
# Updated: 20/05/2569

## Purpose

Prevent conflict between older governance-platform rules and the current municipal finance product workflow.

---

## Two Different Systems Exist

### 1. Governance / Runtime Platform

Legacy platform scope:

- deterministic governance runtime
- control plane
- mesh/quorum
- audit/certification
- read-only operator observatory

Rules:

- governance dashboard surfaces are read-only
- no mutation APIs unless explicitly assigned
- no authority changes
- no hidden governance behavior

---

### 2. Product App / Utility Automation e-LAAS

Current product scope:

- case creation
- document upload
- OCR extraction
- Word memo generation
- budget validation
- e-LAAS assist
- optional browser assist

Rules:

- product mutation APIs are allowed when explicitly inside approved PRODUCT scope
- product UI may call POST endpoints for approved workflows
- product state is operational data, not governance authority

---

## Valid Product Mutation Examples

Allowed inside approved PRODUCT scope:

- `POST /api/cases`
- `POST /api/cases/{case_id}/documents`
- `POST /api/cases/{case_id}/documents/{document_id}/process`
- `POST /api/cases/{case_id}/dika`
- `POST /api/cases/{case_id}/memo/generate`

---

## Forbidden Without Explicit Approval

Still forbidden:

- ledger authority changes
- mesh/quorum changes
- policy promotion changes
- recovery execution authority
- authentication redesign
- governance dashboard mutation
- repo-wide architecture rewrites

---

## Conflict Resolution

If a generic governance rule appears to block approved product work, apply this distinction:

```text
Governance console read-only rule ≠ Product application workflow rule
```

Surface the conflict in the report and proceed only within explicit PRODUCT scope.
