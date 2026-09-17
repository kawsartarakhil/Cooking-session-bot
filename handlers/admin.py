from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from keyboards.inline import admin_panel
from connections import get_connection


router = Router()


@router.message(F.text == "👑 Admin Panel")
async def admin_panel_handler(message: Message):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select role
        from users
        where telegram_id = $1
        """,
        message.from_user.id
    )

    await conn.close()

    if not user or user["role"] != "admin":
        await message.answer("❌ You don't have permission.")
        return

    await message.answer(
        "👑 Admin Panel\n\n"
        "Choose an option:",
        reply_markup=admin_panel
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

