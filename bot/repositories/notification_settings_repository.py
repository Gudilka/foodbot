from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.dml import upsert_insert
from bot.db.models import UserNotificationSettings


class NotificationSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_defaults(self, *, user_id: str) -> None:
        stmt = (
            upsert_insert(self._session, UserNotificationSettings.__table__)
            .values(user_id=user_id)
            .on_conflict_do_nothing(index_elements=[UserNotificationSettings.user_id])
        )
        await self._session.execute(stmt)
