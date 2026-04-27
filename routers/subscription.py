from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F, Bot
from aiogram.types import LabeledPrice, PreCheckoutQuery
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.menu_kb import menu_kb
from keyboards.profile_kb import get_access_kb
from keyboards.subscription_kb import subscription_kb, payment_method_kb, activate_trial_kb, sub_channel_kb
from states.menu_state import Menu
from states.payment_state import Payment
import logging
import os
from dotenv import load_dotenv
from database.db import database
from datetime import datetime, timedelta
from services.vpn_service import create_vpn_user, extend_vpn_user
import hashlib
import asyncio
import time
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.scheduler import schedule_single_subscription
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.check_sub_channel import is_user_subscribed
import aiohttp
import base64

subscription_router = Router()
load_dotenv()

TERMINAL_KEY = os.getenv("TINKOFF_TERMINAL_KEY")
PASSWORD = os.getenv("TINKOFF_PASSWORD")
SHOP_ID = os.getenv("SHOP_ID")
SECRET_KEY = os.getenv("SECRET_KEY")

@subscription_router.callback_query(F.data == "buy_subscription")
async def subscription(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    user_id = database.get_user_id(tg_id)
    trial_used = database.is_exist_trial(user_id)
    admins = [admin[2] for admin in database.get_all_admins()]
    mode_key = 2 if tg_id in admins else 1
    tariffs_list = database.get_all_tariffs()
    tariffs_text = ""
    for _, name, price, _, is_status in tariffs_list:
        if is_status:
            tariffs_text += f"— {name} — {price}₽\n"
    is_subscription = database.get_subscription_date(user_id)
    if not is_subscription: #если подписки нет или она закончилась
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

def make_tinkoff_token(params):
    excluded = ["Token", "Receipt", "Shops", "DATA"]
    params_to_sign = {k: v for k, v in params.items() if k not in excluded}
    params_to_sign["Password"] = PASSWORD
    sorted_values = [str(params_to_sign[k]) for k in sorted(params_to_sign.keys())]
    data = "".join(sorted_values)
    return hashlib.sha256(data.encode()).hexdigest()

async def create_tinkoff_pay_link(amount, order_id, description):
    params = {
        "TerminalKey": TERMINAL_KEY,
        "Amount": int(amount * 100),  # в копейках
        "OrderId": str(order_id),
        "Description": description,
    }
    params["Token"] = make_tinkoff_token(params)
    async with aiohttp.ClientSession() as session:
        async with session.post("https://securepay.tinkoff.ru/v2/Init", json=params) as resp:
            res_data = await resp.json()
            if res_data.get("Success"):
                return res_data.get("PaymentURL")
            return None

async def create_yookassa_payment(amount, order_id, description):
    auth = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()
    logging.info(f"[YOOKASSA] Create payment started | order_id={order_id} | amount={amount}")
    headers = {
        "Authorization": f"Basic {auth}",
        "Idempotence-Key": order_id,
        "Content-Type": "application/json"
    }
    json_data = {
        "amount": {
            "value": f"{amount:.2f}",  # строка с копейками
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"  # можно оставить так
        },
        "capture": True,
        "description": description
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=json_data
        ) as resp:
            data = await resp.json()
            logging.info(f"[YOOKASSA] Response: {data}")
            if "confirmation" in data:
                logging.info(f"[YOOKASSA] Payment created OK | payment_id={data.get('id')}")
                return data["confirmation"]["confirmation_url"], data["id"]
            logging.error(f"[YOOKASSA] Payment creation FAILED: {data}")
            return None, None

async def check_yookassa_payment(payment_id):
    auth = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()
    logging.info(f"[YOOKASSA] Checking payment | payment_id={payment_id}")
    headers = {
        "Authorization": f"Basic {auth}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.yookassa.ru/v3/payments/{payment_id}",
            headers=headers
        ) as resp:
            data = await resp.json()
            logging.info(f"[YOOKASSA] Check response: {data}")
            status = data.get("status")
            logging.info(f"[YOOKASSA] Payment status = {status}")
            if data.get("status") == "succeeded":
                logging.info(f"[YOOKASSA] PAYMENT SUCCESS ✅ {payment_id}")
                return True
    logging.info(f"[YOOKASSA] PAYMENT NOT CONFIRMED ❌ {payment_id}")
    return False

#сюда подставить название способа оплаты
@subscription_router.callback_query(F.data.startswith("payment_method_"))
async def payment_method(call: CallbackQuery, state: FSMContext):
    await call.answer()
    method_id = int(call.data.split("_")[2])
    data = await state.get_data()
    price_rub = int(data.get("price"))
    if method_id == 1: #юкасса
        try:
            logging.info(
                f"[PAYMENT] YooKassa selected | user={call.from_user.id} | tariff={data.get('tariff_name')} | price={price_rub}")
            await call.message.edit_text("⏳ Формируем ссылку на оплату...")
            order_id = f"yk_{call.from_user.id}_{int(time.time())}"
            description = f"VPN доступ — {data.get('tariff_name')}"
            pay_url, payment_id = await create_yookassa_payment(
                price_rub,
                order_id,
                description
            )
            logging.info(f"[PAYMENT] YooKassa response received | payment_id={payment_id} | url={pay_url}")
            if not pay_url:
                logging.error(f"[PAYMENT] YooKassa FAILED (no url) | order_id={order_id}")
                raise Exception("ЮKassa не вернула ссылку")
            await state.update_data(payment_id=payment_id)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_yk")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="buy_subscription")]
            ])
            await call.message.answer(
                f"Счет на оплату тарифа *{data.get('tariff_name')}* готов!\n\n"
                f"Сумма: {price_rub} руб.\n"
                "После оплаты нажмите «Проверить оплату».",
                reply_markup=kb,
                parse_mode="Markdown"
            )
            await safe_delete(call.message)
        except Exception as e:
            logging.error(f"[PAYMENT] YooKassa ERROR: {e}")
            await state.clear()
            await state.set_state(Menu.menu)
            bot_msg = await call.message.answer(
                "Ошибка оплаты 😞",
                reply_markup=menu_kb()
            )
            await state.update_data(last_msg_id=bot_msg.message_id)
    elif method_id == 2: #Т-банк
        try:
            await call.message.edit_text("⏳ Формируем ссылку на оплату...")
            order_id = f"inv_{call.from_user.id}_{int(time.time())}"
            description = f"VPN доступ — {data.get('tariff_name')}"
            pay_url = await create_tinkoff_pay_link(price_rub, order_id, description)
            if pay_url:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Оплатить (СБП/Карта)", url=pay_url)],
                    [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_pay_{order_id}")],
                    # Передаем order_id
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="buy_subscription")]
                ])
                await call.message.answer(
                    f"Счет на оплату тарифа *{data.get('tariff_name')}* готов!\n\n"
                    f"Сумма: {price_rub} руб.\n"
                    "После оплаты доступ активируется автоматически (в течение 1-2 минут).",
                    reply_markup=kb,
                    parse_mode="Markdown")
                await safe_delete(call.message)
            else:
                raise Exception("API Т-Банка не вернул ссылку")
        except Exception as e:
            logging.info(f'Ошибка Т-Банка: {e}')
            await state.clear()
            await state.set_state(Menu.menu)
            bot_msg = await call.message.answer(
                "Оплату невозможно произвести. Попробуйте выбрать другой способ оплаты или обратиться в поддержку:",
                reply_markup=menu_kb())
            await state.update_data(last_msg_id=bot_msg.message_id)
    else:  # если оплата через платежки из Bot-father (только иностранные карты)
        try:
            token_env_name = f"PAYMENT_TOKEN_{method_id}"
            current_token = os.getenv(token_env_name)
            price_pennies = price_rub * 100
            await call.message.edit_text("⏳ Формируем счет на оплату...")
            await call.message.answer_invoice(
                title=f"VPN доступ — {data.get('tariff_name')}",
                description=f"⚡️ Тариф: {data.get('tariff_name')}",
                payload=data.get("payload"),
                provider_token=current_token,
                currency="RUB",
                prices=[
                        LabeledPrice(label=data.get("tariff_name"), amount=price_pennies)],
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

@subscription_router.callback_query(F.data == "check_yk")
async def verify_yookassa_payment(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    logging.info(f"[VERIFY] Payment check started | user={call.from_user.id}")
    try:
        await call.answer("Проверяем оплату...")

        data = await state.get_data()
        if data.get("paid_done"):
            logging.info("[VERIFY] already processed payment, skipping")
            await call.answer("Уже оплачено ✅", show_alert=False)
            return

        payment_id = data.get("payment_id")
        if not payment_id:
            logging.warning("[VERIFY] no payment_id (already processed or expired state)")
            await call.answer("Оплата уже обработана ✅", show_alert=False)
            return
        is_paid = await check_yookassa_payment(payment_id)
        logging.info(f"[VERIFY] payment result | payment_id={payment_id} | is_paid={is_paid}")
        if is_paid:
            logging.info(f"[VERIFY] PAYMENT SUCCESS ✅ | user={call.from_user.id}")
            days = int(data.get("payload").split("_")[1])
            await process_subscription_grant(
                call.from_user.id,
                days,
                state,
                call.message,
                scheduler,
                bot)
        else:
            logging.info(f"[VERIFY] PAYMENT NOT FOUND ❌ | payment_id={payment_id}")
            await call.answer("Оплата пока не найдена. Попробуйте через минуту.", show_alert=True)
    except Exception as e:
        logging.error(f"[VERIFY] ERROR: {e}")  # ✅ FIX
        await call.answer("Ошибка проверки оплаты", show_alert=True)

async def check_tinkoff_payment(order_id):
    params = {
        "TerminalKey": TERMINAL_KEY,
        "OrderId": str(order_id),
    }
    params["Token"] = make_tinkoff_token(params)
    async with aiohttp.ClientSession() as session:
        async with session.post("https://tinkoff.ru", json=params) as resp:
            res_data = await resp.json()
            # Статус 'CONFIRMED' означает успешную оплату
            if res_data.get("Success") and res_data.get("Status") == "CONFIRMED":
                return True
            return False

async def process_subscription_grant(tg_id: int, days: int, state: FSMContext, event_source, scheduler: AsyncIOScheduler, bot: Bot):
    try:
        user_id = database.get_user_id(tg_id)
        start_date = datetime.now().replace(microsecond=0)
        loading_msg = await event_source.answer("⏳ Пожалуйста, подождите...")
        data = await state.get_data()
        tariff_id = data.get("tariff_id")
        is_subscription = data.get("is_subscription")
        if not is_subscription:  # если нет подписки еще или она закончилась
            end_date = start_date + timedelta(days=days)
            database.making_subscription(user_id, start_date, end_date, tariff_id)  # делаем запись о подписке
            await loading_msg.edit_text("🔐 Создаём VPN доступ...")
            for suffix in ["PH", "PC"]:  # создаем 2 юзера
                await asyncio.to_thread(create_vpn_user, f"{tg_id}_{suffix}", days=days)
                await asyncio.sleep(5)
            await state.update_data(paid_done=True)
            await schedule_single_subscription(scheduler, bot, tg_id, end_date)
            await loading_msg.edit_text(
                "🎉 Подписка успешно оформлена!\n\n🔐 Получите доступ к VPN:",
                reply_markup=get_access_kb())
        else:  # если есть активная подписка
            subscription_list = database.get_subscription_date(user_id)
            end_date = subscription_list[0][1] + timedelta(days=days)
            database.update_subscription(user_id, end_date)
            await loading_msg.edit_text("🔁 Продлеваем VPN доступ...")
            success_all = True
            # продление сразу 2 конфигов
            for suffix in ["PH", "PC"]:
                vpn_username = f"{tg_id}_{suffix}"
                success = await asyncio.to_thread(extend_vpn_user, vpn_username, days=days)
                await asyncio.sleep(5)
                if success is False:
                    success_all = False
            if success_all:
                await state.update_data(paid_done=True)

                await schedule_single_subscription(
                    scheduler,
                    bot,
                    tg_id,
                    end_date)
                await loading_msg.edit_text(
                    "🎉 Подписка успешно продлена!\n\n🔐 Ваш VPN доступ активен:",
                    reply_markup=get_access_kb())
            else:
                await loading_msg.edit_text(
                    "⚠️ VPN продлён, но возникла проблема с конфигами.\n"
                    "Обратитесь в поддержку.",
                    reply_markup=get_access_kb())

        logging.info(f"Пользователь {tg_id} оплатил {days} дней.")
        if database.is_exist_trial(user_id):  # если есть пробная подписка, убираем ее
            database.update_profile_trial(user_id)
        await state.set_state(Payment.access)
    except Exception as e:
        logging.error(f"[GRANT ERROR] {e}")
        try:
            await event_source.answer(
                "❌ Ошибка выдачи VPN. Обратитесь в поддержку.")
        except:
            pass

@subscription_router.callback_query(F.data.startswith("check_pay_"))
async def verify_payment(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    order_id = call.data.split("_")[2]
    is_paid = await check_tinkoff_payment(order_id)
    if is_paid:
        await call.message.delete()
        data = await state.get_data()
        days = int(data.get("payload").split("_")[1])
        await process_subscription_grant(call.from_user.id, days, state, call.message, scheduler, bot)
    else:
        await call.answer("Оплата пока не поступила. Попробуйте через минуту.", show_alert=True)

@subscription_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Если всё ок, отвечаем True
    logging.info('Статус оплаты: ок')
    await pre_checkout_query.answer(ok=True)

@subscription_router.message(F.successful_payment)  # ловит системные сообщения об оплате
async def success_payment(message: Message, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("vpn_"):
        days = int(payload.split("_")[1])
        await process_subscription_grant(message.from_user.id, days, state, message, scheduler, bot)

@subscription_router.callback_query(F.data == "free_tariff")
async def free_tariff(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await safe_delete(call.message)
    tg_id = call.from_user.id
    chat_username = "@HClearNetVPN"
    subscribed_channel = await is_user_subscribed(bot, tg_id, chat_username)  # проверка подписки на канал
    if subscribed_channel: #если уже подпискан
        bot_msg = await call.message.answer('ℹ️ Пробная подписка доступна только один раз.\n\nВы уверены, что хотите прямо сейчас активировать пробную подписку?',
                                            reply_markup=activate_trial_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)
        await state.set_state(Payment.trial)
    else: #если еще нет подписки
        bot_msg = await call.message.answer(
            f'Для активации пробной подписки необходимо подписаться на следующие каналы 👇:\n\n{chat_username}',
            reply_markup=sub_channel_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

@subscription_router.callback_query(F.data == "activate_trial_yes")
async def activate_trial_yes(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    await call.answer()
    await safe_delete(call.message)
    loading_msg = await call.message.answer("⏳ Активируем доступ, пожалуйста, подождите...")
    tg_id = call.from_user.id
    user_id = database.get_user_id(tg_id)
    database.update_profile_trial(user_id)
    start_date = datetime.now().replace(microsecond=0)
    end_date = start_date + timedelta(days=7)
    database.making_subscription(user_id, start_date, end_date, None)
    for suffix in ["PH", "PC"]:  # создаем 2 юзера
        await asyncio.to_thread(create_vpn_user, f"{tg_id}_{suffix}", days=7) #7 дней
        await asyncio.sleep(5)
    await schedule_single_subscription(scheduler, bot, tg_id, end_date)
    date_str = end_date.strftime("%d.%m.%Y")
    time_str = end_date.strftime("%H:%M")
    final_text = f"🎉 Пробная подписка активирована! Она закончится {date_str} в {time_str}.\n\nКаким способом удобно получить доступ к VPN?:"
    await loading_msg.edit_text(final_text, reply_markup=get_access_kb())
    await state.update_data(last_msg_id=loading_msg.message_id)

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
    admins = [admin[2] for admin in database.get_all_admins()]
    mode_key = 2 if tg_id in admins else 1 # является ли юзер админом
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