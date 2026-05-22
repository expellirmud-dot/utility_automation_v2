# PRODUCT-005C2A Read-First Report

## Inspection Summary
- **Files Inspected**: 
  - `src/product/api/budget.py`
- **Current State**: 
  - `budget.py` contains budget endpoints including `/preview/remained-budget` which uses the parser and normalizer.
  - The endpoint we need to add is a POST to `/preview/readiness`.
  - It does not require database access or reading Excel files.
- **Goal**: 
  - Add a POST endpoint `/preview/readiness` accepting `case_facts` and `budget_preview_batch` and returning `BudgetPreviewMatcher.match_case_to_preview(...)`.
  - Strict compliance: no DB access, no file system access, no mutations.

## Action Plan
1. In `src/product/api/budget.py`:
   - Import `BudgetPreviewMatcher` if not already imported.
   - Add a Pydantic model for the request payload `ReadinessPreviewRequest(BaseModel)`.
   - Add `@router.post("/preview/readiness")` returning the matcher's result.
2. In `tests/product/test_budget_readiness_preview_endpoint.py`:
   - Write tests using `TestClient` verifying the endpoint exists, handles electricity, handles blocked statuses, missing data, and requires no DB.
3. Validate tests.
4. Generate final worker report and runtime manifest.
