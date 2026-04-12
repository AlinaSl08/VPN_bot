from aiogram.fsm.state import StatesGroup, State

class Profile(StatesGroup):
    waiting_for_phone = State()
    profile = State()
