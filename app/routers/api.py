from fastapi import APIRouter, HTTPException
from app import sites as site_store
from app import traefik
from app.models import SiteCreate, MaintenanceToggleRequest, Site

router = APIRouter(prefix="/api/v1")


@router.get("/sites")
def list_sites() -> list[Site]:
    return site_store.list_sites()


@router.get("/sites/{hostname}")
def get_site(hostname: str) -> Site:
    site = site_store.get_site(hostname)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post("/sites", status_code=201)
def create_site(req: SiteCreate) -> Site:
    try:
        return site_store.add_site(req)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/sites/{hostname}", status_code=204)
def delete_site(hostname: str) -> None:
    try:
        # Disable maintenance first if active
        site = site_store.get_site(hostname)
        if site and site.maintenance:
            traefik.remove_maintenance_router(hostname)
        site_store.remove_site(hostname)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sites/{hostname}/maintenance")
def enable_maintenance(hostname: str, req: MaintenanceToggleRequest | None = None) -> Site:
    if req is None:
        req = MaintenanceToggleRequest()
    try:
        site = site_store.enable_maintenance(hostname, req)
        traefik.write_maintenance_router(hostname)
        return site
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/sites/{hostname}/maintenance")
def disable_maintenance(hostname: str) -> Site:
    try:
        site = site_store.disable_maintenance(hostname)
        traefik.remove_maintenance_router(hostname)
        return site
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
