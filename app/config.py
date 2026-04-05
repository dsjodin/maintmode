from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    traefik_dynamic_dir: str = "/traefik-dynamic"
    admin_host: str = "maint.storavalla.se"
    data_dir: str = "/app/data"
    default_cert_resolver: str = "le"
    default_entrypoint: str = "websecure"
    maintmode_container_name: str = "maintmode"
    maintmode_port: int = 8010
    router_priority: int = 1000

    @property
    def sites_file(self) -> Path:
        return Path(self.data_dir) / "sites.json"

    @property
    def dynamic_dir(self) -> Path:
        return Path(self.traefik_dynamic_dir)

    model_config = {"env_prefix": ""}


settings = Settings()
