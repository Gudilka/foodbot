from bot.fsm.flow import ORDERED_STEPS, next_state, prev_state, resolve_state
from bot.fsm.states import RegistrationStates


def test_next_state_moves_forward() -> None:
    assert next_state(RegistrationStates.budget) == RegistrationStates.household_size


def test_prev_state_moves_backward() -> None:
    assert prev_state(RegistrationStates.cooking_skill) == RegistrationStates.dietary_restrictions


def test_resolve_state() -> None:
    state = resolve_state(RegistrationStates.notes.state)
    assert state == RegistrationStates.notes


def test_next_state_on_none_returns_first_step() -> None:
    assert next_state(None) == ORDERED_STEPS[0]
