from decimal import Decimal

from bot.services.dto import RegistrationDraft


def test_registration_draft_validation() -> None:
    draft = RegistrationDraft(
        telegram_user_id=1,
        weekly_budget_rub=Decimal('3000'),
        household_size=2,
        cooking_skill=4,
        max_cook_time_min=45,
        dietary_restriction_codes=['vegan', 'vegan', 'gluten_free'],
        cuisine_codes=['asian', 'asian'],
        reminder_hour_local=10,
    )
    assert draft.dietary_restriction_codes == ['vegan', 'gluten_free']
    assert draft.cuisine_codes == ['asian']
