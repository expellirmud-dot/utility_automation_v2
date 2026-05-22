# PRODUCT-005C1 Read-First Report

## Overview
We need to implement a `BudgetPreviewMatcher` that acts on in-memory case facts and an in-memory `BudgetPreviewBatch` object to find matching budget rows.

## Constraints
- Pure functions only.
- In-memory case facts and in-memory `BudgetPreviewBatch` object.
- Utility categories must remain separate: electricity, phone, internet, water, unknown. Do not merge phone and internet into telecom.
- No DB access, no API changes, no frontend changes.

## Implementation Plan
1. Create `src/product/services/budget_preview_matcher.py` with `BudgetPreviewMatcher` class.
2. Implement `match_utility(category: str, batch: dict) -> list[dict]` or similar pure function.
3. Create `tests/product/test_budget_preview_matcher.py` with unit tests for each category.
4. Categories mapping:
   - electricity -> `ค่าไฟฟ้า`
   - phone -> `ค่าโทรศัพท์`
   - internet -> `ค่าบริการสื่อสารและโทรคมนาคม` or similar (must check what is typically internet)
   - water -> `ค่าน้ำประปา ค่าน้ำบาดาล`
   - unknown -> anything else
