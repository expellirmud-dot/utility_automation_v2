from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/ui/templates")

@router.get("/dashboard")
async def dashboard(request: Request):
    # Call a dashboard service/viewmodel here
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": {}})
