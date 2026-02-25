from __future__ import annotations

import uuid

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import EventLog


class EventLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_event(self, *, user_id: uuid.UUID | None, event_name: str, source: str = 'bot', payload: dict | None = None) -> None:
        await self._session.execute(
            insert(EventLog).values(
                user_id=user_id,
                event_name=event_name,
                source=source,
                payload=payload or {},
            )
        )
