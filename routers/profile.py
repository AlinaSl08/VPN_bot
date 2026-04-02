from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.profile_kb import profile_kb, get_access_kb
from states.menu_state import Menu
from keyboards.menu_kb import menu_kb
from states.payment_state import Payment
from database.db import database
from services.vpn_service import get_config, generate_qr_image
from aiogram.types import BufferedInputFile
import logging

profile_router = Router()

@profile_router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    user_id = database.get_user_id(tg_id)
    trial_used = database.is_exist_trial(user_id)
    trial = '🟡 Использован' if not trial_used else '🟢 Доступен'
    subscription = database.get_subscription_date(user_id)
    if subscription:
        status_subscription = '🔵 Активна'
        start_date = subscription[0][0].strftime("%d.%m.%Y")
        end_date = subscription[0][1].strftime("%d.%m.%Y")
        period_subscription = f'{start_date} - {end_date}'
        subscription_mode = 1
    else:
        status_subscription =  '🔴 Не активна'
        period_subscription = '???'
        subscription_mode = 0
    admins = [admin[2] for admin in database.get_all_admins()]
    mode_key = 2 if tg_id in admins else 1
    bot_msg = await call.message.answer(
        f'👤 Ваш профиль:\n\n🆔 ID: {tg_id}\n\n🎫 Статус подписки: {status_subscription}'
        f'\n\n📅 Период подписки: {period_subscription}\n\n⏳ Пробный период: {trial}',
        reply_markup=profile_kb(mode_key, subscription_mode))
    await state.update_data(last_msg_id=bot_msg.message_id)

#получение доступа
@profile_router.callback_query(F.data == "get_access")
async def get_access(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer(
        "🔐 Каким способом удобно получить доступ к VPN?: 👇",
        reply_markup=get_access_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(Payment.access)

#получение доступа по QR, запросы к серверу
@profile_router.callback_query(F.data == "get_qr")
async def send_qr(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    suffixes  = ["PH", "PC"]
    try:
        await call.message.answer("⏳ Генерируем QR-коды для ваших устройств (1 и 2)...")
        for suffix in suffixes:
            vpn_username = f"{tg_id}_{suffix}"
            config = get_config(vpn_username)
            print(config)
            if config:
                qr_image = generate_qr_image(config)
                file_data = qr_image.getvalue()
                file = BufferedInputFile(file_data, filename=f"qr_{suffix}.png")
                await call.message.answer_photo(file,
                    caption=f"✅ QR-код \n\n⚠️ Используйте этот код строго на одном устройстве.")
            else:
                await call.message.answer(f"❌ Конфиг {suffix} не найден. Обратитесь в поддержку.")
        bot_msg = await call.message.answer('Выберите действие:',reply_markup=menu_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)
    except Exception as e:
        await call.message.answer("❌ Ошибка при получении доступа. Обратитесь в поддержку")
        logging.info(f'Ошибка при создании QR: {e}')
    await state.clear()
    await state.set_state(Menu.menu)

#получение доступа через конфиг, запросы к серверу
@profile_router.callback_query(F.data == "get_config")
async def send_config(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    suffixes = ["PH", "PC"]
    try:
        await call.message.answer("⏳ Подготавливаем файлы конфигурации...")
        for suffix in suffixes:
            vpn_username = f"{tg_id}_{suffix}"
            config = get_config(vpn_username)
            if config:
                file = BufferedInputFile(config.encode(), filename=f"vpn_{suffix}.conf")
                await call.message.answer_document(file,
                    caption=f"📄 Файл конфигурации \n\n⚠️ Используйте этот файл строго на одном устройстве.")
        bot_msg = await call.message.answer('Выберите действие:',
                                            reply_markup=menu_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)
    except Exception as e:
        logging.info(f"Ошибка в отправке конфига: {e}")
        await call.message.answer("❌ Ошибка при загрузке файлов.")
    await state.clear()
    await state.set_state(Menu.menu)


@profile_router.message(Payment.access)
async def access_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    bot_msg = await message.answer(
        "Пожалуйста, выберите способ получения доступа с помощью кнопок ниже 👇",
        reply_markup=get_access_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)