from aiogram.utils.keyboard import InlineKeyboardBuilder

def cancel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='⬅️ В меню', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()