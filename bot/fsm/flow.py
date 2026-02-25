from __future__ import annotations

from aiogram.fsm.state import State

from bot.fsm.states import RegistrationStates

ORDERED_STEPS: list[State] = [
    RegistrationStates.budget,
    RegistrationStates.diet_type,
    RegistrationStates.nutrition_goal,
    RegistrationStates.household_size,
    RegistrationStates.dietary_restrictions,
    RegistrationStates.confirm,
]


def next_state(current: State | None) -> State:
    if current is None:
        return ORDERED_STEPS[0]
    try:
        idx = ORDERED_STEPS.index(current)
    except ValueError:
        return ORDERED_STEPS[0]
    if idx >= len(ORDERED_STEPS) - 1:
        return ORDERED_STEPS[-1]
    return ORDERED_STEPS[idx + 1]


def prev_state(current: State | None) -> State:
    if current is None:
        return ORDERED_STEPS[0]
    try:
        idx = ORDERED_STEPS.index(current)
    except ValueError:
        return ORDERED_STEPS[0]
    if idx <= 0:
        return ORDERED_STEPS[0]
    return ORDERED_STEPS[idx - 1]


def resolve_state(state_name: str | None) -> State:
    if not state_name:
        return ORDERED_STEPS[0]
    for state in ORDERED_STEPS:
        if state.state == state_name:
            return state
    return ORDERED_STEPS[0]


def progress_caption(current: State | None) -> str:
    if current is None:
        return f"Шаг 1/{len(ORDERED_STEPS)}"
    try:
        idx = ORDERED_STEPS.index(current)
    except ValueError:
        idx = 0
    return f"Шаг {idx + 1}/{len(ORDERED_STEPS)}"
