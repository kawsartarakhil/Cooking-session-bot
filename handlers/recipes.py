from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from connections import get_connection

router = Router()


# recipes  for  users and admin

@router.message(F.text == "🍳 Recipes")
async def recipes(message: Message):
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
        await message.answer(
            "🍳 Recipes\n\n"
            "There are no categories yet."
        )
        return

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"user_recipe_category_{category['id']}"
            )
        ])

    await message.answer(
        "📂 Choose a category:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


# choose category

@router.callback_query(F.data.regexp(r"^user_recipe_category_\d+$"))
async def user_recipe_category(callback: CallbackQuery):
    category_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    recipes = await conn.fetch(
        """
        select id, name
        from recipes
        where category_id = $1
        order by id
        """,
        category_id
    )

    await conn.close()

    if not recipes:
        await callback.message.edit_text(
            "❌ No recipes available in this category.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Back",
                            callback_data="user_recipes"
                        )
                    ]
                ]
            )
        )

        await callback.answer()
        return

    keyboard = []

    for recipe in recipes:
        keyboard.append([
            InlineKeyboardButton(
                text=recipe["name"],
                callback_data=f"user_recipe_{recipe['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="user_recipes"
        )
    ])

    await callback.message.edit_text(
        "🍳 Choose a recipe:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


#categories
@router.callback_query(F.data == "user_recipes")
async def user_recipes_back(callback: CallbackQuery):
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
            "🍳 There are no categories yet."
        )
        await callback.answer()
        return

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"user_recipe_category_{category['id']}"
            )
        ])

    await callback.message.edit_text(
        "📂 Choose a category:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


# recipe details

@router.callback_query( F.data.regexp(r"^user_recipe_\d+$"))
async def user_recipe(callback: CallbackQuery):
    recipe_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    recipe = await conn.fetchrow(
        """
        select
            r.name,
            r.description,
            r.cooking_time_minutes,
            r.difficulty,
            r.servings,
            c.name as category_name
        from recipes r
        join categories c
            on c.id = r.category_id
        where r.id = $1
        """,
        recipe_id
    )

    ingredients = await conn.fetch(
        """
        select name, amount, unit
        from ingredients
        where recipe_id = $1
        order by id
        """,
        recipe_id
    )

    steps = await conn.fetch(
        """
        select step_number, instruction, timer_seconds
        from steps
        where recipe_id = $1
        order by step_number
        """,
        recipe_id
    )

    await conn.close()

    if not recipe:
        await callback.answer("Recipe not found.")
        return

    text = (
        f"🍳 {recipe['name']}\n\n"
        f"📂 Category: {recipe['category_name']}\n"
        f"📝 {recipe['description']}\n"
        f"🕒 Cooking time: {recipe['cooking_time_minutes']} min\n"
        f"⭐ Difficulty: {recipe['difficulty']}\n"
        f"🍽️ Servings: {recipe['servings']}\n\n"
        f"🥕 Ingredients:\n"
    )

    for ingredient in ingredients:
        unit = ingredient["unit"] or ""
        text += (
            f"• {ingredient['name']} "
            f"{ingredient['amount']} {unit}\n"
        )

    text += "\n👨‍🍳 Steps:\n"

    for step in steps:
        text += (
            f"\n{step['step_number']}. "
            f"{step['instruction']}"
        )

        if step["timer_seconds"] > 0:
            minutes = step["timer_seconds"] // 60
            text += f" ⏱️ {minutes} min"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton( text="❤️ Add to Favorites", callback_data=f"add_favorite_{recipe_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Back",callback_data="user_recipes")
            ]
    ]
)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# add favorite


@router.callback_query(F.data.regexp(r"^add_favorite_\d+$"))
async def add_favorite(callback: CallbackQuery):
    recipe_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    recipe = await conn.fetchrow(
        """
        select id
        from recipes
        where id = $1
        """,
        recipe_id
    )

    if not recipe:
        await conn.close()
        await callback.answer("Recipe not found.")
        return

    user = await conn.fetchrow(
        """
        select id
        from users
        where telegram_id = $1
        """,
        callback.from_user.id
    )

    if not user:
        await conn.close()
        await callback.answer("User not found.")
        return

    await conn.execute(
        """
        insert into favorites (user_id, recipe_id)
        values ($1, $2)
        on conflict (user_id, recipe_id)
        do nothing
        """,
        user["id"],
        recipe_id
    )

    await conn.close()

    await callback.answer(
        "❤️ Recipe added to favorites!"
    )


# favorites


@router.message(F.text == "❤️ Favorites")
async def favorites(message: Message):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select id
        from users
        where telegram_id = $1
        """,
        message.from_user.id
    )

    if not user:
        await conn.close()
        await message.answer("❌ User not found.")
        return

    recipes = await conn.fetch(
        """
        select r.id, r.name
        from recipes r
        join favorites f
            on f.recipe_id = r.id
        where f.user_id = $1
        order by f.created_at desc
        """,
        user["id"]
    )

    await conn.close()

    if not recipes:
        await message.answer(
            "❤️ Favorites\n\n"
            "You don't have any favorite recipes yet."
        )
        return

    keyboard = []

    for recipe in recipes:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🍳 {recipe['name']}",
                callback_data=f"favorite_recipe_{recipe['id']}"
            )
        ])

    await message.answer(
        "❤️ Your Favorite Recipes:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


@router.callback_query(F.data.regexp(r"^favorite_recipe_\d+$"))
async def favorite_recipe(callback: CallbackQuery):
    recipe_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    recipe = await conn.fetchrow(
        """
        select
            r.name,
            r.description,
            r.cooking_time_minutes,
            r.difficulty,
            r.servings,
            c.name as category_name
        from recipes r
        join categories c
            on c.id = r.category_id
        where r.id = $1
        """,
        recipe_id
    )

    ingredients = await conn.fetch(
        """
        select name, amount, unit
        from ingredients
        where recipe_id = $1
        order by id
        """,
        recipe_id
    )

    steps = await conn.fetch(
        """
        select step_number, instruction, timer_seconds
        from steps
        where recipe_id = $1
        order by step_number
        """,
        recipe_id
    )

    await conn.close()

    if not recipe:
        await callback.answer("Recipe not found.")
        return

    text = (
        f"🍳 {recipe['name']}\n\n"
        f"📂 Category: {recipe['category_name']}\n"
        f"📝 {recipe['description']}\n"
        f"🕒 Cooking time: {recipe['cooking_time_minutes']} min\n"
        f"⭐ Difficulty: {recipe['difficulty']}\n"
        f"🍽️ Servings: {recipe['servings']}\n\n"
        f"🥕 Ingredients:\n"
    )

    for ingredient in ingredients:
        unit = ingredient["unit"] or ""

        text += (
            f"• {ingredient['name']} "
            f"{ingredient['amount']} {unit}\n"
        )

    text += "\n👨‍🍳 Steps:\n"

    for step in steps:
        text += (
            f"\n{step['step_number']}. "
            f"{step['instruction']}"
        )

        if step["timer_seconds"] > 0:
            minutes = step["timer_seconds"] // 60
            text += f" ⏱️ {minutes} min"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑️ Remove from Favorites",
                    callback_data=f"remove_favorite_{recipe_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="back_favorites"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()

@router.callback_query(
    F.data.regexp(r"^remove_favorite_\d+$")
)
async def remove_favorite(callback: CallbackQuery):
    recipe_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select id
        from users
        where telegram_id = $1
        """,
        callback.from_user.id
    )

    if not user:
        await conn.close()
        await callback.answer("User not found.")
        return

    await conn.execute(
        """
        delete from favorites
        where user_id = $1
        and recipe_id = $2
        """,
        user["id"],
        recipe_id
    )

    await conn.close()

    await callback.answer(
        "🗑️ Removed from favorites."
    )

    await callback.message.delete()


@router.callback_query(F.data == "back_favorites")
async def back_favorites(callback: CallbackQuery):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select id
        from users
        where telegram_id = $1
        """,
        callback.from_user.id
    )

    if not user:
        await conn.close()
        await callback.answer("User not found.")
        return

    recipes = await conn.fetch(
        """
        select r.id, r.name
        from recipes r
        join favorites f
            on f.recipe_id = r.id
        where f.user_id = $1
        order by f.created_at desc
        """,
        user["id"]
    )

    await conn.close()

    if not recipes:
        await callback.message.edit_text(
            "❤️ You don't have any favorite recipes yet."
        )
        await callback.answer()
        return

    keyboard = []

    for recipe in recipes:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🍳 {recipe['name']}",
                callback_data=f"favorite_recipe_{recipe['id']}"
            )
        ])

    await callback.message.edit_text(
        "❤️ Your Favorite Recipes:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()