import pytest
from src.product.services.budget_preview_matcher import BudgetPreviewMatcher

def test_electricity_ready_and_wht_false():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "required_amount": 1000.0,
        "provider": "PEA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "ready"
    assert res["ready"] is True
    assert res["withholding_tax"]["applies"] is False
    assert res["withholding_tax"]["rule_id"] == "UTILITY_ELECTRICITY_NO_WHT"

def test_phone_ready_and_wht_true():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าโทรศัพท์",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าโทรศัพท์",
        "required_amount": 1000.0,
        "provider": "NT โทรศัพท์"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "ready"
    assert res["withholding_tax"]["applies"] is True
    assert res["withholding_tax"]["rule_id"] == "UTILITY_DEFAULT_WHT"

def test_internet_ready_and_wht_true():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าอินเทอร์เน็ต",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าอินเทอร์เน็ต",
        "required_amount": 1000.0,
        "provider": "NT อินเทอร์เน็ต"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "ready"
    assert res["withholding_tax"]["applies"] is True

def test_water_ready_and_wht_true():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าน้ำประปา",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าน้ำประปา",
        "required_amount": 1000.0,
        "provider": "PWA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "ready"
    assert res["withholding_tax"]["applies"] is True

def test_nt_alone_returns_warning():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าโทรศัพท์",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าโทรศัพท์",
        "required_amount": 1000.0,
        "provider": "NT"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "warning"
    assert "NT ambiguous" in res["warnings"]

def test_selected_electricity_but_provider_is_phone():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "required_amount": 1000.0,
        "provider": "NT โทรศัพท์"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "blocked"
    assert "selected electricity but provider/bill clearly phone/internet/water" in res["blockers"]

def test_insufficient_remaining_amount():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 500.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "required_amount": 1000.0,
        "provider": "PEA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "blocked"
    assert "required_amount > remaining_amount" in res["blockers"]

def test_no_matching_row():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าโทรศัพท์",
                    "remaining_amount": 500.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "required_amount": 1000.0,
        "provider": "PEA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "blocked"
    assert "no matching preview row for fiscal year + utility category" in res["blockers"]

def test_missing_required_amount():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 5000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "provider": "PEA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "missing_data"
    assert "required_amount" in res["missing_data"]

def test_multiple_matching_rows():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 5000.0
                }
            },
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 2000.0
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "required_amount": 1000.0,
        "provider": "PEA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "warning"
    assert "multiple matching rows" in res["warnings"]

def test_placeholder_department():
    batch = {
        "metadata": {"fiscal_year_be": 2569},
        "rows": [
            {
                "extracted": {
                    "expense_type": "ค่าไฟฟ้า",
                    "remaining_amount": 5000.0
                },
                "placeholders": {
                    "department": "รอข้อมูลจริง"
                }
            }
        ]
    }
    case_facts = {
        "fiscal_year_be": 2569,
        "expense_group": "ค่าไฟฟ้า",
        "required_amount": 1000.0,
        "provider": "PEA"
    }
    res = BudgetPreviewMatcher.match_case_to_preview(case_facts, batch)
    assert res["status"] == "warning"
    assert 'department/plan/budget are "รอข้อมูลจริง"' in res["warnings"]
