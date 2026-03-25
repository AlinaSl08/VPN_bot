from aiogram.utils.keyboard import InlineKeyboardBuilder

def menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='⭐ Купить подписку', callback_data='buy_subscription')
    kb.button(text='👤 Профиль', callback_data='profile')
    kb.button(text='ℹ️ О сервисе', callback_data='about_the_service')
    kb.button(text='👨‍💻 Поддержка', callback_data='support')
    kb.adjust(2, 2)
    return kb.as_markup()