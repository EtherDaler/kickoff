from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer, cast, delete
from app.database import get_db
from app.models.user import User, FriendRequest, FriendRequestStatus
from app.models.match_stats import PlayerMatchStat
from app.schemas.user import UserOut, UserUpdate, UserShort, FriendRequestOut, FriendRequestCreate, UserStats
from app.services.telegram_auth import verify_telegram_init_data
from app.services.telegram_notify import notify_users
from app.config import get_settings

router = APIRouter(prefix="/users", tags=["users"])


async def get_current_user(
    x_init_data: str | None = Header(None, alias="X-Init-Data"),
    x_bot_auth: str | None = Header(None, alias="X-Bot-Auth"),
    db: AsyncSession = Depends(get_db),
) -> User:
    telegram_id: int | None = None

    settings = get_settings()
    if x_bot_auth and x_bot_auth.isdigit() and settings.dev_mode:
        # X-Bot-Auth is only accepted when DEV_MODE=true — never in production
        telegram_id = int(x_bot_auth)
    elif x_init_data:
        tg_data = verify_telegram_init_data(x_init_data)
        if tg_data:
            telegram_id = tg_data["id"]

    if not telegram_id:
        raise HTTPException(401, "Unauthorized")

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found. Please authenticate first.")
    return user


async def get_user_stats(user_id: int, db: AsyncSession) -> UserStats:
    stats_result = await db.execute(
        select(
            func.count(PlayerMatchStat.id).label("total_matches"),
            func.coalesce(func.sum(PlayerMatchStat.goals), 0).label("total_goals"),
            func.coalesce(func.sum(PlayerMatchStat.assists), 0).label("total_assists"),
            func.coalesce(func.sum(PlayerMatchStat.yellow_cards), 0).label("total_yellow_cards"),
            func.coalesce(func.sum(PlayerMatchStat.red_cards), 0).label("total_red_cards"),
            func.coalesce(func.sum(PlayerMatchStat.fouls), 0).label("total_fouls"),
            func.coalesce(func.sum(cast(PlayerMatchStat.is_injured, Integer)), 0).label("injuries"),
        ).where(PlayerMatchStat.user_id == user_id, PlayerMatchStat.is_referee == False)
    )
    row = stats_result.first()
    referee_result = await db.execute(
        select(func.count(PlayerMatchStat.id)).where(
            PlayerMatchStat.user_id == user_id,
            PlayerMatchStat.is_referee == True,
        )
    )
    referee_count = referee_result.scalar() or 0
    if row:
        return UserStats(
            total_matches=row.total_matches or 0,
            total_goals=row.total_goals or 0,
            total_assists=row.total_assists or 0,
            total_yellow_cards=row.total_yellow_cards or 0,
            total_red_cards=row.total_red_cards or 0,
            total_fouls=row.total_fouls or 0,
            referee_matches=referee_count,
            injuries=row.injuries or 0,
        )
    return UserStats(referee_matches=referee_count)


def _build_friend_req_out(req: FriendRequest, sender: User, receiver: User) -> FriendRequestOut:
    return FriendRequestOut(
        id=req.id,
        sender=UserShort.model_validate(sender),
        receiver=UserShort.model_validate(receiver),
        status=req.status,
        created_at=req.created_at,
    )


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    out = UserOut.model_validate(current_user)
    out.stats = await get_user_stats(current_user.id, db)
    return out


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.age is not None:
        current_user.age = data.age
    if data.city is not None:
        current_user.city = data.city
    if data.bio is not None:
        current_user.bio = data.bio
    if data.roles is not None:
        current_user.set_roles(data.roles)
    await db.flush()
    out = UserOut.model_validate(current_user)
    out.stats = await get_user_stats(current_user.id, db)
    return out


@router.get("/search", response_model=list[UserShort])
async def search_users(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            (User.username.ilike(f"%{q}%")) | (User.first_name.ilike(f"%{q}%")),
            User.id != current_user.id,
        ).limit(20)
    )
    return [UserShort.model_validate(u) for u in result.scalars().all()]


@router.get("/friends/requests", response_model=list[FriendRequestOut])
async def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.receiver_id == current_user.id,
            FriendRequest.status == FriendRequestStatus.PENDING,
        )
    )
    out = []
    for req in result.scalars().all():
        sender = await db.get(User, req.sender_id)
        receiver = await db.get(User, req.receiver_id)
        if sender and receiver:
            out.append(_build_friend_req_out(req, sender, receiver))
    return out


@router.get("/friends/list", response_model=list[UserShort])
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            (FriendRequest.sender_id == current_user.id) | (FriendRequest.receiver_id == current_user.id),
            FriendRequest.status == FriendRequestStatus.ACCEPTED,
        )
    )
    friend_ids = [
        req.receiver_id if req.sender_id == current_user.id else req.sender_id
        for req in result.scalars().all()
    ]
    friends = []
    for fid in friend_ids:
        u = await db.get(User, fid)
        if u:
            friends.append(UserShort.model_validate(u))
    return friends


@router.post("/friends/request", response_model=FriendRequestOut)
async def send_friend_request(
    data: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == data.receiver_telegram_id))
    receiver = result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(404, "User not found")
    if receiver.id == current_user.id:
        raise HTTPException(400, "Cannot add yourself")

    # Block if there's already a pending or accepted relation in either direction
    existing = await db.execute(
        select(FriendRequest).where(
            (
                (FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == receiver.id)
            ) | (
                (FriendRequest.sender_id == receiver.id) & (FriendRequest.receiver_id == current_user.id)
            ),
            FriendRequest.status.in_([FriendRequestStatus.PENDING, FriendRequestStatus.ACCEPTED]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Friend request already exists or already friends")

    req = FriendRequest(sender_id=current_user.id, receiver_id=receiver.id)
    db.add(req)
    await db.flush()

    sender_name = f"@{current_user.username}" if current_user.username else current_user.first_name
    notify_text = (
        f"👥 <b>{sender_name}</b> отправил(а) тебе запрос в друзья!\n\n"
        f"Открой раздел «Друзья» чтобы принять или отклонить."
    )
    settings = get_settings()
    await notify_users(settings.bot_token, [receiver.telegram_id], notify_text)

    return _build_friend_req_out(req, current_user, receiver)


@router.post("/friends/requests/{request_id}/accept", response_model=FriendRequestOut)
async def accept_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FriendRequest).where(FriendRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req or req.receiver_id != current_user.id:
        raise HTTPException(404, "Request not found")
    req.status = FriendRequestStatus.ACCEPTED
    await db.flush()
    sender = await db.get(User, req.sender_id)
    receiver = await db.get(User, req.receiver_id)

    accepter_name = f"@{current_user.username}" if current_user.username else current_user.first_name
    notify_text = f"✅ <b>{accepter_name}</b> принял(а) твой запрос в друзья!"
    settings = get_settings()
    await notify_users(settings.bot_token, [sender.telegram_id], notify_text)

    return _build_friend_req_out(req, sender, receiver)


@router.post("/friends/requests/{request_id}/decline")
async def decline_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FriendRequest).where(FriendRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req or req.receiver_id != current_user.id:
        raise HTTPException(404, "Request not found")
    await db.delete(req)
    await db.flush()
    return {"ok": True}


@router.get("/friends/sent", response_model=list[FriendRequestOut])
async def get_sent_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.sender_id == current_user.id,
            FriendRequest.status == FriendRequestStatus.PENDING,
        )
    )
    out = []
    for req in result.scalars().all():
        receiver = await db.get(User, req.receiver_id)
        if receiver:
            out.append(_build_friend_req_out(req, current_user, receiver))
    return out


@router.delete("/friends/requests/{request_id}")
async def cancel_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FriendRequest).where(FriendRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req or req.sender_id != current_user.id or req.status != FriendRequestStatus.PENDING:
        raise HTTPException(404, "Request not found")
    await db.delete(req)
    await db.flush()
    return {"ok": True}


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    out = UserOut.model_validate(user)
    out.stats = await get_user_stats(user.id, db)
    return out
