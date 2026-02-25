from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    budget = State()
    diet_type = State()
    nutrition_goal = State()
    household_size = State()
    dietary_restrictions = State()
    confirm = State()
