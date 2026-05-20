import pytest
from datetime import date
from src.product.services.fiscal_year import get_thai_fiscal_year

def test_fiscal_year_before_october():
    # September 30, 2025 -> should be FY 2025 + 543 = 2568
    assert get_thai_fiscal_year(date(2025, 9, 30)) == 2568

def test_fiscal_year_on_october_first():
    # October 1, 2025 -> should be FY 2026 + 543 = 2569
    assert get_thai_fiscal_year(date(2025, 10, 1)) == 2569

def test_fiscal_year_in_december():
    # December 31, 2025 -> should be FY 2026 + 543 = 2569
    assert get_thai_fiscal_year(date(2025, 12, 31)) == 2569

def test_fiscal_year_in_january():
    # January 1, 2026 -> should be FY 2026 + 543 = 2569
    assert get_thai_fiscal_year(date(2026, 1, 1)) == 2569

def test_fiscal_year_in_september_next_year():
    # September 30, 2026 -> should be FY 2026 + 543 = 2569
    assert get_thai_fiscal_year(date(2026, 9, 30)) == 2569
