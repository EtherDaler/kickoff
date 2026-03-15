from datetime import datetime
from pydantic import BaseModel, Field, field_validator


def _parse_roles(v) -> list[str]:
    """Convert comma-separated string from DB to list, or pass through if already a list."""
    if isinstance(v, str):
        return [r.strip() for r in v.split(",") if r.strip()]
    if isinstance(v, list):
        return v
    return []


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str
    last_name: str | None = None
    avatar_url: str | None = None


class UserUpdate(BaseModel):
    age: int | None = Field(None, ge=5, le=100)
    city: str | None = None
    bio: str | None = None
    roles: list[str] | None = None


class UserShort(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    avatar_url: str | None
    roles: list[str] = []

    model_config = {"from_attributes": True}

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, v):
        return _parse_roles(v)


class UserStats(BaseModel):
    total_matches: int = 0
    total_goals: int = 0
    total_assists: int = 0
    total_yellow_cards: int = 0
    total_red_cards: int = 0
    total_fouls: int = 0
    referee_matches: int = 0
    injuries: int = 0


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    avatar_url: str | None
    age: int | None
    city: str | None
    bio: str | None
    roles: list[str] = []
    created_at: datetime
    stats: UserStats | None = None

    model_config = {"from_attributes": True}

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, v):
        return _parse_roles(v)


class FriendRequestCreate(BaseModel):
    receiver_telegram_id: int


class FriendRequestOut(BaseModel):
    id: int
    sender: UserShort
    receiver: UserShort
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
