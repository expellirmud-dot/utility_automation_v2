# PRODUCT-005D1 Read First Report

## Goal
Replace hardcoded `http://127.0.0.1:8000` API base URL usage in `frontend/product-ui/app/create/page.tsx` with a minimal local helper or constant.

## Context
- **Scope**: Frontend URL refactoring.
- **Rules applied**: `repo_memory/PRODUCT_CONTROLLER_OVERRIDE.md` overrides legacy rules; do not change backend API behavior, no new dependencies, no backend files touched. MVP approach preferred.
- **Constraints**: 
  - Do not change endpoint paths (`/api/budget/preview/remained-budget`, `/api/budget/preview/readiness`, `/api/cases/`).
  - Do not change request/response behavior or add new actions.
  - Keep readiness and budget previews read-only.
  
## Findings
- `frontend/product-ui/app/create/page.tsx` had 3 hardcoded URLs.
- Option A (local constant inside the file) was requested as minimal approach.

## Plan
1. Insert `const API_BASE_URL = process.env.NEXT_PUBLIC_PRODUCT_API_BASE_URL ?? "http://127.0.0.1:8000";`
2. Insert `const apiUrl = (path: string) => \`\${API_BASE_URL}\${path}\`;`
3. Replace hardcoded strings with `apiUrl(...)` calls.
4. Verify backend, DB, governance remain untouched.
5. Validate via `npm run build` and pytest commands.
