# PRODUCT-006A Read-First Report

## Context
PRODUCT-006A aims to add structured `DataQualityIssue` evidence objects to the `ReadinessValidator` while preserving the existing flat `blockers` and `warnings` lists for backward compatibility. This improves auditability and aligns the `ReadinessValidator` with `BudgetPreviewMatcher`.

## Files Inspected
- `src/product/services/readiness_validator.py`
- `tests/product/test_readiness_validator.py`
- `src/product/services/budget_preview_matcher.py` (for structured evidence format reference)

## Findings
The `ReadinessValidator` exposes `evaluate_readiness(case, db)`, which aggregates various checks:
1. `check_documents` -> "ไม่มีเอกสารอัปโหลด" -> Will map to `MISSING_SOURCE_DOCUMENT`
2. `check_ocr_status` -> "ยังไม่มีบิลที่ผ่านการวิเคราะห์ (OCR) สำเร็จ" -> Will map to `MISSING_SUCCESSFUL_OCR`
3. `check_dika_metadata` -> "ข้อมูลฎีกาไม่ครบถ้วน" -> Will map to `INCOMPLETE_DIKA_METADATA`
4. `check_memo_generated` -> "ยังไม่ได้สร้างบันทึกข้อความ (Word)" -> Will map to `MISSING_MEMO`
5. `validate_budget` -> returns dictionary. Reason will map to `INSUFFICIENT_BUDGET`.
6. `check_duplicate_bill` -> returns a list of warning strings. Each string will map to `DUPLICATE_BILL_WARNING`.

## Strategy
1. Modify `evaluate_readiness` in `ReadinessValidator` to instantiate `blocker_details` and `warning_details` alongside the `blockers` and `warnings` arrays.
2. Build each detail object matching the required schema.
3. Update `test_readiness_validator.py` to assert the presence of these new objects without breaking existing assertions.
4. Execute test validation.
