from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_menu(mini_app_url: str, telegram_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if mini_app_url:
        builder.add(InlineKeyboardButton(
            text="🖥 Открыть Mini App",
            web_app={"url": mini_app_url}
        ))
    builder.add(InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats"))
    builder.adjust(1)
    return builder.as_markup()


def edit_profile_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎂 Возраст", callback_data="edit_age"))
    builder.add(InlineKeyboardButton(text="🏙 Город", callback_data="edit_city"))
    builder.add(InlineKeyboardButton(text="📝 О себе", callback_data="edit_bio"))
    builder.add(InlineKeyboardButton(text="⚽ Позиции", callback_data="edit_roles"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_profile"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def roles_keyboard(current_roles: list[str]) -> InlineKeyboardMarkup:
    roles = [
        ("forward", "Нападающий"),
        ("midfielder", "Полузащитник"),
        ("defender", "Защитник"),
        ("goalkeeper", "Вратарь"),
        ("referee", "Судья"),
    ]
    builder = InlineKeyboardBuilder()
    for role_key, role_name in roles:
        check = "✅ " if role_key in current_roles else ""
        builder.add(InlineKeyboardButton(
            text=f"{check}{role_name}",
            callback_data=f"toggle_role:{role_key}"
        ))
    builder.add(InlineKeyboardButton(text="💾 Сохранить", callback_data="save_roles"))
    builder.adjust(1)
    return builder.as_markup()


def match_actions(
    match_id: int,
    is_organizer: bool,
    is_participant: bool,
    is_paid: bool,
    status: str = "upcoming",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    is_finished = status in ("finished", "cancelled")

    if is_finished:
        builder.add(InlineKeyboardButton(text="🔁 Повторить матч", callback_data=f"repeat_match:{match_id}"))
    else:
        if not is_participant and not is_organizer:
            builder.add(InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"join_match:{match_id}"))
            builder.add(InlineKeyboardButton(text="🟡 Как судья", callback_data=f"join_referee:{match_id}"))
        if is_participant and not is_organizer:
            if is_paid:
                builder.add(InlineKeyboardButton(text="📸 Загрузить чек", callback_data=f"upload_receipt:{match_id}"))
            builder.add(InlineKeyboardButton(text="❌ Отменить участие", callback_data=f"leave_match:{match_id}"))
        if is_organizer:
            builder.add(InlineKeyboardButton(text="✏️ Редактировать матч", callback_data=f"edit_match:{match_id}"))
            builder.add(InlineKeyboardButton(text="📊 Добавить статистику", callback_data=f"add_stats:{match_id}"))
            builder.add(InlineKeyboardButton(text="🧾 Чеки игроков", callback_data=f"view_receipts:{match_id}"))
    builder.adjust(1)
    return builder.as_markup()


def match_edit_menu(match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fields = [
        ("title", "✏️ Название"),
        ("address", "📍 Адрес"),
        ("match_date", "📅 Дата и время"),
        ("max_players", "👥 Макс. игроков"),
        ("price_per_player", "💰 Цена за игрока"),
        ("description", "📝 Описание"),
    ]
    for field, label in fields:
        builder.add(InlineKeyboardButton(
            text=label,
            callback_data=f"edit_field:{match_id}:{field}",
        ))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data=f"match_info:{match_id}"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def friends_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="👥 Мои друзья", callback_data="my_friends"))
    builder.add(InlineKeyboardButton(text="📨 Запросы в друзья", callback_data="friend_requests"))
    builder.add(InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="search_user"))
    builder.adjust(1)
    return builder.as_markup()


def friend_request_actions(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_fr:{request_id}"))
    builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_fr:{request_id}"))
    builder.adjust(2)
    return builder.as_markup()


def matches_list_keyboard(matches: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in matches[:10]:
        date_str = m["match_date"][:10]
        builder.add(InlineKeyboardButton(
            text=f"⚽ {m['title']} ({date_str})",
            callback_data=f"match_info:{m['id']}"
        ))
    builder.adjust(1)
    return builder.as_markup()


def paginate_keyboard(items: list[dict], page: int, prefix: str, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}_page:{page+1}"))
    if nav:
        builder.row(*nav)
    return builder.as_markup()


def add_friend_keyboard(receiver_telegram_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="➕ Добавить в друзья",
        callback_data=f"add_friend:{receiver_telegram_id}"
    ))
    return builder.as_markup()
