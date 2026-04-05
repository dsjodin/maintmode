from pydantic import BaseModel, field_validator
from datetime import datetime
import re


class SiteCreate(BaseModel):
    hostname: str
    name: str

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)*$", v):
            raise ValueError("Invalid hostname")
        return v


class MaintenanceToggleRequest(BaseModel):
    message: str | None = None
    estimated_return: str | None = None


class Site(BaseModel):
    hostname: str
    name: str
    maintenance: bool = False
    maintenance_message: str | None = None
    estimated_return: str | None = None
    enabled_at: datetime | None = None


class SiteRegistry(BaseModel):
    sites: dict[str, Site] = {}
