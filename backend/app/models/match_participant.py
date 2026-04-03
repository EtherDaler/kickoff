import enum
from datetime import datetime
from sqlalchemy import Integer, DateTime, Enum, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ParticipantRole(str, enum.Enum):
    PLAYER = "player"
    REFEREE = "referee"


class ParticipantStatus(str, enum.Enum):
    INVITED = "invited"
    PENDING_PAYMENT = "pending_payment"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(ParticipantRole), default=ParticipantRole.PLAYER, nullable=False
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus), default=ParticipantStatus.PENDING_PAYMENT, nullable=False
    )
    payment_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_co_organizer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="participants")  # type: ignore[name-defined]
    user: Mapped["User"] = relationship("User", back_populates="participations")  # type: ignore[name-defined]
    payment: Mapped["PaymentReceipt | None"] = relationship(  # type: ignore[name-defined]
        "PaymentReceipt",
        primaryjoin="and_(MatchParticipant.match_id == PaymentReceipt.match_id, MatchParticipant.user_id == PaymentReceipt.user_id)",
        foreign_keys="[PaymentReceipt.match_id, PaymentReceipt.user_id]",
        viewonly=True,
        uselist=False,
    )
