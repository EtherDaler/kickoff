from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.api.client import APIClient
from bot.keyboards.inline import friends_menu, friend_request_actions, add_friend_keyboard
from bot.keyboards.reply import main_menu, cancel_kb
from bot.states.states import FriendSearch

router = Router()


def format_user_short(u: dict) -> str:
    name = f"{u['first_name']}" + (f" {u['last_name']}" if u.get("last_name") else "")
    username = f"@{u['username']}" if u.get("username") else "—"
    roles_map = {
        "forward": "Нападающий", "midfielder": "Полузащитник",
        "defender": "Защитник", "goalkeeper": "Вратарь", "referee": "Судья",
    }
    roles_str = ", ".join(roles_map.get(r, r) for r in u.get("roles", []))
    return f"👤 {name} ({username})" + (f"\n⚽ {roles_str}" if roles_str else "")


@router.message(F.text == "👥 Друзья")
@router.message(Command("friends"))
async def cmd_friends(message: Message):
    await message.answer(
        "👥 <b>Управление друзьями</b>",
        parse_mode="HTML",
        reply_markup=friends_menu(),
    )


@router.callback_query(F.data == "my_friends")
async def cb_my_friends(call: CallbackQuery, api: APIClient):
    friends = await api.get_friends(call.from_user.id)
    if not friends:
        await call.answer("У тебя пока нет друзей 😔", show_alert=True)
        return

    text = "👥 <b>Мои друзья:</b>\n\n"
    for u in friends:
        text += format_user_short(u) + "\n\n"

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "friend_requests")
async def cb_friend_requests(call: CallbackQuery, api: APIClient):
    requests = await api.get_friend_requests(call.from_user.id)
    if not requests:
        await call.answer("Нет новых запросов в друзья 👍", show_alert=True)
        return

    await call.answer()
    for req in requests:
        sender = req["sender"]
        text = f"📨 <b>Запрос от:</b>\n{format_user_short(sender)}"
        await call.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=friend_request_actions(req["id"]),
        )


@router.callback_query(F.data.startswith("accept_fr:"))
async def cb_accept_fr(call: CallbackQuery, api: APIClient):
    req_id = int(call.data.split(":")[1])
    success = await api.accept_friend_request(call.from_user.id, req_id)
    if success:
        await call.message.edit_text("✅ Запрос принят! Теперь вы друзья.")
    else:
        await call.answer("❌ Ошибка принятия запроса", show_alert=True)
    await call.answer()


@router.callback_query(F.data.startswith("decline_fr:"))
async def cb_decline_fr(call: CallbackQuery, api: APIClient):
    import aiohttp
    from bot.config import get_settings
    settings = get_settings()
    req_id = int(call.data.split(":")[1])
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.backend_url}/users/friends/requests/{req_id}/decline",
            headers={"X-Bot-Auth": str(call.from_user.id)},
        ) as resp:
            if resp.status == 200:
                await call.message.edit_text("❌ Запрос отклонён.")
            else:
                await call.answer("Ошибка", show_alert=True)
    await call.answer()


@router.callback_query(F.data == "search_user")
async def cb_search_user(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "🔍 Введи имя пользователя или @username для поиска:",
        reply_markup=cancel_kb(),
    )
    await state.set_state(FriendSearch.waiting_query)
    await call.answer()


@router.message(FriendSearch.waiting_query)
async def process_user_search(message: Message, state: FSMContext, api: APIClient):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    query = message.text.strip().lstrip("@")
    users = await api.search_users(message.from_user.id, query)
    await state.clear()

    if not users:
        await message.answer(f"😔 Пользователи по запросу «{query}» не найдены.", reply_markup=main_menu())
        return

    await message.answer(f"🔍 <b>Найдено ({len(users)}):</b>", parse_mode="HTML")
    for u in users[:5]:
        text = format_user_short(u)
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=add_friend_keyboard(u["telegram_id"]),
        )
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data.startswith("add_friend:"))
async def cb_add_friend(call: CallbackQuery, api: APIClient):
    receiver_tg_id = int(call.data.split(":")[1])
    result = await api.send_friend_request(call.from_user.id, receiver_tg_id)
    if result:
        await call.answer("✅ Запрос в друзья отправлен!", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=None)
    else:
        await call.answer("❌ Не удалось отправить запрос (возможно, уже отправлен)", show_alert=True)
