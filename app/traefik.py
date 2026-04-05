import os
import re
import yaml
from pathlib import Path

from app.config import settings


def _sanitize_name(hostname: str) -> str:
    """Convert hostname to a safe Traefik resource name."""
    return re.sub(r"[^a-z0-9]", "-", hostname.lower()).strip("-")


def _maint_filename(hostname: str) -> str:
    return f"maint-{_sanitize_name(hostname)}.yaml"


def _service_filename() -> str:
    return "_maintenance-service.yaml"


def _errors_filename() -> str:
    return "_errors-middleware.yaml"


def ensure_shared_configs() -> None:
    """Write the shared maintenance service and error middleware configs."""
    _write_service_config()
    _write_errors_config()


def _write_service_config() -> None:
    """Write the shared maintenance-backend service definition."""
    config = {
        "http": {
            "services": {
                "maintenance-backend": {
                    "loadBalancer": {
                        "servers": [
                            {"url": f"http://{settings.maintmode_container_name}:{settings.maintmode_port}"}
                        ]
                    }
                }
            }
        }
    }
    _atomic_write(settings.dynamic_dir / _service_filename(), config)


def _write_errors_config() -> None:
    """Write the custom-errors middleware for services to opt into."""
    config = {
        "http": {
            "middlewares": {
                "custom-errors": {
                    "errors": {
                        "status": ["400-599"],
                        "service": "maintenance-backend",
                        "query": "/error/{status}",
                    }
                }
            }
        }
    }
    _atomic_write(settings.dynamic_dir / _errors_filename(), config)


def write_maintenance_router(hostname: str) -> None:
    """Create a high-priority Traefik router that sends traffic to maintenance backend."""
    safe_name = _sanitize_name(hostname)
    router_name = f"maint-{safe_name}"
    middleware_name = f"maint-headers-{safe_name}"

    config = {
        "http": {
            "routers": {
                router_name: {
                    "rule": f"Host(`{hostname}`)",
                    "entryPoints": [settings.default_entrypoint],
                    "service": "maintenance-backend",
                    "priority": settings.router_priority,
                    "tls": {
                        "certResolver": settings.default_cert_resolver,
                    },
                    "middlewares": [middleware_name],
                }
            },
            "middlewares": {
                middleware_name: {
                    "headers": {
                        "customResponseHeaders": {
                            "Retry-After": "3600",
                        }
                    }
                }
            },
        }
    }
    _atomic_write(settings.dynamic_dir / _maint_filename(hostname), config)


def remove_maintenance_router(hostname: str) -> None:
    """Delete the maintenance router config file."""
    path = settings.dynamic_dir / _maint_filename(hostname)
    if path.exists():
        path.unlink()


def has_maintenance_router(hostname: str) -> bool:
    """Check if a maintenance router file exists for this hostname."""
    return (settings.dynamic_dir / _maint_filename(hostname)).exists()


def list_maintenance_files() -> list[str]:
    """List all maint-*.yaml files and extract hostnames."""
    hostnames = []
    for f in settings.dynamic_dir.glob("maint-*.yaml"):
        if f.name.startswith("maint-") and not f.name.startswith("_"):
            try:
                data = yaml.safe_load(f.read_text())
                routers = data.get("http", {}).get("routers", {})
                for router in routers.values():
                    rule = router.get("rule", "")
                    match = re.search(r"Host\(`([^`]+)`\)", rule)
                    if match:
                        hostnames.append(match.group(1))
            except Exception:
                continue
    return hostnames


def _atomic_write(path: Path, config: dict) -> None:
    """Write YAML config atomically using a temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    os.rename(str(tmp), str(path))
