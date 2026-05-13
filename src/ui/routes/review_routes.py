from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/ui/templates")


@router.get("/review")
def review_queue(request: Request):
    return templates.TemplateResponse("review_queue.html", {"request": request})
