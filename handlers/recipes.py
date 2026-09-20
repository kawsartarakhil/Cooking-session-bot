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
                InlineKeyboardButton(text="👨‍🍳 Start Cooking",callback_data=f"start_cooking_{recipe_id}")
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
                InlineKeyboardButton(text="👨‍🍳 Start Cooking",callback_data=f"start_cooking_{recipe_id}")
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


# my recipes


@router.message(F.text == "📖 My Recipes")
async def my_recipes(message: Message):
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
        select id, name
        from recipes
        where created_by = $1
        order by id
        """,
        user["id"]
    )

    await conn.close()

    if not recipes:
        await message.answer(
            "📖 My Recipes\n\n"
            "You haven't created any recipes yet."
        )
        return

    keyboard = []

    for recipe in recipes:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🍳 {recipe['name']}",
                callback_data=f"my_recipe_{recipe['id']}"
            )
        ])

    await message.answer(
        "📖 Your Recipes:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


@router.callback_query(
    F.data.regexp(r"^my_recipe_\d+$")
)
async def my_recipe(callback: CallbackQuery):
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
                    text="🔙 Back",
                    callback_data="back_my_recipes"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "back_my_recipes")
async def back_my_recipes(callback: CallbackQuery):
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
        select id, name
        from recipes
        where created_by = $1
        order by id
        """,
        user["id"]
    )

    await conn.close()

    if not recipes:
        await callback.message.edit_text(
            "📖 You haven't created any recipes yet."
        )
        await callback.answer()
        return

    keyboard = []

    for recipe in recipes:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🍳 {recipe['name']}",
                callback_data=f"my_recipe_{recipe['id']}"
            )
        ])

    await callback.message.edit_text(
        "📖 Your Recipes:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()




# history


@router.message(F.text == "🕐 History")
async def history(message: Message):
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

    sessions = await conn.fetch(
        """
        select
            cs.id,
            r.name,
            cs.status,
            cs.started_at
        from cooking_sessions cs
        join recipes r
            on r.id = cs.recipe_id
        where cs.user_id = $1
        order by cs.started_at desc
        """,
        user["id"]
    )

    await conn.close()

    if not sessions:
        await message.answer(
            "🕐 History\n\n"
            "You haven't cooked any recipes yet."
        )
        return

    text = "🕐 Cooking History\n\n"

    for session in sessions:
        if session["status"] == "completed":
            status = "✅ Completed"
        elif session["status"] == "stopped":
            status = "🛑 Stopped"
        elif session["status"] == "paused":
            status = "⏸️ Paused"
        else:
            status = "🍳 Active"

        text += (
            f"🍳 {session['name']}\n"
            f"{status}\n"
            f"📅 {session['started_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )

    await message.answer(text)



# settings


@router.message(F.text == "⚙️ Settings")
async def settings(message: Message):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select notifications_enabled
        from users
        where telegram_id = $1
        """,
        message.from_user.id
    )

    await conn.close()

    if not user:
        await message.answer("❌ User not found.")
        return

    if user["notifications_enabled"]:
        status = "🔔 Notifications: ON"
        button_text = "🔕 Turn Off Notifications"
    else:
        status = "🔕 Notifications: OFF"
        button_text = "🔔 Turn On Notifications"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data="toggle_notifications"
                )
            ]
        ]
    )

    await message.answer(
        f"⚙️ Settings\n\n"
        f"{status}",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery):
    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select notifications_enabled
        from users
        where telegram_id = $1
        """,
        callback.from_user.id
    )

    if not user:
        await conn.close()
        await callback.answer("User not found.")
        return

    new_status = not user["notifications_enabled"]

    await conn.execute(
        """
        update users
        set notifications_enabled = $1
        where telegram_id = $2
        """,
        new_status,
        callback.from_user.id
    )

    await conn.close()

    if new_status:
        status = "🔔 Notifications: ON"
        button_text = "🔕 Turn Off Notifications"
    else:
        status = "🔕 Notifications: OFF"
        button_text = "🔔 Turn On Notifications"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data="toggle_notifications"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"⚙️ Settings\n\n"
        f"{status}",
        reply_markup=keyboard
    )

    await callback.answer("✅ Settings updated.")



# cooking


@router.callback_query(F.data.regexp(r"^start_cooking_\d+$"))
async def start_cooking(callback: CallbackQuery):
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

    recipe = await conn.fetchrow(
        """
        select name
        from recipes
        where id = $1
        """,
        recipe_id
    )

    if not recipe:
        await conn.close()
        await callback.answer("Recipe not found.")
        return

    steps = await conn.fetch(
        """
        select step_number, instruction, photo_file_id, timer_seconds
        from steps
        where recipe_id = $1
        order by step_number
        """,
        recipe_id
    )

    if not steps:
        await conn.close()
        await callback.answer("This recipe has no steps yet.")
        return

    session = await conn.fetchrow(
        """
        insert into cooking_sessions (
            user_id,
            recipe_id,
            current_step,
            status
        )
        values ($1, $2, 1, 'active')
        returning id
        """,
        user["id"],
        recipe_id
    )

    await conn.close()

    step = steps[0]

    text = (
        f"👨‍🍳 {recipe['name']}\n\n"
        f"Step {step['step_number']}\n"
        f"{step['instruction']}\n\n"
    )

    if step["timer_seconds"] > 0:
        minutes = step["timer_seconds"] // 60
        text += f"⏱️ Timer: {minutes} min"

    await callback.message.answer(text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Next Step",
                    callback_data=f"next_step_{session['id']}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛑 Stop Cooking",
                    callback_data=f"stop_cooking_{session['id']}"
                )
            ]
        ]
    )

    if step["photo_file_id"]:
        await callback.message.answer_photo(
            step["photo_file_id"],
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "No photo for this step.",
            reply_markup=keyboard
        )

    await callback.answer()



@router.callback_query(F.data.regexp(r"^next_step_\d+$"))
async def next_step(callback: CallbackQuery):
    session_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    session = await conn.fetchrow(
        """
        select recipe_id, current_step
        from cooking_sessions
        where id = $1
        and status = 'active'
        """,
        session_id
    )

    if not session:
        await conn.close()
        await callback.answer("Cooking session not found.")
        return

    next_step_number = session["current_step"] + 1

    step = await conn.fetchrow(
        """
        select step_number, instruction, photo_file_id, timer_seconds
        from steps
        where recipe_id = $1
        and step_number = $2
        """,
        session["recipe_id"],
        next_step_number
    )

    if not step:
        await conn.execute(
            """
            update cooking_sessions
            set status = 'completed',
                finished_at = current_timestamp
            where id = $1
            """,
            session_id
        )

        await conn.close()

        await callback.message.answer(
            "🎉 Cooking completed!\n\n"
            "✅ You finished the recipe."
        )

        await callback.answer("🎉 Recipe completed!")
        return

    await conn.execute(
        """
        update cooking_sessions
        set current_step = $1
        where id = $2
        """,
        next_step_number,
        session_id
    )

    recipe = await conn.fetchrow(
        """
        select name
        from recipes
        where id = $1
        """,
        session["recipe_id"]
    )

    await conn.close()

    text = (
        f"👨‍🍳 {recipe['name']}\n\n"
        f"Step {step['step_number']}\n"
        f"{step['instruction']}\n\n"
    )

    if step["timer_seconds"] > 0:
        minutes = step["timer_seconds"] // 60
        text += f"⏱️ Timer: {minutes} min"

    await callback.message.answer(text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Next Step",
                    callback_data=f"next_step_{session_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛑 Stop Cooking",
                    callback_data=f"stop_cooking_{session_id}"
                )
            ]
        ]
    )

    if step["photo_file_id"]:
        await callback.message.answer_photo(
            step["photo_file_id"],
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "No photo for this step.",
            reply_markup=keyboard
        )

    await callback.answer()



@router.callback_query(F.data.regexp(r"^stop_cooking_\d+$"))
async def stop_cooking(callback: CallbackQuery):
    session_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    await conn.execute(
        """
        update cooking_sessions
        set status = 'stopped',
            finished_at = current_timestamp
        where id = $1
        """,
        session_id
    )

    await conn.close()

    await callback.message.edit_text(
        "🛑 Cooking stopped.\n\n"
        "Your session was saved in History."
    )

    await callback.answer("Cooking stopped.")