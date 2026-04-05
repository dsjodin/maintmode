from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

ERROR_MESSAGES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Page Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


@router.get("/error/{status_code}", response_class=HTMLResponse)
async def error_page(request: Request, status_code: int) -> HTMLResponse:
    message = ERROR_MESSAGES.get(status_code, "Something went wrong")
    return templates.TemplateResponse(
        request,
        "errors/error.html",
        context={
            "status_code": status_code,
            "message": message,
        },
        status_code=status_code,
    )
