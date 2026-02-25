from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bot.db.models import Base, Cuisine, DietaryRestriction

DIETARY_RESTRICTIONS = [
    {"id": 1, "code": "lactose_free", "name": "Lactose free"},
    {"id": 2, "code": "gluten_free", "name": "Gluten free"},
    {"id": 3, "code": "nut_free", "name": "Nut free"},
    {"id": 4, "code": "vegan", "name": "Vegan"},
    {"id": 5, "code": "vegetarian", "name": "Vegetarian"},
    {"id": 6, "code": "halal", "name": "Halal"},
]

CUISINES = [
    {"id": 1, "code": "russian", "name": "Russian"},
    {"id": 2, "code": "italian", "name": "Italian"},
    {"id": 3, "code": "asian", "name": "Asian"},
    {"id": 4, "code": "georgian", "name": "Georgian"},
    {"id": 5, "code": "mediterranean", "name": "Mediterranean"},
    {"id": 6, "code": "mexican", "name": "Mexican"},
]


async def bootstrap_database(engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

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
