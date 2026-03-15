from aiogram.fsm.state import State, StatesGroup


class ProfileEdit(StatesGroup):
    waiting_age = State()
    waiting_city = State()
    waiting_bio = State()
    editing_roles = State()


class MatchSearch(StatesGroup):
    waiting_query = State()
    waiting_match_id = State()


class FriendSearch(StatesGroup):
    waiting_query = State()
    waiting_add_id = State()


class ReceiptUpload(StatesGroup):
    waiting_photo = State()
