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