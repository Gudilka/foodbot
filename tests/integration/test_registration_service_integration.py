from __future__ import annotations

import os
import random
from decimal import Decimal

import pytest
from sqlalchemy import text

from bot.db.session import build_engine, build_session_factory
from bot.services.dto import RegistrationDraft
from bot.services.registration_service import RegistrationService


pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def session_factory():
    db_url = os.getenv("TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TEST_DATABASE_URL is not set")
    engine = build_engine(db_url)
    factory = build_session_factory(engine)
    yield factory
    await engine.dispose()


async def test_save_profile_upsert_and_replace_relations(session_factory) -> None:
    service = RegistrationService(session_factory)
    telegram_id = random.randint(10_000_000, 99_999_999)

    draft = RegistrationDraft(
        telegram_user_id=telegram_id,
        weekly_budget_rub=Decimal("5000"),
        household_size=2,
        cooking_skill=3,
        max_cook_time_min=60,
        dietary_restriction_codes=["vegan", "gluten_free"],
        cuisine_codes=["asian", "italian"],
        reminder_hour_local=19,
    )
    await service.save_profile(draft=draft, mode="create")

    draft_2 = RegistrationDraft(
        telegram_user_id=telegram_id,
        weekly_budget_rub=Decimal("4500"),
        household_size=1,
        cooking_skill=2,
        max_cook_time_min=40,
        dietary_restriction_codes=["lactose_free"],
        cuisine_codes=["russian"],
        reminder_hour_local=10,
    )
    await service.save_profile(draft=draft_2, mode="update")

    async with session_factory() as session:
        profile_row = (
            await session.execute(
                text(
                    """
                    SELECT p.weekly_budget_rub, p.household_size, p.max_cook_time_min
                    FROM users u
                    JOIN user_profiles p ON p.user_id = u.id
                    WHERE u.telegram_user_id = :telegram_id
                    """
                ),
                {"telegram_id": telegram_id},
            )
        ).first()
        assert profile_row is not None
        assert Decimal(profile_row.weekly_budget_rub) == Decimal("4500")
        assert profile_row.household_size == 1

        restrictions = await session.execute(
            text(
                """
                SELECT dr.code
                FROM users u
                JOIN user_dietary_restrictions udr ON udr.user_id = u.id
                JOIN dietary_restrictions dr ON dr.id = udr.restriction_id
                WHERE u.telegram_user_id = :telegram_id
                ORDER BY dr.code
                """
            ),
            {"telegram_id": telegram_id},
        )
        assert [row.code for row in restrictions.fetchall()] == ["lactose_free"]

        cuisines = await session.execute(
            text(
                """
                SELECT c.code
                FROM users u
                JOIN user_cuisine_preferences ucp ON ucp.user_id = u.id
                JOIN cuisines c ON c.id = ucp.cuisine_id
                WHERE u.telegram_user_id = :telegram_id
                ORDER BY c.code
                """
            ),
            {"telegram_id": telegram_id},
        )
        assert [row.code for row in cuisines.fetchall()] == ["russian"]

        events = await session.execute(
            text(
                """
                SELECT event_name
                FROM event_log e
                JOIN users u ON u.id = e.user_id
                WHERE u.telegram_user_id = :telegram_id
                ORDER BY e.id
                """
            ),
            {"telegram_id": telegram_id},
        )
        event_names = [row.event_name for row in events.fetchall()]
        assert "onboarding_completed" in event_names
        assert "profile_updated" in event_names
