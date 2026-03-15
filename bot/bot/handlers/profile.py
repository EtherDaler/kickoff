from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.api.client import APIClient
from bot.keyboards.inline import profile_menu, edit_profile_menu, roles_keyboard
from bot.keyboards.reply import main_menu, cancel_kb
from bot.states.states import ProfileEdit
from bot.config import get_settings

router = Router()
settings = get_settings()

ROLE_NAMES = {
    "forward": "⚡ Нападающий",
    "midfielder": "🔄 Полузащитник",
    "defender": "🛡 Защитник",
    "goalkeeper": "🧤 Вратарь",
    "referee": "🟡 Судья",
}


def format_profile(user: dict) -> str:
    roles = [ROLE_NAMES.get(r, r) for r in user.get("roles", [])]
    stats = user.get("stats") or {}
    name = f"{user['first_name']}" + (f" {user['last_name']}" if user.get("last_name") else "")
    username = f"@{user['username']}" if user.get("username") else "—"

    lines = [
        f"👤 <b>{name}</b>",
        f"🔗 {username}",
    ]
    if user.get("age"):
        lines.append(f"🎂 Возраст: {user['age']}")
    if user.get("city"):
        lines.append(f"🏙 Город: {user['city']}")
    if user.get("bio"):
        lines.append(f"📝 {user['bio']}")
    if roles:
        lines.append(f"⚽ Позиции: {', '.join(roles)}")

    if stats:
        lines += [
            "",
            "📊 <b>Статистика:</b>",
            f"🏆 Матчей: {stats.get('total_matches', 0)}",
            f"⚽ Голов: {stats.get('total_goals', 0)}",
            f"🎯 Передач: {stats.get('total_assists', 0)}",
            f"🟡 Ж.карточек: {stats.get('total_yellow_cards', 0)}",
            f"🔴 К.карточек: {stats.get('total_red_cards', 0)}",
            f"🏥 Травм: {stats.get('injuries', 0)}",
            f"🟡 Судейских матчей: {stats.get('referee_matches', 0)}",
        ]

    return "\n".join(lines)


@router.message(F.text == "👤 Мой профиль")
@router.message(Command("profile"))
async def show_profile(message: Message, api: APIClient):
    user = await api.get_profile(message.from_user.id)
    if not user:
        await message.answer("⚠️ Профиль не найден. Введи /start")
        return
    await message.answer(
        format_profile(user),
        parse_mode="HTML",
        reply_markup=profile_menu(settings.mini_app_url, message.from_user.id),
    )


@router.callback_query(F.data == "edit_profile")
async def cb_edit_profile(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=edit_profile_menu())
    await call.answer()


@router.callback_query(F.data == "back_to_profile")
async def cb_back_to_profile(call: CallbackQuery, api: APIClient):
    user = await api.get_profile(call.from_user.id)
    if not user:
        await call.answer("Профиль не найден")
        return
    await call.message.edit_text(
        format_profile(user),
        parse_mode="HTML",
        reply_markup=profile_menu(settings.mini_app_url, call.from_user.id),
    )
    await call.answer()


@router.callback_query(F.data == "edit_age")
async def cb_edit_age(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🎂 Введи свой возраст (5–100):", reply_markup=cancel_kb())
    await state.set_state(ProfileEdit.waiting_age)
    await call.answer()


@router.message(ProfileEdit.waiting_age)
async def process_age(message: Message, state: FSMContext, api: APIClient):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return
    if not message.text.isdigit() or not (5 <= int(message.text) <= 100):
        await message.answer("❗ Введи корректный возраст (5–100):")
        return
    await api.update_profile(message.from_user.id, {"age": int(message.text)})
    await state.clear()
    await message.answer("✅ Возраст обновлён!", reply_markup=main_menu())


@router.callback_query(F.data == "edit_city")
async def cb_edit_city(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🏙 Введи название своего города:", reply_markup=cancel_kb())
    await state.set_state(ProfileEdit.waiting_city)
    await call.answer()


@router.message(ProfileEdit.waiting_city)
async def process_city(message: Message, state: FSMContext, api: APIClient):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return
    await api.update_profile(message.from_user.id, {"city": message.text.strip()})
    await state.clear()
    await message.answer("✅ Город обновлён!", reply_markup=main_menu())


@router.callback_query(F.data == "edit_bio")
async def cb_edit_bio(call: CallbackQuery, state: FSMContext):
    await call.message.answer("📝 Напиши кратко о себе:", reply_markup=cancel_kb())
    await state.set_state(ProfileEdit.waiting_bio)
    await call.answer()


@router.message(ProfileEdit.waiting_bio)
async def process_bio(message: Message, state: FSMContext, api: APIClient):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return
    await api.update_profile(message.from_user.id, {"bio": message.text.strip()[:512]})
    await state.clear()
    await message.answer("✅ Описание обновлено!", reply_markup=main_menu())


@router.callback_query(F.data == "edit_roles")
async def cb_edit_roles(call: CallbackQuery, state: FSMContext, api: APIClient):
    user = await api.get_profile(call.from_user.id)
    current_roles = user.get("roles", []) if user else []
    await state.update_data(roles=current_roles)
    await state.set_state(ProfileEdit.editing_roles)
    await call.message.answer(
        "⚽ Выбери свои позиции (можно несколько):",
        reply_markup=roles_keyboard(current_roles),
    )
    await call.answer()


@router.callback_query(F.data.startswith("toggle_role:"), ProfileEdit.editing_roles)
async def toggle_role(call: CallbackQuery, state: FSMContext):
    role = call.data.split(":")[1]
    data = await state.get_data()
    roles: list[str] = data.get("roles", [])
    if role in roles:
        roles.remove(role)
    else:
        roles.append(role)
    await state.update_data(roles=roles)
    await call.message.edit_reply_markup(reply_markup=roles_keyboard(roles))
    await call.answer()


@router.callback_query(F.data == "save_roles", ProfileEdit.editing_roles)
async def save_roles(call: CallbackQuery, state: FSMContext, api: APIClient):
    data = await state.get_data()
    roles = data.get("roles", [])
    await api.update_profile(call.from_user.id, {"roles": roles})
    await state.clear()
    await call.message.edit_text("✅ Позиции сохранены!")
    await call.answer("Сохранено!")


@router.callback_query(F.data == "my_stats")
async def cb_my_stats(call: CallbackQuery, api: APIClient):
    user = await api.get_profile(call.from_user.id)
    if not user or not user.get("stats"):
        await call.answer("Статистика пуста", show_alert=True)
        return
    await call.message.answer(format_profile(user), parse_mode="HTML")
    await call.answer()
