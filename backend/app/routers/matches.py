from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, delete
from app.database import get_db
from app.models.match import Match, MatchStatus, MatchVisibility
from app.models.match_participant import MatchParticipant, ParticipantRole, ParticipantStatus
from app.models.match_stats import MatchStats, PlayerMatchStat
from app.models.payment import PaymentReceipt, PaymentStatus
from app.models.user import User
from app.schemas.match import MatchCreate, MatchUpdate, MatchOut, MatchShort, MatchStatsCreate, MatchStatsOut, ParticipantOut
from app.schemas.payment import PaymentReceiptOut, PaymentStatusUpdate
from app.schemas.user import UserShort
from app.services.file_upload import save_upload
from app.routers.users import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


def build_match_short(match: Match) -> MatchShort:
    organizer_short = UserShort.model_validate(match.organizer)
    organizer_short.roles = match.organizer.get_roles()
    confirmed = sum(1 for p in match.participants if p.status == ParticipantStatus.CONFIRMED)
    return MatchShort(
        id=match.id,
        title=match.title,
        address=match.address,
        match_date=match.match_date,
        max_players=match.max_players,
        price_per_player=float(match.price_per_player),
        visibility=match.visibility,
        status=match.status,
        is_paid=match.is_paid,
        organizer=organizer_short,
        participants_count=len(match.participants),
        confirmed_count=confirmed,
    )


def build_match_out(match: Match) -> MatchOut:
    organizer_short = UserShort.model_validate(match.organizer)
    organizer_short.roles = match.organizer.get_roles()
    participants_out = []
    for p in match.participants:
        user_short = UserShort.model_validate(p.user)
        user_short.roles = p.user.get_roles()
        participants_out.append(ParticipantOut(
            id=p.id,
            user=user_short,
            role=p.role,
            status=p.status,
            payment_confirmed=p.payment_confirmed,
            joined_at=p.joined_at,
        ))
    return MatchOut(
        id=match.id,
        title=match.title,
        address=match.address,
        latitude=float(match.latitude) if match.latitude else None,
        longitude=float(match.longitude) if match.longitude else None,
        match_date=match.match_date,
        max_players=match.max_players,
        price_per_player=float(match.price_per_player),
        description=match.description,
        visibility=match.visibility,
        status=match.status,
        is_paid=match.is_paid,
        requires_referee=match.requires_referee,
        organizer=organizer_short,
        participants=participants_out,
        created_at=match.created_at,
    )


async def load_match(match_id: int, db: AsyncSession) -> Match:
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Match)
        .options(
            selectinload(Match.organizer),
            selectinload(Match.participants).selectinload(MatchParticipant.user),
        )
        .where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Match not found")
    return match


@router.post("", response_model=MatchOut)
async def create_match(
    data: MatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = Match(
        organizer_id=current_user.id,
        title=data.title,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        match_date=data.match_date,
        max_players=data.max_players,
        price_per_player=data.price_per_player,
        description=data.description,
        visibility=data.visibility,
        is_paid=data.is_paid,
        requires_referee=data.requires_referee,
    )
    db.add(match)
    await db.flush()

    organizer_participant = MatchParticipant(
        match_id=match.id,
        user_id=current_user.id,
        role=ParticipantRole.PLAYER,
        status=ParticipantStatus.CONFIRMED,
        payment_confirmed=True,
    )
    db.add(organizer_participant)

    for user_id in data.invited_user_ids:
        invite = MatchParticipant(
            match_id=match.id,
            user_id=user_id,
            role=ParticipantRole.PLAYER,
            status=ParticipantStatus.INVITED,
        )
        db.add(invite)

    await db.flush()
    match = await load_match(match.id, db)
    return build_match_out(match)


@router.get("", response_model=list[MatchShort])
async def list_matches(
    status: MatchStatus | None = None,
    mine: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload
    query = select(Match).options(
        selectinload(Match.organizer),
        selectinload(Match.participants).selectinload(MatchParticipant.user),
    )

    if mine:
        participant_match_ids = await db.execute(
            select(MatchParticipant.match_id).where(MatchParticipant.user_id == current_user.id)
        )
        ids = [r[0] for r in participant_match_ids.all()]
        query = query.where(or_(Match.organizer_id == current_user.id, Match.id.in_(ids)))
    else:
        query = query.where(
            or_(Match.visibility == MatchVisibility.PUBLIC, Match.organizer_id == current_user.id)
        )

    if status:
        query = query.where(Match.status == status)

    query = query.order_by(Match.match_date.asc())
    result = await db.execute(query)
    matches = result.scalars().all()
    return [build_match_short(m) for m in matches]


@router.get("/search", response_model=list[MatchShort])
async def search_matches(
    q: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Match).options(
            selectinload(Match.organizer),
            selectinload(Match.participants).selectinload(MatchParticipant.user),
        ).where(
            Match.visibility == MatchVisibility.PUBLIC,
            Match.status == MatchStatus.UPCOMING,
            or_(Match.title.ilike(f"%{q}%"), Match.address.ilike(f"%{q}%")),
        ).order_by(Match.match_date.asc()).limit(20)
    )
    return [build_match_short(m) for m in result.scalars().all()]


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.visibility == MatchVisibility.PRIVATE and match.organizer_id != current_user.id:
        is_participant = any(p.user_id == current_user.id for p in match.participants)
        if not is_participant:
            raise HTTPException(403, "This match is private")
    return build_match_out(match)


@router.patch("/{match_id}", response_model=MatchOut)
async def update_match(
    match_id: int,
    data: MatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.organizer_id != current_user.id:
        raise HTTPException(403, "Only organizer can update")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(match, field, value)
    await db.flush()
    match = await load_match(match_id, db)
    return build_match_out(match)


@router.post("/{match_id}/join", response_model=MatchOut)
async def join_match(
    match_id: int,
    as_referee: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.status != MatchStatus.UPCOMING:
        raise HTTPException(400, "Match is not open for joining")

    existing = next((p for p in match.participants if p.user_id == current_user.id), None)
    if existing:
        raise HTTPException(400, "Already joined")

    role = ParticipantRole.REFEREE if as_referee else ParticipantRole.PLAYER
    if role == ParticipantRole.PLAYER:
        confirmed_players = sum(
            1 for p in match.participants
            if p.role == ParticipantRole.PLAYER and p.status == ParticipantStatus.CONFIRMED
        )
        if confirmed_players >= match.max_players:
            raise HTTPException(400, "No slots available")

    initial_status = ParticipantStatus.PENDING_PAYMENT if match.is_paid and role == ParticipantRole.PLAYER else ParticipantStatus.CONFIRMED
    participant = MatchParticipant(
        match_id=match.id,
        user_id=current_user.id,
        role=role,
        status=initial_status,
        payment_confirmed=(role == ParticipantRole.REFEREE),
    )
    db.add(participant)
    await db.flush()
    match = await load_match(match_id, db)
    return build_match_out(match)


@router.post("/{match_id}/leave", response_model=MatchOut)
async def leave_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.organizer_id == current_user.id:
        raise HTTPException(400, "Organizer cannot leave. Cancel the match instead.")

    participant = next((p for p in match.participants if p.user_id == current_user.id), None)
    if not participant:
        raise HTTPException(404, "Not a participant")

    participant.status = ParticipantStatus.CANCELLED
    await db.flush()
    match = await load_match(match_id, db)
    return build_match_out(match)


@router.post("/{match_id}/invite/{user_id}", response_model=MatchOut)
async def invite_user(
    match_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.organizer_id != current_user.id:
        raise HTTPException(403, "Only organizer can invite")

    existing = next((p for p in match.participants if p.user_id == user_id), None)
    if existing:
        raise HTTPException(400, "User already invited or participating")

    invite = MatchParticipant(
        match_id=match.id,
        user_id=user_id,
        role=ParticipantRole.PLAYER,
        status=ParticipantStatus.INVITED,
    )
    db.add(invite)
    await db.flush()
    match = await load_match(match_id, db)
    return build_match_out(match)


@router.post("/{match_id}/accept-invite", response_model=MatchOut)
async def accept_invite(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    participant = next((p for p in match.participants if p.user_id == current_user.id), None)
    if not participant or participant.status != ParticipantStatus.INVITED:
        raise HTTPException(404, "No invitation found")

    participant.status = ParticipantStatus.PENDING_PAYMENT if match.is_paid else ParticipantStatus.CONFIRMED
    await db.flush()
    match = await load_match(match_id, db)
    return build_match_out(match)


@router.post("/{match_id}/upload-receipt", response_model=PaymentReceiptOut)
async def upload_receipt(
    match_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    participant = next((p for p in match.participants if p.user_id == current_user.id), None)
    if not participant:
        raise HTTPException(403, "Not a participant")
    if not match.is_paid:
        raise HTTPException(400, "Match is not paid")

    url = await save_upload(file, subfolder="receipts")

    existing = await db.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.match_id == match_id,
            PaymentReceipt.user_id == current_user.id,
        )
    )
    receipt = existing.scalar_one_or_none()
    if receipt:
        receipt.receipt_url = url
        receipt.status = PaymentStatus.UPLOADED
    else:
        receipt = PaymentReceipt(
            match_id=match_id,
            user_id=current_user.id,
            receipt_url=url,
        )
        db.add(receipt)
    await db.flush()
    await db.refresh(receipt)

    user_short = UserShort.model_validate(current_user)
    user_short.roles = current_user.get_roles()
    return PaymentReceiptOut(
        id=receipt.id,
        match_id=receipt.match_id,
        user=user_short,
        receipt_url=receipt.receipt_url,
        status=receipt.status,
        organizer_note=receipt.organizer_note,
        uploaded_at=receipt.uploaded_at,
        reviewed_at=receipt.reviewed_at,
    )


@router.get("/{match_id}/receipts", response_model=list[PaymentReceiptOut])
async def get_receipts(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.organizer_id != current_user.id:
        raise HTTPException(403, "Only organizer can view receipts")

    result = await db.execute(
        select(PaymentReceipt).where(PaymentReceipt.match_id == match_id)
    )
    receipts = result.scalars().all()
    out = []
    for r in receipts:
        user = await db.get(User, r.user_id)
        user_short = UserShort.model_validate(user)
        user_short.roles = user.get_roles() if user else []
        out.append(PaymentReceiptOut(
            id=r.id, match_id=r.match_id, user=user_short,
            receipt_url=r.receipt_url, status=r.status,
            organizer_note=r.organizer_note, uploaded_at=r.uploaded_at,
            reviewed_at=r.reviewed_at,
        ))
    return out


@router.patch("/{match_id}/receipts/{receipt_id}", response_model=PaymentReceiptOut)
async def review_receipt(
    match_id: int,
    receipt_id: int,
    data: PaymentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.organizer_id != current_user.id:
        raise HTTPException(403, "Only organizer can review receipts")

    result = await db.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.id == receipt_id, PaymentReceipt.match_id == match_id
        )
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(404, "Receipt not found")

    receipt.status = data.status
    receipt.organizer_note = data.organizer_note
    receipt.reviewed_at = datetime.utcnow()

    if data.status == PaymentStatus.APPROVED:
        participant_result = await db.execute(
            select(MatchParticipant).where(
                MatchParticipant.match_id == match_id,
                MatchParticipant.user_id == receipt.user_id,
            )
        )
        participant = participant_result.scalar_one_or_none()
        if participant:
            participant.payment_confirmed = True
            participant.status = ParticipantStatus.CONFIRMED

    await db.flush()
    user = await db.get(User, receipt.user_id)
    user_short = UserShort.model_validate(user)
    user_short.roles = user.get_roles() if user else []
    return PaymentReceiptOut(
        id=receipt.id, match_id=receipt.match_id, user=user_short,
        receipt_url=receipt.receipt_url, status=receipt.status,
        organizer_note=receipt.organizer_note, uploaded_at=receipt.uploaded_at,
        reviewed_at=receipt.reviewed_at,
    )


@router.post("/{match_id}/stats", response_model=MatchStatsOut)
async def submit_stats(
    match_id: int,
    data: MatchStatsCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await load_match(match_id, db)
    if match.organizer_id != current_user.id:
        raise HTTPException(403, "Only organizer can submit stats")

    existing = await db.execute(select(MatchStats).where(MatchStats.match_id == match_id))
    match_stats = existing.scalar_one_or_none()
    if match_stats:
        match_stats.team1_score = data.team1_score
        match_stats.team2_score = data.team2_score
        await db.execute(
            delete(PlayerMatchStat).where(PlayerMatchStat.match_stats_id == match_stats.id)
        )
    else:
        match_stats = MatchStats(match_id=match_id, team1_score=data.team1_score, team2_score=data.team2_score)
        db.add(match_stats)
        await db.flush()

    for ps in data.player_stats:
        stat = PlayerMatchStat(
            match_stats_id=match_stats.id,
            user_id=ps.user_id,
            goals=ps.goals,
            assists=ps.assists,
            yellow_cards=ps.yellow_cards,
            red_cards=ps.red_cards,
            fouls=ps.fouls,
            is_injured=ps.is_injured,
            is_referee=ps.is_referee,
            notes=ps.notes,
        )
        db.add(stat)

    match.status = MatchStatus.FINISHED
    await db.flush()

    result = await db.execute(
        select(MatchStats)
        .where(MatchStats.id == match_stats.id)
    )
    ms = result.scalar_one()

    ps_result = await db.execute(
        select(PlayerMatchStat).where(PlayerMatchStat.match_stats_id == ms.id)
    )
    player_stats_rows = ps_result.scalars().all()

    from app.schemas.match import PlayerMatchStatOut
    ps_out = []
    for row in player_stats_rows:
        user = await db.get(User, row.user_id)
        if user:
            user_short = UserShort.model_validate(user)
            user_short.roles = user.get_roles()
            ps_out.append(PlayerMatchStatOut(
                id=row.id, user=user_short,
                goals=row.goals, assists=row.assists,
                yellow_cards=row.yellow_cards, red_cards=row.red_cards,
                fouls=row.fouls, is_injured=row.is_injured,
                is_referee=row.is_referee, notes=row.notes,
            ))

    return MatchStatsOut(
        id=ms.id, match_id=ms.match_id,
        team1_score=ms.team1_score, team2_score=ms.team2_score,
        player_stats=ps_out, created_at=ms.created_at,
    )


@router.get("/{match_id}/stats", response_model=MatchStatsOut)
async def get_stats(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MatchStats).where(MatchStats.match_id == match_id))
    ms = result.scalar_one_or_none()
    if not ms:
        raise HTTPException(404, "Stats not found")

    ps_result = await db.execute(
        select(PlayerMatchStat).where(PlayerMatchStat.match_stats_id == ms.id)
    )
    player_stats_rows = ps_result.scalars().all()

    from app.schemas.match import PlayerMatchStatOut
    ps_out = []
    for row in player_stats_rows:
        user = await db.get(User, row.user_id)
        if user:
            user_short = UserShort.model_validate(user)
            user_short.roles = user.get_roles()
            ps_out.append(PlayerMatchStatOut(
                id=row.id, user=user_short,
                goals=row.goals, assists=row.assists,
                yellow_cards=row.yellow_cards, red_cards=row.red_cards,
                fouls=row.fouls, is_injured=row.is_injured,
                is_referee=row.is_referee, notes=row.notes,
            ))

    return MatchStatsOut(
        id=ms.id, match_id=ms.match_id,
        team1_score=ms.team1_score, team2_score=ms.team2_score,
        player_stats=ps_out, created_at=ms.created_at,
    )
