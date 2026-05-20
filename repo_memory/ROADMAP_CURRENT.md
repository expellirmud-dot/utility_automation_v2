# ROADMAP CURRENT
# Updated: 20/05/2569

## Completed

- PRODUCT-001: Main dashboard and product baseline
- PRODUCT-002: Case document intake and registry
- PRODUCT-003: OCR / extraction integration
- PRODUCT-004: Word memo generation

---

## Active / Next

### PRODUCT-005: Budget Integration + Readiness Validation

Scope:

- budget lookup
- remaining balance
- budget line selection
- budget integration hardening
- submission readiness validator

Validator checks:

- documents uploaded
- OCR extracted
- provider resolved
- amount detected
- memo generated
- budget sufficient
- required fields complete

---

### PRODUCT-006: Data Quality Guardrails

Scope:

- provider alias mapping
- duplicate bill guard
- warning-only duplicate detection

---

### PRODUCT-007: e-LAAS Assist

Scope:

- prepare submission payload
- copy-ready values
- attachment checklist
- operator assist flow

---

### PRODUCT-008: Optional Browser Assist

Scope:

- Playwright guided browser automation
- login/session handling
- operator-supervised assist mode

---

### PRODUCT-009: Polish / Acceptance

Scope:

- UX cleanup
- Thai wording corrections
- edge cases
- template adjustment
- real operator testing

---

## Plan Adherence

Do not add major architecture layers unless controller approves.

Do not reintroduce governance-platform expansion into product MVP.
