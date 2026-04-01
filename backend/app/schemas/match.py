from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.match import MatchStatus, MatchVisibility
from app.models.match_participant import ParticipantRole, ParticipantStatus
from app.schemas.user import UserShort


def _strip_tz(v: datetime | None) -> datetime | None:
    """Remove timezone info so the value is compatible with TIMESTAMP WITHOUT TIME ZONE."""
    if isinstance(v, datetime) and v.tzinfo is not None:
        return v.replace(tzinfo=None)
    return v


class MatchRepeat(BaseModel):
    match_date: datetime

    @field_validator("match_date", mode="after")
    @classmethod
    def naive_match_date(cls, v: datetime) -> datetime:
        return _strip_tz(v)


class MatchCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=128)
    address: str = Field(..., min_length=3, max_length=256)
    latitude: float | None = None
    longitude: float | None = None
    match_date: datetime
    max_players: int = Field(10, ge=2, le=50)
    price_per_player: float = Field(0.0, ge=0)
    description: str | None = None
    visibility: MatchVisibility = MatchVisibility.PUBLIC
    is_paid: bool = False
    requires_referee: bool = False
    invited_user_ids: list[int] = []

    @field_validator("match_date", mode="after")
    @classmethod
    def naive_match_date(cls, v: datetime) -> datetime:
        return _strip_tz(v)


class MatchUpdate(BaseModel):
    title: str | None = None
    address: str | None = None
    match_date: datetime | None = None
    max_players: int | None = Field(None, ge=2, le=50)
    price_per_player: float | None = Field(None, ge=0)
    description: str | None = None
    visibility: MatchVisibility | None = None
    status: MatchStatus | None = None
    is_paid: bool | None = None

    @field_validator("match_date", mode="after")
    @classmethod
    def naive_match_date(cls, v: datetime | None) -> datetime | None:
        return _strip_tz(v)


class ParticipantOut(BaseModel):
    id: int
    user: UserShort
    role: ParticipantRole
    status: ParticipantStatus
    payment_confirmed: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class MatchShort(BaseModel):
    id: int
    title: str
    address: str
    match_date: datetime
    max_players: int
    price_per_player: float
    visibility: MatchVisibility
    status: MatchStatus
    is_paid: bool
    organizer: UserShort
    participants_count: int = 0
    confirmed_count: int = 0

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    id: int
    title: str
    address: str
    latitude: float | None
    longitude: float | None
    match_date: datetime
    max_players: int
    price_per_player: float
    description: str | None
    visibility: MatchVisibility
    status: MatchStatus
    is_paid: bool
    requires_referee: bool
    organizer: UserShort
    participants: list[ParticipantOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PlayerMatchStatCreate(BaseModel):
    user_id: int
    goals: int = Field(0, ge=0)
    assists: int = Field(0, ge=0)
    yellow_cards: int = Field(0, ge=0, le=2)
    red_cards: int = Field(0, ge=0, le=1)
    fouls: int = Field(0, ge=0)
    is_injured: bool = False
    is_referee: bool = False
    notes: str | None = None


class MatchStatsCreate(BaseModel):
    team1_score: int = Field(0, ge=0)
    team2_score: int = Field(0, ge=0)
    player_stats: list[PlayerMatchStatCreate] = []


class PlayerMatchStatOut(BaseModel):
    id: int
    user: UserShort
    goals: int
    assists: int
    yellow_cards: int
    red_cards: int
    fouls: int
    is_injured: bool
    is_referee: bool
    notes: str | None

    model_config = {"from_attributes": True}


class MatchStatsOut(BaseModel):
    id: int
    match_id: int
    team1_score: int
    team2_score: int
    player_stats: list[PlayerMatchStatOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}
