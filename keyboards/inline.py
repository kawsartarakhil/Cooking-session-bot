from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

#admin
admin_panel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📂 Categories",
                callback_data="admin_categories"
            )
        ],
        [
            InlineKeyboardButton(
                text="🍳 Recipes",
                callback_data="admin_recipes"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Statistics",
                callback_data="admin_statistics"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data="admin_back"
            )
        ]
    ]
)

admin_panel = InlineKeyboardMarkup( 
    inline_keyboard=[
        [ 
            InlineKeyboardButton( text="📂 Categories", callback_data="admin_categories" ) ], 
        [ 
            InlineKeyboardButton( text="🍳 Recipes", callback_data="admin_recipes" ) ], 
        [ 
            InlineKeyboardButton( text="📊 Statistics", callback_data="admin_statistics" ) ],
        [ 
            InlineKeyboardButton( text="🔙 Back", callback_data="admin_back" ) ] 
            ] 
                ) 

#category
category_menu = InlineKeyboardMarkup( 
    inline_keyboard=[ 
        [ 
            InlineKeyboardButton( text="➕ Add Category", callback_data="add_category" ) ], 
        [ 
            InlineKeyboardButton( text="📋 View Categories", callback_data="view_categories" ) ], 

        [ InlineKeyboardButton( text="🔙 Back", callback_data="admin_panel" ) ] 
            ] 
                )

#recipe
recipe_admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Recipe", callback_data="add_recipe")],
        [InlineKeyboardButton(text="📋 View Recipes", callback_data="view_recipes")],
        [InlineKeyboardButton(text="✏️ Edit Recipe", callback_data="edit_recipe")],
        [InlineKeyboardButton(text="🗑️ Delete Recipe", callback_data="delete_recipe")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel")]
    ]
)

finish_ingredients = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Finish Ingredients",
                callback_data="finish_ingredients"
            )
        ]
    ]
)

finish_steps = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Finish Steps",
                callback_data="finish_steps"
            )
        ]
    ]
)