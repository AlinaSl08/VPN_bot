from aiogram.types import  CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from utils.delete_last_message import safe_delete
from keyboards.menu_kb import menu_kb
from states.menu_state import Menu


menu_router = Router()

#--ВЕРНУТЬСЯ В МЕНЮ--
@menu_router.callback_query(F.data == "cancel_menu")
async def cancel_menu(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    await state.clear()
    await call.answer("Возвращаемся в меню...")
    bot_msg = await call.message.answer("🔐 Главное меню\n\nВыберите действие 👇:", reply_markup=menu_kb())
    await state.set_state(Menu.menu)
    await state.update_data(last_msg_id=bot_msg.message_id)