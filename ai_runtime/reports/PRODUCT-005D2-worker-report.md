# Worker Report: PRODUCT-005D2

## Task Accomplished
Improved BudgetPreviewMatcher output to include detailed, structured codes (`blocker_details`, `warning_details`, `missing_data_details`) and an `evidence` object for better auditability, while strictly maintaining backward compatibility with the original string lists.

## Evidence & Message Code Changes
- **MISSING_FISCAL_YEAR_BE**: Added to missing data / blockers when FY is missing.
- **MISSING_EXPENSE_TYPE**: Added to missing data / blockers when expense group is missing.
- **MISSING_REQUIRED_AMOUNT**: Added to missing data / blockers when required amount is missing.
- **NO_PREVIEW_ROWS**: Blockers when batch has no rows.
- **NO_MATCHING_PREVIEW_ROW**: Blockers when no rows match the given FY and canonical utility type.
- **MISSING_REMAINING_AMOUNT**: Blockers when the matched row lacks remaining amount.
- **INSUFFICIENT_REMAINING_AMOUNT**: Blockers when the required amount exceeds the remaining amount.
- **UTILITY_PROVIDER_MISMATCH**: Blockers when the selected utility group and the provider classification contradict.
- **PROVIDER_UNKNOWN**: Warning when provider cannot be classified.
- **AMBIGUOUS_NT_PROVIDER**: Warning when provider is only "NT" without "โทรศัพท์" or "อินเทอร์เน็ต".
- **MULTIPLE_MATCHING_ROWS**: Warning when multiple preview rows map to the same case.
- **PLACEHOLDER_MAPPING_FIELDS**: Warning when department/plan/budget are placeholders.
- **evidence object**: Added containing `source_file`, `source_sheet`, `source_hash`, `preview_row_id`, `source_row`, `match_basis`, and `ignored_warning_only_fields`.

## Backward Compatibility Notes
Original string arrays (`blockers`, `warnings`, `missing_data`) are fully preserved in exactly the same format. The API payload shape includes new properties alongside the old ones, ensuring existing consumers (like the frontend) will not break.

## Sample Readiness Object
```json
{
  "status": "blocked",
  "ready": false,
  "case": {
    "case_id": 123,
    "fiscal_year_be": 2569,
    "expense_type": "ค่าไฟฟ้า",
    "canonical_utility_type": "electricity",
    "required_amount": 1000.0
  },
  "budget_match": {
    "match_status": "matched",
    "preview_row_id": "row_123",
    "source_row": 5,
    "expense_type": "ค่าไฟฟ้า",
    "canonical_utility_type": "electricity",
    "remaining_amount": 500.0
  },
  "withholding_tax": {
    "applies": false,
    "rule_id": "UTILITY_ELECTRICITY_NO_WHT",
    "display_label": "ไม่หักภาษี ณ ที่จ่าย"
  },
  "blockers": ["required_amount > remaining_amount"],
  "warnings": [],
  "missing_data": [],
  "blocker_details": [
    {
      "code": "INSUFFICIENT_REMAINING_AMOUNT",
      "level": "blocker",
      "message": "ยอดขอเบิกมากกว่างบคงเหลือ",
      "field": "required_amount",
      "detail": {
        "required": 1000.0,
        "remaining": 500.0
      }
    }
  ],
  "warning_details": [],
  "missing_data_details": [],
  "evidence": {
    "source_file": "B_RemainedBudget.xlsx",
    "preview_row_id": "row_123",
    "source_row": 5,
    "match_basis": ["fiscal_year_be", "canonical_utility_type"],
    "ignored_warning_only_fields": ["department", "plan", "budget"]
  }
}
```

## Validation Output
```
$ python -m pytest tests/product/test_budget_preview_matcher.py -q
...........                                                              [100%]
11 passed in 0.14s

$ python -m pytest tests/product/test_budget_readiness_preview_endpoint.py -q
......                                                                   [100%]
6 passed, 2 warnings in 2.12s

$ python -m pytest tests/product/test_budget_preview_endpoint.py -q
......                                                                   [100%]
6 passed, 1 warning in 2.18s

$ python -m pytest tests/product -q
........................................................................ [ 61%]
..............................................                           [100%]
118 passed, 2 warnings in 11.35s
```

## git diff --stat
```
 src/product/services/budget_preview_matcher.py | 37 ++++++++++++++++++++++++--
 tests/product/test_budget_preview_matcher.py   | 16 ++++++++++-
 2 files changed, 50 insertions(+), 3 deletions(-)
```

## Final Status Confirmations
- **No Database changes:** Confirmed.
- **No Schema changes:** Confirmed.
- **No Config changes:** Confirmed.
- **No Frontend changes:** Confirmed.
- **No API changes:** Confirmed (returned schema is strictly additive).
- **No files staged/committed/pushed:** Confirmed.
