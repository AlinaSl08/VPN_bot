from aiogram.fsm.state import StatesGroup, State

class Admin(StatesGroup):
    add_tariff_name = State()
    add_tariff_days = State()
    add_tariff_price = State()
    add_method = State()
    add_admin = State()
    del_user = State()
    del_admin = State()