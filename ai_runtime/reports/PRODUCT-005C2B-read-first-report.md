# PRODUCT-005C2B Read First Report

## Inspected Files
- `repo_memory/PRODUCT_CONTROLLER_OVERRIDE.md` (via instructions)
- `docs/Control.md` (via instructions)
- `frontend/product-ui/app/create/page.tsx`
- `src/product/api/budget.py`
- `tests/product/test_budget_readiness_preview_endpoint.py`
- `tests/product/test_budget_preview_endpoint.py`

## Plan
1. In `frontend/product-ui/app/create/page.tsx`, we will add React state variables to track:
   - `formFiscalYear`
   - `formExpenseGroup`
   - `formAmount`
   - `formProvider`
   - `readinessData`, `readinessLoading`, `readinessError`
2. Update the form `<select>` and `<input>` elements to use these states. We will add the `required_amount` and `provider` inputs so that the user can test the readiness check effectively.
3. Add a `useEffect` that listens to `previewData` and the form state fields. If `previewData` and `formExpenseGroup` are available, it will `POST` to `/api/budget/preview/readiness` to fetch the advisory results.
4. Add a "ตรวจความพร้อมงบประมาณ" UI block directly below the form fields or near the preview section. This UI will display:
   - Advisory warning text.
   - Match status (`ready`, `warning`, `blocked`, `missing_data`).
   - matched row details (if any).
   - WHT display label.
   - Blockers, warnings, and missing data lists.
5. Preserve all existing backend endpoints, database structure, and page behaviors.
