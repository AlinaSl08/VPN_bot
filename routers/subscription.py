from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import LabeledPrice, PreCheckoutQuery
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.menu_kb import menu_kb
from keyboards.profile_kb import get_access_kb
from keyboards.subscription_kb import subscription_kb, payment_method_kb, activate_trial_kb
from states.menu_state import Menu
from states.payment_state import Payment
import logging
import os
from dotenv import load_dotenv
from database.db import database
from datetime import datetime, timedelta

subscription_router = Router()
load_dotenv()

@subscription_router.callback_query(F.data == "buy_subscription")
async def subscription(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    user_id = database.get_user_id(tg_id)
    trial_used = database.is_exist_trial(user_id)
    admins = [admin[1] for admin in database.get_all_admins()]
    mode_key = 2 if tg_id in admins else 1
    tariffs_list = database.get_all_tariffs()
    tariffs_text = ""
    for _, name, price, _, is_status in tariffs_list:
        if is_status:
            tariffs_text += f"— {name} — {price}₽\n"
    is_subscription = database.get_subscription_date(user_id)
    if not is_subscription: #если подписки нет
        bot_msg = await call.message.answer(f"🔐 Подписка на VPN\n\nБезопасный и стабильный доступ к интернету без ограничений 🌐"
                              "\n\n💡 Что входит:\n\n— Подключение до 2 устройств\n— Высокая скорость"
                              f"\n— Простая настройка (QR или файл)\n— Поддержка при необходимости\n\n📅 Тарифы:\n\n{tariffs_text}\n"
                              "Выберите тариф 👇:", reply_markup=subscription_kb(mode_key=mode_key, trial_used=trial_used, is_subscription=False))
        await state.update_data(last_msg_id=bot_msg.message_id, is_subscription=False)
    else:
        start_date = is_subscription[0][0].strftime("%d.%m.%Y")
        end_date = is_subscription[0][1].strftime("%d.%m.%Y")
        period_subscription = f'{start_date} - {end_date}'
        bot_msg = await call.message.answer(f"💡 У вас есть активная подписка.\n\n📅 Период подписки: {period_subscription}"
                                            f"\n\n Вы можете продлить дату подписки, докупив еще дни 👇:",
                                            reply_markup=subscription_kb(mode_key=mode_key, trial_used=trial_used, is_subscription=True))
        await state.update_data(last_msg_id=bot_msg.message_id, is_subscription=True)
    await state.set_state(Payment.tariff)

@subscription_router.callback_query(F.data.startswith("buy_"))
async def buy_subscription(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tariff_id= int(call.data.split("_")[1]) #айди тарифа
    tariffs_list = database.get_all_tariffs() #активные тарифы
    tariffs = {t_id: (name, price, duration_day) for t_id, name, price, duration_day, _ in tariffs_list}
    tariff_data = tariffs.get(tariff_id)
    if not tariff_data:
        await state.clear()
        await state.set_state(Menu.menu)
        bot_msg = await call.message.answer('Извините, этот тариф больше не доступен. 😞',
                                            reply_markup=menu_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)
        return
    try:
        name, price, days = tariff_data
        await state.update_data(tariff_name=name, price=price, payload=f"vpn_{days}_days", tariff_id=tariff_id)
        bot_msg = await call.message.answer(f'Вы выбрали тариф на {name} за {price} рублей.'
                                  f'\n\nВыберите способ оплаты 👇:', reply_markup=payment_method_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)
        await state.set_state(Payment.method)
    except Exception as e:
        logging.info(f'Не удалось оформить подписку. Ошибка: {e}')
        await state.clear()
        await state.set_state(Menu.menu)
        bot_msg = await call.message.answer('Не удалось оформить подписку. Обратитесь в поддержку 😞', reply_markup=menu_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

#сюда подставить название способа оплаты
@subscription_router.callback_query(F.data.startswith("payment_method_"))
async def payment_method(call: CallbackQuery, state: FSMContext):
    await call.answer()
    method_id = int(call.data.split("_")[2])
    token_env_name = f"PAYMENT_TOKEN_{method_id}"
    current_token = os.getenv(token_env_name)
    data = await state.get_data()
    price = int(data.get("price")) * 100
    try:
        await call.message.edit_text("⏳ Формируем счет на оплату...")
        await call.message.answer_invoice(
            title=f"VPN доступ — {data.get('tariff_name')}",
            description=f"⚡️ Тариф: {data.get('tariff_name')}",
            payload=data.get("payload"),
            provider_token=current_token,
            currency="RUB",
            prices=[
                    LabeledPrice(label=data.get("tariff_name"), amount=price)],
            start_parameter=data.get("payload"),
            is_test=True) #для тестов, потом убрать!!!!!!!
        await safe_delete(call.message)
    except Exception as e:
        logging.info(f"Ошибка оплаты: {e}")
        await state.clear()
        await state.set_state(Menu.menu)
        bot_msg = await call.message.answer("Оплату невозможно произвести. Попробуйте выбрать другой способ оплаты или обратиться в поддержку:",
                                            reply_markup=menu_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

@subscription_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Если всё ок, отвечаем True
    logging.info('Статус оплаты: ок')
    await pre_checkout_query.answer(ok=True)

@subscription_router.message(F.successful_payment)  # ловит системные сообщения об оплате
async def success_payment(message: Message, state: FSMContext):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    if payload.startswith("vpn_"):
        days = int(payload.split("_")[1])
        tg_id = message.from_user.id
        user_id = database.get_user_id(tg_id)
        start_date = datetime.now().replace(microsecond=0)
        end_date = start_date + timedelta(days=days)
        data = await state.get_data()
        tariff_id = data.get("tariff_id")
        is_subscription = data.get("is_subscription")
        if not is_subscription:
            database.making_subscription(user_id, start_date, end_date, tariff_id) #делаем запись о подписке
        else:
            subscription_list = database.get_subscription_date(user_id)
            new_end_date = subscription_list[0][1] + timedelta(days=days)

            database.update_subscription(user_id, new_end_date)
        logging.info(f"Пользователь {tg_id} оплатил {days} дней.")
    bot_msg = await message.answer(
        "🎉 Поздравляем! Оплата прошла успешно.\n🔐 Каким способом удобно получить доступ к VPN?:",
        reply_markup=get_access_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(Payment.access)

@subscription_router.callback_query(F.data == "free_tariff")
async def free_tariff(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer('ℹ️ Пробная подписка доступна только один раз.\n\nВы уверены, что хотите прямо сейчас активировать пробную подписку?',
                                        reply_markup=activate_trial_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(Payment.trial)

@subscription_router.callback_query(F.data == "activate_trial_yes")
async def activate_trial_yes(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    user_id = database.get_user_id(tg_id)
    database.update_profile_trial(user_id)
    start_date = datetime.now().replace(microsecond=0)
    end_date = start_date + timedelta(days=7)
    database.making_subscription(user_id, start_date, end_date, None)
    date_str = end_date.strftime("%d.%m.%Y")
    time_str = end_date.strftime("%H:%M")
    bot_msg = await call.message.answer(f"🎉 Пробная подписка активирована! Она закончится {date_str} в {time_str}."
                                        f"\n\nКаким способом удобно получить доступ к VPN?:", reply_markup=get_access_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

@subscription_router.callback_query(F.data == "activate_trial_no")
async def activate_trial_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Возвращаемся в меню...")
    await safe_delete(call.message)
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=menu_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

@subscription_router.message(Payment.tariff)
async def tariff_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    tg_id = message.from_user.id
    user_id = database.get_user_id(tg_id)
    trial_used = database.is_exist_trial(user_id)
    admins = [admin[1] for admin in database.get_all_admins()]
    if tg_id in admins:  # является ли юзер админом
        mode_key = 2
    else:
        mode_key = 1
    bot_msg = await message.answer(
        "Пожалуйста, выберите тариф с помощью кнопок ниже 👇",
        reply_markup=subscription_kb(mode_key=mode_key, trial_used=trial_used))
    await state.update_data(last_msg_id=bot_msg.message_id)

@subscription_router.message(Payment.method)
async def method_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    bot_msg = await message.answer(
        "Пожалуйста, выберите способ оплаты с помощью кнопок ниже 👇",
        reply_markup=payment_method_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

@subscription_router.message(Payment.trial)
async def trial_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    bot_msg = await message.answer(
        "Пожалуйста, выберите подтвердите действие с помощью кнопок ниже 👇",
        reply_markup=activate_trial_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)