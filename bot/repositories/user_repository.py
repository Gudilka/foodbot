from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.dml import upsert_insert
from bot.db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        query = select(User).where(User.telegram_user_id == telegram_user_id)
        return await self._session.scalar(query)

    async def upsert_user(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str,
    ) -> str:
        stmt = (
            upsert_insert(self._session, User.__table__)
            .values(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code or "ru",
                last_seen_at=datetime.now(tz=timezone.utc),
            )
            .on_conflict_do_update(
                index_elements=[User.telegram_user_id],
                set_={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "language_code": language_code or "ru",
                    "last_seen_at": datetime.now(tz=timezone.utc),
                },
            )
        )
        await self._session.execute(stmt)
        user = await self.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            raise RuntimeError("Failed to upsert user")
        return user.id
