from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserNotificationSettings


class NotificationSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_defaults(self, *, user_id: uuid.UUID) -> None:
        stmt = (
            insert(UserNotificationSettings)
            .values(user_id=user_id)
            .on_conflict_do_nothing(index_elements=[UserNotificationSettings.user_id])
        )
        await self._session.execute(stmt)
