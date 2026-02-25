from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.db.dml import upsert_insert
from bot.db.models import BotFSMState


def _state_to_str(state: StateType = None) -> str | None:
    if state is None:
        return None
    if isinstance(state, State):
        return state.state
    return str(state)


class DatabaseFSMStorage(BaseStorage):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def close(self) -> None:
        return

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        async with self._session_factory() as session:
            current_data = await self._get_data_raw(session, key)
            stmt = (
                upsert_insert(session, BotFSMState.__table__)
                .values(
                    bot_id=key.bot_id,
                    chat_id=key.chat_id,
                    user_id=key.user_id,
                    state=_state_to_str(state),
                    data=current_data,
                    updated_at=datetime.now(tz=timezone.utc),
                )
                .on_conflict_do_update(
                    index_elements=[BotFSMState.bot_id, BotFSMState.chat_id, BotFSMState.user_id],
                    set_={"state": _state_to_str(state), "updated_at": datetime.now(tz=timezone.utc)},
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        async with self._session_factory() as session:
            query = select(BotFSMState.state).where(
                BotFSMState.bot_id == key.bot_id,
                BotFSMState.chat_id == key.chat_id,
                BotFSMState.user_id == key.user_id,
            )
            return await session.scalar(query)

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        async with self._session_factory() as session:
            current_state = await self._get_state_raw(session, key)
            stmt = (
                upsert_insert(session, BotFSMState.__table__)
                .values(
                    bot_id=key.bot_id,
                    chat_id=key.chat_id,
                    user_id=key.user_id,
                    state=current_state,
                    data=data,
                    updated_at=datetime.now(tz=timezone.utc),
                )
                .on_conflict_do_update(
                    index_elements=[BotFSMState.bot_id, BotFSMState.chat_id, BotFSMState.user_id],
                    set_={"data": data, "updated_at": datetime.now(tz=timezone.utc)},
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with self._session_factory() as session:
            return await self._get_data_raw(session, key)

    async def update_data(self, key: StorageKey, data: dict[str, Any]) -> dict[str, Any]:
        async with self._session_factory() as session:
            current = await self._get_data_raw(session, key)
            current_state = await self._get_state_raw(session, key)
            current.update(data)
            stmt = (
                upsert_insert(session, BotFSMState.__table__)
                .values(
                    bot_id=key.bot_id,
                    chat_id=key.chat_id,
                    user_id=key.user_id,
                    state=current_state,
                    data=current,
                    updated_at=datetime.now(tz=timezone.utc),
                )
                .on_conflict_do_update(
                    index_elements=[BotFSMState.bot_id, BotFSMState.chat_id, BotFSMState.user_id],
                    set_={"data": current, "updated_at": datetime.now(tz=timezone.utc)},
                )
            )
            await session.execute(stmt)
            await session.commit()
            return current

    async def _get_data_raw(self, session: AsyncSession, key: StorageKey) -> dict[str, Any]:
        query = select(BotFSMState.data).where(
            BotFSMState.bot_id == key.bot_id,
            BotFSMState.chat_id == key.chat_id,
            BotFSMState.user_id == key.user_id,
        )
        data = await session.scalar(query)
        return data or {}

    async def _get_state_raw(self, session: AsyncSession, key: StorageKey) -> str | None:
        query = select(BotFSMState.state).where(
            BotFSMState.bot_id == key.bot_id,
            BotFSMState.chat_id == key.chat_id,
            BotFSMState.user_id == key.user_id,
        )
        return await session.scalar(query)


# Backward-compatible alias.
PostgresFSMStorage = DatabaseFSMStorage
