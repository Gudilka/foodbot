from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def db_health_check(session: AsyncSession) -> None:
    await session.execute(text("SELECT 1"))
    restrictions_count = await session.scalar(text("SELECT count(*) FROM dietary_restrictions"))
    cuisines_count = await session.scalar(text("SELECT count(*) FROM cuisines"))
    if (restrictions_count or 0) == 0:
        raise RuntimeError("dietary_restrictions reference table is empty")
    if (cuisines_count or 0) == 0:
        raise RuntimeError("cuisines reference table is empty")
