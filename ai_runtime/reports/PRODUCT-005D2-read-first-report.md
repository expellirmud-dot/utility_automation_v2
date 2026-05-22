# READ-FIRST Report: PRODUCT-005D2

## Context
This task focuses on improving the budget preview matcher evidence and adding readable message codes. It aims to make readiness results easier to audit and explain without changing the existing API or frontend behavior.

## Files Inspected
1. `src/product/services/budget_preview_matcher.py` - Core logic for categorization, withholding tax, and readiness checks.
2. `tests/product/test_budget_preview_matcher.py` - Existing tests for the matcher functionality.

## Proposed Strategy
1. Modify `BudgetPreviewMatcher.match_case_to_preview` to include `blocker_details`, `warning_details`, and `missing_data_details`.
2. Each detail object will follow the schema: `{"code": "...", "level": "...", "message": "...", "field": "...", "detail": {...}}`.
3. Preserve the original plain string arrays (`blockers`, `warnings`, `missing_data`) to prevent breaking existing API consumers or the UI.
4. Add an `evidence` object that includes provenance like `source_file`, `source_sheet`, `source_hash`, `preview_row_id`, and `source_row`.
5. Add/update assertions in `tests/product/test_budget_preview_matcher.py` to ensure the detailed codes and evidence are returned correctly.
6. Verify no external side-effects (DB, schema, frontend) exist.
