from aiogram import Bot

async def is_user_subscribed(bot: Bot, user_id: int, chat_id: str = "@HClearNetVPN") -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        # если статус не 'left' и не 'kicked', значит пользователь в канале
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False