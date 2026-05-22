import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.product.api.budget import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_preview_remained_budget_missing_file(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    
    response = client.get("/api/budget/preview/remained-budget")
    assert response.status_code == 404
    assert response.json()["detail"] == "Preview source file not found: B_RemainedBudget.xlsx"

def test_preview_remained_budget_method_not_allowed():
    # POST should not be allowed
    response = client.post("/api/budget/preview/remained-budget")
    assert response.status_code == 405
    
    # PUT should not be allowed
    response = client.put("/api/budget/preview/remained-budget")
    assert response.status_code == 405
    
    # PATCH should not be allowed
    response = client.patch("/api/budget/preview/remained-budget")
    assert response.status_code == 405
    
    # DELETE should not be allowed
    response = client.delete("/api/budget/preview/remained-budget")
    assert response.status_code == 405

def test_preview_remained_budget_success(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    
    class MockFile:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def read(self): return b"dummy_content"
        
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: MockFile())
    
    raw_rows = [{
        "source_row": 9,
        "work": "งานบริหารทั่วไป",
        "appropriation_category": "ค่าสาธารณูปโภค",
        "expense_type": "ค่าโทรศัพท์",
        "project": "",
        "budget_code": "00111",
        "approved_amount": 10000.0,
        "remaining_amount": 5000.0,
        "source_file": "B_RemainedBudget.xlsx",
        "source_sheet": "reportRemainBudgetXlsx"
    }]
    
    monkeypatch.setattr(
        "src.product.services.remained_budget_parser.RemainedBudgetParser.parse_preview",
        lambda content, file_path: raw_rows
    )
    
    response = client.get("/api/budget/preview/remained-budget")
    assert response.status_code == 200
    
    data = response.json()
    assert "preview_kind" in data
    assert data["preview_kind"] == "remained_budget_xlsx"
    assert "rows" in data
    assert len(data["rows"]) == 1
    
    row = data["rows"][0]
    assert row["derived"]["db_import_safe"] is False
    assert row["placeholders"]["department"] == "รอข้อมูลจริง"
    assert row["extracted"]["expense_type"] == "ค่าโทรศัพท์"
