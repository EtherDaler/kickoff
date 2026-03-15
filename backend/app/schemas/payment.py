from datetime import datetime
from pydantic import BaseModel
from app.models.payment import PaymentStatus
from app.schemas.user import UserShort


class PaymentReceiptOut(BaseModel):
    id: int
    match_id: int
    user: UserShort
    receipt_url: str
    status: PaymentStatus
    organizer_note: str | None
    uploaded_at: datetime
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
    organizer_note: str | None = None
