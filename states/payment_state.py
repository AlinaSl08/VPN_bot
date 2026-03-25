from aiogram.fsm.state import StatesGroup, State

class Payment(StatesGroup):
    tariff = State()
    method = State()
    access = State()
    trial = State()