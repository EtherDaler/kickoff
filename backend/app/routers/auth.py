from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.services.telegram_auth import verify_telegram_init_data

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=UserOut)
async def auth_telegram(
    x_init_data: str = Header(..., alias="X-Init-Data"),
    db: AsyncSession = Depends(get_db),
):
    tg_data = verify_telegram_init_data(x_init_data)
    if not tg_data:
        raise HTTPException(401, "Invalid Telegram init data")

    telegram_id = tg_data["id"]
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=tg_data.get("username"),
            first_name=tg_data.get("first_name", ""),
            last_name=tg_data.get("last_name"),
            avatar_url=tg_data.get("photo_url"),
        )
        db.add(user)
        await db.flush()

    return UserOut.model_validate(user)


@router.post("/bot-register", response_model=UserOut)
async def bot_register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Used by the bot to register/update users."""
    result = await db.execute(select(User).where(User.telegram_id == data.telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=data.telegram_id,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            avatar_url=data.avatar_url,
        )
        db.add(user)
    else:
        if data.username is not None:
            user.username = data.username
        if data.first_name:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url

    await db.flush()
    return UserOut.model_validate(user)
