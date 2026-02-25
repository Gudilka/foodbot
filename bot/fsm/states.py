from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    start = State()
    budget = State()
    household_size = State()
    dietary_restrictions = State()
    cooking_skill = State()
    max_cook_time = State()
    goals_kbju = State()
    exclude_fast_food = State()
    cuisine_preferences = State()
    reminder_settings = State()
    notes = State()
    confirm = State()
