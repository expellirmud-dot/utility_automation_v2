# READ-FIRST Report: PRODUCT-005B1

## Task
Implement budget preview normalizer only.

## Files Inspected
- `repo_memory/PRODUCT_CONTROLLER_OVERRIDE.md`
- `docs/Control.md`
- `src/product/services/remained_budget_parser.py`

## Context & Constraints Confirmed
- This is a PRODUCT recovery task (PRODUCT-005B1).
- The focus is strictly on transforming parser output into a canonical preview-only shape.
- NO database import, schema changes, or UI/API implementations.
- `department`, `plan`, `budget` must be "รอข้อมูลจริง" (placeholders).
- Strict withholding tax derivation rules apply.
- Evidence tracking must separate `extracted`, `placeholders`, `derived`, and `evidence`.

## Next Steps
- Implement `src/product/services/budget_preview_normalizer.py`
- Implement `tests/product/test_budget_preview_normalizer.py`
- Run validation and generate final worker report.
