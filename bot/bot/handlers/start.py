from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from bot.api.client import APIClient
from bot.keyboards.reply import main_menu

router = Router()

ROLE_NAMES = {
    "forward": "Нападающий",
    "midfielder": "Полузащитник",
    "defender": "Защитник",
    "goalkeeper": "Вратарь",
    "referee": "Судья",
}


@router.message(CommandStart())
async def cmd_start(message: Message, api: APIClient):
    user = message.from_user
    await api.register_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    await message.answer(
        f"⚽ <b>Привет, {user.first_name}!</b>\n\n"
        "Добро пожаловать в <b>Football Bot</b> — платформу для организации и поиска футбольных матчей.\n\n"
        "Используй меню ниже для навигации:",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Доступные команды:</b>\n\n"
        "/start — Начало работы\n"
        "/profile — Мой профиль\n"
        "/matches — Список матчей\n"
        "/mymatches — Мои матчи\n"
        "/search — Найти матч\n"
        "/friends — Друзья\n"
        "/match_id <id> — Информация о матче по ID\n",
        parse_mode="HTML",
    )


@router.message(Command("match_id"))
async def cmd_match_by_id(message: Message, api: APIClient):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❗ Укажи ID матча: /match_id 42")
        return

    match_id = int(parts[1])
    await show_match_info(message, api, match_id)


async def show_match_info(message: Message, api: APIClient, match_id: int):
    from bot.keyboards.inline import match_actions
    match = await api.get_match(message.from_user.id, match_id)
    if not match:
        await message.answer("❌ Матч не найден или у вас нет доступа.")
        return

    is_org = match["organizer"]["telegram_id"] == message.from_user.id
    is_part = any(p["user"]["telegram_id"] == message.from_user.id for p in match.get("participants", []))

    status_map = {
        "upcoming": "📅 Предстоящий",
        "ongoing": "🟢 В процессе",
        "finished": "✅ Завершён",
        "cancelled": "❌ Отменён",
    }
    vis_map = {"public": "🌍 Публичный", "private": "🔒 Закрытый"}
    confirmed = sum(1 for p in match.get("participants", []) if p["status"] == "confirmed")

    text = (
        f"⚽ <b>{match['title']}</b> (#{match['id']})\n\n"
        f"📍 {match['address']}\n"
        f"📅 {match['match_date'].replace('T', ' ')[:16]}\n"
        f"👥 {confirmed}/{match['max_players']} игроков\n"
        f"💰 {match['price_per_player']} руб./чел.\n"
        f"🔍 {vis_map.get(match['visibility'], match['visibility'])}\n"
        f"📊 {status_map.get(match['status'], match['status'])}\n"
    )
    if match.get("description"):
        text += f"\n📝 {match['description']}\n"

    if match.get("participants"):
        text += "\n<b>Участники:</b>\n"
        for p in match["participants"][:10]:
            u = p["user"]
            role_icon = "🟡" if p["role"] == "referee" else "⚽"
            status_icon = {"confirmed": "✅", "pending_payment": "⏳", "invited": "📨", "cancelled": "❌"}.get(p["status"], "❓")
            name = u.get("username") and f"@{u['username']}" or u["first_name"]
            text += f"  {role_icon} {status_icon} {name}\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=match_actions(match_id, is_org, is_part, match.get("is_paid", False)),
    )
