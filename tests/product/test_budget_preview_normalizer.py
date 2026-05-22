import pytest
from src.product.services.budget_preview_normalizer import BudgetPreviewNormalizer

def test_normalize_empty_batch():
    batch = BudgetPreviewNormalizer.normalize_batch([], "empty.xlsx")
    assert batch["preview_kind"] == "remained_budget_xlsx"
    assert batch["summary"]["total_rows"] == 0
    assert len(batch["rows"]) == 0

def test_normalize_standard_row():
    raw_row = {
        "source_row": 9,
        "fiscal_year_be": 2569,
        "printed_month": "พฤษภาคม",
        "municipality": "เทศบาลตำบลด่านทับตะโก",
        "work": "งานบริหารทั่วไป",
        "appropriation_category": "ค่าสาธารณูปโภค",
        "expense_type": "ค่าโทรศัพท์",
        "project": "",
        "budget_code": "00111",
        "approved_amount": 10000.0,
        "remaining_amount": 5000.0,
        "source_file": "B_RemainedBudget.xlsx",
        "source_sheet": "reportRemainBudgetXlsx"
    }
    
    batch = BudgetPreviewNormalizer.normalize_batch([raw_row], "B_RemainedBudget.xlsx", "file_hash_123")
    
    assert batch["summary"]["total_rows"] == 1
    assert batch["metadata"]["fiscal_year_be"] == 2569
    
    row = batch["rows"][0]
    
    # ID and Source Row
    assert row["source_row"] == 9
    assert row["preview_row_id"].startswith("prev_")
    
    # Placeholders
    assert row["placeholders"]["department"] == "รอข้อมูลจริง"
    assert row["placeholders"]["plan"] == "รอข้อมูลจริง"
    assert row["placeholders"]["budget"] == "รอข้อมูลจริง"
    
    # Derived - Tax
    tax = row["derived"]["withholding_tax"]
    assert tax["applies"] is True
    assert tax["rule_id"] == "UTILITY_DEFAULT_WHT"
    
    # Derived - Readiness
    readiness = row["derived"]["mapping_readiness"]
    assert readiness["db_import_status"] == "blocked_pending_confirmed_mapping"
    assert row["derived"]["db_import_safe"] is False
    
    # Evidence
    ev = row["evidence"]
    assert ev["source_file"] == "B_RemainedBudget.xlsx"
    assert ev["source_row"] == 9
    assert ev["source_hash"] is not None
    assert ev["column_evidence"]["expense_type"]["normalized_value"] == "ค่าโทรศัพท์"
    assert ev["column_evidence"]["expense_type"]["column_index"] == 3

def test_tax_derivation_rules():
    def get_tax(app_cat, exp_type):
        raw = {
            "source_row": 1,
            "appropriation_category": app_cat,
            "expense_type": exp_type
        }
        batch = BudgetPreviewNormalizer.normalize_batch([raw], "test.xlsx", "id")
        return batch["rows"][0]["derived"]["withholding_tax"]

    # Rule 1: Electricity
    tax = get_tax("ค่าสาธารณูปโภค", "ค่าไฟฟ้า")
    assert tax["applies"] is False
    assert tax["rule_id"] == "UTILITY_ELECTRICITY_NO_WHT"
    
    # Rule 2: Utility (not electricity)
    tax = get_tax("ค่าสาธารณูปโภค", "ค่าบริการไปรษณีย์")
    assert tax["applies"] is True
    assert tax["rule_id"] == "UTILITY_DEFAULT_WHT"
    
    # Rule 3: Other
    tax = get_tax("ค่าใช้สอย", "ค่าซ่อมแซม")
    assert tax["applies"] is None
    assert tax["rule_id"] == "NON_UTILITY_UNKNOWN"

def test_safe_float_handling():
    # Simulate a pandas NaN which might sneak through if not handled properly in parser, 
    # though parser should handle it, we test normalizer's safety net.
    float_nan = float('nan')
    raw_row = {
        "source_row": 2,
        "approved_amount": float_nan,
        "remaining_amount": 100.5
    }
    
    batch = BudgetPreviewNormalizer.normalize_batch([raw_row], "test.xlsx", "id")
    extracted = batch["rows"][0]["extracted"]
    
    assert extracted["approved_amount"] is None
    assert extracted["remaining_amount"] == 100.5
