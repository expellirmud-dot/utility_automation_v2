# DEFINITION OF DONE
# Updated: 20/05/2569

## Product Task DoD

A PRODUCT task is not complete until all required gates pass.

---

## Required Gates

1. Scope matches approved plan
2. READ-FIRST evidence exists
3. Serena evidence exists for repo-aware work
4. Exact files changed are reported
5. Tests pass
6. Frontend build passes when frontend changed
7. Generated artifacts are proven when applicable
8. Reports are written to `ai_runtime/reports`
9. Forbidden files are not staged
10. `git diff --cached --check` passes before commit
11. Controller approves commit
12. Commit is pushed to the correct branch

---

## Standard Validation Commands

Backend/product tests:

```powershell
python -m pytest tests/product -q
```

Frontend build:

```powershell
cd frontend\product-ui
npm run build
cd ..\..
```

Git hygiene:

```powershell
git status --short
git diff --stat
git diff --cached --check
git status --short | Select-String "\.next|node_modules|product\.db|uploads|generated|__pycache__"
```

---

## Forbidden Commit Content

Do not commit:

- `.next/`
- `node_modules/`
- `data/*.db`
- `data/uploads/`
- `data/generated/`
- `__pycache__/`
- temporary archives
- videos
- raw mockup files unless explicitly approved
- unrelated legacy TASK artifacts
