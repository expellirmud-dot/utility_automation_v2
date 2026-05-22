# READ-FIRST Report: PRODUCT-005B2A-HARDEN

## Task
Harden backend budget preview endpoint.

## Files Inspected
- `repo_memory/PRODUCT_CONTROLLER_OVERRIDE.md`
- `docs/Control.md`
- `src/product/api/budget.py`
- `tests/product/test_budget_preview_endpoint.py`

## Context & Constraints Confirmed
- This is a PRODUCT recovery task (PRODUCT-005B2A-HARDEN).
- Goal is to harden the existing `GET /api/budget/preview/remained-budget` endpoint.
- Replace hardcoded fragile path with safe path resolution from project root.
- Ensure error responses (404, 400, 500) are safe, deterministic, and do not leak internal exception representations.
- Keep endpoint GET-only and preview-only (no DB writes/reads, no frontend integration).
- Response shape remains `BudgetPreviewBatch` with `db_import_safe` as false.

## Next Steps
- Update `src/product/api/budget.py` to use `Path(__file__).parent` resolution to find the project root and resolve the preview source file safely.
- Update error handling in the endpoint to avoid leaking raw exceptions.
- Update `tests/product/test_budget_preview_endpoint.py` to test parse/normalize failure safe messages.
- Run validations and generate final reports.