from aiogram.utils.keyboard import InlineKeyboardBuilder

def instructions_kb():
    kb = InlineKeyboardBuilder() #закинуть в получение доступа
    kb.button(text=f'📖 Инструкция подключения', url='https://telegra.ph/Instrukciya-po-podklyucheniyu-VPN-WireGuard-03-23')
    kb.button(text='⬅️ Назад', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()