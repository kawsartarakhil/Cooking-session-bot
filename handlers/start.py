from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from connections import get_connection
from keyboards.reply import user_menu, admin_menu


router = Router()


@router.message(CommandStart())
async def start(message: Message):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        insert into users (telegram_id, username, first_name)
        values ($1, $2, $3)
        on conflict (telegram_id)
        do update set
            username = $2,
            first_name = $3
        returning role
        """,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    await conn.close()

    if user["role"] == "admin":
        keyboard = admin_menu
    else:
        keyboard = user_menu

    await message.answer(f"👋 Welcome, {message.from_user.first_name}!\n\n""🍳 Welcome to CookMate!",reply_markup=keyboard)
