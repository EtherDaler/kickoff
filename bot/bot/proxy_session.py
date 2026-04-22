"""
Resilient SOCKS5 proxy session for aiogram.

Proxy URLs are loaded from the PROXY_URLS env variable (comma-separated).
On every TelegramNetworkError automatically rotates to the next proxy.
Proxies are tried in random order at startup, so load is spread evenly.
"""
import logging
import random
from typing import TYPE_CHECKING, Any

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.methods import TelegramMethod
    from aiogram.methods.base import TelegramType

logger = logging.getLogger(__name__)


class ResilientProxySession(AiohttpSession):
    """
    AiohttpSession that rotates between SOCKS5 proxies on TelegramNetworkError.
    Tries every proxy before giving up and re-raising the last exception.
    """

    def __init__(self, proxy_urls: list[str], **kwargs: Any) -> None:
        if not proxy_urls:
            raise ValueError("At least one proxy URL is required")

        self._proxy_urls = list(proxy_urls)
        random.shuffle(self._proxy_urls)
        self._current_idx = 0

        super().__init__(proxy=self._proxy_urls[0], **kwargs)
        logger.info("Proxy session initialised with: %s", self._active_host())

    def _active_host(self) -> str:
        # Log only host:port, never credentials
        url = str(self._proxy_urls[self._current_idx])
        return url.split("@")[-1] if "@" in url else url

    async def _rotate_proxy(self) -> None:
        """Close current aiohttp session and switch to the next proxy URL."""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
        except Exception:
            pass

        self._session = None  # type: ignore[assignment]
        self._connector = None  # type: ignore[assignment]

        self._current_idx = (self._current_idx + 1) % len(self._proxy_urls)
        self.proxy = self._proxy_urls[self._current_idx]
        logger.warning("Rotated to proxy: %s", self._active_host())

    async def make_request(
        self,
        bot: "Bot",
        method: "TelegramMethod[TelegramType]",
        *args: Any,
        **kwargs: Any,
    ) -> "TelegramType":
        last_exc: TelegramNetworkError | None = None
        attempts = len(self._proxy_urls)

        for attempt in range(attempts):
            try:
                return await super().make_request(bot, method, *args, **kwargs)
            except TelegramNetworkError as exc:
                last_exc = exc
                logger.warning(
                    "Proxy %s failed (attempt %d/%d): %s",
                    self._active_host(),
                    attempt + 1,
                    attempts,
                    exc,
                )
                if attempt < attempts - 1:
                    await self._rotate_proxy()

        raise last_exc  # type: ignore[misc]


def create_proxy_session() -> ResilientProxySession | None:
    """
    Build a ResilientProxySession from the PROXY_URLS env variable.
    Returns None if no proxies are configured (direct connection).
    """
    from bot.config import get_settings
    raw = get_settings().proxy_urls.strip()
    if not raw:
        logger.info("No PROXY_URLS configured — using direct connection")
        return None
    urls = [u.strip() for u in raw.split(",") if u.strip()]
    if not urls:
        return None
    return ResilientProxySession(proxy_urls=urls)
