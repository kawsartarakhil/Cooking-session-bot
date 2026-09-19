from aiogram.fsm.state import StatesGroup, State


class RecipeStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_time = State()
    waiting_for_difficulty = State()
    waiting_for_servings = State()
    waiting_for_photo = State()

    waiting_for_ingredient_name = State()
    waiting_for_ingredient_amount = State()
    waiting_for_ingredient_unit = State()

    waiting_for_step_instruction = State()
    waiting_for_step_photo = State()
    waiting_for_step_timer = State()

    waiting_for_edit_name = State()
    waiting_for_edit_description = State()
    waiting_for_edit_category = State()
    waiting_for_edit_time = State()
    waiting_for_edit_difficulty = State()
    waiting_for_edit_servings = State()
    waiting_for_edit_recipe_photo = State()

    waiting_for_edit_ingredient_name = State()
    waiting_for_edit_ingredient_amount = State()
    waiting_for_edit_ingredient_unit = State()

    waiting_for_edit_step_instruction = State()
    waiting_for_edit_step_photo = State()
    waiting_for_edit_step_timer = State()