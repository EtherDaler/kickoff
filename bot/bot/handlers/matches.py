from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from bot.api.client import APIClient
from bot.keyboards.inline import matches_list_keyboard, match_actions, match_edit_menu
from bot.keyboards.reply import main_menu, cancel_kb
from bot.states.states import MatchSearch, ReceiptUpload, MatchRepeat, MatchEdit

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

    tg_id = message.from_user.id
    is_org = match["organizer"]["telegram_id"] == tg_id
    participants = match.get("participants", [])
    is_part = any(p["user"]["telegram_id"] == tg_id for p in participants)
    is_co_org = any(
        p["user"]["telegram_id"] == tg_id and p.get("is_co_organizer")
        for p in participants
    )
    confirmed = sum(1 for p in participants if p["status"] == "confirmed")

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

    if participants:
        text += "\n<b>Участники:</b>\n"
        for p in participants[:15]:
            u = p["user"]
            role_icon = "🟡" if p["role"] == "referee" else "⚽"
            status_icon = {"confirmed": "✅", "pending_payment": "⏳", "invited": "📨", "cancelled": "❌"}.get(p["status"], "❓")
            name = f"@{u['username']}" if u.get("username") else u["first_name"]
            co_label = " 👑" if p.get("is_co_organizer") else ""
            text += f"  {role_icon} {status_icon} {name}{co_label}\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=match_actions(
            match_id, is_org, is_part,
            match.get("is_paid", False),
            status=match.get("status", "upcoming"),
            is_co_organizer=is_co_org,
        ),
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


# ─── История матчей ────────────────────────────────────────────────────────────

@router.message(F.text == "📜 История")
@router.message(Command("history"))
async def cmd_history(message: Message, api: APIClient):
    matches = await api.get_matches(message.from_user.id, mine=True, status="finished")
    if not matches:
        await message.answer("📜 У тебя пока нет завершённых матчей.")
        return

    text = f"📜 <b>История матчей</b> ({len(matches)}):\n\n"
    for m in matches[:5]:
        text += format_match_short(m) + "\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=matches_list_keyboard(matches),
    )


# ─── Повторить матч ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("repeat_match:"))
async def cb_repeat_match(call: CallbackQuery, state: FSMContext):
    match_id = int(call.data.split(":")[1])
    await state.update_data(repeat_match_id=match_id)
    await state.set_state(MatchRepeat.waiting_date)
    await call.message.answer(
        "🔁 <b>Повторить матч</b>\n\n"
        "Введи новую дату и время в формате:\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
        "Например: <code>15.06.2025 18:00</code>",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(MatchRepeat.waiting_date)
async def process_repeat_date(message: Message, state: FSMContext, api: APIClient):
    if not message.text:
        await message.answer("❗ Отправь дату текстовым сообщением.")
        return

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❗ Неверный формат. Введи дату в виде: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>",
            parse_mode="HTML",
        )
        return

    if dt <= datetime.now():
        await message.answer("❗ Дата должна быть в будущем. Попробуй ещё раз.")
        return

    data = await state.get_data()
    match_id = data.get("repeat_match_id")
    await state.clear()

    iso_date = dt.strftime("%Y-%m-%dT%H:%M:%S")
    result = await api.repeat_match(message.from_user.id, match_id, iso_date)

    if not result or "error" in result:
        await message.answer("❌ Не удалось создать матч. Попробуй позже.", reply_markup=main_menu())
        return

    await message.answer(
        f"✅ Матч успешно создан! (#{result['id']})\n\nПоказываю детали:",
        reply_markup=main_menu(),
    )
    await show_match_detail(message, api, result["id"])


# ─── Редактирование матча ──────────────────────────────────────────────────────

EDIT_FIELD_LABELS = {
    "title": "названия",
    "address": "адреса",
    "match_date": "даты и времени",
    "max_players": "макс. числа игроков",
    "price_per_player": "цены за игрока",
    "description": "описания",
}

EDIT_FIELD_HINTS = {
    "title": "Введи новое название матча:",
    "address": "Введи новый адрес матча:",
    "match_date": "Введи новую дату и время (<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>):",
    "max_players": "Введи максимальное количество игроков (2–50):",
    "price_per_player": "Введи новую цену за игрока (руб.):",
    "description": "Введи новое описание матча (или «-» чтобы убрать):",
}


@router.callback_query(F.data.startswith("edit_match:"))
async def cb_edit_match(call: CallbackQuery, api: APIClient):
    match_id = int(call.data.split(":")[1])
    match = await api.get_match(call.from_user.id, match_id)
    if not match:
        await call.answer("Матч не найден", show_alert=True)
        return
    if match["organizer"]["telegram_id"] != call.from_user.id:
        await call.answer("Только организатор может редактировать матч", show_alert=True)
        return

    await call.message.answer(
        f"✏️ <b>Редактировать матч «{match['title']}»</b>\n\nВыбери, что хочешь изменить:",
        parse_mode="HTML",
        reply_markup=match_edit_menu(match_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def cb_edit_field(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    match_id = int(parts[1])
    field = parts[2]

    await state.update_data(edit_match_id=match_id, edit_field=field)
    await state.set_state(MatchEdit.waiting_value)

    hint = EDIT_FIELD_HINTS.get(field, "Введи новое значение:")
    await call.message.answer(
        hint,
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(MatchEdit.waiting_value)
async def process_edit_value(message: Message, state: FSMContext, api: APIClient):
    if not message.text:
        await message.answer("❗ Отправь текстовое сообщение.")
        return

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    data = await state.get_data()
    match_id = data.get("edit_match_id")
    field = data.get("edit_field")
    raw = message.text.strip()

    parsed_value = None
    if field == "match_date":
        try:
            dt = datetime.strptime(raw, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer(
                "❗ Неверный формат даты. Введи в виде: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>",
                parse_mode="HTML",
            )
            return
        if dt <= datetime.now():
            await message.answer("❗ Дата должна быть в будущем. Попробуй ещё раз.")
            return
        parsed_value = dt.strftime("%Y-%m-%dT%H:%M:%S")
    elif field == "max_players":
        if not raw.isdigit() or not (2 <= int(raw) <= 50):
            await message.answer("❗ Введи число от 2 до 50.")
            return
        parsed_value = int(raw)
    elif field == "price_per_player":
        try:
            parsed_value = float(raw)
            if parsed_value < 0:
                raise ValueError
        except ValueError:
            await message.answer("❗ Введи корректную сумму (например: 500 или 0).")
            return
    elif field == "description":
        parsed_value = "" if raw == "-" else raw
    else:
        parsed_value = raw

    await state.clear()

    update_data = {field: parsed_value}
    result = await api.update_match(message.from_user.id, match_id, update_data)

    if not result or "error" in result:
        err_detail = ""
        if result and "error" in result:
            import json
            try:
                err_detail = json.loads(result["error"]).get("detail", "")
            except Exception:
                pass
        await message.answer(
            f"❌ Не удалось обновить матч. {err_detail}",
            reply_markup=main_menu(),
        )
        return

    label = EDIT_FIELD_LABELS.get(field, field)
    await message.answer(
        f"✅ {label.capitalize()} успешно обновлено! Участники получат уведомление.",
        reply_markup=main_menu(),
    )
    await show_match_detail(message, api, match_id)
