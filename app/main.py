import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app import sites as site_store
from app import traefik
from app.routers import api, admin, errors

logger = logging.getLogger("maintmode")

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load site registry and ensure shared Traefik configs
    site_store.load()
    try:
        traefik.ensure_shared_configs()
        _reconcile_state()
    except Exception:
        logger.warning("Failed to write Traefik configs on startup — check volume mount", exc_info=True)
    yield


def _reconcile_state() -> None:
    """Ensure Traefik files match persisted site state on startup."""
    for site in site_store.list_sites():
        has_file = traefik.has_maintenance_router(site.hostname)
        if site.maintenance and not has_file:
            traefik.write_maintenance_router(site.hostname)
        elif not site.maintenance and has_file:
            traefik.remove_maintenance_router(site.hostname)


app = FastAPI(title="Maintmode", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register routers
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(errors.router)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.middleware("http")
async def route_by_host(request: Request, call_next):
    """
    Host-based routing:
    - Admin host -> admin UI + API (pass through to FastAPI routes)
    - Any other host -> serve maintenance page
    """
    host = request.headers.get("host", "").split(":")[0].strip().lower()
    logger.debug("Request host=%r path=%r admin_host=%r", host, request.url.path, settings.admin_host)

    if host == settings.admin_host:
        return await call_next(request)

    # For non-admin hosts, check if this is an error page request
    if request.url.path.startswith("/error/"):
        return await call_next(request)

    # Serve maintenance page for this host
    site = site_store.get_site(host)
    site_name = site.name if site else host
    message = (site.maintenance_message if site else None) or "We're performing scheduled maintenance. We'll be back shortly."
    estimated_return = site.estimated_return if site else None

    return templates.TemplateResponse(
        "maintenance/maintenance.html",
        {
            "request": request,
            "site_name": site_name,
            "message": message,
            "estimated_return": estimated_return,
        },
        status_code=503,
        headers={"Retry-After": "3600"},
    )
