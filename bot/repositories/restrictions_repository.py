from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import DietaryRestriction


class RestrictionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_restrictions(self) -> list[DietaryRestriction]:
        result = await self._session.scalars(select(DietaryRestriction).order_by(DietaryRestriction.name))
        return list(result)
