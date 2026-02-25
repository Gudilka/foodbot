from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Cuisine


class CuisinesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cuisines(self) -> list[Cuisine]:
        result = await self._session.scalars(select(Cuisine).order_by(Cuisine.name))
        return list(result)
