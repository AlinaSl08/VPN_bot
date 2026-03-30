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
    bot_msg = await call.message.answer(f"⚡ <b>ClearNET VPN</b>: Безопасность. Приватность. Стабильность."
                                        f"\nВаш личный щит в цифровом пространстве. Мы обеспечиваем максимальную защиту "
                                        f"ваших данных с помощью современных протоколов шифрования⚔️."
                                        f"\n\n✅ <b>Высокая скорость</b> — Оптимизированные серверы для работы с тяжелым контентом и онлайн-игр без задержек."
                                        f"\n✅ <b>Конфиденциальность</b> — Строгая политика отсутствия логов. Ваша активность остается только вашей."
                                        f"\n✅ <b>Безопасный доступ</b> — Надежная защита при использовании открытых Wi-Fi сетей в кафе, аэропортах и отелях."
                                        f"\n✅ <b>One-Tap Connect</b> — Подключение в один клик без сложных настроек."
                                        f"\n✅ <b>Стабильная работа</b> — 24/7 на любых устройствах."
                                        f"\n\nЗащитите свою информацию и сохраните приватность в одно касание 😍"
                                        f"\nОставайтесь в безопасности вместе с <b>ClearNET VPN</b> 😎", reply_markup=instructions_kb(), parse_mode='HTML')
    await state.update_data(last_msg_id=bot_msg.message_id)


