from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_settings_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='🔥 Настроить тарифы', callback_data='settings_tariff')
    kb.button(text='💳 Настроить способы оплат', callback_data='settings_payment_method')
    kb.button(text='⬅️ Назад', callback_data='buy_subscription')
    kb.adjust(1)
    return kb.as_markup()


def settings_tariff_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='☑️ Добавить тариф', callback_data='add_tariff')
    kb.button(text='🗑️ Удалить тариф', callback_data='del_tariff')
    kb.button(text='🟢 Включить тариф', callback_data='on_tariff')
    kb.button(text='🔴 Выключить тариф', callback_data='off_tariff')
    kb.button(text='⬅️ Назад', callback_data='payment_settings')
    kb.adjust(1)
    return kb.as_markup()

def get_tariff_kb(count_tariff, tariffs_list, mode_key=1):
    modes = {1: 'del_tariff', 2: 'on_tariff', 3: 'off_tariff'}
    mode = modes[mode_key]
    kb = InlineKeyboardBuilder()
    if mode == "del_tariff":
        for i in range(1, count_tariff + 1):
            kb.button(text=f'{i}', callback_data=f'num_del_tariff_{tariffs_list[i - 1][0]}')
    elif mode == "on_tariff":
        for i in range(1, count_tariff + 1):
            kb.button(text=f'{i}', callback_data=f'turn_tariff_on_{tariffs_list[i - 1][0]}')
    elif mode == "off_tariff":
        for i in range(1, count_tariff + 1):
            kb.button(text=f'{i}', callback_data=f'turn_tariff_off_{tariffs_list[i - 1][0]}')
    kb.button(text='⬅️ Назад', callback_data='settings_tariff')
    kb.adjust(1)
    return kb.as_markup()


def settings_payment_method_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='☑️ Добавить метод', callback_data='add_method')
    kb.button(text='🗑️ Удалить метод', callback_data='del_method')
    kb.button(text='🟢 Включить метод', callback_data='on_method')
    kb.button(text='🔴 Выключить метод', callback_data='off_method')
    kb.button(text='⬅️ Назад', callback_data='payment_settings')
    kb.adjust(1)
    return kb.as_markup()

