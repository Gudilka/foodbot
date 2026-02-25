from __future__ import annotations

from sqlalchemy import text
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bot.db.models import Base, Cuisine, DietaryRestriction

DIETARY_RESTRICTIONS = [
    {"id": 1, "code": "lactose_free", "name": "Без лактозы"},
    {"id": 2, "code": "gluten_free", "name": "Без глютена"},
    {"id": 3, "code": "nut_free", "name": "Без орехов"},
    {"id": 4, "code": "vegan", "name": "Веганское"},
    {"id": 5, "code": "vegetarian", "name": "Вегетарианское"},
    {"id": 6, "code": "halal", "name": "Халяль"},
]

CUISINES = [
    {"id": 1, "code": "russian", "name": "Русская"},
    {"id": 2, "code": "italian", "name": "Итальянская"},
    {"id": 3, "code": "asian", "name": "Азиатская"},
    {"id": 4, "code": "georgian", "name": "Грузинская"},
    {"id": 5, "code": "mediterranean", "name": "Средиземноморская"},
    {"id": 6, "code": "mexican", "name": "Мексиканская"},
]


async def bootstrap_database(engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "sqlite":
            await _ensure_sqlite_profile_columns(connection)

    async with session_factory() as session:
        await _seed_reference_data(session)
        await session.commit()


async def _seed_reference_data(session: AsyncSession) -> None:
    restrictions_count = await session.scalar(select(func.count()).select_from(DietaryRestriction))
    if (restrictions_count or 0) == 0:
        session.add_all([DietaryRestriction(**item) for item in DIETARY_RESTRICTIONS])

    cuisines_count = await session.scalar(select(func.count()).select_from(Cuisine))
    if (cuisines_count or 0) == 0:
        session.add_all([Cuisine(**item) for item in CUISINES])


async def _ensure_sqlite_profile_columns(connection) -> None:  # type: ignore[no-untyped-def]
    pragma_rows = (await connection.execute(text("PRAGMA table_info(user_profiles)"))).fetchall()
    existing_columns = {row[1] for row in pragma_rows}
    if "diet_type" not in existing_columns:
        await connection.execute(text("ALTER TABLE user_profiles ADD COLUMN diet_type TEXT"))
    if "nutrition_goal" not in existing_columns:
        await connection.execute(text("ALTER TABLE user_profiles ADD COLUMN nutrition_goal TEXT"))
