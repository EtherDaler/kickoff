import enum
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Boolean, Numeric, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MatchStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class MatchVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    match_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    price_per_player: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[MatchVisibility] = mapped_column(
        Enum(MatchVisibility), default=MatchVisibility.PUBLIC, nullable=False
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), default=MatchStatus.UPCOMING, nullable=False
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_referee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    organizer: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="organized_matches", foreign_keys=[organizer_id]
    )
    participants: Mapped[list["MatchParticipant"]] = relationship(  # type: ignore[name-defined]
        "MatchParticipant", back_populates="match", cascade="all, delete-orphan"
    )
    stats: Mapped["MatchStats | None"] = relationship(  # type: ignore[name-defined]
        "MatchStats", back_populates="match", uselist=False, cascade="all, delete-orphan"
    )
    payments: Mapped[list["PaymentReceipt"]] = relationship(  # type: ignore[name-defined]
        "PaymentReceipt", back_populates="match", cascade="all, delete-orphan"
    )
