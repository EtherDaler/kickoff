from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="⚽ Матчи")],
            [KeyboardButton(text="👥 Друзья"), KeyboardButton(text="🔍 Найти матч")],
            [KeyboardButton(text="📋 Мои матчи"), KeyboardButton(text="📜 История")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
