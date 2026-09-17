from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🍳 Recipes"),
            KeyboardButton(text="❤️ Favorites")
        ],
        [
            KeyboardButton(text="📖 My Recipes"),
            KeyboardButton(text="🕐 History")
        ],
        [
            KeyboardButton(text="⚙️ Settings")
        ]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🍳 Recipes"),
            KeyboardButton(text="❤️ Favorites")
        ],
        [
            KeyboardButton(text="📖 My Recipes"),
            KeyboardButton(text="🕐 History")
        ],
        [
            KeyboardButton(text="⚙️ Settings")
        ],
        [
            KeyboardButton(text="👑 Admin Panel")
        ]
    ],
    resize_keyboard=True
)

