# READ-FIRST Report: PRODUCT-005B2B

## Task
Implement frontend read-only budget preview UI.

## Files Inspected
- `repo_memory/PRODUCT_CONTROLLER_OVERRIDE.md`
- `docs/Control.md`
- `frontend/product-ui/app/create/page.tsx`

## Context & Constraints Confirmed
- This is a PRODUCT recovery task (PRODUCT-005B2B).
- The goal is to add a read-only budget preview panel to `frontend/product-ui/app/create/page.tsx`.
- Must fetch from `GET /api/budget/preview/remained-budget`.
- Must display safe fields from the parser and normalizer, clearly mark placeholders as "รอข้อมูลจริง", and show the `db_import_safe=false` warning.
- NO API changes, DB operations, or config file changes allowed.
- Must not block case creation or integrate tightly with case saving logic (purely read-only and informational).

## Next Steps
- Update `frontend/product-ui/app/create/page.tsx` with a new `useEffect` hook to fetch data.
- Append a new section to render the BudgetPreview table with loading and error states handled gracefully.
- Run frontend build validation and backend test verification.
- Output final reports.