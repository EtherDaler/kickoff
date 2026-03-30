import aiohttp
import logging

logger = logging.getLogger(__name__)


async def notify_users(bot_token: str, telegram_ids: list[int], text: str) -> None:
    """Send a Telegram message to multiple users via Bot API."""
    if not bot_token or not telegram_ids:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        for tg_id in telegram_ids:
            try:
                async with session.post(url, json={
                    "chat_id": tg_id,
                    "text": text,
                    "parse_mode": "HTML",
                }) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.warning("TG notify failed for %s: %s", tg_id, body)
            except Exception as exc:
                logger.warning("TG notify exception for %s: %s", tg_id, exc)
