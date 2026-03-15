import aiohttp
from bot.config import get_settings

settings = get_settings()


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def register_user(self, telegram_id: int, username: str | None, first_name: str, last_name: str | None = None, avatar_url: str | None = None) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth/bot-register",
                json={
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "avatar_url": avatar_url,
                }
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def get_profile(self, telegram_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/users/me",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def update_profile(self, telegram_id: int, data: dict) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/users/me",
                json=data,
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def search_users(self, telegram_id: int, query: str) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/users/search",
                params={"q": query},
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def send_friend_request(self, telegram_id: int, receiver_telegram_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/users/friends/request",
                json={"receiver_telegram_id": receiver_telegram_id},
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def get_friend_requests(self, telegram_id: int) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/users/friends/requests",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def accept_friend_request(self, telegram_id: int, request_id: int) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/users/friends/requests/{request_id}/accept",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                return resp.status == 200

    async def get_matches(self, telegram_id: int, mine: bool = False, status: str | None = None) -> list[dict]:
        params: dict = {}
        if mine:
            params["mine"] = "true"
        if status:
            params["status"] = status
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/matches",
                params=params,
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def get_match(self, telegram_id: int, match_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/matches/{match_id}",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def search_matches(self, telegram_id: int, query: str) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/matches/search",
                params={"q": query},
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def join_match(self, telegram_id: int, match_id: int, as_referee: bool = False) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/matches/{match_id}/join",
                params={"as_referee": str(as_referee).lower()},
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                text = await resp.text()
                return {"error": text}

    async def leave_match(self, telegram_id: int, match_id: int) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/matches/{match_id}/leave",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                return resp.status == 200

    async def upload_receipt(self, telegram_id: int, match_id: int, file_bytes: bytes, filename: str) -> dict | None:
        data = aiohttp.FormData()
        data.add_field("file", file_bytes, filename=filename, content_type="image/jpeg")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/matches/{match_id}/upload-receipt",
                data=data,
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def get_friends(self, telegram_id: int) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/users/friends/list",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []

    async def accept_invite(self, telegram_id: int, match_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/matches/{match_id}/accept-invite",
                headers=self._bot_auth_header(telegram_id),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    def _bot_auth_header(self, telegram_id: int) -> dict:
        """Generate a special bot auth header that bypasses init data validation."""
        return {"X-Bot-Auth": str(telegram_id)}
