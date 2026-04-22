from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    bot_token: str
    mini_app_url: str = ""
    database_url: str
    secret_key: str  # required — no insecure default
    allowed_origins: str = "*"
    upload_dir: str = "/app/uploads"
    dev_mode: bool = False  # set DEV_MODE=true only for local development

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
