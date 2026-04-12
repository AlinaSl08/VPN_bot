from aiogram.utils.keyboard import InlineKeyboardBuilder

def instructions_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='⬅️ Назад', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()