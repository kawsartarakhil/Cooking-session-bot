from aiogram.fsm.state import StatesGroup, State

class CategoryStates(StatesGroup):
    waiting_for_name = State()