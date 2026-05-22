# Worker Report: PRODUCT-005B2A

## Task
Implement backend read-only budget preview endpoint.

## Exact Files Inspected
- `repo_memory/PRODUCT_CONTROLLER_OVERRIDE.md`
- `docs/Control.md`
- `src/product/api/budget.py`

## Exact Files Changed
- `src/product/api/budget.py` (Modified)
- `tests/product/test_budget_preview_endpoint.py` (Created)
- `ai_runtime/reports/PRODUCT-005B2A-read-first-report.md` (Created)
- `ai_runtime/reports/PRODUCT-005B2A-worker-report.md` (Created)
- `ai_runtime/reports/PRODUCT-005B2A-runtime-manifest.json` (Created)

## Route Added
- `GET /api/budget/preview/remained-budget`

## Git Diff --stat
```
 ai_runtime/reports/PRODUCT-005B2A-read-first-report.md |  17 +++++++++++++++++
 ai_runtime/reports/PRODUCT-005B2A-runtime-manifest.json |  21 +++++++++++++++++++++
 ai_runtime/reports/PRODUCT-005B2A-worker-report.md     | 139 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 src/product/api/budget.py                              |  28 ++++++++++++++++++++++++++++
 tests/product/test_budget_preview_endpoint.py          |  71 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 5 files changed, 276 insertions(+)
```

## Validation Output
```
$ python -m pytest tests/product/test_budget_preview_endpoint.py -q ; python -m pytest tests/product/test_budget_preview_normalizer.py -q ; python -m pytest tests/product -q
...
3 passed, 1 warning in 2.08s
....
4 passed in 0.10s
..................................................................................................
98 passed, 1 warning in 10.74s
```
All tests passed successfully, including the newly added endpoint tests.

## Sample Response Shape (First Row)
```json
{
  "preview_row_id": "prev_5cc900e02301",
  "source_row": 9,
  "extracted": {
    "work": "งานบริหารทั่วไป",
    "appropriation_category": "เงินเดือน (ฝ่ายการเมือง)",
    "expense_type": "เงินเดือนนายก/รองนายกองค์กรปกครองส่วนท้องถิ่น",
    "project": "",
    "budget_code": "9969011121010001",
    "approved_amount": 695520.0,
    "transfer_in": 0.0,
    "transfer_out": 0.0,
    "obligated_amount": 27600.0,
    "disbursed_amount": 398636.0,
    "remaining_amount": 269284.0
  },
  "placeholders": {
    "department": "รอข้อมูลจริง",
    "plan": "รอข้อมูลจริง",
    "budget": "รอข้อมูลจริง"
  },
  "derived": {
    "withholding_tax": {
      "applies": null,
      "rule_id": "NON_UTILITY_UNKNOWN",
      "display_label": "รอตรวจสอบ"
    },
    "mapping_readiness": {
      "plan_work_mapping_status": "missing_reference",
      "budget_expense_mapping_status": "missing_reference",
      "db_import_status": "blocked_pending_confirmed_mapping",
      "elaas_assist_status": "preview_only"
    },
    "db_import_safe": false
  },
  "evidence": {
    "source_file": "B_RemainedBudget.xlsx",
    "source_sheet": "reportRemainBudgetXlsx",
    "source_hash": "7a1cdc75e883",
    "source_row": 9,
    "column_evidence": {
      "work": {
        "column_index": 1,
        "raw_value": "งานบริหารทั่วไป",
        "normalized_value": "งานบริหารทั่วไป"
      },
      "appropriation_category": {
        "column_index": 2,
        "raw_value": "เงินเดือน (ฝ่ายการเมือง)",
        "normalized_value": "เงินเดือน (ฝ่ายการเมือง)"
      },
      "expense_type": {
        "column_index": 3,
        "raw_value": "เงินเดือนนายก/รองนายกองค์กรปกครองส่วนท้องถิ่น",
        "normalized_value": "เงินเดือนนายก/รองนายกองค์กรปกครองส่วนท้องถิ่น"
      },
      "approved_amount": {
        "column_index": 8,
        "raw_value": 695520.0,
        "normalized_value": 695520.0
      },
      "remaining_amount": {
        "column_index": 14,
        "raw_value": 269284.0,
        "normalized_value": 269284.0
      }
    }
  }
}
```

## Confirmations
- **No DB import/init/migration was run.**
- **No frontend, DB schema, governance/runtime configs, or API configuration files were changed.**
- **No files were staged, committed, or pushed.**