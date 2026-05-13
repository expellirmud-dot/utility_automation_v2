# Final Dashboard Integration logic
# This file acts as the bridge for the dashboard UI to the backend services
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.ui.routes import dashboard_routes, review_routes
from src.services.observability.api.dashboard_api import router as dash_router
from src.services.control_plane.api.ops import router as ops_router
from src.ui.ops_overview_api import router as ops_overview_router
from src.services.observability.telemetry_middleware import observability_middleware

app = FastAPI(title="Governance Operations Dashboard")

app.middleware("http")(observability_middleware)
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
# Use the new dashboard template directory
templates = Jinja2Templates(directory="src/ui/dashboard/templates")

app.include_router(dash_router)
app.include_router(ops_router)
app.include_router(ops_overview_router)
app.include_router(dashboard_routes.router)
app.include_router(review_routes.router)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
