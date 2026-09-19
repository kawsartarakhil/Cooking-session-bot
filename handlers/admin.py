from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery, InlineKeyboardMarkup
from keyboards.inline import admin_panel, category_menu, recipe_admin_menu, finish_ingredients, finish_steps
from connections import get_connection
from aiogram.fsm.context import FSMContext
from states.category_states import CategoryStates
from states.recipe_states import RecipeStates

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


# categories

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


# recipe

@router.callback_query(F.data == "admin_recipes")
async def admin_recipes(callback: CallbackQuery):
    await callback.message.edit_text(
        "🍳 Recipes\n\n"
        "Choose an option:",
        reply_markup=recipe_admin_menu
    )

    await callback.answer()


@router.callback_query(F.data == "add_recipe")
async def add_recipe(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RecipeStates.waiting_for_name)

    await callback.message.answer(
        "➕ Add Recipe\n\n"
        "Enter the recipe name:"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_name)
async def recipe_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(RecipeStates.waiting_for_description)

    await message.answer(
        "Enter the recipe description:"
    )


@router.message(RecipeStates.waiting_for_description)
async def recipe_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)

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
        await message.answer("❌ There are no categories yet.")
        return

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"recipe_category_{category['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await state.set_state(RecipeStates.waiting_for_category)

    await message.answer(
        "📂 Choose the recipe category:",
        reply_markup=keyboard
    )


@router.callback_query(
    F.data.startswith("recipe_category_"),
    RecipeStates.waiting_for_category
)
async def save_recipe_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])

    await state.update_data(category_id=category_id)

    await state.set_state(RecipeStates.waiting_for_time)

    await callback.message.edit_text(
        "🕒Enter cooking time in minutes:"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_time)
async def recipe_time(message: Message, state: FSMContext):
    try:
        time = int(message.text)

        if time <= 0:
            await message.answer("❌ Enter a number greater than 0.")
            return

    except ValueError:
        await message.answer("❌ Please enter the cooking time in minutes.")
        return

    await state.update_data(cooking_time_minutes=time)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Easy",
                    callback_data="difficulty_easy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟡 Medium",
                    callback_data="difficulty_medium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Hard",
                    callback_data="difficulty_hard"
                )
            ]
        ]
    )

    await state.set_state(RecipeStates.waiting_for_difficulty)

    await message.answer(
        "Choose the difficulty:",
        reply_markup=keyboard
    )


@router.callback_query(
    F.data.startswith("difficulty_"),
    RecipeStates.waiting_for_difficulty
)
async def save_difficulty(callback: CallbackQuery, state: FSMContext):
    difficulty = callback.data.split("_")[1]

    await state.update_data(difficulty=difficulty)

    await state.set_state(RecipeStates.waiting_for_servings)

    await callback.message.edit_text(
        "🍽️ How many servings does this recipe make?"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_servings)
async def recipe_servings(message: Message, state: FSMContext):
    servings = int(message.text)

    if servings <= 0:
        await message.answer("❌ Enter a number greater than 0.")
        return

    await state.update_data(servings=servings)

    await state.set_state(RecipeStates.waiting_for_photo)

    await message.answer(
        "📷 Send a photo of the recipe:"
    )


@router.message(RecipeStates.waiting_for_photo, F.photo)
async def recipe_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]

    await state.update_data(
        photo_file_id=photo.file_id
    )

    await state.set_state(RecipeStates.waiting_for_ingredient_name)

    await message.answer(
        "🥕 Enter the ingredient name:"
    )


@router.message(RecipeStates.waiting_for_photo)
async def wrong_recipe_photo(message: Message):
    await message.answer(
        "❌ Please send a photo of the recipe."
    )


@router.message(RecipeStates.waiting_for_ingredient_name)
async def ingredient_name(message: Message, state: FSMContext):
    await state.update_data(
        ingredient_name=message.text
    )

    await state.set_state(RecipeStates.waiting_for_ingredient_amount)

    await message.answer(
        "⚖️ Enter the amount:"
    )


@router.message(RecipeStates.waiting_for_ingredient_amount)
async def ingredient_amount(message: Message, state: FSMContext):
    await state.update_data(
        ingredient_amount=message.text
    )

    await state.set_state(RecipeStates.waiting_for_ingredient_unit)

    await message.answer(
        "📏 Enter the unit (g, kg, ml, tbsp, etc.):"
    )


@router.message(RecipeStates.waiting_for_ingredient_unit)
async def ingredient_unit(message: Message, state: FSMContext):
    data = await state.get_data()

    ingredients = data.get("ingredients", [])

    ingredients.append({
        "name": data["ingredient_name"],
        "amount": data["ingredient_amount"],
        "unit": message.text
    })

    await state.update_data(
        ingredients=ingredients
    )

    await message.answer(
        "✅ Ingredient saved.\n\n"
        "Add another ingredient or finish:",
        reply_markup=finish_ingredients
    )

    await state.set_state(RecipeStates.waiting_for_ingredient_name)


@router.callback_query(F.data == "finish_ingredients")
async def finish_ingredients_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    conn = await get_connection()

    user = await conn.fetchrow(
        """
        select id
        from users
        where telegram_id = $1
        """,
        callback.from_user.id
    )

    recipe = await conn.fetchrow(
        """
        insert into recipes (
            category_id,
            created_by,
            name,
            description,
            photo_file_id,
            cooking_time_minutes,
            difficulty,
            servings
        )
        values ($1, $2, $3, $4, $5, $6, $7, $8)
        returning id
        """,
        data["category_id"],
        user["id"],
        data["name"],
        data["description"],
        data["photo_file_id"],
        data["cooking_time_minutes"],
        data["difficulty"],
        data["servings"]
    )

    recipe_id = recipe["id"]

    for ingredient in data["ingredients"]:
        await conn.execute(
            """
            insert into ingredients (
                recipe_id,
                name,
                amount,
                unit
            )
            values ($1, $2, $3, $4)
            """,
            recipe_id,
            ingredient["name"],
            ingredient["amount"],
            ingredient["unit"]
        )

    await conn.close()

    await state.update_data(
        recipe_id=recipe_id,
        steps=[]
    )

    await state.set_state(RecipeStates.waiting_for_step_instruction)

    await callback.message.edit_text(
        "✅ Ingredients saved!\n\n"
        "📝 Enter Step 1 instruction:"
    )

    await callback.answer()


# instructions

@router.message(RecipeStates.waiting_for_step_instruction)
async def step_instruction(message: Message, state: FSMContext):
    await state.update_data(
        step_instruction=message.text
    )

    await state.set_state(RecipeStates.waiting_for_step_photo)

    await message.answer(
        "📷 Send a photo for this step:"
    )


@router.message(RecipeStates.waiting_for_step_photo, F.photo)
async def step_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]

    await state.update_data(
        step_photo_file_id=photo.file_id
    )

    await state.set_state(RecipeStates.waiting_for_step_timer)

    await message.answer(
        "⏱️ Enter the timer in minutes.\n"
        "Enter 0 if this step has no timer:"
    )


@router.message(RecipeStates.waiting_for_step_timer)
async def step_timer(message: Message, state: FSMContext):
    try:
        timer = int(message.text)

        if timer < 0:
            await message.answer(
                "❌ Enter 0 or a number greater than 0."
            )
            return

    except ValueError:
        await message.answer(
            "❌ Please enter the timer in minutes."
        )
        return

    data = await state.get_data()

    steps = data.get("steps", [])

    steps.append({
        "instruction": data["step_instruction"],
        "photo_file_id": data["step_photo_file_id"],
        "timer_seconds": timer * 60
    })

    await state.update_data(
        steps=steps
    )

    await message.answer(
        f"✅ Step {len(steps)} saved.\n\n"
        "Add another step or finish:",
        reply_markup=finish_steps
    )

    await state.set_state(RecipeStates.waiting_for_step_instruction)


@router.callback_query(F.data == "finish_steps")
async def finish_steps_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    conn = await get_connection()

    for number, step in enumerate(data["steps"], start=1):
        await conn.execute(
            """
            insert into steps (
                recipe_id,
                step_number,
                instruction,
                photo_file_id,
                timer_seconds
            )
            values ($1, $2, $3, $4, $5)
            """,
            data["recipe_id"],
            number,
            step["instruction"],
            step["photo_file_id"],
            step["timer_seconds"]
        )

    await conn.close()

    await state.clear()

    await callback.message.edit_text(
        "🎉 Recipe added successfully!\n\n"
        "✅ Recipe information\n"
        "✅ Ingredients\n"
        "✅ Cooking steps"
    )

    await callback.answer()


# view recipes

@router.callback_query(F.data == "view_recipes")
async def view_recipes(callback: CallbackQuery):
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
            "📋 View Recipes\n\n"
            "There are no categories yet.",
            reply_markup=recipe_admin_menu
        )
        await callback.answer()
        return

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"view_category_{category['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="admin_recipes"
        )
    ])

    await callback.message.edit_text(
        "📂 Choose a category:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(F.data.startswith("view_category_"))
async def view_category_recipes(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[-1])

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
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Back",
                        callback_data="view_recipes"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "❌ No recipes available in this category.",
            reply_markup=keyboard
        )

        await callback.answer()
        return

    keyboard = []

    for recipe in recipes:
        keyboard.append([
            InlineKeyboardButton(
                text=recipe["name"],
                callback_data=f"view_recipe_{recipe['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="view_recipes"
        )
    ])

    await callback.message.edit_text(
        "🍳 Choose a recipe:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(F.data.startswith("view_recipe_"))
async def view_recipe(callback: CallbackQuery):
    recipe_id = int(callback.data.split("_")[-1])

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
        join categories c on c.id = r.category_id
        where r.id = $1
        """,
        recipe_id
    )

    ingredients = await conn.fetch(
        """
        select name, amount, unit
        from ingredients
        where recipe_id = $1
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
        text += (
            f"• {ingredient['name']} "
            f"{ingredient['amount']} {ingredient['unit']}\n"
        )

    text += "\n👨‍🍳 Steps:\n"

    for step in steps:
        timer = step["timer_seconds"] // 60

        text += f"\n{step['step_number']}. {step['instruction']}"

        if timer > 0:
            text += f" ⏱️ {timer} min"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="view_recipes"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# edit recipe

def edit_recipe_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Name",
                    callback_data="edit_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Description",
                    callback_data="edit_description"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Category",
                    callback_data="edit_recipe_category"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🕒 Cooking Time",
                    callback_data="edit_time"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Difficulty",
                    callback_data="edit_difficulty"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍽️ Servings",
                    callback_data="edit_servings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📷 Recipe Photo",
                    callback_data="edit_recipe_photo"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥕 Ingredients",
                    callback_data="edit_ingredients"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🍳 Steps",
                    callback_data="edit_steps"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="edit_back_recipe_admin"
                )
            ]
        ]
    )


def ingredient_edit_keyboard(ingredient_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Name",
                    callback_data=f"edit_ing_name_{ingredient_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚖️ Amount",
                    callback_data=f"edit_ing_amount_{ingredient_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📏 Unit",
                    callback_data=f"edit_ing_unit_{ingredient_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete",
                    callback_data=f"delete_ingredient_{ingredient_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="edit_ingredients"
                )
            ]
        ]
    )


def step_edit_keyboard(step_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Instruction",
                    callback_data=f"edit_step_instruction_{step_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📷 Photo",
                    callback_data=f"edit_step_photo_{step_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏱️ Timer",
                    callback_data=f"edit_step_timer_{step_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete",
                    callback_data=f"delete_step_{step_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="edit_steps"
                )
            ]
        ]
    )


@router.callback_query(F.data == "edit_recipe")
async def edit_recipe(callback: CallbackQuery, state: FSMContext):
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
            "✏️ Edit Recipe\n\n"
            "There are no categories yet.",
            reply_markup=recipe_admin_menu
        )
        await callback.answer()
        return

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"edit_category_{category['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="admin_recipes"
        )
    ])

    await callback.message.edit_text(
        "📂 Choose a category:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(F.data.startswith("edit_category_"))
async def edit_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])

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
                            callback_data="edit_recipe"
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
                callback_data=f"edit_select_recipe_{recipe['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="edit_recipe"
        )
    ])

    await callback.message.edit_text(
        "🍳 Choose a recipe:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(F.data.startswith("edit_select_recipe_"))
async def edit_select_recipe(callback: CallbackQuery, state: FSMContext):
    recipe_id = int(callback.data.split("_")[-1])

    await state.update_data(
        edit_recipe_id=recipe_id
    )

    await callback.message.edit_text(
        "✏️ Edit Recipe\n\n"
        "Choose what you want to edit:",
        reply_markup=edit_recipe_keyboard()
    )

    await callback.answer()


# name

@router.callback_query(F.data == "edit_name")
async def edit_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(
        RecipeStates.waiting_for_edit_name
    )

    await callback.message.edit_text(
        "✏️ Enter the new recipe name:"
    )

    await callback.answer()


@router.message(
    RecipeStates.waiting_for_edit_name,
    F.text
)
async def save_edit_name(message: Message, state: FSMContext):
    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await message.answer("❌ Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set name = $1
        where id = $2
        """,
        message.text,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Recipe name updated.",
        reply_markup=edit_recipe_keyboard()
    )


# description

@router.callback_query(F.data == "edit_description")
async def edit_description(callback: CallbackQuery, state: FSMContext):
    await state.set_state(
        RecipeStates.waiting_for_edit_description
    )

    await callback.message.edit_text(
        "📝 Enter the new description:"
    )

    await callback.answer()


@router.message(
    RecipeStates.waiting_for_edit_description,
    F.text
)
async def save_edit_description(message: Message, state: FSMContext):
    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await message.answer("❌ Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set description = $1
        where id = $2
        """,
        message.text,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Description updated.",
        reply_markup=edit_recipe_keyboard()
    )


# category

@router.callback_query(F.data == "edit_recipe_category")
async def edit_recipe_category(
    callback: CallbackQuery,
    state: FSMContext
):
    conn = await get_connection()

    categories = await conn.fetch(
        """
        select id, name
        from categories
        order by id
        """
    )

    await conn.close()

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"edit_set_category_{category['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="edit_back_edit_menu"
        )
    ])

    await state.set_state(
        RecipeStates.waiting_for_edit_category
    )

    await callback.message.edit_text(
        "📂 Choose the new category:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("edit_set_category_"),
    RecipeStates.waiting_for_edit_category
)
async def save_edit_category(
    callback: CallbackQuery,
    state: FSMContext
):
    category_id = int(callback.data.split("_")[-1])

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set category_id = $1
        where id = $2
        """,
        category_id,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await callback.message.edit_text(
        "✅ Category updated.\n\n"
        "✏️ Edit Recipe\n\n"
        "Choose what you want to edit:",
        reply_markup=edit_recipe_keyboard()
    )

    await callback.answer()


# cooking time

@router.callback_query(F.data == "edit_time")
async def edit_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(
        RecipeStates.waiting_for_edit_time
    )

    await callback.message.edit_text(
        "🕒 Enter the new cooking time in minutes:"
    )

    await callback.answer()


@router.message(
    RecipeStates.waiting_for_edit_time,
    F.text
)
async def save_edit_time(message: Message, state: FSMContext):
    try:
        time = int(message.text)

        if time <= 0:
            await message.answer(
                "❌ Enter a number greater than 0."
            )
            return

    except ValueError:
        await message.answer(
            "❌ Enter the cooking time in minutes."
        )
        return

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await message.answer("❌ Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set cooking_time_minutes = $1
        where id = $2
        """,
        time,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Cooking time updated.",
        reply_markup=edit_recipe_keyboard()
    )


# difficulty

@router.callback_query(F.data == "edit_difficulty")
async def edit_difficulty(
    callback: CallbackQuery,
    state: FSMContext
):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Easy",
                    callback_data="edit_set_difficulty_easy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟡 Medium",
                    callback_data="edit_set_difficulty_medium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Hard",
                    callback_data="edit_set_difficulty_hard"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="edit_back_edit_menu"
                )
            ]
        ]
    )

    await state.set_state(
        RecipeStates.waiting_for_edit_difficulty
    )

    await callback.message.edit_text(
        "⭐ Choose the new difficulty:",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("edit_set_difficulty_"),
    RecipeStates.waiting_for_edit_difficulty
)
async def save_edit_difficulty(
    callback: CallbackQuery,
    state: FSMContext
):
    difficulty = callback.data.split("_")[-1]

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set difficulty = $1
        where id = $2
        """,
        difficulty,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await callback.message.edit_text(
        "✅ Difficulty updated.\n\n"
        "✏️ Edit Recipe\n\n"
        "Choose what you want to edit:",
        reply_markup=edit_recipe_keyboard()
    )

    await callback.answer()


# servings

@router.callback_query(F.data == "edit_servings")
async def edit_servings(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.set_state(
        RecipeStates.waiting_for_edit_servings
    )

    await callback.message.edit_text(
        "🍽️ Enter the new number of servings:"
    )

    await callback.answer()


@router.message(
    RecipeStates.waiting_for_edit_servings,
    F.text
)
async def save_edit_servings(
    message: Message,
    state: FSMContext
):
    try:
        servings = int(message.text)

        if servings <= 0:
            await message.answer(
                "❌ Enter a number greater than 0."
            )
            return

    except ValueError:
        await message.answer(
            "❌ Enter the number of servings."
        )
        return

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await message.answer("❌ Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set servings = $1
        where id = $2
        """,
        servings,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Servings updated.",
        reply_markup=edit_recipe_keyboard()
    )


# recipe photo

@router.callback_query(F.data == "edit_recipe_photo")
async def edit_recipe_photo(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.set_state(
        RecipeStates.waiting_for_edit_recipe_photo
    )

    await callback.message.edit_text(
        "📷 Send the new recipe photo:"
    )

    await callback.answer()


@router.message(
    RecipeStates.waiting_for_edit_recipe_photo,
    F.photo
)
async def save_edit_recipe_photo(
    message: Message,
    state: FSMContext
):
    photo = message.photo[-1]

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await message.answer("❌ Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        update recipes
        set photo_file_id = $1
        where id = $2
        """,
        photo.file_id,
        data["edit_recipe_id"]
    )

    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Recipe photo updated.",
        reply_markup=edit_recipe_keyboard()
    )


@router.message(
    RecipeStates.waiting_for_edit_recipe_photo
)
async def wrong_edit_recipe_photo(message: Message):
    await message.answer(
        "❌ Please send a photo."
    )


# ingredients

@router.callback_query(F.data == "edit_ingredients")
async def edit_ingredients(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    ingredients = await conn.fetch(
        """
        select id, name, amount, unit
        from ingredients
        where recipe_id = $1
        order by id
        """,
        data["edit_recipe_id"]
    )

    await conn.close()

    if not ingredients:
        await callback.message.edit_text(
            "🥕 There are no ingredients in this recipe.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Back",
                            callback_data="edit_back_edit_menu"
                        )
                    ]
                ]
            )
        )
        await callback.answer()
        return

    keyboard = []

    for ingredient in ingredients:
        keyboard.append([
            InlineKeyboardButton(
                text=(
                    f"{ingredient['name']} - "
                    f"{ingredient['amount']} "
                    f"{ingredient['unit'] or ''}"
                ),
                callback_data=f"edit_ingredient_{ingredient['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="edit_back_edit_menu"
        )
    ])

    await callback.message.edit_text(
        "🥕 Choose an ingredient:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(
    F.data.regexp(r"^edit_ingredient_\d+$")
)
async def edit_ingredient(
    callback: CallbackQuery,
    state: FSMContext
):
    ingredient_id = int(
        callback.data.split("_")[-1]
    )

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    ingredient = await conn.fetchrow(
        """
        select name, amount, unit
        from ingredients
        where id = $1 and recipe_id = $2
        """,
        ingredient_id,
        data["edit_recipe_id"]
    )

    await conn.close()

    if not ingredient:
        await callback.answer("Ingredient not found.")
        return

    await state.update_data(
        edit_ingredient_id=ingredient_id
    )

    await callback.message.edit_text(
        f"🥕 {ingredient['name']}\n\n"
        "Choose what to change:",
        reply_markup=ingredient_edit_keyboard(ingredient_id)
    )

    await callback.answer()


@router.callback_query(F.data.regexp(r"^edit_ing_name_\d+$"))
async def edit_ing_name(callback: CallbackQuery,state: FSMContext):
    ingredient_id = int(
        callback.data.split("_")[-1]
    )

    await state.update_data(
        edit_ingredient_id=ingredient_id
    )

    await state.set_state(
        RecipeStates.waiting_for_edit_ingredient_name
    )

    await callback.message.edit_text(
        "✏️ Enter the new ingredient name:"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_edit_ingredient_name)
async def save_edit_ing_name(message: Message, state: FSMContext):
    data = await state.get_data()

    conn = await get_connection()
    await conn.execute(
        """
        update ingredients
        set name = $1
        where id = $2 and recipe_id = $3
        """,
        message.text,
        data["edit_ingredient_id"],
        data["edit_recipe_id"]
    )
    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Ingredient name updated.",
        reply_markup=edit_recipe_keyboard()
    )


@router.callback_query(F.data.regexp(r"^edit_ing_amount_\d+$"))
async def edit_ing_amount(callback: CallbackQuery,state: FSMContext):
    ingredient_id = int(callback.data.split("_")[-1])

    await state.update_data(edit_ingredient_id=ingredient_id)

    await state.set_state(RecipeStates.waiting_for_edit_ingredient_amount)

    await callback.message.edit_text("⚖️ Enter the new amount:")

    await callback.answer()


@router.message(RecipeStates.waiting_for_edit_ingredient_amount)
async def save_edit_ing_amount(message: Message, state: FSMContext):
    data = await state.get_data()

    conn = await get_connection()
    await conn.execute(
        """
        update ingredients
        set amount = $1
        where id = $2 and recipe_id = $3
        """,
        message.text,
        data["edit_ingredient_id"],
        data["edit_recipe_id"]
    )
    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Ingredient amount updated.",
        reply_markup=edit_recipe_keyboard()
    )

@router.callback_query(
    F.data.regexp(r"^edit_ing_unit_\d+$")
)
async def edit_ing_unit(
    callback: CallbackQuery,
    state: FSMContext
):
    ingredient_id = int(
        callback.data.split("_")[-1]
    )

    await state.update_data(
        edit_ingredient_id=ingredient_id
    )

    await state.set_state(
        RecipeStates.waiting_for_edit_ingredient_unit
    )

    await callback.message.edit_text(
        "📏 Enter the new unit:"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_edit_ingredient_unit)
async def save_edit_ing_unit(message: Message, state: FSMContext):
    data = await state.get_data()

    conn = await get_connection()
    await conn.execute(
        """
        update ingredients
        set unit = $1
        where id = $2 and recipe_id = $3
        """,
        message.text,
        data["edit_ingredient_id"],
        data["edit_recipe_id"]
    )
    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Ingredient unit updated.",
        reply_markup=edit_recipe_keyboard()
    )

@router.callback_query(
    F.data.regexp(r"^delete_ingredient_\d+$")
)
async def delete_ingredient(
    callback: CallbackQuery,
    state: FSMContext
):
    ingredient_id = int(
        callback.data.split("_")[-1]
    )

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        delete from ingredients
        where id = $1 and recipe_id = $2
        """,
        ingredient_id,
        data["edit_recipe_id"]
    )

    await conn.close()

    await callback.answer(
        "✅ Ingredient deleted."
    )

    await edit_ingredients(callback, state)


# steps

@router.callback_query(F.data == "edit_steps")
async def edit_steps(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    steps = await conn.fetch(
        """
        select id, step_number, instruction, timer_seconds
        from steps
        where recipe_id = $1
        order by step_number
        """,
        data["edit_recipe_id"]
    )

    await conn.close()

    if not steps:
        await callback.message.edit_text(
            "👨‍🍳 There are no steps in this recipe.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Back",
                            callback_data="edit_back_edit_menu"
                        )
                    ]
                ]
            )
        )
        await callback.answer()
        return

    keyboard = []

    for step in steps:
        keyboard.append([
            InlineKeyboardButton(
                text=(
                    f"Step {step['step_number']}: "
                    f"{step['instruction']}"
                ),
                callback_data=f"edit_step_{step['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="edit_back_edit_menu"
        )
    ])

    await callback.message.edit_text(
        "👨‍🍳 Choose a step:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(
    F.data.regexp(r"^edit_step_\d+$")
)
async def edit_step(
    callback: CallbackQuery,
    state: FSMContext
):
    step_id = int(
        callback.data.split("_")[-1]
    )

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    step = await conn.fetchrow(
        """
        select step_number, instruction
        from steps
        where id = $1 and recipe_id = $2
        """,
        step_id,
        data["edit_recipe_id"]
    )

    await conn.close()

    if not step:
        await callback.answer("Step not found.")
        return

    await state.update_data(
        edit_step_id=step_id
    )

    await callback.message.edit_text(
        f"👨‍🍳 Step {step['step_number']}\n\n"
        "Choose what to change:",
        reply_markup=step_edit_keyboard(step_id)
    )

    await callback.answer()


@router.callback_query(
    F.data.regexp(r"^edit_step_instruction_\d+$")
)
async def edit_step_instruction(
    callback: CallbackQuery,
    state: FSMContext
):
    step_id = int(
        callback.data.split("_")[-1]
    )

    await state.update_data(
        edit_step_id=step_id
    )

    await state.set_state(
        RecipeStates.waiting_for_edit_step_instruction
    )

    await callback.message.edit_text(
        "📝 Enter the new instruction:"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_edit_step_instruction)
async def save_edit_step_instruction(message: Message, state: FSMContext):
    data = await state.get_data()

    conn = await get_connection()
    await conn.execute(
        """
        update steps
        set instruction = $1
        where id = $2 and recipe_id = $3
        """,
        message.text,
        data["edit_step_id"],
        data["edit_recipe_id"]
    )
    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Step instruction updated.",
        reply_markup=edit_recipe_keyboard()
    )


@router.callback_query(
    F.data.regexp(r"^edit_step_photo_\d+$")
)
async def edit_step_photo(
    callback: CallbackQuery,
    state: FSMContext
):
    step_id = int(
        callback.data.split("_")[-1]
    )

    await state.update_data(
        edit_step_id=step_id
    )

    await state.set_state(
        RecipeStates.waiting_for_edit_step_photo
    )

    await callback.message.edit_text(
        "📷 Send the new step photo:"
    )

    await callback.answer()


@router.message(RecipeStates.waiting_for_edit_step_photo, F.photo)
async def save_edit_step_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    photo = message.photo[-1]

    conn = await get_connection()
    await conn.execute(
        """
        update steps
        set photo_file_id = $1
        where id = $2 and recipe_id = $3
        """,
        photo.file_id,
        data["edit_step_id"],
        data["edit_recipe_id"]
    )
    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Step photo updated.",
        reply_markup=edit_recipe_keyboard()
    )


@router.message(
    RecipeStates.waiting_for_edit_step_photo
)
async def wrong_edit_step_photo(message: Message):
    await message.answer(
        "❌ Please send a photo."
    )


@router.callback_query(
    F.data.regexp(r"^edit_step_timer_\d+$")
)
async def edit_step_timer(
    callback: CallbackQuery,
    state: FSMContext
):
    step_id = int(
        callback.data.split("_")[-1]
    )

    await state.update_data(
        edit_step_id=step_id
    )

    await state.set_state(
        RecipeStates.waiting_for_edit_step_timer
    )

    await callback.message.edit_text(
        "⏱️ Enter the new timer in minutes.\n"
        "Enter 0 if there is no timer:"
    )

    await callback.answer()

@router.message(RecipeStates.waiting_for_edit_step_timer)
async def save_edit_step_timer(message: Message, state: FSMContext):
    try:
        timer = int(message.text)

        if timer < 0:
            await message.answer("❌ Enter 0 or a number greater than 0.")
            return

    except ValueError:
        await message.answer("❌ Please enter the timer in minutes.")
        return

    data = await state.get_data()

    conn = await get_connection()
    await conn.execute(
        """
        update steps
        set timer_seconds = $1
        where id = $2 and recipe_id = $3
        """,
        timer * 60,
        data["edit_step_id"],
        data["edit_recipe_id"]
    )
    await conn.close()

    await state.set_state(None)

    await message.answer(
        "✅ Step timer updated.",
        reply_markup=edit_recipe_keyboard()
    )
    
@router.callback_query(
    F.data.regexp(r"^delete_step_\d+$")
)
async def delete_step(
    callback: CallbackQuery,
    state: FSMContext
):
    step_id = int(
        callback.data.split("_")[-1]
    )

    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    conn = await get_connection()

    await conn.execute(
        """
        delete from steps
        where id = $1 and recipe_id = $2
        """,
        step_id,
        data["edit_recipe_id"]
    )

    steps = await conn.fetch(
        """
        select id
        from steps
        where recipe_id = $1
        order by step_number
        """,
        data["edit_recipe_id"]
    )

    for number, step in enumerate(steps, start=1):
        await conn.execute(
            """
            update steps
            set step_number = $1
            where id = $2
            """,
            number,
            step["id"]
        )

    await conn.close()

    await callback.answer(
        "✅ Step deleted."
    )

    await edit_steps(callback, state)


# back buttons

@router.callback_query(F.data == "edit_back_edit_menu")
async def edit_back_edit_menu(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    if "edit_recipe_id" not in data:
        await callback.answer("Recipe not selected.")
        return

    await state.set_state(None)

    await callback.message.edit_text(
        "✏️ Edit Recipe\n\n"
        "Choose what you want to edit:",
        reply_markup=edit_recipe_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "edit_back_recipe_admin")
async def edit_back_recipe_admin(callback: CallbackQuery):
    await callback.message.edit_text(
        "🍳 Recipes\n\n"
        "Choose an option:",
        reply_markup=recipe_admin_menu
    )

    await callback.answer()



# delete recipe


@router.callback_query(F.data == "delete_recipe")
async def delete_recipe(callback: CallbackQuery):
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
            "🗑 Delete Recipe\n\n"
            "There are no categories yet.",
            reply_markup=recipe_admin_menu
        )
        await callback.answer()
        return

    keyboard = []

    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"delete_category_{category['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="admin_recipes"
        )
    ])

    await callback.message.edit_text(
        "📂 Choose a category:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(
    F.data.regexp(r"^delete_category_\d+$")
)
async def delete_category(callback: CallbackQuery):
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
                            callback_data="delete_recipe"
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
                callback_data=f"delete_select_recipe_{recipe['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="delete_recipe"
        )
    ])

    await callback.message.edit_text(
        "🍳 Choose a recipe to delete:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()


@router.callback_query(
    F.data.regexp(r"^delete_select_recipe_\d+$")
)
async def delete_select_recipe(callback: CallbackQuery):
    recipe_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

    recipe = await conn.fetchrow(
        """
        select name
        from recipes
        where id = $1
        """,
        recipe_id
    )

    await conn.close()

    if not recipe:
        await callback.answer("Recipe not found.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, delete",
                    callback_data=f"confirm_delete_recipe_{recipe_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data="delete_recipe"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"🗑️ Delete Recipe\n\n"
        f"Are you sure you want to delete:\n"
        f"🍳 {recipe['name']}?",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(
    F.data.regexp(r"^confirm_delete_recipe_\d+$")
)
async def confirm_delete_recipe(callback: CallbackQuery):
    recipe_id = int(
        callback.data.split("_")[-1]
    )

    conn = await get_connection()

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

    await conn.execute(
        """
        delete from recipes
        where id = $1
        """,
        recipe_id
    )

    await conn.close()

    await callback.message.edit_text(
        f"✅ Recipe deleted successfully.\n\n"
        f"🍳 {recipe['name']}",
        reply_markup=recipe_admin_menu
    )

    await callback.answer()