from aiogram.utils.keyboard import InlineKeyboardBuilder

def profile_kb(mode_key=1, subscription_mode=0):
    modes = {1: 'user', 2: 'admin'}
    mode = modes[mode_key]
    kb = InlineKeyboardBuilder()
    if subscription_mode == 1: #если подписка активна
        kb.button(text='🔓 Получить доступ', callback_data='get_access')
    else: #если нет подписки
        kb.button(text='⭐ Купить подписку', callback_data='buy_subscription')
    if mode == 'admin':
        kb.button(text='⚙️ Настройки бота', callback_data='settings_bot')
    kb.button(text='⬅️ В меню', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()

def get_access_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='📱 QR-код', callback_data='get_qr')
    kb.button(text='📄 Конфигурационный файл', callback_data=f'get_config')
    kb.button(text='⬅️ В меню', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()