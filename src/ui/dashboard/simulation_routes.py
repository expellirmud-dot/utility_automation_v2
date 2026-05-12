from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from src.services.governance.simulation.simulation_api import _simulation_reports
from typing import List

router = APIRouter(prefix="/simulation", tags=["Dashboard"])
templates = Jinja2Templates(directory="src/ui/dashboard/templates")

@router.get("/dashboard")
async def dashboard(request: Request):
    # Deterministic sorting
    sorted_reports = sorted(_simulation_reports.items(), key=lambda x: x[0])
    
    # Normalize for UI
    normalized = []
    for h, r in sorted_reports:
        normalized.append({
            "hash": h,
            "status": r.get("impact", {}).get("status", "unknown"),
            "manual_review_required": r.get("manual_review_required", False),
            "warning_count": len(r.get("warnings", []))
        })
        
    return templates.TemplateResponse(
        request=request,
        name="simulation_dashboard.html",
        context={"reports": normalized}
    )

@router.get("/detail/{report_hash}")
async def detail(request: Request, report_hash: str):
    report = _simulation_reports.get(report_hash)
    if not report:
        return {"error": "Report not found"}
        
    normalized = {
        "simulation_hash": report.get("simulation_hash", report_hash),
        "status": report.get("impact", {}).get("status", "unknown"),
        "manual_review_required": report.get("manual_review_required", False),
        "warnings": report.get("warnings", []),
        "warning_count": len(report.get("warnings", [])),
        "confidence_assessment": report.get("confidence_assessment", "N/A")
    }
    
    return templates.TemplateResponse(
        request=request,
        name="simulation_detail.html",
        context={"report": normalized}
    )
