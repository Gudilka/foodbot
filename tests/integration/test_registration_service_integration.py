from __future__ import annotations

import random
from decimal import Decimal

import pytest
from sqlalchemy import text

from bot.db.bootstrap import bootstrap_database
from bot.db.session import build_engine, build_session_factory
from bot.services.dto import RegistrationDraft
from bot.services.registration_service import RegistrationService


pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def session_factory(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path}/integration_foodbot.db"
    engine = build_engine(db_url)
    factory = build_session_factory(engine)
    await bootstrap_database(engine, factory)
    yield factory
    await engine.dispose()


async def test_save_profile_upsert_and_replace_relations(session_factory) -> None:
    service = RegistrationService(session_factory)
    telegram_id = random.randint(10_000_000, 99_999_999)

    draft = RegistrationDraft(
        telegram_user_id=telegram_id,
        weekly_budget_rub=Decimal("5000"),
        diet_type="vegetarian",
        nutrition_goal="weight_loss",
        household_size=2,
        dietary_restriction_codes=["gluten_free"],
    )
    await service.save_profile(draft=draft, mode="create")

    draft_2 = RegistrationDraft(
        telegram_user_id=telegram_id,
        weekly_budget_rub=Decimal("4500"),
        diet_type="omnivore",
        nutrition_goal="maintenance",
        household_size=1,
        dietary_restriction_codes=["lactose_free"],
    )
    await service.save_profile(draft=draft_2, mode="update")

    async with session_factory() as session:
        profile_row = (
            await session.execute(
                text(
                    """
                    SELECT p.weekly_budget_rub, p.household_size, p.diet_type, p.nutrition_goal
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
        assert profile_row.diet_type == "omnivore"
        assert profile_row.nutrition_goal == "maintenance"

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


async def test_bootstrap_adds_new_profile_columns_for_legacy_sqlite(tmp_path) -> None:
    db_url = f"sqlite+aiosqlite:///{tmp_path}/legacy_profile.db"
    engine = build_engine(db_url)

    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                CREATE TABLE users (
                  id TEXT PRIMARY KEY,
                  telegram_user_id BIGINT UNIQUE NOT NULL
                )
                """
            )
        )
        await connection.execute(
            text(
                """
                CREATE TABLE user_profiles (
                  user_id TEXT PRIMARY KEY,
                  currency TEXT NOT NULL DEFAULT 'RUB',
                  household_size SMALLINT NOT NULL DEFAULT 1,
                  weekly_budget_rub NUMERIC(12,2) NOT NULL
                )
                """
            )
        )

    session_factory = build_session_factory(engine)
    await bootstrap_database(engine, session_factory)

    async with engine.begin() as connection:
        rows = (await connection.execute(text("PRAGMA table_info(user_profiles)"))).fetchall()
        columns = {row[1] for row in rows}
        assert "diet_type" in columns
        assert "nutrition_goal" in columns

    await engine.dispose()
