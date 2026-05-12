from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.ui.routes import dashboard_routes, review_routes
from src.services.observability.api.dashboard_api import router as dash_router
from src.services.control_plane.api.ops import router as ops_router
from src.services.observability.telemetry_middleware import observability_middleware

app = FastAPI(title="Utility Automation V2 - Review Dashboard")

app.middleware("http")(observability_middleware)
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
templates = Jinja2Templates(directory="src/ui/templates")

app.include_router(dashboard_routes.router)
app.include_router(review_routes.router)
app.include_router(dash_router)
app.include_router(ops_router)

@app.get("/")
async def root():
    return templates.TemplateResponse("index.html", {"request": Request}) # Redirect to dashboard
