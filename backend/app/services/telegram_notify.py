import httpx
import logging

logger = logging.getLogger(__name__)


async def notify_users(bot_token: str, telegram_ids: list[int], text: str) -> None:
    """Send a Telegram message to multiple users via Bot API."""
    if not bot_token or not telegram_ids:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        for tg_id in telegram_ids:
            try:
                resp = await client.post(url, json={
                    "chat_id": tg_id,
                    "text": text,
                    "parse_mode": "HTML",
                })
                if resp.status_code != 200:
                    logger.warning("TG notify failed for %s: %s", tg_id, resp.text)
            except Exception as exc:
                logger.warning("TG notify exception for %s: %s", tg_id, exc)
