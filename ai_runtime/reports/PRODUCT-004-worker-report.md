# PRODUCT-004 — Checkpoint 1 Worker Report

## Task
Word Memo / Dika Document Generation — Backend Service + Tests

## Status
CHECKPOINT 1 COMPLETE — AWAITING CONTROLLER APPROVAL FOR CHECKPOINT 2 (Frontend)

---

## Exact Files Created / Modified

### Created (new)
- `src/product/services/word_generation.py` — Word generation service with helpers
- `src/product/api/memos.py` — Dika save, memo generate, and download API routes
- `tests/product/test_word_generation.py` — 15 test cases

### Modified
- `src/product/db/models.py` — Added `file_path` column to `Memo` model (+1 line)
- `src/product/main.py` — Registered `memos_router` (+2 lines)
- `requirements.txt` — Added `python-docx` (+1 line)

---

## Architecture Decisions

1. **Template safety**: `shutil.copy2()` always copies `Word Template.docx` to `data/generated/case_{id}_memo.docx` before any edit. The original is never opened for writing.
2. **Run merging**: Each paragraph is scanned; if `[` is detected, all runs are merged into `runs[0]` before replacement. This prevents Word's run-splitting from breaking bracket detection.
3. **Deterministic replacement order**: Longer/more specific placeholders (e.g. `[…………………ผู้ออกบิล…………………..]`) are replaced before shorter ambiguous ones (`[…………..]`), preventing partial collisions.
4. **No BillHeader schema changes**: `provider`, `bill_date`, `total_amount` used as-is.
5. **No OCR rerun**: Invoice number placeholder left blank in MVP; no pipeline triggered during generation.
6. **Minimal Dika input**: Only `dika_no`, `dika_date`, `payee_name`, `memo_number`, `memo_date` accepted.

---

## Validation Output

```
pytest -v tests/product/test_word_generation.py

15 passed, 1 warning in 3.32s

pytest -q tests/product/

28 passed, 1 warning in 4.36s
```

---

## Generated File Proof

```
OUTPUT FILE: D:\utility_automation_v2_light\data\generated\case_99999_memo.docx
EXISTS: True
SIZE (bytes): 36572
TEMPLATE MTIME unchanged: OK
```

---

## Git Status

```
 M requirements.txt
 M src/product/db/models.py
 M src/product/main.py
?? src/product/api/memos.py
?? src/product/services/word_generation.py
?? tests/product/test_word_generation.py
```

Git diff --stat:
```
 requirements.txt         | 1 +
 src/product/db/models.py | 1 +
 src/product/main.py      | 2 ++
 3 files changed, 4 insertions(+)
```

---

## Remaining Risks

- `Dika.dika_number` has `unique=True` constraint — second save for same case will fail. Mitigation: upsert logic in route queries existing record first (implemented).
- SQLite does not enforce schema migrations at runtime. `Memo.file_path` column will only appear after `create_all()` is called on a fresh DB. Existing `product.db` (in `data/`) may need a migration step.

---

## Checkpoint 2 Scope (PENDING APPROVAL)

- Frontend: Add Dika/Memo form card to `frontend/product-ui/app/cases/[id]/page.tsx`
- Fields: dika_no, dika_date, payee_name, memo_number, memo_date
- Actions: Save Dika, Generate Word, Download .docx
