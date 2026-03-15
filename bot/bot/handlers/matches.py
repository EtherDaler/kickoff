from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from bot.api.client import APIClient
from bot.keyboards.inline import matches_list_keyboard, match_actions
from bot.keyboards.reply import main_menu, cancel_kb
from bot.states.states import MatchSearch, ReceiptUpload

router = Router()

STATUS_MAP = {
    "upcoming": "📅 Предстоящий",
    "ongoing": "🟢 В процессе",
    "finished": "✅ Завершён",
    "cancelled": "❌ Отменён",
}
VIS_MAP = {"public": "🌍 Публичный", "private": "🔒 Закрытый"}


def format_match_short(m: dict) -> str:
    confirmed = m.get("confirmed_count", 0)
    total = m.get("max_players", 0)
    paid = "💰 Платный" if m.get("is_paid") else "🆓 Бесплатный"
    return (
        f"⚽ <b>{m['title']}</b> (#{m['id']})\n"
        f"📍 {m['address']}\n"
        f"📅 {m['match_date'].replace('T', ' ')[:16]}\n"
        f"👥 {confirmed}/{total} | {paid}\n"
        f"📊 {STATUS_MAP.get(m['status'], m['status'])}\n"
    )


async def show_match_detail(message: Message, api: APIClient, match_id: int):
    match = await api.get_match(message.from_user.id, match_id)
    if not match:
        await message.answer("❌ Матч не найден или у вас нет доступа.")
        return

    is_org = match["organizer"]["telegram_id"] == message.from_user.id
    is_part = any(p["user"]["telegram_id"] == message.from_user.id for p in match.get("participants", []))
    confirmed = sum(1 for p in match.get("participants", []) if p["status"] == "confirmed")

    text = (
        f"⚽ <b>{match['title']}</b> (#{match['id']})\n\n"
        f"📍 {match['address']}\n"
        f"📅 {match['match_date'].replace('T', ' ')[:16]}\n"
        f"👥 {confirmed}/{match['max_players']} игроков\n"
        f"💰 {match['price_per_player']} руб./чел.\n"
        f"🔍 {VIS_MAP.get(match['visibility'], match['visibility'])}\n"
        f"📊 {STATUS_MAP.get(match['status'], match['status'])}\n"
    )
    if match.get("description"):
        text += f"\n📝 {match['description']}\n"

    participants = match.get("participants", [])
    if participants:
        text += "\n<b>Участники:</b>\n"
        for p in participants[:15]:
            u = p["user"]
            role_icon = "🟡" if p["role"] == "referee" else "⚽"
            status_icon = {"confirmed": "✅", "pending_payment": "⏳", "invited": "📨", "cancelled": "❌"}.get(p["status"], "❓")
            name = f"@{u['username']}" if u.get("username") else u["first_name"]
            text += f"  {role_icon} {status_icon} {name}\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=match_actions(match_id, is_org, is_part, match.get("is_paid", False)),
    )


@router.message(F.text == "⚽ Матчи")
@router.message(Command("matches"))
async def cmd_matches(message: Message, api: APIClient):
    matches = await api.get_matches(message.from_user.id, status="upcoming")
    if not matches:
        await message.answer("😔 Публичных предстоящих матчей пока нет.")
        return

    text = f"⚽ <b>Публичные матчи</b> ({len(matches)}):\n\n"
    for m in matches[:5]:
        text += format_match_short(m) + "\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=matches_list_keyboard(matches),
    )


@router.message(F.text == "📋 Мои матчи")
@router.message(Command("mymatches"))
async def cmd_my_matches(message: Message, api: APIClient):
    matches = await api.get_matches(message.from_user.id, mine=True)
    if not matches:
        await message.answer("У тебя пока нет матчей.")
        return

    text = f"📋 <b>Мои матчи</b> ({len(matches)}):\n\n"
    for m in matches[:5]:
        text += format_match_short(m) + "\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=matches_list_keyboard(matches),
    )


@router.message(F.text == "🔍 Найти матч")
@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    await message.answer(
        "🔍 Введи название или адрес матча для поиска (или ID матча):",
        reply_markup=cancel_kb(),
    )
    await state.set_state(MatchSearch.waiting_query)


@router.message(MatchSearch.waiting_query)
async def process_search(message: Message, state: FSMContext, api: APIClient):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    query = message.text.strip()
    await state.clear()

    if query.isdigit():
        await show_match_detail(message, api, int(query))
        return

    matches = await api.search_matches(message.from_user.id, query)
    if not matches:
        await message.answer(f"😔 Матчи по запросу «{query}» не найдены.", reply_markup=main_menu())
        return

    text = f"🔍 <b>Результаты поиска</b> ({len(matches)}):\n\n"
    for m in matches[:5]:
        text += format_match_short(m) + "\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=matches_list_keyboard(matches),
    )
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data.startswith("match_info:"))
async def cb_match_info(call: CallbackQuery, api: APIClient):
    match_id = int(call.data.split(":")[1])
    await show_match_detail(call.message, api, match_id)
    await call.answer()


@router.callback_query(F.data.startswith("join_match:"))
async def cb_join_match(call: CallbackQuery, api: APIClient):
    match_id = int(call.data.split(":")[1])
    result = await api.join_match(call.from_user.id, match_id)
    if result and "error" not in result:
        await call.answer("✅ Ты присоединился к матчу!", show_alert=True)
        await show_match_detail(call.message, api, match_id)
    else:
        error_msg = "❌ Не удалось присоединиться."
        if result and "error" in result:
            import json
            try:
                err = json.loads(result["error"])
                error_msg = f"❌ {err.get('detail', error_msg)}"
            except Exception:
                pass
        await call.answer(error_msg, show_alert=True)


@router.callback_query(F.data.startswith("join_referee:"))
async def cb_join_referee(call: CallbackQuery, api: APIClient):
    match_id = int(call.data.split(":")[1])
    result = await api.join_match(call.from_user.id, match_id, as_referee=True)
    if result and "error" not in result:
        await call.answer("🟡 Ты присоединился как судья!", show_alert=True)
        await show_match_detail(call.message, api, match_id)
    else:
        await call.answer("❌ Не удалось присоединиться как судья.", show_alert=True)


@router.callback_query(F.data.startswith("leave_match:"))
async def cb_leave_match(call: CallbackQuery, api: APIClient):
    match_id = int(call.data.split(":")[1])
    success = await api.leave_match(call.from_user.id, match_id)
    if success:
        await call.answer("✅ Ты отменил участие.", show_alert=True)
        await show_match_detail(call.message, api, match_id)
    else:
        await call.answer("❌ Не удалось отменить участие.", show_alert=True)


@router.callback_query(F.data.startswith("upload_receipt:"))
async def cb_upload_receipt(call: CallbackQuery, state: FSMContext):
    match_id = int(call.data.split(":")[1])
    await state.update_data(receipt_match_id=match_id)
    await state.set_state(ReceiptUpload.waiting_photo)
    await call.message.answer(
        "📸 Отправь фото чека об оплате:",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(ReceiptUpload.waiting_photo, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext, api: APIClient):
    data = await state.get_data()
    match_id = data.get("receipt_match_id")

    photo: PhotoSize = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    result = await api.upload_receipt(
        message.from_user.id, match_id,
        file_bytes.read(), f"receipt_{photo.file_id}.jpg"
    )
    await state.clear()
    if result:
        await message.answer(
            "✅ Чек загружен! Ожидай подтверждения от организатора.",
            reply_markup=main_menu(),
        )
    else:
        await message.answer("❌ Ошибка загрузки чека.", reply_markup=main_menu())


@router.message(ReceiptUpload.waiting_photo)
async def process_receipt_not_photo(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return
    await message.answer("❗ Отправь именно фото чека.")


@router.callback_query(F.data.startswith("view_receipts:"))
async def cb_view_receipts(call: CallbackQuery, api: APIClient):
    match_id = int(call.data.split(":")[1])
    match = await api.get_match(call.from_user.id, match_id)
    if not match:
        await call.answer("Матч не найден", show_alert=True)
        return
    if match["organizer"]["telegram_id"] != call.from_user.id:
        await call.answer("Только организатор может смотреть чеки", show_alert=True)
        return

    import aiohttp
    from bot.config import get_settings
    settings = get_settings()
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.backend_url}/matches/{match_id}/receipts",
            headers={"X-Bot-Auth": str(call.from_user.id)},
        ) as resp:
            if resp.status != 200:
                await call.answer("Ошибка получения чеков", show_alert=True)
                return
            receipts = await resp.json()

    if not receipts:
        await call.answer("Чеки не загружены", show_alert=True)
        return

    text = f"🧾 <b>Чеки по матчу #{match_id}</b>:\n\n"
    for r in receipts:
        u = r["user"]
        name = f"@{u['username']}" if u.get("username") else u["first_name"]
        status_icon = {"uploaded": "⏳", "approved": "✅", "rejected": "❌", "refunded": "💸"}.get(r["status"], "❓")
        text += f"{status_icon} {name}: {r['receipt_url']}\n"

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("add_stats:"))
async def cb_add_stats(call: CallbackQuery):
    match_id = int(call.data.split(":")[1])
    await call.message.answer(
        f"📊 Чтобы добавить статистику по матчу #{match_id}, воспользуйся Mini App или введи данные через веб-интерфейс.",
        parse_mode="HTML",
    )
    await call.answer()
