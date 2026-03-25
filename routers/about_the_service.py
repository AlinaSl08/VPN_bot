from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from utils.delete_last_message import safe_delete
from keyboards.about_the_service_kb import instructions_kb

about_the_service_router = Router()

@about_the_service_router.callback_query(F.data == "about_the_service")
async def subscription(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    await state.clear()
    bot_msg = await call.message.answer(f"⚡ <b>ClearNET VPN</b>: Безопасность. Анонимность. Скорость."
                                        f"\nНадежный спутник в мире интернета. Защищаем ваши данные с помощью современных протоколов шифрования⚔️."
                                        f"\n\n✅ Все летает: Быстрые серверы для Instagram, YouTube и игр."
                                        f"\n✅ Полная анонимность: никаких логов и отслеживания."
                                        f"\n✅ <b>Global Access</b> — Обходи любые ограничения и пользуйся любимыми соцсетями."
                                        f"\n✅ <b>One-Tap Connect</b> — Подключение в один клик без сложных настроек."
                                        f"\n✅ Стабильная работа 24/7 на любых устройствах.\n\nТвоя цифровая свобода нужна и важна 😍"
                                        f"\nЗабудь о блокировках и медленном интернете😎", reply_markup=instructions_kb(), parse_mode='HTML')
    await state.update_data(last_msg_id=bot_msg.message_id)


