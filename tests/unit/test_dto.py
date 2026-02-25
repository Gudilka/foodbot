from decimal import Decimal

import pytest

from bot.services.dto import RegistrationDraft
from bot.services.registration_service import DIET_TYPE_LABELS, NUTRITION_GOAL_LABELS, ReferenceOption, RegistrationService


def test_registration_draft_validation() -> None:
    draft = RegistrationDraft(
        telegram_user_id=1,
        weekly_budget_rub=Decimal('3000'),
        diet_type='vegetarian',
        nutrition_goal='weight_loss',
        household_size=2,
        dietary_restriction_codes=['vegan', 'vegan', 'gluten_free'],
    )
    assert draft.dietary_restriction_codes == ['vegan', 'gluten_free']
    assert draft.diet_type == 'vegetarian'
    assert draft.nutrition_goal == 'weight_loss'


def test_registration_draft_rejects_unsupported_values() -> None:
    with pytest.raises(ValueError):
        RegistrationDraft(
            telegram_user_id=1,
            weekly_budget_rub=Decimal('3000'),
            diet_type='invalid',
            nutrition_goal='maintenance',
            household_size=1,
        )


def test_restrictions_filter_excludes_diet_types() -> None:
    options = [
        ReferenceOption(code='vegan', name='Веганское'),
        ReferenceOption(code='vegetarian', name='Вегетарианское'),
        ReferenceOption(code='gluten_free', name='Без глютена'),
    ]
    filtered = RegistrationService.filter_restriction_options(options)
    assert [item.code for item in filtered] == ['gluten_free']


def test_russian_labels_present_for_diet_type_and_goal() -> None:
    assert DIET_TYPE_LABELS['omnivore'] == 'Всеядное'
    assert NUTRITION_GOAL_LABELS['maintenance'] == 'Поддержание формы'
