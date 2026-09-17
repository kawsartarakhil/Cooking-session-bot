from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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


category_menu = InlineKeyboardMarkup( 
    inline_keyboard=[ 
        [ 
            InlineKeyboardButton( text="➕ Add Category", callback_data="add_category" ) ], 
        [ 
            InlineKeyboardButton( text="📋 View Categories", callback_data="view_categories" ) ], 

        [ InlineKeyboardButton( text="🔙 Back", callback_data="admin_panel" ) ] 
            ] 
                )