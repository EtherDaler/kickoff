"""
Resilient SOCKS5 proxy session for aiogram.

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

# SOCKS5 proxies in format: socks5://user:password@host:port
_PROXY_URLS: list[str] = [
    "socks5://proxy_user:JrMwCNHfKxF3HpeQ@134.122.120.67:30130",
    "socks5://proxy_user:3NsIvOTPeyJSnmcL@185.237.165.81:43101",
]


class ResilientProxySession(AiohttpSession):
    """
    AiohttpSession that rotates between SOCKS5 proxies on TelegramNetworkError.
    Tries every proxy before giving up and re-raising the last exception.
    """

    def __init__(self, proxy_urls: list[str], **kwargs: Any) -> None:
        if not proxy_urls:
            raise ValueError("At least one proxy URL is required")

        self._proxy_urls = list(proxy_urls)
        random.shuffle(self._proxy_urls)  # Random starting proxy on each restart
        self._current_idx = 0

        super().__init__(proxy=self._proxy_urls[0], **kwargs)
        logger.info("Proxy session initialised with: %s", self._active_host())

    def _active_host(self) -> str:
        return str(self._proxy_urls[self._current_idx]).split("@")[-1]

    async def _rotate_proxy(self) -> None:
        """Close current aiohttp session and switch to the next proxy URL."""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
        except Exception:
            pass

        # Reset session and connector so create_session() rebuilds them
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


def create_proxy_session() -> ResilientProxySession:
    return ResilientProxySession(proxy_urls=_PROXY_URLS)
