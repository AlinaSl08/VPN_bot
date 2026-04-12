from datetime import datetime
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from database.db import database
from datetime import timedelta
import logging
from apscheduler.triggers.interval import IntervalTrigger


def get_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='⭐ Продлить подписку', callback_data='buy_subscription')
    kb.button(text='⬅️ В меню', callback_data='cancel_menu')
    kb.adjust(1)
    return kb.as_markup()

async def send_reminder_before(bot: Bot, tg_id):
    try:
        text = f"⏰ Ваша подписка заканчивается сегодня! Можете ее продлить 👇:"
        await bot.send_message(chat_id=int(tg_id), text=text, reply_markup=get_keyboard())
    except Exception as e:
        logging.info(f"Ошибка отправки {tg_id}: {e}")

async def send_reminder(bot: Bot, tg_id):
    try:
        text = f"⏰ Ваша подписка закончилась! Можете ее продлить 👇:"
        await bot.send_message(chat_id=int(tg_id), text=text, reply_markup=get_keyboard())
    except Exception as e:
        logging.info(f"Ошибка отправки {tg_id}: {e}")

# проверка на просроченную задачу
async def check_overdue_subscriptions(bot: Bot):
    try:
        now = datetime.now()
        users_data = database.get_all_user()
        for user_id, tg_id, _, _ in users_data:
            subscription = database.get_subscription_date(user_id)
            if subscription:
                end_date = subscription[0][1]
                if end_date.strftime('%Y-%m-%d %H:%M') == now.strftime('%Y-%m-%d %H:%M'):
                    database.overdue_subscription(user_id)
                    await send_reminder(bot, tg_id)
    except Exception as e:
        logging.info(f'Ошибка проверки статуса подписки: {e}')

async def add_overdue_checker(scheduler, bot):
    scheduler.add_job(
        check_overdue_subscriptions,
        trigger=IntervalTrigger(seconds=60),
        id="check_overdue_subscriptions",
        args=[bot])

async def schedule_single_subscription(scheduler: AsyncIOScheduler, bot: Bot, tg_id, date_end):
    #напоминания приходят за 2 часа до окончания подписки
    now = datetime.now()
    #если дата окончания равна сегодняшней
    if date_end.date() == now.date():
        reminder_time = date_end - timedelta(hours=2)
        if reminder_time > datetime.now():
            scheduler.add_job(
                        send_reminder_before,
                        trigger=DateTrigger(run_date=reminder_time),
                        args=[bot, tg_id],
                        id=f"rem_exact_{tg_id}",
                        replace_existing=True)
        else: #если время прошло, сразу вызывается функция
            await send_reminder_before(bot, tg_id)

async def schedule_all_subscriptions(scheduler: AsyncIOScheduler, bot: Bot):
    users_data = database.get_all_user() #список всех юзеров
    for user_id, tg_id, _, _ in users_data:
        if database.get_subscription_date(user_id): #если подписка есть
            date_end = database.get_subscription_date(user_id)[0][1]
            await schedule_single_subscription(scheduler, bot, tg_id, date_end)

async def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    await schedule_all_subscriptions(scheduler, bot)
    # проверка каждую минуту на просрочку
    await add_overdue_checker(scheduler, bot)
    if not scheduler.running:  # если не запущен
        scheduler.start()
    return scheduler