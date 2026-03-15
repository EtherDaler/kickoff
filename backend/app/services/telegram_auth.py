import hashlib
import hmac
import json
from urllib.parse import unquote
from app.config import get_settings


def verify_telegram_init_data(init_data: str) -> dict | None:
    """Verify Telegram Mini App init data and return parsed user data."""
    settings = get_settings()
    try:
        parsed = dict(item.split("=", 1) for item in init_data.split("&"))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={unquote(v)}" for k, v in sorted(parsed.items())
        )
        secret_key = hmac.new(key=b"WebAppData", msg=settings.bot_token.encode(), digestmod=hashlib.sha256).digest()
        expected_hash = hmac.new(key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            return None

        user_data = parsed.get("user")
        if not user_data:
            return None

        return json.loads(unquote(user_data))
    except Exception:
        return None
