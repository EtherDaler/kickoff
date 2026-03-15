import enum
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PlayerRole(str, enum.Enum):
    FORWARD = "forward"
    MIDFIELDER = "midfielder"
    DEFENDER = "defender"
    GOALKEEPER = "goalkeeper"
    REFEREE = "referee"


class FriendRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(512), nullable=True)
    roles: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    organized_matches: Mapped[list["Match"]] = relationship(  # type: ignore[name-defined]
        "Match", back_populates="organizer", foreign_keys="Match.organizer_id"
    )
    participations: Mapped[list["MatchParticipant"]] = relationship(  # type: ignore[name-defined]
        "MatchParticipant", back_populates="user"
    )
    player_stats: Mapped[list["PlayerMatchStat"]] = relationship(  # type: ignore[name-defined]
        "PlayerMatchStat", back_populates="user"
    )
    sent_friend_requests: Mapped[list["FriendRequest"]] = relationship(
        "FriendRequest", back_populates="sender", foreign_keys="FriendRequest.sender_id"
    )
    received_friend_requests: Mapped[list["FriendRequest"]] = relationship(
        "FriendRequest", back_populates="receiver", foreign_keys="FriendRequest.receiver_id"
    )

    def get_roles(self) -> list[str]:
        return [r for r in self.roles.split(",") if r]

    def set_roles(self, roles: list[str]):
        self.roles = ",".join(set(roles))


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus), default=FriendRequestStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sender: Mapped["User"] = relationship("User", back_populates="sent_friend_requests", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", back_populates="received_friend_requests", foreign_keys=[receiver_id])
