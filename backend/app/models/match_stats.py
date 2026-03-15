from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, func, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MatchStats(Base):
    __tablename__ = "match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), unique=True, nullable=False)
    team1_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    team2_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="stats")  # type: ignore[name-defined]
    player_stats: Mapped[list["PlayerMatchStat"]] = relationship(
        "PlayerMatchStat", back_populates="match_stats", cascade="all, delete-orphan"
    )


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_stats_id: Mapped[int] = mapped_column(Integer, ForeignKey("match_stats.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fouls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_injured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_referee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    match_stats: Mapped["MatchStats"] = relationship("MatchStats", back_populates="player_stats")
    user: Mapped["User"] = relationship("User", back_populates="player_stats")  # type: ignore[name-defined]
