from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.inline import admin_panel,category_menu
from connections import get_connection
from aiogram.fsm.context import FSMContext
from states.category_states import CategoryStates


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

@router.callback_query(F.data == "admin_categories")
async def categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📂 Categories\n\n"
        "Choose an option:",
        reply_markup=category_menu
    )

    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


#categories
@router.callback_query(F.data == "add_category")
async def add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryStates.waiting_for_name)

    await callback.message.answer(
        "➕ Add Category\n\n"
        "Enter the category name:"
    )

    await callback.answer()


@router.message(CategoryStates.waiting_for_name)
async def save_category(message: Message, state: FSMContext):
    name = message.text.strip()

    if not name:
        await message.answer("❌ Category name cannot be empty.")
        return

    conn = await get_connection()

    try:
        await conn.execute(
            """
            insert into categories (name)
            values ($1)
            """,
            name
        )

        await message.answer(
            f"✅ Category '{name}' added successfully!"
        )

        await state.clear()

    except Exception:
        await message.answer(
            "❌ This category may already exist."
        )

    finally:
        await conn.close()

@router.callback_query(F.data == "view_categories")
async def view_categories(callback: CallbackQuery):
    conn = await get_connection()

    categories = await conn.fetch(
        """
        select id, name
        from categories
        order by id
        """
    )

    await conn.close()

    if not categories:
        await callback.message.edit_text(
            "📋 Categories\n\n"
            "There are no categories yet.",
            reply_markup=category_menu
        )
        await callback.answer()
        return

    text = "📋 Categories\n\n"

    for category in categories:
        text += f"{category['id']}. {category['name']}\n"

    await callback.message.edit_text(
        text,
        reply_markup=category_menu
    )

    await callback.answer()


@router.callback_query(F.data == "admin_panel")
async def back_to_admin_panel(callback: CallbackQuery):
    await callback.message.answer(
        "👑 Admin Panel\n\n"
        "Choose an option:",
        reply_markup=admin_panel
    )

    await callback.answer()