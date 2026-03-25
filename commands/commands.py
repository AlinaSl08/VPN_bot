from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message, CallbackQuery
from utils.delete_last_message import delete_last_message, safe_delete
from states.menu_state import Menu
from keyboards.menu_kb import menu_kb
from database.db import database

commands_router = Router()

@commands_router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    tg_id = str(message.chat.id)
    if not database.is_exist_user(tg_id):
        database.add_new_user(tg_id)
        user_id = database.get_user_id(tg_id)
        database.create_profile(user_id)
        bot_msg = await message.answer("👋 Добро пожаловать!\n\n🔐 VPN доступ\n\nБезопасный интернет без ограничений\nВысокая скорость и стабильное соединение ⚡\n\nВыберите действие 👇:", reply_markup=menu_kb())
        await state.set_state(Menu.menu)
        await state.update_data(last_msg_id=bot_msg.message_id)
    else:
        bot_msg = await message.answer(
            "👋 С возвращением!\n\nВыберите действие 👇:",
            reply_markup=menu_kb())
        await state.set_state(Menu.menu)
        await state.update_data(last_msg_id=bot_msg.message_id)

@commands_router.message(Command("help"))
async def help(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🤖 Список доступных команд бота: \n/start\n/menu\n/help")



@commands_router.message(Command("menu"))
async def menu(message: Message, state: FSMContext):
    await state.clear()
    bot_msg = await message.answer("Выберите действие:", reply_markup=menu_kb())
    await state.set_state(Menu.menu)
    await state.update_data(last_msg_id=bot_msg.message_id)


async def set_bot_commands(bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Показать меню"),
        BotCommand(command="help", description="Список команд"),
    ]
    await bot.set_my_commands(commands) # отправляем телеграм список команд бота



@commands_router.message(F.text, StateFilter(Menu.menu))
async def ignore_menu(message: Message, state: FSMContext):
    current_state = await state.get_state()
    # Если пользователь находится в состоянии меню
    if current_state != "general_chat":
        data = await state.get_data()
        menu_msg_id = data.get("last_msg_id")
        # Удаляем старое сообщение бота
        if menu_msg_id:
            await delete_last_message(menu_msg_id, message)
        bot_msg = await message.answer(
            "Пожалуйста, выберите действие с помощью кнопок ниже 👇", reply_markup=menu_kb())
        # Сохраняем новый id
        await state.update_data(last_msg_id=bot_msg.message_id)