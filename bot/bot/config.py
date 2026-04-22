from pydantic_settings import BaseSettings
from functools import lru_cache


class BotSettings(BaseSettings):
    bot_token: str
    backend_url: str = "http://backend:8000"
    mini_app_url: str = ""
    proxy_urls: str = ""  # comma-separated socks5://user:pass@host:port entries

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()
