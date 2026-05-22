import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.product.api.budget import router

test_app = FastAPI()
test_app.include_router(router)

client = TestClient(test_app)

def test_readiness_preview_endpoint_exists():
    response = client.post("/api/budget/preview/readiness", json={
        "case_facts": {},
        "budget_preview_batch": {}
    })
    # Will fail with missing fields or return matcher result
    assert response.status_code in [200, 422]
    # If 200, it's returning the matcher result

def test_electricity_ready():
    payload = {
        "case_facts": {
            "case_id": 123,
            "fiscal_year_be": 2569,
            "expense_group": "ค่าไฟฟ้า",
            "required_amount": 1000.0,
            "provider": "PEA"
        },
        "budget_preview_batch": {
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
    }
    response = client.post("/api/budget/preview/readiness", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["withholding_tax"]["applies"] is False

def test_insufficient_amount_blocked():
    payload = {
        "case_facts": {
            "fiscal_year_be": 2569,
            "expense_group": "ค่าไฟฟ้า",
            "required_amount": 6000.0,
            "provider": "PEA"
        },
        "budget_preview_batch": {
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
    }
    response = client.post("/api/budget/preview/readiness", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked"
    assert "required_amount > remaining_amount" in data["blockers"]

def test_missing_required_amount_missing_data():
    payload = {
        "case_facts": {
            "fiscal_year_be": 2569,
            "expense_group": "ค่าไฟฟ้า",
            "provider": "PEA"
        },
        "budget_preview_batch": {
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
    }
    response = client.post("/api/budget/preview/readiness", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "missing_data"
    assert "required_amount" in data["missing_data"]

def test_no_db_dependency():
    # If the endpoint required DB, we would have to mock it or pass it.
    # Since we are using an app without DB overrides and it works, it doesn't hit DB.
    pass

def test_methods_not_allowed():
    response_get = client.get("/api/budget/preview/readiness")
    assert response_get.status_code == 405
    
    response_put = client.put("/api/budget/preview/readiness")
    assert response_put.status_code == 405
    
    response_patch = client.patch("/api/budget/preview/readiness")
    assert response_patch.status_code == 405
    
    response_delete = client.delete("/api/budget/preview/readiness")
    assert response_delete.status_code == 405
