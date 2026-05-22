# PRODUCT-006B Design Report: Align BudgetPreviewMatcher issue detail schema

## Design Questions & Answers

**1. What schema does ReadinessValidator currently return?**
It returns a schema with flat arrays (`blockers`, `warnings`) and detailed structured arrays (`blocker_details`, `warning_details`).
The detail objects follow this structure:
```json
{
  "code": "MISSING_SOURCE_DOCUMENT",
  "level": "blocker",
  "message": "ไม่มีเอกสารอัปโหลด",
  "component": "readiness_validator",
  "field": "documents",
  "detail": {}
}
```

**2. What schema does BudgetPreviewMatcher currently return?**
It returns flat arrays (`blockers`, `warnings`, `missing_data`) and detailed structured arrays (`blocker_details`, `warning_details`, `missing_data_details`).
The detail objects follow this structure:
```json
{
  "code": "INSUFFICIENT_REMAINING_AMOUNT",
  "level": "blocker",
  "message": "ยอดขอเบิกมากกว่างบคงเหลือ",
  "field": "required_amount",
  "detail": {"required": 1000.0, "remaining": 500.0}
}
```

**3. What mismatches exist?**
The primary mismatch is the missing `component` field in `BudgetPreviewMatcher`'s detail objects. `ReadinessValidator` includes `"component": "readiness_validator"`, while `BudgetPreviewMatcher` lacks this field entirely.

**4. Should PRODUCT-006B change BudgetPreviewMatcher only?**
Yes, the scope is to align `BudgetPreviewMatcher` to match the already committed `PRODUCT-006A` schema in `ReadinessValidator`.

**5. Should flat blockers/warnings/missing_data remain untouched?**
Yes, these must remain as simple lists of strings to ensure backward compatibility with current UI or API consumers.

**6. Should blocker_details/warning_details/missing_data_details remain additive only?**
Yes, they should be returned alongside the flat arrays without replacing them.

**7. What exact codes/fields need alignment?**
Every object appended to `blocker_details`, `warning_details`, and `missing_data_details` inside `src/product/services/budget_preview_matcher.py` must have `"component": "budget_preview_matcher"` added.
This applies to:
- `MISSING_FISCAL_YEAR_BE`
- `MISSING_EXPENSE_TYPE`
- `MISSING_REQUIRED_AMOUNT`
- `PROVIDER_UNKNOWN`
- `AMBIGUOUS_NT_PROVIDER`
- `UTILITY_PROVIDER_MISMATCH`
- `NO_PREVIEW_ROWS`
- `NO_MATCHING_PREVIEW_ROW`
- `MULTIPLE_MATCHING_ROWS`
- `MISSING_REMAINING_AMOUNT`
- `INSUFFICIENT_REMAINING_AMOUNT`
- `PLACEHOLDER_MAPPING_FIELDS`

**8. What files should change in implementation?**
- `src/product/services/budget_preview_matcher.py` (to inject the `component` field).

**9. What tests need updates?**
- `tests/product/test_budget_preview_matcher.py` should be updated to assert that `w["component"] == "budget_preview_matcher"` for at least one or all detail elements to prevent regressions.

**10. What validation commands should run?**
```bash
python -m pytest tests/product/test_budget_preview_matcher.py -q
python -m pytest tests/product/test_budget_readiness_preview_endpoint.py -q
python -m pytest tests/product/test_budget_preview_endpoint.py -q
python -m pytest tests/product -q
```

---

## Recommended Implementation Slice
Simply inject `"component": "budget_preview_matcher"` into all 16 `dict` literals appended to `blocker_details`, `warning_details`, and `missing_data_details` in `src/product/services/budget_preview_matcher.py`. Then add basic assertions for the `component` field in `tests/product/test_budget_preview_matcher.py`.

## Exact files likely to change
1. `src/product/services/budget_preview_matcher.py`
2. `tests/product/test_budget_preview_matcher.py`

## Validation Plan
1. Run matcher unit tests to ensure `component` field is verified.
2. Run API endpoint tests to ensure no schema breakage.
3. Run all product tests to ensure no cross-component regressions.

## Final Git Status
```
On branch mission/recovery-audit
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        ai_runtime/reports/PRODUCT-006B-design-report.md

nothing added to commit but untracked files present (use "git add" to track)
```

**Confirmation**: No implementation code was edited, staged, committed, or pushed.
