from fastapi import APIRouter

from src.services.dashboard.projection_service import DashboardProjectionService

router = APIRouter(prefix="/dashboard", tags=["Dashboard Projection"])
service = DashboardProjectionService()


@router.get("/projection")
async def get_dashboard_projection():
    return service.projection()
