from aiogram.types import Message
import aiogram

# функция удаления сообщения по его айди
async def delete_last_message(last_msg_id: int, message: Message):
    if last_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=last_msg_id
            )
        except aiogram.exceptions.TelegramBadRequest as tbr:
            print("При удалении несуществующего сообщения произошла ошибка!")

#удаление предыдущих сообщений с проверкой
async def safe_delete(message: Message):
    try:
        await message.delete()
    except aiogram.exceptions.TelegramBadRequest as tbr:
        print("При удалении несуществующего сообщения произошла ошибка!: ", tbr)