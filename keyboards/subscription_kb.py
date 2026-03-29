from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import database

def subscription_kb(mode_key=1, trial_used=True, is_subscription=False):
    modes = {1: 'user', 2: 'admin'}
    mode = modes[mode_key]
    kb = InlineKeyboardBuilder()
    tariffs_list = database.get_all_tariffs()
    tariffs = {tariff_id: (name, price, duration_day, is_status) for tariff_id, name, price, duration_day, is_status in tariffs_list}
    for key, item in tariffs.items():
        name, price, days, is_status = item
        if is_status:
            kb.button(text=f'💎 Тариф {name} ({price}₽)', callback_data=f'buy_{key}')
    if trial_used and not is_subscription:
        kb.button(text='🎁 Пробный бесплатный тариф 7 дней', callback_data='free_tariff') #тут делаем проверку использовал или нет, если нет, то кнопка есть
    if mode == 'admin':
        kb.button(text=f'⚙️ Изменить настройки оплаты', callback_data='payment_settings')
    kb.button(text='⬅️ Назад', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()

def payment_method_kb():
    kb = InlineKeyboardBuilder()
    payments_method = database.get_payments_method()
    for method in payments_method:
        method_id, method_name, _ = method
        kb.button(text=f'💳 {method_name}', callback_data=f'payment_method_{method_id}')
    kb.button(text='⬅️ Назад', callback_data='buy_subscription')
    kb.adjust(1)
    return kb.as_markup()



def activate_trial_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="activate_trial_yes")
    kb.button(text="❌ Нет", callback_data="activate_trial_no")
    kb.adjust(2)
    return kb.as_markup()
