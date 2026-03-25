from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_settings_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='⬅️ Назад', callback_data='buy_subscription')
    kb.adjust(1)
    return kb.as_markup()
