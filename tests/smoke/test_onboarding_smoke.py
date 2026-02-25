from __future__ import annotations

import random
from decimal import Decimal

import pytest
from aiogram.types import User as TgUser

from bot.db.bootstrap import bootstrap_database
from bot.db.session import build_engine, build_session_factory
from bot.services.dto import RegistrationDraft
from bot.services.registration_service import RegistrationService


pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def service(tmp_path) -> RegistrationService:
    db_url = f"sqlite+aiosqlite:///{tmp_path}/smoke_foodbot.db"
    engine = build_engine(db_url)
    factory = build_session_factory(engine)
    await bootstrap_database(engine, factory)
    yield RegistrationService(factory)
    await engine.dispose()


async def test_new_user_onboarding_and_existing_user_profile_edit(service: RegistrationService) -> None:
    telegram_id = random.randint(100_000_000, 999_999_999)
    tg_user = TgUser(id=telegram_id, is_bot=False, first_name="Test", username="test_user", language_code="ru")

    user_id, is_new = await service.ensure_user(tg_user)
    assert user_id is not None
    assert is_new is True

    first_draft = RegistrationDraft(
        telegram_user_id=telegram_id,
        username="test_user",
        first_name="Test",
        last_name=None,
        language_code="ru",
        weekly_budget_rub=Decimal("3200"),
        household_size=1,
        cooking_skill=3,
        max_cook_time_min=55,
        dietary_restriction_codes=["vegan"],
        cuisine_codes=["asian"],
        reminder_hour_local=18,
    )
    await service.save_profile(draft=first_draft, mode="create")
    profile = await service.get_profile(telegram_user_id=telegram_id)
    assert profile is not None
    assert profile.weekly_budget_rub == Decimal("3200")
    assert profile.cuisine_codes == ["asian"]

    second_draft = first_draft.model_copy(update={"weekly_budget_rub": Decimal("4100"), "cuisine_codes": ["russian"]})
    await service.save_profile(draft=second_draft, mode="update")
    profile_after = await service.get_profile(telegram_user_id=telegram_id)
    assert profile_after is not None
    assert profile_after.weekly_budget_rub == Decimal("4100")
    assert profile_after.cuisine_codes == ["russian"]
