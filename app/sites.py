import json
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings
from app.models import Site, SiteRegistry, SiteCreate, MaintenanceToggleRequest

_registry: SiteRegistry = SiteRegistry()


def _save() -> None:
    path = settings.sites_file
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _registry.model_dump(mode="json")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.rename(path)


def load() -> None:
    global _registry
    path = settings.sites_file
    if path.exists():
        data = json.loads(path.read_text())
        _registry = SiteRegistry.model_validate(data)
    else:
        _registry = SiteRegistry()
        _save()


def list_sites() -> list[Site]:
    return list(_registry.sites.values())


def get_site(hostname: str) -> Site | None:
    return _registry.sites.get(hostname)


def add_site(req: SiteCreate) -> Site:
    if req.hostname in _registry.sites:
        raise ValueError(f"Site {req.hostname} already exists")
    site = Site(hostname=req.hostname, name=req.name)
    _registry.sites[req.hostname] = site
    _save()
    return site


def remove_site(hostname: str) -> None:
    if hostname not in _registry.sites:
        raise KeyError(f"Site {hostname} not found")
    del _registry.sites[hostname]
    _save()


def enable_maintenance(hostname: str, req: MaintenanceToggleRequest) -> Site:
    site = _registry.sites.get(hostname)
    if site is None:
        raise KeyError(f"Site {hostname} not found")
    site.maintenance = True
    site.maintenance_message = req.message or "We're performing scheduled maintenance. We'll be back shortly."
    site.estimated_return = req.estimated_return
    site.enabled_at = datetime.now(timezone.utc)
    _save()
    return site


def disable_maintenance(hostname: str) -> Site:
    site = _registry.sites.get(hostname)
    if site is None:
        raise KeyError(f"Site {hostname} not found")
    site.maintenance = False
    site.maintenance_message = None
    site.estimated_return = None
    site.enabled_at = None
    _save()
    return site
