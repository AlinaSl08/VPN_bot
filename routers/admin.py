from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.menu_kb import menu_kb
from keyboards.admin_kb import payment_settings_kb
from states.menu_state import Menu

admin_router = Router()

ADMINS = [967760347, 1926843289] #потом берем из бд

@admin_router.callback_query(F.data == "payment_settings")
async def payment_settings(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=payment_settings_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)
