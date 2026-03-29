from aiogram.types import CallbackQuery
from aiogram import Router, F
from utils.delete_last_message import safe_delete
from keyboards.support_kb import cancel_kb
from aiogram.types import LinkPreviewOptions

support_router = Router()

@support_router.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    await call.answer()
    await safe_delete(call.message)
    support_text = ('🆘 <b>Техническая поддержка сервиса</b>\n\n'
                    'По вопросам некорректной работы услуг или финансовых операций, пожалуйста, свяжитесь с оператором:'
                    '\n\n🔗 <a href="https://t.me/ClearNET_VPN_Help">Написать менеджеру</a>\n🔗 <a href="https://t.me/HClearNetVPN">Канал с новостями</a>'
                    '\n\n<b>Режим работы:</b> 24/7.')
    await call.message.answer(support_text,
                              parse_mode="HTML",
                              link_preview_options=LinkPreviewOptions(is_disabled=True),
                              reply_markup=cancel_kb())