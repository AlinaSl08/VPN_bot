import asyncio
import logging
from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from commands.commands import set_bot_commands
from routers.subscription import subscription_router
from routers.menu import menu_router
from routers.admin import admin_router
from routers.support import support_router
from routers.profile import profile_router
from commands.commands import commands_router
from routers.about_the_service import about_the_service_router
from utils.scheduler import setup_scheduler

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

#--ЗАПУСК БОТА--
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
    main_router = Router()
    dp.include_router(main_router)
    dp.include_router(subscription_router)
    dp.include_router(commands_router)
    dp.include_router(menu_router)
    dp.include_router(admin_router)
    dp.include_router(about_the_service_router)
    dp.include_router(support_router)
    dp.include_router(profile_router)
    await set_bot_commands(bot)
    scheduler = await setup_scheduler(bot)
    await dp.start_polling(bot, scheduler=scheduler)

if __name__ == "__main__":
    asyncio.run(main())