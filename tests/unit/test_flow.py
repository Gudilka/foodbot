from bot.fsm.flow import ORDERED_STEPS, next_state, prev_state, progress_caption, resolve_state
from bot.fsm.states import RegistrationStates


def test_next_state_moves_forward() -> None:
    assert next_state(RegistrationStates.budget) == RegistrationStates.diet_type


def test_prev_state_moves_backward() -> None:
    assert prev_state(RegistrationStates.household_size) == RegistrationStates.nutrition_goal


def test_resolve_state() -> None:
    state = resolve_state(RegistrationStates.confirm.state)
    assert state == RegistrationStates.confirm


def test_next_state_on_none_returns_first_step() -> None:
    assert next_state(None) == ORDERED_STEPS[0]


def test_progress_caption_uses_new_step_count() -> None:
    assert progress_caption(None) == "Шаг 1/6"
